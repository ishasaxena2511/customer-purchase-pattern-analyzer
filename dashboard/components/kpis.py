"""
kpis.py
-------
Purpose:
    Computes and renders the top-row executive KPI cards with period-over-period
    deltas for Total Revenue, Total Customers, AOV, Repeat Purchase Rate, and CLV.
"""

from typing import Dict, Any, Optional
import pandas as pd
import streamlit as st

from dashboard.theme import (
    format_currency,
    format_number,
    render_kpi_card_html,
)


def calculate_kpis(
    current_df: pd.DataFrame,
    prior_df: Optional[pd.DataFrame] = None,
    customer_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """
    Calculate headline business KPIs and comparison deltas.

    Parameters
    ----------
    current_df : pd.DataFrame
        Filtered transaction DataFrame for the active period.
    prior_df : Optional[pd.DataFrame]
        Filtered transaction DataFrame for the equivalent prior period.
    customer_df : Optional[pd.DataFrame]
        Full customer features DataFrame for lifetime value metrics.

    Returns
    -------
    Dict[str, Any]
        Dictionary with formatted metric values and delta percentages.
    """
    if current_df.empty:
        return {
            "revenue": 0.0,
            "revenue_str": "₹0.00",
            "revenue_delta": None,
            "customers": 0,
            "customers_str": "0",
            "customers_delta": None,
            "aov": 0.0,
            "aov_str": "₹0.00",
            "aov_delta": None,
            "repeat_rate": 0.0,
            "repeat_rate_str": "0.0%",
            "repeat_rate_delta": None,
            "clv": 0.0,
            "clv_str": "₹0.00",
            "clv_delta": None,
        }

    # Current period metrics
    revenue = float(current_df["Total_Purchase_Value"].sum())
    n_customers = int(current_df["Customer_ID"].nunique())
    n_orders = len(current_df)
    aov = revenue / n_orders if n_orders > 0 else 0.0

    cust_counts = current_df.groupby("Customer_ID").size()
    repeat_customers = int((cust_counts >= 2).sum())
    repeat_rate = (repeat_customers / len(cust_counts) * 100.0) if len(cust_counts) > 0 else 0.0

    # CLV derivation
    active_cust_ids = set(current_df["Customer_ID"].unique())
    if customer_df is not None and not customer_df.empty:
        matched_cust = customer_df[customer_df["Customer_ID"].isin(active_cust_ids)]
        clv = float(matched_cust["Basic_CLV"].mean()) if not matched_cust.empty else (aov * (n_orders / max(n_customers, 1)) * 3.0)
    else:
        clv = aov * (n_orders / max(n_customers, 1)) * 3.0

    # Prior period comparison
    revenue_delta = None
    customers_delta = None
    aov_delta = None
    repeat_rate_delta = None
    clv_delta = None

    if prior_df is not None and not prior_df.empty:
        prior_revenue = float(prior_df["Total_Purchase_Value"].sum())
        prior_customers = int(prior_df["Customer_ID"].nunique())
        prior_orders = len(prior_df)
        prior_aov = prior_revenue / prior_orders if prior_orders > 0 else 0.0

        prior_counts = prior_df.groupby("Customer_ID").size()
        prior_repeat = int((prior_counts >= 2).sum())
        prior_repeat_rate = (prior_repeat / len(prior_counts) * 100.0) if len(prior_counts) > 0 else 0.0

        prior_active_ids = set(prior_df["Customer_ID"].unique())
        if customer_df is not None and not customer_df.empty:
            prior_matched = customer_df[customer_df["Customer_ID"].isin(prior_active_ids)]
            prior_clv = float(prior_matched["Basic_CLV"].mean()) if not prior_matched.empty else (prior_aov * (prior_orders / max(prior_customers, 1)) * 3.0)
        else:
            prior_clv = prior_aov * (prior_orders / max(prior_customers, 1)) * 3.0

        if prior_revenue > 0:
            revenue_delta = ((revenue - prior_revenue) / prior_revenue) * 100.0
        if prior_customers > 0:
            customers_delta = ((n_customers - prior_customers) / prior_customers) * 100.0
        if prior_aov > 0:
            aov_delta = ((aov - prior_aov) / prior_aov) * 100.0
        if prior_customers > 0:
            repeat_rate_delta = repeat_rate - prior_repeat_rate
        if prior_clv > 0:
            clv_delta = ((clv - prior_clv) / prior_clv) * 100.0

    return {
        "revenue": revenue,
        "revenue_str": format_currency(revenue),
        "revenue_delta": revenue_delta,
        "customers": n_customers,
        "customers_str": format_number(n_customers),
        "customers_delta": customers_delta,
        "aov": aov,
        "aov_str": format_currency(aov),
        "aov_delta": aov_delta,
        "repeat_rate": repeat_rate,
        "repeat_rate_str": f"{repeat_rate:.1f}%",
        "repeat_rate_delta": repeat_rate_delta,
        "clv": clv,
        "clv_str": format_currency(clv),
        "clv_delta": clv_delta,
    }


def render_kpi_cards(kpi_data: Dict[str, Any], subtext: str = "vs prior period") -> None:
    """
    Render 5 executive KPI cards side-by-side using responsive Streamlit columns.
    """
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(
            render_kpi_card_html(
                label="Total Revenue",
                value=kpi_data["revenue_str"],
                delta=kpi_data["revenue_delta"],
                delta_suffix="%",
                subtext=subtext,
            ),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            render_kpi_card_html(
                label="Total Customers",
                value=kpi_data["customers_str"],
                delta=kpi_data["customers_delta"],
                delta_suffix="%",
                subtext=subtext,
            ),
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            render_kpi_card_html(
                label="Avg Order Value (AOV)",
                value=kpi_data["aov_str"],
                delta=kpi_data["aov_delta"],
                delta_suffix="%",
                subtext=subtext,
            ),
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            render_kpi_card_html(
                label="Repeat Purchase Rate",
                value=kpi_data["repeat_rate_str"],
                delta=kpi_data["repeat_rate_delta"],
                delta_suffix=" pts",
                subtext=subtext,
            ),
            unsafe_allow_html=True,
        )

    with col5:
        st.markdown(
            render_kpi_card_html(
                label="Customer Lifetime Value",
                value=kpi_data["clv_str"],
                delta=kpi_data["clv_delta"],
                delta_suffix="%",
                subtext=subtext,
            ),
            unsafe_allow_html=True,
        )
