"""
options_analyzer.py — Options chain analysis and Wheel recommendation engine.

For each screened stock this module:
  1. Selects the best-fit expiry (closest to DTE_TARGET within [DTE_MIN, DTE_MAX])
  2. Scans the put chain for the strike whose delta is closest to the target
  3. Computes premium, annualised ROC, and probability of profit for the CSP
  4. If assigned, recommends a covered-call follow-on strike + DTE
"""

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

import config
from black_scholes import bs_delta, bs_greeks, implied_volatility, prob_otm_put
from data_fetcher import get_options_expirations, get_options_chain


# ──────────────────────────────────────────────
# Expiry selection
# ──────────────────────────────────────────────

def _select_expiry(
    expirations: list[str],
    dte_min: int = config.DTE_MIN,
    dte_max: int = config.DTE_MAX,
    dte_target: int = config.DTE_TARGET,
) -> Optional[str]:
    """
    Pick the expiry date string closest to dte_target that falls within
    [dte_min, dte_max].  Returns None if no suitable expiry exists.
    """
    today = datetime.today().date()
    candidates = []
    for exp_str in expirations:
        exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
        dte = (exp_date - today).days
        if dte_min <= dte <= dte_max:
            candidates.append((abs(dte - dte_target), dte, exp_str))

    if not candidates:
        return None
    # Sort by proximity to target DTE, break ties by shorter DTE
    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[0][2]


# ──────────────────────────────────────────────
# Strike selection for Cash-Secured Put
# ──────────────────────────────────────────────

def _select_csp_strike(
    puts_df: pd.DataFrame,
    spot: float,
    T: float,           # time to expiry in years
    iv_guess: float,    # fallback IV if market IV unavailable
) -> Optional[dict]:
    """
    Find the put strike whose |delta| is closest to the midpoint of
    [CSP_DELTA_MIN, CSP_DELTA_MAX].

    Strategy:
      1. For each strike, compute delta (using market IV if we can back-solve
         it, else use historical vol as proxy)
      2. Filter to strikes with |delta| in [CSP_DELTA_MIN, CSP_DELTA_MAX]
      3. Return the best-fit row with computed analytics

    Returns a dict of analytics or None.
    """
    if puts_df.empty or spot <= 0 or T <= 0:
        return None

    r = config.RISK_FREE_RATE
    delta_target = (config.CSP_DELTA_MIN + config.CSP_DELTA_MAX) / 2

    rows = []
    for _, row in puts_df.iterrows():
        K = float(row.get("strike", 0))
        if K <= 0:
            continue

        # Mid-price from bid/ask; fall back to lastPrice
        bid = float(row.get("bid") or 0)
        ask = float(row.get("ask") or 0)
        last = float(row.get("lastPrice") or 0)

        if bid > 0 and ask > 0:
            mid_price = (bid + ask) / 2
        elif last > 0:
            mid_price = last
        else:
            continue  # no usable price

        # IV from market price (Newton-Raphson), fallback to iv_guess
        iv = implied_volatility(mid_price, spot, K, T, r, option_type="put")
        if iv is None or iv < 0.01:
            iv = max(iv_guess, 0.15)  # floor at 15%

        # Greeks
        greeks = bs_greeks(spot, K, T, r, iv, option_type="put")
        delta = greeks["delta"]
        if delta is None:
            continue

        # Store absolute delta for comparison
        abs_delta = abs(delta)

        # Probability of profit (put expires worthless = stock stays above K)
        pop = prob_otm_put(spot, K, T, r, iv)

        # Open interest and volume for liquidity check
        oi = int(row.get("openInterest") or 0)
        vol = int(row.get("volume") or 0)

        rows.append({
            "strike": K,
            "mid_price": round(mid_price, 2),
            "iv": round(iv, 4),
            "delta": round(delta, 4),
            "abs_delta": abs_delta,
            "gamma": greeks["gamma"],
            "theta": greeks["theta"],
            "vega": greeks["vega"],
            "pop": round(pop, 4) if pop is not None else None,
            "open_interest": oi,
            "volume": vol,
        })

    if not rows:
        return None

    rows_df = pd.DataFrame(rows)

    # Filter to delta range
    in_range = rows_df[
        (rows_df["abs_delta"] >= config.CSP_DELTA_MIN) &
        (rows_df["abs_delta"] <= config.CSP_DELTA_MAX)
    ]

    if in_range.empty:
        # Relax: take the closest strike to target delta across all strikes
        rows_df["delta_dist"] = (rows_df["abs_delta"] - delta_target).abs()
        best = rows_df.sort_values("delta_dist").iloc[0]
    else:
        in_range = in_range.copy()
        in_range["delta_dist"] = (in_range["abs_delta"] - delta_target).abs()
        best = in_range.sort_values("delta_dist").iloc[0]

    return best.to_dict()


# ──────────────────────────────────────────────
# Return metrics
# ──────────────────────────────────────────────

def _compute_csp_metrics(
    strike: float,
    premium: float,  # per-share premium (mid-price of put)
    T: float,        # years to expiry
    spot: float,
) -> dict:
    """
    Calculate:
      - Capital at risk (= strike × 100 per contract, reported per-share)
      - Premium yield (premium / strike)
      - Annualised ROC = premium_yield / T
      - Dollar return per contract (100 shares)
    """
    capital_at_risk = strike  # per share
    premium_yield = premium / capital_at_risk if capital_at_risk > 0 else 0
    annualised_roc = premium_yield / T if T > 0 else 0
    dollar_return_per_contract = premium * 100  # 1 contract = 100 shares
    return {
        "capital_per_contract": round(capital_at_risk * 100, 2),
        "premium_yield_pct": round(premium_yield * 100, 2),
        "annualised_roc_pct": round(annualised_roc * 100, 2),
        "dollar_return_per_contract": round(dollar_return_per_contract, 2),
    }


# ──────────────────────────────────────────────
# Covered Call recommendation (if assigned)
# ──────────────────────────────────────────────

def _recommend_covered_call(
    ticker_obj,
    expirations: list[str],
    cost_basis: float,  # put strike = effective cost basis if assigned at expiry
    spot: float,
    iv_guess: float,
) -> Optional[dict]:
    """
    Recommend a covered-call strike targeting CC_OTM_PCT above cost basis
    with DTE near CC_DTE_TARGET.
    """
    exp_str = _select_expiry(
        expirations,
        dte_min=config.DTE_MIN,
        dte_max=config.DTE_MAX,
        dte_target=config.CC_DTE_TARGET,
    )
    if exp_str is None:
        return None

    today = datetime.today().date()
    exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
    dte = (exp_date - today).days
    T = dte / 365

    _, calls_df = get_options_chain(ticker_obj, exp_str)
    if calls_df is None or calls_df.empty:
        return None

    # Target strike: cost_basis * (1 + CC_OTM_PCT)
    target_strike = cost_basis * (1 + config.CC_OTM_PCT)
    r = config.RISK_FREE_RATE

    best_call = None
    min_dist = float("inf")

    for _, row in calls_df.iterrows():
        K = float(row.get("strike", 0))
        if K < cost_basis:  # don't sell below cost basis
            continue

        bid = float(row.get("bid") or 0)
        ask = float(row.get("ask") or 0)
        last = float(row.get("lastPrice") or 0)
        mid = (bid + ask) / 2 if bid > 0 and ask > 0 else last
        if mid <= 0:
            continue

        iv = implied_volatility(mid, spot, K, T, r, option_type="call")
        if iv is None:
            iv = iv_guess

        greeks = bs_greeks(spot, K, T, r, iv, option_type="call")
        dist = abs(K - target_strike)
        if dist < min_dist:
            min_dist = dist
            annualised_roc = (mid / cost_basis) / T * 100 if T > 0 else 0
            best_call = {
                "cc_expiry": exp_str,
                "cc_dte": dte,
                "cc_strike": round(K, 2),
                "cc_premium": round(mid, 2),
                "cc_delta": round(greeks["delta"], 4) if greeks["delta"] else None,
                "cc_iv": round(iv, 4),
                "cc_annualised_roc_pct": round(annualised_roc, 2),
                "cc_dollar_per_contract": round(mid * 100, 2),
            }

    return best_call


# ──────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────

def analyze_options(candidates_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each row in candidates_df (output of screener.run_screener),
    fetch the options chain and produce a full Wheel recommendation.

    Returns a DataFrame with one row per recommended trade.
    """
    if candidates_df.empty:
        return pd.DataFrame()

    print(f"\n{'='*60}")
    print("  OPTIONS CHAIN ANALYSIS")
    print(f"{'='*60}\n")

    recommendations = []

    for _, cand in candidates_df.iterrows():
        symbol = cand["symbol"]
        spot = float(cand["price"])
        iv_guess = float(cand["iv"]) if cand["iv"] > 0 else 0.30

        print(f"  Analysing {symbol} (spot=${spot:.2f}, HV={iv_guess:.1%}) ...", end=" ")

        exps, ticker_obj = get_options_expirations(symbol)
        if not exps or ticker_obj is None:
            print("SKIP (no expirations)")
            continue

        # ── 1. Select expiry ──────────────────────────
        exp_str = _select_expiry(exps)
        if exp_str is None:
            print(f"SKIP (no expiry in {config.DTE_MIN}–{config.DTE_MAX} DTE window)")
            continue

        today = datetime.today().date()
        exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
        dte = (exp_date - today).days
        T = dte / 365.0

        # ── 2. Fetch put chain ────────────────────────
        puts_df, _ = get_options_chain(ticker_obj, exp_str)
        if puts_df is None or puts_df.empty:
            print("SKIP (empty put chain)")
            continue

        # ── 3. Select best CSP strike ─────────────────
        best = _select_csp_strike(puts_df, spot, T, iv_guess)
        if best is None:
            print("SKIP (no suitable strike found)")
            continue

        # ── 4. Return metrics ─────────────────────────
        metrics = _compute_csp_metrics(
            strike=best["strike"],
            premium=best["mid_price"],
            T=T,
            spot=spot,
        )

        # Skip if annualised ROC is below threshold
        if metrics["annualised_roc_pct"] < config.MIN_ANNUALISED_ROC * 100:
            print(f"SKIP (ROC {metrics['annualised_roc_pct']:.1f}% < threshold)")
            continue

        # ── 5. Covered call follow-on ─────────────────
        cc = _recommend_covered_call(
            ticker_obj=ticker_obj,
            expirations=exps,
            cost_basis=best["strike"],
            spot=spot,
            iv_guess=iv_guess,
        )

        rec = {
            # Identification
            "symbol": symbol,
            "spot_price": round(spot, 2),
            "screener_score": round(cand["score"], 1),
            # CSP details
            "csp_expiry": exp_str,
            "csp_dte": dte,
            "csp_strike": best["strike"],
            "csp_premium": best["mid_price"],
            "csp_delta": best["delta"],
            "csp_iv_pct": round(best["iv"] * 100, 1),
            "csp_pop_pct": round(best["pop"] * 100, 1) if best["pop"] is not None else None,
            "csp_theta_day": best["theta"],
            # Capital & returns
            "capital_per_contract": metrics["capital_per_contract"],
            "premium_yield_pct": metrics["premium_yield_pct"],
            "annualised_roc_pct": metrics["annualised_roc_pct"],
            "dollar_return_contract": metrics["dollar_return_per_contract"],
            # Option liquidity
            "put_open_interest": best["open_interest"],
            "put_volume": best["volume"],
        }

        # Merge covered-call recommendation if available
        if cc:
            rec.update(cc)

        recommendations.append(rec)
        print(
            f"OK  strike=${best['strike']:.1f}  "
            f"prem=${best['mid_price']:.2f}  "
            f"ROC={metrics['annualised_roc_pct']:.1f}%  "
            f"PoP={rec.get('csp_pop_pct', '?')}%"
        )

    return pd.DataFrame(recommendations)
