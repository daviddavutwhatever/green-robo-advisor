"""Project configuration used by all modules."""

ETF_UNIVERSE = {
    "ESGU": {
        "name": "iShares ESG Aware MSCI USA ETF",
        "asset_class": "Equity",
        "esg_rating": "A",
        "esg_quality_score": 7.1,
        "source_note": "MSCI ESG Fund Rating / iShares page",
    },
    "ESGD": {
        "name": "iShares ESG Aware MSCI EAFE ETF",
        "asset_class": "Equity",
        "esg_rating": "AAA",
        "esg_quality_score": 8.6,
        "source_note": "MSCI ESG Fund Rating / iShares page",
    },
    "ESGE": {
        "name": "iShares ESG Aware MSCI EM ETF",
        "asset_class": "Equity",
        "esg_rating": "AA",
        "esg_quality_score": 8.0,
        "source_note": "MSCI ESG Fund Rating / iShares page",
    },
    "SUSB": {
        "name": "iShares ESG Aware 1-5 Year USD Corporate Bond ETF",
        "asset_class": "Bond",
        "esg_rating": "AA",
        "esg_quality_score": 8.2,
        "source_note": "MSCI ESG Fund Rating / iShares page",
    },
    "SUSC": {
        "name": "iShares ESG Aware USD Corporate Bond ETF",
        "asset_class": "Bond",
        "esg_rating": "AA",
        "esg_quality_score": 7.7,
        "source_note": "MSCI ESG Fund Rating / iShares page",
    },
}

DEFAULT_TICKERS = list(ETF_UNIVERSE.keys())
DEFAULT_BENCHMARK = "ESGU"
TRADING_DAYS = 252
