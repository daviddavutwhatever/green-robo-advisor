"""Tests for the app enhancements (A1-A4), using Streamlit's built-in headless test runner.

No browser is opened. Each test runs the whole app with the sample data source.
"""
from __future__ import annotations

from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = str(Path(__file__).resolve().parents[1] / "green_robo_advisor" / "app.py")


def run_app(setup=lambda at: None):
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    at.sidebar.selectbox[0].set_value("sample")   # A1: data source from the sidebar
    setup(at)
    at.run()
    at.button[0].click().run()
    return at


def test_default_run_shows_results_in_tabs():
    at = run_app()
    assert not at.exception and not at.error
    assert [t.label for t in at.tabs] == ["Allocation", "Performance & risk", "Diversification", "Data quality"]  # A3


def test_infeasible_sidebar_setting_gives_readable_error():
    at = run_app(lambda a: a.sidebar.slider[0].set_value(0.25))   # A1 + A2: minimum weight 25 % x 5 ETFs
    assert not at.exception                                         # no traceback ...
    assert "cannot be satisfied" in at.error[0].value               # ... but a readable message


def test_unknown_benchmark_gives_readable_error():
    at = run_app(lambda a: a.text_input[0].set_value("XXXX"))     # A2
    assert not at.exception
    assert "could not be loaded" in at.error[0].value


def test_two_csv_downloads_are_offered():
    at = run_app()
    labels = [element.proto.label for element in at.get("download_button")]   # A4
    assert labels == ["Download allocation (CSV)", "Download performance summary (CSV)"]
