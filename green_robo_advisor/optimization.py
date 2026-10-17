"""Module 3: portfolio optimization methods using daily log returns.

Team enhancements in this module (5):
- O1 Weight bounds: every method can respect a minimum and maximum weight per ETF.
- O2 ESG floor: every method can respect a minimum weighted ESG score.
- O3 Mean-variance: a new method trades off return against risk with a risk-aversion value.
- O4 Feasibility check: settings are checked BEFORE optimizing (readable explanation instead
     of a cryptic solver message) and the result is verified AFTER optimizing.
- O5 Risk contributions: the result shows each ETF's share of total portfolio risk.
The result dictionary keeps all old keys; new keys are only added.

Old calls such as optimize_portfolio(returns, "max_sharpe", 0.06, 0.10) still work and
give the same weights as before, because all new parameters have neutral defaults.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import linprog, minimize

from .config import TRADING_DAYS

TOLERANCE = 1e-6  # numerical slack used when checking constraints
METHODS = ["min_variance", "max_return", "max_sharpe", "risk_parity", "mean_variance"]


class OptimizationError(RuntimeError):
    """The solver ran but did not find a valid portfolio."""


class InfeasibleSettingsError(OptimizationError):
    """The chosen settings contradict each other, so no portfolio can satisfy them.

    It is a subclass of OptimizationError, so old code that catches
    OptimizationError keeps working.
    """


@dataclass
class PortfolioConstraints:
    """All conditions a portfolio must satisfy, collected in one place.

    min_weight / max_weight: bounds for EVERY ETF (0.05 = at least 5 %).
    esg_scores: one ESG score per ticker (pandas Series with tickers as index).
    esg_floor: minimum weighted ESG score of the portfolio, or None for "no floor".
    """

    min_weight: float = 0.0
    max_weight: float = 1.0
    esg_scores: pd.Series | None = None
    esg_floor: float | None = None


# ---------------------------------------------------------------------------
# Basic statistics (unchanged)
# ---------------------------------------------------------------------------

def annualized_statistics(log_returns: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """Annualized mean vector and covariance matrix based on daily log returns."""
    mu = log_returns.mean() * TRADING_DAYS
    Sigma = log_returns.cov() * TRADING_DAYS  # Variance-Covariance Matrix
    return mu, Sigma


def portfolio_return(weights: np.ndarray, mu: pd.Series) -> float:
    """Expected annual portfolio log return."""
    return float(np.dot(weights, mu.values))


def portfolio_volatility(weights: np.ndarray, sigma: pd.DataFrame) -> float:
    return float(np.sqrt(weights @ sigma.values @ weights))


def negative_sharpe(
    weights: np.ndarray,
    mu: pd.Series,
    sigma: pd.DataFrame,
    risk_free_rate: float = 0.0,
) -> float:
    """Negative Sharpe ratio using annualized log-return moments."""
    vol = portfolio_volatility(weights, sigma)
    if vol <= 0:
        return 1e6
    ret = portfolio_return(weights, mu)
    return -((ret - risk_free_rate) / vol)


def risk_contributions(weights: np.ndarray, sigma: pd.DataFrame) -> np.ndarray:
    """O5: how much each ETF adds to total portfolio volatility (the values sum to the volatility)."""
    vol = portfolio_volatility(weights, sigma)
    if vol <= 0:
        return np.zeros_like(weights)
    marginal = sigma.values @ weights / vol
    return weights * marginal


def portfolio_esg_score(weights: np.ndarray, esg_scores: pd.Series) -> float:
    """O2: weighted average ESG score: sum of weight * score."""
    return float(np.dot(weights, esg_scores.values))


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------

def _aligned_esg(constraints: PortfolioConstraints, tickers: list[str]) -> pd.Series | None:
    """Return ESG scores in the same order as the return columns (or None)."""
    if constraints.esg_scores is None:
        if constraints.esg_floor is not None:
            raise InfeasibleSettingsError("An ESG floor was set, but no ESG scores were provided.")
        return None
    missing = [t for t in tickers if t not in constraints.esg_scores.index]
    if missing:
        raise InfeasibleSettingsError(f"No ESG score is available for: {missing}.")
    return constraints.esg_scores.reindex(tickers).astype(float)


def _base_constraints(esg: pd.Series | None = None, esg_floor: float | None = None) -> list[dict]:
    """Weights sum to one, and (optionally) the weighted ESG score is at least the floor."""
    rules = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    if esg is not None and esg_floor is not None:
        rules.append({"type": "ineq", "fun": lambda w: portfolio_esg_score(w, esg) - esg_floor})
    return rules


def _base_bounds(n_assets: int, min_weight: float = 0.0, max_weight: float = 1.0) -> tuple:
    """O1: the same (min, max) range for every ETF."""
    return tuple((min_weight, max_weight) for _ in range(n_assets))


def _initial_guess(n_assets: int) -> np.ndarray:
    return np.repeat(1.0 / n_assets, n_assets)


def _solve(objective, n_assets: int, c: PortfolioConstraints, esg, extra: list[dict], name: str) -> np.ndarray:
    """Run the SLSQP solver with the common bounds and constraints."""
    result = minimize(
        fun=objective,
        x0=_initial_guess(n_assets),
        method="SLSQP",
        bounds=_base_bounds(n_assets, c.min_weight, c.max_weight),
        constraints=_base_constraints(esg, c.esg_floor) + extra,
        options={"maxiter": 1000, "ftol": 1e-12},
    )
    if not result.success:
        raise OptimizationError(f"{name} failed: {result.message}")
    # Remove tiny numerical noise such as -1e-17, then make the weights sum to exactly one.
    weights = np.clip(result.x, c.min_weight, c.max_weight)
    return weights / weights.sum()


def _linear_range(values: np.ndarray, c: PortfolioConstraints, esg) -> tuple[float, float]:
    """Smallest and largest possible value of sum(w * values) under the constraints.

    Used to find, e.g., the highest achievable return or ESG score. This is a
    linear programme, so it is solved exactly with scipy's linprog.
    """
    n = len(values)
    a_ub, b_ub = None, None
    if esg is not None and c.esg_floor is not None:
        a_ub, b_ub = [-esg.values], [-c.esg_floor]  # -esg.w <= -floor  <=>  esg.w >= floor
    common = dict(
        A_ub=a_ub, b_ub=b_ub, A_eq=[np.ones(n)], b_eq=[1.0],
        bounds=_base_bounds(n, c.min_weight, c.max_weight), method="highs",
    )
    low = linprog(values, **common)
    high = linprog(-values, **common)
    return float(low.fun), float(-high.fun)


# ---------------------------------------------------------------------------
# Feasibility check: "can ANY portfolio satisfy these settings?"
# ---------------------------------------------------------------------------

def check_feasibility(  # O4
    mu: pd.Series,
    sigma: pd.DataFrame,
    constraints: PortfolioConstraints,
    method: str,
    target_return: float | None = None,
    target_risk: float | None = None,
) -> None:
    """Raise InfeasibleSettingsError with a plain-language reason if settings contradict each other."""
    n = len(mu)
    lo, hi = constraints.min_weight, constraints.max_weight

    # 1. Weight bounds
    if not 0.0 <= lo <= hi <= 1.0:
        raise InfeasibleSettingsError(
            f"Weight bounds must satisfy 0 <= min ({lo:.0%}) <= max ({hi:.0%}) <= 100%."
        )
    if n * lo > 1.0 + TOLERANCE:
        raise InfeasibleSettingsError(
            f"With {n} ETFs, a minimum weight of {lo:.0%} needs {n * lo:.0%} in total, "
            f"which is more than 100%. Lower the minimum weight to at most {1 / n:.0%}."
        )
    if n * hi < 1.0 - TOLERANCE:
        raise InfeasibleSettingsError(
            f"With {n} ETFs, a maximum weight of {hi:.0%} allows only {n * hi:.0%} in total, "
            f"so the weights cannot reach 100%. Raise the maximum weight to at least {1 / n:.0%} "
            f"or select more ETFs."
        )

    # 2. ESG floor
    esg = _aligned_esg(constraints, list(mu.index))
    if esg is not None and constraints.esg_floor is not None:
        no_floor = PortfolioConstraints(lo, hi, esg, None)
        _, best_esg = _linear_range(esg.values, no_floor, esg)
        if constraints.esg_floor > best_esg + TOLERANCE:
            raise InfeasibleSettingsError(
                f"The ESG floor of {constraints.esg_floor:.2f} cannot be reached. With the current ETFs "
                f"and weight bounds, the highest possible portfolio ESG score is {best_esg:.2f}."
            )

    # 3. Return / risk targets of the methods that use them
    if method == "min_variance" and target_return is not None:
        low_ret, high_ret = _linear_range(mu.values, constraints, esg)
        if not low_ret - TOLERANCE <= target_return <= high_ret + TOLERANCE:
            raise InfeasibleSettingsError(
                f"The target return of {target_return:.2%} is outside what these ETFs can deliver "
                f"under the current constraints (possible range: {low_ret:.2%} to {high_ret:.2%}). "
                f"Choose another profile, another method, or relax the constraints."
            )
    if method == "max_return" and target_risk is not None:
        lowest_weights = _solve(
            lambda w: portfolio_volatility(w, sigma) ** 2, n, constraints, esg, [], "Minimum risk check"
        )
        lowest_vol = portfolio_volatility(lowest_weights, sigma)
        if target_risk < lowest_vol - TOLERANCE:
            raise InfeasibleSettingsError(
                f"The target risk of {target_risk:.2%} is below the lowest achievable volatility "
                f"of {lowest_vol:.2%} under the current constraints."
            )


def validate_weights(  # O4
    weights: np.ndarray, constraints: PortfolioConstraints, esg) -> dict:
    """Check the invariants after optimizing. Returns a dict of True/False results."""
    checks = {
        "weights_sum_to_one": abs(float(np.sum(weights)) - 1.0) <= TOLERANCE,
        "min_weight_respected": bool(np.all(weights >= constraints.min_weight - TOLERANCE)),
        "max_weight_respected": bool(np.all(weights <= constraints.max_weight + TOLERANCE)),
    }
    if esg is not None and constraints.esg_floor is not None:
        checks["esg_floor_respected"] = portfolio_esg_score(weights, esg) >= constraints.esg_floor - TOLERANCE
    return checks


# ---------------------------------------------------------------------------
# Optimization methods (same names as before, new optional `constraints` argument)
# ---------------------------------------------------------------------------

def min_variance_for_target_return(mu, sigma, target_return, constraints=None, esg=None) -> np.ndarray:
    """Minimum-variance portfolio for a target annual log return."""
    c = constraints or PortfolioConstraints()
    extra = [{"type": "eq", "fun": lambda w: portfolio_return(w, mu) - target_return}]
    return _solve(lambda w: portfolio_volatility(w, sigma) ** 2, len(mu), c, esg, extra, "Min-variance")


def max_return_for_risk(mu, sigma, target_risk, constraints=None, esg=None) -> np.ndarray:
    """Maximum expected annual log return for a target annual volatility."""
    c = constraints or PortfolioConstraints()
    extra = [{"type": "ineq", "fun": lambda w: target_risk - portfolio_volatility(w, sigma)}]
    return _solve(lambda w: -portfolio_return(w, mu), len(mu), c, esg, extra, "Max return")


def max_sharpe_ratio(mu, sigma, risk_free_rate=0.0, constraints=None, esg=None) -> np.ndarray:
    c = constraints or PortfolioConstraints()
    return _solve(
        lambda w: negative_sharpe(w, mu, sigma, risk_free_rate=risk_free_rate),
        len(mu), c, esg, [], "Max Sharpe",
    )


def risk_parity(sigma, constraints=None, esg=None) -> np.ndarray:
    c = constraints or PortfolioConstraints()
    n_assets = len(sigma)

    def objective(w: np.ndarray) -> float:
        rc = risk_contributions(w, sigma)
        target = np.repeat(np.sum(rc) / n_assets, n_assets)
        return float(np.sum((rc - target) ** 2))

    return _solve(objective, n_assets, c, esg, [], "Risk parity")


def mean_variance(mu, sigma, risk_aversion=3.0, constraints=None, esg=None) -> np.ndarray:
    """O3: maximize  expected return - (risk_aversion / 2) * variance.

    Low risk aversion (0.5) -> return matters most; high risk aversion (8) -> variance matters most.
    """
    if risk_aversion <= 0:
        raise InfeasibleSettingsError("Risk aversion must be greater than zero.")
    c = constraints or PortfolioConstraints()

    def objective(w: np.ndarray) -> float:
        return -(portfolio_return(w, mu) - 0.5 * risk_aversion * portfolio_volatility(w, sigma) ** 2)

    return _solve(objective, len(mu), c, esg, [], "Mean-variance")


# ---------------------------------------------------------------------------
# Public entry point used by app.py and run_demo.py
# ---------------------------------------------------------------------------

def optimize_portfolio(
    returns: pd.DataFrame,
    method: str,
    target_return: float,
    target_risk: float,
    risk_free_rate: float = 0.0,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
    esg_scores: pd.Series | None = None,
    esg_floor: float | None = None,
    risk_aversion: float = 3.0,
) -> dict:
    """Optimize a portfolio from daily log returns.

    The first five parameters are the original contract. The new keyword
    parameters are optional; their defaults reproduce the old prototype.
    """
    mu, sigma = annualized_statistics(returns)
    constraints = PortfolioConstraints(min_weight, max_weight, esg_scores, esg_floor)
    method = method.lower().strip()
    if method not in METHODS:
        raise ValueError(f"Unknown method: {method}")

    check_feasibility(mu, sigma, constraints, method, target_return, target_risk)
    esg = _aligned_esg(constraints, list(returns.columns))

    if method == "min_variance":
        weights = min_variance_for_target_return(mu, sigma, target_return, constraints, esg)
    elif method == "max_return":
        weights = max_return_for_risk(mu, sigma, target_risk, constraints, esg)
    elif method == "max_sharpe":
        weights = max_sharpe_ratio(mu, sigma, risk_free_rate, constraints, esg)
    elif method == "risk_parity":
        weights = risk_parity(sigma, constraints, esg)
    else:
        weights = mean_variance(mu, sigma, risk_aversion, constraints, esg)

    checks = validate_weights(weights, constraints, esg)
    if not all(checks.values()):
        failed = [name for name, ok in checks.items() if not ok]
        raise OptimizationError(f"The solver returned weights that violate: {failed}")

    volatility = portfolio_volatility(weights, sigma)
    rc = risk_contributions(weights, sigma)
    tickers = returns.columns
    return {
        # --- original keys (unchanged meaning) ---
        "weights": pd.Series(weights, index=tickers, name="weight"),
        "expected_return": portfolio_return(weights, mu),
        "expected_volatility": volatility,
        "mu": mu,
        "sigma": sigma,
        # --- new keys ---
        "risk_contributions": pd.Series(rc, index=tickers, name="risk_contribution"),
        "risk_contribution_share": pd.Series(rc / volatility if volatility > 0 else rc, index=tickers,
                                             name="risk_share"),
        "esg_score": portfolio_esg_score(weights, esg) if esg is not None else None,
        "constraints": {
            "min_weight": min_weight,
            "max_weight": max_weight,
            "esg_floor": esg_floor,
            "risk_aversion": risk_aversion if method == "mean_variance" else None,
            "risk_free_rate": risk_free_rate,
        },
        "checks": checks,
    }
