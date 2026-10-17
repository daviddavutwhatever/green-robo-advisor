"""Before/after comparison for all module enhancements of the Green Robo Advisor.

Runs the OLD modules (green_robo_advisor/prototype_backup) and the NEW modules
on exactly the same sample data and settings, then writes:
    docs/before_after/before_after.md   - tables for the documentation
    docs/before_after/*.png             - charts for the slides

Run from the project folder:  python compare_before_after.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from green_robo_advisor.data_module import get_etf_metadata, load_dataset
from green_robo_advisor.optimization import InfeasibleSettingsError, optimize_portfolio
from green_robo_advisor.prototype_backup import optimization as old_opt
from green_robo_advisor.questionnaire import score_to_profile

OUT = Path(__file__).resolve().parent / "docs" / "before_after"
OUT.mkdir(parents=True, exist_ok=True)

# Chart styling (validated colour-blind-safe categorical order)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
TEXT, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": TEXT,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 11,
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
})

data = load_dataset(start="2020-01-01", source="sample")
returns = data["asset_returns"]
tickers = list(returns.columns)
esg = get_etf_metadata().set_index("ticker")["esg_quality_score"]
balanced = score_to_profile(10)
aggressive = score_to_profile(20)
mu, sigma = old_opt.annualized_statistics(returns)
SETTINGS = {"min_weight": 0.05, "max_weight": 0.40, "esg_floor": 7.8}

lines: list[str] = ["# Before/after comparison (sample data, start 2020-01-01)\n"]

# --- Comparison 1: same profile and method, old vs new with constraints -------------
before = old_opt.optimize_portfolio(returns, "max_sharpe", balanced.target_return, balanced.target_risk)
after = optimize_portfolio(returns, "max_sharpe", balanced.target_return, balanced.target_risk,
                           esg_scores=esg, **SETTINGS)
before_rc = old_opt.risk_contributions(before["weights"].values, sigma)
before_esg = float(before["weights"] @ esg.reindex(tickers))

table = pd.DataFrame({
    "ESG score": esg.reindex(tickers),
    "Weight before": before["weights"],
    "Weight after": after["weights"],
    "Risk share before": before_rc / before_rc.sum(),
    "Risk share after": after["risk_contribution_share"],
})
lines.append("## 1. Balanced profile, max_sharpe\n")
lines.append(f"After = min weight {SETTINGS['min_weight']:.0%}, max weight {SETTINGS['max_weight']:.0%}, "
             f"ESG floor {SETTINGS['esg_floor']}.\n")
fmt = table.copy()
for col in fmt.columns[1:]:
    fmt[col] = fmt[col].map(lambda v: f"{v:.1%}")
lines.append(fmt.to_markdown() + "\n")
summary = pd.DataFrame({
    "Before": [f"{before['expected_return']:.2%}", f"{before['expected_volatility']:.2%}",
               f"{before['expected_return'] / before['expected_volatility']:.2f}", f"{before_esg:.2f}",
               f"{(before['weights'] > 1e-4).sum()} of 5", f"{before['weights'].max():.1%}"],
    "After": [f"{after['expected_return']:.2%}", f"{after['expected_volatility']:.2%}",
              f"{after['expected_return'] / after['expected_volatility']:.2f}", f"{after['esg_score']:.2f}",
              f"{(after['weights'] > 1e-4).sum()} of 5", f"{after['weights'].max():.1%}"],
}, index=["Expected return", "Expected volatility", "Return / volatility", "Portfolio ESG score",
          "ETFs used", "Largest weight"])
lines.append(summary.to_markdown() + "\n")

x = np.arange(len(tickers))
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.bar(x - 0.2, before["weights"], 0.38, color=SERIES[0], label="Before (no constraints)")
ax.bar(x + 0.2, after["weights"], 0.38, color=SERIES[1], label="After (5-40 %, ESG >= 7.8)")
for xi, (b, a) in enumerate(zip(before["weights"], after["weights"])):
    ax.text(xi - 0.2, b + 0.01, f"{b:.0%}", ha="center", fontsize=9, color=MUTED)
    ax.text(xi + 0.2, a + 0.01, f"{a:.0%}", ha="center", fontsize=9, color=MUTED)
ax.axhline(SETTINGS["max_weight"], color=MUTED, lw=1, ls="--")
ax.text(-0.45, SETTINGS["max_weight"] + 0.015, "max weight 40 %", ha="left", fontsize=9, color=MUTED)
ax.set_xticks(x, [f"{t}\nESG {esg[t]:.1f}" for t in tickers])
ax.set_ylabel("Portfolio weight")
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax.set_title("Max Sharpe weights: before vs after constraints")
ax.legend(frameon=False, loc="upper center")
fig.tight_layout(); fig.savefig(OUT / "weights_before_after.png", dpi=160); plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 4.6))
ax.bar(x - 0.2, before_rc / before_rc.sum(), 0.38, color=SERIES[0], label="Before")
ax.bar(x + 0.2, after["risk_contribution_share"], 0.38, color=SERIES[1], label="After")
ax.set_xticks(x, tickers)
ax.set_ylabel("Share of portfolio volatility")
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax.set_title("Where the risk comes from: risk contributions")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(OUT / "risk_contributions_before_after.png", dpi=160); plt.close(fig)

# --- Comparison 2: the crash case ------------------------------------------------------
lines.append("## 2. Aggressive profile, min_variance (target return 10 %)\n")
try:
    old_opt.optimize_portfolio(returns, "min_variance", aggressive.target_return, aggressive.target_risk)
    old_msg = "(no error)"
except Exception as exc:
    old_msg = f"{type(exc).__name__}: {exc}"
try:
    optimize_portfolio(returns, "min_variance", aggressive.target_return, aggressive.target_risk)
    new_msg = "(no error)"
except InfeasibleSettingsError as exc:
    new_msg = f"InfeasibleSettingsError: {exc}"
lines.append(f"- **Before:** `{old_msg}` - the Streamlit page crashes with a traceback.\n")
lines.append(f"- **After:** `{new_msg}` - shown as a red warning box in the app.\n")

# --- Comparison 3: ESG floor sweep ------------------------------------------------------
floors = np.round(np.arange(7.4, 8.61, 0.05), 2)
rows = []
for f in floors:
    try:
        r = optimize_portfolio(returns, "max_sharpe", 0.06, 0.10, esg_scores=esg,
                               min_weight=0.05, max_weight=0.40, esg_floor=float(f))
        rows.append({"floor": f, "feasible": True, "return": r["expected_return"],
                     "volatility": r["expected_volatility"], **r["weights"].to_dict()})
    except InfeasibleSettingsError:
        rows.append({"floor": f, "feasible": False})
sweep = pd.DataFrame(rows)
ok = sweep[sweep["feasible"]]
limit = ok["floor"].max()

lines.append("## 3. ESG floor sweep (max_sharpe, weights 5-40 %)\n")
show = ok[ok["floor"].isin([7.4, 7.6, 7.8, 8.0, 8.2])][["floor", "return", "volatility"] + tickers].copy()
for col in ["return", "volatility"] + tickers:
    show[col] = show[col].map(lambda v: f"{v:.1%}")
lines.append(show.to_markdown(index=False) + "\n")
lines.append(f"Floors above {limit:.2f} are infeasible: the app shows a warning with the highest reachable score.\n")

fig, ax = plt.subplots(figsize=(9, 4.6))
ax.stackplot(ok["floor"], [ok[t] for t in tickers], colors=SERIES, labels=tickers,
             edgecolor=SURFACE, linewidth=1.5)
ax.axvspan(limit + 0.025, floors.max() + 0.025, color=GRID, alpha=0.8)
ax.text((limit + floors.max()) / 2 + 0.025, 0.5, "infeasible\n(warning\nin app)", ha="center",
        va="center", fontsize=10, color=MUTED)
ax.set_xlim(floors.min(), floors.max() + 0.025)
ax.set_ylim(0, 1)
ax.set_xlabel("ESG floor (minimum weighted ESG score)")
ax.set_ylabel("Portfolio weight")
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax.set_title("Raising the ESG floor shifts weight to higher-scoring ETFs")
ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0))
fig.tight_layout(); fig.savefig(OUT / "esg_floor_weights.png", dpi=160); plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 4.2))
ax.plot(ok["floor"], ok["return"], color=SERIES[0], lw=2, marker="o", ms=5)
ax.axvspan(limit + 0.025, floors.max() + 0.025, color=GRID, alpha=0.8)
ax.set_xlim(floors.min(), floors.max() + 0.025)
ax.set_xlabel("ESG floor (minimum weighted ESG score)")
ax.set_ylabel("Expected annual log return")
ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.005))
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=1))
ax.text((limit + floors.max()) / 2 + 0.025, ok["return"].mean(), "infeasible", ha="center", fontsize=10, color=MUTED)
ax.set_title("The price of a higher ESG floor: expected return")
fig.tight_layout(); fig.savefig(OUT / "esg_floor_return.png", dpi=160); plt.close(fig)

# --- Comparison 4: risk parity accuracy ----------------------------------------------
old_rp = old_opt.optimize_portfolio(returns, "risk_parity", 0.06, 0.10)["weights"].values
new_rp = optimize_portfolio(returns, "risk_parity", 0.06, 0.10)
old_rc = old_opt.risk_contributions(old_rp, sigma)
lines.append("## 4. Side effect: more accurate risk parity\n")
rp = pd.DataFrame({"Risk share before": old_rc / old_rc.sum(),
                   "Risk share after": new_rp["risk_contribution_share"].values}, index=tickers)
lines.append(rp.map(lambda v: f"{v:.1%}").to_markdown() + "\n")
lines.append("Risk parity should give every ETF the same risk share (20 %). The old solver stopped early; "
             "the new solver uses a tighter tolerance and reaches equal shares.\n")

# --- Comparison 5: questionnaire - risk tolerance vs risk capacity --------------------
from green_robo_advisor.prototype_backup import questionnaire as old_q
from green_robo_advisor.questionnaire import profile_from_answers

lines.append("## 5. Questionnaire: risk tolerance vs risk capacity\n")
investors = {
    "A: wants growth, needs most money soon": {"goal": 4, "loss": 4, "horizon": 4, "reaction": 4,
                                               "liquidity": 1, "esg": 2},
    "B: wants growth, needs half": {"goal": 4, "loss": 4, "horizon": 4, "reaction": 4,
                                    "liquidity": 2, "esg": 4},
    "C: wants growth, no liquidity need, very green": {"goal": 4, "loss": 4, "horizon": 4, "reaction": 4,
                                                       "liquidity": 5, "esg": 5},
}
q_rows = []
for name, ans in investors.items():
    tolerance_only = {k: v for k, v in ans.items() if k in ("goal", "loss", "horizon", "reaction")}
    old_profile = old_q.profile_from_answers(tolerance_only)
    new_profile = profile_from_answers(ans)
    q_rows.append({"Investor": name, "Before: profile": old_profile.risk_level,
                   "After: tolerance": new_profile.risk_tolerance_level,
                   "After: liquidity need": new_profile.liquidity_need,
                   "After: profile": new_profile.risk_level,
                   "After: ESG floor": new_profile.suggested_esg_floor or "none"})
lines.append(pd.DataFrame(q_rows).to_markdown(index=False) + "\n")
lines.append("Before, all three investors got the same Growth profile and no ESG input. After, the liquidity "
             "answer caps the risk level and the ESG answer becomes the optimizer's ESG floor.\n")

# --- Comparison 6: data module - provenance and quality ------------------------------
lines.append("## 6. Data: provenance and data quality\n")
lines.append("- **Before:** a Yahoo failure was only printed in the terminal; the page showed one small text "
             "line 'Data source used: sample'. Assets and benchmark could come from different sources. "
             "Missing prices were filled without telling anyone.\n")
lines.append("- **After:** the app shows a green box (live data) or a yellow warning with the fallback reason, "
             "the common sample period, and this data-quality report:\n")
lines.append(data["quality_report"].to_markdown(index=False) + "\n")
lines.append(f"The bundled sample file has {int(data['quality_report']['missing_before_cleaning'].iloc[0])} "
             "missing prices per ticker; all are filled before returns are computed (0 NaN left).\n")

# --- Comparison 7: visualization - drawdown and summary ------------------------------
from green_robo_advisor.visualization import drawdown, performance_summary, portfolio_returns

lines.append("## 7. Diagnostics: drawdown and portfolio-vs-benchmark summary\n")
bench = data["benchmark_returns"].squeeze()
port_before = portfolio_returns(returns, before["weights"])
port_after = portfolio_returns(returns, after["weights"])
summary = pd.concat({"Before (unconstrained)": performance_summary(port_before, bench)["Portfolio"],
                     "After (constrained)": performance_summary(port_after, bench)["Portfolio"],
                     "Benchmark (ESGU)": performance_summary(port_after, bench)["Benchmark"]}, axis=1)
fmt_summary = summary.copy().astype(object)
for row in fmt_summary.index:
    fmt_summary.loc[row] = [f"{v:.2f}" if row in ("Sharpe ratio", "Growth of 1") else f"{v:.1%}"
                            for v in summary.loc[row]]
lines.append("Before, the app only showed growth and rolling volatility. After, it adds this table "
             "(historical, in-sample) and a drawdown chart:\n")
lines.append(fmt_summary.to_markdown() + "\n")

fig, ax = plt.subplots(figsize=(9, 4.6))
ax.plot(drawdown(bench).index, drawdown(bench).values, color=SERIES[0], lw=1.6, label="Benchmark (ESGU)")
ax.plot(drawdown(port_after).index, drawdown(port_after).values, color=SERIES[1], lw=1.6,
        label="Constrained portfolio")
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax.set_ylabel("Below previous peak")
ax.set_title("Drawdown: how deep the falls were")
ax.legend(frameon=False, loc="lower left")
fig.tight_layout(); fig.savefig(OUT / "drawdown.png", dpi=160); plt.close(fig)

# --- Comparison 8: Q3 consistency check and V3 correlation -------------------------
from green_robo_advisor.questionnaire import check_answer_consistency
from green_robo_advisor.visualization import correlation_matrix

lines.append("## 8. Questionnaire consistency check (Q3)\n")
contradictory = {"goal": 3, "loss": 1, "horizon": 3, "reaction": 5}
lines.append(f"Answers {contradictory}: before, accepted without comment "
             f"(profile {old_q.profile_from_answers(contradictory).risk_level}). After, same profile plus warning: "
             f"*{check_answer_consistency(contradictory)[0]}*\n")

lines.append("## 9. Correlation of daily returns (V3)\n")
corr = correlation_matrix(returns)
lines.append(corr.round(2).to_markdown() + "\n")
lines.append("Equity ETFs move together (0.68-0.83), equity vs bond barely (0.16-0.26). This is why the "
             "unconstrained max-Sharpe portfolio combines one equity ETF (ESGU) with one bond ETF (SUSC).\n")

fig, ax = plt.subplots(figsize=(6.4, 5.2))
image = ax.imshow(corr.values, cmap="Greens", vmin=0, vmax=1)
ax.set_xticks(range(len(corr)), corr.columns)
ax.set_yticks(range(len(corr)), corr.index)
ax.grid(False)
for i in range(len(corr)):
    for j in range(len(corr)):
        ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center", fontsize=11,
                color="white" if corr.values[i, j] > 0.6 else TEXT)
fig.colorbar(image, ax=ax, fraction=0.046)
ax.set_title("Correlation of daily returns")
fig.tight_layout(); fig.savefig(OUT / "correlation.png", dpi=160); plt.close(fig)

# --- Comparison 10: D5 extended sample data (5 vs 10 ETFs) ---------------------------
from green_robo_advisor.config import ALL_TICKERS

lines.append("## 10. Extended sample data: 5 vs 10 ETFs (D5)\n")
data10 = load_dataset(tickers=ALL_TICKERS, start="2020-01-01", source="sample")
rows10 = []
for label, rets in [("5 ETFs (original sample)", returns), ("10 ETFs (extended sample)", data10["asset_returns"])]:
    r = optimize_portfolio(rets, "max_sharpe", balanced.target_return, balanced.target_risk,
                           esg_scores=esg if len(rets.columns) == 5 else
                           get_etf_metadata().set_index("ticker")["esg_quality_score"],
                           max_weight=0.40, esg_floor=7.8)
    meta_esg = get_etf_metadata().set_index("ticker")["esg_quality_score"].reindex(rets.columns)
    best_esg = float(np.sort(meta_esg.values)[::-1][:2].sum() * 0.4 + np.sort(meta_esg.values)[::-1][2] * 0.2)
    rows10.append({"Universe": label, "ETFs used": int((r["weights"] > 0.005).sum()),
                   "Expected return": f"{r['expected_return']:.2%}", "Expected volatility": f"{r['expected_volatility']:.2%}",
                   "Return / volatility": f"{r['expected_return'] / r['expected_volatility']:.2f}",
                   "Highest reachable ESG (max 40 %)": f"{best_esg:.2f}"})
lines.append("Same settings: Balanced profile, max Sharpe, max 40 % per ETF, ESG floor 7.8.\n")
lines.append(pd.DataFrame(rows10).to_markdown(index=False) + "\n")
lines.append("A larger opportunity set gives the optimizer more ways to meet the same constraints. The green bond "
             "ETF (BGRN, ESG 9.0) and the ESG bond ETF (EAGG) also raise the highest reachable ESG score.\n")

(OUT / "before_after.md").write_text("\n".join(lines))
print("\n".join(lines))
print(f"Charts written to {OUT}")
