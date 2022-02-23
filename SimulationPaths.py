# Derivatives Pricing using QuantLib: An Introduction
# https://web.iima.ac.in/assets/snippets/workingpaperpdf/7473160052015-03-16.pdf
import pandas as pd
import numpy as np
import QuantLib as ql
import matplotlib.pyplot as plt

evaluationDate = ql.Date("2022-02-18", "%Y-%m-%d")
ql.Settings.instance().evaluationDate = evaluationDate

#%%
"""
Simulation Hull White One-Factor Model: dr(t) = (θ(t)-a*r(t))dt + σ*dW(t)
Where a and σ are constants, and θ(t) is chosen in order to fit the input term structure of interest rates.

QuantLib func.
ql.HullWhiteProcess(riskFreeTS, a, sigma)

"""

a, sigma = (0.1, 0.1) 
length = 4/12 # in year
timestep = int(360 * length)

forward_rate = 0.05
day_count = ql.Actual360()

# Build HullWhiteProcess
forwardQuote = ql.QuoteHandle(ql.SimpleQuote(forward_rate))
spot_curve = ql.FlatForward(evaluationDate, forwardQuote, day_count)
spot_curve_handle = ql.YieldTermStructureHandle(spot_curve)

hw_process = ql.HullWhiteProcess(spot_curve_handle, a, sigma)

# Monte Carlo method
rng = ql.GaussianRandomSequenceGenerator(ql.UniformRandomSequenceGenerator(timestep, ql.UniformRandomGenerator()))
seq = ql.GaussianPathGenerator(hw_process, length, timestep, rng, False)


def generate_paths(num_paths, timestep):
    arr = np.zeros((num_paths, timestep + 1))
    
    for i in range(num_paths):
        path = seq.next().value()
        
        time = [path.time(j) for j in range(len(path))]
        value = [path[j] for j in range(len(path))]
        arr[i, :] = np.array(value)
        
    return np.array(time), arr

num_paths = 20000
time, paths = generate_paths(num_paths, timestep)

for i in range(num_paths):
    plt.plot(time, paths[i, :], lw=0.8, alpha=0.6)
plt.title("Hull-White Short Rate Simulation")
plt.show()

#%% 單一資產
# QuantLib 金融計算——隨機過程之一般 Black Scholes 過程
# https://www.cnblogs.com/xuruilong100/p/10328476.html
"""
Simulation Heston Model: dS = rS(t)dt + σ(S,t)S(t)dWt

QuantLib func.
BlackScholesMertonProcess(initialValue, dividendTS, riskFreeTS, volTS)
    
"""

date = lambda d: ql.Date(d, "%Y-%m-%d")

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Local volatility using market data
strikes = [70.0, 80.0, 90.0, 100.0, 110.0, 120.0, 130.0]
expirations = [date("2022-07-01"), date("2022-09-01"), date("2022-12-01"), date("2023-06-01")]
vol_matrix = ql.Matrix(len(strikes), len(expirations))

# params are sigma_0, beta, vol_vol, rho
day_count = ql.Actual360()
spot = 114
sabr_params = [[0.4, 0.6, 0.4, -0.6],
               [0.4, 0.6, 0.4, -0.6],
               [0.4, 0.6, 0.4, -0.6],
               [0.4, 0.6, 0.4, -0.6]]

for j, expiration in enumerate(expirations):
    for i, strike in enumerate(strikes):
        tte = day_count.yearFraction(evaluationDate, expiration)
        vol_matrix[i][j] = ql.sabrVolatility(strike, spot, tte, *sabr_params[j])

print(np.array(vol_matrix)) 

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

calendar = ql.UnitedStates()
## BlackVarianceSurface(referenceDate, calendar, expirations, strikes, volMatrix, dayCounter)
implied_surface = ql.BlackVarianceSurface(evaluationDate, calendar, expirations, strikes, vol_matrix, day_count)
implied_surface.setInterpolation('bicubic')
vol_ts = ql.BlackVolTermStructureHandle(implied_surface)
# implied_surface.blackVol(0.5, 90)

riskFreeTS = ql.YieldTermStructureHandle(ql.FlatForward(evaluationDate, 0.05, day_count))
dividendTS = ql.YieldTermStructureHandle(ql.FlatForward(evaluationDate, 0, day_count))

process = ql.BlackScholesMertonProcess(ql.QuoteHandle(ql.SimpleQuote(spot)), dividendTS, riskFreeTS, vol_ts)


# Monte Carlo method
rng = ql.GaussianRandomSequenceGenerator(ql.UniformRandomSequenceGenerator(timestep, ql.UniformRandomGenerator()))
seq = ql.GaussianPathGenerator(process, length, timestep, rng, False)


def generate_paths(num_paths, timestep):
    arr = np.zeros((num_paths, timestep + 1))
    
    for i in range(num_paths):
        path = seq.next().value()
        
        time = [path.time(j) for j in range(len(path))]
        value = [path[j] for j in range(len(path))]
        arr[i, :] = np.array(value)
        
    return np.array(time), arr

num_paths = 2000
time, paths = generate_paths(num_paths, timestep)

for i in range(num_paths):
    plt.plot(time, paths[i, :], lw=0.8, alpha=0.6)
plt.title("Black Scholes Process Simulation")
plt.show()

#%% 多資產
# QuantLib-Python: Simulating Paths for Correlated 1-D Stochastic Processes
# http://mikejuniperhill.blogspot.com/2018/11/quantlib-python-simulating-paths-for.html

def GenerateCorrelatedPaths(processArray, timeGrid, nPaths):
    
    times = []; [times.append(timeGrid[t]) for t in range(len(timeGrid))]
    generator = ql.UniformRandomGenerator()
    nProcesses = processArray.size()
    nGridSteps = len(times) - 1 # deduct initial time (0.0)
    nSteps = nGridSteps * nProcesses
    sequenceGenerator = ql.UniformRandomSequenceGenerator(nSteps, generator)
    gaussianSequenceGenerator = ql.GaussianRandomSequenceGenerator(sequenceGenerator)
    multiPathGenerator = ql.GaussianMultiPathGenerator(processArray, times, gaussianSequenceGenerator)
    paths = np.zeros(shape = (nPaths, nProcesses, len(timeGrid)))

    # loop through number of paths
    for i in range(nPaths):
        # request multiPath, which contains the list of paths for each process
        multiPath = multiPathGenerator.next().value()
        # loop through number of processes
        for j in range(multiPath.assetNumber()):
            # request path, which contains the list of simulated prices for a process
            path = multiPath[j]
            # push prices to array
            paths[i, j, :] = np.array([path[k] for k in range(len(path))])
    return paths

# create two 1-D stochastic processes
process = []
nProcesses = 2
correlation = -1.0
names = ['equity_1', 'equity_2']
spot = [100.0, 100.0]
mue = [0.01, 0.01]
sigma = [0.10, 0.10]
[process.append(ql.GeometricBrownianMotionProcess(spot[i], mue[i], sigma[i])) for i in range(nProcesses)]
matrix = [[1.0, correlation], [correlation, 1.0]]

# create timegrid object and define number of paths
maturity = 1.0
nSteps = 90
timeGrid = ql.TimeGrid(maturity, nSteps)
nPaths = 20

# create StochasticProcessArray object
# (array of correlated 1-D stochastic processes)
processArray = ql.StochasticProcessArray(process, matrix)
# request simulated correlated paths for all processes
# result array dimensions: nPaths, nProcesses, len(timeGrid)
paths = GenerateCorrelatedPaths(processArray, timeGrid, nPaths)

# plot paths
f, subPlots = plt.subplots(nProcesses, sharex = True)
f.suptitle('Path simulations rho=' + str(correlation) + ', n=' + str(nPaths))

for i in range(nPaths):
    for j in range(nProcesses):
        subPlots[j].set_title(names[j])
        path = paths[i, j, :]
        subPlots[j].plot(timeGrid, path)








































