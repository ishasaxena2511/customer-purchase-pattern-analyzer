"""
features.py
-----------
Purpose:
    Performs feature engineering on cleaned customer transaction data for retail analytics.
    
    Produces two feature-enriched datasets:
      1. data/processed/transactions_features.csv
         - Calendar & temporal features: Year, Month, Month Name, Quarter, Week,
           Day of Week, Is Weekend, Season, Season/Festive Flag
         - Demographic features: Age Group (18-24, 25-34, 35-44, 45-54, 55+)
         - Financial & profitability features: Discount Amount, Unit Cost (COGS),
           Estimated Profit, and Margin %
           
      2. data/processed/customer_features.csv
         - Aggregated 360-degree customer profile:
           Total Revenue, Order Count, Average Order Value (AOV), Total Quantity,
           First Purchase Date, Last Purchase Date, Recency (days since latest dataset date),
           Purchase Frequency, Average Days Between Purchases, Customer Tenure,
           Favourite Category, Preferred Payment Method, Preferred Channel,
           Discount Usage Rate, Customer Type (One-time vs Repeat), and Basic CLV.

Customer Lifespan & CLV Modeling Assumption:
    -----------------------------------------
    Formula:
        Basic CLV = Average Order Value (AOV) × Purchase Frequency × Customer Lifespan
        
    Assumption:
        In customer analytics and retail e-commerce when longitudinal multi-year data is limited,
        the average customer relationship horizon (lifespan) is assumed to be 3.0 years (36 months),
        aligned with industry empirical retention benchmarks. This projects expected gross customer
        lifetime value based on current purchasing velocity and basket size.
"""

from datetime import datetime
import os
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

# Default retail customer lifespan benchmark in years
DEFAULT_CUSTOMER_LIFESPAN_YEARS: float = 3.0

# Cost of Goods Sold (COGS) ratio by Product Category
# Represents wholesale procurement cost as a fraction of selling price.
# Electronics: ~70% COGS (30% gross margin)
# Clothing: ~45% COGS (55% gross margin)
# Home & Kitchen: ~60% COGS (40% gross margin)
# Beauty & Personal Care: ~35% COGS (65% gross margin)
# Sports & Fitness: ~50% COGS (50% gross margin)
# Books: ~40% COGS (60% gross margin)
CATEGORY_COGS_RATIO: Dict[str, float] = {
    "Electronics": 0.70,
    "Clothing": 0.45,
    "Home & Kitchen": 0.60,
    "Beauty & Personal Care": 0.35,
    "Sports & Fitness": 0.50,
    "Books": 0.40,
}


def calculate_aov(total_revenue: float, order_count: int) -> float:
    """
    Compute Average Order Value (AOV).
    
    Formula:
        AOV = Total Revenue / Order Count
    """
    if order_count <= 0:
        return 0.0
    return round(float(total_revenue) / int(order_count), 2)


def calculate_recency(latest_dataset_date: datetime, last_purchase_date: datetime) -> int:
    """
    Compute Recency in days as of the latest transaction date in the dataset.
    
    Formula:
        Recency = (Dataset Latest Date - Customer Last Purchase Date) in days
    """
    return max(0, int((latest_dataset_date - last_purchase_date).days))


def calculate_basic_clv(
    aov: float,
    purchase_frequency: int,
    customer_lifespan_years: float = DEFAULT_CUSTOMER_LIFESPAN_YEARS,
) -> float:
    """
    Compute basic Customer Lifetime Value (CLV).
    
    Formula:
        CLV = Average Order Value (AOV) × Purchase Frequency × Customer Lifespan
        
    Note:
        Customer Lifespan is parameterized (default = 3.0 years).
    """
    if aov <= 0.0 or purchase_frequency <= 0:
        return 0.0
    return round(float(aov) * int(purchase_frequency) * float(customer_lifespan_years), 2)


def calculate_average_days_between_purchases(
    order_count: int,
    first_purchase_date: datetime,
    last_purchase_date: datetime,
) -> float:
    """
    Compute average inter-purchase interval in days for a customer.
    
    Formula:
        Span = (Last Purchase Date - First Purchase Date) in days
        Average Interval = Span / (Order Count - 1)  [for Order Count > 1]
        Average Interval = 0.0                       [for Order Count == 1]
    """
    if order_count <= 1:
        return 0.0
    span_days = max(0, (last_purchase_date - first_purchase_date).days)
    return round(float(span_days) / float(order_count - 1), 2)


def add_transaction_features(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich transaction records with temporal, demographic, and financial margin metrics.
    
    Output columns added:
      - Year, Month, Month_Name, Quarter, Week, Day_of_Week, Is_Weekend
      - Season, Is_Festive_Season, Season_Festive_Flag
      - Age_Group
      - Discount_Amount, Unit_Cost, Estimated_Profit, Margin_Percentage
    """
    df = df_clean.copy()
    
    # 1. Temporal & Calendar Feature Extraction
    dt_series = pd.to_datetime(df["Purchase_Date"])
    df["Year"] = dt_series.dt.year.astype(int)
    df["Month"] = dt_series.dt.month.astype(int)
    df["Month_Name"] = dt_series.dt.month_name()
    df["Quarter"] = "Q" + dt_series.dt.quarter.astype(str)
    df["Week"] = dt_series.dt.isocalendar().week.astype(int)
    df["Day_of_Week"] = dt_series.dt.day_name()
    df["Is_Weekend"] = dt_series.dt.dayofweek.isin([5, 6])
    
    # Seasonality definition
    # Winter (Dec, Jan, Feb), Spring (Mar, Apr, May), Summer (Jun, Jul, Aug), Autumn (Sep, Oct, Nov)
    season_map = {
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Spring", 4: "Spring", 5: "Spring",
        6: "Summer", 7: "Summer", 8: "Summer",
        9: "Autumn", 10: "Autumn", 11: "Autumn",
    }
    df["Season"] = df["Month"].map(season_map)
    
    # Festive Flag: Q4 Retail Peak (October, November, December - Diwali, Cyber Week, Christmas)
    df["Is_Festive_Season"] = df["Month"].isin([10, 11, 12])
    df["Season_Festive_Flag"] = np.where(df["Is_Festive_Season"], "Festive Peak (Q4)", df["Season"])
    
    # 2. Demographic Age Grouping
    # Standard demographic cohorts: 18-24, 25-34, 35-44, 45-54, 55+
    age_bins = [0, 24, 34, 44, 54, 150]
    age_labels = ["18-24", "25-34", "35-44", "45-54", "55+"]
    df["Age_Group"] = pd.cut(df["Age"], bins=age_bins, labels=age_labels, right=True).astype(str)
    
    # 3. Financial & Margin Feature Engineering
    # Discount Amount = Quantity * Unit_Price * Discount_Used
    df["Discount_Amount"] = (df["Quantity_Purchased"] * df["Unit_Price"] * df["Discount_Used"]).round(2)
    
    # Unit Cost & COGS
    df["Unit_Cost"] = (df["Unit_Price"] * df["Product_Category"].map(CATEGORY_COGS_RATIO).fillna(0.50)).round(2)
    
    # Estimated Profit = Net Revenue (Total_Purchase_Value) - Total COGS (Qty * Unit_Cost)
    total_cogs = df["Quantity_Purchased"] * df["Unit_Cost"]
    df["Estimated_Profit"] = (df["Total_Purchase_Value"] - total_cogs).round(2)
    
    # Margin % = (Estimated Profit / Total Purchase Value) * 100
    df["Margin_Percentage"] = ((df["Estimated_Profit"] / df["Total_Purchase_Value"]) * 100).round(2)
    
    return df


def compute_customer_features(
    df_trans: pd.DataFrame,
    customer_lifespan_years: float = DEFAULT_CUSTOMER_LIFESPAN_YEARS,
) -> pd.DataFrame:
    """
    Construct a consolidated customer-level analytics profile aggregating purchasing behavior,
    RFM metrics, channel preferences, retention status, and basic CLV.
    """
    df = df_trans.copy()
    dt_series = pd.to_datetime(df["Purchase_Date"])
    df["_dt"] = dt_series
    latest_dataset_date = dt_series.max()
    
    customer_records = []
    
    for customer_id, group in df.groupby("Customer_ID"):
        first_row = group.iloc[0]
        customer_name = first_row["Customer_Name"]
        age = first_row["Age"]
        age_group = first_row.get("Age_Group", "Unknown")
        gender = first_row["Gender"]
        city = first_row["City"]
        region = first_row["Region"]
        occupation = first_row["Occupation"]
        loyalty_status = first_row["Loyalty_Status"]
        base_segment = first_row.get("Customer_Segment", "Standard")
        
        # Financial & Order Aggregates
        total_revenue = round(float(group["Total_Purchase_Value"].sum()), 2)
        order_count = int(len(group))
        aov = calculate_aov(total_revenue, order_count)
        total_quantity = int(group["Quantity_Purchased"].sum())
        
        # Date & Recency
        first_dt = group["_dt"].min()
        last_dt = group["_dt"].max()
        recency_days = calculate_recency(latest_dataset_date, last_dt)
        purchase_frequency = order_count
        
        avg_days_between = calculate_average_days_between_purchases(
            order_count=order_count,
            first_purchase_date=first_dt,
            last_purchase_date=last_dt,
        )
        customer_tenure_days = max(0, int((latest_dataset_date - first_dt).days))
        
        # Preferences & Habits
        # Favourite Category (by total spend; fallback to frequency)
        cat_spend = group.groupby("Product_Category")["Total_Purchase_Value"].sum()
        fav_category = str(cat_spend.idxmax())
        
        # Preferred Payment & Channel (Statistical Mode)
        pay_mode = group["Payment_Method"].mode()
        pref_payment = str(pay_mode.iloc[0]) if not pay_mode.empty else "UPI"
        
        chan_mode = group["Purchase_Channel"].mode()
        pref_channel = str(chan_mode.iloc[0]) if not chan_mode.empty else "Online"
        
        # Discount Usage Rate (% of orders utilizing a discount)
        disc_usage_rate = round(float((group["Discount_Used"] > 0).mean() * 100), 2)
        
        # Customer Type
        customer_type = "Repeat" if order_count > 1 else "One-time"
        
        # Customer Lifetime Value
        basic_clv = calculate_basic_clv(
            aov=aov,
            purchase_frequency=purchase_frequency,
            customer_lifespan_years=customer_lifespan_years,
        )
        
        customer_records.append({
            "Customer_ID": customer_id,
            "Customer_Name": customer_name,
            "Age": age,
            "Age_Group": age_group,
            "Gender": gender,
            "City": city,
            "Region": region,
            "Occupation": occupation,
            "Loyalty_Status": loyalty_status,
            "Customer_Segment": base_segment,
            "Total_Revenue": total_revenue,
            "Order_Count": order_count,
            "Average_Order_Value": aov,
            "Total_Quantity": total_quantity,
            "First_Purchase_Date": first_dt.strftime("%Y-%m-%d"),
            "Last_Purchase_Date": last_dt.strftime("%Y-%m-%d"),
            "Recency": recency_days,
            "Purchase_Frequency": purchase_frequency,
            "Average_Days_Between_Purchases": avg_days_between,
            "Customer_Tenure": customer_tenure_days,
            "Favourite_Category": fav_category,
            "Preferred_Payment_Method": pref_payment,
            "Preferred_Channel": pref_channel,
            "Discount_Usage_Rate": disc_usage_rate,
            "Customer_Type": customer_type,
            "Basic_CLV": basic_clv,
        })
        
    df_customers = pd.DataFrame(customer_records)
    return df_customers


def engineer_features(
    clean_data_path: str = "data/processed/customer_purchases_clean.csv",
    output_trans_path: str = "data/processed/transactions_features.csv",
    output_cust_path: str = "data/processed/customer_features.csv",
    customer_lifespan_years: float = DEFAULT_CUSTOMER_LIFESPAN_YEARS,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main execution pipeline for feature engineering.
    
    Reads cleaned transactions, creates enriched transaction features,
    computes customer-level RFM and CLV metrics, and persists both datasets.
    
    Returns:
        Tuple of (transactions_features DataFrame, customer_features DataFrame).
    """
    print(f"Loading cleaned transactions from: {clean_data_path}")
    if not os.path.exists(clean_data_path):
        raise FileNotFoundError(f"Cleaned dataset not found at {clean_data_path}. Run clean_data.py first.")
        
    df_clean = pd.read_csv(clean_data_path)
    
    # 1. Generate enriched transaction features
    print("Engineering transaction-level calendar, profit, and demographic features...")
    df_trans_features = add_transaction_features(df_clean)
    
    # 2. Generate aggregated customer profile features
    print(f"Engineering customer-level RFM, behavior, and CLV features (Lifespan={customer_lifespan_years} yrs)...")
    df_cust_features = compute_customer_features(df_trans_features, customer_lifespan_years)
    
    # Persist outputs
    os.makedirs(os.path.dirname(output_trans_path), exist_ok=True)
    os.makedirs(os.path.dirname(output_cust_path), exist_ok=True)
    
    df_trans_features.to_csv(output_trans_path, index=False)
    df_cust_features.to_csv(output_cust_path, index=False)
    
    print(f"Saved transactions features: {output_trans_path} ({df_trans_features.shape[0]} rows, {df_trans_features.shape[1]} cols)")
    print(f"Saved customer features: {output_cust_path} ({df_cust_features.shape[0]} customers, {df_cust_features.shape[1]} cols)")
    
    return df_trans_features, df_cust_features


if __name__ == "__main__":
    engineer_features()
