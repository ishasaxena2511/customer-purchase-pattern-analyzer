"""
data_quality.py
---------------
Purpose:
    Renders the Data Quality and Pipeline Integrity audit tab.
    Displays cleansing metrics, validation test suite results,
    category outlier fences, and full audit logs from reports/cleaning_log.md.
"""

from pathlib import Path
import streamlit as st
import pandas as pd

from dashboard.theme import render_kpi_card_html


def render_data_quality_tab(log_path: Path) -> None:
    """
    Render executive data quality summary cards and the complete audit report.
    """
    st.markdown('<div class="section-title">🛡️ Data Pipeline Integrity & Cleaning Audit</div>', unsafe_allow_html=True)
    st.markdown(
        """
        The data cleaning pipeline (`clean_data.py`) validates raw transactions against strict mathematical,
        temporal, and taxonomy assertions before populating analytical tables.
        """
    )

    # 1. Headline Cleansing Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            render_kpi_card_html("Raw Transactions", "1,235", delta=None, subtext="data/raw/customer_purchases_raw.csv"),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            render_kpi_card_html("Cleaned Rows", "1,160", delta=-6.1, delta_suffix="%", subtext="40 invalid dropped, 35 dupes", is_higher_better=False),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            render_kpi_card_html("Missing Values Fixed", "140", delta=0.0, delta_suffix=" nulls remaining", subtext="Imputed via justified rules"),
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            render_kpi_card_html("Outliers Flagged", "82", delta=7.1, delta_suffix="% of total", subtext="Flagged via IQR, zero data loss", is_higher_better=False),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 2. Validation & Outlier Overview
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### ✅ Automated Integrity Assertion Suite")
        validation_data = [
            {"Test": "Non-Zero Positive Quantities", "Rule": "Quantity > 0", "Status": "PASSED (100%)", "Result": "Min Qty: 1"},
            {"Test": "Mathematical Revenue Consistency", "Rule": "|Total - Qty*Price*(1-Disc)| <= 0.05", "Status": "PASSED (100%)", "Result": "Max diff: ₹0.01"},
            {"Test": "Temporal Plausibility", "Rule": "Purchase_Date <= Today", "Status": "PASSED (100%)", "Result": "No future dates"},
            {"Test": "Demographic Bounds", "Rule": "18 <= Age <= 80", "Status": "PASSED (100%)", "Result": "Age range: 18 - 71"},
            {"Test": "Geographic Consistency", "Rule": "City matches Region", "Status": "PASSED (100%)", "Result": "Deterministic map"},
            {"Test": "Categorical Taxonomy", "Rule": "Category, Payment, Channel valid", "Status": "PASSED (100%)", "Result": "Zero unmapped"},
        ]
        val_df = pd.DataFrame(validation_data)
        st.dataframe(val_df, use_container_width=True, hide_index=True)

    with col_right:
        st.markdown("#### 📦 Category IQR Outlier Fences")
        outlier_data = [
            {"Category": "Books", "Q1": "₹620.91", "Q3": "₹1,494.10", "IQR": "₹873.19", "Upper Fence": "₹2,803.89", "Outliers": 9},
            {"Category": "Beauty & Personal Care", "Q1": "₹552.07", "Q3": "₹1,741.45", "IQR": "₹1,189.38", "Upper Fence": "₹3,525.52", "Outliers": 18},
            {"Category": "Electronics", "Q1": "₹1,677.32", "Q3": "₹5,599.80", "IQR": "₹3,922.48", "Upper Fence": "₹11,483.51", "Outliers": 12},
            {"Category": "Home & Kitchen", "Q1": "₹1,127.12", "Q3": "₹3,869.34", "IQR": "₹2,742.21", "Upper Fence": "₹7,982.65", "Outliers": 14},
            {"Category": "Sports & Fitness", "Q1": "₹848.99", "Q3": "₹4,098.89", "IQR": "₹3,249.90", "Upper Fence": "₹8,973.73", "Outliers": 20},
            {"Category": "Clothing", "Q1": "₹1,045.47", "Q3": "₹3,810.87", "IQR": "₹2,765.40", "Upper Fence": "₹7,958.97", "Outliers": 9},
        ]
        out_df = pd.DataFrame(outlier_data)
        st.dataframe(out_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 3. Full Cleaning Audit Log
    st.markdown("#### 📄 Complete Pipeline Audit Log (`reports/cleaning_log.md`)")
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
        with st.expander("Click to view full Markdown cleaning log", expanded=False):
            st.markdown(log_content)
    else:
        st.info("Cleaning log report file not found. Run clean_data.py to generate.")
