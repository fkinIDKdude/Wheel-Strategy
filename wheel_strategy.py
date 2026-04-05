#!/usr/bin/env python3
"""
wheel_strategy.py — Entry point for the Wheel Strategy automation system.

Usage:
    python wheel_strategy.py                    # full run (screen + analyse)
    python wheel_strategy.py --screen-only      # screener output only
    python wheel_strategy.py --tickers AAPL MSFT TSLA  # override universe

The system runs in two passes:
  Pass 1 — Fundamental screener filters the universe down to the best
            Wheel candidates based on price, IV, fundamentals, and liquidity.
  Pass 2 — Options analyser picks the optimal CSP strike + expiry for
            each candidate and adds covered-call follow-on recommendations.

All parameters are in config.py.
"""

import argparse
import sys
import time
import warnings

warnings.filterwarnings("ignore")

import config
from screener import run_screener
from options_analyzer import analyze_options
from output_formatter import print_recommendations, export_to_csv


# ──────────────────────────────────────────────
# CLI argument parsing
# ──────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Wheel Strategy automation: screener + options recommender"
    )
    parser.add_argument(
        "--screen-only",
        action="store_true",
        help="Run only the fundamental screener (skip options analysis)",
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        metavar="TICKER",
        help="Override the universe in config.py with specific tickers",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=config.TOP_N_CANDIDATES,
        help=f"Number of top screener candidates to analyse (default {config.TOP_N_CANDIDATES})",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Skip CSV export even if EXPORT_CSV=True in config.py",
    )
    return parser.parse_args()


# ──────────────────────────────────────────────
# Main pipeline
# ──────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    # Override config values from CLI flags
    universe = args.tickers if args.tickers else config.UNIVERSE
    config.TOP_N_CANDIDATES = args.top_n

    t_start = time.time()

    # ── PASS 1: Fundamental Screener ──────────────────────
    candidates_df = run_screener(universe=universe)

    if candidates_df.empty:
        print("\n[!] Screener returned no candidates. Exiting.\n")
        print("    Suggestions:")
        print("      - Widen MAX_STOCK_PRICE or relax MIN_IV / MAX_IV in config.py")
        print("      - Add more tickers to UNIVERSE")
        print("      - Check your internet connection / API availability")
        sys.exit(0)

    # Print screener summary
    print("\n  TOP WHEEL CANDIDATES (screener):")
    print(f"  {'Symbol':<8}{'Price':>8}{'MktCap(B)':>12}{'IV':>8}{'Score':>8}")
    print(f"  {'─'*6:<8}{'─'*6:>8}{'─'*8:>12}{'─'*6:>8}{'─'*6:>8}")
    for _, row in candidates_df.iterrows():
        print(
            f"  {row['symbol']:<8}"
            f"${row['price']:>7.2f}"
            f"  ${row['market_cap_b']:>8.1f}B"
            f"  {row['iv']:>6.1%}"
            f"  {row['score']:>6.1f}"
        )

    if args.screen_only:
        elapsed = time.time() - t_start
        print(f"\n  [screen-only mode]  Done in {elapsed:.1f}s\n")
        return

    # ── PASS 2: Options Analysis ──────────────────────────
    recommendations_df = analyze_options(candidates_df)

    # ── OUTPUT ────────────────────────────────────────────
    print_recommendations(recommendations_df)

    if config.EXPORT_CSV and not args.no_export:
        export_to_csv(recommendations_df)

    elapsed = time.time() - t_start
    print(f"  Completed in {elapsed:.1f}s\n")


if __name__ == "__main__":
    main()
