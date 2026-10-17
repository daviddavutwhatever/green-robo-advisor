"""Module 5: Streamlit web app that combines all modules."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from green_robo_advisor.config import DEFAULT_BENCHMARK, DEFAULT_TICKERS
from green_robo_advisor.data_module import get_etf_metadata, load_dataset
from green_robo_advisor.optimization import optimize_portfolio
from green_robo_advisor.questionnaire import QUESTIONS, profile_from_answers
from green_robo_advisor.visualization import cumulative_returns, portfolio_returns, rolling_volatility


st.set_page_config(page_title="Green Robo Advisor", layout="wide")

st.title("Green Robo Advisor")
st.write(
    "A simple classroom app to demonstrate modularization, data handling, portfolio optimization, and visualization."
)
st.caption("This version uses daily log returns consistently throughout the data, optimization, and visualization modules.")

with st.expander("Step 1 - Sustainable ETF universe"):
    st.dataframe(get_etf_metadata(), use_container_width=True)

st.subheader("Step 2 - Investor questionnaire")
answers = {}
for question in QUESTIONS:
    answers[question["id"]] = st.radio(
        question["text"],
        options=list(question["answers"].keys()),
        format_func=lambda x, q=question: f"{x} - {q['answers'][x]}",
        horizontal=True,
    )

profile = profile_from_answers(answers)
st.info(
    f"Profile: {profile.risk_level} | target annual log return = {profile.target_return:.1%} | "
    f"target annual volatility = {profile.target_risk:.1%}"
)

st.subheader("Step 3 - Portfolio settings")
method = st.selectbox(
    "Choose optimization method",
    ["min_variance", "max_return", "max_sharpe", "risk_parity"],
)
benchmark = st.text_input("Benchmark ticker", value=DEFAULT_BENCHMARK)
start_date = st.date_input("Start date", value=pd.to_datetime("2020-01-01"))
selected_tickers = st.multiselect("ETF universe", DEFAULT_TICKERS, default=DEFAULT_TICKERS)

if st.button("Run robo advisor"):
    with st.spinner("Loading data and optimizing portfolio..."):
        data = load_dataset(
            tickers=selected_tickers,
            benchmark=benchmark,
            start=str(start_date),
        )
        result = optimize_portfolio(
            returns=data["asset_returns"],
            method=method,
            target_return=profile.target_return,
            target_risk=profile.target_risk,
        )

        weights = result["weights"]
        portfolio = portfolio_returns(data["asset_returns"], weights)
        benchmark_returns = data["benchmark_returns"].squeeze()

        st.subheader("Step 4 - Allocation result")
        weights_df = weights.reset_index()
        weights_df.columns = ["ticker", "weight"]
        weights_df["weight"] = weights_df["weight"].round(4)
        st.dataframe(weights_df, use_container_width=True)
        st.write(f"Expected annual log return: {result['expected_return']:.2%}")
        st.write(f"Expected annual volatility: {result['expected_volatility']:.2%}")
        st.write(f"Data source used: {data['data_source']}")

        st.subheader("Step 5 - Visualizations")
        st.line_chart(
            pd.DataFrame(
                {
                    "Portfolio": cumulative_returns(portfolio),
                    "Benchmark": cumulative_returns(benchmark_returns),
                }
            )
        )
        st.line_chart(
            pd.DataFrame(
                {
                    "Portfolio": rolling_volatility(portfolio),
                    "Benchmark": rolling_volatility(benchmark_returns),
                }
            )
        )

        st.success("Finished. Each module can also be tested separately in Python.")

st.caption(
    "Educational use only. The app simplifies real-world suitability checks, optimization constraints, and ESG assessment."
)
