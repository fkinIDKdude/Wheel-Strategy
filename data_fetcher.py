"""
data_fetcher.py — Thin wrappers around yfinance / yahooquery.

All external I/O is isolated here so the rest of the system
stays testable and API-swappable.
"""

import warnings
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore", category=FutureWarning)


# ──────────────────────────────────────────────
# Fundamentals & price
# ──────────────────────────────────────────────

def get_ticker_info(symbol: str) -> dict:
    """
    Fetch summary fundamentals from yfinance for a single ticker.
    Returns an empty dict on any failure.
    """
    try:
        t = yf.Ticker(symbol)
        info = t.info or {}
        return info
    except Exception as e:
        print(f"  [WARN] {symbol}: info fetch failed — {e}")
        return {}


def get_price_history(symbol: str, period: str = "1y") -> pd.DataFrame:
    """
    Download OHLCV history.  Returns empty DataFrame on failure.
    """
    try:
        df = yf.download(symbol, period=period, auto_adjust=True, progress=False)
        return df
    except Exception as e:
        print(f"  [WARN] {symbol}: price history failed — {e}")
        return pd.DataFrame()


def get_historical_volatility(symbol: str, window: int = 30) -> Optional[float]:
    """
    Compute 30-day realised (historical) volatility from log returns.
    Returns annualised HV as a decimal, or None.
    """
    df = get_price_history(symbol, period="6mo")
    if df.empty or len(df) < window + 1:
        return None
    closes = df["Close"].squeeze()
    log_returns = (closes / closes.shift(1)).apply(lambda x: x ** 0).mul(0)  # placeholder
    # Proper log-return calculation
    import numpy as np
    log_returns = np.log(closes / closes.shift(1)).dropna()
    hv = log_returns.rolling(window).std().iloc[-1] * (252 ** 0.5)
    return float(hv)


# ──────────────────────────────────────────────
# Options chain
# ──────────────────────────────────────────────

def get_options_expirations(symbol: str) -> tuple[list[str], yf.Ticker]:
    """
    Return (list_of_expiry_strings, Ticker_object).
    Expiries are ISO date strings e.g. '2025-01-17'.
    Returns ([], None) on failure.
    """
    try:
        t = yf.Ticker(symbol)
        exps = list(t.options)  # tuple of date strings
        return exps, t
    except Exception as e:
        print(f"  [WARN] {symbol}: options expirations failed — {e}")
        return [], None


def get_options_chain(ticker_obj: yf.Ticker, expiry: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetch puts and calls DataFrames for a given expiry date string.
    Returns (puts_df, calls_df).  Empty DataFrames on failure.
    """
    try:
        chain = ticker_obj.option_chain(expiry)
        return chain.puts, chain.calls
    except Exception as e:
        print(f"  [WARN] options chain for {expiry} failed — {e}")
        return pd.DataFrame(), pd.DataFrame()


def get_next_earnings_date(symbol: str) -> Optional[datetime]:
    """
    Attempt to retrieve the next earnings date from yfinance calendar.
    Returns a datetime or None if unavailable.
    """
    try:
        t = yf.Ticker(symbol)
        cal = t.calendar
        if cal is None or cal.empty:
            return None
        # calendar index contains dates; Earnings Date is first row
        if "Earnings Date" in cal.index:
            raw = cal.loc["Earnings Date"]
            # raw may be a Series (multiple dates) or a scalar
            if isinstance(raw, pd.Series):
                raw = raw.iloc[0]
            return pd.Timestamp(raw).to_pydatetime()
        return None
    except Exception:
        return None


def get_analyst_ratings(info: dict) -> float:
    """
    Derive the fraction of buy/strong-buy ratings from the info dict.
    yfinance exposes 'recommendationMean' (1=Strong Buy … 5=Strong Sell).
    We convert that to an approximate buy-fraction proxy.
    Returns a float 0–1 (higher is more bullish).
    """
    mean = info.get("recommendationMean")
    if mean is None:
        return 0.5  # neutral if missing
    # recommendationMean: 1.0 → strong buy, 3.0 → hold, 5.0 → strong sell
    # Map linearly: 1 → 1.0, 3 → 0.5, 5 → 0.0
    fraction = max(0.0, min(1.0, (5.0 - mean) / 4.0))
    return fraction
