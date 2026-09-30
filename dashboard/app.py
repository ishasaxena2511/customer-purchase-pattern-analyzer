"""
app.py
------
Purpose:
    Main entry point for the Streamlit Executive Business Intelligence Dashboard.
    Visualizes KPIs, sales trends, RFM customer segments, geographic distribution,
    product performance, and automated dynamic business recommendations.
"""

import streamlit as st


def main() -> None:
    st.set_page_config(
        page_title="Customer Purchase Pattern Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("📊 Customer Purchase Pattern Analyzer")
    st.info("Dashboard initialized. Run pipeline to populate analytics data.")


if __name__ == "__main__":
    main()
