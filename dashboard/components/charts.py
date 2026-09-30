"""
charts.py
---------
Purpose:
    Modular Plotly charting functions for the Executive Dashboard and RFM analysis.
    Each visualization strictly follows corporate design tokens and handles
    empty filtered states gracefully.
"""

from typing import Optional
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

try:
    from dashboard.theme import (
        COLORS,
        PLOTLY_COLORWAY,
        apply_theme_to_figure,
        format_currency,
    )
except ModuleNotFoundError:
    from theme import (
        COLORS,
        PLOTLY_COLORWAY,
        apply_theme_to_figure,
        format_currency,
    )


def _empty_figure(message: str = "No data available for selected filters.") -> go.Figure:
    """Create an empty placeholder figure with a clean message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color=COLORS["slate"], family="Segoe UI, Inter, sans-serif"),
    )
    apply_theme_to_figure(fig, title="", height=360)
    return fig


# ---------------------------------------------------------
# Row 1: Middle Section Visualizations
# ---------------------------------------------------------

def render_revenue_trend(df: pd.DataFrame, show_mom: bool = False) -> go.Figure:
    """
    Render monthly revenue trend line chart with an interactive MoM growth toggle.
    """
    if df.empty or "Purchase_Date" not in df.columns:
        return _empty_figure("No transaction dates available.")

    temp_df = df.copy()
    temp_df["Purchase_Date"] = pd.to_datetime(temp_df["Purchase_Date"])
    temp_df["Year_Month"] = temp_df["Purchase_Date"].dt.to_period("M").astype(str)

    monthly = (
        temp_df.groupby("Year_Month")
        .agg(
            Revenue=("Total_Purchase_Value", "sum"),
            Orders=("Customer_ID", "count"),
            Customers=("Customer_ID", "nunique"),
        )
        .reset_index()
        .sort_values("Year_Month")
    )

    monthly["MoM_Growth_Pct"] = monthly["Revenue"].pct_change() * 100.0

    if show_mom:
        # MoM Growth % bar chart
        colors = [
            COLORS["success"] if val >= 0 else COLORS["danger"]
            for val in monthly["MoM_Growth_Pct"].fillna(0)
        ]
        fig = go.Figure(
            go.Bar(
                x=monthly["Year_Month"],
                y=monthly["MoM_Growth_Pct"].fillna(0),
                marker_color=colors,
                text=[
                    f"{v:+.1f}%" if pd.notnull(v) else "Base"
                    for v in monthly["MoM_Growth_Pct"]
                ],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>MoM Growth: %{y:.1f}%<extra></extra>",
            )
        )
        fig.add_hline(y=0, line_dash="dash", line_color="#94A3B8", line_width=1)
        apply_theme_to_figure(fig, title="Month-over-Month Revenue Growth (%)", height=380)
        fig.update_yaxes(title_text="MoM Growth (%)", ticksuffix="%")
    else:
        # Absolute monthly revenue line chart
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=monthly["Year_Month"],
                y=monthly["Revenue"],
                mode="lines+markers",
                line=dict(color=COLORS["secondary"], width=3, shape="spline"),
                marker=dict(size=8, color=COLORS["primary"], line=dict(width=2, color="#FFFFFF")),
                fill="tozeroy",
                fillcolor="rgba(19, 168, 158, 0.08)",
                hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.2f}<br>Orders: %{customdata[0]}<extra></extra>",
                customdata=monthly[["Orders"]],
            )
        )
        apply_theme_to_figure(fig, title="Monthly Revenue Trajectory", height=380)
        fig.update_yaxes(title_text="Revenue (₹)", tickprefix="₹")

    fig.update_xaxes(title_text="Month", type="category")
    return fig


def render_segment_revenue(df: pd.DataFrame) -> go.Figure:
    """
    Render horizontal or vertical bar chart of Revenue by customer segment.
    """
    segment_col = "RFM_Segment" if "RFM_Segment" in df.columns else "Customer_Segment"
    if df.empty or segment_col not in df.columns:
        return _empty_figure("No customer segment data available.")

    seg_summary = (
        df.groupby(segment_col)
        .agg(Revenue=("Total_Purchase_Value", "sum"), Customers=("Customer_ID", "nunique"))
        .reset_index()
        .sort_values("Revenue", ascending=True)
    )

    total_rev = seg_summary["Revenue"].sum()
    seg_summary["Share"] = (seg_summary["Revenue"] / total_rev * 100.0) if total_rev > 0 else 0.0

    fig = go.Figure(
        go.Bar(
            y=seg_summary[segment_col],
            x=seg_summary["Revenue"],
            orientation="h",
            marker=dict(
                color=seg_summary["Revenue"],
                colorscale=[[0, "#93C5FD"], [0.5, "#13A89E"], [1.0, "#0B2545"]],
            ),
            text=[f"₹{v/1e3:.1f}K ({s:.1f}%)" for v, s in zip(seg_summary["Revenue"], seg_summary["Share"])],
            textposition="auto",
            hovertemplate="<b>%{y}</b><br>Revenue: ₹%{x:,.2f}<br>Share: %{customdata:.1f}%<extra></extra>",
            customdata=seg_summary["Share"],
        )
    )
    apply_theme_to_figure(fig, title="Revenue by Customer Segment", height=380)
    fig.update_xaxes(title_text="Revenue (₹)", tickprefix="₹")
    fig.update_yaxes(title_text="")
    return fig


def render_category_performance(df: pd.DataFrame, show_margin: bool = False) -> go.Figure:
    """
    Render category performance bar chart with toggle for Revenue vs Gross Margin %.
    """
    if df.empty or "Product_Category" not in df.columns:
        return _empty_figure("No category data available.")

    cat_summary = (
        df.groupby("Product_Category")
        .agg(
            Revenue=("Total_Purchase_Value", "sum"),
            Units=("Quantity_Purchased", "sum"),
            Profit=("Estimated_Profit", "sum") if "Estimated_Profit" in df.columns else ("Total_Purchase_Value", lambda x: 0),
        )
        .reset_index()
    )

    if show_margin and "Profit" in cat_summary.columns:
        cat_summary["Margin_Pct"] = (
            cat_summary["Profit"] / cat_summary["Revenue"] * 100.0
        ).fillna(0.0)
        cat_summary = cat_summary.sort_values("Margin_Pct", ascending=False)

        fig = go.Figure(
            go.Bar(
                x=cat_summary["Product_Category"],
                y=cat_summary["Margin_Pct"],
                marker_color=COLORS["secondary"],
                text=[f"{v:.1f}%" for v in cat_summary["Margin_Pct"]],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Gross Margin: %{y:.1f}%<br>Profit: ₹%{customdata:,.2f}<extra></extra>",
                customdata=cat_summary["Profit"],
            )
        )
        avg_margin = cat_summary["Margin_Pct"].mean()
        fig.add_hline(
            y=avg_margin,
            line_dash="dot",
            line_color=COLORS["accent"],
            annotation_text=f"Avg: {avg_margin:.1f}%",
            annotation_position="top right",
        )
        apply_theme_to_figure(fig, title="Category Gross Margin (%)", height=380)
        fig.update_yaxes(title_text="Gross Margin (%)", ticksuffix="%")
    else:
        cat_summary = cat_summary.sort_values("Revenue", ascending=False)
        fig = go.Figure(
            go.Bar(
                x=cat_summary["Product_Category"],
                y=cat_summary["Revenue"],
                marker_color=COLORS["primary"],
                text=[f"₹{v/1e3:.1f}K" for v in cat_summary["Revenue"]],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.2f}<br>Units: %{customdata}<extra></extra>",
                customdata=cat_summary["Units"],
            )
        )
        apply_theme_to_figure(fig, title="Category Revenue Performance", height=380)
        fig.update_yaxes(title_text="Revenue (₹)", tickprefix="₹")

    fig.update_xaxes(title_text="", tickangle=-20)
    return fig


# ---------------------------------------------------------
# Row 2: Secondary Middle Visualizations
# ---------------------------------------------------------

def render_regional_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Render regional sales heatmap (Region x Product_Category) with revenue cells.
    """
    if df.empty or "Region" not in df.columns or "Product_Category" not in df.columns:
        return _empty_figure("Regional data unavailable.")

    pivot = pd.pivot_table(
        df,
        values="Total_Purchase_Value",
        index="Region",
        columns="Product_Category",
        aggfunc="sum",
        fill_value=0.0,
    )

    if pivot.empty:
        return _empty_figure("No regional category matrix available.")

    text_values = pivot.map(lambda v: f"₹{v/1e3:.1f}K" if v >= 1000 else f"₹{v:.0f}")

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            text=text_values.values,
            texttemplate="%{text}",
            textfont=dict(size=11, family="Segoe UI, Inter, sans-serif"),
            colorscale=[
                [0.0, "#F8FAFC"],
                [0.2, "#CCFBF1"],
                [0.5, "#14B8A6"],
                [0.8, "#0F766E"],
                [1.0, "#0B2545"],
            ],
            colorbar=dict(title="Revenue (₹)", tickprefix="₹"),
            hovertemplate="<b>%{y} × %{x}</b><br>Revenue: ₹%{z:,.2f}<extra></extra>",
        )
    )
    apply_theme_to_figure(fig, title="Regional Category Revenue Heatmap", height=380)
    fig.update_xaxes(tickangle=-15)
    return fig


def render_top_customers(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """
    Render horizontal bar chart of top N customers by total spend.
    """
    if df.empty or "Customer_ID" not in df.columns:
        return _empty_figure("Customer purchase records unavailable.")

    name_col = "Customer_Name" if "Customer_Name" in df.columns else "Customer_ID"

    top_cust = (
        df.groupby(["Customer_ID", name_col])
        .agg(Revenue=("Total_Purchase_Value", "sum"), Orders=("Total_Purchase_Value", "count"))
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(top_n)
    )

    if top_cust.empty:
        return _empty_figure("No top customer records found.")

    top_cust["Display_Label"] = top_cust[name_col] + " (" + top_cust["Customer_ID"] + ")"
    top_cust = top_cust.sort_values("Revenue", ascending=True)

    fig = go.Figure(
        go.Bar(
            y=top_cust["Display_Label"],
            x=top_cust["Revenue"],
            orientation="h",
            marker_color=COLORS["secondary"],
            text=[f"₹{v:,.0f}" for v in top_cust["Revenue"]],
            textposition="auto",
            hovertemplate="<b>%{y}</b><br>Spend: ₹%{x:,.2f}<br>Orders: %{customdata}<extra></extra>",
            customdata=top_cust["Orders"],
        )
    )
    apply_theme_to_figure(fig, title=f"Top {top_n} Customers by Spend", height=380)
    fig.update_xaxes(title_text="Total Spend (₹)", tickprefix="₹")
    fig.update_yaxes(title_text="")
    return fig


def render_purchase_frequency(df: pd.DataFrame) -> go.Figure:
    """
    Render purchase frequency distribution among customers.
    """
    if df.empty or "Customer_ID" not in df.columns:
        return _empty_figure("Purchase frequency records unavailable.")

    order_counts = df.groupby("Customer_ID").size().value_counts().sort_index().reset_index()
    order_counts.columns = ["Order_Count", "Customer_Count"]

    fig = go.Figure(
        go.Bar(
            x=[f"{int(x)} Orders" for x in order_counts["Order_Count"]],
            y=order_counts["Customer_Count"],
            marker_color=COLORS["primary"],
            text=order_counts["Customer_Count"],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Customers: %{y}<extra></extra>",
        )
    )
    apply_theme_to_figure(fig, title="Customer Purchase Frequency Distribution", height=380)
    fig.update_xaxes(title_text="Orders per Customer")
    fig.update_yaxes(title_text="Number of Customers")
    return fig


# ---------------------------------------------------------
# Row 3: Demographics & Channels
# ---------------------------------------------------------

def render_age_group_analysis(df: pd.DataFrame) -> go.Figure:
    """
    Render spend analysis across customer demographic age groups.
    """
    if df.empty or "Age_Group" not in df.columns:
        return _empty_figure("Age group demographic data unavailable.")

    age_summary = (
        df.groupby("Age_Group")
        .agg(
            Revenue=("Total_Purchase_Value", "sum"),
            Orders=("Customer_ID", "count"),
            Avg_Spend=("Total_Purchase_Value", "mean"),
        )
        .reset_index()
    )

    # Standard natural age group sort order
    order_map = {"18-24": 1, "25-34": 2, "35-44": 3, "45-54": 4, "55+": 5}
    age_summary["Order"] = age_summary["Age_Group"].map(lambda x: order_map.get(x, 99))
    age_summary = age_summary.sort_values("Order")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=age_summary["Age_Group"],
            y=age_summary["Revenue"],
            name="Total Revenue",
            marker_color=COLORS["primary"],
            text=[f"₹{v/1e3:.1f}K" for v in age_summary["Revenue"]],
            textposition="auto",
            hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.2f}<br>Avg Order: ₹%{customdata:,.2f}<extra></extra>",
            customdata=age_summary["Avg_Spend"],
        )
    )
    apply_theme_to_figure(fig, title="Revenue by Customer Age Group", height=360)
    fig.update_xaxes(title_text="Age Group")
    fig.update_yaxes(title_text="Revenue (₹)", tickprefix="₹")
    return fig


def render_payment_donut(df: pd.DataFrame) -> go.Figure:
    """
    Render payment method distribution donut chart.
    """
    if df.empty or "Payment_Method" not in df.columns:
        return _empty_figure("Payment method data unavailable.")

    pay_summary = (
        df.groupby("Payment_Method")
        .agg(Revenue=("Total_Purchase_Value", "sum"), Orders=("Customer_ID", "count"))
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )

    fig = go.Figure(
        data=[
            go.Pie(
                labels=pay_summary["Payment_Method"],
                values=pay_summary["Revenue"],
                hole=0.55,
                marker=dict(colors=PLOTLY_COLORWAY),
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Revenue: ₹%{value:,.2f}<br>Share: %{percent}<extra></extra>",
            )
        ]
    )
    apply_theme_to_figure(fig, title="Payment Method Revenue Share", height=360)
    fig.update_layout(showlegend=False)
    return fig


# ---------------------------------------------------------
# Segments Tab Visualizations
# ---------------------------------------------------------

def render_rfm_scatter(customer_df: pd.DataFrame) -> go.Figure:
    """
    Render 2D interactive scatter plot of Recency vs Monetary Value sized by Frequency.
    """
    if customer_df.empty or "Recency" not in customer_df.columns:
        return _empty_figure("Customer RFM metrics unavailable.")

    desired_hover = {
        "Customer_ID": True,
        "RFM_Score": True,
        "Recency": True,
        "Purchase_Frequency": True,
        "Total_Revenue": ":,.2f",
        "Basic_CLV": ":,.2f",
    }
    hover_data = {k: v for k, v in desired_hover.items() if k in customer_df.columns}

    fig = px.scatter(
        customer_df,
        x="Recency",
        y="Total_Revenue",
        size="Purchase_Frequency",
        color="RFM_Segment" if "RFM_Segment" in customer_df.columns else ("Cluster_Name" if "Cluster_Name" in customer_df.columns else None),
        hover_name="Customer_Name" if "Customer_Name" in customer_df.columns else None,
        hover_data=hover_data,
        color_discrete_sequence=PLOTLY_COLORWAY,
        size_max=28,
    )
    apply_theme_to_figure(fig, title="Customer RFM Landscape (Recency vs Monetary)", height=450)
    fig.update_xaxes(title_text="Recency (Days since last purchase — Lower is fresher)")
    fig.update_yaxes(title_text="Monetary Value / Revenue (₹)", tickprefix="₹")
    return fig
