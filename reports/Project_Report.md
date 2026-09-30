# Customer Purchase Pattern Analyzer — Comprehensive Project Report

**Author / Role:** Senior Data Analyst & Analytics Engineer  
**Date:** 2026-09-30  
**Technology Stack:** Python 3.12, Pandas, NumPy, Scikit-Learn, SQLite, Plotly, Streamlit, Pytest, ReportLab  
**GitHub Repository:** `customer-purchase-pattern-analyzer`  

---

## 1. Executive Summary

This analytics engineering and customer intelligence project provides end-to-end transaction analysis, RFM cohort segmentation, and customer lifetime value optimization for an omnichannel Indian retail enterprise. 

Analyzing **1,160 validated transactions** across **129 distinct customer profiles** over calendar year 2024, the pipeline generated **₹3,771,206.53** in total gross merchandise volume with an Average Order Value of **₹3,251.04**. 

Key strategic findings reveal that **88.37% of customers are repeat buyers** generating **99.01% of company revenue**, customer lifetime equity yields a **13.1x spend multiplier** upon second-order conversion, and the top **40.3% of customers generate 80.0% of all gross sales**. Furthermore, **32 high-value repeat spenders** are currently overdue for purchase based on their historical purchase cadence, presenting a quantifiable **₹476,000+ retention intervention opportunity**.

---

## 2. Business Problem & Strategic Objectives

Modern retail and e-commerce organizations struggle with disjointed transactional data, leading to three critical strategic vulnerabilities:
1. **Undifferentiated Mass Marketing:** Treating high-value repeat spenders and one-time discount seekers identically, causing customer fatigue and wasted promotional spend.
2. **Silent Customer Churn:** Inability to detect when a loyal buyer has exceeded their natural replenishment cadence until after they have permanently defected.
3. **Margin Dilution:** Promoting low-margin hardware categories (e.g. electronics at 25.4% gross margin) without enforcing cross-sell attach rates for high-margin categories (e.g. beauty at 62.8% margin).

### Strategic Project Goals:
- Build an automated, reproducible data engineering pipeline that cleans raw transactional feeds, imputes missing values with justified domain rules, and detects outliers using category-specific IQR fences.
- Engineer multi-dimensional behavioral features including calendar seasonality, demographic groupings, customer tenure, purchase frequency, recency, and 3-year Basic Customer Lifetime Value (CLV).
- Construct rule-based RFM (Recency, Frequency, Monetary) quintile cohorts and compare them against unsupervised K-Means clustering ($k=4$).
- Deliver an interactive executive dashboard with corporate styling and automated dynamic business recommendations.

---

## 3. Dataset Architecture & Preprocessing

### 3.1 Data Schema
The raw transactional log (`customer_purchases_raw.csv`) comprises 1,235 raw records across 20 attributes:
- **Demographics:** `Customer_ID`, `Customer_Name`, `Age`, `Gender`, `City`, `Region`, `Occupation`
- **Transactions:** `Product_Category`, `Product_Name`, `Purchase_Date`, `Quantity_Purchased`, `Unit_Price`, `Discount_Used`, `Total_Purchase_Value`
- **Operational:** `Payment_Method`, `Purchase_Channel`, `Loyalty_Status`, `Customer_Segment`

### 3.2 Cleaning & Preprocessing Summary (`clean_data.py`)
The automated data cleaning suite enforced 8 rigorous validation steps:
- **Duplicate Removal:** Removed 35 exact duplicate rows (1,235 → 1,200 rows).
- **Name Standardization:** Standardized 949 names (trimmed whitespace, collapsed spaces, formatted to Title Case).
- **Date Normalization:** Parsed mixed date formats into ISO `YYYY-MM-DD`; flagged and dropped 22 unparseable dates.
- **Taxonomy Normalization:** Corrected 97 category typos and casing mismatches using fuzzy string matching (`difflib`).
- **Missing Value Imputation:** Dropped 40 records missing critical keys (`Customer_ID` or `Purchase_Date`). Recomputed 24 missing totals mathematically ($Qty \times Price \times (1 - Discount)$). Imputed Age via median (47.0 years) and categorical attributes via statistical mode.
- **Outlier Detection (IQR Method):** Evaluated category-specific fences ($[Q1 - 1.5 \times IQR, Q3 + 1.5 \times IQR]$). Identified 82 outliers and **flagged** them (`Is_Outlier = True`) without deletion to preserve financial accounting reconciliation.
- **Validation Test Suite:** 100% pass rate across zero-quantity, temporal bounds, and formula reconciliation tests. Final clean dataset: **1,160 rows, 21 columns**.

---

## 4. Analytical Metric Definitions & Mathematical Formulations

| Metric Name | Mathematical Formula | Business Purpose |
| :--- | :--- | :--- |
| **Total Revenue** | $\text{Revenue} = \sum_{i=1}^{N} \text{Total\_Purchase\_Value}_i$ | Topline gross merchandise volume |
| **Average Order Value (AOV)** | $\text{AOV} = \frac{\sum \text{Total\_Purchase\_Value}}{\text{Total Orders}}$ | Measures transaction basket magnitude |
| **Purchase Frequency** | $\text{Frequency} = \frac{\text{Total Orders}}{\text{Distinct Customers}}$ | Transaction velocity per customer |
| **Recency** | $\text{Recency} = \max(\text{Date}) - \text{Last\_Purchase\_Date}_i$ | Freshness of customer engagement (days) |
| **Repeat Purchase Rate** | $\text{Repeat Rate} = \frac{\text{Count}(\text{Customers with Orders} \ge 2)}{\text{Total Customers}} \times 100$ | Customer retention health indicator |
| **Gross Margin %** | $\text{Margin \%} = \frac{\text{Total Revenue} - \text{Total COGS}}{\text{Total Revenue}} \times 100$ | Category product profitability |
| **Basic CLV** | $\text{CLV} = \text{AOV} \times \text{Frequency} \times \text{Lifespan (3.0 yrs)}$ | Historical baseline lifetime equity |
| **Market Basket Lift** | $\text{Lift}(A, B) = \frac{P(A \cap B)}{P(A) \times P(B)}$ | Measure of co-purchase affinity above chance |

---

## 5. Customer Segmentation Methodology

### 5.1 Rule-Based RFM Quintile Scoring
Customers were scored from 1 to 5 across Recency (lower recency = higher score 5), Frequency (higher orders = 5), and Monetary value (higher spend = 5). Customers were mapped into 7 actionable cohorts:
- **Champions (32 customers, 24.8% base | ₹2,118,754.10, 56.2% rev):** Bought recently, buy frequently, spend highest.
- **Loyal Customers (26 customers, 20.2% base | ₹804,174.56, 21.3% rev):** Steady purchasing cadence and strong profitability.
- **Can't Lose Them (11 customers, 8.5% base | ₹364,776.46, 9.7% rev):** Historically heavy spenders who have not purchased in >70 days.
- **At Risk (19 customers, 14.7% base | ₹196,343.04, 5.2% rev):** Below-average recency and declining frequency.
- **Hibernating (31 customers, 24.0% base | ₹142,976.09, 3.8% rev):** Lapsed buyers with low frequency (avg recency: 192 days).
- **New Customers (5 customers, 3.9% base | ₹85,627.33, 2.3% rev):** High recency (bought <10 days ago), low order count.
- **Potential Loyalists (5 customers, 3.9% base | ₹58,554.95, 1.6% rev):** Recent buyers with average frequency.

### 5.2 Unsupervised K-Means Clustering ($k=4$)
Using log-transformed and standardized RFM features, the optimal cluster count $k=4$ was selected via Elbow Method and Silhouette Analysis (Silhouette Score: **0.4313**):
- **Cluster 0 — Core VIP Champions (42 customers):** Avg spend ₹64,288, avg frequency 15.6 orders, recency 14 days.
- **Cluster 1 — Lapsed / Low-Frequency Buyers (36 customers):** Avg spend ₹4,892, avg frequency 2.1 orders, recency 188 days.
- **Cluster 2 — Steady Mid-Tier Spenders (28 customers):** Avg spend ₹18,450, avg frequency 7.8 orders, recency 32 days.
- **Cluster 3 — Occasional / Developing Buyers (23 customers):** Avg spend ₹9,210, avg frequency 4.5 orders, recency 58 days.

---

## 6. Key Business Findings & Strategic Insights

1. **Severe Revenue Concentration:** Pareto analysis proves that the top **40.3% of customers generate 80.0% of revenue**. Top 20% of customers generate 57.3% of sales.
2. **Second-Purchase Lifetime Multiplier:** Repeat buyers spend **₹32,752.20 vs ₹2,497.05 for one-time buyers** — a **13.1x lifetime spend multiplier**.
3. **Category Profitability Skew:** Beauty (62.8% margin) and Books (57.2% margin) deliver superior gross margin percentages, whereas Electronics (25.4% margin) commands scale but dilutes gross margin.
4. **Loyalty Status Expansion:** Platinum members generate a **₹4,175.23 AOV** (+34.3% higher than Regular members), validating tiered loyalty incentives.
5. **Geographic Balance:** North leads total revenue (₹1,068,592.56, 28.3% share), while East commands the highest average order value (₹3,860.22).
6. **Seasonal Demand Spikes:** Twin annual peaks in April (₹476,871.00, +99.8% MoM) and December (₹336,084.00, +58.5% MoM).
7. **Cross-Category Affinity:** Strong association lift between complementary items (e.g. Electric Blender + Face Cleanser, 2.39x Lift; Blender + Power Bank, 2.24x Lift).
8. **Quantifiable Churn Risk:** 32 repeat-capable customers are overdue for purchase based on personal inter-purchase gaps, and 61 customers across churn-risk RFM cohorts represent ₹704,000+ in historical spend.

---

## 7. Actionable Strategic Recommendations

1. **Implement VIP Retention Concierge:** Protect the 32 Champions and 11 "Can't Lose Them" accounts with priority support, zero-fee expedited shipping, and personalized quarterly gifts.
2. **Automate Second-Order Bridge Nurture:** Trigger automated SMS/email flows 14 days post-first purchase offering a 10% voucher for high-margin categories.
3. **Enforce Cross-Sell Bundling at Checkout:** Configure automated cross-sell carousels pairing low-margin Electronics with high-margin Beauty or Accessories to maintain blended margins >40%.
4. **Execute Win-Back Campaigns for Overdue Customers:** Deploy targeted 15% discount incentives with time limits for the 32 customers identified in the overdue retention audit.

---

## 8. Limitations & Assumptions

- **Synthetic Dataset:** The dataset is synthetically generated to mirror real-world e-commerce dynamics; findings reflect the underlying synthetic distributions.
- **Unit Cost & Margin Assumption:** Unit Cost is estimated via industry-standard COGS heuristics (Electronics: 70%, Beauty: 35%, Clothing: 45%, Books: 40%). Actual manufacturer rebates, shipping overhead, and return rates are omitted.
- **Fixed CLV Lifespan:** Basic CLV assumes a fixed 3.0-year horizon ($AOV \times Frequency \times 3.0$). In production, probabilistic models should dynamically estimate individual churn probability.

---

## 9. Future Analytics Roadmap

1. **Machine Learning Churn Prediction:** Train XGBoost and Random Forest binary classifiers on customer feature vectors to predict 90-day churn probability with SHAP interpretability.
2. **Personalized Collaborative Filtering:** Build an item-item collaborative filtering recommendation engine using implicit matrix factorization (ALS) to serve dynamic web carousels.
3. **Probabilistic CLV Forecasting:** Implement the BG/NBD (Beta-Geometric / Negative Binomial Distribution) and Gamma-Gamma model suite via `lifetimes` to forecast transaction counts and monetary value dynamically.
