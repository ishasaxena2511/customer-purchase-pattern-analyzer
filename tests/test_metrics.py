"""
test_metrics.py
----------------
Purpose:
    Unit test suite validating KPI calculations, dimensional aggregations,
    monthly trends, category margins, retention opportunities, cross-selling lift,
    and Pareto analysis in src/metrics.py.
"""

from datetime import datetime
import pandas as pd
import pytest

from src.metrics import (
    get_headline_kpis,
    get_revenue_by_dimension,
    get_monthly_revenue_trend,
    get_profit_and_margin_by_category,
    get_high_value_customers,
    get_retention_opportunities,
    get_top_product_pairs,
    calculate_pareto_revenue,
)


@pytest.fixture
def sample_metrics_data():
    """Provides a small controlled dataset with transactions and customer features."""
    df_trans = pd.DataFrame([
        {
            "Customer_ID": "C1",
            "Product_Category": "Electronics",
            "Product_Name": "Headphones",
            "Purchase_Date": "2024-01-10",
            "Year": 2024,
            "Month": 1,
            "Month_Name": "January",
            "Quantity_Purchased": 1,
            "Unit_Price": 1000.0,
            "Unit_Cost": 700.0,
            "Discount_Used": 0.0,
            "Total_Purchase_Value": 1000.0,
            "Estimated_Profit": 300.0,
            "Margin_Percentage": 30.0,
        },
        {
            "Customer_ID": "C1",
            "Product_Category": "Electronics",
            "Product_Name": "Power Bank",
            "Purchase_Date": "2024-02-10",
            "Year": 2024,
            "Month": 2,
            "Month_Name": "February",
            "Quantity_Purchased": 2,
            "Unit_Price": 500.0,
            "Unit_Cost": 350.0,
            "Discount_Used": 0.0,
            "Total_Purchase_Value": 1000.0,
            "Estimated_Profit": 300.0,
            "Margin_Percentage": 30.0,
        },
        {
            "Customer_ID": "C2",
            "Product_Category": "Clothing",
            "Product_Name": "T-Shirt",
            "Purchase_Date": "2024-01-15",
            "Year": 2024,
            "Month": 1,
            "Month_Name": "January",
            "Quantity_Purchased": 2,
            "Unit_Price": 500.0,
            "Unit_Cost": 225.0,
            "Discount_Used": 0.0,
            "Total_Purchase_Value": 1000.0,
            "Estimated_Profit": 550.0,
            "Margin_Percentage": 55.0,
        },
        {
            "Customer_ID": "C3",
            "Product_Category": "Clothing",
            "Product_Name": "Headphones",  # Also bought Headphones
            "Purchase_Date": "2024-02-15",
            "Year": 2024,
            "Month": 2,
            "Month_Name": "February",
            "Quantity_Purchased": 1,
            "Unit_Price": 1000.0,
            "Unit_Cost": 700.0,
            "Discount_Used": 0.0,
            "Total_Purchase_Value": 1000.0,
            "Estimated_Profit": 300.0,
            "Margin_Percentage": 30.0,
        },
    ])
    
    df_cust = pd.DataFrame([
        {
            "Customer_ID": "C1",
            "Customer_Name": "Customer One",
            "Order_Count": 2,
            "Total_Revenue": 2000.0,
            "Average_Order_Value": 1000.0,
            "Recency": 60,
            "Average_Days_Between_Purchases": 31.0,
            "Basic_CLV": 6000.0,
            "Customer_Type": "Repeat",
            "Favourite_Category": "Electronics",
        },
        {
            "Customer_ID": "C2",
            "Customer_Name": "Customer Two",
            "Order_Count": 1,
            "Total_Revenue": 1000.0,
            "Average_Order_Value": 1000.0,
            "Recency": 45,
            "Average_Days_Between_Purchases": 0.0,
            "Basic_CLV": 3000.0,
            "Customer_Type": "One-time",
            "Favourite_Category": "Clothing",
        },
        {
            "Customer_ID": "C3",
            "Customer_Name": "Customer Three",
            "Order_Count": 1,
            "Total_Revenue": 1000.0,
            "Average_Order_Value": 1000.0,
            "Recency": 10,
            "Average_Days_Between_Purchases": 0.0,
            "Basic_CLV": 3000.0,
            "Customer_Type": "One-time",
            "Favourite_Category": "Clothing",
        },
    ])
    
    return df_trans, df_cust


def test_headline_kpis(sample_metrics_data):
    """Test 1: Verify headline KPIs (Revenue, Orders, AOV, Repeat Rate, CLV)."""
    df_trans, df_cust = sample_metrics_data
    kpis = get_headline_kpis(df_trans, df_cust)
    
    assert kpis["Total_Revenue"] == 4000.0
    assert kpis["Total_Orders"] == 4
    assert kpis["Total_Customers"] == 3
    assert kpis["Average_Order_Value"] == 1000.0
    assert kpis["Average_Spend_Per_Customer"] == round(4000.0 / 3, 2)
    # 1 of 3 customers is repeat (>=2 orders) -> 33.33%
    assert kpis["Repeat_Purchase_Rate_Pct"] == 33.33
    assert kpis["Average_CLV"] == 4000.0


def test_monthly_revenue_trend(sample_metrics_data):
    """Test 2: Verify MoM growth % and Seasonal Index calculation."""
    df_trans, _ = sample_metrics_data
    monthly = get_monthly_revenue_trend(df_trans)
    
    assert len(monthly) == 2
    # Month 1: 2000, Month 2: 2000 -> MoM is 0.0%
    assert monthly.loc[0, "Revenue"] == 2000.0
    assert monthly.loc[1, "Revenue"] == 2000.0
    assert monthly.loc[1, "MoM_Growth_Pct"] == 0.0
    # Average is 2000 -> Seasonal Index is 100.0
    assert monthly.loc[0, "Seasonal_Index"] == 100.0
    assert monthly.loc[1, "Seasonal_Index"] == 100.0


def test_profit_and_margin_by_category(sample_metrics_data):
    """Test 3: Verify category profit and gross margin %."""
    df_trans, _ = sample_metrics_data
    cat_profit = get_profit_and_margin_by_category(df_trans)
    
    assert len(cat_profit) == 2
    clothing_row = cat_profit[cat_profit["Product_Category"] == "Clothing"].iloc[0]
    # Clothing revenue: 2000.0, Profit: 550 + 300 = 850.0 -> Margin = 850 / 2000 = 42.5%
    assert clothing_row["Total_Revenue"] == 2000.0
    assert clothing_row["Total_Profit"] == 850.0
    assert clothing_row["Gross_Margin_Pct"] == 42.5


def test_retention_opportunities(sample_metrics_data):
    """Test 4: Verify churn-risk identification using 1.5× cadence threshold."""
    _, df_cust = sample_metrics_data
    # C1: gap = 31.0 days, 1.5x = 46.5 days, recency = 60 days -> 60 > 46.5 => AT RISK!
    # C2, C3: One-time buyers -> excluded from repeat-capable cadence
    at_risk = get_retention_opportunities(df_cust, gap_multiplier=1.5)
    
    assert len(at_risk) == 1
    assert at_risk.iloc[0]["Customer_ID"] == "C1"
    assert at_risk.iloc[0]["Days_Overdue"] == 29.0  # 60 - 31.0


def test_pareto_analysis(sample_metrics_data):
    """Test 5: Verify Pareto 80/20 customer distribution."""
    _, df_cust = sample_metrics_data
    # Total revenue = 4000. C1 has 2000 (50%). C1 + C2 = 3000 (75%). C1 + C2 + C3 = 4000 (100%).
    # To reach 80% (3200), we need 3 customers.
    pareto = calculate_pareto_revenue(df_cust, target_pct=0.80)
    
    assert pareto["Total_Customers"] == 3
    assert pareto["Customers_Generating_Target_Revenue"] == 3
    assert pareto["Customer_Percentage_For_Target"] == 100.0


def test_cross_selling_lift(sample_metrics_data):
    """Test 6: Verify product-pair co-purchase, support, and lift."""
    df_trans, _ = sample_metrics_data
    # C1 bought: Headphones + Power Bank
    # C2 bought: T-Shirt
    # C3 bought: Headphones
    pairs = get_top_product_pairs(df_trans, min_support=0.01)
    
    assert len(pairs) == 1
    pair = pairs.iloc[0]
    assert pair["Product_A"] == "Headphones"
    assert pair["Product_B"] == "Power Bank"
    assert pair["Co_Purchase_Count"] == 1
    # Support: 1 / 3 = 33.33%
    assert pair["Support_Pct"] == 33.33
    # P(A) = 2/3, P(B) = 1/3, P(A,B) = 1/3 -> Lift = (1/3) / ((2/3)*(1/3)) = 1.5
    assert pair["Lift"] == 1.5
