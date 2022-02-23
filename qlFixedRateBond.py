# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 09:43:46 2022

@author: joshchien
"""
import pandas as pd
import numpy as np
from QuantLib import *
#from qlSchedule import *

class qlFixedRateBond(object):
    
    def __init__(self,settlementDays, faceAmount, scheduleobj, coupon, paymentConvention,
               spotCurve,discountCurve,marketprice,freq,compound,isCalibration=True):
        self.settlements = settlementDays
        self.faceAmount = faceAmount
        self.scheduleobj = scheduleobj
        self.coupon = coupon
        self.paymentConvention = paymentConvention
        self.spotCurve = spotCurve
        self.discountCurve = discountCurve
        self.marketprice = marketprice
        self.freq = freq
        self.compound = compound
        self.isCalibration = isCalibration
     
        # FixedRateBond Object setting 
        fixedRateBond = FixedRateBond(self.settlements, self.faceAmount, self.scheduleobj,
                                      self.coupon,self.paymentConvention)
        discountCurveHandle = YieldTermStructureHandle(self.discountCurve)
        bondEngine = DiscountingBondEngine(discountCurveHandle)
        fixedRateBond.setPricingEngine(bondEngine)
        
        # # calculate measures 
        self.cleanPrice = fixedRateBond.cleanPrice()
        self.dirtyPrice = fixedRateBond.dirtyPrice()
        self.NPV = fixedRateBond.NPV()
        if isCalibration == True:
            self.spread_mkt = BondFunctions.zSpread(fixedRateBond, self.marketprice, self.spotCurve, 
                                                    self.paymentConvention,self.compound, self.freq)
            self.yield_mkt = fixedRateBond.bondYield(self.marketprice, self.paymentConvention,
                                                     self.compound,self.freq)
        else:
            self.spread_mkt = BondFunctions.zSpread(fixedRateBond, self.cleanPrice, self.spotCurve, 
                                                    self.paymentConvention,self.compound, self.freq)
            self.yield_mkt = fixedRateBond.bondYield(self.cleanPrice, self.paymentConvention,
                                                     self.compound,self.freq)
            
            
        self.bps_df = BondFunctions.bps(fixedRateBond,self.discountCurve)
        self.ModDur = BondFunctions.duration(fixedRateBond,self.yield_mkt,self.paymentConvention,
                                        self.compound,self.freq, Duration.Modified)
        self.MacDur = BondFunctions.duration(fixedRateBond,self.yield_mkt,self.paymentConvention,
                                        self.compound,self.freq, Duration.Macaulay)
        self.Convex = BondFunctions.convexity(fixedRateBond,self.yield_mkt,self.paymentConvention,
                                        self.compound,self.freq)
       
        
        # Generate Cashflow table 
        # fields = [
        #     'accrualDays', 'accrualEndDate', 'accrualPeriod', 'accrualStartDate',
        #     'amount',  'date', 'dayCounter', 'interestRate', 'nominal',  'rate'
        # ]

        # self.CF_Detail = []
        # for cf in list(map(as_fixed_rate_coupon, fixedRateBond.cashflows()))[:-1]:
        #     self.CF_Detail.append({fld: eval(f"cf.{fld}()") for fld in fields})
        # self.CF_Detail = pd.DataFrame(self.CF_Detail)
        
        self.CF = []
        dates = [ c.date() for c in fixedRateBond.cashflows() ]
        cfs = [ c.amount() for c in fixedRateBond.cashflows() ]
        self.CF = pd.DataFrame(zip(dates, cfs),columns = ('date','amount'), index = range(1,len(dates)+1))

    # Mehtod
    
    def CleanPrice_THEO(self):
        return self.cleanPrice
    
    def DirtyPrice_THEO(self):
        return self.dirtyPrice
        
    def Get_MktPrice(self):
        return self.marketprice
   
    def NPV_THEO(self):
        return self.NPV
    
    def Spread_mkt(self):
        return self.spread_mkt
    
    def Yield_mkt(self):
        return self.yield_mkt
    
    def PV01_df(self):
        return self.bps_df
    
    def DurMod(self):
        return self.ModDur
    
    def DurMac(self):
        return self.MacDur
    
    def Convexity(self):
        return self.Convex

    # def CashFlow_Detail(self):
    #     return self.CF_Detail
    
    def CashFlow(self):
        return self.CF

"""
   spread = QuoteHandle(SimpleQuote(z_spread))
   ts_spreaded1 = ZeroSpreadedTermStructure(spotCurveHandle, spread, Compounded, Semiannual)
   disCurveHandle = YieldTermStructureHandle(ts_spreaded1)

   discounts = [ts_spreaded1.discount(date) for date in spotDates]
   bondEngine = DiscountingBondEngine(disCurveHandle)

   fixedRateBond.setPricingEngine(bondEngine)
   print(fixedRateBond.cleanPrice()) 
"""