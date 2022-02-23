# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 10:09:58 2022

@author: joshchien
"""

from QuantLib import *

# Schedule(effectiveDate, terminationDate, tenor, calendar, convention, terminationDateConvention, rule, endOfMonth, firstDate=Date(), nextToLastDate=Date())

class qlSchedule(object):
    
    def __init__(self,effectiveDate, terminationDate, tenor, calendar, convention,
                 terminationDateConvention,rule):
        self.effectiveDate = effectiveDate
        self.terminationDate = terminationDate
        self.tenor = tenor
        self.calendar = calendar
        self.convention = convention
        self.convention = terminationDateConvention
        self.rule = rule
    
        self.schObj = Schedule(self.effectiveDate,self.terminationDate,self.tenor,self.calendar,
                               self.convention,self.convention,self.rule,False)
    
    def ScheduleObj(self):
        return self.schObj
        
