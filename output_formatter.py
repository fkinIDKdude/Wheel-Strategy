"""
output_formatter.py — Pretty-print recommendations and optionally export to CSV.
"""

from datetime import datetime
from typing import Optional

import pandas as pd

import config


def _fmt_pct(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    return f"{val:.1f}%"


def _fmt_dollar(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    return f"${val:,.2f}"


def _fmt_int(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    return f"{int(val):,}"


def _fmt_float(val, decimals=2) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    return f"{val:.{decimals}f}"


# ──────────────────────────────────────────────
# Console display
# ──────────────────────────────────────────────

CSP_DISPLAY_COLS = [
    ("symbol",              "Ticker",         "<8"),
    ("spot_price",          "Spot",           ">8"),
    ("csp_expiry",          "Expiry",         ">12"),
    ("csp_dte",             "DTE",            ">5"),
    ("csp_strike",          "Strike",         ">8"),
    ("csp_premium",         "Premium",        ">9"),
    ("csp_delta",           "Delta",          ">7"),
    ("csp_iv_pct",          "IV%",            ">6"),
    ("csp_pop_pct",         "PoP%",           ">6"),
    ("capital_per_contract","Capital/Ct",     ">11"),
    ("annualised_roc_pct",  "Ann.ROC%",       ">9"),
    ("dollar_return_contract","$/Contract",   ">11"),
]

CC_DISPLAY_COLS = [
    ("symbol",              "Ticker",         "<8"),
    ("csp_strike",          "Cost Basis",     ">10"),
    ("cc_expiry",           "CC Expiry",      ">12"),
    ("cc_dte",              "DTE",            ">5"),
    ("cc_strike",           "CC Strike",      ">9"),
    ("cc_premium",          "Premium",        ">9"),
    ("cc_delta",            "Delta",          ">7"),
    ("cc_iv",               "CC IV",          ">7"),
    ("cc_annualised_roc_pct","Ann.ROC%",      ">9"),
    ("cc_dollar_per_contract","$/Contract",   ">11"),
]


def _print_table(df: pd.DataFrame, columns: list[tuple]) -> None:
    """Generic fixed-width table printer."""
    col_keys   = [c[0] for c in columns]
    col_labels = [c[1] for c in columns]
    col_fmts   = [c[2] for c in columns]

    # Header
    header = "  ".join(f"{label:{fmt}}" for label, fmt in zip(col_labels, col_fmts))
    sep    = "  ".join("─" * int(fmt[1:]) for fmt in col_fmts)
    print(header)
    print(sep)

    for _, row in df.iterrows():
        cells = []
        for key, fmt in zip(col_keys, col_fmts):
            width = int(fmt[1:])
            align = fmt[0]
            val = row.get(key)
            if key in ("csp_delta", "cc_delta"):
                cell = _fmt_float(val, 3)
            elif key in ("csp_premium", "cc_premium", "spot_price", "csp_strike",
                          "cc_strike", "csp_strike"):
                cell = _fmt_dollar(val)
            elif key in ("capital_per_contract", "dollar_return_contract",
                          "cc_dollar_per_contract"):
                cell = _fmt_dollar(val)
            elif key in ("annualised_roc_pct", "premium_yield_pct",
                          "csp_iv_pct", "csp_pop_pct", "cc_annualised_roc_pct"):
                cell = _fmt_pct(val)
            elif key in ("csp_dte", "cc_dte", "put_open_interest", "put_volume"):
                cell = _fmt_int(val)
            elif key == "cc_iv":
                cell = _fmt_pct(float(val) * 100 if val and not pd.isna(val) else None)
            else:
                cell = str(val) if val is not None and not (isinstance(val, float) and pd.isna(val)) else "—"
            # Apply alignment
            cells.append(f"{cell:{align}{width}}")
        print("  ".join(cells))


def print_recommendations(recs_df: pd.DataFrame) -> None:
    """
    Print the full recommendations report to the console.
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'═'*80}")
    print(f"  WHEEL STRATEGY RECOMMENDATIONS  —  Generated {ts}")
    print(f"{'═'*80}")

    if recs_df.empty:
        print("\n  No recommendations generated — try relaxing screener thresholds.\n")
        return

    # ── Section 1: Cash-Secured Puts ──────────────────────
    print(f"\n  ┌─ CASH-SECURED PUT OPPORTUNITIES ({len(recs_df)} trades) ─────────────────────────┐\n")
    _print_table(recs_df, CSP_DISPLAY_COLS)

    # ── Section 2: Follow-on Covered Calls ────────────────
    cc_cols = [c[0] for c in CC_DISPLAY_COLS]
    cc_df = recs_df[[c for c in cc_cols if c in recs_df.columns]].dropna(
        subset=["cc_strike"] if "cc_strike" in recs_df.columns else []
    )
    if not cc_df.empty:
        print(f"\n  ┌─ IF ASSIGNED — COVERED CALL FOLLOW-ON ────────────────────────────────────┐\n")
        _print_table(cc_df, CC_DISPLAY_COLS)

    # ── Section 3: Summary stats ───────────────────────────
    print(f"\n{'─'*80}")
    print("  SUMMARY STATISTICS")
    print(f"{'─'*80}")
    avg_roc = recs_df["annualised_roc_pct"].mean()
    avg_pop = recs_df["csp_pop_pct"].mean() if "csp_pop_pct" in recs_df else None
    avg_dte = recs_df["csp_dte"].mean()
    print(f"  Trades recommended  : {len(recs_df)}")
    print(f"  Avg annualised ROC  : {avg_roc:.1f}%")
    if avg_pop is not None:
        print(f"  Avg prob of profit  : {avg_pop:.1f}%")
    print(f"  Avg DTE             : {avg_dte:.0f} days")
    total_capital = recs_df["capital_per_contract"].sum()
    total_income  = recs_df["dollar_return_contract"].sum()
    print(f"  Total capital (1ct) : {_fmt_dollar(total_capital)}")
    print(f"  Total income (1ct)  : {_fmt_dollar(total_income)}")
    print(f"{'═'*80}\n")


# ──────────────────────────────────────────────
# CSV export
# ──────────────────────────────────────────────

def export_to_csv(recs_df: pd.DataFrame, path: str = config.OUTPUT_FILE) -> None:
    """Export recommendations DataFrame to CSV."""
    if recs_df.empty:
        print(f"  [INFO] Nothing to export.")
        return
    recs_df.to_csv(path, index=False)
    print(f"  [INFO] Recommendations exported to: {path}")
