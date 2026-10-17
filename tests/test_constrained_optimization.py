"""Tests for the team feature "Constrained optimization" (optimization.py).

Run from the project folder with:
    python -m pytest tests -v

All tests use the bundled sample data (source="sample"), so they give the same
result on every computer and do not need an internet connection.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from green_robo_advisor.data_module import get_etf_metadata, load_dataset
from green_robo_advisor.optimization import (
    METHODS,
    InfeasibleSettingsError,
    OptimizationError,
    optimize_portfolio,
)
from green_robo_advisor.prototype_backup import optimization as old_optimization
from green_robo_advisor.questionnaire import score_to_profile

TOL = 1e-6


@pytest.fixture(scope="module")
def returns() -> pd.DataFrame:
    return load_dataset(start="2020-01-01", source="sample")["asset_returns"]


@pytest.fixture(scope="module")
def esg_scores() -> pd.Series:
    return get_etf_metadata().set_index("ticker")["esg_quality_score"]


BALANCED = score_to_profile(10)  # target return 6 %, target risk 10 %


# 1. The invariants the handout asks for: weights sum to one and respect the bounds
@pytest.mark.parametrize("method", METHODS)
def test_weights_sum_to_one_and_respect_bounds(returns, esg_scores, method):
    result = optimize_portfolio(
        returns, method, BALANCED.target_return, BALANCED.target_risk,
        min_weight=0.05, max_weight=0.40, esg_scores=esg_scores,
    )
    w = result["weights"]
    assert abs(w.sum() - 1.0) < TOL
    assert (w >= 0.05 - TOL).all()
    assert (w <= 0.40 + TOL).all()
    assert all(result["checks"].values())


# 2. The ESG floor is respected and actually changes the solution
def test_esg_floor_is_respected_and_changes_weights(returns, esg_scores):
    common = dict(returns=returns, method="max_sharpe", target_return=0.06, target_risk=0.10,
                  esg_scores=esg_scores)
    without_floor = optimize_portfolio(**common)
    with_floor = optimize_portfolio(**common, esg_floor=8.0)
    assert without_floor["esg_score"] < 8.0              # the floor is binding ...
    assert with_floor["esg_score"] >= 8.0 - TOL          # ... and it is met
    assert not np.allclose(without_floor["weights"], with_floor["weights"], atol=1e-3)


# 3. Infeasible settings give a readable error instead of a cryptic solver message
@pytest.mark.parametrize(
    "settings, expected_text",
    [
        ({"min_weight": 0.25}, "more than 100%"),          # 5 x 25 % = 125 %
        ({"max_weight": 0.15}, "cannot reach 100%"),       # 5 x 15 % = 75 %
        ({"esg_floor": 9.0}, "ESG floor"),                 # above every ETF's score
    ],
)
def test_infeasible_settings_are_explained(returns, esg_scores, settings, expected_text):
    with pytest.raises(InfeasibleSettingsError, match=expected_text):
        optimize_portfolio(returns, "max_sharpe", 0.06, 0.10, esg_scores=esg_scores, **settings)


def test_unreachable_target_return_is_explained(returns):
    aggressive = score_to_profile(20)  # target return 10 % > best ETF in the sample data
    with pytest.raises(InfeasibleSettingsError, match="target return"):
        optimize_portfolio(returns, "min_variance", aggressive.target_return, aggressive.target_risk)


def test_infeasible_error_is_still_an_optimization_error():
    # old code that catches OptimizationError must keep working
    assert issubclass(InfeasibleSettingsError, OptimizationError)


# 4. Module contract: old calls give the old result and the old keys still exist
@pytest.mark.parametrize("method", ["min_variance", "max_return", "max_sharpe"])
def test_default_settings_reproduce_the_old_prototype(returns, method):
    old = old_optimization.optimize_portfolio(returns, method, BALANCED.target_return, BALANCED.target_risk)
    new = optimize_portfolio(returns, method, BALANCED.target_return, BALANCED.target_risk)
    assert np.allclose(old["weights"], new["weights"], atol=1e-2)
    for key in ["weights", "expected_return", "expected_volatility", "mu", "sigma"]:
        assert key in new


# 5. Risk contributions add up to total volatility; risk parity equalizes them
def test_risk_contributions_add_up(returns):
    result = optimize_portfolio(returns, "risk_parity", 0.06, 0.10)
    assert abs(result["risk_contributions"].sum() - result["expected_volatility"]) < TOL
    assert abs(result["risk_contribution_share"].sum() - 1.0) < TOL
    assert np.allclose(result["risk_contribution_share"], 1 / len(returns.columns), atol=1e-3)


# 6. Higher risk aversion in mean-variance mode should not increase volatility
def test_higher_risk_aversion_lowers_volatility(returns):
    vols = [
        optimize_portfolio(returns, "mean_variance", 0.06, 0.10, risk_aversion=ra)["expected_volatility"]
        for ra in (0.5, 3.0, 8.0)
    ]
    assert vols[0] >= vols[1] >= vols[2]
