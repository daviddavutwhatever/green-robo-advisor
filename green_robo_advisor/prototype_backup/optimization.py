"""Module 3: portfolio optimization methods using daily log returns."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .config import TRADING_DAYS


class OptimizationError(RuntimeError):
    pass



def annualized_statistics(log_returns: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """Annualized mean vector and covariance matrix based on daily log returns."""
    mu = log_returns.mean() * TRADING_DAYS
    Sigma = log_returns.cov() * TRADING_DAYS # Variance-Covaiance Matrix
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
    vol = portfolio_volatility(weights, sigma)
    if vol <= 0:
        return np.zeros_like(weights)
    marginal = sigma.values @ weights / vol
    return weights * marginal



def _base_constraints() -> list[dict]:
    return [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]



def _base_bounds(n_assets: int) -> tuple:
    return tuple((0.0, 1.0) for _ in range(n_assets))



def _initial_guess(n_assets: int) -> np.ndarray:
    return np.repeat(1.0 / n_assets, n_assets)



def min_variance_for_target_return(mu: pd.Series, sigma: pd.DataFrame, target_return: float) -> np.ndarray:
    """Minimum-variance portfolio for a target annual log return."""
    n_assets = len(mu)
    constraints = _base_constraints() + [
        {"type": "eq", "fun": lambda w: portfolio_return(w, mu) - target_return}
    ]
    result = minimize(
        fun=lambda w: portfolio_volatility(w, sigma) ** 2,
        x0=_initial_guess(n_assets),
        bounds=_base_bounds(n_assets),
        constraints=constraints,
    )
    if not result.success:
        raise OptimizationError(f"Min-variance failed: {result.message}")
    return result.x



def max_return_for_risk(mu: pd.Series, sigma: pd.DataFrame, target_risk: float) -> np.ndarray:
    """Maximum expected annual log return for a target annual volatility."""
    n_assets = len(mu)
    constraints = _base_constraints() + [
        {"type": "ineq", "fun": lambda w: target_risk - portfolio_volatility(w, sigma)}
    ]
    result = minimize(
        fun=lambda w: -portfolio_return(w, mu),
        x0=_initial_guess(n_assets),
        bounds=_base_bounds(n_assets),
        constraints=constraints,
    )
    if not result.success:
        raise OptimizationError(f"Max return failed: {result.message}")
    return result.x



def max_sharpe_ratio(mu: pd.Series, sigma: pd.DataFrame, risk_free_rate: float = 0.0) -> np.ndarray:
    n_assets = len(mu)
    result = minimize(
        fun=lambda w: negative_sharpe(w, mu, sigma, risk_free_rate=risk_free_rate),
        x0=_initial_guess(n_assets),
        bounds=_base_bounds(n_assets),
        constraints=_base_constraints(),
    )
    if not result.success:
        raise OptimizationError(f"Max Sharpe failed: {result.message}")
    return result.x



def risk_parity(sigma: pd.DataFrame) -> np.ndarray:
    n_assets = len(sigma)

    def objective(w: np.ndarray) -> float:
        rc = risk_contributions(w, sigma)
        target = np.repeat(np.sum(rc) / n_assets, n_assets)
        return float(np.sum((rc - target) ** 2))

    result = minimize(
        fun=objective,
        x0=_initial_guess(n_assets),
        bounds=_base_bounds(n_assets),
        constraints=_base_constraints(),
    )
    if not result.success:
        raise OptimizationError(f"Risk parity failed: {result.message}")
    return result.x



def optimize_portfolio(
    returns: pd.DataFrame,
    method: str,
    target_return: float,
    target_risk: float,
    risk_free_rate: float = 0.0,
) -> dict:
    """Optimize a portfolio from daily log returns."""
    mu, sigma = annualized_statistics(returns)

    method = method.lower().strip()
    if method == "min_variance":
        weights = min_variance_for_target_return(mu, sigma, target_return)
    elif method == "max_return":
        weights = max_return_for_risk(mu, sigma, target_risk)
    elif method == "max_sharpe":
        weights = max_sharpe_ratio(mu, sigma, risk_free_rate=risk_free_rate)
    elif method == "risk_parity":
        weights = risk_parity(sigma)
    else:
        raise ValueError(f"Unknown method: {method}")

    weights_series = pd.Series(weights, index=returns.columns, name="weight")
    return {
        "weights": weights_series,
        "expected_return": portfolio_return(weights, mu),
        "expected_volatility": portfolio_volatility(weights, sigma),
        "mu": mu,
        "sigma": sigma,
    }
