# -*- coding: utf-8 -*-
"""
Created on Mon Feb 21 15:12:17 2022

@author: joshchien
"""
#%%
import pandas as pd
import numpy as np
from QuantLib import *

deposits = { (1, Weeks): 0.1733,
             (2, Weeks): 0.2422,
             (1, Months): 0.3908,
             (2, Months): 0.4428,
             (3, Months): 0.4802,
             (6, Months): 0.5725,
             }

swaps = { (1,Years): 0.6801,
          (2,Years): 0.8351,
          (3,Years): 0.9020,
          (4,Years): 0.9130,
          (5,Years): 0.9201,
          (7,Years): 0.9325,
          (10,Years): 0.9451,
          (15,Years): 0.9150,
          }

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
settlementDate = Date("21-02-2022", "%d-%m-%Y")
Settings.instance().evaluationDate = settlementDate

# DepositRateHelper(quote, tenor, fixingDays, calendar, convention, endOfMonth, dayCounter)
depositHelpers = []
for i, (n, unit) in enumerate(deposits.keys()):
    deposit = QuoteHandle(SimpleQuote(deposits[(n,unit)] * 0.01))
    depositHelpers.append(DepositRateHelper(deposit, Period(n, unit), 2, Taiwan(), 
                                                Following, False, ActualActual())) 
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  

# IborIndex(familyName, tenor, settlementDays, currency, fixingCalendar, convention, endOfMonth, 
#           dayCounter, =Handleql.YieldTermStructure())

Taibor3M = IborIndex('TAIBOR3M', Period(3, Months), 2, TWDCurrency(), Taiwan(), 
                    ModifiedFollowing, False, ActualActual())

#Libor3M = USDLibor(Period('3M'))


# SwapRateHelper(quote, tenor, calendar, fixedFrequency, fixedConvention, fixedDayCount, iborIndex, 
#               d=ql.QuoteHandle(), fwdStart=ql.Period(), discountingCurve=ql.YieldTermStructureHandle(), 
#                set spreatlementDays=Null< Natural >(), pillar=ql.Pillar.LastRelevantDate, customPillarDate=ql.Date(), 
#                endOfMonth=False)

swapHelpers = []   
for n,unit in swaps.keys():
    swap = QuoteHandle(SimpleQuote(swaps[(n,unit)] * 0.01))
    
    swapHelpers.append(SwapRateHelper(swap, Period(n, unit), Taiwan(), Quarterly, 
                                      Following, ActualActual(), Taibor3M))
    

helpers = depositHelpers + swapHelpers
referenceDate = settlementDate

# # PiecewiseYieldCurve <ZeroYield, Linear>
pwYieldCurve = PiecewiseLinearZero(referenceDate, helpers, ActualActual())
pwYieldCurve.enableExtrapolation()
dates, rates = zip(*pwYieldCurve.nodes())

"""
# PiecewiseSplineCubicDiscount <ZeroYield, Linear>

pwDiscountCurve = PiecewiseSplineCubicDiscount(referenceDate, helpers, Actual360())
pwDiscountCurve.enableExtrapolation()
dates, discounts = zip(*pwDiscountCurve.nodes())    

for date in dates:
discountRates = []
    tau = Actual360().yearFraction(settlementDate, date)
    discountRates.append(pwDiscountCurve.discount(tau))
"""

zeroRates = []
for date in dates:
    zeroRates.append(pwYieldCurve.zeroRate(date, ActualActual(ActualActual.Actual365), Compounded, Annual).rate())

discountRates = []
for date in dates:
    discountRates.append(pwYieldCurve.discount(date))
  
                        
data_ = pd.DataFrame({'Date': [date.ISO() for date in dates],
                      'Zero': [zeroRate * 100 for zeroRate in zeroRates],
                      'Discount': discountRates})

data = pd.DataFrame({'Date': dates,
                     'tau': [date - settlementDate for date in dates],
                     'Zero': zeroRates,
                     'Discount': discountRates})
# ZeroCurve(dates, yields, dayCounter, cal, i, comp, freq)
spotDates = data['Date']
spotRates = data['Zero']
spotCurve = ZeroCurve(spotDates, spotRates, ActualActual(), Taiwan(), Linear(),
                      Compounded, Annual)
spotCurveHandle = YieldTermStructureHandle(spotCurve)

# DiscountCurve(dates, dfs, dayCounter, cal=ql.NullCalendar())
dfs = data['Discount']
discountCurve = DiscountCurve(spotDates, dfs, ActualActual(), Taiwan())
discountCurveHandle = YieldTermStructureHandle(discountCurve)

engine =DiscountingSwapEngine(discountCurveHandle)
Taibor3M = IborIndex('TAIBOR3M', Period(3, Months), 2,TWDCurrency(),Taiwan(),
                     ModifiedFollowing, False, ActualActual(),spotCurveHandle)
Taibor3M.addFixing(Date(3, 2, 2022), 0.0048)
Taibor3M.addFixing(Date(1, 2, 2018), 0.0048)
#index = USDLibor(Period('3M'),discountCurveHandle)

schedule = MakeSchedule(Date(5,2,2018), Date(5,2,2023), Period('3M'),forwards=True)
nominal = [300e6]


fixedLeg = FixedRateLeg(schedule, Taibor3M.dayCounter(), nominal, [0.0106])
floatingLeg = IborLeg(nominal, schedule, Taibor3M)
#swap = ql.Swap(fixedLeg, floatingLeg)
swap = Swap(floatingLeg,fixedLeg)
swap.setPricingEngine(engine)

fix = swap.legNPV(0)
flo = swap.legNPV(1)
MtM = swap.NPV()


cashflows = pd.DataFrame({
    'date': cf.date(),
    'amount': cf.amount()
    } for cf in swap.leg(1))
display(cashflows)
#%%%
discountTermStructure = RelinkableYieldTermStructureHandle(discountCurve)
shift = 0.0001
# UP
shiftedDiscountCurve = ZeroSpreadedTermStructure(discountCurveHandle, QuoteHandle(SimpleQuote(shift)))
discountTermStructure.linkTo(shiftedDiscountCurve)
P_p = CashFlows.npv(swap.leg(0), discountTermStructure, False, settlementDate)
# Down
shiftedDiscountCurve = ZeroSpreadedTermStructure(discountCurveHandle, QuoteHandle(SimpleQuote(-shift)))
discountTermStructure.linkTo(shiftedDiscountCurve)
P_m = CashFlows.npv(swap.leg(0), discountTermStructure, False, settlementDate)

bps = P_p - abs(fix)

#%%%





cashflows = pd.DataFrame({
    'nominal': cf.nominal(),
    'accrualStartDate': cf.accrualStartDate().ISO(),
    'accrualEndDate': cf.accrualEndDate().ISO(),
    'rate': cf.rate(),
    'amount': cf.amount()
    } for cf in map(as_coupon, swap.leg(0)))
display(cashflows)