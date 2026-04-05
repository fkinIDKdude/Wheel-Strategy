"""
black_scholes.py — Analytic Black-Scholes pricing and Greeks.

Used to:
  - Compute theoretical option price (for validation / when market price is stale)
  - Compute delta, gamma, theta, vega
  - Back-solve implied volatility from a market price (Newton-Raphson)
  - Estimate probability of expiring OTM (= N(-d2) for puts)
"""

import math
from typing import Optional


# ──────────────────────────────────────────────
# Normal distribution helpers
# ──────────────────────────────────────────────

def _norm_cdf(x: float) -> float:
    """Standard normal CDF via math.erfc for precision."""
    return 0.5 * math.erfc(-x / math.sqrt(2))


def _norm_pdf(x: float) -> float:
    """Standard normal PDF."""
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


# ──────────────────────────────────────────────
# Core BS formula
# ──────────────────────────────────────────────

def bs_price(
    S: float,   # spot price
    K: float,   # strike price
    T: float,   # time to expiry in years
    r: float,   # risk-free rate (annual)
    sigma: float,  # implied volatility (annual)
    option_type: str = "put",  # 'put' or 'call'
) -> Optional[float]:
    """
    Black-Scholes option price.
    Returns None for degenerate inputs (T<=0, sigma<=0, S<=0, K<=0).
    """
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return None
    try:
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        if option_type == "call":
            price = S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
        else:  # put
            price = K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)
        return price
    except (ValueError, ZeroDivisionError):
        return None


def bs_delta(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "put"
) -> Optional[float]:
    """
    BS delta.
    Call delta ∈ (0, 1);  put delta ∈ (-1, 0).
    """
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return None
    try:
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        if option_type == "call":
            return _norm_cdf(d1)
        else:
            return _norm_cdf(d1) - 1  # put delta is negative
    except (ValueError, ZeroDivisionError):
        return None


def bs_greeks(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "put"
) -> dict:
    """
    Return a dict with delta, gamma, theta (per day), vega (per 1% IV).
    Any value that cannot be computed is None.
    """
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return {"delta": None, "gamma": None, "theta": None, "vega": None}
    try:
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        nd1 = _norm_pdf(d1)
        gamma = nd1 / (S * sigma * math.sqrt(T))
        vega = S * nd1 * math.sqrt(T) / 100  # per 1% change in IV
        if option_type == "call":
            delta = _norm_cdf(d1)
            theta = (
                -(S * nd1 * sigma) / (2 * math.sqrt(T))
                - r * K * math.exp(-r * T) * _norm_cdf(d2)
            ) / 365
        else:
            delta = _norm_cdf(d1) - 1
            theta = (
                -(S * nd1 * sigma) / (2 * math.sqrt(T))
                + r * K * math.exp(-r * T) * _norm_cdf(-d2)
            ) / 365
        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "theta": round(theta, 4),
            "vega": round(vega, 4),
        }
    except (ValueError, ZeroDivisionError):
        return {"delta": None, "gamma": None, "theta": None, "vega": None}


# ──────────────────────────────────────────────
# Implied Volatility solver
# ──────────────────────────────────────────────

def implied_volatility(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str = "put",
    max_iterations: int = 200,
    tolerance: float = 1e-6,
) -> Optional[float]:
    """
    Back-solve IV from a market price using Newton-Raphson.
    Returns annualised IV (decimal) or None if it fails to converge.
    """
    if market_price <= 0 or T <= 0 or S <= 0 or K <= 0:
        return None

    sigma = 0.30  # initial guess: 30%
    for _ in range(max_iterations):
        price = bs_price(S, K, T, r, sigma, option_type)
        if price is None:
            return None
        diff = price - market_price
        if abs(diff) < tolerance:
            return sigma

        # vega (full, not per-1%)
        try:
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            vega_full = S * _norm_pdf(d1) * math.sqrt(T)
        except (ValueError, ZeroDivisionError):
            return None

        if vega_full < 1e-10:
            return None  # too close to zero vega (deep ITM/OTM)
        sigma -= diff / vega_full
        if sigma <= 0:
            sigma = 1e-6

    return None  # did not converge


# ──────────────────────────────────────────────
# Probability helpers
# ──────────────────────────────────────────────

def prob_otm_put(S: float, K: float, T: float, r: float, sigma: float) -> Optional[float]:
    """
    Risk-neutral probability that stock stays ABOVE strike at expiry
    (= probability a put expires worthless = N(d2) for a put seller).
    """
    if T <= 0 or sigma <= 0:
        return None
    try:
        d2 = (math.log(S / K) + (r - 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        return _norm_cdf(d2)
    except (ValueError, ZeroDivisionError):
        return None
