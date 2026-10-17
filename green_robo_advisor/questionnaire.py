"""Module 1: a very simple investor questionnaire.

This module is intentionally basic so first-semester students can understand and modify it.

Team enhancements in this module (3):
- Q1 Risk capacity: a new liquidity question measures how much risk you can AFFORD.
     The four original questions still measure risk TOLERANCE (how much risk you WANT).
     If you may need most of the money soon, the profile is capped at a safer level.
- Q2 ESG preference: a new ESG question becomes a suggested ESG floor for the optimizer.
- Q3 Consistency check: contradictory answers produce warnings (e.g. "I dislike losses"
     but "I would buy more after a 15 % fall"), so the user can double-check them.
All old fields of InvestorProfile and all old functions keep their meaning.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class InvestorProfile:
    total_score: int
    risk_level: str
    target_return: float
    target_risk: float
    explanation: str
    # --- new fields (with defaults, so old code that builds a profile still works) ---
    risk_tolerance_level: str = ""          # what the four tolerance questions alone say
    liquidity_need: str = "not asked"       # High / Medium / Low
    capacity_cap_applied: bool = False      # True if liquidity lowered the risk level
    esg_preference: Optional[int] = None    # 1-5 answer, None if not asked
    suggested_esg_floor: Optional[float] = None  # used as default ESG floor in the app
    consistency_warnings: List[str] = field(default_factory=list)  # Q3


QUESTIONS: List[Dict] = [
    {
        "id": "goal",
        "group": "Risk tolerance",
        "text": "How important is high return for you?",
        "answers": {
            1: "Not important",
            2: "Slightly important",
            3: "Moderately important",
            4: "Important",
            5: "Very important",
        },
    },
    {
        "id": "loss",
        "group": "Risk tolerance",
        "text": "How comfortable are you with temporary losses?",
        "answers": {
            1: "I dislike losses very much",
            2: "I am only slightly comfortable",
            3: "I can accept some losses",
            4: "I can accept larger losses",
            5: "I can accept strong fluctuations",
        },
    },
    {
        "id": "horizon",
        "group": "Risk tolerance",
        "text": "How long is your investment horizon?",
        "answers": {
            1: "Less than 1 year",
            2: "1-3 years",
            3: "3-5 years",
            4: "5-10 years",
            5: "More than 10 years",
        },
    },
    {
        "id": "reaction",
        "group": "Risk tolerance",
        "text": "What would you do if your portfolio falls by 15%?",
        "answers": {
            1: "Sell everything",
            2: "Sell a large part",
            3: "Wait and see",
            4: "Hold the portfolio",
            5: "Buy more",
        },
    },
    # --- NEW: risk capacity ---
    {
        "id": "liquidity",
        "group": "Risk capacity",
        "text": "How much of this money might you need within the next 2 years?",
        "answers": {
            1: "Most of it",
            2: "About half",
            3: "About a quarter",
            4: "Very little",
            5: "None of it",
        },
    },
    # --- NEW: sustainability preference ---
    {
        "id": "esg",
        "group": "Sustainability",
        "text": "How important is sustainability (ESG) in your investments?",
        "answers": {
            1: "Not important",
            2: "Slightly important",
            3: "Moderately important",
            4: "Important",
            5: "Very important",
        },
    },
]

# Questions that are NOT part of the risk-tolerance score
NON_TOLERANCE_IDS = {"liquidity", "esg"}

# Risk levels from safest to riskiest, with their pedagogical targets (unchanged values)
LEVELS = {
    "Conservative": (0.04, 0.06, "Low risk tolerance: more bond-heavy allocation is expected."),
    "Balanced": (0.06, 0.10, "Medium risk tolerance: mixed equity-bond allocation is expected."),
    "Growth": (0.08, 0.14, "Higher risk tolerance: stronger equity share is possible."),
    "Aggressive": (0.10, 0.18, "Very high risk tolerance: aggressive equity allocation is possible."),
}
LEVEL_ORDER = list(LEVELS.keys())

# Liquidity answer -> (label, highest risk level allowed or None for "no cap")
LIQUIDITY_MAPPING = {
    1: ("High", "Conservative"),
    2: ("Medium", "Balanced"),
    3: ("Low", None),
    4: ("Low", None),
    5: ("Low", None),
}

# ESG answer -> suggested minimum weighted ESG score (None = no floor)
ESG_FLOOR_MAPPING = {1: None, 2: None, 3: 7.6, 4: 7.8, 5: 8.0}


def _profile_for_level(level: str, total_score: int) -> InvestorProfile:
    target_return, target_risk, explanation = LEVELS[level]
    return InvestorProfile(
        total_score=total_score,
        risk_level=level,
        target_return=target_return,
        target_risk=target_risk,
        explanation=explanation,
        risk_tolerance_level=level,
    )


def score_to_profile(total_score: int) -> InvestorProfile:
    """Map the questionnaire score to an annual target return and annual target risk.

    Returns are pedagogical target values, not financial advice. (Unchanged thresholds.)
    """
    if total_score <= 8:
        return _profile_for_level("Conservative", total_score)
    if total_score <= 12:
        return _profile_for_level("Balanced", total_score)
    if total_score <= 16:
        return _profile_for_level("Growth", total_score)
    return _profile_for_level("Aggressive", total_score)


def check_answer_consistency(answers: Dict[str, int]) -> List[str]:
    """Q3: return plain-language warnings for answers that contradict each other.

    The warnings do not change the profile; they ask the user to double-check.
    """
    a = {k: int(v) for k, v in answers.items()}
    warnings: List[str] = []
    if a.get("loss", 3) <= 2 and a.get("reaction", 3) >= 4:
        warnings.append("You dislike losses, but say you would hold or buy more after a 15% fall.")
    if a.get("loss", 3) >= 4 and a.get("reaction", 3) <= 2:
        warnings.append("You say you can accept larger losses, but would sell after a 15% fall.")
    if a.get("horizon", 3) == 1 and a.get("goal", 3) >= 4:
        warnings.append("High returns are important to you, but your horizon is under 1 year; "
                        "short horizons leave little time to recover from losses.")
    if "liquidity" in a and a["liquidity"] <= 2 and a.get("horizon", 3) >= 4:
        warnings.append("Your horizon is long, but you may need a large part of the money within 2 years.")
    return warnings


def profile_from_answers(answers: Dict[str, int]) -> InvestorProfile:
    """Build the profile: tolerance score -> level, then apply capacity cap and ESG preference.

    A dictionary with only the four original answers gives exactly the old result.
    """
    tolerance_score = sum(int(v) for k, v in answers.items() if k not in NON_TOLERANCE_IDS)
    profile = score_to_profile(tolerance_score)

    # Q1 risk capacity: you cannot take more risk than you can afford, whatever you want
    if "liquidity" in answers:
        label, cap = LIQUIDITY_MAPPING[int(answers["liquidity"])]
        profile.liquidity_need = label
        if cap is not None and LEVEL_ORDER.index(profile.risk_level) > LEVEL_ORDER.index(cap):
            wanted = profile.risk_level
            capped = _profile_for_level(cap, tolerance_score)
            profile.risk_level = capped.risk_level
            profile.target_return = capped.target_return
            profile.target_risk = capped.target_risk
            profile.capacity_cap_applied = True
            need_text = QUESTIONS[4]["answers"][int(answers["liquidity"])]
            profile.explanation = (
                f"Your risk-tolerance answers point to {wanted}. But you answered \"{need_text}\" when "
                f"asked how much of this money you may need within 2 years, so your capacity to bear "
                f"losses is limited. The profile is therefore capped at {cap}."
            )

    # Q3: contradictions are reported, not "fixed"
    profile.consistency_warnings = check_answer_consistency(answers)

    # Q2: sustainability preference -> suggested ESG floor for the optimizer
    if "esg" in answers:
        profile.esg_preference = int(answers["esg"])
        profile.suggested_esg_floor = ESG_FLOOR_MAPPING[profile.esg_preference]

    return profile
