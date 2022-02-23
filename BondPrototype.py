# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
#%%
import pandas as pd
import numpy as np
from QuantLib import *
deposits = { (1, Days): 0.18,  # O/N
             (2, Days): 0.12,  # T/N
             (3, Days): 0.12,   # S/N
             (1, Weeks): 0.16,
             (2, Weeks): 0.085,
             (3, Weeks): 0.16,
             (1, Months): 0.165,
             (2, Months): 0.275,
             (3, Months): 0.335,
             (4, Months): 0.425,
             (5, Months): 0.505,
             }

swaps = { (1,Years): 0.881,
          (2,Years): 1.34,
          (3,Years): 1.5365,
          (4,Years): 1.6518,
          (5,Years): 1.6890,
          (6,Years): 1.7305,
          (7,Years): 1.766,
          (8,Years): 1.788,
          (9,Years): 1.808,
          (10,Years): 1.828,
          (12,Years): 1.873,
          (15,Years): 1.906,
          (20,Years): 1.945,
          (25,Years): 1.925,
          (30,Years): 1.8978,
          }

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

settlementDate = Date("31-01-2022", "%d-%m-%Y")
Settings.instance().evaluationDate = settlementDate

# DepositRateHelper(quote, tenor, fixingDays, calendar, convention, endOfMonth, dayCounter)
depositHelpers = []
for i, (n, unit) in enumerate(deposits.keys()):
    deposit = QuoteHandle(SimpleQuote(deposits[(n,unit)] * 0.01))
    if i < 3:
        depositHelpers.append(DepositRateHelper(deposit, Period(1, Days), i, UnitedStates(UnitedStates.NYSE), 
                                                Following, False, Actual360())) 
    else:
        depositHelpers.append(DepositRateHelper(deposit, Period(n, unit), 2, UnitedStates(UnitedStates.NYSE), 
                                                Following, False, Actual360())) 
    
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  

# IborIndex(familyName, tenor, settlementDays, currency, fixingCalendar, convention, endOfMonth, 
#           dayCounter, =Handleql.YieldTermStructure())
"""
Libor3M = IborIndex('CPIndex', Period(3, Months), 2, USDCurrency(), UnitedStates(UnitedStates.LiborImpact), 
                    ModifiedFollowing, False, Actual360())
"""
Libor3M = USDLibor(Period('3M'))


# SwapRateHelper(quote, tenor, calendar, fixedFrequency, fixedConvention, fixedDayCount, iborIndex, 
#               d=ql.QuoteHandle(), fwdStart=ql.Period(), discountingCurve=ql.YieldTermStructureHandle(), 
#                set spreatlementDays=Null< Natural >(), pillar=ql.Pillar.LastRelevantDate, customPillarDate=ql.Date(), 
#                endOfMonth=False)

swapHelpers = []   
for n,unit in swaps.keys():
    swap = QuoteHandle(SimpleQuote(swaps[(n,unit)] * 0.01))
    
    swapHelpers.append(SwapRateHelper(swap, Period(n, unit), UnitedStates(UnitedStates.NYSE), Annual, 
                                      Following, Actual360(), Libor3M))
    

helpers = depositHelpers + swapHelpers
referenceDate = settlementDate

# # PiecewiseYieldCurve <ZeroYield, Linear>
pwYieldCurve = PiecewiseLinearZero(referenceDate, helpers, Actual360())
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
spotCurve = ZeroCurve(spotDates, spotRates, Thirty360(), UnitedStates(UnitedStates.NYSE), Linear(),
                      Compounded, Annual)
spotCurveHandle = YieldTermStructureHandle(spotCurve)

# DiscountCurve(dates, dfs, dayCounter, cal=ql.NullCalendar())
dfs = data['Discount']
discountCurve = DiscountCurve(spotDates, dfs, Thirty360(), UnitedStates(UnitedStates.NYSE))
discountCurveHandle = YieldTermStructureHandle(discountCurve)

                   
# Schedule(effectiveDate, terminationDate, tenor, calendar, convention, terminationDateConvention, rule, endOfMonth, firstDate=Date(), nextToLastDate=Date())
schedule_backward = Schedule(Date(29, 10, 2020), Date(29, 10, 2030), Period(Semiannual), UnitedStates(UnitedStates.NYSE),
                             ModifiedFollowing, Following, DateGeneration.Backward, False)

# FixedRateBond(settlementDays, faceAmount, schedule, coupon, paymentConvention)
fixedRateBond = FixedRateBond(2, 1000000, schedule_backward, [0.012], Thirty360())

# DiscountingBondEngine(discountCurve)
bondEngine = DiscountingBondEngine(discountCurveHandle)
fixedRateBond.setPricingEngine(bondEngine)
print(fixedRateBond.NPV())
print(fixedRateBond.cleanPrice()) # Written by: BondFunctions.cleanPrice(fixedRateBond, spotCurve)
#%%
# Cash Flow all details.        
# https://quant.stackexchange.com/questions/54666/how-can-i-see-the-cashflows-of-a-specific-bond-created-in-quantlib-in-python-th        
fields = [
    'accrualDays', 'accrualEndDate', 'accrualPeriod', 'accrualStartDate',
    'amount',  'date', 'dayCounter', 'interestRate', 'nominal',  'rate'
]

cashFlow = []
for cf in list(map(as_fixed_rate_coupon, fixedRateBond.cashflows()))[:-1]:
    cashFlow.append({fld: eval(f"cf.{fld}()") for fld in fields})
cashFlow = pd.DataFrame(cashFlow)

#%%
# Bond Valuation
mkt_value = 91.833
z_spread = BondFunctions.zSpread(fixedRateBond, mkt_value, spotCurve, Thirty360(), Compounded, Semiannual)

bd_yield = fixedRateBond.bondYield(mkt_value, Thirty360(),Compounded,Semiannual)

bps_rate = BondFunctions.bps(fixedRateBond,discountCurve)

ModDur = BondFunctions.duration(fixedRateBond,bd_yield,Thirty360(), Compounded,Semiannual, Duration.Modified)
MacDur = BondFunctions.duration(fixedRateBond,bd_yield,Thirty360(), Compounded,Semiannual, Duration.Macaulay)
Convex = BondFunctions.convexity(fixedRateBond,bd_yield,Thirty360(), Compounded,Semiannual)


spread = QuoteHandle(SimpleQuote(z_spread))
ts_spreaded1 = ZeroSpreadedTermStructure(spotCurveHandle, spread, Compounded, Semiannual)
disCurveHandle = YieldTermStructureHandle(ts_spreaded1)

discounts = [ts_spreaded1.discount(date) for date in spotDates]
bondEngine = DiscountingBondEngine(disCurveHandle)

fixedRateBond.setPricingEngine(bondEngine)
print(fixedRateBond.cleanPrice()) 

cashFlow.accrualEndDate = cashFlow.accrualEndDate.apply(lambda x:x.ISO())
cashFlow.accrualStartDate = cashFlow.accrualStartDate.apply(lambda x:x.ISO())
cashFlow.date = cashFlow.date.apply(lambda x:x.ISO())

cashFlow.to_csv('C:/Users/joshchien/Desktop/Python/cashflow.csv')


dates = [ c.date() for c in fixedRateBond.cashflows() ]
cfs = [ c.amount() for c in fixedRateBond.cashflows() ]
InputCF = pd.DataFrame(zip(dates, cfs),columns = ('date','amount'), index = range(1,len(dates)+1))

