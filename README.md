# Green Robo Advisor – one enhancement per module

Put it online for the class: see DEPLOY.md (free link via Streamlit Community Cloud)

Start here:
- `docs/DOCUMENTATION.md`    – problem, enhancements, module contracts, GenAI prompts, tests, before/after, assumptions & limitations per module
- `docs/CODE_WALKTHROUGH.md` – every change explained in plain language, plus likely professor questions
- `docs/before_after/`       – comparison tables (before_after.md) and charts
- `docs/test_output.txt`     – pytest result (53 passed)

Run:
    conda env create -f environment.yml
    conda activate green-robo-advisor
    python run_demo.py
    python -m pytest tests -v
    python compare_before_after.py
    python -m streamlit run green_robo_advisor/app.py

Enhancements (22 in total, at least two per module; IDs also appear in code comments):
- questionnaire.py  (3) – Q1 risk capacity cap · Q2 ESG preference -> ESG floor · Q3 consistency check
- data_module.py    (5) – D1 provenance & same source · D2 missing-ticker check · D3 data-quality report · D4 region · D5 extended sample data (10 ESG ETFs)
- optimization.py   (5) – O1 weight bounds · O2 ESG floor · O3 mean-variance · O4 feasibility check · O5 risk contributions
- visualization.py  (3) – V1 drawdown · V2 summary vs benchmark · V3 correlation heatmap
- app.py + ui.py    (6) – A1 sidebar · A2 readable errors · A3 result tabs · A4 CSV downloads · A5 modern fintech design · A6 interactive Plotly charts

Screenshots of the app: docs/screenshots/
Regenerate the extended sample data: python green_robo_advisor/data/generate_sample_data.py

Original prototype (unchanged): green_robo_advisor/prototype_backup/
New files: tests/ (6 files), green_robo_advisor/ui.py, .streamlit/config.toml, data/generate_sample_data.py, compare_before_after.py, docs/
