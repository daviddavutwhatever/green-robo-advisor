"""Tests for the questionnaire enhancement (risk capacity + ESG preference).

Run with:  python -m pytest tests -v
"""
from __future__ import annotations

import itertools

import pytest

from green_robo_advisor.prototype_backup import questionnaire as old_questionnaire
from green_robo_advisor.questionnaire import ESG_FLOOR_MAPPING, QUESTIONS, profile_from_answers

ORIGINAL_IDS = ["goal", "loss", "horizon", "reaction"]
HIGH_TOLERANCE = {"goal": 4, "loss": 4, "horizon": 4, "reaction": 4}  # score 16 -> Growth


def test_old_answers_give_exactly_the_old_profile():
    """Module contract: all 625 combinations of the four original questions are unchanged."""
    for combo in itertools.product(range(1, 6), repeat=4):
        answers = dict(zip(ORIGINAL_IDS, combo))
        old, new = old_questionnaire.profile_from_answers(answers), profile_from_answers(answers)
        assert (old.total_score, old.risk_level, old.target_return, old.target_risk) == (
            new.total_score, new.risk_level, new.target_return, new.target_risk)


def test_new_questions_exist_and_keep_old_ones():
    ids = [q["id"] for q in QUESTIONS]
    assert ids[:4] == ORIGINAL_IDS
    assert "liquidity" in ids and "esg" in ids


@pytest.mark.parametrize("liquidity, expected_level, capped", [
    (1, "Conservative", True),   # needs most of the money soon
    (2, "Balanced", True),       # needs about half
    (3, "Growth", False),        # no cap
    (5, "Growth", False),
])
def test_liquidity_need_caps_the_risk_level(liquidity, expected_level, capped):
    profile = profile_from_answers({**HIGH_TOLERANCE, "liquidity": liquidity})
    assert profile.risk_tolerance_level == "Growth"       # what the investor wants
    assert profile.risk_level == expected_level           # what the investor can afford
    assert profile.capacity_cap_applied is capped


def test_liquidity_never_increases_risk():
    low = {"goal": 1, "loss": 1, "horizon": 1, "reaction": 1}
    assert profile_from_answers({**low, "liquidity": 5}).risk_level == "Conservative"


def test_new_answers_do_not_change_the_tolerance_score():
    profile = profile_from_answers({**HIGH_TOLERANCE, "liquidity": 5, "esg": 5})
    assert profile.total_score == 16


@pytest.mark.parametrize("esg_answer", [1, 2, 3, 4, 5])
def test_esg_answer_sets_the_suggested_floor(esg_answer):
    profile = profile_from_answers({**HIGH_TOLERANCE, "esg": esg_answer})
    assert profile.suggested_esg_floor == ESG_FLOOR_MAPPING[esg_answer]
    floors = [ESG_FLOOR_MAPPING[a] or 0 for a in range(1, 6)]
    assert floors == sorted(floors)  # more ESG importance never lowers the floor


# --- Q3: consistency check ---------------------------------------------------------------
from green_robo_advisor.questionnaire import check_answer_consistency


def test_contradictory_answers_produce_a_warning():
    answers = {"goal": 3, "loss": 1, "horizon": 3, "reaction": 5}  # dislikes losses, but buys more
    warnings = check_answer_consistency(answers)
    assert len(warnings) == 1 and "dislike losses" in warnings[0]


def test_consistent_answers_produce_no_warning():
    assert check_answer_consistency({"goal": 3, "loss": 3, "horizon": 3, "reaction": 3, "liquidity": 3}) == []


def test_warnings_do_not_change_the_profile():
    answers = {"goal": 3, "loss": 1, "horizon": 3, "reaction": 5}
    profile = profile_from_answers(answers)
    assert profile.consistency_warnings                                    # warning is reported ...
    assert profile.risk_level == old_questionnaire.profile_from_answers(answers).risk_level  # ... profile unchanged
