# Data Cleaning & Integrity Audit Log

**Generated On:** 2026-09-30 18:19:58  
**Pipeline Step:** Data Ingestion & Preprocessing (`clean_data.py`)  
**Target Dataset:** `data/processed/customer_purchases_clean.csv`  

---

## 1. Before vs. After Summary

| Metric | Raw Dataset (`data/raw`) | Cleaned Dataset (`data/processed`) | Net Change |
| :--- | :--- | :--- | :--- |
| **Total Rows** | 1,235 | 1,160 | -75 rows |
| **Total Columns** | 20 | 21 (added `Is_Outlier`) | +1 column |
| **Total Missing Values** | 140 | 0 | -140 nulls |
| **Exact Duplicate Rows** | 35 | 0 | -35 duplicates |
| **Distinct Customers** | 130 | 129 | Clean cohort |

---

## 2. Step-by-Step Cleaning Audit

| Step | Action | Rows In | Rows Out | Values Modified | Technical Details |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Remove Exact Duplicates | 1,235 | 1,200 | 0 | Identified and removed 35 exact duplicate records. |
| **2** | Standardize Customer Names | 1,200 | 1,200 | 949 | Standardized 949 customer names by trimming leading/trailing spaces, collapsing multiple internal spaces, and formatting to Title Case. |
| **3** | Parse & Standardize Dates | 1,200 | 1,200 | 1,170 | Parsed heterogeneous date formats to ISO YYYY-MM-DD. Encountered and flagged 22 unparseable date values as invalid (NaT). |
| **4** | Correct Category Typos | 1,200 | 1,200 | 97 | Corrected 97 category typos and casing mismatches using dictionary mapping and difflib fuzzy matching against valid taxonomy. |
| **5** | Handle Missing Values | 1,200 | 1,160 | 110 | Dropped 40 records missing critical Customer_ID or Purchase_Date. Recomputed 24 missing Totals and 18 missing Unit Prices mathematically. Imputed Age (median=47.0), Discount (0.0), and categorical columns using mode/justified fallbacks. |
| **6** | Detect & Flag Outliers (IQR Method) | 1,160 | 1,160 | 82 | Evaluated category-specific IQR fences (1.5x IQR). Identified 82 outliers and flagged them in 'Is_Outlier' column without data loss to preserve financial integrity. |
| **7** | Data Validation & Assertion Suite | 1,160 | 1,160 | 0 | All 6 structural and mathematical assertion tests PASSED with zero violations. |
| **8** | Recompute Customer Aggregates | 1,160 | 1,160 | 2,222 | Synchronized customer summary metrics across transactions: realigned 1145 Purchase Frequency values and 1077 Last Purchase Date records. |

---

## 3. Outlier Analysis (IQR Method per Product Category)

> **Methodology Note on Outliers:**  
> Outliers in `Total_Purchase_Value` were evaluated independently within each `Product_Category` using 
> the Interquartile Range ($IQR = Q3 - Q1$) with fences established at $[\max(0, Q1 - 1.5 \times IQR), Q3 + 1.5 \times IQR]$.  
> **Decision:** We **flagged** outliers (`Is_Outlier = True`) rather than hard-clipping or dropping them. 
> In retail e-commerce, high-value bulk purchases represent legitimate business income that would distort 
> accounting records if removed. Flagging preserves data integrity while enabling analytical models to filter or handle them appropriately.

| Product Category | Q1 (25th %) | Q3 (75th %) | IQR | Upper Fence (1.5x) | Outlier Transactions |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Books** | ₹620.91 | ₹1,494.10 | ₹873.19 | ₹2,803.89 | 9 |
| **Beauty & Personal Care** | ₹552.07 | ₹1,741.45 | ₹1,189.38 | ₹3,525.52 | 18 |
| **Electronics** | ₹1,677.32 | ₹5,599.80 | ₹3,922.48 | ₹11,483.51 | 12 |
| **Home & Kitchen** | ₹1,127.12 | ₹3,869.34 | ₹2,742.21 | ₹7,982.65 | 14 |
| **Sports & Fitness** | ₹848.99 | ₹4,098.89 | ₹3,249.90 | ₹8,973.73 | 20 |
| **Clothing** | ₹1,045.47 | ₹3,810.87 | ₹2,765.40 | ₹7,958.97 | 9 |

---

## 4. Data Validation & Integrity Verification

| Validation Check | Status | Verification Findings |
| :--- | :--- | :--- |
| **No negative or zero quantities** | ✅ PASSED | All 1160 transactions have Quantity > 0 (Min: 1). |
| **Total = Qty × Unit Price × (1 - Discount)** | ✅ PASSED | All 1160 transactions mathematically verified within 0.05 tolerance (Max diff: ₹0.0100). |
| **Purchase Date <= Today** | ✅ PASSED | All transaction dates are on or before current date (2026-09-30). |
| **Age within [18, 80]** | ✅ PASSED | Age bounds validated. Range: 18 to 71 years. |
| **Region matches City mapping** | ✅ PASSED | All cities mapped accurately to corresponding geographic regions. |
| **Taxonomy validation (Category, Payment, Channel)** | ✅ PASSED | All categorical values strictly conform to allowed taxonomy dictionaries. |

---

## 5. Column-by-Column Missing Value Treatment Strategy

- **`Customer_ID`**: Dropped. Unidentified transactions cannot be linked to purchase patterns or repeat behavior.
- **`Purchase_Date`**: Dropped if unparseable/missing. Time-series metrics and RFM Recency strictly require valid dates.
- **`Discount_Used`**: Imputed with `0.0`. Standard retail assumption is that unrecorded discount implies zero discount.
- **`Quantity_Purchased`**: Imputed with baseline `1`. Non-positive records corrected.
- **`Unit_Price` & `Total_Purchase_Value`**: Mathematically recomputed ($Total = Quantity \times Price \times (1 - Discount)$). If both missing, imputed via Category median.
- **`Age`**: Imputed with median customer age. Median is robust to demographic skewness compared to arithmetic mean.
- **`Gender`, `Payment_Method`, `Purchase_Channel`**: Imputed using statistical mode.
- **`Loyalty_Status`**: Imputed with `'Regular'` tier as base default.
- **`Region`**: Deterministically harmonized from `City` via standard regional mapping.

*Audit log successfully generated by `src/clean_data.py`.*