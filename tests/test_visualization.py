"""Tests for the visualization enhancement (drawdown + performance summary)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from green_robo_advisor.data_module import load_dataset
from green_robo_advisor.optimization import optimize_portfolio
from green_robo_advisor.visualization import (
    cumulative_returns,
    drawdown,
    max_drawdown,
    performance_summary,
    portfolio_returns,
)


@pytest.fixture(scope="module")
def series():
    data = load_dataset(start="2020-01-01", source="sample")
    weights = optimize_portfolio(data["asset_returns"], "max_sharpe", 0.06, 0.10)["weights"]
    return portfolio_returns(data["asset_returns"], weights), data["benchmark_returns"].squeeze()


def test_drawdown_is_never_positive_and_uses_same_dates(series):
    portfolio, _ = series
    dd = drawdown(portfolio)
    assert (dd <= 1e-12).all()             # checklist: drawdown is at or below zero
    assert dd.index.equals(portfolio.index)


def test_max_drawdown_on_a_known_example():
    # price path 100 -> 120 -> 90 -> 110: worst fall is 120 -> 90 = -25 %
    prices = pd.Series([100.0, 120.0, 90.0, 110.0])
    log_returns = np.log(prices / prices.shift(1)).dropna()
    assert max_drawdown(log_returns) == pytest.approx(-0.25)


def test_growth_starts_near_one(series):
    portfolio, _ = series
    assert cumulative_returns(portfolio).iloc[0] == pytest.approx(1.0, abs=0.05)


def test_summary_table_is_consistent(series):
    portfolio, benchmark = series
    summary = performance_summary(portfolio, benchmark)
    assert list(summary.columns) == ["Portfolio", "Benchmark"]
    for column in summary.columns:
        col = summary[column]
        assert col["Annual volatility"] > 0
        assert col["Max drawdown"] <= 0
        assert col["Sharpe ratio"] == pytest.approx(col["Annual log return"] / col["Annual volatility"])


# --- V3: correlation heatmap -----------------------------------------------------------
from green_robo_advisor.visualization import correlation_matrix


def test_correlation_matrix_is_valid():
    returns = load_dataset(start="2020-01-01", source="sample")["asset_returns"]
    corr = correlation_matrix(returns)
    assert np.allclose(np.diag(corr), 1.0)                 # every ETF is perfectly correlated with itself
    assert np.allclose(corr.values, corr.values.T)         # symmetric
    assert ((corr.values >= -1) & (corr.values <= 1)).all()
    assert corr.loc["ESGU", "ESGD"] > corr.loc["ESGU", "SUSC"]  # equities move together more than equity/bond
