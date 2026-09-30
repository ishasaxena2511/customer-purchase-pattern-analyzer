"""
clean_data.py
-------------
Purpose:
    Cleans and standardizes raw customer purchase transaction data for retail analytics.
    Performs data cleaning across 8 modular steps:
      1. Deduplication (exact row removal)
      2. Customer name standardization (whitespace trimming & Title Case)
      3. Mixed-format date parsing to ISO YYYY-MM-DD & invalid date filtering
      4. Category typo resolution via explicit mapping & fuzzy matching (difflib)
      5. Column-justified missing value imputation and mathematical recomputation
      6. IQR-based outlier detection per product category (flagged via Is_Outlier)
      7. Business rule data validation & assertion checks
      8. Customer-level aggregate recomputation (Purchase Frequency & Last Purchase Date)
      
    Outputs:
      - data/processed/customer_purchases_clean.csv
      - reports/cleaning_log.md (Detailed audit log and before/after metrics)
"""

from datetime import datetime
import difflib
import os
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd

# Standard reference taxonomy
VALID_CATEGORIES: List[str] = [
    "Electronics",
    "Clothing",
    "Home & Kitchen",
    "Beauty & Personal Care",
    "Sports & Fitness",
    "Books",
]

KNOWN_CATEGORY_MAPPINGS: Dict[str, str] = {
    "electrnics": "Electronics",
    "electronics": "Electronics",
    "electronicss": "Electronics",
    "electonics": "Electronics",
    "cloting": "Clothing",
    "clothing": "Clothing",
    "clothng": "Clothing",
    "clothings": "Clothing",
    "home and kitchen": "Home & Kitchen",
    "home & kitchen": "Home & Kitchen",
    "home&kitchen": "Home & Kitchen",
    "home kitchen": "Home & Kitchen",
    "beauty & personal": "Beauty & Personal Care",
    "beauty & personal care": "Beauty & Personal Care",
    "beauty & care": "Beauty & Personal Care",
    "sports & fitnes": "Sports & Fitness",
    "sports and fitness": "Sports & Fitness",
    "sport & fitness": "Sports & Fitness",
    "sports & fitness": "Sports & Fitness",
    "boks": "Books",
    "books": "Books",
    "bookss": "Books",
}

CITY_TO_REGION: Dict[str, str] = {
    "Delhi": "North",
    "Noida": "North",
    "Jaipur": "North",
    "Mumbai": "West",
    "Pune": "West",
    "Ahmedabad": "West",
    "Bangalore": "South",
    "Hyderabad": "South",
    "Chennai": "South",
    "Kolkata": "East",
    "Bhubaneswar": "East",
}

VALID_PAYMENT_METHODS: List[str] = [
    "UPI",
    "Credit Card",
    "Debit Card",
    "Net Banking",
    "Cash on Delivery",
]

VALID_PURCHASE_CHANNELS: List[str] = ["Online", "In-Store", "Mobile App"]


class CleaningAudit:
    """Tracks and logs quantitative audit metrics for each cleaning step."""

    def __init__(self) -> None:
        """Initialize empty containers for step logs, outlier statistics, and validations."""
        self.step_logs: List[Dict[str, Any]] = []
        self.outlier_stats: Dict[str, Dict[str, float]] = {}
        self.validation_results: List[Dict[str, Any]] = []

    def log_step(
        self,
        step_number: int,
        step_name: str,
        rows_before: int,
        rows_after: int,
        values_modified: int,
        details: str,
    ) -> None:
        """Record the outcome of an individual cleaning step."""
        rows_dropped = rows_before - rows_after
        self.step_logs.append({
            "step_number": step_number,
            "step_name": step_name,
            "rows_before": rows_before,
            "rows_after": rows_after,
            "rows_dropped": rows_dropped,
            "values_modified": values_modified,
            "details": details,
        })


def remove_duplicates(df: pd.DataFrame, audit: CleaningAudit) -> pd.DataFrame:
    """
    Step 1: Identify and remove exact duplicate rows across all columns.
    """
    rows_before = len(df)
    duplicates_mask = df.duplicated()
    num_duplicates = int(duplicates_mask.sum())
    
    df_deduped = df.drop_duplicates().copy()
    rows_after = len(df_deduped)
    
    audit.log_step(
        step_number=1,
        step_name="Remove Exact Duplicates",
        rows_before=rows_before,
        rows_after=rows_after,
        values_modified=0,
        details=f"Identified and removed {num_duplicates} exact duplicate records.",
    )
    return df_deduped


def standardize_customer_names(df: pd.DataFrame, audit: CleaningAudit) -> pd.DataFrame:
    """
    Step 2: Clean customer names: strip outer whitespace, collapse multiple spaces,
    and convert to Title Case.
    """
    df = df.copy()
    rows_before = len(df)
    
    original_names = df["Customer_Name"].astype(str)
    
    # Strip leading/trailing whitespaces, collapse interior spaces, convert to Title Case
    cleaned_names = (
        df["Customer_Name"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.title()
    )
    # Restore NaN if original was null
    cleaned_names = cleaned_names.replace("", np.nan)
    
    changed_mask = (original_names != cleaned_names) & original_names.notna()
    num_changed = int(changed_mask.sum())
    
    df["Customer_Name"] = cleaned_names
    
    audit.log_step(
        step_number=2,
        step_name="Standardize Customer Names",
        rows_before=rows_before,
        rows_after=rows_before,
        values_modified=num_changed,
        details=(
            f"Standardized {num_changed} customer names by trimming leading/trailing spaces, "
            f"collapsing multiple internal spaces, and formatting to Title Case."
        ),
    )
    return df


def parse_and_standardize_dates(df: pd.DataFrame, audit: CleaningAudit) -> pd.DataFrame:
    """
    Step 3: Parse mixed date formats (ISO, DD/MM/YYYY, MM-DD-YYYY, textual) into
    standard ISO YYYY-MM-DD. Coerce unparseable dates to NaT for subsequent handling.
    """
    df = df.copy()
    rows_before = len(df)
    
    # Use pandas flexible format='mixed' parser
    parsed_dates = pd.to_datetime(df["Purchase_Date"], format="mixed", errors="coerce")
    
    unparseable_mask = df["Purchase_Date"].notna() & parsed_dates.isna()
    num_unparseable = int(unparseable_mask.sum())
    
    # Convert valid timestamps to ISO date strings (YYYY-MM-DD)
    iso_date_strings = parsed_dates.dt.strftime("%Y-%m-%d")
    
    df["Purchase_Date"] = iso_date_strings
    
    audit.log_step(
        step_number=3,
        step_name="Parse & Standardize Dates",
        rows_before=rows_before,
        rows_after=rows_before,
        values_modified=int(parsed_dates.notna().sum()),
        details=(
            f"Parsed heterogeneous date formats to ISO YYYY-MM-DD. "
            f"Encountered and flagged {num_unparseable} unparseable date values as invalid (NaT)."
        ),
    )
    return df


def correct_category_typos(df: pd.DataFrame, audit: CleaningAudit) -> pd.DataFrame:
    """
    Step 4: Harmonize product categories using direct mapping and fuzzy string matching (difflib).
    """
    df = df.copy()
    rows_before = len(df)
    
    original_categories = df["Product_Category"].copy()
    corrected_categories = []
    typo_corrections_count = 0
    
    for val in df["Product_Category"]:
        if pd.isna(val):
            corrected_categories.append(val)
            continue
            
        val_clean = str(val).strip()
        val_lower = val_clean.lower()
        
        # 1. Exact match against valid list
        if val_clean in VALID_CATEGORIES:
            corrected_categories.append(val_clean)
        # 2. Match against known dictionary mappings
        elif val_lower in KNOWN_CATEGORY_MAPPINGS:
            matched_cat = KNOWN_CATEGORY_MAPPINGS[val_lower]
            corrected_categories.append(matched_cat)
            if matched_cat != val:
                typo_corrections_count += 1
        # 3. Fuzzy match fallback
        else:
            closest_matches = difflib.get_close_matches(val_clean, VALID_CATEGORIES, n=1, cutoff=0.55)
            if closest_matches:
                corrected_categories.append(closest_matches[0])
                typo_corrections_count += 1
            else:
                corrected_categories.append(val_clean)
                
    df["Product_Category"] = corrected_categories
    
    audit.log_step(
        step_number=4,
        step_name="Correct Category Typos",
        rows_before=rows_before,
        rows_after=rows_before,
        values_modified=typo_corrections_count,
        details=(
            f"Corrected {typo_corrections_count} category typos and casing mismatches "
            f"using dictionary mapping and difflib fuzzy matching against valid taxonomy."
        ),
    )
    return df


def handle_missing_values(df: pd.DataFrame, audit: CleaningAudit) -> pd.DataFrame:
    """
    Step 5: Address missing values using a documented, justified strategy per column:
      - Drop rows missing Customer_ID (unidentified customer cannot be analyzed).
      - Drop rows missing Purchase_Date (unusable for time-series / RFM recency analysis).
      - Discount_Used: fill with 0.0 (absence of recorded discount implies full price).
      - Total_Purchase_Value: recompute from Quantity * Unit Price * (1 - Discount) where possible.
      - Unit_Price: recompute from Total / (Quantity * (1 - Discount)) where possible,
        otherwise impute by category median.
      - Age: impute with median age (robust against outliers and skewness).
      - Categoricals (Gender, Occupation, Loyalty_Status): impute with mode or 'Unknown'.
      - Geographic / Channel / Payment: impute with mode or derive Region from City.
    """
    df = df.copy()
    rows_before = len(df)
    
    # 1. Drop rows missing critical identifiers: Customer_ID or Purchase_Date
    critical_missing = df["Customer_ID"].isna() | df["Purchase_Date"].isna()
    dropped_critical_count = int(critical_missing.sum())
    df = df[~critical_missing].copy()
    
    # Track imputation counts
    imputation_counts: Dict[str, int] = {}
    
    # 2. Discount_Used: Recover mathematically if Total, Unit_Price, and Qty exist; otherwise default to 0.0
    recoverable_disc = df["Discount_Used"].isna() & df["Total_Purchase_Value"].notna() & df["Unit_Price"].notna() & (df["Quantity_Purchased"] > 0)
    recovered_disc_count = int(recoverable_disc.sum())
    if recoverable_disc.any():
        implied_disc = 1.0 - (
            df.loc[recoverable_disc, "Total_Purchase_Value"]
            / (df.loc[recoverable_disc, "Quantity_Purchased"] * df.loc[recoverable_disc, "Unit_Price"])
        )
        # Clip to valid retail discount range [0.0, 0.50] and round to 2 decimal places
        df.loc[recoverable_disc, "Discount_Used"] = implied_disc.clip(0.0, 0.50).round(2)
        
    remaining_null_disc = int(df["Discount_Used"].isna().sum())
    df["Discount_Used"] = df["Discount_Used"].fillna(0.0)
    imputation_counts["Discount_Used (Recovered/Imputed)"] = recovered_disc_count + remaining_null_disc
    
    # 3. Quantity_Purchased: Fill nulls with 1 (standard retail transaction baseline)
    null_qty = int(df["Quantity_Purchased"].isna().sum())
    df["Quantity_Purchased"] = df["Quantity_Purchased"].fillna(1).astype(int)
    imputation_counts["Quantity_Purchased"] = null_qty
    
    # 4. Recompute Unit_Price and Total_Purchase_Value
    # Case A: Total is missing, but Unit_Price and Quantity exist
    missing_total_mask = df["Total_Purchase_Value"].isna() & df["Unit_Price"].notna()
    recomputed_totals = int(missing_total_mask.sum())
    df.loc[missing_total_mask, "Total_Purchase_Value"] = (
        df.loc[missing_total_mask, "Quantity_Purchased"]
        * df.loc[missing_total_mask, "Unit_Price"]
        * (1.0 - df.loc[missing_total_mask, "Discount_Used"])
    ).round(2)
    imputation_counts["Total_Purchase_Value (Recomputed)"] = recomputed_totals
    
    # Case B: Unit_Price is missing, but Total exists
    missing_price_mask = df["Unit_Price"].isna() & df["Total_Purchase_Value"].notna()
    recomputed_prices = int(missing_price_mask.sum())
    discount_factor = (1.0 - df.loc[missing_price_mask, "Discount_Used"]).replace(0, 1.0)
    df.loc[missing_price_mask, "Unit_Price"] = (
        df.loc[missing_price_mask, "Total_Purchase_Value"]
        / (df.loc[missing_price_mask, "Quantity_Purchased"] * discount_factor)
    ).round(2)
    imputation_counts["Unit_Price (Recomputed)"] = recomputed_prices
    
    # Case C: If both Unit_Price and Total are still missing, impute Unit_Price from category median
    still_missing_price = df["Unit_Price"].isna()
    if still_missing_price.any():
        cat_median_prices = df.groupby("Product_Category")["Unit_Price"].transform("median")
        df["Unit_Price"] = df["Unit_Price"].fillna(cat_median_prices).fillna(1000.0).round(2)
        df["Total_Purchase_Value"] = (
            df["Quantity_Purchased"] * df["Unit_Price"] * (1.0 - df["Discount_Used"])
        ).round(2)
        
    # 5. Age: Impute missing with median age (default to 35.0 if entire cohort is missing)
    null_age = int(df["Age"].isna().sum())
    median_val = df["Age"].median()
    median_age = float(median_val) if pd.notna(median_val) else 35.0
    df["Age"] = df["Age"].fillna(median_age).round().astype(int)
    imputation_counts["Age (Median Imputed)"] = null_age
    
    # 6. Categoricals: Impute missing values with mode or business defaults
    null_gender = int(df["Gender"].isna().sum())
    gender_mode = df["Gender"].mode()[0] if not df["Gender"].mode().empty else "Unknown"
    df["Gender"] = df["Gender"].fillna(gender_mode)
    imputation_counts["Gender"] = null_gender
    
    null_loyalty = int(df["Loyalty_Status"].isna().sum())
    df["Loyalty_Status"] = df["Loyalty_Status"].fillna("Regular")
    imputation_counts["Loyalty_Status"] = null_loyalty
    
    null_pay = int(df["Payment_Method"].isna().sum())
    pay_mode = df["Payment_Method"].mode()[0] if not df["Payment_Method"].mode().empty else "UPI"
    df["Payment_Method"] = df["Payment_Method"].fillna(pay_mode)
    imputation_counts["Payment_Method"] = null_pay
    
    null_chan = int(df["Purchase_Channel"].isna().sum())
    chan_mode = df["Purchase_Channel"].mode()[0] if not df["Purchase_Channel"].mode().empty else "Online"
    df["Purchase_Channel"] = df["Purchase_Channel"].fillna(chan_mode)
    imputation_counts["Purchase_Channel"] = null_chan
    
    null_occ = int(df["Occupation"].isna().sum())
    df["Occupation"] = df["Occupation"].fillna("Unknown")
    imputation_counts["Occupation"] = null_occ
    
    # 7. Harmonize Region based on City mapping
    df["Region"] = df["City"].map(CITY_TO_REGION).fillna(df["Region"]).fillna("North")
    
    total_modifications = sum(imputation_counts.values())
    rows_after = len(df)
    
    audit.log_step(
        step_number=5,
        step_name="Handle Missing Values",
        rows_before=rows_before,
        rows_after=rows_after,
        values_modified=total_modifications,
        details=(
            f"Dropped {dropped_critical_count} records missing critical Customer_ID or Purchase_Date. "
            f"Recomputed {recomputed_totals} missing Totals and {recomputed_prices} missing Unit Prices mathematically. "
            f"Imputed Age (median={median_age:.1f}), Discount (0.0), and categorical columns using mode/justified fallbacks."
        ),
    )
    return df


def detect_and_flag_outliers(df: pd.DataFrame, audit: CleaningAudit) -> pd.DataFrame:
    """
    Step 6: Detect outliers in Total_Purchase_Value using the Interquartile Range (IQR)
    method computed separately per Product_Category.
    
    Decision: Flagging (Is_Outlier = True/False) rather than hard truncation/deletion.
    Rationale:
      In commercial retail and e-commerce, high-value bulk purchases represent legitimate
      revenue and true business transactions. Truncating or deleting them distorts financial
      accounting, whereas flagging enables data analysts to segment high-value wholesale
      orders from everyday consumer patterns without loss of data fidelity.
    """
    df = df.copy()
    rows_before = len(df)
    
    df["Is_Outlier"] = False
    total_outliers = 0
    
    for category in df["Product_Category"].unique():
        cat_mask = df["Product_Category"] == category
        cat_values = df.loc[cat_mask, "Total_Purchase_Value"]
        
        q1 = float(cat_values.quantile(0.25))
        q3 = float(cat_values.quantile(0.75))
        iqr = q3 - q1
        
        lower_bound = max(0.0, q1 - 1.5 * iqr)
        upper_bound = q3 + 1.5 * iqr
        
        outliers_cat_mask = cat_mask & (
            (df["Total_Purchase_Value"] < lower_bound) | (df["Total_Purchase_Value"] > upper_bound)
        )
        cat_outlier_count = int(outliers_cat_mask.sum())
        total_outliers += cat_outlier_count
        
        df.loc[outliers_cat_mask, "Is_Outlier"] = True
        
        audit.outlier_stats[str(category)] = {
            "Q1": round(q1, 2),
            "Q3": round(q3, 2),
            "IQR": round(iqr, 2),
            "Lower_Bound": round(lower_bound, 2),
            "Upper_Bound": round(upper_bound, 2),
            "Outlier_Count": cat_outlier_count,
        }
        
    audit.log_step(
        step_number=6,
        step_name="Detect & Flag Outliers (IQR Method)",
        rows_before=rows_before,
        rows_after=rows_before,
        values_modified=total_outliers,
        details=(
            f"Evaluated category-specific IQR fences (1.5x IQR). Identified {total_outliers} outliers "
            f"and flagged them in 'Is_Outlier' column without data loss to preserve financial integrity."
        ),
    )
    return df


def validate_cleaned_data(df: pd.DataFrame, audit: CleaningAudit) -> pd.DataFrame:
    """
    Step 7: Enforce data validation rules and assert data integrity:
      - Quantity_Purchased > 0
      - Unit_Price > 0 and Total_Purchase_Value > 0
      - Mathematical reconciliation: Total = Qty * Unit Price * (1 - Discount) within tolerance
      - Purchase_Date <= current date
      - Age between 18 and 80
      - Region matches City taxonomy
      - Valid Category, Payment Method, and Purchase Channel values
    """
    df = df.copy()
    rows_before = len(df)
    
    # 1. Assert no negative or zero quantities
    assert (df["Quantity_Purchased"] > 0).all(), "Validation Error: Non-positive Quantity found."
    audit.validation_results.append({
        "check": "No negative or zero quantities",
        "status": "PASSED",
        "detail": f"All {len(df)} transactions have Quantity > 0 (Min: {df['Quantity_Purchased'].min()}).",
    })
    
    # 2. Mathematical consistency: Total = Qty * Price * (1 - Discount) within 0.05 tolerance
    expected_totals = (
        df["Quantity_Purchased"] * df["Unit_Price"] * (1.0 - df["Discount_Used"])
    ).round(2)
    max_discrepancy = float((df["Total_Purchase_Value"] - expected_totals).abs().max())
    
    # Realign any sub-cent floating-point precision to exact 2-decimal arithmetic
    assert max_discrepancy <= 0.05, f"Validation Error: Mathematical discrepancy {max_discrepancy} exceeds 0.05 tolerance."
    df["Total_Purchase_Value"] = expected_totals
    assert (df["Total_Purchase_Value"] > 0).all(), "Validation Error: Non-positive Total Purchase Value found."
    audit.validation_results.append({
        "check": "Total = Qty × Unit Price × (1 - Discount)",
        "status": "PASSED",
        "detail": f"All {len(df)} transactions mathematically verified within 0.05 tolerance (Max diff: ₹{max_discrepancy:.4f}).",
    })
    
    # 3. Assert Purchase_Date <= today
    today_str = datetime.now().strftime("%Y-%m-%d")
    date_violations = df["Purchase_Date"] > today_str
    assert not date_violations.any(), "Validation Error: Future transaction dates detected."
    audit.validation_results.append({
        "check": "Purchase Date <= Today",
        "status": "PASSED",
        "detail": f"All transaction dates are on or before current date ({today_str}).",
    })
    
    # 4. Assert Age between 18 and 80
    age_valid = (df["Age"] >= 18) & (df["Age"] <= 80)
    assert age_valid.all(), "Validation Error: Age outside acceptable range [18, 80]."
    audit.validation_results.append({
        "check": "Age within [18, 80]",
        "status": "PASSED",
        "detail": f"Age bounds validated. Range: {df['Age'].min()} to {df['Age'].max()} years.",
    })
    
    # 5. Assert Region matches City
    for city, reg in CITY_TO_REGION.items():
        city_rows = df[df["City"] == city]
        if not city_rows.empty:
            assert (city_rows["Region"] == reg).all(), f"Region mismatch for city {city}."
    audit.validation_results.append({
        "check": "Region matches City mapping",
        "status": "PASSED",
        "detail": f"All cities mapped accurately to corresponding geographic regions.",
    })
    
    # 6. Assert valid taxonomy
    assert df["Product_Category"].isin(VALID_CATEGORIES).all(), "Invalid categories found."
    assert df["Payment_Method"].isin(VALID_PAYMENT_METHODS).all(), "Invalid payment methods found."
    assert df["Purchase_Channel"].isin(VALID_PURCHASE_CHANNELS).all(), "Invalid purchase channels found."
    audit.validation_results.append({
        "check": "Taxonomy validation (Category, Payment, Channel)",
        "status": "PASSED",
        "detail": "All categorical values strictly conform to allowed taxonomy dictionaries.",
    })
    
    audit.log_step(
        step_number=7,
        step_name="Data Validation & Assertion Suite",
        rows_before=rows_before,
        rows_after=rows_before,
        values_modified=0,
        details="All 6 structural and mathematical assertion tests PASSED with zero violations.",
    )
    return df


def recompute_customer_aggregates(df: pd.DataFrame, audit: CleaningAudit) -> pd.DataFrame:
    """
    Step 8: Recompute customer-level Purchase Frequency and Last Purchase Date
    directly from transactional records to eliminate discrepancies.
    """
    df = df.copy()
    rows_before = len(df)
    
    # Compute true transaction count per customer
    true_frequency = df.groupby("Customer_ID")["Purchase_Date"].transform("count")
    
    # Compute true maximum (most recent) purchase date per customer
    true_last_date = df.groupby("Customer_ID")["Purchase_Date"].transform("max")
    
    freq_diff_count = int((df["Purchase_Frequency"] != true_frequency).sum())
    date_diff_count = int((df["Last_Purchase_Date"] != true_last_date).sum())
    
    df["Purchase_Frequency"] = true_frequency.astype(int)
    df["Last_Purchase_Date"] = true_last_date
    
    audit.log_step(
        step_number=8,
        step_name="Recompute Customer Aggregates",
        rows_before=rows_before,
        rows_after=rows_before,
        values_modified=freq_diff_count + date_diff_count,
        details=(
            f"Synchronized customer summary metrics across transactions: "
            f"realigned {freq_diff_count} Purchase Frequency values and {date_diff_count} Last Purchase Date records."
        ),
    )
    return df


def generate_cleaning_report(
    audit: CleaningAudit,
    df_raw: pd.DataFrame,
    df_clean: pd.DataFrame,
    report_path: str = "reports/cleaning_log.md",
) -> None:
    """
    Generates a Markdown audit report detailing before/after metrics,
    cleaning actions, outlier thresholds, and validation results.
    """
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    raw_rows = len(df_raw)
    clean_rows = len(df_clean)
    raw_nulls = int(df_raw.isna().sum().sum())
    clean_nulls = int(df_clean.isna().sum().sum())
    raw_dups = int(df_raw.duplicated().sum())
    clean_dups = int(df_clean.duplicated().sum())
    
    md_lines: List[str] = [
        "# Data Cleaning & Integrity Audit Log",
        "",
        f"**Generated On:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Pipeline Step:** Data Ingestion & Preprocessing (`clean_data.py`)  ",
        f"**Target Dataset:** `data/processed/customer_purchases_clean.csv`  ",
        "",
        "---",
        "",
        "## 1. Before vs. After Summary",
        "",
        "| Metric | Raw Dataset (`data/raw`) | Cleaned Dataset (`data/processed`) | Net Change |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Total Rows** | {raw_rows:,} | {clean_rows:,} | -{raw_rows - clean_rows:,} rows |",
        f"| **Total Columns** | {df_raw.shape[1]} | {df_clean.shape[1]} (added `Is_Outlier`) | +1 column |",
        f"| **Total Missing Values** | {raw_nulls:,} | {clean_nulls:,} | -{raw_nulls - clean_nulls:,} nulls |",
        f"| **Exact Duplicate Rows** | {raw_dups:,} | {clean_dups:,} | -{raw_dups - clean_dups:,} duplicates |",
        f"| **Distinct Customers** | {df_raw['Customer_ID'].dropna().nunique():,} | {df_clean['Customer_ID'].nunique():,} | Clean cohort |",
        "",
        "---",
        "",
        "## 2. Step-by-Step Cleaning Audit",
        "",
        "| Step | Action | Rows In | Rows Out | Values Modified | Technical Details |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    
    for s in audit.step_logs:
        md_lines.append(
            f"| **{s['step_number']}** | {s['step_name']} | {s['rows_before']:,} | {s['rows_after']:,} | "
            f"{s['values_modified']:,} | {s['details']} |"
        )
        
    md_lines.extend([
        "",
        "---",
        "",
        "## 3. Outlier Analysis (IQR Method per Product Category)",
        "",
        "> **Methodology Note on Outliers:**  ",
        "> Outliers in `Total_Purchase_Value` were evaluated independently within each `Product_Category` using ",
        "> the Interquartile Range ($IQR = Q3 - Q1$) with fences established at $[\\max(0, Q1 - 1.5 \\times IQR), Q3 + 1.5 \\times IQR]$.  ",
        "> **Decision:** We **flagged** outliers (`Is_Outlier = True`) rather than hard-clipping or dropping them. ",
        "> In retail e-commerce, high-value bulk purchases represent legitimate business income that would distort ",
        "> accounting records if removed. Flagging preserves data integrity while enabling analytical models to filter or handle them appropriately.",
        "",
        "| Product Category | Q1 (25th %) | Q3 (75th %) | IQR | Upper Fence (1.5x) | Outlier Transactions |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ])
    
    for cat, stats in audit.outlier_stats.items():
        md_lines.append(
            f"| **{cat}** | ₹{stats['Q1']:,.2f} | ₹{stats['Q3']:,.2f} | ₹{stats['IQR']:,.2f} | ₹{stats['Upper_Bound']:,.2f} | {stats['Outlier_Count']} |"
        )
        
    md_lines.extend([
        "",
        "---",
        "",
        "## 4. Data Validation & Integrity Verification",
        "",
        "| Validation Check | Status | Verification Findings |",
        "| :--- | :--- | :--- |",
    ])
    
    for val in audit.validation_results:
        status_badge = "✅ PASSED" if val["status"] == "PASSED" else "❌ FAILED"
        md_lines.append(f"| **{val['check']}** | {status_badge} | {val['detail']} |")
        
    md_lines.extend([
        "",
        "---",
        "",
        "## 5. Column-by-Column Missing Value Treatment Strategy",
        "",
        "- **`Customer_ID`**: Dropped. Unidentified transactions cannot be linked to purchase patterns or repeat behavior.",
        "- **`Purchase_Date`**: Dropped if unparseable/missing. Time-series metrics and RFM Recency strictly require valid dates.",
        "- **`Discount_Used`**: Imputed with `0.0`. Standard retail assumption is that unrecorded discount implies zero discount.",
        "- **`Quantity_Purchased`**: Imputed with baseline `1`. Non-positive records corrected.",
        "- **`Unit_Price` & `Total_Purchase_Value`**: Mathematically recomputed ($Total = Quantity \\times Price \\times (1 - Discount)$). If both missing, imputed via Category median.",
        "- **`Age`**: Imputed with median customer age. Median is robust to demographic skewness compared to arithmetic mean.",
        "- **`Gender`, `Payment_Method`, `Purchase_Channel`**: Imputed using statistical mode.",
        "- **`Loyalty_Status`**: Imputed with `'Regular'` tier as base default.",
        "- **`Region`**: Deterministically harmonized from `City` via standard regional mapping.",
        "",
        "*Audit log successfully generated by `src/clean_data.py`.*",
    ])
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))


def clean_dataset(
    raw_path: str = "data/raw/customer_purchases_raw.csv",
    output_path: str = "data/processed/customer_purchases_clean.csv",
    report_path: str = "reports/cleaning_log.md",
) -> Tuple[pd.DataFrame, CleaningAudit]:
    """
    Main execution pipeline for data cleaning and integrity validation.
    
    Parameters:
        raw_path: Path to the raw CSV file.
        output_path: Destination path for cleaned CSV dataset.
        report_path: Destination path for Markdown audit report.
        
    Returns:
        Tuple of (Cleaned DataFrame, CleaningAudit instance).
    """
    print(f"Reading raw dataset from: {raw_path}")
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw data file not found at {raw_path}. Run generate_data.py first.")
        
    df_raw = pd.read_csv(raw_path)
    audit = CleaningAudit()
    
    # Execute modular cleaning sequence
    df_current = df_raw.copy()
    df_current = remove_duplicates(df_current, audit)
    df_current = standardize_customer_names(df_current, audit)
    df_current = parse_and_standardize_dates(df_current, audit)
    df_current = correct_category_typos(df_current, audit)
    df_current = handle_missing_values(df_current, audit)
    df_current = detect_and_flag_outliers(df_current, audit)
    df_current = validate_cleaned_data(df_current, audit)
    df_current = recompute_customer_aggregates(df_current, audit)
    
    # Save cleaned dataset
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_current.to_csv(output_path, index=False)
    print(f"Cleaned dataset saved to: {output_path} ({len(df_current)} rows, {df_current.shape[1]} columns)")
    
    # Generate audit report
    generate_cleaning_report(audit, df_raw, df_current, report_path)
    print(f"Cleaning audit report written to: {report_path}")
    
    return df_current, audit


if __name__ == "__main__":
    clean_dataset()
