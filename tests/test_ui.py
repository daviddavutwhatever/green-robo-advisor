"""Tests for the app's design helpers (A5 design, A6 interactive charts)."""
from __future__ import annotations

import pandas as pd

from green_robo_advisor import ui
from green_robo_advisor.data_module import get_etf_metadata
from green_robo_advisor.questionnaire import profile_from_answers


def test_line_chart_uses_dates_on_the_x_axis():
    # handout 12.4: pass dates explicitly so the row number is never plotted by mistake
    dates = pd.date_range("2024-01-01", periods=5, freq="B")
    series = pd.Series([1.0, 1.01, 1.02, 1.0, 1.03], index=dates)
    fig = ui.line_chart(series, series * 0.99)
    for trace in fig.data:
        assert pd.to_datetime(list(trace.x)).equals(dates)


def test_allocation_chart_colours_bars_by_asset_class():
    meta = get_etf_metadata()
    weights = pd.Series({"ESGU": 0.6, "SUSC": 0.4})
    fig = ui.allocation_chart(weights, weights, meta)
    colours = dict(zip(fig.data[0].y, fig.data[0].marker.color))
    assert colours["ESGU"] == ui.TEAL and colours["SUSC"] == ui.GOLD


def test_hero_lists_every_etf_and_escapes_text():
    html = ui.hero(get_etf_metadata())
    for ticker in get_etf_metadata()["ticker"]:
        assert ticker in html
    assert "<script" not in ui.step(1, "<script>")


def test_profile_card_shows_level_and_esg_floor():
    profile = profile_from_answers({"goal": 4, "loss": 4, "horizon": 4, "reaction": 4, "liquidity": 5, "esg": 5})
    card = ui.profile_card(profile)
    assert "Growth investor" in card and "8.0" in card
