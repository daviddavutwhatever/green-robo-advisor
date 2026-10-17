"""Module 5: Streamlit web app that combines all modules.

Team enhancements in this module (6):
- A1 Sidebar with assumptions: data source, weight bounds, ESG floor (pre-filled from the
     questionnaire), risk-free rate. Risk aversion appears next to the method that uses it.
- A2 Readable errors: data problems and infeasible settings show a message box with a tip
     instead of a Python traceback.
- A3 Results in tabs: Allocation | Performance & risk | Diversification | Data quality.
- A4 Download: the allocation and the performance summary can be downloaded as CSV files.
- A5 Modern design: dark finance theme (.streamlit/config.toml), fonts, cards, pill buttons
     and tabs, and an ESG ticker tape in the header (styles live in ui.py).
- A6 Interactive charts: Plotly charts with hover and zoom instead of static line charts.
The app also displays the new outputs of the other modules (Q1-Q3, D1-D5, O1-O5, V1-V3).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make "import green_robo_advisor" work however the app is started
# (locally from the project folder, or on Streamlit Community Cloud).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from green_robo_advisor import ui
from green_robo_advisor.config import ALL_TICKERS, DEFAULT_BENCHMARK
from green_robo_advisor.data_module import get_etf_metadata, load_dataset
from green_robo_advisor.optimization import (
    METHODS,
    InfeasibleSettingsError,
    OptimizationError,
    optimize_portfolio,
)
from green_robo_advisor.questionnaire import QUESTIONS, profile_from_answers
from green_robo_advisor.visualization import (
    correlation_matrix,
    cumulative_returns,
    drawdown,
    performance_summary,
    portfolio_returns,
    rolling_volatility,
)

METHOD_LABELS = {
    "min_variance": "Minimum variance for my target return",
    "max_return": "Maximum return for my target risk",
    "max_sharpe": "Best return per unit of risk (max Sharpe)",
    "risk_parity": "Equal risk from every ETF (risk parity)",
    "mean_variance": "Return vs risk trade-off (mean-variance)",
}
PLOTLY_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}

st.set_page_config(page_title="Green Robo Advisor", page_icon="🌿", layout="wide")
st.markdown(ui.inject_css(), unsafe_allow_html=True)                                   # A5

metadata = get_etf_metadata()
esg_scores = metadata.set_index("ticker")["esg_quality_score"]
st.markdown(ui.hero(metadata), unsafe_allow_html=True)                                  # A5 ticker tape

# ---------------------------------------------------------------------------
# Step 1 - questionnaire (Q1-Q3)
# ---------------------------------------------------------------------------
st.markdown(ui.step(1, "Your investor profile",
                    "Six short questions. The first four measure the risk you want, the last two "
                    "what you can afford and how green you want to invest."), unsafe_allow_html=True)


def ask(question: dict) -> int:
    return st.radio(
        question["text"],
        options=list(question["answers"].keys()),
        format_func=lambda x, q=question: q["answers"][x],
        horizontal=True,
        key=f"q_{question['id']}",
    )


answers = {}
tolerance = [q for q in QUESTIONS if q.get("group") == "Risk tolerance"]
others = [q for q in QUESTIONS if q.get("group") != "Risk tolerance"]
st.markdown('<p class="gr-group">Risk tolerance</p>', unsafe_allow_html=True)
left, right = st.columns(2, gap="large")
for i, question in enumerate(tolerance):
    with (left if i % 2 == 0 else right):
        answers[question["id"]] = ask(question)
left, right = st.columns(2, gap="large")
for column, question in zip([left, right], others):
    with column:
        st.markdown(f'<p class="gr-group">{question["group"]}</p>', unsafe_allow_html=True)
        answers[question["id"]] = ask(question)

profile = profile_from_answers(answers)
st.markdown(ui.profile_card(profile), unsafe_allow_html=True)
if profile.capacity_cap_applied:
    st.warning("Your profile was capped because of your liquidity need (see above).", icon="🛡️")
for message in profile.consistency_warnings:                                              # Q3
    st.warning(f"Please double-check your answers: {message}", icon="⚠️")

# ---------------------------------------------------------------------------
# A1 Sidebar - model assumptions (defaults reproduce the original prototype)
# ---------------------------------------------------------------------------
st.sidebar.markdown("## Data")
source = st.sidebar.selectbox(
    "Price-data source", ["auto", "yfinance", "sample"], index=2,
    help="sample = the bundled offline data with 10 ESG ETFs (reproducible). "
         "auto = try Yahoo Finance first, fall back to the sample.",
)
st.sidebar.markdown("## Constraints")
min_weight = st.sidebar.slider(
    "Minimum weight per ETF", 0.0, 0.30, 0.0, 0.01,
    help="Every selected ETF must get at least this share. Too high makes the problem infeasible.",
)
max_weight = st.sidebar.slider(
    "Maximum weight per ETF", 0.10, 1.0, 1.0, 0.05,
    help="No ETF may exceed this share. A lower cap forces diversification; 1.0 = no cap.",
)
use_esg_floor = st.sidebar.checkbox(
    "Require a minimum ESG score",
    value=profile.suggested_esg_floor is not None,
    help="Ticked automatically when sustainability is at least moderately important to you.",
)
esg_floor = None
if use_esg_floor:
    esg_floor = st.sidebar.slider(
        "ESG floor (weighted score)", float(esg_scores.min()), float(esg_scores.max()),
        float(profile.suggested_esg_floor or 7.8), 0.1,
        help=f"Scores range from {esg_scores.min():.1f} to {esg_scores.max():.1f} in this universe.",
    )
st.sidebar.markdown("## Market")
risk_free_rate = st.sidebar.slider(
    "Risk-free rate", 0.0, 0.06, 0.0, 0.005, format="%.3f",
    help="Used by max Sharpe and the Sharpe ratios: excess return is measured above this rate.",
)
st.sidebar.caption("Change one setting at a time and compare the results.")

# ---------------------------------------------------------------------------
# Step 2 - portfolio setup
# ---------------------------------------------------------------------------
st.markdown(ui.step(2, "Portfolio setup", "Choose how the optimizer should judge a good portfolio."),
            unsafe_allow_html=True)
col_method, col_bench, col_date = st.columns([2.2, 1, 1], gap="medium")
with col_method:
    method = st.selectbox("Optimization method", METHODS, format_func=METHOD_LABELS.get,
                          help="Different objectives give different meanings of a good portfolio.")
    risk_aversion = 3.0
    if method == "mean_variance":
        risk_aversion = st.slider("Risk aversion", 0.5, 10.0, 3.0, 0.5,
                                  help="Objective: return - (risk aversion / 2) x variance.")
with col_bench:
    benchmark = st.text_input("Benchmark ticker", value=DEFAULT_BENCHMARK)
with col_date:
    start_date = st.date_input("Start date", value=pd.to_datetime("2020-01-01"))
selected_tickers = st.multiselect("ETF universe", ALL_TICKERS, default=ALL_TICKERS,
                                  help="Remove ETFs to see how the opportunity set changes the result.")
with st.expander("ETF details: asset class, region, theme and ESG score"):
    st.dataframe(metadata.drop(columns=["name"]).set_index("ticker"), use_container_width=True)

run = st.button("Build my portfolio", type="primary", use_container_width=True)

if run:
    if len(selected_tickers) < 2:
        st.warning("Select at least two ETFs to build a portfolio.")
        st.stop()

    with st.spinner("Loading prices and optimizing..."):
        # A2: readable errors instead of tracebacks
        try:
            data = load_dataset(tickers=selected_tickers, benchmark=benchmark, start=str(start_date), source=source)
        except Exception as exc:
            st.error(f"The price data could not be loaded: {exc}")
            st.info("Check the benchmark ticker and start date, or choose 'sample' as data source.")
            st.stop()
        try:
            result = optimize_portfolio(
                returns=data["asset_returns"], method=method,
                target_return=profile.target_return, target_risk=profile.target_risk,
                risk_free_rate=risk_free_rate, min_weight=min_weight, max_weight=max_weight,
                esg_scores=esg_scores, esg_floor=esg_floor, risk_aversion=risk_aversion,
            )
        except InfeasibleSettingsError as exc:
            st.error(f"**These settings cannot be satisfied at the same time.** {exc}")
            st.info("Relax one constraint in the sidebar, choose another method, or add ETFs to the universe.")
            st.stop()
        except OptimizationError as exc:
            st.error(f"The optimizer did not find a valid portfolio: {exc}")
            st.stop()

    weights = result["weights"]
    portfolio = portfolio_returns(data["asset_returns"], weights)
    benchmark_returns = data["benchmark_returns"].squeeze()
    summary = performance_summary(portfolio, benchmark_returns, risk_free_rate)
    expected_sharpe = (result["expected_return"] - risk_free_rate) / result["expected_volatility"]

    # ---------------------------------------------------------------------------
    # Step 3 - results
    # ---------------------------------------------------------------------------
    st.markdown(ui.step(3, "Your portfolio"), unsafe_allow_html=True)
    st.markdown(ui.source_badge(data), unsafe_allow_html=True)                       # D1
    if data["fallback_used"]:
        st.warning(f"Live data were not available. {data['fallback_reason']}")
    floor_text = "no floor" if esg_floor is None else f"floor {esg_floor:.1f}"
    st.markdown('<div class="gr-stats">' + "".join([
        ui.stat("Expected return", f"{result['expected_return']:.2%}", "annual, log", "gr-accent"),
        ui.stat("Expected volatility", f"{result['expected_volatility']:.2%}", "annual"),
        ui.stat("Sharpe ratio", f"{expected_sharpe:.2f}", f"risk-free {risk_free_rate:.1%}"),
        ui.stat("Portfolio ESG score", f"{result['esg_score']:.2f}", floor_text, "gr-esg"),
        ui.stat("ETFs used", f"{int((weights > 0.005).sum())} of {len(weights)}", f"largest {weights.max():.0%}"),
    ]) + "</div>", unsafe_allow_html=True)
    st.write("")

    # A3: results organised in tabs
    tab_alloc, tab_perf, tab_div, tab_data = st.tabs(
        ["Allocation", "Performance & risk", "Diversification", "Data quality"]
    )

    with tab_alloc:
        chart_col, table_col = st.columns([1.35, 1], gap="large")
        with chart_col:
            st.markdown("**Where the money goes and where the risk comes from**")
            st.plotly_chart(ui.allocation_chart(weights, result["risk_contribution_share"], metadata),  # A6, O5
                            use_container_width=True, config=PLOTLY_CONFIG)
        with table_col:
            weights_df = pd.DataFrame({
                "ticker": weights.index,
                "weight": weights.values.round(4),
                "ESG score": esg_scores.reindex(weights.index).values,
                "risk share": result["risk_contribution_share"].values.round(4),
            })
            st.dataframe(
                weights_df.set_index("ticker").style.format(
                    {"weight": "{:.1%}", "risk share": "{:.1%}", "ESG score": "{:.1f}"}),
                use_container_width=True, height=min(420, 38 * (len(weights_df) + 1)),
            )
            check_labels = {"weights_sum_to_one": "Weights sum to 100%", "min_weight_respected": "Minimum weight respected",
                            "max_weight_respected": "Maximum weight respected", "esg_floor_respected": "ESG floor respected"}
            st.markdown("  \n".join(f"{'✅' if ok else '❌'} {check_labels.get(name, name)}"           # O4
                                     for name, ok in result["checks"].items()))
            st.download_button("Download allocation (CSV)",                             # A4
                               data=weights_df.to_csv(index=False).encode("utf-8"),
                               file_name="green_robo_allocation.csv", mime="text/csv")

    with tab_perf:
        st.markdown("**Portfolio vs benchmark** (historical, same dates)")             # V2
        st.dataframe(
            summary.style.format(
                {"Portfolio": "{:.2%}", "Benchmark": "{:.2%}"},
                subset=pd.IndexSlice[["Annual log return", "Annual volatility", "Max drawdown", "Worst day"], :],
            ).format("{:.2f}", subset=pd.IndexSlice[["Sharpe ratio", "Growth of 1"], :]),
            use_container_width=True,
        )
        st.download_button("Download performance summary (CSV)",                         # A4
                           data=summary.to_csv().encode("utf-8"),
                           file_name="green_robo_performance.csv", mime="text/csv")
        st.markdown("**Growth of 1** invested at the start")
        st.plotly_chart(ui.line_chart(cumulative_returns(portfolio), cumulative_returns(benchmark_returns),
                                      y_format=".2f"), use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("**Drawdown**: how far below its previous peak the investment is")   # V1
        st.plotly_chart(ui.line_chart(drawdown(portfolio), drawdown(benchmark_returns),
                                      y_format=".0%", fill=True), use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("**Rolling volatility** over 21 trading days, annualized")
        st.plotly_chart(ui.line_chart(rolling_volatility(portfolio).dropna(),
                                      rolling_volatility(benchmark_returns).dropna(), y_format=".0%", height=300),
                        use_container_width=True, config=PLOTLY_CONFIG)

    with tab_div:
        st.markdown("**Correlation of daily returns**: near 1 move together, low values diversify")  # V3
        st.plotly_chart(ui.correlation_chart(correlation_matrix(data["asset_returns"])),
                        use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown("**Asset class, region and theme**")                                # D4, D5
        st.dataframe(metadata.set_index("ticker").reindex(weights.index)[["name", "asset_class", "region", "theme"]]
                     .assign(weight=weights.map("{:.1%}".format)), use_container_width=True)

    with tab_data:
        st.dataframe(data["quality_report"].set_index("ticker"), use_container_width=True)  # D3
        st.caption(f"Missing prices are filled by time interpolation. Missing values left in the "
                   f"return sample: {data['nan_in_returns']}.")

st.markdown('<p class="gr-legal">Teaching prototype for FinTech and Financial Intelligence. The questionnaire '
            'is not a suitability assessment, ESG scores are simplified, and results are historical estimates, '
            'not investment advice.</p>', unsafe_allow_html=True)
