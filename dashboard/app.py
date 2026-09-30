"""
app.py
------
Purpose:
    Executive Business Intelligence Dashboard for Customer Purchase Pattern Analyzer.
    Provides responsive filters, headline KPIs with period deltas, multi-dimensional
    sales analytics, dynamic recommendations, RFM segmentation, and data quality audits.
"""

from pathlib import Path
from typing import Tuple
import pandas as pd
import streamlit as st

from dashboard.theme import CUSTOM_CSS
from dashboard.components.kpis import calculate_kpis, render_kpi_cards
from dashboard.components.charts import (
    render_revenue_trend,
    render_segment_revenue,
    render_category_performance,
    render_regional_heatmap,
    render_top_customers,
    render_purchase_frequency,
    render_age_group_analysis,
    render_payment_donut,
)
from dashboard.components.recommendations import (
    compute_insights,
    render_insights_section,
)
from dashboard.components.segments_tab import render_segments_tab
from dashboard.components.data_quality import render_data_quality_tab

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"


@st.cache_data
def load_datasets() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load transactions and customer features, merging segment attributes for analytical joins.
    """
    tx_path = DATA_DIR / "transactions_features.csv"
    cf_path = DATA_DIR / "customer_features.csv"

    if not tx_path.exists():
        raise FileNotFoundError(f"Missing processed transaction data: {tx_path}")
    if not cf_path.exists():
        raise FileNotFoundError(f"Missing processed customer data: {cf_path}")

    tx_df = pd.read_csv(tx_path)
    cf_df = pd.read_csv(cf_path)

    tx_df["Purchase_Date"] = pd.to_datetime(tx_df["Purchase_Date"])

    # Harmonize RFM Segment onto transactions if not present
    if "RFM_Segment" not in tx_df.columns and "RFM_Segment" in cf_df.columns:
        seg_map = cf_df.set_index("Customer_ID")["RFM_Segment"].to_dict()
        tx_df["RFM_Segment"] = tx_df["Customer_ID"].map(seg_map).fillna("Standard")

    return tx_df, cf_df


def main() -> None:
    st.set_page_config(
        page_title="Executive Analytics | Customer Purchase Analyzer",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject Corporate CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Load Data
    try:
        transactions_df, customer_df = load_datasets()
    except Exception as exc:
        st.error(f"Error loading analytical data: {exc}")
        st.info("Run `python src/run_pipeline.py` to generate processed datasets.")
        return

    # Header Banner
    st.markdown(
        """
        <div class="executive-header">
            <h1 class="executive-title">📊 Executive Purchase Pattern & Revenue Analyzer</h1>
            <p class="executive-subtitle">Enterprise Retail Analytics • Dynamic Cohorts • Churn Risk & Strategic Recommendations</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------------------------------------
    # Sidebar Filters
    # -------------------------------------------------------------
    st.sidebar.markdown("### 🎛️ Executive Filters")

    # Date Range Filter
    min_date = transactions_df["Purchase_Date"].min().date()
    max_date = transactions_df["Purchase_Date"].max().date()
    date_selection = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        help="Select calendar window for transaction evaluation",
    )

    if isinstance(date_selection, (tuple, list)) and len(date_selection) == 2:
        start_date, end_date = date_selection
    else:
        start_date, end_date = min_date, max_date

    # Region Filter
    all_regions = sorted(transactions_df["Region"].dropna().unique().tolist())
    selected_regions = st.sidebar.multiselect("Region", options=all_regions, default=all_regions)

    # City Filter (Hierarchically filtered by selected regions)
    available_cities = sorted(
        transactions_df[transactions_df["Region"].isin(selected_regions)]["City"].dropna().unique().tolist()
    )
    selected_cities = st.sidebar.multiselect("City", options=available_cities, default=available_cities)

    # Product Category Filter
    all_categories = sorted(transactions_df["Product_Category"].dropna().unique().tolist())
    selected_categories = st.sidebar.multiselect("Product Category", options=all_categories, default=all_categories)

    # Customer Segment Filter
    all_segments = sorted(transactions_df["RFM_Segment"].dropna().unique().tolist())
    selected_segments = st.sidebar.multiselect("Customer Segment", options=all_segments, default=all_segments)

    # Loyalty Status Filter
    all_loyalty = sorted(transactions_df["Loyalty_Status"].dropna().unique().tolist())
    selected_loyalty = st.sidebar.multiselect("Loyalty Status", options=all_loyalty, default=all_loyalty)

    # Payment Method Filter
    all_payments = sorted(transactions_df["Payment_Method"].dropna().unique().tolist())
    selected_payments = st.sidebar.multiselect("Payment Method", options=all_payments, default=all_payments)

    # Purchase Channel Filter
    all_channels = sorted(transactions_df["Purchase_Channel"].dropna().unique().tolist())
    selected_channels = st.sidebar.multiselect("Purchase Channel", options=all_channels, default=all_channels)

    # Reset Filter Button
    if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
        st.rerun()

    # -------------------------------------------------------------
    # Apply Filtering Logic & Calculate Comparison Windows
    # -------------------------------------------------------------
    tx_mask = (
        (transactions_df["Purchase_Date"].dt.date >= start_date)
        & (transactions_df["Purchase_Date"].dt.date <= end_date)
        & (transactions_df["Region"].isin(selected_regions))
        & (transactions_df["City"].isin(selected_cities))
        & (transactions_df["Product_Category"].isin(selected_categories))
        & (transactions_df["RFM_Segment"].isin(selected_segments))
        & (transactions_df["Loyalty_Status"].isin(selected_loyalty))
        & (transactions_df["Payment_Method"].isin(selected_payments))
        & (transactions_df["Purchase_Channel"].isin(selected_channels))
    )
    filtered_tx = transactions_df[tx_mask].copy()

    # Calculate prior comparison period of matching length
    duration_days = (end_date - start_date).days + 1
    prior_end = start_date - pd.Timedelta(days=1)
    prior_start = start_date - pd.Timedelta(days=duration_days)

    if prior_start >= min_date:
        prior_mask = (
            (transactions_df["Purchase_Date"].dt.date >= prior_start)
            & (transactions_df["Purchase_Date"].dt.date <= prior_end)
            & (transactions_df["Region"].isin(selected_regions))
            & (transactions_df["City"].isin(selected_cities))
            & (transactions_df["Product_Category"].isin(selected_categories))
            & (transactions_df["RFM_Segment"].isin(selected_segments))
            & (transactions_df["Loyalty_Status"].isin(selected_loyalty))
            & (transactions_df["Payment_Method"].isin(selected_payments))
            & (transactions_df["Purchase_Channel"].isin(selected_channels))
        )
        prior_tx = transactions_df[prior_mask].copy()
        delta_subtext = "vs prior period"
    else:
        # User selected early period; compare recent half vs first half of selected range
        half_days = max(1, duration_days // 2)
        mid_point = start_date + pd.Timedelta(days=half_days)
        early_mask = (
            (transactions_df["Purchase_Date"].dt.date >= start_date)
            & (transactions_df["Purchase_Date"].dt.date < mid_point)
            & (transactions_df["Region"].isin(selected_regions))
            & (transactions_df["City"].isin(selected_cities))
            & (transactions_df["Product_Category"].isin(selected_categories))
            & (transactions_df["RFM_Segment"].isin(selected_segments))
            & (transactions_df["Loyalty_Status"].isin(selected_loyalty))
            & (transactions_df["Payment_Method"].isin(selected_payments))
            & (transactions_df["Purchase_Channel"].isin(selected_channels))
        )
        prior_tx = transactions_df[early_mask].copy()
        delta_subtext = "vs prior half"

    # Synchronize Customer Features with Active Cohort
    active_cust_ids = set(filtered_tx["Customer_ID"].unique())
    filtered_cf = customer_df[customer_df["Customer_ID"].isin(active_cust_ids)].copy()

    # -------------------------------------------------------------
    # Navigation Tabs
    # -------------------------------------------------------------
    tab_overview, tab_rfm, tab_quality = st.tabs(
        ["📈 Executive Overview", "🎯 Segments (RFM)", "🛡️ Data Quality"]
    )

    # =============================================================
    # Tab 1: Executive Overview
    # =============================================================
    with tab_overview:
        # Top Row: 5 KPI Cards
        kpi_metrics = calculate_kpis(
            current_df=filtered_tx,
            prior_df=prior_tx,
            customer_df=customer_df,
        )
        render_kpi_cards(kpi_metrics, subtext=delta_subtext)

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        # Middle Section: Three Columns (Trend, Segment, Category)
        col_m1, col_m2, col_m3 = st.columns([1.1, 0.95, 0.95])

        with col_m1:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            head_col, tog_col = st.columns([2, 1])
            with head_col:
                st.markdown("##### 📈 Revenue Trajectory")
            with tog_col:
                show_mom = st.toggle("MoM Growth %", key="mom_toggle", value=False)
            fig_trend = render_revenue_trend(filtered_tx, show_mom=show_mom)
            st.plotly_chart(fig_trend, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_m2:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("##### 👥 Segment Revenue")
            fig_segment = render_segment_revenue(filtered_tx)
            st.plotly_chart(fig_segment, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_m3:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            head_col, tog_col = st.columns([2, 1])
            with head_col:
                st.markdown("##### 🏷️ Category Performance")
            with tog_col:
                show_margin = st.toggle("Margin %", key="margin_toggle", value=False)
            fig_category = render_category_performance(filtered_tx, show_margin=show_margin)
            st.plotly_chart(fig_category, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Second Middle Row: Three Columns (Regional Heatmap, Top 10, Frequency)
        col_s1, col_s2, col_s3 = st.columns([1, 1, 1])

        with col_s1:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("##### 🗺️ Regional Sales Heatmap")
            fig_heatmap = render_regional_heatmap(filtered_tx)
            st.plotly_chart(fig_heatmap, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_s2:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("##### 🏆 Top 10 Customers")
            fig_top_cust = render_top_customers(filtered_tx, top_n=10)
            st.plotly_chart(fig_top_cust, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_s3:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("##### 🔁 Purchase Frequency")
            fig_freq = render_purchase_frequency(filtered_tx)
            st.plotly_chart(fig_freq, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Third Row: Two Columns (Age Group, Payment Method)
        col_t1, col_t2 = st.columns([1.1, 0.9])

        with col_t1:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("##### 🎂 Customer Age-Group Spend")
            fig_age = render_age_group_analysis(filtered_tx)
            st.plotly_chart(fig_age, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_t2:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("##### 💳 Payment Method Distribution")
            fig_payment = render_payment_donut(filtered_tx)
            st.plotly_chart(fig_payment, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Bottom Section: Dynamic Recommendations & At-Risk Export
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        insights, at_risk_df = compute_insights(filtered_tx, customer_df)
        render_insights_section(insights, at_risk_df)
        st.markdown("</div>", unsafe_allow_html=True)

    # =============================================================
    # Tab 2: Segments (RFM)
    # =============================================================
    with tab_rfm:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_segments_tab(filtered_cf if not filtered_cf.empty else customer_df)
        st.markdown("</div>", unsafe_allow_html=True)

    # =============================================================
    # Tab 3: Data Quality
    # =============================================================
    with tab_quality:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        cleaning_log_path = REPORTS_DIR / "cleaning_log.md"
        render_data_quality_tab(cleaning_log_path)
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
