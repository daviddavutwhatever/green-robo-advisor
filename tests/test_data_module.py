"""Tests for the data-module enhancement (provenance + data-quality report).

All tests use source="sample" or a fake downloader, so no internet connection is needed.
"""
from __future__ import annotations

import pandas as pd
import pytest

import green_robo_advisor.data_module as data_module
import green_robo_advisor.prototype_backup.data_module as old_data_module
from green_robo_advisor.data_module import (
    DataDownloadError,
    check_missing_tickers,
    get_etf_metadata,
    load_dataset,
)


@pytest.fixture(scope="module")
def dataset() -> dict:
    return load_dataset(start="2020-01-01", source="sample")


def test_old_keys_are_unchanged(dataset, monkeypatch):
    """Module contract: every key of the old dataset still exists with the same values."""
    monkeypatch.setattr(old_data_module, "SAMPLE_DATA_PATH", data_module.SAMPLE_DATA_PATH)
    old = old_data_module.load_dataset(start="2020-01-01", source="sample")
    for key in ["asset_prices", "asset_returns", "benchmark_prices", "benchmark_returns"]:
        pd.testing.assert_frame_equal(old[key], dataset[key])
    assert old["data_source"] == dataset["data_source"]


def test_no_missing_values_in_the_return_sample(dataset):
    """Validation checklist: no unexpected NaN values in the common return sample."""
    assert dataset["nan_in_returns"] == 0
    assert not dataset["asset_returns"].isna().any().any()
    assert dataset["asset_returns"].index.equals(dataset["benchmark_returns"].index)


def test_quality_report_counts_filled_prices(dataset):
    report = dataset["quality_report"]
    assert len(report) == 6                                    # 5 ETFs + benchmark
    assert (report["missing_before_cleaning"] > 0).all()       # the sample file has gaps ...
    assert (report["missing_after_cleaning"] == 0).all()       # ... and cleaning fills them all
    assert set(report["source"]) == {"sample"}


def test_missing_ticker_is_detected():
    prices = pd.DataFrame({"AAA": [1.0, 1.1], "BBB": [None, None]})
    assert check_missing_tickers(prices, ["AAA", "BBB", "CCC"]) == ["BBB", "CCC"]


def test_fallback_is_reported_when_yahoo_fails(monkeypatch):
    def broken_download(*args, **kwargs):
        raise DataDownloadError("simulated network block")

    monkeypatch.setattr(data_module, "download_prices_yfinance", broken_download)
    result = load_dataset(start="2020-01-01", source="auto")
    assert result["fallback_used"] is True
    assert "simulated network block" in result["fallback_reason"]
    assert result["data_source"] == "sample"                   # assets AND benchmark from one source


def test_metadata_has_region():
    meta = get_etf_metadata()
    assert "region" in meta.columns
    assert meta["region"].notna().all()


# --- D5: extended sample data (10 ETFs) ------------------------------------------------
from green_robo_advisor.config import ALL_TICKERS, DEFAULT_TICKERS


def test_extended_sample_has_ten_etfs_and_default_stays_five():
    assert len(ALL_TICKERS) == 10 and len(DEFAULT_TICKERS) == 5
    full = load_dataset(tickers=ALL_TICKERS, start="2020-01-01", source="sample")
    assert list(full["asset_returns"].columns) == ALL_TICKERS
    assert full["nan_in_returns"] == 0
    assert list(load_dataset(start="2020-01-01", source="sample")["asset_returns"].columns) == DEFAULT_TICKERS


def test_new_etfs_have_plausible_relationships():
    returns = load_dataset(tickers=ALL_TICKERS, start="2020-01-01", source="sample")["asset_returns"]
    corr, vol = returns.corr(), returns.std() * 252 ** 0.5
    assert corr.loc["SUSA", "ESGU"] > 0.9            # US ESG equity behaves like ESGU
    assert corr.loc["EAGG", "SUSC"] > 0.7            # ESG bonds move with bonds ...
    assert corr.loc["EAGG", "ESGU"] < 0.4            # ... and only weakly with equities
    assert vol["ICLN"] > vol["ESGU"] > vol["EAGG"]   # thematic equity > broad equity > bonds
