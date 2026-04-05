"""
config.py — All tunable parameters for the Wheel Strategy system.
Adjust these thresholds before running wheel_strategy.py.
"""

# ─────────────────────────────────────────────
# SCREENER FILTERS
# ─────────────────────────────────────────────

# Stock price range (cash-secured put capital requirements)
MIN_STOCK_PRICE = 10.0       # Avoid penny stocks
MAX_STOCK_PRICE = 150.0      # Keep CSP margin manageable

# Market cap (in USD billions)
MIN_MARKET_CAP_B = 2.0       # Mid-cap floor (~$2B)

# Implied Volatility range (annualised, expressed as decimal e.g. 0.30 = 30%)
MIN_IV = 0.20                # Too low → poor premium
MAX_IV = 0.80                # Too high → stock may be distressed

# Minimum average daily option volume (contracts) across all strikes
MIN_OPTION_VOLUME = 100

# Minimum average daily stock volume (shares)
MIN_AVG_VOLUME = 500_000

# Fundamental thresholds
MIN_CURRENT_RATIO = 1.0      # Short-term liquidity
MAX_DEBT_TO_EQUITY = 2.0     # Financial leverage ceiling
MIN_PROFIT_MARGIN = 0.0      # Must be profitable (or break-even)
MIN_REVENUE_GROWTH_YOY = -0.05  # Allow slight contraction (-5%)

# Earnings event blackout window (days)
# Skip stocks with earnings within this many days
EARNINGS_BLACKOUT_DAYS = 21

# Analyst sentiment: minimum fraction of Buy/Strong-Buy ratings
MIN_BUY_RATING_FRACTION = 0.40  # At least 40% analyst buys

# Number of top candidates to carry into options analysis
TOP_N_CANDIDATES = 10

# ─────────────────────────────────────────────
# UNIVERSE — candidate tickers to screen
# ─────────────────────────────────────────────
# A curated list of liquid, optionable US equities commonly
# used in income strategies. Expand or replace as needed.
UNIVERSE = [
    # Technology
    "AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD", "INTC", "CSCO",
    "ORCL", "IBM", "TXN", "QCOM", "MU", "AMAT", "KLAC",
    # Financials
    "JPM", "BAC", "WFC", "GS", "MS", "C", "AXP", "BLK",
    # Healthcare
    "JNJ", "PFE", "MRK", "ABBV", "UNH", "CVS", "CI", "HCA",
    # Consumer
    "WMT", "TGT", "COST", "HD", "LOW", "MCD", "SBUX", "NKE",
    # Energy
    "XOM", "CVX", "COP", "SLB", "OXY",
    # Industrials
    "CAT", "DE", "HON", "GE", "MMM", "BA",
    # ETFs (highly liquid, wheel-friendly)
    "SPY", "QQQ", "IWM", "GLD", "SLV",
]

# ─────────────────────────────────────────────
# OPTIONS RECOMMENDER PARAMETERS
# ─────────────────────────────────────────────

# Target delta range for cash-secured puts (absolute value)
# 0.25–0.35 is the classic "sweet spot" for premium vs. assignment risk
CSP_DELTA_MIN = 0.20
CSP_DELTA_MAX = 0.40

# Fallback OTM % if delta data is unavailable
# e.g. 0.05 → strike ~5% below current price
CSP_OTM_FALLBACK_PCT = 0.05

# Days-to-expiry targets (the recommender picks the expiry closest to ideal)
DTE_MIN = 21
DTE_MAX = 45
DTE_TARGET = 30            # Preferred DTE

# Minimum acceptable annualised return on capital for a CSP
MIN_ANNUALISED_ROC = 0.12  # 12% annualised

# Covered call target: how far OTM above assigned cost basis
CC_OTM_PCT = 0.02          # Strike ~2% above cost basis
CC_DTE_TARGET = 30

# Risk-free rate for Black-Scholes (annualised)
RISK_FREE_RATE = 0.05      # ~current T-bill yield

# ─────────────────────────────────────────────
# OUTPUT
# ─────────────────────────────────────────────
EXPORT_CSV = True
OUTPUT_FILE = "wheel_recommendations.csv"
