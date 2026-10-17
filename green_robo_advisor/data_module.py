"""Module 2: download ETF prices and clean missing values.

This version is classroom-friendly:
- it first tries live data from Yahoo Finance
- if Yahoo blocks the request or returns no data, it falls back to a bundled sample dataset
- all return series are daily log returns

Team enhancements in this module (4):
- D1 Data provenance: the dataset records WHY a fallback to sample data happened, and the
     benchmark always comes from the same source as the ETFs.
- D2 Missing-ticker check: tickers that Yahoo returns without any prices are detected
     instead of silently kept.
- D3 Data-quality report: per ticker, the source, the date range, and how many missing
     prices were filled during cleaning.
- D4 Region metadata: each ETF now has a region (config.py), shown in the metadata table.
- D5 Extended sample data: the offline sample now holds 10 ESG ETFs instead of 5
     (data/generate_sample_data.py). The original 5 columns are unchanged.
All old keys of load_dataset() are unchanged; new keys are only added.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from .config import DEFAULT_BENCHMARK, DEFAULT_TICKERS, ETF_UNIVERSE

try:  # yfinance is optional: without it, the sample data still work
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None


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
                "region": info.get("region", "n/a"),  # D4
                "theme": info.get("theme", "n/a"),    # D5
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


def check_missing_tickers(prices: pd.DataFrame, tickers: list[str]) -> list[str]:
    """D2: tickers that are absent or have no price at all (e.g. delisted or blocked)."""
    return [t for t in tickers if t not in prices.columns or prices[t].dropna().empty]


def download_prices_yfinance(
    tickers: list[str],
    start: str = "2020-01-01",
    end: str | None = None,
) -> pd.DataFrame:
    if yf is None:
        raise DataDownloadError("The yfinance package is not installed.")
    data = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    prices = _extract_close_prices(data, tickers)
    missing = check_missing_tickers(prices, tickers)
    if missing:
        raise DataDownloadError(f"Yahoo Finance returned no prices for: {missing}")
    return prices.loc[:, tickers]


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


def download_prices_with_reason(
    tickers: list[str],
    start: str = "2020-01-01",
    end: str | None = None,
    source: Literal["auto", "yfinance", "sample"] = "auto",
) -> tuple[pd.DataFrame, str, str | None]:
    """D1: like download_prices, but also returns why a fallback happened (or None)."""
    if source == "sample":
        return load_sample_prices(tickers, start=start, end=end), "sample", None

    if source == "yfinance":
        return download_prices_yfinance(tickers, start=start, end=end), "yfinance", None

    try:
        return download_prices_yfinance(tickers, start=start, end=end), "yfinance", None
    except Exception as exc:
        prices = load_sample_prices(tickers, start=start, end=end)
        reason = f"Live Yahoo Finance download failed ({exc}). Using bundled sample data instead."
        print(f"Warning: {reason}")
        return prices, "sample", reason


def download_prices(
    tickers: list[str] | None = None,
    start: str = "2020-01-01",
    end: str | None = None,
    source: Literal["auto", "yfinance", "sample"] = "auto",
) -> tuple[pd.DataFrame, str]:
    """Download prices and return (prices, source_used). (Unchanged contract.)"""
    tickers = tickers or DEFAULT_TICKERS
    prices, used, _ = download_prices_with_reason(tickers, start=start, end=end, source=source)
    return prices, used


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


def data_quality_report(raw_prices: pd.DataFrame, cleaned_prices: pd.DataFrame, source: str) -> pd.DataFrame:
    """D3: one row per ticker describing where the data came from and how much was repaired."""
    rows = []
    for ticker in raw_prices.columns:
        raw = raw_prices[ticker]
        valid = raw.dropna()
        n_missing = int(raw.isna().sum())
        rows.append(
            {
                "ticker": ticker,
                "source": source,
                "first_date": valid.index.min().date() if not valid.empty else None,
                "last_date": valid.index.max().date() if not valid.empty else None,
                "price_rows": int(len(raw)),
                "missing_before_cleaning": n_missing,
                "missing_share": round(n_missing / len(raw), 4) if len(raw) else 0.0,
                "missing_after_cleaning": int(cleaned_prices[ticker].isna().sum()),
            }
        )
    return pd.DataFrame(rows)


def load_dataset(
    tickers: list[str] | None = None,
    benchmark: str = DEFAULT_BENCHMARK,
    start: str = "2020-01-01",
    end: str | None = None,
    source: Literal["auto", "yfinance", "sample"] = "auto",
) -> dict:
    tickers = tickers or DEFAULT_TICKERS
    asset_raw, asset_source, asset_reason = download_prices_with_reason(tickers, start=start, end=end, source=source)
    asset_prices = fill_missing_linear(asset_raw)
    asset_returns = returns_from_prices(asset_prices)

    # If the assets had to fall back to sample data, use sample data for the benchmark too,
    # so that portfolio and benchmark always come from the same source.
    benchmark_mode = "sample" if asset_source == "sample" and source == "auto" else source
    benchmark_raw, benchmark_source, benchmark_reason = download_prices_with_reason(
        [benchmark], start=start, end=end, source=benchmark_mode
    )
    benchmark_prices = fill_missing_linear(benchmark_raw)
    benchmark_returns = returns_from_prices(benchmark_prices)

    common_index = asset_returns.index.intersection(benchmark_returns.index)
    if len(common_index) < 60:
        raise DataDownloadError(
            f"Only {len(common_index)} common trading days between assets and benchmark; "
            "choose an earlier start date."
        )
    asset_returns = asset_returns.loc[common_index]
    asset_prices = asset_prices.loc[common_index]
    benchmark_returns = benchmark_returns.loc[common_index]
    benchmark_prices = benchmark_prices.loc[common_index]

    quality = pd.concat(
        [
            data_quality_report(asset_raw, fill_missing_linear(asset_raw), asset_source),
            data_quality_report(benchmark_raw, fill_missing_linear(benchmark_raw), benchmark_source)
            .assign(ticker=lambda df: df["ticker"] + " (benchmark)"),
        ],
        ignore_index=True,
    )

    return {
        # --- original keys (unchanged) ---
        "asset_prices": asset_prices,
        "asset_returns": asset_returns,
        "benchmark_prices": benchmark_prices,
        "benchmark_returns": benchmark_returns,
        "metadata": get_etf_metadata(),
        "benchmark": benchmark,
        "data_source": asset_source if asset_source == benchmark_source else f"assets={asset_source}, benchmark={benchmark_source}",
        # --- new keys ---
        "fallback_used": source == "auto" and asset_source == "sample",
        "fallback_reason": asset_reason or benchmark_reason,
        "quality_report": quality,
        "sample_period": (common_index.min().date(), common_index.max().date(), len(common_index)),
        "nan_in_returns": int(asset_returns.isna().sum().sum() + benchmark_returns.isna().sum().sum()),
    }
