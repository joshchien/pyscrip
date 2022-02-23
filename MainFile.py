import pandas as pd
import numpy as np
import QuantLib as ql
import matplotlib.pyplot as plt

evaluationDate = ql.Date("2022-02-18", "%Y-%m-%d")
ql.Settings.instance().evaluationDate = evaluationDate

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Step 1: Input Variables & Maintain Calendar.
startDate = ql.Date("2022-02-23", "%Y-%m-%d")
endDate = ql.Date("2022-05-23", "%Y-%m-%d")
tenor = '1M'
notional = 1000000
CouponRates = 0.01

autocallBarrier = 1
accruedBarrier = 0.8
putStrike = 0.8
KnockInBarrier = 0.6
autoCallMemory = True
guaranteedPeriod = 1 
spread = 0

paymentDelay = '3D'
dayCounter =  ql.Actual360()
convention = ql.ModifiedFollowing
endDateConvention = ql.Following
rule = ql.DateGeneration.Forward

fixingCalendar = ql.UnitedStates(ql.UnitedStates.FederalReserve)
fundingCalendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)
paymentCalendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)

underlyings = ['F.O', 'AMD.O']
correlation = -1.0
corr_matrix = [[1.0, correlation], 
               [correlation, 1.0]]    

nProcesses = len(underlyings)
spots = [114, 115] # trade date Close

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Step 2: read Local volatilty => Fake data.
strikes = [70.0, 80.0, 90.0, 100.0, 110.0, 120.0, 130.0]
date_format = lambda d: ql.Date(d, "%Y-%m-%d")

expirations = [date_format("2022-07-01"), date_format("2022-09-01"), 
               date_format("2022-12-01"), date_format("2023-06-01")]
volMatrix = ql.Matrix(len(strikes), len(expirations))

# params are sigma_0, beta, vol_vol, rho
sabr_params = [[0.4, 0.6, 0.4, -0.6],
               [0.4, 0.6, 0.4, -0.6],
               [0.4, 0.6, 0.4, -0.6],
               [0.4, 0.6, 0.4, -0.6]]

for j, expiration in enumerate(expirations):
    for i, strike in enumerate(strikes):
        tte = dayCounter.yearFraction(evaluationDate, expiration)
        volMatrix[i][j] = ql.sabrVolatility(strike, spots[0], tte, *sabr_params[j])

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Step 3: Simulate Stock prices.

def GenerateCorrelatedPaths(processArray, maturity, nSteps, nPaths):
    nProcesses = processArray.size()
    
    timeGrid = ql.TimeGrid(maturity, nSteps)  # similar with np.linspace(0, maturity, num=nSteps)
    times = [timeGrid[t] for t in range(len(timeGrid))]
    
    nGridSteps = len(times) - 1 # deduct initial time (0.0)
    sequenceGenerator = ql.UniformRandomSequenceGenerator(nGridSteps * nProcesses, ql.UniformRandomGenerator())
    gaussianSequenceGenerator = ql.GaussianRandomSequenceGenerator(sequenceGenerator)
    
    multiPathGenerator = ql.GaussianMultiPathGenerator(processArray, times, gaussianSequenceGenerator)
    paths = np.zeros(shape = (nPaths, nProcesses, len(timeGrid)))

    
    for i in range(nPaths): # loop through number of paths
        multiPath = multiPathGenerator.next().value()
        
        for j in range(multiPath.assetNumber()): # loop through number of processes
            path = multiPath[j]
            paths[i, j, :] = np.array([path[k] for k in range(len(path))])\
                
    return paths

# Volatility Term Structure Handle
implied_surface = ql.BlackVarianceSurface(evaluationDate, fixingCalendar, expirations, strikes, volMatrix, dayCounter)
implied_surface.setInterpolation('bicubic')
volTS = ql.BlackVolTermStructureHandle(implied_surface)

# riskFree rate Term Structure Handle
riskFreeTS = ql.YieldTermStructureHandle(ql.FlatForward(evaluationDate, 0.05, dayCounter))

# dividend rate Term Structure Handle
dividendTS = ql.YieldTermStructureHandle(ql.FlatForward(evaluationDate, 0, dayCounter))

process = [ql.BlackScholesMertonProcess(ql.QuoteHandle(ql.SimpleQuote(spots[0])), 
                                        dividendTS, riskFreeTS, volTS),
           ql.BlackScholesMertonProcess(ql.QuoteHandle(ql.SimpleQuote(spots[1])), 
                                        dividendTS, riskFreeTS, volTS)]

# create StochasticProcessArray object
maturity = fixingCalendar.businessDaysBetween(startDate, endDate,  False, True) / 360 # in year
nSteps = int(maturity * 360)
nPaths = 2000

processArray = ql.StochasticProcessArray(process, corr_matrix)
paths = GenerateCorrelatedPaths(processArray, maturity, nSteps, nPaths)

# plot paths
f, subPlots = plt.subplots(nProcesses, sharex = True)
f.suptitle('Path simulations rho=' + str(correlation) + ', n=' + str(nPaths))

for i in range(nPaths):
    for j in range(nProcesses):
        subPlots[j].set_title(underlyings[j])
        path = paths[i, j, :]
        subPlots[j].plot(ql.TimeGrid(maturity, nSteps), path)
        
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Step 4: Build Schedules & read SOFR forward rates and discount rates.

sofrRates = [0.001, 0.002, 0.004]

tenors = ['0D', '7D', '28D', '91D', '182D', '364D', '2Y']
spotDates = [fixingCalendar.adjust(evaluationDate + ql.Period(t), ql.Following) for t in tenors]

discountRates = [1, 0.9999789, 0.9997392, 0.9990037, 0.9974138, 0.9966901, 0.9903279]

X, y = [d - evaluationDate for d in spotDates], discountRates
method = ql.LinearInterpolation(X, y)


schedule = ql.Schedule(startDate, endDate, ql.Period(tenor), fundingCalendar, convention, 
                       endDateConvention, rule, False)


schedules = pd.DataFrame(columns=['PaymentDate', 'StartDate', 'EndDate', 'fundingDays', 'equityDays'])
for i, end in enumerate(list(schedule)[1:]):
    start, end = schedule[i], schedule[i+1]
    paymentDate = paymentCalendar.advance(end, ql.Period(paymentDelay), convention, False)
    equityRangedDays = fixingCalendar.businessDaysBetween(start, end, False, True)
    fundingAccruedDays = end - start
    sofr_rate = sofrRates[i]
    dfs = method(paymentDate - evaluationDate, allowExtrapolation=True)
    
    schedules = schedules.append(
                {'PaymentDate': paymentDate,
                 'StartDate': start,
                 'EndDate': end,
                 'fundingDays': fundingAccruedDays,
                 'equityDays': equityRangedDays,
                 'SOFRIndex': sofr_rate,
                 'discounts': dfs
                 }, ignore_index=True)
          
    
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Step 5: Get price

def Guaranteed_periods(simStocks, initStocks, notional, CouponRates, 
                       spread, sofr_rate, fundingDays):
    x_perfs = np.multiply(simStocks.T, 1/np.array(initStocks))
    totalBuinessDays = x_prefs.shape[0]
    
    # funding leg
    funding = notional * spread * (fundingDays / 360) + notional * sofr_rate 
    # equity leg
    equity = notional * CouponRates * (totalBuinessDays/totalBuinessDays)
    
    return {'fundingLeg': funding, 'equityLeg': equity}


def AutoCall_period(simStocks, initStocks, notional, CouponRates, 
                    spread, sofr_rate, fundingDays, memory=True):
    #  x_perfs = np.multiply(paths[0,:,:].T, 1/np.array(spots))
    x_perfs = np.multiply(simStocks.T, 1/np.array(initStocks))
    totalBuinessDays = x_perfs.shape[0]
    nAssets = x_perfs.shape[1] # 2
    
    # Auto Call Examined. 錯: 需提前離場
    autoCall = x_perfs >= autocallBarrier
    date_memo = 0 
    if memory: 
        for day in range(totalBuinessDays):
            if autoCall[day, 0] == True: autoCall[day+1:, 0] = True
            if autoCall[day, 1] == True: autoCall[day+1:, 1] = True
        
    else:
        for day in range(totalBuinessDays):
            if autoCall[day, 0] == True: autoCall[day+1:, 0] = True
            if autoCall[day, 1] == True: autoCall[day+1:, 1] = True
            if autoCall[day+1:, :].all(): 
                x_ko = True
                break
        x_ko = (False or x_ko) if memory else False
        
    
    # Knock In Examined.
    KnockIn = x_perfs <= KnockInBarrier   # 任一資產觸碰下限價格
    x_ki = True if np.sum(KnockIn) > 0 else False
    
    # Accrued Days Examined.
    accruedDay = x_perfs >= accruedBarrier
    accruedDay = np.sum(accruedDay, axis=1)
    accruedDays = len(np.argwhere(accruedDay == nAssets))
        
    # funding leg
    funding = notional * spread * (fundingDays / 360) + notional * sofr_rate 
    # equity leg
    equity = notional * CouponRates * (accruedDays/totalBuinessDays)
    
    return {'fundingLeg': funding, 'equityLeg': equity}


df = pd.DataFrame(columns=['fundingLeg', 'equityLeg'])
x_ko = False; x_ki = False
e = 1 

for period in range(len(schedules)):
    s = e
    e = e + schedules.loc[period, 'equityDays']
    fundingDays = schedules.loc[period, 'fundingDays']
    sofr_rate = schedules.loc[period, 'SOFRIndex']
    discounts = schedules.loc[period, 'discounts']
    
    for simStocks in paths[0, :, s:e]:  
        if period <= guaranteedPeriod:
            Guaranteed_periods

        
Guaranteed_periods(simStocks, initStocks, notional, CouponRates, spread, sofr_rate, fundingDays)



 schedules = schedules.append(
             {'PaymentDate': paymentDate,
              'StartDate': start,
              'EndDate': end,
              'fundingDays': fundingAccruedDays,
              'equityDays': equityRangedDays,
              'SOFRIndex': sofr_rate,
              'discounts': dfs
              }, ignore_index=True)




































 