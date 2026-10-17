"""D5: build the extended offline sample (10 ESG ETFs) from the original 5-ETF sample.

Why: the professor allows sample data instead of Yahoo Finance, and the handout suggests
enlarging the universe to about 10 ETFs. This script adds 5 ETFs to sample_prices.csv.

How (one-factor model, fully reproducible with a fixed random seed):
    new daily log return = drift + beta x factor return + idiosyncratic noise
- the factor is built from the ORIGINAL sample: the average equity return (ESGU, ESGD, ESGE)
  or the average bond return (SUSB, SUSC). New ETFs therefore get realistic correlations
  with the old ones (e.g. a US ESG equity ETF moves almost like ESGU),
- the noise is Student-t distributed (df = 4): more extreme days than a normal distribution,
  as in real markets, and it is scaled by the factor's recent volatility, so calm and
  turbulent periods (volatility clustering) also appear in the new series,
- the drift is chosen so the annual mean return matches a target,
- 8 random price gaps per new ETF, like the original file, to keep the cleaning step realistic.

The original 5 columns are NOT changed, so every earlier result stays reproducible.
The prices are synthetic: they illustrate the method and are not real market data.

Run from the project folder:  python green_robo_advisor/data/generate_sample_data.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PATH = Path(__file__).resolve().parent / "sample_prices.csv"
ORIGINAL = ["ESGU", "ESGD", "ESGE", "SUSB", "SUSC"]
SEED = 2026
TRADING_DAYS = 252

# ticker: (factor, beta, idiosyncratic annual vol, target annual log return, start price)
NEW_ETFS = {
    "SUSA": ("equity_us", 0.95, 0.04, 0.080, 95.0),   # US ESG select equity: close to ESGU
    "DSI": ("equity_us", 1.00, 0.05, 0.084, 80.0),    # US social-index equity
    "ICLN": ("equity", 1.25, 0.24, 0.010, 15.0),      # global clean energy: high ESG, high risk
    "EAGG": ("bond", 1.00, 0.025, 0.015, 52.0),       # US aggregate ESG bonds
    "BGRN": ("bond_green", 1.05, 0.030, 0.012, 48.0), # USD green bonds
}


def build_factors(returns: pd.DataFrame) -> dict[str, pd.Series]:
    equity = returns[["ESGU", "ESGD", "ESGE"]].mean(axis=1)
    bond = returns[["SUSB", "SUSC"]].mean(axis=1)
    return {
        "equity_us": returns["ESGU"],
        "equity": equity,
        "bond": bond,
        "bond_green": 0.95 * bond + 0.05 * equity,   # green bonds: slight equity sensitivity
    }


def main() -> None:
    rng = np.random.default_rng(SEED)
    prices = pd.read_csv(PATH, parse_dates=["Date"], index_col="Date")[ORIGINAL]
    filled = prices.interpolate(method="time").ffill().bfill()
    returns = np.log(filled / filled.shift(1)).dropna()
    factors = build_factors(returns)

    for ticker, (factor_name, beta, idio_vol, target_mu, start_price) in NEW_ETFS.items():
        factor = factors[factor_name]
        # volatility clustering: noise is larger when the factor has been volatile recently
        regime = factor.rolling(21, min_periods=5).std().bfill()
        regime = regime / regime.mean()
        t_noise = rng.standard_t(df=4, size=len(factor)) / np.sqrt(4 / (4 - 2))  # unit variance
        noise = t_noise * idio_vol / np.sqrt(TRADING_DAYS) * regime.values
        raw = beta * factor.values + noise
        drift = target_mu / TRADING_DAYS - raw.mean()
        log_returns = raw + drift
        path = start_price * np.exp(np.concatenate([[0.0], np.cumsum(log_returns)]))
        series = pd.Series(path, index=filled.index, name=ticker)
        gaps = rng.choice(np.arange(1, len(series) - 1), size=8, replace=False)
        series.iloc[gaps] = np.nan
        prices[ticker] = series

    prices.index.name = "Date"
    prices.to_csv(PATH)
    print(f"Wrote {prices.shape[1]} tickers x {prices.shape[0]} days to {PATH}")


if __name__ == "__main__":
    main()
