"""
test_features.py
----------------
Purpose:
    Unit test suite validating feature engineering calculations:
    Average Order Value (AOV), Recency, Customer Lifetime Value (CLV),
    inter-purchase interval, and full customer aggregation on a tiny hand-made DataFrame.
"""

from datetime import datetime
import pandas as pd
import pytest

from src.features import (
    calculate_aov,
    calculate_recency,
    calculate_basic_clv,
    calculate_average_days_between_purchases,
    add_transaction_features,
    compute_customer_features,
)


def test_calculate_aov():
    """Verify Average Order Value formula: AOV = Revenue / Count."""
    assert calculate_aov(1000.0, 4) == 250.0
    assert calculate_aov(450.50, 2) == 225.25
    assert calculate_aov(0.0, 0) == 0.0


def test_calculate_recency():
    """Verify Recency formula: Days from last purchase to dataset latest date."""
    latest_dt = datetime(2024, 12, 31)
    last_dt = datetime(2024, 12, 21)
    assert calculate_recency(latest_dt, last_dt) == 10
    
    # Same day purchase -> 0 days
    assert calculate_recency(latest_dt, latest_dt) == 0


def test_calculate_basic_clv():
    """Verify basic CLV formula: AOV × Purchase Frequency × Lifespan (default 3.0 yrs)."""
    # AOV = 200, Frequency = 4 orders, Lifespan = 3.0 years -> 200 * 4 * 3.0 = 2400.0
    assert calculate_basic_clv(aov=200.0, purchase_frequency=4, customer_lifespan_years=3.0) == 2400.0
    # Zero orders or revenue -> 0.0
    assert calculate_basic_clv(aov=0.0, purchase_frequency=0) == 0.0


def test_calculate_average_days_between_purchases():
    """Verify inter-purchase interval calculation for repeat vs one-time customers."""
    first_dt = datetime(2024, 1, 1)
    last_dt = datetime(2024, 1, 21)
    
    # 3 orders over 20 days -> 20 / (3 - 1) = 10.0 days
    assert calculate_average_days_between_purchases(3, first_dt, last_dt) == 10.0
    # Single order customer -> 0.0 days
    assert calculate_average_days_between_purchases(1, first_dt, last_dt) == 0.0


@pytest.fixture
def tiny_handmade_dataset() -> pd.DataFrame:
    """
    Controlled hand-made DataFrame with 2 customers:
      - C001: Repeat buyer (2 orders, span 10 days)
      - C002: One-time buyer (1 order)
    """
    return pd.DataFrame([
        {
            "Customer_ID": "C001",
            "Customer_Name": "Priya Sharma",
            "Age": 22,
            "Gender": "Female",
            "City": "Delhi",
            "Region": "North",
            "Occupation": "Student",
            "Product_Category": "Electronics",
            "Product_Name": "Wireless Headphones",
            "Purchase_Date": "2024-01-01",
            "Quantity_Purchased": 1,
            "Unit_Price": 100.0,
            "Total_Purchase_Value": 100.0,
            "Payment_Method": "UPI",
            "Purchase_Channel": "Online",
            "Customer_Segment": "Standard",
            "Loyalty_Status": "Gold",
            "Discount_Used": 0.0,
            "Purchase_Frequency": 2,
            "Last_Purchase_Date": "2024-01-11",
            "Is_Outlier": False,
        },
        {
            "Customer_ID": "C001",
            "Customer_Name": "Priya Sharma",
            "Age": 22,
            "Gender": "Female",
            "City": "Delhi",
            "Region": "North",
            "Occupation": "Student",
            "Product_Category": "Electronics",
            "Product_Name": "Smartwatch",
            "Purchase_Date": "2024-01-11",
            "Quantity_Purchased": 3,
            "Unit_Price": 100.0,
            "Total_Purchase_Value": 300.0,
            "Payment_Method": "UPI",
            "Purchase_Channel": "Online",
            "Customer_Segment": "Standard",
            "Loyalty_Status": "Gold",
            "Discount_Used": 0.0,
            "Purchase_Frequency": 2,
            "Last_Purchase_Date": "2024-01-11",
            "Is_Outlier": False,
        },
        {
            "Customer_ID": "C002",
            "Customer_Name": "Rohan Gupta",
            "Age": 48,
            "Gender": "Male",
            "City": "Mumbai",
            "Region": "West",
            "Occupation": "Manager",
            "Product_Category": "Clothing",
            "Product_Name": "Casual Jacket",
            "Purchase_Date": "2024-01-15",
            "Quantity_Purchased": 2,
            "Unit_Price": 250.0,
            "Total_Purchase_Value": 500.0,
            "Payment_Method": "Credit Card",
            "Purchase_Channel": "In-Store",
            "Customer_Segment": "Standard",
            "Loyalty_Status": "Regular",
            "Discount_Used": 0.0,
            "Purchase_Frequency": 1,
            "Last_Purchase_Date": "2024-01-15",
            "Is_Outlier": False,
        },
    ])


def test_customer_features_aggregation(tiny_handmade_dataset: pd.DataFrame):
    """
    Test customer profile feature aggregation on tiny hand-made DataFrame.
    Dataset latest date is 2024-01-15.
    """
    df_trans = add_transaction_features(tiny_handmade_dataset)
    df_cust = compute_customer_features(df_trans, customer_lifespan_years=3.0)
    
    assert len(df_cust) == 2
    
    # 1. Customer C001 (Repeat Buyer)
    c1 = df_cust[df_cust["Customer_ID"] == "C001"].iloc[0]
    assert c1["Total_Revenue"] == 400.0
    assert c1["Order_Count"] == 2
    assert c1["Average_Order_Value"] == 200.0
    assert c1["Total_Quantity"] == 4
    assert c1["First_Purchase_Date"] == "2024-01-01"
    assert c1["Last_Purchase_Date"] == "2024-01-11"
    # Latest date in dataset is 2024-01-15 -> Recency = 15 - 11 = 4 days
    assert c1["Recency"] == 4
    # Span = 10 days / (2 - 1) = 10.0 days
    assert c1["Average_Days_Between_Purchases"] == 10.0
    # Customer Tenure = 15 - 1 = 14 days
    assert c1["Customer_Tenure"] == 14
    assert c1["Customer_Type"] == "Repeat"
    assert c1["Age_Group"] == "18-24"
    assert c1["Favourite_Category"] == "Electronics"
    # Basic CLV = 200.0 * 2 * 3.0 = 1200.0
    assert c1["Basic_CLV"] == 1200.0
    
    # 2. Customer C002 (One-time Buyer)
    c2 = df_cust[df_cust["Customer_ID"] == "C002"].iloc[0]
    assert c2["Total_Revenue"] == 500.0
    assert c2["Order_Count"] == 1
    assert c2["Average_Order_Value"] == 500.0
    assert c2["Total_Quantity"] == 2
    assert c2["First_Purchase_Date"] == "2024-01-15"
    assert c2["Last_Purchase_Date"] == "2024-01-15"
    # Latest date is 2024-01-15 -> Recency = 0 days
    assert c2["Recency"] == 0
    assert c2["Average_Days_Between_Purchases"] == 0.0
    assert c2["Customer_Tenure"] == 0
    assert c2["Customer_Type"] == "One-time"
    assert c2["Age_Group"] == "45-54"
    # Basic CLV = 500.0 * 1 * 3.0 = 1500.0
    assert c2["Basic_CLV"] == 1500.0
