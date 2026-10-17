"""Simple command-line demo for students who do not want to start the web app first.

The first block is the original demo (unchanged output). The blocks below show one
enhancement per module, so every change is visible without opening the browser.
"""
from __future__ import annotations

from green_robo_advisor.data_module import get_etf_metadata, load_dataset
from green_robo_advisor.optimization import InfeasibleSettingsError, optimize_portfolio
from green_robo_advisor.questionnaire import profile_from_answers, score_to_profile
from green_robo_advisor.visualization import correlation_matrix, performance_summary, portfolio_returns


def main() -> None:
    print("Green Robo Advisor - command line demo")
    print("Example: assume a total questionnaire score of 13")
    profile = score_to_profile(13)
    print(f"Risk profile: {profile.risk_level}")
    print(f"Target return: {profile.target_return:.1%}")
    print(f"Target risk: {profile.target_risk:.1%}")

    dataset = load_dataset(start="2020-01-01", source="auto")
    print(f"Data source used: {dataset['data_source']}")
    result = optimize_portfolio(
        returns=dataset["asset_returns"],
        method="max_sharpe",
        target_return=profile.target_return,
        target_risk=profile.target_risk,
    )

    print("\nPortfolio weights:")
    print(result["weights"].round(4))
    print(f"\nExpected annual return: {result['expected_return']:.2%}")
    print(f"Expected annual volatility: {result['expected_volatility']:.2%}")

    # --- Questionnaire: Q1 risk capacity, Q2 ESG preference, Q3 consistency check ---
    print("\n=== Questionnaire: tolerance vs capacity ===")
    answers = {"goal": 4, "loss": 4, "horizon": 3, "reaction": 4, "liquidity": 1, "esg": 4}
    new_profile = profile_from_answers(answers)
    print(f"Answers: {answers}")
    print(f"Risk tolerance says: {new_profile.risk_tolerance_level} -> final profile: {new_profile.risk_level}")
    print(f"Liquidity need: {new_profile.liquidity_need} | suggested ESG floor: {new_profile.suggested_esg_floor}")
    print(new_profile.explanation)
    contradictory = {"goal": 3, "loss": 1, "horizon": 3, "reaction": 5}
    print(f"Consistency check (Q3) for {contradictory}: {profile_from_answers(contradictory).consistency_warnings}")

    # --- Data: D1 provenance, D3 quality report (D2 and D4 run inside load_dataset / metadata) ---
    print("\n=== Data: provenance and quality ===")
    first, last, n_days = dataset["sample_period"]
    print(f"Source: {dataset['data_source']} | fallback used: {dataset['fallback_used']}")
    if dataset["fallback_reason"]:
        print(f"Reason: {dataset['fallback_reason']}")
    print(f"Common sample: {first} to {last} ({n_days} trading days), NaN left in returns: {dataset['nan_in_returns']}")
    print(dataset["quality_report"][["ticker", "source", "missing_before_cleaning", "missing_after_cleaning"]]
          .to_string(index=False))

    # --- Optimization: O1 bounds, O2 ESG floor, O4 feasibility, O5 risk contributions ---
    print("\n=== Optimization: constraints ===")
    esg_scores = get_etf_metadata().set_index("ticker")["esg_quality_score"]
    settings = {"min_weight": 0.05, "max_weight": 0.40, "esg_floor": 7.8}
    print(f"max_sharpe with {settings}:")
    constrained = optimize_portfolio(
        returns=dataset["asset_returns"],
        method="max_sharpe",
        target_return=profile.target_return,
        target_risk=profile.target_risk,
        esg_scores=esg_scores,
        **settings,
    )
    print(constrained["weights"].round(4))
    print(f"Expected annual return: {constrained['expected_return']:.2%}")
    print(f"Expected annual volatility: {constrained['expected_volatility']:.2%}")
    print(f"Portfolio ESG score: {constrained['esg_score']:.2f}")
    print("Risk contribution share:")
    print(constrained["risk_contribution_share"].round(4))
    print(f"Constraint checks: {constrained['checks']}")

    print("\nFeasibility check example (ESG floor 9.0 is above every ETF's score):")
    try:
        optimize_portfolio(
            returns=dataset["asset_returns"], method="max_sharpe",
            target_return=profile.target_return, target_risk=profile.target_risk,
            esg_scores=esg_scores, esg_floor=9.0,
        )
    except InfeasibleSettingsError as exc:
        print(f"Infeasible settings detected: {exc}")

    # --- Visualization: V1 drawdown, V2 summary, V3 correlation ---
    print("\n=== Diagnostics: portfolio (constrained) vs benchmark ===")
    portfolio = portfolio_returns(dataset["asset_returns"], constrained["weights"])
    summary = performance_summary(portfolio, dataset["benchmark_returns"].squeeze())
    print(summary.round(4).to_string())
    print("\nCorrelation of daily returns (V3):")
    print(correlation_matrix(dataset["asset_returns"]).round(2).to_string())


if __name__ == "__main__":
    main()
