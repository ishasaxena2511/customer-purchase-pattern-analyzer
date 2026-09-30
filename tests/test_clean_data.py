"""
test_clean_data.py
------------------
Purpose:
    Automated pytest test suite verifying the functionality and integrity
    of each data cleaning step in src/clean_data.py.
"""

import os
import numpy as np
import pandas as pd
import pytest

from src.clean_data import (
    CleaningAudit,
    remove_duplicates,
    standardize_customer_names,
    parse_and_standardize_dates,
    correct_category_typos,
    handle_missing_values,
    detect_and_flag_outliers,
    validate_cleaned_data,
    recompute_customer_aggregates,
    clean_dataset,
    VALID_CATEGORIES,
)


@pytest.fixture
def sample_dirty_data() -> pd.DataFrame:
    """Fixture providing a controlled dirty sample DataFrame."""
    return pd.DataFrame([
        {
            "Customer_ID": "C0001",
            "Customer_Name": "  john   doe ",
            "Age": 28,
            "Gender": "Male",
            "City": "Delhi",
            "Region": "North",
            "Occupation": "Software Engineer",
            "Product_Category": "Electrnics",
            "Product_Name": "Wireless Headphones",
            "Purchase_Date": "15/03/2024",
            "Quantity_Purchased": 2,
            "Unit_Price": 1500.0,
            "Total_Purchase_Value": 2700.0,
            "Payment_Method": "UPI",
            "Purchase_Channel": "Online",
            "Customer_Segment": "Standard",
            "Loyalty_Status": "Gold",
            "Discount_Used": 0.10,
            "Purchase_Frequency": 1,
            "Last_Purchase_Date": "15/03/2024",
        },
        {
            "Customer_ID": "C0001",
            "Customer_Name": "john doe",
            "Age": 28,
            "Gender": "Male",
            "City": "Delhi",
            "Region": "North",
            "Occupation": "Software Engineer",
            "Product_Category": "Electronics",
            "Product_Name": "Smartwatch",
            "Purchase_Date": "2024-06-20",
            "Quantity_Purchased": 1,
            "Unit_Price": 3000.0,
            "Total_Purchase_Value": 3000.0,
            "Payment_Method": "UPI",
            "Purchase_Channel": "Online",
            "Customer_Segment": "Standard",
            "Loyalty_Status": "Gold",
            "Discount_Used": 0.0,
            "Purchase_Frequency": 1,
            "Last_Purchase_Date": "15/03/2024",
        },
        # Exact duplicate of row 0
        {
            "Customer_ID": "C0001",
            "Customer_Name": "  john   doe ",
            "Age": 28,
            "Gender": "Male",
            "City": "Delhi",
            "Region": "North",
            "Occupation": "Software Engineer",
            "Product_Category": "Electrnics",
            "Product_Name": "Wireless Headphones",
            "Purchase_Date": "15/03/2024",
            "Quantity_Purchased": 2,
            "Unit_Price": 1500.0,
            "Total_Purchase_Value": 2700.0,
            "Payment_Method": "UPI",
            "Purchase_Channel": "Online",
            "Customer_Segment": "Standard",
            "Loyalty_Status": "Gold",
            "Discount_Used": 0.10,
            "Purchase_Frequency": 1,
            "Last_Purchase_Date": "15/03/2024",
        },
    ])


def test_remove_duplicates(sample_dirty_data: pd.DataFrame):
    audit = CleaningAudit()
    assert len(sample_dirty_data) == 3
    df_deduped = remove_duplicates(sample_dirty_data, audit)
    assert len(df_deduped) == 2
    assert audit.step_logs[0]["rows_dropped"] == 1


def test_standardize_customer_names(sample_dirty_data: pd.DataFrame):
    audit = CleaningAudit()
    df_clean_names = standardize_customer_names(sample_dirty_data, audit)
    assert (df_clean_names["Customer_Name"] == "John Doe").all()


def test_parse_and_standardize_dates():
    audit = CleaningAudit()
    df_dates = pd.DataFrame({
        "Purchase_Date": ["15/03/2024", "2024-05-10", "12-25-2024", "INVALID_DATE"]
    })
    res = parse_and_standardize_dates(df_dates, audit)
    assert res.loc[0, "Purchase_Date"] == "2024-03-15"
    assert res.loc[1, "Purchase_Date"] == "2024-05-10"
    assert res.loc[2, "Purchase_Date"] == "2024-12-25"
    assert pd.isna(res.loc[3, "Purchase_Date"])


def test_correct_category_typos():
    audit = CleaningAudit()
    df_cats = pd.DataFrame({
        "Product_Category": ["Electrnics", "Cloting", "Home and Kitchen", "Boks", "Sports & Fitness"]
    })
    res = correct_category_typos(df_cats, audit)
    assert res["Product_Category"].tolist() == [
        "Electronics", "Clothing", "Home & Kitchen", "Books", "Sports & Fitness"
    ]


def test_handle_missing_values():
    audit = CleaningAudit()
    df_missing = pd.DataFrame([
        # Missing Customer_ID -> must be dropped
        {
            "Customer_ID": np.nan,
            "Customer_Name": "Aditi Roy",
            "Age": 30,
            "Gender": "Female",
            "City": "Mumbai",
            "Region": "West",
            "Occupation": "Doctor",
            "Product_Category": "Clothing",
            "Product_Name": "Casual Jacket",
            "Purchase_Date": "2024-04-12",
            "Quantity_Purchased": 1,
            "Unit_Price": 2500.0,
            "Total_Purchase_Value": 2500.0,
            "Payment_Method": "Credit Card",
            "Purchase_Channel": "Online",
            "Customer_Segment": "Standard",
            "Loyalty_Status": "Silver",
            "Discount_Used": 0.0,
            "Purchase_Frequency": 1,
            "Last_Purchase_Date": "2024-04-12",
        },
        # Missing Total -> must be recomputed (2 * 1000 * (1 - 0.10) = 1800)
        {
            "Customer_ID": "C0002",
            "Customer_Name": "Rohan Shah",
            "Age": np.nan,
            "Gender": np.nan,
            "City": "Mumbai",
            "Region": "West",
            "Occupation": np.nan,
            "Product_Category": "Clothing",
            "Product_Name": "Slim Fit Jeans",
            "Purchase_Date": "2024-04-15",
            "Quantity_Purchased": 2,
            "Unit_Price": 1000.0,
            "Total_Purchase_Value": np.nan,
            "Payment_Method": "Credit Card",
            "Purchase_Channel": "Online",
            "Customer_Segment": "Standard",
            "Loyalty_Status": np.nan,
            "Discount_Used": 0.10,
            "Purchase_Frequency": 1,
            "Last_Purchase_Date": "2024-04-15",
        },
    ])
    res = handle_missing_values(df_missing, audit)
    assert len(res) == 1
    row = res.iloc[0]
    assert row["Customer_ID"] == "C0002"
    assert row["Total_Purchase_Value"] == 1800.0
    assert row["Age"] >= 18
    assert row["Loyalty_Status"] == "Regular"


def test_recompute_customer_aggregates(sample_dirty_data: pd.DataFrame):
    audit = CleaningAudit()
    df_deduped = remove_duplicates(sample_dirty_data, audit)
    df_deduped = parse_and_standardize_dates(df_deduped, audit)
    res = recompute_customer_aggregates(df_deduped, audit)
    assert (res["Purchase_Frequency"] == 2).all()
    assert (res["Last_Purchase_Date"] == "2024-06-20").all()


def test_clean_dataset_pipeline():
    """Verify end-to-end cleaning execution produces valid artifacts."""
    clean_csv = "data/processed/customer_purchases_clean.csv"
    report_md = "reports/cleaning_log.md"
    
    df_clean, audit = clean_dataset(
        raw_path="data/raw/customer_purchases_raw.csv",
        output_path=clean_csv,
        report_path=report_md,
    )
    assert os.path.exists(clean_csv)
    assert os.path.exists(report_md)
    assert df_clean.isna().sum().sum() == 0
    assert not df_clean.duplicated().any()
    assert "Is_Outlier" in df_clean.columns
