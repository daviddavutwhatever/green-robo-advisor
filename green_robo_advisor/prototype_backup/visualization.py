"""Module 4: create simple charts for portfolio results using log returns."""
from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import TRADING_DAYS



def portfolio_returns(asset_returns: pd.DataFrame, weights: pd.Series) -> pd.Series:
    """Daily portfolio log returns for a daily rebalanced portfolio.

    Input asset returns are daily log returns. For exact daily portfolio aggregation,
    we first convert them to simple returns, aggregate across assets with the weights,
    and then convert the portfolio return back to a log return.
    """
    aligned_weights = weights.reindex(asset_returns.columns)
    asset_simple_returns = np.exp(asset_returns) - 1.0
    portfolio_simple_returns = (asset_simple_returns * aligned_weights).sum(axis=1)
    return np.log1p(portfolio_simple_returns)



def cumulative_returns(log_returns: pd.Series) -> pd.Series:
    """Growth of 1 monetary unit from daily log returns."""
    return np.exp(log_returns.cumsum())



def rolling_volatility(log_returns: pd.Series, window: int = 21) -> pd.Series:
    """Rolling annualized volatility based on daily log returns."""
    return log_returns.rolling(window).std() * (TRADING_DAYS ** 0.5)



def create_plots(
    asset_returns: pd.DataFrame,
    benchmark_returns: pd.Series,
    weights: pd.Series,
    output_dir: str = "charts",
) -> dict:
    os.makedirs(output_dir, exist_ok=True)

    portfolio = portfolio_returns(asset_returns, weights)
    benchmark_series = benchmark_returns.squeeze()

    portfolio_cum = cumulative_returns(portfolio)
    benchmark_cum = cumulative_returns(benchmark_series)

    portfolio_roll = rolling_volatility(portfolio)
    benchmark_roll = rolling_volatility(benchmark_series)

    results = {
        "portfolio_returns": portfolio,
        "benchmark_returns": benchmark_series,
        "portfolio_cumulative": portfolio_cum,
        "benchmark_cumulative": benchmark_cum,
        "portfolio_rolling_vol": portfolio_roll,
        "benchmark_rolling_vol": benchmark_roll,
    }

    plt.figure(figsize=(10, 5))
    plt.plot(portfolio_cum.index, portfolio_cum.values, label="Portfolio")
    plt.plot(benchmark_cum.index, benchmark_cum.values, label="Benchmark")
    plt.title("Cumulative Returns")
    plt.xlabel("Date")
    plt.ylabel("Growth of $1")
    plt.legend()
    plt.tight_layout()
    cumulative_path = f"{output_dir}/cumulative_returns.png"
    plt.savefig(cumulative_path)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.plot(portfolio_roll.index, portfolio_roll.values, label="Portfolio")
    plt.plot(benchmark_roll.index, benchmark_roll.values, label="Benchmark")
    plt.title("Rolling Annualized Volatility (21 trading days)")
    plt.xlabel("Date")
    plt.ylabel("Volatility")
    plt.legend()
    plt.tight_layout()
    rolling_path = f"{output_dir}/rolling_volatility.png"
    plt.savefig(rolling_path)
    plt.close()

    results["cumulative_plot_path"] = cumulative_path
    results["rolling_plot_path"] = rolling_path
    return results
