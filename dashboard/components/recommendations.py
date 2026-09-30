"""
recommendations.py
------------------
Purpose:
    Generates dynamic, automated business recommendations and action cards
    derived directly from the filtered analytics dataset, alongside an exportable
    audit list of at-risk customers.
"""

from typing import Dict, Any, Tuple
from itertools import combinations
from collections import Counter
import pandas as pd
import streamlit as st

try:
    from dashboard.theme import (
        COLORS,
        format_currency,
        render_insight_card_html,
    )
except ModuleNotFoundError:
    from theme import (
        COLORS,
        format_currency,
        render_insight_card_html,
    )


def compute_insights(
    df: pd.DataFrame,
    customer_df: pd.DataFrame,
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Dynamically derive corporate insights and extract at-risk customer records.

    Parameters
    ----------
    df : pd.DataFrame
        Filtered transaction DataFrame.
    customer_df : pd.DataFrame
        Full customer features DataFrame.

    Returns
    -------
    Tuple[Dict[str, Any], pd.DataFrame]
        Dictionary of computed insight text strings and DataFrame of at-risk customers.
    """
    insights = {}

    if df.empty:
        insights["top_segment"] = {"title": "Top Segment", "text": "No data available.", "alert": False, "badge": ""}
        insights["best_region"] = {"title": "Best Region", "text": "No data available.", "alert": False, "badge": ""}
        insights["retention"] = {"title": "Retention Alert", "text": "No data available.", "alert": False, "badge": ""}
        insights["cross_sell"] = {"title": "Cross-Sell Pair", "text": "No data available.", "alert": False, "badge": ""}
        return insights, pd.DataFrame()

    total_revenue = df["Total_Purchase_Value"].sum()

    # 1. Top Segment
    segment_col = "RFM_Segment" if "RFM_Segment" in df.columns else "Customer_Segment"
    seg_rev = df.groupby(segment_col)["Total_Purchase_Value"].sum().sort_values(ascending=False)
    if not seg_rev.empty:
        top_seg_name = seg_rev.index[0]
        top_seg_val = seg_rev.iloc[0]
        top_seg_share = (top_seg_val / total_revenue * 100.0) if total_revenue > 0 else 0.0
        n_seg_cust = df[df[segment_col] == top_seg_name]["Customer_ID"].nunique()
        insights["top_segment"] = {
            "title": "Top Revenue Segment",
            "text": f"<b>{top_seg_name}</b> generates <b>{format_currency(top_seg_val)}</b> ({top_seg_share:.1f}% of filtered revenue) across {n_seg_cust} active customers. Priority: Protect VIP retention with concierge support and tiered loyalty upgrades.",
            "alert": False,
            "badge": f"{top_seg_share:.0f}% Share",
        }
    else:
        insights["top_segment"] = {"title": "Top Segment", "text": "Insufficient segment data.", "alert": False, "badge": ""}

    # 2. Best Region
    reg_rev = df.groupby("Region")["Total_Purchase_Value"].sum().sort_values(ascending=False)
    if not reg_rev.empty:
        top_reg = reg_rev.index[0]
        top_reg_val = reg_rev.iloc[0]
        top_reg_share = (top_reg_val / total_revenue * 100.0) if total_revenue > 0 else 0.0
        top_reg_cat = (
            df[df["Region"] == top_reg]
            .groupby("Product_Category")["Total_Purchase_Value"]
            .sum()
            .idxmax()
        )
        insights["best_region"] = {
            "title": "Geographic Sales Leader",
            "text": f"The <b>{top_reg} Region</b> leads revenue contribution with <b>{format_currency(top_reg_val)}</b> ({top_reg_share:.1f}% share), heavily driven by <b>{top_reg_cat}</b>. Strategy: Expand localized regional inventory and high-intent local promotions.",
            "alert": False,
            "badge": top_reg,
        }
    else:
        insights["best_region"] = {"title": "Best Region", "text": "Insufficient regional data.", "alert": False, "badge": ""}

    # 3. Retention Opportunities & At-Risk Customers
    active_cust_ids = set(df["Customer_ID"].unique())
    matched_cust = customer_df[customer_df["Customer_ID"].isin(active_cust_ids)].copy()

    # Identify overdue or at-risk customers
    is_at_risk_segment = matched_cust["RFM_Segment"].isin(["At Risk", "Can't Lose Them", "Hibernating"])
    is_overdue = (
        (matched_cust["Recency"] > 1.5 * matched_cust["Average_Days_Between_Purchases"])
        & (matched_cust["Purchase_Frequency"] >= 2)
    )
    at_risk_df = matched_cust[is_at_risk_segment | is_overdue].copy()

    if not at_risk_df.empty:
        n_at_risk = len(at_risk_df)
        at_risk_rev = at_risk_df["Total_Revenue"].sum()
        insights["retention"] = {
            "title": "Retention Alert & Churn Risk",
            "text": f"<b>{n_at_risk} customers</b> have exceeded their typical purchase interval or fallen into churn-risk cohorts, representing <b>{format_currency(at_risk_rev)}</b> in historical spend. Action: Deploy automated 'We Miss You' win-back campaigns with 10% discounts.",
            "alert": True,
            "badge": f"{n_at_risk} At-Risk",
        }
    else:
        insights["retention"] = {
            "title": "Retention Status",
            "text": "All active customer cohorts are purchasing within regular cadence windows. Retention health is optimal.",
            "alert": False,
            "badge": "Healthy",
        }

    # 4. Cross-Sell Pair Analysis
    baskets = df.groupby(["Customer_ID", "Purchase_Date"])["Product_Category"].unique()
    pair_counter = Counter()
    for cats in baskets:
        if len(cats) >= 2:
            for pair in combinations(sorted(cats), 2):
                pair_counter[pair] += 1

    if pair_counter:
        top_pair, pair_count = pair_counter.most_common(1)[0]
        insights["cross_sell"] = {
            "title": "Affinity & Cross-Sell Opportunity",
            "text": f"High category co-purchase detected: <b>{top_pair[0]} + {top_pair[1]}</b> purchased simultaneously across {pair_count} multi-item orders. Recommendation: Package both categories as a bundled cross-sell checkout offer.",
            "alert": False,
            "badge": f"{top_pair[0]} & {top_pair[1]}",
        }
    else:
        # Fallback to customer-level favourite categories
        cust_cats = df.groupby("Customer_ID")["Product_Category"].unique()
        for cats in cust_cats:
            if len(cats) >= 2:
                for pair in combinations(sorted(cats), 2):
                    pair_counter[pair] += 1
        if pair_counter:
            top_pair, pair_count = pair_counter.most_common(1)[0]
            insights["cross_sell"] = {
                "title": "Affinity & Cross-Sell Opportunity",
                "text": f"Cross-category affinity: <b>{top_pair[0]} + {top_pair[1]}</b> repeat across {pair_count} customer purchase histories. Action: Test email cross-promotions between these two catalogs.",
                "alert": False,
                "badge": "Bundle",
            }
        else:
            insights["cross_sell"] = {
                "title": "Cross-Sell Opportunity",
                "text": "Cross-sell basket overlap is distributed evenly across all catalog lines.",
                "alert": False,
                "badge": "Standard",
            }

    # Prepare exportable columns for at-risk table
    display_cols = [
        "Customer_ID",
        "Customer_Name",
        "RFM_Segment",
        "Recency",
        "Average_Days_Between_Purchases",
        "Purchase_Frequency",
        "Total_Revenue",
        "Marketing_Action",
    ]
    present_cols = [c for c in display_cols if c in at_risk_df.columns]
    at_risk_export = at_risk_df[present_cols].sort_values("Total_Revenue", ascending=False)

    return insights, at_risk_export


def render_insights_section(
    insights: Dict[str, Any],
    at_risk_df: pd.DataFrame,
) -> None:
    """
    Render 4 insight cards in a 2x2 grid followed by the downloadable at-risk table.
    """
    st.markdown('<div class="section-title">💡 Customer Insights & Strategic Recommendations</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            render_insight_card_html(
                title=insights["top_segment"]["title"],
                content=insights["top_segment"]["text"],
                alert=insights["top_segment"]["alert"],
                badge=insights["top_segment"]["badge"],
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            render_insight_card_html(
                title=insights["retention"]["title"],
                content=insights["retention"]["text"],
                alert=insights["retention"]["alert"],
                badge=insights["retention"]["badge"],
            ),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            render_insight_card_html(
                title=insights["best_region"]["title"],
                content=insights["best_region"]["text"],
                alert=insights["best_region"]["alert"],
                badge=insights["best_region"]["badge"],
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            render_insight_card_html(
                title=insights["cross_sell"]["title"],
                content=insights["cross_sell"]["text"],
                alert=insights["cross_sell"]["alert"],
                badge=insights["cross_sell"]["badge"],
            ),
            unsafe_allow_html=True,
        )

    # At-risk customer table & CSV download
    st.markdown("#### ⚠️ At-Risk Customer Interventions")
    if not at_risk_df.empty:
        st.caption(f"Displaying {len(at_risk_df)} customers exhibiting overdue purchase intervals or churn-risk RFM profiles.")
        
        # Format currency & numbers for presentation
        formatted_table = at_risk_df.copy()
        if "Total_Revenue" in formatted_table.columns:
            formatted_table["Total_Revenue"] = formatted_table["Total_Revenue"].apply(lambda v: f"₹{v:,.2f}")
        if "Recency" in formatted_table.columns:
            formatted_table["Recency"] = formatted_table["Recency"].apply(lambda v: f"{int(v)} days")
        if "Average_Days_Between_Purchases" in formatted_table.columns:
            formatted_table["Average_Days_Between_Purchases"] = formatted_table["Average_Days_Between_Purchases"].apply(lambda v: f"{v:.1f} days")

        st.dataframe(
            formatted_table,
            use_container_width=True,
            hide_index=True,
        )

        csv_bytes = at_risk_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download At-Risk Customer Export (CSV)",
            data=csv_bytes,
            file_name="at_risk_customers_campaign.csv",
            mime="text/csv",
            help="Download targeted customer contact list with personalized marketing interventions.",
        )
    else:
        st.success("No at-risk customers identified in the selected filter segment.")
