"""Module 2: download ETF prices and clean missing values.

This version is classroom-friendly:
- it first tries live data from Yahoo Finance
- if Yahoo blocks the request or returns no data, it falls back to a bundled sample dataset
- all return series are daily log returns
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import yfinance as yf

from .config import DEFAULT_BENCHMARK, DEFAULT_TICKERS, ETF_UNIVERSE


class DataDownloadError(RuntimeError):
    """Raised when no usable market data can be downloaded."""


SAMPLE_DATA_PATH = Path(__file__).resolve().parent / "data" / "sample_prices.csv"


def get_etf_metadata() -> pd.DataFrame:
    rows = []
    for ticker, info in ETF_UNIVERSE.items():
        rows.append(
            {
                "ticker": ticker,
                "name": info["name"],
                "asset_class": info["asset_class"],
                "esg_rating": info["esg_rating"],
                "esg_quality_score": info["esg_quality_score"],
            }
        )
    return pd.DataFrame(rows)


def _extract_close_prices(data: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    if data.empty:
        raise DataDownloadError("Data source returned no rows.")

    if isinstance(data.columns, pd.MultiIndex):
        if "Close" in data.columns.get_level_values(0):
            prices = data["Close"].copy()
        elif "Adj Close" in data.columns.get_level_values(0):
            prices = data["Adj Close"].copy()
        else:
            prices = data.xs(data.columns.levels[0][0], axis=1, level=0).copy()
    else:
        prices = data.to_frame(name=tickers[0]) if len(tickers) == 1 else data.copy()

    prices = prices.dropna(how="all")
    if prices.empty:
        raise DataDownloadError("Downloaded data only contains missing values.")
    return prices



def download_prices_yfinance(
    tickers: list[str],
    start: str = "2020-01-01",
    end: str | None = None,
) -> pd.DataFrame:
    data = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    prices = _extract_close_prices(data, tickers)
    return prices



def load_sample_prices(
    tickers: list[str],
    start: str = "2020-01-01",
    end: str | None = None,
) -> pd.DataFrame:
    if not SAMPLE_DATA_PATH.exists():
        raise DataDownloadError(f"Sample dataset not found: {SAMPLE_DATA_PATH}")

    prices = pd.read_csv(SAMPLE_DATA_PATH, parse_dates=["Date"], index_col="Date")
    missing = [ticker for ticker in tickers if ticker not in prices.columns]
    if missing:
        raise DataDownloadError(f"Sample dataset does not contain tickers: {missing}")

    prices = prices.loc[:, tickers].sort_index()
    prices = prices.loc[prices.index >= pd.Timestamp(start)]
    if end is not None:
        prices = prices.loc[prices.index <= pd.Timestamp(end)]
    if prices.empty:
        raise DataDownloadError("Sample dataset is empty for the selected date range.")
    return prices



def download_prices(
    tickers: list[str] | None = None,
    start: str = "2020-01-01",
    end: str | None = None,
    source: Literal["auto", "yfinance", "sample"] = "auto",
) -> tuple[pd.DataFrame, str]:
    """Download prices and return (prices, source_used)."""
    tickers = tickers or DEFAULT_TICKERS

    if source == "sample":
        return load_sample_prices(tickers, start=start, end=end), "sample"

    if source == "yfinance":
        return download_prices_yfinance(tickers, start=start, end=end), "yfinance"

    try:
        return download_prices_yfinance(tickers, start=start, end=end), "yfinance"
    except Exception as exc:
        prices = load_sample_prices(tickers, start=start, end=end)
        print(
            "Warning: live Yahoo Finance download failed. "
            f"Using bundled sample data instead. Original error: {exc}"
        )
        return prices, "sample"



def fill_missing_linear(prices: pd.DataFrame) -> pd.DataFrame:
    """Fill gaps with time-based linear interpolation and edge filling."""
    cleaned = prices.sort_index().copy()
    cleaned = cleaned.interpolate(method="time")
    cleaned = cleaned.ffill().bfill()
    return cleaned



def returns_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute daily log returns from price levels."""
    log_returns = np.log(prices / prices.shift(1)).dropna()
    return log_returns



def load_dataset(
    tickers: list[str] | None = None,
    benchmark: str = DEFAULT_BENCHMARK,
    start: str = "2020-01-01",
    end: str | None = None,
    source: Literal["auto", "yfinance", "sample"] = "auto",
) -> dict:
    tickers = tickers or DEFAULT_TICKERS
    asset_raw, asset_source = download_prices(tickers, start=start, end=end, source=source)
    asset_prices = fill_missing_linear(asset_raw)
    asset_returns = returns_from_prices(asset_prices)

    benchmark_raw, benchmark_source = download_prices([benchmark], start=start, end=end, source=source)
    benchmark_prices = fill_missing_linear(benchmark_raw)
    benchmark_returns = returns_from_prices(benchmark_prices)

    common_index = asset_returns.index.intersection(benchmark_returns.index)
    asset_returns = asset_returns.loc[common_index]
    asset_prices = asset_prices.loc[common_index]
    benchmark_returns = benchmark_returns.loc[common_index]
    benchmark_prices = benchmark_prices.loc[common_index]

    return {
        "asset_prices": asset_prices,
        "asset_returns": asset_returns,
        "benchmark_prices": benchmark_prices,
        "benchmark_returns": benchmark_returns,
        "metadata": get_etf_metadata(),
        "benchmark": benchmark,
        "data_source": asset_source if asset_source == benchmark_source else f"assets={asset_source}, benchmark={benchmark_source}",
    }
