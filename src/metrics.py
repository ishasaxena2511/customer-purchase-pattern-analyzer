"""
metrics.py
----------
Purpose:
    Computes modular, tidy analytical metrics and business KPIs from customer transactions
    and customer profiles for retail business intelligence.
    
    Functions return either tidy pandas DataFrames or typed numeric dictionaries/scalars.
    
    Key Metrics Computed:
      - Headline KPIs (Total Revenue, AOV, Spend per Customer, Repeat Rate, Basic CLV)
      - Dimensional Breakdowns (Segment, Category, Region, City, Payment, Channel, Age Group)
      - Monthly Revenue Trends, MoM Growth %, and Seasonal Index
      - Top Customers (Revenue) and Top Products (Units & Revenue)
      - Category Profit & Gross Margin %
      - High-Value Customers (Top 20%), One-Time vs Repeat, and Retention-Opportunity List
      - Cross-Selling: Category Co-Purchase Matrix and Product-Pair Lift/Support
      - Pareto Analysis (80/20 Rule: % of customers generating 80% revenue)
"""

from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


def get_headline_kpis(df_trans: pd.DataFrame, df_cust: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate executive topline financial and customer health KPIs.
    
    Returns:
        Dictionary with Total Revenue, Customers, Orders, AOV, Spend per Customer,
        Repeat Purchase Rate (%), Average Frequency, and Average CLV.
    """
    total_revenue = round(float(df_trans["Total_Purchase_Value"].sum()), 2)
    total_customers = int(df_trans["Customer_ID"].nunique())
    total_orders = int(len(df_trans))
    aov = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0
    avg_spend = round(total_revenue / total_customers, 2) if total_customers > 0 else 0.0
    
    # Repeat rate: % of unique customers with 2 or more orders
    repeat_customers = int((df_cust["Order_Count"] >= 2).sum())
    repeat_rate = round((repeat_customers / total_customers) * 100, 2) if total_customers > 0 else 0.0
    avg_frequency = round(total_orders / total_customers, 2) if total_customers > 0 else 0.0
    avg_clv = round(float(df_cust["Basic_CLV"].mean()), 2) if not df_cust.empty else 0.0
    
    return {
        "Total_Revenue": total_revenue,
        "Total_Customers": total_customers,
        "Total_Orders": total_orders,
        "Average_Order_Value": aov,
        "Average_Spend_Per_Customer": avg_spend,
        "Average_Purchase_Frequency": avg_frequency,
        "Repeat_Purchase_Rate_Pct": repeat_rate,
        "Average_CLV": avg_clv,
    }


def get_revenue_by_dimension(df_trans: pd.DataFrame, dimension_col: str) -> pd.DataFrame:
    """
    Generic aggregator computing tidy revenue and volume metrics by any dimension column.
    
    Returns:
        DataFrame sorted descending by Revenue with Revenue_Share_Pct and AOV.
    """
    if dimension_col not in df_trans.columns:
        raise ValueError(f"Column '{dimension_col}' not found in transactions DataFrame.")
        
    grouped = df_trans.groupby(dimension_col).agg(
        Revenue=("Total_Purchase_Value", "sum"),
        Order_Count=("Total_Purchase_Value", "count"),
        Total_Units=("Quantity_Purchased", "sum"),
    ).reset_index()
    
    total_rev = grouped["Revenue"].sum()
    grouped["Revenue"] = grouped["Revenue"].round(2)
    grouped["Revenue_Share_Pct"] = ((grouped["Revenue"] / total_rev) * 100).round(2)
    grouped["Average_Order_Value"] = (grouped["Revenue"] / grouped["Order_Count"]).round(2)
    
    return grouped.sort_values("Revenue", ascending=False).reset_index(drop=True)


def get_revenue_by_customer_segment(df_trans: pd.DataFrame, df_cust: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Breakdown of revenue, order volume, and AOV by Customer Segment."""
    # If customer features has updated segment labels, merge them
    if df_cust is not None and "Customer_Segment" in df_cust.columns:
        df_merged = df_trans.drop(columns=["Customer_Segment"], errors="ignore").merge(
            df_cust[["Customer_ID", "Customer_Segment"]], on="Customer_ID", how="left"
        )
        return get_revenue_by_dimension(df_merged, "Customer_Segment")
    return get_revenue_by_dimension(df_trans, "Customer_Segment")


def get_revenue_by_category(df_trans: pd.DataFrame) -> pd.DataFrame:
    """Breakdown of revenue, volume, and AOV by Product Category."""
    return get_revenue_by_dimension(df_trans, "Product_Category")


def get_revenue_by_region(df_trans: pd.DataFrame) -> pd.DataFrame:
    """Breakdown of revenue, volume, and AOV by Geographic Region."""
    return get_revenue_by_dimension(df_trans, "Region")


def get_revenue_by_city(df_trans: pd.DataFrame) -> pd.DataFrame:
    """Breakdown of revenue, volume, and AOV by City."""
    return get_revenue_by_dimension(df_trans, "City")


def get_revenue_by_payment_method(df_trans: pd.DataFrame) -> pd.DataFrame:
    """Breakdown of revenue, volume, and AOV by Payment Method."""
    return get_revenue_by_dimension(df_trans, "Payment_Method")


def get_revenue_by_channel(df_trans: pd.DataFrame) -> pd.DataFrame:
    """Breakdown of revenue, volume, and AOV by Purchase Channel."""
    return get_revenue_by_dimension(df_trans, "Purchase_Channel")


def get_revenue_by_age_group(df_trans: pd.DataFrame) -> pd.DataFrame:
    """Breakdown of revenue, volume, and AOV by Demographic Age Group."""
    return get_revenue_by_dimension(df_trans, "Age_Group")


def get_monthly_revenue_trend(df_trans: pd.DataFrame) -> pd.DataFrame:
    """
    Compute monthly revenue time series, Month-over-Month (MoM) growth %,
    and monthly Seasonal Index (100 = annual average baseline).
    """
    monthly = df_trans.groupby(["Year", "Month", "Month_Name"]).agg(
        Revenue=("Total_Purchase_Value", "sum"),
        Order_Count=("Total_Purchase_Value", "count"),
        Total_Units=("Quantity_Purchased", "sum"),
    ).reset_index().sort_values(["Year", "Month"]).reset_index(drop=True)
    
    monthly["Revenue"] = monthly["Revenue"].round(2)
    monthly["Average_Order_Value"] = (monthly["Revenue"] / monthly["Order_Count"]).round(2)
    
    # Month-over-Month Growth %
    monthly["MoM_Growth_Pct"] = (monthly["Revenue"].pct_change() * 100).round(2).fillna(0.0)
    
    # Seasonal Index = (Monthly Revenue / Average Monthly Revenue) * 100
    mean_monthly_revenue = monthly["Revenue"].mean()
    monthly["Seasonal_Index"] = ((monthly["Revenue"] / mean_monthly_revenue) * 100).round(2)
    
    return monthly


def get_top_customers(df_cust: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return top N customers ranked by lifetime revenue generated."""
    cols = [
        "Customer_ID", "Customer_Name", "Total_Revenue", "Order_Count",
        "Average_Order_Value", "City", "Region", "Customer_Type", "Basic_CLV"
    ]
    available_cols = [c for c in cols if c in df_cust.columns]
    return df_cust.sort_values("Total_Revenue", ascending=False).head(n)[available_cols].reset_index(drop=True)


def get_top_products_by_units(df_trans: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return top N products ranked by total physical units sold."""
    prod = df_trans.groupby(["Product_Name", "Product_Category"]).agg(
        Units_Sold=("Quantity_Purchased", "sum"),
        Total_Revenue=("Total_Purchase_Value", "sum"),
        Order_Count=("Quantity_Purchased", "count"),
    ).reset_index()
    
    prod["Total_Revenue"] = prod["Total_Revenue"].round(2)
    prod["Avg_Selling_Price"] = (prod["Total_Revenue"] / prod["Units_Sold"]).round(2)
    return prod.sort_values("Units_Sold", ascending=False).head(n).reset_index(drop=True)


def get_top_products_by_revenue(df_trans: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return top N products ranked by gross revenue generated."""
    prod = df_trans.groupby(["Product_Name", "Product_Category"]).agg(
        Total_Revenue=("Total_Purchase_Value", "sum"),
        Units_Sold=("Quantity_Purchased", "sum"),
        Order_Count=("Quantity_Purchased", "count"),
    ).reset_index()
    
    prod["Total_Revenue"] = prod["Total_Revenue"].round(2)
    prod["Avg_Selling_Price"] = (prod["Total_Revenue"] / prod["Units_Sold"]).round(2)
    return prod.sort_values("Total_Revenue", ascending=False).head(n).reset_index(drop=True)


def get_profit_and_margin_by_category(df_trans: pd.DataFrame) -> pd.DataFrame:
    """
    Compute total financial contribution, COGS, estimated profit, and gross margin %
    by Product Category.
    """
    df = df_trans.copy()
    if "Estimated_Profit" not in df.columns:
        # Fallback if profit wasn't already engineered
        from src.features import CATEGORY_COGS_RATIO
        unit_cost = (df["Unit_Price"] * df["Product_Category"].map(CATEGORY_COGS_RATIO).fillna(0.50)).round(2)
        df["Estimated_Profit"] = (df["Total_Purchase_Value"] - (df["Quantity_Purchased"] * unit_cost)).round(2)
        
    cat_profit = df.groupby("Product_Category").agg(
        Total_Revenue=("Total_Purchase_Value", "sum"),
        Total_Profit=("Estimated_Profit", "sum"),
        Order_Count=("Total_Purchase_Value", "count"),
    ).reset_index()
    
    cat_profit["Total_Revenue"] = cat_profit["Total_Revenue"].round(2)
    cat_profit["Total_Profit"] = cat_profit["Total_Profit"].round(2)
    cat_profit["Total_Cost"] = (cat_profit["Total_Revenue"] - cat_profit["Total_Profit"]).round(2)
    cat_profit["Gross_Margin_Pct"] = ((cat_profit["Total_Profit"] / cat_profit["Total_Revenue"]) * 100).round(2)
    
    return cat_profit.sort_values("Total_Profit", ascending=False).reset_index(drop=True)


def get_high_value_customers(
    df_cust: pd.DataFrame,
    top_pct: float = 0.20,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Identify top quantile of customers by revenue (default top 20%) and calculate
    their collective revenue contribution.
    """
    revenue_cutoff = float(df_cust["Total_Revenue"].quantile(1.0 - top_pct))
    high_value_df = df_cust[df_cust["Total_Revenue"] >= revenue_cutoff].copy().sort_values("Total_Revenue", ascending=False)
    
    total_portfolio_rev = float(df_cust["Total_Revenue"].sum())
    hvc_revenue = float(high_value_df["Total_Revenue"].sum())
    hvc_rev_share = round((hvc_revenue / total_portfolio_rev) * 100, 2) if total_portfolio_rev > 0 else 0.0
    
    stats = {
        "High_Value_Customer_Count": len(high_value_df),
        "Revenue_Cutoff_Threshold": round(revenue_cutoff, 2),
        "High_Value_Revenue": round(hvc_revenue, 2),
        "High_Value_Revenue_Share_Pct": hvc_rev_share,
    }
    return high_value_df.reset_index(drop=True), stats


def get_customer_type_breakdown(df_cust: pd.DataFrame) -> pd.DataFrame:
    """
    Compare One-Time vs Repeat customer cohorts: counts, revenue contribution, and AOV.
    """
    breakdown = df_cust.groupby("Customer_Type").agg(
        Customer_Count=("Customer_ID", "count"),
        Total_Revenue=("Total_Revenue", "sum"),
        Total_Orders=("Order_Count", "sum"),
    ).reset_index()
    
    tot_customers = df_cust["Customer_ID"].count()
    tot_revenue = df_cust["Total_Revenue"].sum()
    
    breakdown["Total_Revenue"] = breakdown["Total_Revenue"].round(2)
    breakdown["Customer_Share_Pct"] = ((breakdown["Customer_Count"] / tot_customers) * 100).round(2)
    breakdown["Revenue_Share_Pct"] = ((breakdown["Total_Revenue"] / tot_revenue) * 100).round(2)
    breakdown["Average_Order_Value"] = (breakdown["Total_Revenue"] / breakdown["Total_Orders"]).round(2)
    breakdown["Average_Customer_Spend"] = (breakdown["Total_Revenue"] / breakdown["Customer_Count"]).round(2)
    
    return breakdown.sort_values("Total_Revenue", ascending=False).reset_index(drop=True)


def get_retention_opportunities(
    df_cust: pd.DataFrame,
    gap_multiplier: float = 1.5,
) -> pd.DataFrame:
    """
    Identify churn-risk repeat customers whose recency (days inactive) has exceeded
    the specified multiplier (default 1.5×) of their historical average purchase gap.
    """
    repeat_df = df_cust[df_cust["Order_Count"] >= 2].copy()
    
    # Calculate overdue days relative to historical cadence
    repeat_df["Expected_Cadence_Days"] = (repeat_df["Average_Days_Between_Purchases"] * gap_multiplier).round(1)
    
    at_risk_mask = repeat_df["Recency"] > repeat_df["Expected_Cadence_Days"]
    opportunities = repeat_df[at_risk_mask].copy()
    
    opportunities["Days_Overdue"] = (opportunities["Recency"] - opportunities["Average_Days_Between_Purchases"]).round(1)
    
    cols = [
        "Customer_ID", "Customer_Name", "Recency", "Average_Days_Between_Purchases",
        "Days_Overdue", "Order_Count", "Total_Revenue", "Basic_CLV", "Favourite_Category"
    ]
    available_cols = [c for c in cols if c in opportunities.columns]
    return opportunities.sort_values("Basic_CLV", ascending=False)[available_cols].reset_index(drop=True)


def get_category_co_purchase_matrix(df_trans: pd.DataFrame) -> pd.DataFrame:
    """
    Compute customer-level category co-purchase matrix:
    Counts how many unique customers purchased from both Category A and Category B.
    """
    # Binary indicator matrix: (Customer_ID x Product_Category)
    cust_cat = df_trans.groupby(["Customer_ID", "Product_Category"]).size().unstack(fill_value=0)
    binary_matrix = (cust_cat > 0).astype(int)
    
    # Matrix dot product gives co-occurrence count
    co_matrix = binary_matrix.T.dot(binary_matrix)
    return co_matrix


def get_top_product_pairs(
    df_trans: pd.DataFrame,
    min_support: float = 0.05,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Perform market basket analysis across customer order history.
    Calculates Support, Confidence, and Lift for pairs of products frequently purchased together.
    
    Formulas:
        Support(A, B) = P(A ∩ B) = Count(A, B) / Total Baskets
        Confidence(A -> B) = P(B | A) = Count(A, B) / Count(A)
        Lift(A, B) = P(A ∩ B) / (P(A) × P(B))
    """
    baskets = df_trans.groupby("Customer_ID")["Product_Name"].apply(lambda s: set(s)).tolist()
    total_baskets = len(baskets)
    
    item_counts: Dict[str, int] = {}
    pair_counts: Dict[Tuple[str, str], int] = {}
    
    for basket in baskets:
        for item in basket:
            item_counts[item] = item_counts.get(item, 0) + 1
        for item1, item2 in combinations(sorted(basket), 2):
            pair = (item1, item2)
            pair_counts[pair] = pair_counts.get(pair, 0) + 1
            
    pairs_list = []
    for (item1, item2), count in pair_counts.items():
        supp_ab = count / total_baskets
        if supp_ab < min_support:
            continue
            
        supp_a = item_counts[item1] / total_baskets
        supp_b = item_counts[item2] / total_baskets
        conf_a_b = (count / item_counts[item1]) * 100
        lift = supp_ab / (supp_a * supp_b)
        
        pairs_list.append({
            "Product_A": item1,
            "Product_B": item2,
            "Co_Purchase_Count": count,
            "Support_Pct": round(supp_ab * 100, 2),
            "Confidence_A_to_B_Pct": round(conf_a_b, 2),
            "Lift": round(lift, 2),
        })
        
    df_pairs = pd.DataFrame(pairs_list)
    if df_pairs.empty:
        return df_pairs
    return df_pairs.sort_values("Lift", ascending=False).head(top_n).reset_index(drop=True)


def calculate_pareto_revenue(
    df_cust: pd.DataFrame,
    target_pct: float = 0.80,
) -> Dict[str, Any]:
    """
    Perform Pareto 80/20 Analysis on customer revenue distribution.
    Determines the exact percentage and count of top customers that generate 80% of total revenue.
    """
    sorted_df = df_cust.sort_values("Total_Revenue", ascending=False).reset_index(drop=True)
    total_rev = float(sorted_df["Total_Revenue"].sum())
    total_cust = len(sorted_df)
    
    sorted_df["Cumulative_Revenue"] = sorted_df["Total_Revenue"].cumsum()
    sorted_df["Cumulative_Rev_Pct"] = sorted_df["Cumulative_Revenue"] / total_rev
    
    # Identify customers contributing to target threshold (e.g. 80%)
    qualifying_indices = sorted_df[sorted_df["Cumulative_Rev_Pct"] >= target_pct].index
    if not qualifying_indices.empty:
        cutoff_rank = qualifying_indices[0] + 1
    else:
        cutoff_rank = total_cust
        
    pct_customers_for_target = round((cutoff_rank / total_cust) * 100, 2)
    
    # Top 20% customers revenue share
    top_20_count = max(1, int(total_cust * 0.20))
    top_20_rev = float(sorted_df.iloc[:top_20_count]["Total_Revenue"].sum())
    top_20_share_pct = round((top_20_rev / total_rev) * 100, 2)
    
    return {
        "Target_Revenue_Percentage": round(target_pct * 100, 1),
        "Total_Customers": total_cust,
        "Customers_Generating_Target_Revenue": cutoff_rank,
        "Customer_Percentage_For_Target": pct_customers_for_target,
        "Top_20_Percent_Customer_Count": top_20_count,
        "Top_20_Percent_Revenue_Share_Pct": top_20_share_pct,
    }


def print_headline_summary(df_trans: pd.DataFrame, df_cust: pd.DataFrame) -> None:
    """
    Print a structured, one-page executive summary of headline business analytics.
    Every metric displayed is dynamically computed from underlying transaction data.
    """
    kpis = get_headline_kpis(df_trans, df_cust)
    pareto = calculate_pareto_revenue(df_cust, target_pct=0.80)
    monthly = get_monthly_revenue_trend(df_trans)
    cat_profit = get_profit_and_margin_by_category(df_trans)
    retention_opps = get_retention_opportunities(df_cust)
    product_pairs = get_top_product_pairs(df_trans, min_support=0.05, top_n=3)
    
    # Peak Month
    peak_month_row = monthly.loc[monthly["Revenue"].idxmax()]
    
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("\n" + "=" * 80)
    print("      CUSTOMER PURCHASE PATTERN ANALYZER -- EXECUTIVE HEADLINE SUMMARY")
    print("=" * 80)
    
    print("\n--- 1. TOPLINE FINANCIAL & CUSTOMER KPIs ---")
    print(f"  * Total Portfolio Revenue:      Rs. {kpis['Total_Revenue']:,.2f}")
    print(f"  * Total Transactions Analyzed:  {kpis['Total_Orders']:,}")
    print(f"  * Active Customer Base:         {kpis['Total_Customers']:,} unique buyers")
    print(f"  * Average Order Value (AOV):    Rs. {kpis['Average_Order_Value']:,.2f}")
    print(f"  * Average Spend Per Customer:   Rs. {kpis['Average_Spend_Per_Customer']:,.2f}")
    print(f"  * Repeat Purchase Rate:         {kpis['Repeat_Purchase_Rate_Pct']:.2f}% of customer base")
    print(f"  * Average Customer CLV:         Rs. {kpis['Average_CLV']:,.2f} (3-Year Baseline Horizon)")
    
    print("\n--- 2. PARETO & REVENUE CONCENTRATION ---")
    print(f"  * Pareto 80/20 Finding:         {pareto['Customers_Generating_Target_Revenue']} of {pareto['Total_Customers']} customers ({pareto['Customer_Percentage_For_Target']}%) drive 80% of revenue.")
    print(f"  * Top 20% Customer Cohort:      Generates {pareto['Top_20_Percent_Revenue_Share_Pct']}% of total company revenue.")
    
    print("\n--- 3. CATEGORY PROFITABILITY & MARGIN LEADERS ---")
    for _, row in cat_profit.iterrows():
        print(f"  * {row['Product_Category']:<24} Revenue: Rs. {row['Total_Revenue']:>10,.2f} | Profit: Rs. {row['Total_Profit']:>9,.2f} | Margin: {row['Gross_Margin_Pct']:>5.2f}%")
        
    print("\n--- 4. SEASONAL VELOCITY & MOMENTUM ---")
    print(f"  * Peak Revenue Month:           {peak_month_row['Month_Name']} {peak_month_row['Year']} (Rs. {peak_month_row['Revenue']:,.2f}, Index: {peak_month_row['Seasonal_Index']:.1f})")
    latest_month = monthly.iloc[-1]
    print(f"  * Latest Month MoM Growth:      {latest_month['Month_Name']} ({latest_month['MoM_Growth_Pct']:+.2f}% vs prior month)")
    
    print("\n--- 5. RETENTION & CROSS-SELLING OPPORTUNITIES ---")
    print(f"  * At-Risk Repeat Customers:     {len(retention_opps)} customers overdue for re-order (>1.5x cadence).")
    if not retention_opps.empty:
        top_risk = retention_opps.iloc[0]
        print(f"    - Priority Contact:           {top_risk['Customer_Name']} ({top_risk['Customer_ID']}) -- CLV: Rs. {top_risk['Basic_CLV']:,.2f} | {top_risk['Days_Overdue']:.0f} days overdue.")
        
    print(f"  * High-Lift Cross-Selling Pairs:")
    for _, pair in product_pairs.iterrows():
        print(f"    - {pair['Product_A']} + {pair['Product_B']}: Lift={pair['Lift']:.2f}x (Co-purchased by {pair['Co_Purchase_Count']} customers, {pair['Support_Pct']}% support)")
        
    print("=" * 80 + "\n")


if __name__ == "__main__":
    trans_path = "data/processed/transactions_features.csv"
    cust_path = "data/processed/customer_features.csv"
    df_t = pd.read_csv(trans_path)
    df_c = pd.read_csv(cust_path)
    print_headline_summary(df_t, df_c)
