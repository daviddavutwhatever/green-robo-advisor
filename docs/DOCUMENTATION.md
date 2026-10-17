# Green Robo Advisor – one enhancement per module

**FinTech and Financial Intelligence – team project documentation**

## 1. Problem statement

When we ran the prototype (Phase 0), we found one weakness per module:

| Module | Weakness found in the baseline |
|---|---|
| `questionnaire.py` | Risk tolerance, liquidity needs and sustainability preference are not separated. An investor who needs the money next year can still get a Growth profile, and the ESG preference is never asked. |
| `data_module.py` | A Yahoo failure is only printed in the terminal. Assets and benchmark can come from different sources. Missing prices are filled silently. |
| `optimization.py` | Only "weights between 0 and 1". Max Sharpe puts 70 % in one ETF and 0 % in three others. ESG plays no role. Impossible settings crash the app with a solver message. |
| `visualization.py` | Only cumulative growth and rolling volatility. Investors feel the size of falls (drawdowns), which is not shown. No summary against the benchmark. |
| `app.py` | Assumptions are hidden in the code. Errors show a Python traceback. |

**User decision that should improve:** an investor should get a profile that reflects what they *want* and what they can *afford*, see where the data come from, state constraints (bounds, ESG), get an explanation when something is impossible, and see the downside risk of the result.

## 2. Overview of the enhancements (22 in total)

Every module got at least two enhancements. The number per module follows where the prototype was weakest.

| Module | # | Enhancements | Handout reference |
|---|---|---|---|
| `questionnaire.py` | **3** | **Q1** risk capacity (liquidity question caps the risk level) · **Q2** ESG preference → suggested ESG floor · **Q3** consistency check for contradictory answers | §4 Questionnaire, §9, §11 |
| `data_module.py` + `config.py` | **5** | **D1** data provenance (fallback reason, one source for ETFs and benchmark) · **D2** missing-ticker check · **D3** data-quality report · **D4** region metadata · **D5** extended sample data with 10 ESG ETFs | §4 Data/Metadata, Phase 2, §9 |
| `optimization.py` | **5** | **O1** weight bounds · **O2** ESG floor · **O3** mean-variance with risk aversion · **O4** feasibility check before and verification after · **O5** risk contributions | §4 Optimization, §12.1 |
| `visualization.py` | **3** | **V1** drawdown and max drawdown · **V2** portfolio-vs-benchmark summary · **V3** correlation heatmap | §4 Diagnostics, Phase 5, §11 Visualization |
| `app.py` (+ `ui.py`, `.streamlit/config.toml`) | **6** | **A1** sidebar with assumptions · **A2** readable errors · **A3** results in tabs · **A4** CSV downloads · **A5** modern fintech design · **A6** interactive Plotly charts | §4 Interface, Phase 6, §11 Web interface |
| `tests/` | | 53 automated tests, one file per module | Phase 7 |

## 3. Module contracts (what stayed stable)

Every module keeps its old function names, parameters and output fields. New things are only **added**, with defaults that reproduce the old behaviour. Tests compare against the original code in `prototype_backup/`.

| Module | Input (unchanged) | Output: old part (unchanged) | Output: added |
|---|---|---|---|
| `questionnaire.py` | `profile_from_answers(answers)` | `InvestorProfile`: total_score, risk_level, target_return, target_risk, explanation | risk_tolerance_level, liquidity_need, capacity_cap_applied, esg_preference, suggested_esg_floor |
| `data_module.py` | `load_dataset(tickers, benchmark, start, end, source)` | asset_prices, asset_returns, benchmark_prices, benchmark_returns, metadata, benchmark, data_source | fallback_used, fallback_reason, quality_report, sample_period, nan_in_returns; `region` column in metadata |
| `optimization.py` | `optimize_portfolio(returns, method, target_return, target_risk, risk_free_rate)` | weights, expected_return, expected_volatility, mu, sigma | optional min_weight, max_weight, esg_scores, esg_floor, risk_aversion; output risk_contributions, risk_contribution_share, esg_score, constraints, checks |
| `visualization.py` | `portfolio_returns`, `cumulative_returns`, `rolling_volatility`, `create_plots` | same series and keys | new functions `drawdown`, `max_drawdown`, `performance_summary`; `create_plots` adds drawdown keys and chart |
| `app.py` | user choices | same 5-step flow | sidebar, warnings, new outputs |

**Encapsulation test (handout §6):** the original call in `run_demo.py` still runs unchanged, and the tests prove that old inputs give old outputs. All 625 answer combinations of the original questionnaire give the same profile, the old dataset keys are identical, and the default optimizer gives the same weights.

## 4. What each enhancement does

### 4.1 questionnaire.py – 3 enhancements
- The four original questions still produce the **risk-tolerance** score with the old thresholds.
- **Q1** New question **"How much of this money might you need within the next 2 years?"** This is risk **capacity**: "Most of it" caps the profile at Conservative, "About half" at Balanced, and less than that leaves it uncapped. Capacity can only *lower* the risk level, never raise it.
- **Q2** New question **"How important is sustainability (ESG)?"** maps to a suggested ESG floor: 1–2 none, 3 → 7.6, 4 → 7.8, 5 → 8.0. The app uses this as the default ESG floor in the sidebar.
- **Q3** `check_answer_consistency()` warns about contradictions, e.g. "I dislike losses very much" together with "I would buy more after a 15 % fall", or a horizon under 1 year with a strong return goal. The warnings do not change the profile; they ask the user to double-check.

### 4.2 data_module.py + config.py – 5 enhancements
- **D2** `check_missing_tickers()`: a ticker that Yahoo returns without any prices is detected instead of silently kept.
- **D1** `download_prices_with_reason()`: records *why* the app fell back to sample data. If the assets fall back, the benchmark uses the same source, so the comparison stays consistent.
- **D3** `data_quality_report()`: per ticker, the source, first and last date, number of prices, missing prices before cleaning, and missing prices after cleaning.
- `load_dataset()` also returns the common sample period and the number of NaN left in returns. A sample shorter than 60 days gives a clear error.
- **D4** `config.py`: each ETF has a `region` (United States, Developed markets ex-US, Emerging markets, Global) and a `theme`.
- **D5** Extended sample data. The professor allows sample data instead of Yahoo, and the handout suggests about 10 ETFs. `data/generate_sample_data.py` adds five ESG ETFs (SUSA, DSI, ICLN, EAGG, BGRN) to the offline sample:
  - **Model:** a one-factor model, *new return = drift + beta × factor + noise*. The factor comes from the original ETFs (US equity, average equity or average bond returns), so correlations are realistic: SUSA vs ESGU 0.97, EAGG vs SUSC 0.87.
  - **Realistic features:** Student-t noise gives fat tails (ICLN kurtosis 3.6); noise scaled by recent factor volatility gives calm and turbulent periods; 8 price gaps per ETF, like the original file.
  - **Reproducible:** a fixed random seed, so the same file every time.
  - **Unchanged originals:** the original 5 columns are untouched, and `DEFAULT_TICKERS` stays the original 5, so all old results still hold. `ALL_TICKERS` has all 10, which the app uses by default.
  - **Illustrative scores:** the ESG scores of the new ETFs are teaching values, not official ratings.

### 4.3 optimization.py – 5 enhancements
- **O1** Bounds per ETF (`min_weight`, `max_weight`).
- **O2** ESG floor: weighted score `Σ wᵢ · ESGᵢ ≥ floor`.
- **O3** New `mean_variance` method: `return − λ/2 · variance`.
- **O4** `check_feasibility()` runs **before** solving and explains impossible settings with numbers (e.g. "highest reachable ESG score is 8.26").
- `validate_weights()` runs **after** solving: sum = 1, bounds and floor respected.
- **O5** Risk contributions show each ETF's share of total volatility.

### 4.4 visualization.py – 3 enhancements
- **V1** `drawdown()`: value ÷ running peak − 1, which is 0 at a new high and negative below it.
- `max_drawdown()`: the worst peak-to-trough loss.
- **V2** `performance_summary()`: annual log return, volatility, Sharpe ratio, max drawdown, worst day and growth of 1, for portfolio and benchmark on the same dates.
- **V3** `correlation_matrix()`: how strongly the ETFs move together, shown as a heatmap. Equity ETFs correlate 0.68–0.83, equity vs bond only 0.16–0.26. This explains why the optimizer combines one equity and one bond ETF.

### 4.5 app.py – 6 enhancements
- **A1 Sidebar:** data source (auto / yfinance / sample), min/max weight, ESG floor (pre-filled from Q2), risk-free rate. Risk aversion appears when mean_variance is chosen. Questions are grouped (Risk tolerance / Risk capacity / Sustainability), with metrics for tolerance, liquidity need and ESG floor, and warnings for Q1 caps and Q3 contradictions.
- **A2 Readable errors:** data problems (e.g. an unknown benchmark) and infeasible settings show a red box with a tip instead of a Python traceback.
- **A3 Tabs:** results are organised in four tabs:
  - **Allocation:** weights, ESG score, risk share, constraint checks ✅/❌, risk-contribution chart.
  - **Performance & risk:** summary table, growth, rolling volatility, drawdown.
  - **Diversification:** correlation heatmap, asset class and region.
  - **Data quality:** quality report.

  The data-source box and three key metrics stay above the tabs.
- **A4 Downloads:** the allocation and the performance summary can be downloaded as CSV files.
- **A5 Modern fintech design** (`ui.py` + `.streamlit/config.toml`):
  - **Theme and type:** a dark navy theme with Sora headings and IBM Plex Sans text.
  - **Fixed colour meaning:** teal = portfolio and equities, gold = ESG and bonds, slate = benchmark, coral = risk.
  - **Header:** an **ESG ticker tape** with all 10 ETFs and their scores (it pauses on hover and stops for users who prefer reduced motion).
  - **Steps and profile:** numbered steps, and a profile card with five key figures.
  - **Controls:** answer options shown as selectable pills, a full-width gradient "Build my portfolio" button, outline download buttons and pill tabs.
  - **Results:** a KPI row with return, volatility, Sharpe, ESG score and ETFs used.
- **A6 Interactive charts:** Plotly replaces the static charts.
  - **Allocation:** horizontal bars of weight vs share of risk, coloured by asset class.
  - **Time series:** growth, drawdown (filled) and rolling volatility, portfolio vs benchmark.
  - **Correlation:** an annotated heatmap.
  - **Interaction:** hover shows exact values, and you can zoom into a period. Dates are always passed explicitly as the x-axis (handout §12.4), and a test checks this.

## 5. GenAI prompts used (handout §10 format)

One prompt per module, each limited to that module and its contract:

> **Questionnaire:** I am extending a classroom Python robo advisor. Work only in questionnaire.py. Add one question about liquidity needs (risk capacity) that can cap the risk level, and one question about ESG importance that maps to a suggested ESG floor. Keep all existing function names, parameters and return fields unchanged; old answer dictionaries must give the old profile. Explain each changed line for a beginner and suggest tests that check the new questions change the profile.

> **Data:** Work only in data_module.py and config.py. Add a check for tickers without prices, record why a fallback to sample data happened, keep assets and benchmark on the same source, and add a per-ticker data-quality report. Add a region field to the ETF metadata. Do not remove or rename any key returned by load_dataset. Add tests that run without internet.

> **Optimization:** Work in optimization.py. Add minimum and maximum weight per ETF, a minimum weighted ESG score, and a mean_variance method with risk aversion. Keep the existing optimize_portfolio parameters and return dictionary unchanged; new parameters must be optional. Check feasibility before optimizing and raise a plain-language error. Return risk contributions. Add tests for weights summing to one and respecting bounds.

> **Visualization:** Work only in visualization.py. Add a drawdown function, a max drawdown and a summary table of portfolio vs benchmark. Keep existing functions unchanged. Add a test that drawdown is never positive and uses the same dates.

> **Questionnaire (Q3):** Work only in questionnaire.py. Add a function that returns plain-language warnings for contradictory answers without changing the profile. Add tests for one contradictory and one consistent set of answers.

> **Visualization (V3):** Work only in visualization.py. Add a correlation matrix of daily returns for a heatmap. Test that it is symmetric, has ones on the diagonal and stays between −1 and 1.

> **Data (D5):** Write a script that adds five ESG ETFs to the offline sample with a one-factor model built from the existing returns, Student-t noise and volatility clustering. Use a fixed seed and keep the existing columns unchanged. Add tests that the old default still loads 5 ETFs and that the new ETFs have plausible correlations and volatilities.

> **Design (A5, A6):** Put all styling and Plotly chart builders in a separate ui.py so app.py stays readable. Use a dark finance theme with fixed colour meanings, pass dates explicitly to every chart, and do not change any module contract.

> **App:** Work only in app.py. Move the new settings into the sidebar with help texts (A1), catch errors with readable messages (A2), organise results in tabs (A3) and add CSV downloads (A4). Show the outputs of the other modules. Add headless tests with Streamlit's AppTest.

**Accepted change:** the files listed in §2. Every AI change was checked by running the old and the new code side by side (`compare_before_after.py`) and by the tests in §7.

## 6. How to run

```
conda env create -f environment.yml
conda activate green-robo-advisor
python run_demo.py                                   # shows each module's enhancement in the terminal
python -m pytest tests -v                            # 53 tests
python compare_before_after.py                       # tables + charts in docs/before_after/
python -m streamlit run green_robo_advisor/app.py    # web app
```

The original prototype is unchanged in `green_robo_advisor/prototype_backup/`.

## 7. Test result

```
53 passed in 3.9s
```

| File | Tests | What they prove |
|---|---|---|
| `test_questionnaire.py` | 16 | Old answers → old profile (all 625 combinations); Q1 liquidity caps but never raises risk; Q2 ESG answer → floor; Q3 contradictions warned without changing the profile |
| `test_data_module.py` | 8 | Old keys identical; no NaN in returns, dates aligned; D1 fallback reason (simulated Yahoo failure); D2 missing ticker detected; D3 quality report; D4 region; D5 10 ETFs available, default still 5, plausible correlations and volatilities |
| `test_constrained_optimization.py` | 16 | O1/O2 weights sum to 1 and respect bounds and floor for all 5 methods; O3 risk aversion lowers volatility; O4 impossible settings explained; old calls give old weights; O5 contributions add up |
| `test_visualization.py` | 5 | V1 drawdown ≤ 0 on the same dates, −25 % hand example; growth starts near 1; V2 summary consistent; V3 correlation valid |
| `test_app.py` | 4 | Whole app runs headless: A1 sidebar source, A2 readable errors (infeasible bound, unknown benchmark), A3 four tabs, A4 two CSV downloads |
| `test_ui.py` | 4 | A6 charts use dates on the x-axis; bars coloured by asset class; A5 header lists every ETF and escapes text; profile card content |

Full output: `docs/test_output.txt`.

## 8. Before-and-after examples

All on the same data: the bundled sample, starting 2020-01-01. Full tables: `docs/before_after/before_after.md`.

**Questionnaire.** Three investors with identical risk-tolerance answers:

| Investor | Before | After |
|---|---|---|
| Needs most money within 2 years | Growth | Conservative (capped) |
| Needs about half | Growth | Balanced (capped), ESG floor 7.8 |
| No liquidity need, very green | Growth | Growth, ESG floor 8.0 |

**Data.** Before, the fallback was visible only in the terminal. After, the app shows a yellow warning with the reason and a quality report. That report revealed **8 missing prices per ETF** in the sample file, which the old code filled silently.

**Optimization.** Balanced profile, max Sharpe. After = 5–40 % bounds and ESG floor 7.8:

| | Before | After |
|---|---|---|
| Weights ESGU / ESGD / ESGE / SUSB / SUSC | 30 / 0 / 0 / 0 / 70 % | 21 / 11 / 5 / 23 / 40 % |
| ETFs used, largest weight | 2 of 5, 70 % | 5 of 5, 40 % |
| Portfolio ESG score | 7.52 | 7.80 |
| Expected return / volatility | 4.74 % / 8.15 % | 3.93 % / 8.01 % |

Aggressive + min-variance: before, a crash with "Positive directional derivative for linesearch". After: "The target return of 10.00 % is outside what these ETFs can deliver (possible range: 0.61 % to 8.69 %)."

**Questionnaire Q3.** The answers "dislike losses very much" + "buy more after a 15 % fall" were accepted silently before. Now the profile stays the same, but the app asks the user to double-check.

**Visualization.** The new summary, historical and in-sample:

| | Before (unconstrained) | After (constrained) | Benchmark |
|---|---|---|---|
| Max drawdown | −20.4 % | −19.2 % | −24.6 % |
| Sharpe ratio | 0.62 | 0.54 | 0.48 |
| Worst day | −2.2 % | −2.0 % | −3.6 % |

**Correlation (V3):** equity ETFs move together (0.68–0.83), while equity and bond ETFs barely do (0.16–0.26).

**Extended sample data (D5).** Same settings (Balanced, max Sharpe, max 40 %, ESG floor 7.8):

| Universe | ETFs used | Return / volatility | Highest reachable ESG |
|---|---|---|---|
| 5 ETFs (original) | 4 | 0.51 | 8.32 |
| 10 ETFs (extended) | 6 | 0.53 | 8.84 |

**App.** Before: a plain white page with static charts, one long scroll, and tracebacks on errors. After: a dark fintech design with an ESG ticker tape, a profile card, KPI cards, a sidebar, readable error boxes, four result tabs, interactive charts and CSV downloads. Screenshots are in `docs/screenshots/`.

**Interpretation:** the constraints buy diversification, a higher ESG score and a slightly smaller drawdown. In exchange, the historical return is lower. Following the handout's warning, this is not automatically an improvement. The investor states a preference, and the model shows what it costs.

**Side effect found during testing:** the old risk parity did not actually equalise risk (shares between 15 % and 24 %). With a tighter solver tolerance, it now gives exactly 20 % each.

## 9. Assumptions and limitations per module

| Module | Assumption | Limitation |
|---|---|---|
| `questionnaire.py` | Summed answers measure risk tolerance; the 2-year liquidity need is a fair proxy for risk capacity; the ESG answer maps linearly to a floor | Not a regulated suitability test. The thresholds and floor values are our choices, not calibrated. Income, wealth and loss capacity are not asked |
| `data_module.py` | Time interpolation is acceptable for a few missing prices; the bundled sample can replace live data; a one-factor model is enough to create the five extra ETFs | The sample prices are synthetic, and the new ETFs inherit the original sample's market history. Interpolation invents prices for missing days. The new ESG scores are illustrative |
| `optimization.py` | Historical mean and covariance of daily log returns estimate the future; ESG scores are fixed and comparable | Estimates are noisy, so weights can move a lot. The same bounds apply to every ETF (no asset-class limits). The ESG score is a single educational number |
| `visualization.py` | Daily rebalancing to fixed weights | The backtest is in-sample (same data used to optimize), so results look better than they would out of sample |
| `app.py` | The user changes one setting at a time; the browser can load Google Fonts | Runs are not stored, so two settings cannot be compared side by side. Without internet, the fonts fall back to system fonts. The custom CSS relies on Streamlit's internal page structure and may need small updates after a Streamlit upgrade |

**Why the results might not generalise:** the weights are fitted on the same synthetic sample they are evaluated on. With live data or another start date, the allocation, the reachable ESG floor and the drawdowns will change.

## 10. Validation checklist (handout §14)

| Check | Evidence |
|---|---|
| Environment | `environment.yml` (+ pytest, tabulate) |
| Pipeline | `python run_demo.py` prints one block per module enhancement |
| App | `tests/test_app.py` runs the whole app headless (no browser) |
| Data | `nan_in_returns = 0`; dates aligned (test); quality report |
| Weights | `checks` in every result; 5 parametrised tests |
| ESG | ESG metric in the app; floor sweep chart; infeasibility message with the highest reachable score |
| Charts | Growth starts near 1; drawdown ≤ 0 (tests); same dates for all series |
| Interface | Grouped questions, help texts, warnings instead of tracebacks |

## 11. Disclaimer

Teaching prototype only. The questionnaire is not a suitability assessment. ESG scores, expected returns and volatility are simplified or historical estimates. This is not investment advice.
