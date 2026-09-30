"""
segments_tab.py
---------------
Purpose:
    Renders Tab 2: "Segments (RFM)" displaying the RFM segment summary table,
    K-Means cluster profile, interactive scatter visualization, and marketing action playbook.
"""

import pandas as pd
import streamlit as st

from dashboard.components.charts import render_rfm_scatter
from dashboard.theme import format_currency


def render_segments_tab(customer_df: pd.DataFrame) -> None:
    """
    Render RFM segment distribution, K-Means profiles, and strategic action guide.
    """
    st.markdown('<div class="section-title">🎯 Customer Segmentation & Cluster Profiling</div>', unsafe_allow_html=True)
    st.markdown(
        """
        Customer segmentation combines **Rule-based RFM Scoring** (1–5 quintiles) and **Unsupervised K-Means Clustering** ($k=4$)
        to identify high-value cohorts and re-engagement opportunities.
        """
    )

    if customer_df.empty or "RFM_Segment" not in customer_df.columns:
        st.warning("Customer segmentation data is unavailable.")
        return

    # 1. RFM Segment Summary Table
    st.markdown("#### 📊 RFM Segment Performance Summary")
    total_cust = len(customer_df)
    total_rev = customer_df["Total_Revenue"].sum()

    rfm_summary = (
        customer_df.groupby("RFM_Segment")
        .agg(
            Customers=("Customer_ID", "count"),
            Revenue=("Total_Revenue", "sum"),
            Avg_Recency=("Recency", "mean"),
            Avg_Frequency=("Purchase_Frequency", "mean"),
            Avg_Order_Value=("Average_Order_Value", "mean"),
            Marketing_Action=("Marketing_Action", "first"),
        )
        .reset_index()
    )

    rfm_summary["Customer_Share"] = (rfm_summary["Customers"] / total_cust * 100.0).apply(lambda v: f"{v:.1f}%")
    rfm_summary["Revenue_Share"] = (rfm_summary["Revenue"] / total_rev * 100.0).apply(lambda v: f"{v:.1f}%")
    rfm_summary["Revenue_Formatted"] = rfm_summary["Revenue"].apply(lambda v: f"₹{v:,.2f}")
    rfm_summary["Avg_Recency"] = rfm_summary["Avg_Recency"].apply(lambda v: f"{v:.0f} d")
    rfm_summary["Avg_Frequency"] = rfm_summary["Avg_Frequency"].apply(lambda v: f"{v:.1f} orders")
    rfm_summary["Avg_Order_Value"] = rfm_summary["Avg_Order_Value"].apply(lambda v: f"₹{v:,.2f}")

    display_rfm = rfm_summary[
        [
            "RFM_Segment",
            "Customers",
            "Customer_Share",
            "Revenue_Formatted",
            "Revenue_Share",
            "Avg_Recency",
            "Avg_Frequency",
            "Avg_Order_Value",
            "Marketing_Action",
        ]
    ].rename(
        columns={
            "RFM_Segment": "Segment",
            "Revenue_Formatted": "Total Revenue",
            "Customer_Share": "Cust %",
            "Revenue_Share": "Rev %",
            "Avg_Recency": "Avg Recency",
            "Avg_Frequency": "Avg Freq",
            "Avg_Order_Value": "AOV",
            "Marketing_Action": "Strategic Action",
        }
    )

    st.dataframe(display_rfm, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 2. Interactive RFM Scatter Chart
    col_scatter, col_cluster = st.columns([3, 2])

    with col_scatter:
        fig_scatter = render_rfm_scatter(customer_df)
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_cluster:
        st.markdown("#### 🤖 K-Means Cluster Profiles ($k=4$)")
        if "Cluster_Name" in customer_df.columns:
            cluster_profile = (
                customer_df.groupby(["Cluster", "Cluster_Name"])
                .agg(
                    Size=("Customer_ID", "count"),
                    Avg_Revenue=("Total_Revenue", "mean"),
                    Avg_Recency=("Recency", "mean"),
                    Avg_Frequency=("Purchase_Frequency", "mean"),
                )
                .reset_index()
                .sort_values("Avg_Revenue", ascending=False)
            )

            cluster_profile["Avg_Revenue"] = cluster_profile["Avg_Revenue"].apply(lambda v: f"₹{v:,.2f}")
            cluster_profile["Avg_Recency"] = cluster_profile["Avg_Recency"].apply(lambda v: f"{v:.0f} days")
            cluster_profile["Avg_Frequency"] = cluster_profile["Avg_Frequency"].apply(lambda v: f"{v:.1f} orders")

            st.dataframe(
                cluster_profile[["Cluster_Name", "Size", "Avg_Revenue", "Avg_Recency", "Avg_Frequency"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("K-Means cluster labels not present in customer features.")

    st.markdown("---")

    # 3. Action Matrix Accordion
    st.markdown("#### 📋 Segment Marketing Activation Playbook")
    playbook = {
        "Champions": "VIP concierge, early access to new product drops, personalized high-tier loyalty gifts, referral incentives.",
        "Loyal Customers": "Cross-sell premium accessories, personalized recommendations, loyalty point tier accelerators.",
        "Potential Loyalists": "Offer limited-time category bundles, incentive for second/third purchase, welcome onboarding sequence.",
        "New Customers": "Onboarding check-in, product usage guides, follow-up discount code for next transaction within 30 days.",
        "At Risk": "Time-sensitive 'We miss you' re-engagement campaign with 15% discount, survey for feedback on product experience.",
        "Can't Lose Them": "High-touch outreach, substantial win-back voucher, survey on product quality or service friction.",
        "Hibernating": "Low-cost programmatic email/SMS campaigns during seasonal mega-sales (Diwali / New Year), catalog clearance.",
    }

    cols = st.columns(2)
    for idx, (seg, action) in enumerate(playbook.items()):
        target_col = cols[idx % 2]
        with target_col:
            with st.expander(f"📌 {seg} Playbook"):
                st.write(action)
