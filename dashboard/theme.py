"""
theme.py
--------
Purpose:
    Defines corporate styling tokens, color palettes, chart styling,
    and CSS definitions for the Streamlit executive analytics dashboard.
"""

# Corporate Color Palette Specification
COLORS = {
    "primary": "#0B2545",       # Corporate Deep Navy
    "secondary": "#13A89E",     # Dynamic Teal
    "accent": "#F59E0B",        # Alert & Highlight Amber
    "navy_light": "#134074",    # Lighter Slate Navy
    "neutral_dark": "#0B2545",  # Deep Charcoal Text
    "neutral_light": "#F8FAFC", # Light Gray Dashboard Canvas
    "card_bg": "#FFFFFF",       # Pure White Surface Cards
    "border": "#E2E8F0",        # Subtle Surface Borders
    "success": "#10B981",       # Emerald Green Delta Positive
    "warning": "#F59E0B",       # Amber Warning
    "danger": "#EF4444",        # Crimson Alert
    "purple": "#8B5CF6",        # Royal Violet
    "slate": "#64748B",         # Muted Subtext
}

# Qualitative sequence for multi-category Plotly charts
PLOTLY_COLORWAY = [
    "#0B2545",  # Navy
    "#13A89E",  # Teal
    "#F59E0B",  # Amber
    "#8B5CF6",  # Violet
    "#10B981",  # Green
    "#EF4444",  # Crimson
    "#64748B",  # Slate
    "#3B82F6",  # Sky Blue
]

CUSTOM_CSS = """
<style>
    /* Global Page Styling */
    .main {
        background-color: #F8FAFC;
    }
    
    /* Clean Chrome Styling */
    header[data-testid="stHeader"] {
        visibility: hidden;
        height: 0px;
    }
    #MainMenu {
        visibility: hidden;
    }
    footer {
        visibility: hidden;
    }
    
    /* Executive Header */
    .executive-header {
        background: linear-gradient(135deg, #0B2545 0%, #134074 100%);
        color: #FFFFFF;
        padding: 24px 32px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(11, 37, 69, 0.08);
    }
    .executive-title {
        font-size: 26px;
        font-weight: 700;
        margin: 0;
        color: #FFFFFF !important;
        letter-spacing: -0.5px;
    }
    .executive-subtitle {
        font-size: 14px;
        color: #94A3B8;
        margin-top: 4px;
        margin-bottom: 0;
    }
    
    /* KPI Metric Cards */
    .kpi-container {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(11, 37, 69, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .kpi-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(11, 37, 69, 0.08);
    }
    .kpi-label {
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748B;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 700;
        color: #0B2545;
        margin-bottom: 4px;
        line-height: 1.1;
    }
    .kpi-delta-positive {
        font-size: 12px;
        font-weight: 600;
        color: #10B981;
    }
    .kpi-delta-negative {
        font-size: 12px;
        font-weight: 600;
        color: #EF4444;
    }
    .kpi-delta-neutral {
        font-size: 12px;
        font-weight: 500;
        color: #64748B;
    }

    /* Section Cards */
    .section-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 6px rgba(11, 37, 69, 0.04);
    }
    .section-title {
        font-size: 17px;
        font-weight: 700;
        color: #0B2545;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Insight Callout Cards */
    .insight-card {
        background-color: #F1F5F9;
        border-left: 4px solid #13A89E;
        padding: 14px 18px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 12px;
    }
    .insight-card-alert {
        background-color: #FFFBEB;
        border-left: 4px solid #F59E0B;
        padding: 14px 18px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 12px;
    }
    .insight-header {
        font-size: 13px;
        font-weight: 700;
        color: #0B2545;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .insight-body {
        font-size: 13px;
        color: #334155;
        line-height: 1.4;
    }
</style>
"""


def format_currency(value: float) -> str:
    """Format float into clean Indian Rupee / corporate currency notation."""
    if abs(value) >= 1_000_000:
        return f"₹{value / 1_000_000:.2f}M"
    elif abs(value) >= 1_000:
        return f"₹{value / 1_000:.1f}K"
    else:
        return f"₹{value:,.2f}"


def format_number(value: float) -> str:
    """Format float or integer into clean readable notation."""
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    else:
        return f"{int(value):,}" if value == int(value) else f"{value:.1f}"


def render_kpi_card_html(
    label: str,
    value: str,
    delta: float | None = None,
    delta_suffix: str = "%",
    subtext: str = "vs prior period",
    is_higher_better: bool = True,
) -> str:
    """
    Generate HTML for a styled executive KPI card with delta indicator.
    """
    if delta is None:
        delta_html = f'<div class="kpi-delta-neutral">Baseline period</div>'
    else:
        is_positive = delta > 0
        is_favorable = is_positive if is_higher_better else not is_positive
        delta_class = "kpi-delta-positive" if is_favorable else ("kpi-delta-negative" if delta != 0 else "kpi-delta-neutral")
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "•")
        sign = "+" if delta > 0 else ""
        delta_html = f'<div class="{delta_class}">{arrow} {sign}{delta:.1f}{delta_suffix} <span style="color:#94A3B8;font-weight:400;">{subtext}</span></div>'

    html = f"""
    <div class="kpi-container">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """
    return html


def render_insight_card_html(
    title: str,
    content: str,
    alert: bool = False,
    badge: str = "",
) -> str:
    """
    Generate HTML for an automated business insight card.
    """
    card_class = "insight-card-alert" if alert else "insight-card"
    badge_html = f'<span style="background-color:{"#F59E0B" if alert else "#13A89E"};color:#FFFFFF;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:700;margin-left:8px;vertical-align:middle;">{badge}</span>' if badge else ""
    return f"""
    <div class="{card_class}">
        <div class="insight-header">{title} {badge_html}</div>
        <div class="insight-body">{content}</div>
    </div>
    """


def apply_theme_to_figure(fig, title: str = "", height: int = 400):
    """
    Apply corporate styling standards to any Plotly figure.
    """
    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(family="Segoe UI, Inter, sans-serif", size=15, color=COLORS["primary"]),
            x=0.01,
            y=0.96,
        ),
        font=dict(family="Segoe UI, Inter, sans-serif", size=12, color=COLORS["neutral_dark"]),
        colorway=PLOTLY_COLORWAY,
        margin=dict(l=40, r=30, t=50, b=40),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.8)",
        ),
    )
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="#F1F5F9",
        linecolor="#CBD5E1",
        tickfont=dict(size=11, color="#64748B"),
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="#F1F5F9",
        linecolor="#CBD5E1",
        tickfont=dict(size=11, color="#64748B"),
    )
    return fig


