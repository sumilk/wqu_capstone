# -*- coding: utf-8 -*-
"""
Created on Sun Sep 20 12:01:05 2020

@author: my pc
"""

# %% Import
from pathlib import Path

import pandas as pd

# %% Constants
folder = Path(r"C:\Users\my pc\Downloads\Project_Code\Data")
(folder / "VaR_results") .mkdir(exist_ok=True)
(folder / "backtesting_results") .mkdir(exist_ok=True)
start_date = pd.Timestamp(2005, 1, 1)
backtesting_start_date = pd.Timestamp(2006, 1, 2)
window_size = 250
hp = 1
ci_var = 0.99
ci_es = 0.975
alpha_var = 1-ci_var
# %% Functions
def shortfall(values, weights=None, alpha=1-ci_es):
    """
    Expected shortfall at alpha significance level.
    
    Parameters
    ----------
    Values: pandas.Series
        The P&L series
    Weights: pandas.Series, optional
        The weights given to each P&L.
        if None provided, uniform weights are used.
    alpha: float, default 0.01
        The significance level
        
    Returns
    --------
    float 
        The expected shortfall of values
    """
    weights = weights or pd.Series([1] * len(values) )
    weights = weights / weights.sum()
    values = pd.DataFrame (
        {
            "Values": values.values,
            "Weights": weights.values
        }
    ). sort_values(by="Values", ascending=True).reset_index()
    values["Cumulative Weights"] = values["Weights"]. cumsum()
    index = values["Cumulative Weights"].searchsorted(alpha)
    
    if index == 0:
        return values["Values"] [0]
    else:
        values["Weights"][index] = (
            alpha - values["Cumulative Weights"][index-1]
        )
        values["Cumulative Weights"] [index] = alpha
        values = values[values["Cumulative Weights"] <= alpha]
        return (values["Values"] * values["Weights"]).sum()/alpha
        
# %% Load data and calculate shortfall
for filepath in folder.glob("*.csv"):
    print(filepath)
    data = pd.read_csv(filepath, parse_dates=["Date"])
    data = data.dropna(how="all"). reset_index(). sort_values(by="Date")
    
    # VaR calculation
    start_index = data["Date"]. searchsorted(start_date)
    end_index = start_index + window_size
    
    pnls = (
        data.set_index("Date")["Close"]
        .pct_change(hp) [start_index:end_index]
    )
    minimum = pnls.min()
    var = pnls.quantile(alpha_var)
    es = shortfall(pnls)
    pnls.name = "P&L"
    pnls["VaR"] = var
    pnls["ES"] = es
    pnls["Min"] = minimum
    pnls.to_csv(folder / "VaR_results" / filepath.name)
                           
    # Backtesting
    backtesting_start_index = data["Date"].searchsorted(backtesting_start_date)
    backtesting_end_index = data.index[-1]
    results = []
    for i in range(backtesting_start_index, backtesting_end_index):
        date = data["Date"][i]
        print(date, end="\r")
        pnls = data["Close"]. pct_change(hp)
        plstrip = pnls[i-window_size:i]
        var = plstrip.quantile(alpha_var)
        es = shortfall(plstrip)
        actual_pl = pnls[i]
        results.append([date, actual_pl, var, es])
     
    results = pd.DataFrame(results, columns=["Date", "PL", "VaR", "ES"])
    results["Exception_VaR"] = results["PL"] < results["VaR"] 
    results["Exception_ES"] = results["PL"] < results["ES"]
    results.to_csv(folder / "backtesting_results" / filepath.name, index = False)
                                             
 # for traffic light threshold - check the index where the value cross 0.95 (green) and 0.9999 (yellow)
 # from scipy.stats import binom
 # temp = pd.Series(binom.cdf(range(250), 250, 0.01), index=range(250))
