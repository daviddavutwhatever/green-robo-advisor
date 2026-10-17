"""Module 4: create simple charts for portfolio results using log returns.

Team enhancements in this module (3):
- V1 Drawdown: drawdown() shows how far below its previous peak the portfolio is on every
     day (always <= 0); max_drawdown() is the worst peak-to-trough loss.
- V2 Performance summary: performance_summary() compares portfolio and benchmark
     (annual return, volatility, Sharpe ratio, max drawdown, worst day, growth of 1).
- V3 Correlation heatmap: correlation_matrix() shows how strongly the ETFs move together,
     which explains why diversification works (or does not).
create_plots() additionally saves drawdown and correlation charts; its old keys are unchanged.
"""
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



def drawdown(log_returns: pd.Series) -> pd.Series:
    """V1: daily drawdown = value / running peak - 1 (0 at a new high, negative below it)."""
    growth = cumulative_returns(log_returns)
    running_peak = growth.cummax()
    return growth / running_peak - 1.0



def max_drawdown(log_returns: pd.Series) -> float:
    """V1: the largest peak-to-trough loss over the period (a negative number)."""
    return float(drawdown(log_returns).min())



def performance_summary(
    portfolio_log_returns: pd.Series,
    benchmark_log_returns: pd.Series,
    risk_free_rate: float = 0.0,
) -> pd.DataFrame:
    """V2: key realised statistics for portfolio and benchmark on the same dates."""
    rows = {}
    for name, series in {"Portfolio": portfolio_log_returns, "Benchmark": benchmark_log_returns}.items():
        annual_return = float(series.mean() * TRADING_DAYS)
        annual_vol = float(series.std() * TRADING_DAYS ** 0.5)
        rows[name] = {
            "Annual log return": annual_return,
            "Annual volatility": annual_vol,
            "Sharpe ratio": (annual_return - risk_free_rate) / annual_vol if annual_vol > 0 else np.nan,
            "Max drawdown": max_drawdown(series),
            "Worst day": float(np.expm1(series.min())),
            "Growth of 1": float(cumulative_returns(series).iloc[-1]),
        }
    return pd.DataFrame(rows)



def correlation_matrix(asset_returns: pd.DataFrame) -> pd.DataFrame:
    """V3: pairwise correlation of daily log returns (+1 = move together, 0 = unrelated)."""
    return asset_returns.corr()



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

    portfolio_dd = drawdown(portfolio)
    benchmark_dd = drawdown(benchmark_series)
    results["portfolio_drawdown"] = portfolio_dd
    results["benchmark_drawdown"] = benchmark_dd
    results["summary"] = performance_summary(portfolio, benchmark_series)

    plt.figure(figsize=(10, 5))
    plt.plot(portfolio_dd.index, portfolio_dd.values, label="Portfolio")
    plt.plot(benchmark_dd.index, benchmark_dd.values, label="Benchmark")
    plt.title("Drawdown (distance below the previous peak)")
    plt.xlabel("Date")
    plt.ylabel("Drawdown")
    plt.legend()
    plt.tight_layout()
    drawdown_path = f"{output_dir}/drawdown.png"
    plt.savefig(drawdown_path)
    plt.close()

    corr = correlation_matrix(asset_returns)
    results["correlation"] = corr
    fig, ax = plt.subplots(figsize=(6, 5))
    image = ax.imshow(corr.values, cmap="Greens", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)), corr.columns)
    ax.set_yticks(range(len(corr)), corr.index)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center",
                    color="white" if corr.values[i, j] > 0.6 else "black")
    fig.colorbar(image, ax=ax)
    ax.set_title("Correlation of daily returns")
    fig.tight_layout()
    correlation_path = f"{output_dir}/correlation.png"
    fig.savefig(correlation_path)
    plt.close(fig)

    results["cumulative_plot_path"] = cumulative_path
    results["rolling_plot_path"] = rolling_path
    results["drawdown_plot_path"] = drawdown_path
    results["correlation_plot_path"] = correlation_path
    return results
