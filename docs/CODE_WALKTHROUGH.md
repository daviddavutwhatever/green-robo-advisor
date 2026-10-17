# Code walkthrough – what every change does (for the team)

Read this next to the code. The handout says every team member must be able to explain the change without the AI tool, so the last section lists questions the professor may ask.

**22 enhancements, at least two per module:** questionnaire 3 (Q1–Q3), data 5 (D1–D5), optimization 5 (O1–O5), visualization 3 (V1–V3), app 6 (A1–A6). The IDs also appear in the code comments, so you can search for them.

**One idea runs through all five modules:** we only *add* things. Old function names, inputs and outputs stay the same, and the defaults give the old behaviour. That is the module contract.

## questionnaire.py (Q1 risk capacity · Q2 ESG preference · Q3 consistency check)

**In one sentence:** we now ask separately what risk you *want* (tolerance) and what risk you can *afford* (capacity), plus how much you care about ESG.

- **New fields in `InvestorProfile`** (`risk_tolerance_level`, `liquidity_need`, `capacity_cap_applied`, `esg_preference`, `suggested_esg_floor`). Each has a default value, so old code that creates a profile still works.
- **Two new entries in `QUESTIONS`:** `liquidity` and `esg`. Every question now has a `group` label so the app can show headings.
- **`NON_TOLERANCE_IDS = {"liquidity", "esg"}`:** these two answers are *not* added to the risk score. Otherwise an investor who cares a lot about ESG would automatically get a riskier profile, which makes no sense.
- **`LEVELS` and `LEVEL_ORDER`:** the four risk levels with the same targets as before, ordered from safe to risky. The order lets us compare levels ("is Growth riskier than Balanced?").
- **`LIQUIDITY_MAPPING`:** answer → (label, highest level allowed). 1 = "Most of it" → Conservative at most; 2 = "About half" → Balanced at most; 3–5 = no cap.
- **`ESG_FLOOR_MAPPING`:** answer → suggested ESG floor (1–2 none, 3 → 7.6, 4 → 7.8, 5 → 8.0).
- **`profile_from_answers`, step by step:**
  1. Add up only the tolerance answers → `score_to_profile` with the **unchanged** thresholds.
  2. If liquidity was asked and the tolerance level is riskier than the cap, lower the level to the cap, set `capacity_cap_applied = True` and write an explanation.
  3. If ESG was asked, store the answer and the suggested floor.

  **Analogy:** someone may *want* to drive fast (tolerance), but on an icy road they *can't* (capacity). The safer of the two wins.
- **Q3 `check_answer_consistency(answers)`:** four simple `if` rules, each producing one plain-language warning:
  1. Dislikes losses (loss ≤ 2) but would hold or buy more after a 15 % fall (reaction ≥ 4).
  2. Accepts larger losses (loss ≥ 4) but would sell after a fall (reaction ≤ 2).
  3. Horizon under 1 year but high returns are important (goal ≥ 4).
  4. Long horizon (≥ 4) but may need a lot of the money within 2 years (liquidity ≤ 2).

  `a.get("loss", 3)` uses 3 as a neutral value when a question was not answered. The warnings are stored in `profile.consistency_warnings`; they **do not change** the profile. **Why not fix the answers automatically?** We cannot know which of the two answers is wrong, so the user should decide.

## data_module.py and config.py (D1 provenance · D2 missing tickers · D3 quality report · D4 region · D5 extended sample)

**In one sentence:** the app now tells you where the data came from, why, and how much had to be repaired.

- **D5 `data/generate_sample_data.py`:** builds the extended offline sample with 10 ETFs. Step by step:
  1. Read the original 5 ETFs and compute their daily log returns.
  2. Build **factors**: ESGU's returns (US equity), the average of the 3 equity ETFs, and the average of the 2 bond ETFs.
  3. For each new ETF: `beta × factor + noise`. Examples:
     - SUSA = 0.95 × ESGU + small noise, so it behaves almost like ESGU (correlation 0.97).
     - ICLN = 1.25 × equity factor + big noise, a volatile clean-energy fund.
  4. **Student-t noise** (`rng.standard_t(df=4)`) has more extreme days than a normal distribution, as in real markets.
  5. **Volatility clustering:** the noise is multiplied by the factor's recent 21-day volatility, so turbulent periods are turbulent for all ETFs.
  6. **Drift:** a constant is added so that the average annual return matches a chosen target.
  7. 8 random gaps per new ETF, like the original file. `SEED = 2026` makes the result identical every time.

  The original 5 columns are never changed, so all old results stay the same. `config.py` keeps `DEFAULT_TICKERS` = the original 5 (the contract) and adds `ALL_TICKERS` = all 10 (used by the app).
- **D4 `config.py`:** each ETF has a `region`. `get_etf_metadata()` shows it as a new column.
- **D2 `check_missing_tickers(prices, tickers)`:** returns the tickers that are missing or completely empty. Yahoo sometimes returns a column full of NaN for a blocked or delisted ticker. Before, that went unnoticed.
- **D1 `download_prices_with_reason(...)`:** the same as the old `download_prices`, but it returns a third value: *why* it fell back to sample data. The old `download_prices` still exists and simply calls the new one, so its contract is kept.
- **D1 Same source for the benchmark:** if the ETFs fell back to sample data, the benchmark is loaded from sample data too. Otherwise you could compare synthetic portfolio data with a real benchmark, which is meaningless.
- **D3 `data_quality_report(raw, cleaned, source)`:** one row per ticker with the source, first and last date, number of prices, missing before cleaning and missing after cleaning. It revealed that the sample file has 8 gaps per ETF, which the old code filled without telling anyone.
- **`load_dataset` new keys:** `fallback_used`, `fallback_reason`, `quality_report`, `sample_period` and `nan_in_returns`. There is also a guard: fewer than 60 common days → clear error.
- **`try: import yfinance`:** if yfinance is not installed, the sample data still work instead of crashing at import.

## visualization.py (V1 drawdown · V2 summary · V3 correlation)

**In one sentence:** besides "how much did it grow", we now show "how deep did it fall".

- **V1 `drawdown(log_returns)`:** first the growth of 1 (`cumulative_returns`), then the highest value so far (`cummax()`), then `growth / peak − 1`. It is 0 on a day with a new high, and −0.20 when you are 20 % below the last high.
- **V1 `max_drawdown`:** the most negative drawdown, i.e. the worst fall from a peak. Test example: prices 100 → 120 → 90 → 110 give −25 % (from 120 down to 90).
- **V2 `performance_summary(portfolio, benchmark, rf)`:** one table with two columns.
  - Annual log return: mean × 252.
  - Annual volatility: std × √252.
  - Sharpe ratio: (return − rf) / volatility.
  - Max drawdown.
  - Worst day: `expm1` converts the worst log return into a normal percentage.
  - Growth of 1: the last value of the growth series.
- **V3 `correlation_matrix(asset_returns)`:** one line, `asset_returns.corr()`. It gives a number between −1 and +1 for every pair of ETFs: +1 = always move together, 0 = unrelated. On the sample data the three equity ETFs correlate 0.68–0.83, the two bond ETFs 0.74, and equity vs bond only 0.16–0.26. **Why it matters:** diversification only helps between assets that do not move together. That is why the optimizer likes one equity ETF plus one bond ETF.
- **`create_plots`** additionally saves `drawdown.png` and `correlation.png` and adds new keys. The old keys are untouched.

**Why drawdown matters:** volatility says how bumpy the ride is. Drawdown says how much money an investor actually saw disappear, which is what makes people panic and sell.

## optimization.py (O1 bounds · O2 ESG floor · O3 mean-variance · O4 feasibility · O5 risk contributions)

### New pieces at the top

```python
TOLERANCE = 1e-6
METHODS = ["min_variance", "max_return", "max_sharpe", "risk_parity", "mean_variance"]
```
`TOLERANCE` is a small allowed rounding error. Computers give results like 0.39999999 instead of 0.40, so a check like "weight ≤ 0.40" needs a small margin. `METHODS` is one list used by the optimizer, the app dropdown and the tests, so the method names are written down only once.

```python
class InfeasibleSettingsError(OptimizationError):
```
A new error type meaning "your settings contradict each other". Because it **inherits** from `OptimizationError`, any old code that catches `OptimizationError` also catches it. That is how we keep the contract.

```python
@dataclass
class PortfolioConstraints:
    min_weight: float = 0.0
    max_weight: float = 1.0
    esg_scores: pd.Series | None = None
    esg_floor: float | None = None
```
A small container that keeps all conditions together, so we pass one object around instead of four separate values. The defaults (0, 1, no ESG) are exactly the old prototype's rules.

### `portfolio_esg_score(weights, esg_scores)`
Computes `w₁·ESG₁ + w₂·ESG₂ + …`. Example: 50 % in an ETF with score 8 and 50 % in one with score 7 gives 7.5.

### `_aligned_esg(...)`
Puts the ESG scores in the same order as the return columns. If you set a floor but give no scores, or a ticker has no score, it raises a clear error instead of silently using wrong numbers.

### `_base_constraints(esg, esg_floor)` and `_base_bounds(n, min, max)`
These existed before; they now take the new settings as **optional** inputs.
- Equality constraint: `sum(w) − 1 = 0` (fully invested).
- Inequality constraint (new): `ESG score − floor ≥ 0`. SciPy's rule is that `"ineq"` functions must be **≥ 0** when the condition holds.
- Bounds: `(min_weight, max_weight)` for each ETF instead of `(0, 1)`.

### `_solve(objective, ...)`
The one place where SciPy's `minimize` is called. All five methods use it, so they share the same bounds, constraints and solver settings.
- `method="SLSQP"` is the solver that supports bounds and constraints (the same one the prototype used implicitly).
- `ftol=1e-12` makes the solver keep going until the result is very precise. This is why risk parity is now exact.
- After solving, `np.clip` removes tiny noise such as −0.00000001, and dividing by the sum makes the total exactly 100 %.

### `_linear_range(values, c, esg)`
Answers "what is the smallest and largest possible value of `Σ wᵢ·valueᵢ`?" under the constraints. Since this is linear, SciPy's `linprog` solves it exactly. We use it twice:
- `values = ESG scores`: the highest reachable ESG score.
- `values = expected returns`: the reachable return range.

### `check_feasibility(...)`
Runs **before** optimizing. Each `if` answers one question and raises an error with numbers the user understands:
1. **Bounds:** with 5 ETFs, a 25 % minimum needs 125 %, which is impossible. A 15 % maximum allows only 75 %, also impossible.
2. **ESG:** if the floor is above the best reachable score, it says what the best reachable score is.
3. **min_variance:** if the target return is outside the reachable range, it prints the range.
4. **max_return:** it computes the lowest possible volatility. If the target risk is below it, it is impossible.

### `validate_weights(...)`
Runs **after** optimizing and returns a dictionary such as `{"weights_sum_to_one": True, ...}`. If any check is False, we raise an error rather than show a wrong portfolio. The app displays these checks as ✅/❌.

### The method functions
`min_variance_for_target_return`, `max_return_for_risk`, `max_sharpe_ratio` and `risk_parity` keep their names and first parameters. Each now builds its objective and passes it to `_solve`.

`mean_variance` is new:
```python
-(portfolio_return(w, mu) - 0.5 * risk_aversion * portfolio_volatility(w, sigma) ** 2)
```
It maximises "return minus a penalty for variance". The minus sign in front is there because `minimize` minimises. A higher `risk_aversion` makes the penalty heavier, so the solution moves to lower-risk portfolios. With the sample data: λ = 0.5 gives 100 % ESGU, and λ = 8 gives 27 % ESGU / 73 % SUSC.

### `optimize_portfolio(...)`
The public entry point.
1. Estimate `mu` and `sigma` (unchanged).
2. Pack the settings into `PortfolioConstraints`.
3. `check_feasibility`, which stops early with a readable message if needed.
4. Call the chosen method.
5. `validate_weights`.
6. Return the **old keys unchanged** plus the new keys.

`risk_contributions` sum to the portfolio volatility, and `risk_contribution_share` is the same divided by volatility, so it sums to 100 %.

## app.py and ui.py (A1 sidebar · A2 readable errors · A3 tabs · A4 downloads · A5 design · A6 interactive charts)

- **A5 `ui.py` + `.streamlit/config.toml`:** all design code lives in `ui.py`, so `app.py` stays a readable list of steps.
  - **`config.toml`:** sets the dark theme colours that Streamlit uses for every widget (sliders, checkboxes, selected options).
  - **`CSS`:** a block of style rules injected once with `st.markdown(ui.inject_css(), unsafe_allow_html=True)`. It sets the fonts, the gradient primary button, the pill tabs and the pill-shaped answers.
  - **Helpers:** `hero()`, `step()`, `stat()` and `profile_card()` return small pieces of HTML for the header, the numbered steps, the KPI cards and the profile card. `html.escape()` makes sure text can never break the page.
  - **Ticker tape:** the chips are written twice in a row and moved left with a CSS animation. When the first copy has scrolled out, the second sits exactly where the first started, so the loop is seamless.
  - **Colour tokens** at the top (`TEAL`, `GOLD`, ...) mean the same thing everywhere: teal = portfolio and equity, gold = ESG and bonds, slate = benchmark.
- **A6 Plotly charts** (`line_chart`, `allocation_chart`, `correlation_chart` in `ui.py`). Each one builds a `go.Figure`, adds traces (`go.Scatter` for lines, `go.Bar` for bars, `go.Heatmap`) and applies one shared layout (`_layout`): transparent background, theme font, grid colour and unified hover. `st.plotly_chart(fig, use_container_width=True)` shows it. The x-axis is always `series.index` (the dates), never the row number, and a test checks this.
- **A3 Tabs:** `st.tabs([...])` creates four tabs, and everything inside `with tab_alloc:` appears in the first tab. The data-source box and three key metrics stay above the tabs because the user should always see them.
  - **Allocation:** weights, risk share, constraint checks, download.
  - **Performance & risk:** summary table, growth, volatility, drawdown, download.
  - **Diversification:** correlation heatmap, asset class and region.
  - **Data quality:** quality report.
- **A4 `st.download_button`:** turns a DataFrame into CSV text (`to_csv()`), and the browser saves it as a file. One button for the allocation, one for the performance summary.
- **Heatmap in the app:** `corr.style.background_gradient(cmap="Greens")` colours each cell by its value: darker green means a higher correlation.
- **Q3 warnings:** a loop shows one `st.warning` per message in `profile.consistency_warnings`.
- **Questionnaire section:** prints a bold heading whenever the question `group` changes. It then shows three metrics (tolerance, liquidity need, suggested ESG floor), and a yellow `st.warning` with the explanation when the capacity cap was applied.
- **Data source selectbox** in the sidebar (auto / yfinance / sample). Its value is passed to `load_dataset(..., source=source)`.
- **ESG checkbox and slider default to the questionnaire answer.** `value=profile.suggested_esg_floor is not None` ticks the box automatically when ESG matters to the investor. This is how two modules work together through their contracts only.
- **After loading:** a green `st.success` box (live data, with period and days) or a yellow `st.warning` (fallback, with the reason), plus an expander with the quality report.
- **Step 5:** `performance_summary` is shown as a formatted table (percentages vs plain numbers), plus `st.area_chart` of the drawdowns.
- **A1 `st.sidebar...`** puts the sliders in the left sidebar. The defaults (0 %, 100 %, no ESG floor, 0 % risk-free rate) reproduce the old app, which is what makes the before/after comparison fair.
- **ESG floor slider:** only appears when the checkbox is ticked (`if use_esg_floor:`). Its range is the lowest to highest ETF score.
- **Risk aversion slider:** only shown when `mean_variance` is selected, because no other method uses it.
- **A2 `try / except InfeasibleSettingsError`:** catches the readable error and shows it with `st.error`, then `st.stop()` ends the run cleanly instead of showing a Python traceback.
- **Data loading is also wrapped** in `try/except`. Before, a mistyped benchmark ticker crashed the page.
- **Results:** a table with weight, ESG score and risk share; three metrics (return, volatility, ESG score); the constraint checks; a bar chart of risk contributions.

## run_demo.py
The original output is untouched. Below it, one block per module shows its enhancement in the terminal: the capped profile, the data provenance and quality report, the constrained run with an impossible ESG floor, and the drawdown/summary table.

## tests/ (53 tests, one file per module)
- `@pytest.fixture` loads the sample data once and shares it between tests.
- `@pytest.mark.parametrize` runs one test several times with different inputs (e.g. all 5 methods), so 8 test functions become 16 test cases.
- `pytest.raises(InfeasibleSettingsError, match="...")` passes only if that error is raised **and** its message contains the text.
- The contract tests import the **old** code from `prototype_backup` and check that old inputs give old outputs (questionnaire, data and optimizer).
- `test_app.py` uses Streamlit's `AppTest`: it runs the whole app **without a browser**, sets sidebar values, clicks the button, and checks the tabs, error boxes and download buttons.
- `monkeypatch` temporarily replaces a function during one test. `test_fallback_is_reported_when_yahoo_fails` replaces the Yahoo download with one that always fails, so we can test the fallback without internet.

## compare_before_after.py
Runs the old and new modules on identical data and settings and writes the tables and charts in `docs/before_after/`: the optimization comparison, the ESG floor sweep, three example investors for the questionnaire, the data-quality report, and the drawdown chart with the summary table.

## Questions the professor might ask

**Questionnaire, data and diagnostics**

- **What is the difference between risk tolerance and risk capacity?** Tolerance is how much risk you *want* or can stand emotionally. Capacity is how much loss you can *afford*, for example because you need the money soon. A suitable profile respects the lower of the two, so liquidity can only lower the risk level.
- **Why is the ESG answer not part of the risk score?** Caring about sustainability says nothing about risk appetite. Adding it to the score would push green investors into riskier profiles.
- **How did you make sure the questionnaire contract holds?** A test runs all 5⁴ = 625 combinations of the original questions through the old and the new code and checks that the profiles are identical.
- **Why must the benchmark come from the same source as the ETFs?** Comparing a synthetic portfolio with a real benchmark mixes two different worlds, so the comparison would be meaningless.
- **What did the quality report reveal?** The sample file has 8 missing prices per ETF. They are filled by time interpolation, and 0 NaN remain in the returns.
- **Why show drawdown when you already show volatility?** Volatility measures how much returns fluctuate. Drawdown measures the actual loss from a peak, which is what investors experience and react to. The constrained portfolio had a max drawdown of −19 % vs −25 % for the benchmark.
- **Are the summary numbers a forecast?** No. They are historical and in-sample: the same data were used to choose the weights.

- **Why warn about contradictory answers instead of fixing them? (Q3)** We cannot know which answer is the wrong one. Real advisors ask the client again, and the warning does the same.
- **What does the correlation heatmap tell you? (V3)** Equity ETFs move together (0.68–0.83), and equity vs bond barely (0.16–0.26). Combining assets with low correlation is what reduces risk, so the optimizer pairs ESGU with SUSC.
- **How did you test the app without clicking? (A1–A4)** Streamlit's `AppTest` runs the app headless. It sets the sidebar, clicks "Run", and checks the four tabs, the error messages and the two download buttons.
- **Why tabs? (A3)** The page shows much more than before. Tabs keep it readable: what to hold, how it performed, why it is diversified, and how good the data are.

- **Is the extended sample data real? (D5)** No. It is synthetic, built from the original sample with a one-factor model. That is fine for teaching, because the method is what matters, but the numbers say nothing about real markets.
- **Why build the new ETFs from the old ones instead of random numbers? (D5)** Random independent series would have zero correlation with the others, and the optimizer would see them as perfect diversifiers. Using the existing returns as factors gives realistic relationships: ESG equity moves with equity, green bonds with bonds.
- **Why put the design in a separate file? (A5)** Modularization again: `app.py` describes *what* the app does, and `ui.py` *how it looks*. You can change the colours without touching the logic.
- **Why Plotly? (A6)** Hover shows exact values and you can zoom into a period, e.g. the 2024 drawdown. The handout lists Plotly as an optional interface upgrade and warns to pass dates explicitly, which a test checks.

**Optimization**

1. **Why can an ESG floor make the problem infeasible?** The weighted score can never exceed what the highest-scoring ETFs give once the bounds are respected. With 5–40 % bounds, at most 40 % can sit in ESGD (8.6), so the maximum is 8.26.
2. **Is the constrained portfolio better?** Not automatically. It has a lower historical return estimate for similar risk, but it is diversified and meets the investor's ESG preference. It solves a different objective.
3. **Why does return fall when the floor rises?** The highest-return ETF in the sample (ESGU) has the lowest ESG score (7.1). Forcing a higher score moves weight away from it.
4. **What did you keep stable?** The function name, the first five parameters and all five old output keys. A test proves that old calls give the old weights.
5. **Why check feasibility before solving?** A solver that fails only says it failed. A check beforehand can say *why* and by how much, which is what a user needs.
6. **Why did risk parity change?** The old solver stopped before risk was really equal (15–24 %). A tighter tolerance reaches 20 % each, and a test checks it.
7. **Main limitation?** Everything rests on historical estimates from synthetic sample data, evaluated in-sample.
