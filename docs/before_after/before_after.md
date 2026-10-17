# Before/after comparison (sample data, start 2020-01-01)

## 1. Balanced profile, max_sharpe

After = min weight 5%, max weight 40%, ESG floor 7.8.

|      |   ESG score | Weight before   | Weight after   | Risk share before   | Risk share after   |
|:-----|------------:|:----------------|:---------------|:--------------------|:-------------------|
| ESGU |         7.1 | 30.0%           | 21.3%          | 55.0%               | 42.5%              |
| ESGD |         8.6 | 0.0%            | 11.0%          | 0.0%                | 18.0%              |
| ESGE |         8   | 0.0%            | 5.0%           | 0.0%                | 9.3%               |
| SUSB |         8.2 | 0.0%            | 22.8%          | 0.0%                | 7.9%               |
| SUSC |         7.7 | 70.0%           | 40.0%          | 45.0%               | 22.3%              |

|                     | Before   | After   |
|:--------------------|:---------|:--------|
| Expected return     | 4.74%    | 3.93%   |
| Expected volatility | 8.15%    | 8.01%   |
| Return / volatility | 0.58     | 0.49    |
| Portfolio ESG score | 7.52     | 7.80    |
| ETFs used           | 2 of 5   | 5 of 5  |
| Largest weight      | 70.0%    | 40.0%   |

## 2. Aggressive profile, min_variance (target return 10 %)

- **Before:** `OptimizationError: Min-variance failed: Positive directional derivative for linesearch` - the Streamlit page crashes with a traceback.

- **After:** `InfeasibleSettingsError: The target return of 10.00% is outside what these ETFs can deliver under the current constraints (possible range: 0.61% to 8.69%). Choose another profile, another method, or relax the constraints.` - shown as a red warning box in the app.

## 3. ESG floor sweep (max_sharpe, weights 5-40 %)

|   floor | return   | volatility   | ESGU   | ESGD   | ESGE   | SUSB   | SUSC   |
|--------:|:---------|:-------------|:-------|:-------|:-------|:-------|:-------|
|     7.4 | 5.2%     | 10.0%        | 40.0%  | 5.0%   | 5.0%   | 10.0%  | 40.0%  |
|     7.6 | 5.0%     | 9.6%         | 37.3%  | 5.0%   | 5.0%   | 12.7%  | 40.0%  |
|     7.8 | 3.9%     | 8.0%         | 21.3%  | 11.0%  | 5.0%   | 22.8%  | 40.0%  |
|     8   | 3.8%     | 8.5%         | 9.7%   | 29.1%  | 5.0%   | 16.3%  | 40.0%  |
|     8.2 | 3.4%     | 9.0%         | 5.0%   | 40.0%  | 5.0%   | 31.0%  | 19.0%  |

Floors above 8.25 are infeasible: the app shows a warning with the highest reachable score.

## 4. Side effect: more accurate risk parity

|      | Risk share before   | Risk share after   |
|:-----|:--------------------|:-------------------|
| ESGU | 19.1%               | 20.0%              |
| ESGD | 20.7%               | 20.0%              |
| ESGE | 20.7%               | 20.0%              |
| SUSB | 15.4%               | 20.0%              |
| SUSC | 24.0%               | 20.0%              |

Risk parity should give every ETF the same risk share (20 %). The old solver stopped early; the new solver uses a tighter tolerance and reaches equal shares.

## 5. Questionnaire: risk tolerance vs risk capacity

| Investor                                       | Before: profile   | After: tolerance   | After: liquidity need   | After: profile   | After: ESG floor   |
|:-----------------------------------------------|:------------------|:-------------------|:------------------------|:-----------------|:-------------------|
| A: wants growth, needs most money soon         | Growth            | Growth             | High                    | Conservative     | none               |
| B: wants growth, needs half                    | Growth            | Growth             | Medium                  | Balanced         | 7.8                |
| C: wants growth, no liquidity need, very green | Growth            | Growth             | Low                     | Growth           | 8.0                |

Before, all three investors got the same Growth profile and no ESG input. After, the liquidity answer caps the risk level and the ESG answer becomes the optimizer's ESG floor.

## 6. Data: provenance and data quality

- **Before:** a Yahoo failure was only printed in the terminal; the page showed one small text line 'Data source used: sample'. Assets and benchmark could come from different sources. Missing prices were filled without telling anyone.

- **After:** the app shows a green box (live data) or a yellow warning with the fallback reason, the common sample period, and this data-quality report:

| ticker           | source   | first_date   | last_date   |   price_rows |   missing_before_cleaning |   missing_share |   missing_after_cleaning |
|:-----------------|:---------|:-------------|:------------|-------------:|--------------------------:|----------------:|-------------------------:|
| ESGU             | sample   | 2020-01-01   | 2025-12-31  |         1566 |                         8 |          0.0051 |                        0 |
| ESGD             | sample   | 2020-01-01   | 2025-12-31  |         1566 |                         8 |          0.0051 |                        0 |
| ESGE             | sample   | 2020-01-01   | 2025-12-31  |         1566 |                         8 |          0.0051 |                        0 |
| SUSB             | sample   | 2020-01-01   | 2025-12-31  |         1566 |                         8 |          0.0051 |                        0 |
| SUSC             | sample   | 2020-01-01   | 2025-12-31  |         1566 |                         8 |          0.0051 |                        0 |
| ESGU (benchmark) | sample   | 2020-01-01   | 2025-12-31  |         1566 |                         8 |          0.0051 |                        0 |

The bundled sample file has 8 missing prices per ticker; all are filled before returns are computed (0 NaN left).

## 7. Diagnostics: drawdown and portfolio-vs-benchmark summary

Before, the app only showed growth and rolling volatility. After, it adds this table (historical, in-sample) and a drawdown chart:

|                   | Before (unconstrained)   | After (constrained)   | Benchmark (ESGU)   |
|:------------------|:-------------------------|:----------------------|:-------------------|
| Annual log return | 5.1%                     | 4.3%                  | 8.7%               |
| Annual volatility | 8.1%                     | 8.0%                  | 18.2%              |
| Sharpe ratio      | 0.62                     | 0.54                  | 0.48               |
| Max drawdown      | -20.4%                   | -19.2%                | -24.6%             |
| Worst day         | -2.2%                    | -2.0%                 | -3.6%              |
| Growth of 1       | 1.37                     | 1.31                  | 1.72               |

## 8. Questionnaire consistency check (Q3)

Answers {'goal': 3, 'loss': 1, 'horizon': 3, 'reaction': 5}: before, accepted without comment (profile Balanced). After, same profile plus warning: *You dislike losses, but say you would hold or buy more after a 15% fall.*

## 9. Correlation of daily returns (V3)

|      |   ESGU |   ESGD |   ESGE |   SUSB |   SUSC |
|:-----|-------:|-------:|-------:|-------:|-------:|
| ESGU |   1    |   0.83 |   0.75 |   0.22 |   0.26 |
| ESGD |   0.83 |   1    |   0.68 |   0.21 |   0.25 |
| ESGE |   0.75 |   0.68 |   1    |   0.16 |   0.2  |
| SUSB |   0.22 |   0.21 |   0.16 |   1    |   0.74 |
| SUSC |   0.26 |   0.25 |   0.2  |   0.74 |   1    |

Equity ETFs move together (0.68-0.83), equity vs bond barely (0.16-0.26). This is why the unconstrained max-Sharpe portfolio combines one equity ETF (ESGU) with one bond ETF (SUSC).

## 10. Extended sample data: 5 vs 10 ETFs (D5)

Same settings: Balanced profile, max Sharpe, max 40 % per ETF, ESG floor 7.8.

| Universe                  |   ETFs used | Expected return   | Expected volatility   |   Return / volatility |   Highest reachable ESG (max 40 %) |
|:--------------------------|------------:|:------------------|:----------------------|----------------------:|-----------------------------------:|
| 5 ETFs (original sample)  |           4 | 3.90%             | 7.62%                 |                  0.51 |                               8.32 |
| 10 ETFs (extended sample) |           6 | 4.57%             | 8.58%                 |                  0.53 |                               8.84 |

A larger opportunity set gives the optimizer more ways to meet the same constraints. The green bond ETF (BGRN, ESG 9.0) and the ESG bond ETF (EAGG) also raise the highest reachable ESG score.
