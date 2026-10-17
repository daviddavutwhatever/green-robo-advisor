"""Module 1: a very simple investor questionnaire.

This module is intentionally basic so first-semester students can understand and modify it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class InvestorProfile:
    total_score: int
    risk_level: str
    target_return: float
    target_risk: float
    explanation: str


QUESTIONS: List[Dict] = [
    {
        "id": "goal",
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
        "text": "What would you do if your portfolio falls by 15%?",
        "answers": {
            1: "Sell everything",
            2: "Sell a large part",
            3: "Wait and see",
            4: "Hold the portfolio",
            5: "Buy more",
        },
    },
]


def score_to_profile(total_score: int) -> InvestorProfile:
    """Map the questionnaire score to an annual target return and annual target risk.

    Returns are pedagogical target values, not financial advice.
    """
    if total_score <= 8:
        return InvestorProfile(
            total_score=total_score,
            risk_level="Conservative",
            target_return=0.04,
            target_risk=0.06,
            explanation="Low risk tolerance: more bond-heavy allocation is expected.",
        )
    if total_score <= 12:
        return InvestorProfile(
            total_score=total_score,
            risk_level="Balanced",
            target_return=0.06,
            target_risk=0.10,
            explanation="Medium risk tolerance: mixed equity-bond allocation is expected.",
        )
    if total_score <= 16:
        return InvestorProfile(
            total_score=total_score,
            risk_level="Growth",
            target_return=0.08,
            target_risk=0.14,
            explanation="Higher risk tolerance: stronger equity share is possible.",
        )
    return InvestorProfile(
        total_score=total_score,
        risk_level="Aggressive",
        target_return=0.10,
        target_risk=0.18,
        explanation="Very high risk tolerance: aggressive equity allocation is possible.",
    )


def profile_from_answers(answers: Dict[str, int]) -> InvestorProfile:
    total_score = sum(int(value) for value in answers.values())
    return score_to_profile(total_score)
