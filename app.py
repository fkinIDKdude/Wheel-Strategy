"""
app.py — Streamlit UI for the Wheel Strategy automation system.

Run with:
    streamlit run app.py

Three tabs:
  1. Screener      — run the fundamental screener with live progress
  2. Recommendations — CSP + covered-call table with Plotly charts
  3. BS Calculator — interactive Black-Scholes pricer / Greeks tool
"""

import math
import warnings
from datetime import datetime, date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore")

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Wheel Strategy",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Internal modules ──────────────────────────────────────────────────────────
import config  # noqa: E402  (imported after set_page_config intentionally)
from black_scholes import bs_price, bs_greeks, prob_otm_put, implied_volatility
from screener import run_screener
from options_analyzer import analyze_options

# ─────────────────────────────────────────────────────────────────────────────
# Shared styles
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Tighten sidebar padding */
    [data-testid="stSidebar"] { padding-top: 1rem; }
    /* Highlight metric delta colours */
    [data-testid="stMetricDelta"] svg { display: none; }
    /* Subtle header underline */
    h2 { border-bottom: 1px solid #333; padding-bottom: 0.3rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — parameter controls
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar() -> dict:
    """Render all tunable parameters in the sidebar; return as a dict."""
    st.sidebar.title("⚙️ Parameters")

    with st.sidebar.expander("📋 Universe", expanded=False):
        raw = st.text_area(
            "Tickers (comma-separated)",
            value=", ".join(config.UNIVERSE),
            height=140,
        )
        universe = [t.strip().upper() for t in raw.split(",") if t.strip()]

    st.sidebar.markdown("### 🔍 Screener Filters")

    price_min, price_max = st.sidebar.slider(
        "Stock price range ($)",
        min_value=1, max_value=500,
        value=(int(config.MIN_STOCK_PRICE), int(config.MAX_STOCK_PRICE)),
        step=5,
    )

    min_mktcap = st.sidebar.slider(
        "Min market cap ($B)",
        min_value=0.1, max_value=50.0,
        value=float(config.MIN_MARKET_CAP_B),
        step=0.5,
    )

    iv_min, iv_max = st.sidebar.slider(
        "IV range (annualised %)",
        min_value=5, max_value=150,
        value=(int(config.MIN_IV * 100), int(config.MAX_IV * 100)),
        step=5,
    )

    min_option_vol = st.sidebar.number_input(
        "Min option volume (contracts)",
        min_value=0, max_value=10_000,
        value=int(config.MIN_OPTION_VOLUME),
        step=50,
    )

    earnings_blackout = st.sidebar.slider(
        "Earnings blackout (days)",
        min_value=0, max_value=60,
        value=int(config.EARNINGS_BLACKOUT_DAYS),
        step=1,
    )

    top_n = st.sidebar.slider(
        "Top N candidates",
        min_value=1, max_value=30,
        value=int(config.TOP_N_CANDIDATES),
        step=1,
    )

    st.sidebar.markdown("### 📈 Options Parameters")

    delta_min, delta_max = st.sidebar.slider(
        "CSP delta range (|Δ|)",
        min_value=0.05, max_value=0.70,
        value=(float(config.CSP_DELTA_MIN), float(config.CSP_DELTA_MAX)),
        step=0.05,
    )

    dte_min, dte_max = st.sidebar.slider(
        "DTE window (days)",
        min_value=7, max_value=90,
        value=(int(config.DTE_MIN), int(config.DTE_MAX)),
        step=1,
    )

    dte_target = st.sidebar.slider(
        "Preferred DTE",
        min_value=7, max_value=90,
        value=int(config.DTE_TARGET),
        step=1,
    )

    min_roc = st.sidebar.slider(
        "Min annualised ROC (%)",
        min_value=0, max_value=100,
        value=int(config.MIN_ANNUALISED_ROC * 100),
        step=1,
    )

    risk_free = st.sidebar.slider(
        "Risk-free rate (%)",
        min_value=0.0, max_value=10.0,
        value=float(config.RISK_FREE_RATE * 100),
        step=0.25,
    )

    return dict(
        universe=universe,
        price_min=price_min, price_max=price_max,
        min_mktcap=min_mktcap,
        iv_min=iv_min / 100, iv_max=iv_max / 100,
        min_option_vol=int(min_option_vol),
        earnings_blackout=int(earnings_blackout),
        top_n=int(top_n),
        delta_min=delta_min, delta_max=delta_max,
        dte_min=dte_min, dte_max=dte_max, dte_target=dte_target,
        min_roc=min_roc / 100,
        risk_free=risk_free / 100,
    )


def apply_params(p: dict) -> None:
    """Push sidebar values into the config module so all sub-modules see them."""
    config.UNIVERSE = p["universe"]
    config.MIN_STOCK_PRICE = p["price_min"]
    config.MAX_STOCK_PRICE = p["price_max"]
    config.MIN_MARKET_CAP_B = p["min_mktcap"]
    config.MIN_IV = p["iv_min"]
    config.MAX_IV = p["iv_max"]
    config.MIN_OPTION_VOLUME = p["min_option_vol"]
    config.EARNINGS_BLACKOUT_DAYS = p["earnings_blackout"]
    config.TOP_N_CANDIDATES = p["top_n"]
    config.CSP_DELTA_MIN = p["delta_min"]
    config.CSP_DELTA_MAX = p["delta_max"]
    config.DTE_MIN = p["dte_min"]
    config.DTE_MAX = p["dte_max"]
    config.DTE_TARGET = p["dte_target"]
    config.MIN_ANNUALISED_ROC = p["min_roc"]
    config.RISK_FREE_RATE = p["risk_free"]


# ─────────────────────────────────────────────────────────────────────────────
# Tab 1 — Screener
# ─────────────────────────────────────────────────────────────────────────────

def tab_screener(params: dict) -> None:
    st.header("📊 Fundamental Screener")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Universe size", len(params["universe"]))
    col2.metric("Price range", f"${params['price_min']}–${params['price_max']}")
    col3.metric("IV range", f"{params['iv_min']:.0%}–{params['iv_max']:.0%}")
    col4.metric("Top N", params["top_n"])

    st.divider()

    run = st.button("▶  Run Screener", type="primary", use_container_width=True)

    if run:
        apply_params(params)

        # Live progress through the universe
        progress_bar = st.progress(0, text="Starting screener…")
        log_box = st.empty()
        log_lines: list[str] = []
        results_rows: list[dict] = []

        total = len(params["universe"])

        # Monkey-patch print so screener logs appear in the UI
        import builtins, io, sys
        _original_print = builtins.print

        def _ui_print(*args, **kwargs):
            text = " ".join(str(a) for a in args)
            _original_print(text)            # keep terminal output too
            log_lines.append(text)
            log_box.code("\n".join(log_lines[-30:]), language=None)

        builtins.print = _ui_print

        try:
            candidates_df = run_screener(universe=params["universe"])
        finally:
            builtins.print = _original_print

        progress_bar.progress(1.0, text="Screener complete.")

        st.session_state["candidates_df"] = candidates_df
        # Clear any stale recommendations when re-screening
        st.session_state.pop("recommendations_df", None)

    # ── Display results ──────────────────────────────────────────────────────
    candidates_df: pd.DataFrame = st.session_state.get("candidates_df", pd.DataFrame())

    if candidates_df.empty:
        st.info("No results yet — adjust parameters and click **Run Screener**.")
        return

    passing = candidates_df[candidates_df.get("passed", pd.Series([True] * len(candidates_df), dtype=bool))]

    st.success(f"✅  **{len(passing)}** candidate(s) passed all filters")

    # Score bar chart
    if not passing.empty and "score" in passing.columns:
        fig = px.bar(
            passing.sort_values("score"),
            x="score", y="symbol",
            orientation="h",
            color="score",
            color_continuous_scale="Teal",
            labels={"score": "Composite Score", "symbol": ""},
            title="Screener Score by Ticker",
            height=max(250, 40 * len(passing)),
        )
        fig.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

    # Results table
    display_cols = ["symbol", "price", "market_cap_b", "avg_volume", "iv", "score"]
    show_cols = [c for c in display_cols if c in passing.columns]
    styled = passing[show_cols].copy()
    if "iv" in styled.columns:
        styled["iv"] = styled["iv"].apply(lambda x: f"{x:.1%}" if pd.notna(x) else "—")
    if "avg_volume" in styled.columns:
        styled["avg_volume"] = styled["avg_volume"].apply(
            lambda x: f"{int(x):,}" if pd.notna(x) else "—"
        )
    styled.columns = [c.replace("_", " ").title() for c in styled.columns]
    st.dataframe(styled, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 2 — Recommendations
# ─────────────────────────────────────────────────────────────────────────────

def tab_recommendations(params: dict) -> None:
    st.header("🎯 Options Recommendations")

    candidates_df: pd.DataFrame = st.session_state.get("candidates_df", pd.DataFrame())

    if candidates_df.empty:
        st.warning("Run the **Screener** tab first to generate candidates.")
        return

    run = st.button("▶  Analyse Options", type="primary", use_container_width=True)

    if run:
        apply_params(params)

        log_box = st.empty()
        log_lines: list[str] = []

        import builtins
        _original_print = builtins.print

        def _ui_print(*args, **kwargs):
            text = " ".join(str(a) for a in args)
            _original_print(text)
            log_lines.append(text)
            log_box.code("\n".join(log_lines[-30:]), language=None)

        builtins.print = _ui_print
        try:
            recs_df = analyze_options(candidates_df)
        finally:
            builtins.print = _original_print

        st.session_state["recommendations_df"] = recs_df

    recs_df: pd.DataFrame = st.session_state.get("recommendations_df", pd.DataFrame())

    if recs_df.empty:
        st.info("No recommendations yet — click **Analyse Options**.")
        return

    # ── Summary metrics ──────────────────────────────────────────────────────
    st.subheader("Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Trades", len(recs_df))
    c2.metric("Avg Ann. ROC", f"{recs_df['annualised_roc_pct'].mean():.1f}%")
    if "csp_pop_pct" in recs_df:
        c3.metric("Avg PoP", f"{recs_df['csp_pop_pct'].mean():.1f}%")
    if "csp_dte" in recs_df:
        c4.metric("Avg DTE", f"{recs_df['csp_dte'].mean():.0f}d")
    if "dollar_return_contract" in recs_df:
        c5.metric("Total income (1ct)", f"${recs_df['dollar_return_contract'].sum():,.0f}")

    st.divider()

    # ── Charts ───────────────────────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        if "annualised_roc_pct" in recs_df.columns:
            fig = px.bar(
                recs_df.sort_values("annualised_roc_pct"),
                x="annualised_roc_pct", y="symbol",
                orientation="h",
                color="annualised_roc_pct",
                color_continuous_scale="Teal",
                labels={"annualised_roc_pct": "Ann. ROC %", "symbol": ""},
                title="Annualised Return on Capital",
                height=max(250, 40 * len(recs_df)),
            )
            fig.add_vline(
                x=params["min_roc"] * 100,
                line_dash="dash", line_color="red",
                annotation_text="Min ROC",
            )
            fig.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        if "csp_pop_pct" in recs_df.columns and "annualised_roc_pct" in recs_df.columns:
            fig = px.scatter(
                recs_df,
                x="csp_pop_pct",
                y="annualised_roc_pct",
                text="symbol",
                color="csp_iv_pct" if "csp_iv_pct" in recs_df.columns else None,
                color_continuous_scale="Plasma",
                size="dollar_return_contract" if "dollar_return_contract" in recs_df.columns else None,
                labels={
                    "csp_pop_pct": "Prob of Profit (%)",
                    "annualised_roc_pct": "Ann. ROC (%)",
                    "csp_iv_pct": "IV %",
                },
                title="Risk / Return  (size = $/contract)",
                height=max(250, 40 * len(recs_df)),
            )
            fig.update_traces(textposition="top center")
            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── CSP Table ────────────────────────────────────────────────────────────
    st.subheader("Cash-Secured Put Opportunities")

    csp_cols = {
        "symbol": "Ticker",
        "spot_price": "Spot ($)",
        "csp_expiry": "Expiry",
        "csp_dte": "DTE",
        "csp_strike": "Strike ($)",
        "csp_premium": "Premium ($)",
        "csp_delta": "Delta",
        "csp_iv_pct": "IV %",
        "csp_pop_pct": "PoP %",
        "capital_per_contract": "Capital/ct ($)",
        "premium_yield_pct": "Yield %",
        "annualised_roc_pct": "Ann. ROC %",
        "dollar_return_contract": "$/Contract",
        "put_open_interest": "OI",
        "put_volume": "Volume",
    }
    show = {k: v for k, v in csp_cols.items() if k in recs_df.columns}
    csp_display = recs_df[list(show.keys())].rename(columns=show)
    st.dataframe(
        csp_display.style.background_gradient(
            subset=["Ann. ROC %"] if "Ann. ROC %" in csp_display.columns else [],
            cmap="Greens",
        ),
        use_container_width=True,
        hide_index=True,
    )

    # CSV download
    st.download_button(
        "⬇  Download CSP recommendations (CSV)",
        data=csp_display.to_csv(index=False).encode(),
        file_name=f"wheel_csp_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

    st.divider()

    # ── Covered Call Table ───────────────────────────────────────────────────
    cc_cols = {
        "symbol": "Ticker",
        "csp_strike": "Cost Basis ($)",
        "cc_expiry": "CC Expiry",
        "cc_dte": "CC DTE",
        "cc_strike": "CC Strike ($)",
        "cc_premium": "CC Premium ($)",
        "cc_delta": "CC Delta",
        "cc_annualised_roc_pct": "CC Ann. ROC %",
        "cc_dollar_per_contract": "CC $/Contract",
    }
    cc_avail = {k: v for k, v in cc_cols.items() if k in recs_df.columns}
    cc_df = recs_df[list(cc_avail.keys())].dropna(subset=["cc_strike"] if "cc_strike" in recs_df.columns else [])

    if not cc_df.empty:
        st.subheader("If Assigned — Covered Call Follow-On")
        cc_display = cc_df.rename(columns=cc_avail)
        st.dataframe(cc_display, use_container_width=True, hide_index=True)

        st.download_button(
            "⬇  Download CC recommendations (CSV)",
            data=cc_display.to_csv(index=False).encode(),
            file_name=f"wheel_cc_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )

    # ── Delta distribution chart ─────────────────────────────────────────────
    if "csp_delta" in recs_df.columns:
        st.divider()
        st.subheader("Delta Distribution")
        fig = px.histogram(
            recs_df,
            x="csp_delta",
            nbins=20,
            color_discrete_sequence=["#00b4d8"],
            labels={"csp_delta": "CSP Delta"},
            title="Distribution of recommended CSP deltas",
        )
        fig.add_vrect(
            x0=-params["delta_max"], x1=-params["delta_min"],
            fillcolor="green", opacity=0.15,
            annotation_text="Target band",
            annotation_position="top left",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=280)
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 3 — Black-Scholes Calculator
# ─────────────────────────────────────────────────────────────────────────────

def tab_bs_calculator(params: dict) -> None:
    st.header("🧮 Black-Scholes Calculator")
    st.caption(
        "Interactive pricer — adjust inputs to explore pricing, Greeks, and probability metrics in real time."
    )

    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        st.subheader("Inputs")
        opt_type = st.radio("Option type", ["Put (CSP)", "Call (CC)"], horizontal=True)
        bs_type = "put" if opt_type.startswith("Put") else "call"

        S = st.number_input("Spot price ($)", min_value=1.0, max_value=5000.0, value=100.0, step=1.0)
        K = st.number_input("Strike price ($)", min_value=1.0, max_value=5000.0, value=95.0, step=1.0)
        dte_bs = st.slider("Days to expiry", min_value=1, max_value=180, value=30)
        T = dte_bs / 365.0
        sigma_pct = st.slider("Implied volatility (%)", min_value=1, max_value=200, value=30)
        sigma = sigma_pct / 100
        r_pct = st.slider("Risk-free rate (%)", min_value=0.0, max_value=15.0, value=params["risk_free"] * 100, step=0.25)
        r = r_pct / 100

        # Market price input for IV back-solve
        st.markdown("---")
        st.markdown("**Back-solve IV from market price**")
        market_price = st.number_input(
            "Market price ($) — leave 0 to skip",
            min_value=0.0, max_value=1000.0, value=0.0, step=0.01,
        )

    # ── Calculations ─────────────────────────────────────────────────────────
    price = bs_price(S, K, T, r, sigma, bs_type)
    greeks = bs_greeks(S, K, T, r, sigma, bs_type)
    pop = prob_otm_put(S, K, T, r, sigma) if bs_type == "put" else None

    iv_solved = None
    if market_price > 0:
        iv_solved = implied_volatility(market_price, S, K, T, r, option_type=bs_type)

    with col_out:
        st.subheader("Results")

        m1, m2, m3 = st.columns(3)
        m1.metric("Theoretical Price", f"${price:.4f}" if price else "—")
        if pop:
            m2.metric("Prob. Profit (PoP)", f"{pop:.2%}")
        else:
            m2.metric("Intrinsic Value", f"${max(0, (K - S) if bs_type == 'put' else (S - K)):.2f}")
        m3.metric(
            "IV (back-solved)" if iv_solved else "IV (input)",
            f"{iv_solved:.2%}" if iv_solved else f"{sigma:.2%}",
        )

        st.markdown("#### Greeks")
        g1, g2, g3, g4 = st.columns(4)
        g1.metric("Delta (Δ)", f"{greeks['delta']:.4f}" if greeks["delta"] is not None else "—")
        g2.metric("Gamma (Γ)", f"{greeks['gamma']:.6f}" if greeks["gamma"] is not None else "—")
        g3.metric("Theta (Θ/day)", f"${greeks['theta']:.4f}" if greeks["theta"] is not None else "—")
        g4.metric("Vega (per 1%IV)", f"${greeks['vega']:.4f}" if greeks["vega"] is not None else "—")

        # ROC metrics for CSP context
        if bs_type == "put" and price:
            st.markdown("#### CSP Return Metrics")
            capital = K
            yield_pct = price / capital * 100
            ann_roc = yield_pct / T * (1 / 100) * 100
            r1, r2, r3 = st.columns(3)
            r1.metric("Premium yield", f"{yield_pct:.2f}%")
            r2.metric("Ann. ROC", f"{ann_roc:.1f}%")
            r3.metric("$/Contract", f"${price * 100:.2f}")

    # ── IV Smile curve ────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Option Price vs Strike")

    strikes = [round(S * m, 2) for m in [0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.0, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30]]
    prices_put  = [bs_price(S, k, T, r, sigma, "put") or 0 for k in strikes]
    prices_call = [bs_price(S, k, T, r, sigma, "call") or 0 for k in strikes]
    deltas_put  = [abs(bs_greeks(S, k, T, r, sigma, "put")["delta"] or 0) for k in strikes]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strikes, y=prices_put,  name="Put",  line=dict(color="#ef476f", width=2)))
    fig.add_trace(go.Scatter(x=strikes, y=prices_call, name="Call", line=dict(color="#06d6a0", width=2)))
    fig.add_vline(x=K, line_dash="dot", line_color="white", annotation_text=f"Strike ${K}", annotation_position="top")
    fig.add_vline(x=S, line_dash="dash", line_color="#ffd166", annotation_text=f"Spot ${S}", annotation_position="top right")
    fig.update_layout(
        xaxis_title="Strike ($)",
        yaxis_title="Option Price ($)",
        legend=dict(orientation="h"),
        margin=dict(l=0, r=0, t=20, b=0),
        height=320,
        template="plotly_dark",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Delta vs Strike ───────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=strikes, y=deltas_put, fill="tozeroy",
                                   name="|Put Delta|", line=dict(color="#00b4d8")))
        fig2.add_hrect(
            y0=params["delta_min"], y1=params["delta_max"],
            fillcolor="green", opacity=0.15,
            annotation_text="Target Δ band",
        )
        fig2.add_vline(x=K, line_dash="dot", line_color="white")
        fig2.add_vline(x=S, line_dash="dash", line_color="#ffd166")
        fig2.update_layout(
            xaxis_title="Strike ($)", yaxis_title="|Delta|",
            margin=dict(l=0, r=0, t=30, b=0), height=260,
            template="plotly_dark", title="Put Delta vs Strike",
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        # Theta decay curve over time
        days_range = list(range(1, dte_bs + 1))
        thetas = [
            bs_greeks(S, K, d / 365, r, sigma, bs_type)["theta"] or 0
            for d in days_range
        ]
        prices_over_time = [
            bs_price(S, K, d / 365, r, sigma, bs_type) or 0
            for d in days_range
        ]
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=days_range[::-1], y=prices_over_time,
            name="Option Price", line=dict(color="#f77f00", width=2),
        ))
        fig3.add_vline(x=dte_bs, line_dash="dot", line_color="white",
                        annotation_text="Today", annotation_position="top")
        fig3.update_layout(
            xaxis_title="DTE", yaxis_title="Option Price ($)",
            margin=dict(l=0, r=0, t=30, b=0), height=260,
            template="plotly_dark", title="Time Decay Curve",
        )
        st.plotly_chart(fig3, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# App shell
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    st.title("⚙️ Wheel Strategy Automation")
    st.caption(
        f"Systematic income generation via cash-secured puts and covered calls  ·  "
        f"Data via yfinance  ·  {date.today().strftime('%B %d, %Y')}"
    )

    # Render sidebar and collect params
    params = render_sidebar()

    # Initialise session state keys
    for key in ("candidates_df", "recommendations_df"):
        if key not in st.session_state:
            st.session_state[key] = pd.DataFrame()

    # Tabs
    t1, t2, t3 = st.tabs(["📊 Screener", "🎯 Recommendations", "🧮 BS Calculator"])

    with t1:
        tab_screener(params)

    with t2:
        tab_recommendations(params)

    with t3:
        tab_bs_calculator(params)


if __name__ == "__main__":
    main()
