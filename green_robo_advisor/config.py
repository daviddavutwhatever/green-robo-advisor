"""Project configuration used by all modules."""

ETF_UNIVERSE = {
    "ESGU": {
        "name": "iShares ESG Aware MSCI USA ETF",
        "asset_class": "Equity",
        "region": "United States",
        "theme": "Core ESG",
        "esg_rating": "A",
        "esg_quality_score": 7.1,
        "source_note": "MSCI ESG Fund Rating / iShares page",
    },
    "ESGD": {
        "name": "iShares ESG Aware MSCI EAFE ETF",
        "asset_class": "Equity",
        "region": "Developed markets ex-US",
        "theme": "Core ESG",
        "esg_rating": "AAA",
        "esg_quality_score": 8.6,
        "source_note": "MSCI ESG Fund Rating / iShares page",
    },
    "ESGE": {
        "name": "iShares ESG Aware MSCI EM ETF",
        "asset_class": "Equity",
        "region": "Emerging markets",
        "theme": "Core ESG",
        "esg_rating": "AA",
        "esg_quality_score": 8.0,
        "source_note": "MSCI ESG Fund Rating / iShares page",
    },
    "SUSB": {
        "name": "iShares ESG Aware 1-5 Year USD Corporate Bond ETF",
        "asset_class": "Bond",
        "region": "United States",
        "theme": "Short-term credit",
        "esg_rating": "AA",
        "esg_quality_score": 8.2,
        "source_note": "MSCI ESG Fund Rating / iShares page",
    },
    "SUSC": {
        "name": "iShares ESG Aware USD Corporate Bond ETF",
        "asset_class": "Bond",
        "region": "United States",
        "theme": "Corporate credit",
        "esg_rating": "AA",
        "esg_quality_score": 7.7,
        "source_note": "MSCI ESG Fund Rating / iShares page",
    },
    # --- D5: five more ETFs for the extended offline sample (synthetic prices, see
    #     data/generate_sample_data.py). ESG ratings and scores are illustrative
    #     teaching values, not official ratings. ---
    "SUSA": {
        "name": "iShares MSCI USA ESG Select ETF",
        "asset_class": "Equity",
        "region": "United States",
        "theme": "ESG select",
        "esg_rating": "AA",
        "esg_quality_score": 7.6,
        "source_note": "Illustrative teaching value",
    },
    "DSI": {
        "name": "iShares MSCI KLD 400 Social ETF",
        "asset_class": "Equity",
        "region": "United States",
        "theme": "Social index",
        "esg_rating": "A",
        "esg_quality_score": 7.4,
        "source_note": "Illustrative teaching value",
    },
    "ICLN": {
        "name": "iShares Global Clean Energy ETF",
        "asset_class": "Equity",
        "region": "Global",
        "theme": "Clean energy",
        "esg_rating": "AA",
        "esg_quality_score": 8.8,
        "source_note": "Illustrative teaching value",
    },
    "EAGG": {
        "name": "iShares ESG Aware U.S. Aggregate Bond ETF",
        "asset_class": "Bond",
        "region": "United States",
        "theme": "Aggregate bonds",
        "esg_rating": "AA",
        "esg_quality_score": 7.9,
        "source_note": "Illustrative teaching value",
    },
    "BGRN": {
        "name": "iShares USD Green Bond ETF",
        "asset_class": "Bond",
        "region": "Global",
        "theme": "Green bonds",
        "esg_rating": "AAA",
        "esg_quality_score": 9.0,
        "source_note": "Illustrative teaching value",
    },
}

# The original five ETFs stay the default, so old calls give old results (module contract).
DEFAULT_TICKERS = ["ESGU", "ESGD", "ESGE", "SUSB", "SUSC"]
# D5: all ETFs available in the extended sample data
ALL_TICKERS = list(ETF_UNIVERSE.keys())
DEFAULT_BENCHMARK = "ESGU"
TRADING_DAYS = 252
