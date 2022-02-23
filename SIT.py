# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 11:35:16 2022

@author: joshchien
"""
#%%
from qlFixedRateBond import *
from qlSchedule import*
from QuantLib import *

# DateGeneration.Backward  Bond Type: Backward   Derivative Type: Forward

IDSchedule = qlSchedule(Date(29, 10, 2020), Date(29, 10, 2030), Period(Semiannual), UnitedStates(UnitedStates.NYSE),
                        ModifiedFollowing, Following, DateGeneration.Backward)
schObj = IDSchedule.ScheduleObj()

mkt = 91.833
settlementDays = 2
faceAmount = 1000000
coupon = [0.012]
paymentConvention = Thirty360() #ql Obj
#schedule_backward #ql Obj
#Semiannual  #ql obj
#Compounded  #ql obj
isCalibration = True
ISINs = qlFixedRateBond(settlementDays,faceAmount,schObj,coupon,
                        paymentConvention,spotCurve,discountCurve,mkt,Semiannual,Compounded,True)
#%%
schedule_backward = Schedule(Date(29, 10, 2020), Date(29, 10, 2030), Period(Semiannual), UnitedStates(UnitedStates.NYSE),
                             ModifiedFollowing, Following, DateGeneration.Backward, True)
