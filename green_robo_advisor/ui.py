"""Look and feel of the web app (used only by app.py).

Team enhancements A5 and A6 live here, so that app.py stays a readable sequence of steps:
- A5 Modern design: one colour system, fonts, styled buttons, tabs and cards, and the
     ESG ticker tape in the header.
- A6 Interactive charts: Plotly charts with hover values and zoom. Dates are always passed
     explicitly as the x-axis (handout 12.4: never plot the row number by mistake).

Colour meaning is fixed across the whole app:
    teal  = the portfolio and equity ETFs      gold  = ESG and bond ETFs
    slate = the benchmark                      coral = warnings and losses
"""
from __future__ import annotations

import html

import pandas as pd
import plotly.graph_objects as go

# --- colour tokens --------------------------------------------------------------------
NAVY = "#0E1726"
PANEL = "#16223A"
PANEL_2 = "#1C2B47"
BORDER = "#263756"
TEXT = "#E7EEF8"
MUTED = "#9AA8BF"
TEAL = "#4FD1C5"
GOLD = "#E3B341"
SLATE = "#8DA2C0"
CORAL = "#F2797B"
ASSET_COLORS = {"Equity": TEAL, "Bond": GOLD}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Sora:wght@600;700&display=swap');

.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea,
.stApp button, .stApp td, .stApp th {{ font-family: 'IBM Plex Sans', system-ui, sans-serif; }}
.stApp h1, .stApp h2, .stApp h3 {{ font-family: 'Sora', 'IBM Plex Sans', sans-serif; letter-spacing: -0.01em; }}
.block-container {{ padding-top: 2.2rem; max-width: 1240px; }}
#MainMenu, footer, [data-testid="stDecoration"] {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}

/* Fallback: force the dark look even if .streamlit/config.toml is missing (e.g. not uploaded) */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {{ background-color: {NAVY} !important; }}
.stApp, .stApp p, .stApp li, .stApp label, .stApp span, .stApp h1, .stApp h2, .stApp h3,
[data-testid="stWidgetLabel"] p, [data-testid="stMarkdownContainer"] p {{ color: {TEXT}; }}
.stApp [data-testid="stCaptionContainer"], .stApp small {{ color: {MUTED} !important; }}
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="base-input"],
.stTextInput input, .stDateInput input, [data-baseweb="select"] input {{
    background-color: {PANEL} !important; color: {TEXT} !important; border-color: {BORDER} !important; }}
[data-baseweb="select"] svg, [data-testid="stExpander"] svg {{ fill: {MUTED}; }}
[data-baseweb="popover"] ul, [data-baseweb="menu"], [role="listbox"] {{ background-color: {PANEL_2} !important; }}
[role="option"] {{ color: {TEXT} !important; }}
[data-baseweb="tag"] {{ background-color: {TEAL} !important; }}
[data-baseweb="tag"] span {{ color: {NAVY} !important; }}
[data-testid="stExpander"] details, [data-testid="stExpander"] > div {{ background-color: {PANEL}; border-color: {BORDER}; }}
[data-testid="stExpander"] summary p {{ color: {TEXT}; }}
[role="slider"] {{ background-color: {TEAL} !important; box-shadow: none !important; }}
[data-testid="stSliderThumbValue"], [data-testid="stThumbValue"] {{ color: {TEAL} !important; }}
[data-testid="stCheckbox"] [role="checkbox"], [data-baseweb="checkbox"] > span {{ border-color: {SLATE}; }}
[data-testid="stTooltipIcon"] svg {{ stroke: {MUTED}; }}
[data-testid="stRadio"] [role="radiogroup"] label p {{ color: {TEXT} !important; }}
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) p {{ color: {TEAL} !important; }}
[data-testid="stAlert"] p {{ color: inherit; }}

/* sidebar */
section[data-testid="stSidebar"] {{ background: {PANEL}; border-right: 1px solid {BORDER}; }}
section[data-testid="stSidebar"] h2 {{ font-size: 1.05rem; color: {TEXT}; margin-top: .6rem; }}

/* hero */
.gr-hero {{ padding: 6px 0 4px; }}
.gr-hero h1 {{ font-size: 2.6rem; line-height: 1.1; margin: 0 0 .5rem; color: {TEXT}; }}
.stApp .gr-hero p.gr-tagline {{ color: {MUTED}; font-size: 1.08rem; max-width: 62ch; margin: 0 0 1.1rem; }}
.stApp p.gr-legal {{ color: {MUTED}; font-size: .8rem; margin-top: 2.5rem; border-top: 1px solid {BORDER}; padding-top: 1rem; }}

/* ESG ticker tape: the one moving element; pauses on hover, stops for reduced motion */
.gr-tape {{ overflow: hidden; border-top: 1px solid {BORDER}; border-bottom: 1px solid {BORDER};
           background: {PANEL}; border-radius: 10px; margin: 0 0 1.6rem; }}
.gr-tape-track {{ display: flex; width: max-content; animation: gr-scroll 60s linear infinite; }}
.gr-tape:hover .gr-tape-track {{ animation-play-state: paused; }}
@media (prefers-reduced-motion: reduce) {{ .gr-tape-track {{ animation: none; }} }}
@keyframes gr-scroll {{ from {{ transform: translateX(0); }} to {{ transform: translateX(-50%); }} }}
.gr-chip {{ display: flex; align-items: center; gap: 10px; padding: 10px 22px; border-right: 1px solid {BORDER};
           white-space: nowrap; font-variant-numeric: tabular-nums; }}
.gr-chip b {{ color: {TEXT}; font-weight: 600; }}
.gr-chip .gr-dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}
.gr-chip .gr-bar {{ width: 54px; height: 5px; background: {BORDER}; border-radius: 3px; overflow: hidden; }}
.gr-chip .gr-bar i {{ display: block; height: 100%; background: {GOLD}; }}
.gr-chip span {{ color: {MUTED}; font-size: .85rem; }}

/* section headers (the steps are a real sequence, so they are numbered) */
.gr-step {{ display: flex; align-items: baseline; gap: 14px; margin: 1.8rem 0 .3rem; }}
.gr-step em {{ font-style: normal; font-family: 'Sora', sans-serif; color: {NAVY}; background: {TEAL};
              border-radius: 999px; width: 30px; height: 30px; display: inline-flex; align-items: center;
              justify-content: center; font-weight: 700; flex: none; }}
.gr-step h2 {{ margin: 0; font-size: 1.45rem; }}
.stApp p.gr-step-note {{ color: {MUTED}; margin: 0 0 1rem 44px; }}
.stApp p.gr-group {{ color: {GOLD}; font-weight: 600; margin: 1rem 0 .2rem; }}

/* profile and KPI cards */
.gr-profile {{ background: linear-gradient(135deg, {PANEL_2}, {PANEL}); border: 1px solid {BORDER};
              border-radius: 16px; padding: 22px 26px; margin: 1rem 0; }}
.gr-profile .gr-level {{ font-family: 'Sora', sans-serif; font-size: 2rem; color: {TEAL}; margin: 0; }}
.gr-profile .gr-sub {{ color: {MUTED}; margin: .2rem 0 1rem; }}
.gr-stats {{ display: flex; flex-wrap: wrap; gap: 14px; }}
.gr-stats > .gr-stat {{ flex: 1 1 170px; }}
.gr-stat {{ background: {NAVY}; border: 1px solid {BORDER}; border-radius: 12px; padding: 14px 16px; }}
.gr-stat small {{ color: {MUTED}; display: block; font-size: .8rem; margin-bottom: 4px; }}
.gr-stat {{ min-width: 0; }}
.gr-stat strong {{ font-family: 'Sora', sans-serif; font-size: clamp(1.05rem, 1.35vw, 1.4rem); color: {TEXT};
                  font-variant-numeric: tabular-nums; display: block; white-space: nowrap;
                  word-break: keep-all; overflow-wrap: normal; hyphens: none;
                  overflow: hidden; text-overflow: ellipsis; }}
.gr-stat.gr-accent strong {{ color: {TEAL}; }}
.gr-stat.gr-esg strong {{ color: {GOLD}; }}
.gr-stat span {{ color: {MUTED}; font-size: .8rem; display: block; margin-top: 2px; }}
.gr-source {{ display: inline-block; padding: 6px 14px; border-radius: 999px; font-size: .85rem;
             border: 1px solid {BORDER}; color: {MUTED}; background: {PANEL}; margin: .6rem 0 .2rem; }}
.gr-source b {{ color: {TEAL}; }}

/* buttons */
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"] {{
    background: linear-gradient(90deg, {TEAL}, #38B2AC); color: {NAVY}; border: 0; border-radius: 12px;
    font-weight: 600; padding: .75rem 1.4rem; font-size: 1.02rem; box-shadow: 0 6px 24px rgba(79,209,197,.25); }}
.stButton > button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover {{
    filter: brightness(1.08); color: {NAVY}; }}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {{ outline: 2px solid {GOLD}; outline-offset: 2px; }}
.stDownloadButton > button {{ background: transparent; border: 1px solid {TEAL}; color: {TEAL}; border-radius: 10px; }}
.stDownloadButton > button:hover {{ background: rgba(79,209,197,.12); color: {TEAL}; border-color: {TEAL}; }}

/* tabs as pills */
.stTabs [data-baseweb="tab-list"] {{ gap: 8px; border-bottom: 0; }}
.stTabs [data-baseweb="tab"], .stTabs button[role="tab"] {{ background: {PANEL}; border: 1px solid {BORDER} !important;
    border-radius: 999px !important; padding: 8px 18px !important; height: auto; }}
.stTabs [aria-selected="true"] {{ background: rgba(79,209,197,.14) !important; border-color: {TEAL} !important; }}
.stTabs [aria-selected="true"] p {{ color: {TEAL}; font-weight: 600; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none; }}

/* answer options as selectable pills */
/* works with Streamlit 1.32 (label > input) and newer versions (div > label > span > input) */
[data-testid="stRadio"] [role="radiogroup"] {{ gap: 8px; flex-wrap: wrap; }}
[data-testid="stRadio"] [role="radiogroup"] label {{ background: {PANEL}; border: 1px solid {BORDER};
    border-radius: 999px; padding: 5px 14px 5px 10px; margin: 0 !important; transition: border-color .15s; }}
[data-testid="stRadio"] [role="radiogroup"] label:hover {{ border-color: {SLATE}; }}
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {{ border-color: {TEAL};
    background: rgba(79,209,197,.14); }}
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) p {{ color: {TEAL}; }}
[data-testid="stRadio"] > label p {{ color: {TEXT}; font-weight: 500; }}
</style>
"""


def inject_css() -> str:
    return CSS


def hero(metadata: pd.DataFrame) -> str:
    """Title, one-line purpose and the ESG ticker tape with every ETF in the universe."""
    chips = []
    for _, row in metadata.iterrows():
        score = float(row["esg_quality_score"])
        chips.append(
            f'<div class="gr-chip"><i class="gr-dot" style="background:{ASSET_COLORS.get(row["asset_class"], SLATE)}"></i>'
            f'<b>{html.escape(row["ticker"])}</b><span>{html.escape(str(row.get("theme", "")))}</span>'
            f'<div class="gr-bar" title="ESG score {score:.1f} of 10"><i style="width:{score * 10:.0f}%"></i></div>'
            f'<span>ESG {score:.1f}</span></div>'
        )
    track = "".join(chips) * 2  # duplicated for a seamless loop
    return (
        '<div class="gr-hero"><h1>Green Robo Advisor</h1>'
        '<p class="gr-tagline">Build a sustainable ETF portfolio that fits the risk you want, the risk you can '
        'afford, and how green you want to invest.</p></div>'
        f'<div class="gr-tape" aria-label="ETF universe with ESG scores"><div class="gr-tape-track">{track}</div></div>'
    )


def step(number: int, title: str, note: str = "") -> str:
    note_html = f'<p class="gr-step-note">{html.escape(note)}</p>' if note else ""
    return f'<div class="gr-step"><em>{number}</em><h2>{html.escape(title)}</h2></div>{note_html}'


def stat(label: str, value: str, sub: str = "", kind: str = "") -> str:
    sub_html = f"<span>{html.escape(sub)}</span>" if sub else ""
    return (f'<div class="gr-stat {kind}"><small>{html.escape(label)}</small>'
            f'<strong>{html.escape(value)}</strong>{sub_html}</div>')


def profile_card(profile) -> str:
    floor = "none" if profile.suggested_esg_floor is None else f"{profile.suggested_esg_floor:.1f}"
    stats = "".join([
        stat("Target return", f"{profile.target_return:.1%}", "annual, log", "gr-accent"),
        stat("Target volatility", f"{profile.target_risk:.1%}", "annual"),
        stat("Risk you want", profile.risk_tolerance_level or profile.risk_level, "risk tolerance"),
        stat("Money needed soon", profile.liquidity_need, "risk capacity"),
        stat("ESG floor", floor, "from your ESG answer", "gr-esg"),
    ])
    return (f'<div class="gr-profile"><p class="gr-level">{html.escape(profile.risk_level)} investor</p>'
            f'<p class="gr-sub">{html.escape(profile.explanation)}</p><div class="gr-stats">{stats}</div></div>')


def source_badge(data: dict) -> str:
    first, last, n_days = data["sample_period"]
    label = "Sample data (offline)" if data["data_source"] == "sample" else f"Live data: {data['data_source']}"
    return (f'<div class="gr-source"><b>{html.escape(label)}</b> &nbsp;{first} to {last}, '
            f'{n_days:,} trading days</div>')


# --- A6 interactive charts ------------------------------------------------------------------

def _layout(fig: go.Figure, height: int = 360, y_format: str = "") -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=36, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, sans-serif", color=MUTED, size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=PANEL_2, bordercolor=BORDER, font=dict(color=TEXT)),
        hovermode="x unified",
    )
    fig.update_xaxes(gridcolor="#22314F", zeroline=False, showline=False)
    fig.update_yaxes(gridcolor="#22314F", zeroline=False, tickformat=y_format)
    return fig


def line_chart(portfolio: pd.Series, benchmark: pd.Series, y_format: str = "", height: int = 340,
               fill: bool = False) -> go.Figure:
    """Portfolio (teal, solid) vs benchmark (slate, dashed) on the same dates."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=benchmark.index, y=benchmark.values, name="Benchmark",
                             line=dict(color=SLATE, width=1.6, dash="dot")))
    fig.add_trace(go.Scatter(x=portfolio.index, y=portfolio.values, name="Portfolio",
                             line=dict(color=TEAL, width=2.4),
                             fill="tozeroy" if fill else None, fillcolor="rgba(79,209,197,.16)"))
    return _layout(fig, height, y_format)


def allocation_chart(weights: pd.Series, risk_share: pd.Series, metadata: pd.DataFrame) -> go.Figure:
    """Weight vs share of risk per ETF, sorted by weight; bar colour = asset class."""
    meta = metadata.set_index("ticker")
    order = weights.sort_values().index
    colors = [ASSET_COLORS.get(meta.loc[t, "asset_class"], SLATE) for t in order]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=list(order), x=weights[order], orientation="h", name="Weight",
                         marker=dict(color=colors), text=[f"{w:.0%}" if w > 0.005 else "" for w in weights[order]],
                         textposition="outside", hovertemplate="%{y}: %{x:.1%} of the money<extra></extra>"))
    fig.add_trace(go.Bar(y=list(order), x=risk_share[order], orientation="h", name="Share of risk",
                         marker=dict(color="rgba(0,0,0,0)", line=dict(color=CORAL, width=1.5)),
                         hovertemplate="%{y}: %{x:.1%} of the risk<extra></extra>"))
    fig.update_layout(barmode="group", bargap=0.25, hovermode="closest")
    fig = _layout(fig, max(320, 46 * len(order)))
    top = float(max(weights.max(), risk_share.max()))
    fig.update_xaxes(tickformat=".0%", range=[0, top * 1.18])
    fig.update_traces(textfont=dict(color=TEXT), cliponaxis=False, selector=dict(name="Weight"))
    return fig


def correlation_chart(corr: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=corr.values, x=list(corr.columns), y=list(corr.index), zmin=0, zmax=1,
        colorscale=[[0, PANEL], [0.5, "#1F5F63"], [1, "#2E9C93"]],
        text=[[f"{v:.2f}" for v in row] for row in corr.values], texttemplate="%{text}",
        textfont=dict(color=TEXT, size=12),
        hovertemplate="%{y} vs %{x}: %{z:.2f}<extra></extra>", colorbar=dict(thickness=10),
    ))
    fig.update_yaxes(autorange="reversed")
    fig = _layout(fig, 460)
    fig.update_layout(hovermode="closest")
    return fig
