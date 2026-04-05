"""
screener.py — Fundamental + liquidity + IV screening for Wheel candidates.

Flow per ticker:
  1. Fetch info dict (price, fundamentals, analyst data)
  2. Apply hard filters (price, market cap, volume, fundamentals)
  3. Check IV range and earnings blackout
  4. Score surviving candidates and return ranked shortlist
"""

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

import config
from data_fetcher import (
    get_ticker_info,
    get_analyst_ratings,
    get_next_earnings_date,
    get_options_expirations,
    get_historical_volatility,
)


# ──────────────────────────────────────────────
# Individual ticker evaluation
# ──────────────────────────────────────────────

def _passes_filters(symbol: str, info: dict) -> tuple[bool, str]:
    """
    Apply all hard-filter rules to a ticker.
    Returns (True, '') if the ticker passes, or (False, reason) if it fails.
    """
    # — Price range
    price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
    if not (config.MIN_STOCK_PRICE <= price <= config.MAX_STOCK_PRICE):
        return False, f"price ${price:.2f} out of range"

    # — Market cap
    mktcap = info.get("marketCap") or 0
    if mktcap < config.MIN_MARKET_CAP_B * 1e9:
        return False, f"market cap ${mktcap/1e9:.1f}B below floor"

    # — Average stock volume
    avg_vol = info.get("averageVolume") or info.get("averageDailyVolume10Day") or 0
    if avg_vol < config.MIN_AVG_VOLUME:
        return False, f"avg volume {avg_vol:,} too low"

    # — Current ratio (liquidity)
    current_ratio = info.get("currentRatio")
    if current_ratio is not None and current_ratio < config.MIN_CURRENT_RATIO:
        return False, f"current ratio {current_ratio:.2f} < {config.MIN_CURRENT_RATIO}"

    # — Debt-to-equity
    de = info.get("debtToEquity")
    if de is not None and de > config.MAX_DEBT_TO_EQUITY * 100:
        # yfinance returns D/E as percentage (e.g. 150 = 1.5x)
        return False, f"D/E {de/100:.2f}x above ceiling"

    # — Profit margin
    pm = info.get("profitMargins")
    if pm is not None and pm < config.MIN_PROFIT_MARGIN:
        return False, f"profit margin {pm:.1%} negative"

    # — Revenue growth YoY
    rev_growth = info.get("revenueGrowth")
    if rev_growth is not None and rev_growth < config.MIN_REVENUE_GROWTH_YOY:
        return False, f"revenue growth {rev_growth:.1%} too low"

    # — Earnings blackout window
    next_earnings = get_next_earnings_date(symbol)
    if next_earnings is not None:
        days_to_earnings = (next_earnings - datetime.now()).days
        if 0 <= days_to_earnings <= config.EARNINGS_BLACKOUT_DAYS:
            return False, f"earnings in {days_to_earnings}d (blackout)"

    # — Analyst sentiment
    buy_frac = get_analyst_ratings(info)
    if buy_frac < config.MIN_BUY_RATING_FRACTION:
        return False, f"analyst buy fraction {buy_frac:.0%} below threshold"

    return True, ""


def _check_iv(symbol: str, info: dict) -> tuple[bool, float]:
    """
    Check that implied volatility is in the desirable range.
    yfinance provides impliedVolatility on the info dict for some tickers;
    for others we fall back to 30-day historical volatility.
    Returns (passes: bool, iv_value: float).
    """
    # Try IV from options chain summary first
    iv = None

    # yfinance doesn't expose a clean per-stock IV on info; we derive it from
    # the ATM put on the nearest monthly expiry (done in options_analyzer).
    # Here we use historical vol as a proxy for the screener pass/fail.
    hv = get_historical_volatility(symbol)
    if hv is not None:
        iv = hv

    if iv is None:
        # If we can't compute volatility at all, give the stock the benefit of the doubt
        return True, 0.0

    passes = config.MIN_IV <= iv <= config.MAX_IV
    return passes, iv


def _check_option_liquidity(symbol: str) -> bool:
    """
    Verify that the ticker has listed options and sufficient option volume.
    We check the nearest expiry for total put volume.
    """
    exps, ticker_obj = get_options_expirations(symbol)
    if not exps or ticker_obj is None:
        return False

    # Fetch nearest expiry chain
    try:
        chain = ticker_obj.option_chain(exps[0])
        put_vol = chain.puts["volume"].fillna(0).sum()
        return put_vol >= config.MIN_OPTION_VOLUME
    except Exception:
        return False


# ──────────────────────────────────────────────
# Scoring
# ──────────────────────────────────────────────

def _score_candidate(info: dict, iv: float) -> float:
    """
    Return a composite score (higher = better Wheel candidate).

    Components:
      - IV attractiveness: reward IVs in the middle of the acceptable band
      - Analyst sentiment
      - Earnings quality (forward P/E vs trailing P/E — improvement proxy)
      - Free cash flow margin
      - Revenue growth
    """
    score = 0.0

    # IV score: peak at midpoint of [MIN_IV, MAX_IV]
    iv_mid = (config.MIN_IV + config.MAX_IV) / 2
    iv_range = (config.MAX_IV - config.MIN_IV) / 2
    iv_score = max(0.0, 1.0 - abs(iv - iv_mid) / iv_range)
    score += iv_score * 30  # weight: 30 pts

    # Analyst buy fraction
    buy_frac = get_analyst_ratings(info)
    score += buy_frac * 20  # weight: 20 pts

    # FCF margin (freeCashflow / totalRevenue)
    fcf = info.get("freeCashflow") or 0
    revenue = info.get("totalRevenue") or 1
    fcf_margin = fcf / revenue if revenue else 0
    score += min(fcf_margin * 100, 20)  # cap at 20 pts

    # Revenue growth
    rev_growth = info.get("revenueGrowth") or 0
    score += min(max(rev_growth * 100, 0), 15)  # cap at 15 pts

    # Earnings yield (1 / forwardPE) relative to risk-free rate
    fwd_pe = info.get("forwardPE")
    if fwd_pe and fwd_pe > 0:
        earnings_yield = 1 / fwd_pe
        excess_yield = max(0, earnings_yield - config.RISK_FREE_RATE)
        score += min(excess_yield * 100, 15)  # cap at 15 pts

    return round(score, 2)


# ──────────────────────────────────────────────
# Main screening entry point
# ──────────────────────────────────────────────

def run_screener(universe: list[str] | None = None) -> pd.DataFrame:
    """
    Screen all tickers in `universe` (defaults to config.UNIVERSE).

    Returns a DataFrame of passing candidates sorted by composite score,
    limited to config.TOP_N_CANDIDATES rows.

    Columns: symbol, price, market_cap_b, avg_volume, iv, score, reject_reason
    """
    if universe is None:
        universe = config.UNIVERSE

    results = []

    print(f"\n{'='*60}")
    print(f"  WHEEL STRATEGY SCREENER  —  {len(universe)} tickers")
    print(f"{'='*60}\n")

    for symbol in universe:
        print(f"  Screening {symbol} ...", end=" ", flush=True)

        info = get_ticker_info(symbol)
        if not info:
            print("SKIP (no data)")
            continue

        # Hard fundamental / liquidity filters
        passed, reason = _passes_filters(symbol, info)
        if not passed:
            print(f"FAIL ({reason})")
            results.append(_row(symbol, info, passed=False, reason=reason))
            continue

        # IV range check
        iv_ok, iv = _check_iv(symbol, info)
        if not iv_ok:
            reason = f"IV {iv:.1%} out of range [{config.MIN_IV:.0%}–{config.MAX_IV:.0%}]"
            print(f"FAIL ({reason})")
            results.append(_row(symbol, info, passed=False, reason=reason, iv=iv))
            continue

        # Option liquidity check
        if not _check_option_liquidity(symbol):
            reason = "insufficient option liquidity"
            print(f"FAIL ({reason})")
            results.append(_row(symbol, info, passed=False, reason=reason, iv=iv))
            continue

        score = _score_candidate(info, iv)
        print(f"PASS  (score={score:.1f}, IV={iv:.1%})")
        results.append(_row(symbol, info, passed=True, reason="", iv=iv, score=score))

    df = pd.DataFrame(results)
    if df.empty:
        print("\n[!] No candidates passed all filters.")
        return df

    # Separate passing from failing for display clarity
    passing = df[df["passed"]].sort_values("score", ascending=False).head(config.TOP_N_CANDIDATES)
    failing = df[~df["passed"]]

    print(f"\n{'─'*60}")
    print(f"  Passed: {len(passing)}  |  Failed: {len(failing)}")
    print(f"{'─'*60}")

    return passing.reset_index(drop=True)


def _row(symbol, info, passed, reason, iv=0.0, score=0.0) -> dict:
    """Build a result dict for one ticker."""
    price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
    mktcap = info.get("marketCap") or 0
    avg_vol = info.get("averageVolume") or 0
    return {
        "symbol": symbol,
        "price": round(price, 2),
        "market_cap_b": round(mktcap / 1e9, 2),
        "avg_volume": int(avg_vol),
        "iv": round(iv, 4),
        "score": score,
        "passed": passed,
        "reject_reason": reason,
    }
