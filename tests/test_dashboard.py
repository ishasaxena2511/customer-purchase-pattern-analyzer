"""
test_dashboard.py
-----------------
Purpose:
    Unit tests for dashboard components: KPI calculations, Plotly chart generation,
    dynamic insight derivation, and theme formatting utilities.
"""

import pandas as pd
import plotly.graph_objects as go
import pytest

from dashboard.components.kpis import calculate_kpis
from dashboard.components.charts import (
    render_revenue_trend,
    render_segment_revenue,
    render_category_performance,
    render_regional_heatmap,
    render_top_customers,
    render_purchase_frequency,
    render_age_group_analysis,
    render_payment_donut,
    render_rfm_scatter,
)
from dashboard.components.recommendations import compute_insights
from dashboard.theme import format_currency, format_number


@pytest.fixture
def sample_data():
    """Create a minimal representative transaction and customer dataset."""
    tx_df = pd.DataFrame(
        {
            "Customer_ID": ["C1", "C1", "C2", "C3", "C3"],
            "Customer_Name": ["Alice", "Alice", "Bob", "Charlie", "Charlie"],
            "Purchase_Date": pd.to_datetime(["2024-01-10", "2024-02-15", "2024-03-01", "2024-04-12", "2024-05-20"]),
            "Total_Purchase_Value": [1000.0, 1500.0, 2000.0, 500.0, 3000.0],
            "Quantity_Purchased": [2, 3, 1, 1, 4],
            "Estimated_Profit": [200.0, 300.0, 400.0, 100.0, 600.0],
            "Product_Category": ["Electronics", "Books", "Electronics", "Clothing", "Books"],
            "Region": ["North", "North", "South", "East", "East"],
            "City": ["Delhi", "Delhi", "Bengaluru", "Kolkata", "Kolkata"],
            "RFM_Segment": ["Champions", "Champions", "Loyal Customers", "At Risk", "At Risk"],
            "Age_Group": ["25-34", "25-34", "35-44", "45-54", "45-54"],
            "Payment_Method": ["UPI", "Credit Card", "UPI", "Debit Card", "Net Banking"],
            "Loyalty_Status": ["Gold", "Gold", "Silver", "Regular", "Regular"],
            "Purchase_Channel": ["Online", "Mobile App", "Online", "In-Store", "Online"],
        }
    )

    cf_df = pd.DataFrame(
        {
            "Customer_ID": ["C1", "C2", "C3"],
            "Customer_Name": ["Alice", "Bob", "Charlie"],
            "RFM_Segment": ["Champions", "Loyal Customers", "At Risk"],
            "Total_Revenue": [2500.0, 2000.0, 3500.0],
            "Order_Count": [2, 1, 2],
            "Purchase_Frequency": [2, 1, 2],
            "Average_Order_Value": [1250.0, 2000.0, 1750.0],
            "Recency": [15, 60, 120],
            "Average_Days_Between_Purchases": [36.0, 0.0, 38.0],
            "Basic_CLV": [7500.0, 6000.0, 10500.0],
            "Cluster": [0, 1, 2],
            "Cluster_Name": ["VIP Core", "Developing", "Lapsed"],
            "Marketing_Action": ["VIP care", "Loyalty up", "Win-back offer"],
        }
    )
    return tx_df, cf_df


def test_theme_formatters():
    """Verify currency and number formatting output standards."""
    assert format_currency(1_500_000.0) == "₹1.50M"
    assert format_currency(25_400.0) == "₹25.4K"
    assert format_currency(450.5) == "₹450.50"

    assert format_number(1_200_000) == "1.20M"
    assert format_number(3_500) == "3.5K"
    assert format_number(129) == "129"


def test_kpis_calculation(sample_data):
    """Verify correct aggregation and delta computation for headline KPIs."""
    tx_df, cf_df = sample_data
    prior_tx = tx_df.iloc[:2]  # Revenue: 2500, Customers: 1

    kpis = calculate_kpis(tx_df, prior_tx, cf_df)

    assert kpis["revenue"] == 8000.0
    assert kpis["customers"] == 3
    assert kpis["aov"] == 1600.0  # 8000 / 5
    assert kpis["repeat_rate"] == (2 / 3) * 100.0  # C1 and C3 repeat
    assert kpis["revenue_delta"] > 0


def test_kpis_empty_df():
    """Verify empty DataFrame does not raise errors and returns safe fallbacks."""
    empty_df = pd.DataFrame()
    kpis = calculate_kpis(empty_df, None, None)
    assert kpis["revenue"] == 0.0
    assert kpis["customers"] == 0
    assert kpis["revenue_delta"] is None


def test_all_charts_render(sample_data):
    """Ensure all modular chart functions return valid Plotly Figures."""
    tx_df, cf_df = sample_data

    charts = [
        render_revenue_trend(tx_df, show_mom=False),
        render_revenue_trend(tx_df, show_mom=True),
        render_segment_revenue(tx_df),
        render_category_performance(tx_df, show_margin=False),
        render_category_performance(tx_df, show_margin=True),
        render_regional_heatmap(tx_df),
        render_top_customers(tx_df, top_n=5),
        render_purchase_frequency(tx_df),
        render_age_group_analysis(tx_df),
        render_payment_donut(tx_df),
        render_rfm_scatter(cf_df),
    ]

    for chart in charts:
        assert isinstance(chart, go.Figure)


def test_charts_empty_dataframe():
    """Verify charts handle completely empty filtered DataFrames without throwing exceptions."""
    empty_df = pd.DataFrame()
    fig1 = render_revenue_trend(empty_df)
    fig2 = render_regional_heatmap(empty_df)
    fig3 = render_top_customers(empty_df)

    assert isinstance(fig1, go.Figure)
    assert isinstance(fig2, go.Figure)
    assert isinstance(fig3, go.Figure)


def test_compute_insights(sample_data):
    """Verify automated dynamic business insight cards and at-risk table."""
    tx_df, cf_df = sample_data
    insights, at_risk = compute_insights(tx_df, cf_df)

    assert "top_segment" in insights
    assert "best_region" in insights
    assert "retention" in insights
    assert "cross_sell" in insights

    # Check top segment matches highest spend segment
    assert "Champions" in insights["top_segment"]["text"] or "At Risk" in insights["top_segment"]["text"]
    # Check at-risk customers were identified
    assert isinstance(at_risk, pd.DataFrame)
    assert len(at_risk) >= 1  # C3 is At Risk
