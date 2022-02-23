# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 10:18:03 2022

@author: joshchien
"""

from QuantLib import *

class qlCurve(object):
    def _init_(self,day, faceAmount, scheduleobj, coupon, paymentConvention,
               curvname,marketprice,freq):



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