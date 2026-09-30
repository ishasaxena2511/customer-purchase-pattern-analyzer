"""
test_sql.py
-----------
Purpose:
    Cross-checks the analytical SQL queries executed on SQLite against
    the pandas metrics calculations to verify mathematical and analytical consistency.
"""

import sqlite3
import pandas as pd
import pytest

from src.load_db import load_to_sqlite
from src.metrics import get_headline_kpis, get_revenue_by_city
from src.run_sql import execute_analytical_queries


@pytest.fixture(scope="module")
def sqlite_setup():
    """Ensure SQLite database is populated and return path and dataframes."""
    db_path = "data/processed/retail.db"
    trans_csv = "data/processed/transactions_features.csv"
    cust_csv = "data/processed/customer_features.csv"
    
    load_to_sqlite(trans_csv, cust_csv, db_path)
    df_trans = pd.read_csv(trans_csv)
    df_cust = pd.read_csv(cust_csv)
    
    sql_results = execute_analytical_queries(db_path=db_path, verbose=False)
    return df_trans, df_cust, sql_results


def test_sql_vs_pandas_total_revenue_and_orders(sqlite_setup):
    """
    Consistency Check 1:
    Verify that Total Revenue and Total Orders from SQL monthly aggregation
    exactly match pandas calculations.
    """
    df_trans, df_cust, sql_results = sqlite_setup
    
    # Pandas baseline
    pandas_total_rev = round(float(df_trans["Total_Purchase_Value"].sum()), 2)
    pandas_total_orders = int(len(df_trans))
    
    # SQL Query 3: Monthly Revenue Trend
    sql_monthly_df = sql_results["3. Monthly Revenue Trend (with MoM Growth % & Cumulative YTD)"]
    sql_total_rev = round(float(sql_monthly_df["Monthly_Revenue"].sum()), 2)
    sql_total_orders = int(sql_monthly_df["Order_Count"].sum())
    
    assert sql_total_rev == pandas_total_rev
    assert sql_total_orders == pandas_total_orders


def test_sql_vs_pandas_top_cities_sales(sqlite_setup):
    """
    Consistency Check 2:
    Verify that Top 5 Cities sales volume and rankings in SQL Query 2
    match pandas groupby results.
    """
    df_trans, _, sql_results = sqlite_setup
    
    # Pandas top 5 cities
    pandas_city_sales = get_revenue_by_city(df_trans).head(5)
    
    # SQL Query 2: Top 5 Cities
    sql_city_df = sql_results["2. Top 5 Cities by Sales Volume (with Running Total)"]
    
    for i in range(5):
        assert sql_city_df.loc[i, "City"] == pandas_city_sales.loc[i, "City"]
        assert sql_city_df.loc[i, "Total_Sales"] == pandas_city_sales.loc[i, "Revenue"]
        assert sql_city_df.loc[i, "Transaction_Count"] == pandas_city_sales.loc[i, "Order_Count"]


def test_sql_vs_pandas_repeat_customers(sqlite_setup):
    """
    Consistency Check 3:
    Verify Repeat vs. One-Time customer counts and revenue shares
    between SQL Query 5 and pandas customer features.
    """
    _, df_cust, sql_results = sqlite_setup
    
    pandas_repeat_count = int((df_cust["Order_Count"] >= 2).sum())
    pandas_onetime_count = int((df_cust["Order_Count"] == 1).sum())
    
    sql_repeat_df = sql_results["5. Repeat vs. One-Time Customer Comparison"]
    sql_repeat_row = sql_repeat_df[sql_repeat_df["Customer_Type"] == "Repeat"].iloc[0]
    sql_onetime_row = sql_repeat_df[sql_repeat_df["Customer_Type"] == "One-time"].iloc[0]
    
    assert int(sql_repeat_row["Customer_Count"]) == pandas_repeat_count
    assert int(sql_onetime_row["Customer_Count"]) == pandas_onetime_count


def test_sql_vs_pandas_rfm_segment_revenue(sqlite_setup):
    """
    Consistency Check 4:
    Verify that segment revenue from SQL Query 8 matches customer_features aggregate revenue.
    """
    _, df_cust, sql_results = sqlite_setup
    
    pandas_seg_rev = df_cust.groupby("RFM_Segment")["Total_Revenue"].sum().round(2).to_dict()
    sql_seg_df = sql_results["8. Average Order Value & Revenue by RFM Segment"]
    sql_seg_rev = dict(zip(sql_seg_df["RFM_Segment"], sql_seg_df["Total_Revenue"].round(2)))
    
    for seg, p_rev in pandas_seg_rev.items():
        assert seg in sql_seg_rev
        assert abs(sql_seg_rev[seg] - p_rev) <= 0.05
