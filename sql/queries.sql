-- ==============================================================================
-- queries.sql
-- ------------------------------------------------------------------------------
-- Purpose:
--   Core analytical SQL queries for Customer Purchase Pattern Analyzer.
--   Executed against the SQLite database (data/processed/retail.db).
--   Utilizes CTEs (Common Table Expressions) and Window Functions (RANK, LAG,
--   running totals, partition shares) to generate business intelligence metrics.
-- ==============================================================================

-- ==============================================================================
-- Query 1: Total Spend and Order Count per Customer
-- Business Value: Identifies customer-level transactional velocity, total
-- cumulative monetary contribution, and average basket size.
-- ==============================================================================
SELECT 
    Customer_ID,
    Customer_Name,
    City,
    Region,
    COUNT(*) AS Order_Count,
    ROUND(SUM(Total_Purchase_Value), 2) AS Total_Spend,
    ROUND(AVG(Total_Purchase_Value), 2) AS Average_Order_Value
FROM transactions
GROUP BY Customer_ID, Customer_Name, City, Region
ORDER BY Total_Spend DESC;


-- ==============================================================================
-- Query 2: Top 5 Cities by Sales Volume with Running Total & Market Share
-- Business Value: Highlights prime geographic clusters and assesses sales
-- concentration across top metro hubs using window functions.
-- ==============================================================================
WITH CitySales AS (
    SELECT 
        City,
        Region,
        COUNT(*) AS Transaction_Count,
        ROUND(SUM(Total_Purchase_Value), 2) AS Total_Sales,
        ROUND(AVG(Total_Purchase_Value), 2) AS Avg_Order_Value
    FROM transactions
    GROUP BY City, Region
)
SELECT 
    RANK() OVER (ORDER BY Total_Sales DESC) AS City_Rank,
    City,
    Region,
    Transaction_Count,
    Total_Sales,
    ROUND(SUM(Total_Sales) OVER (ORDER BY Total_Sales DESC), 2) AS Running_Total_Sales,
    ROUND((Total_Sales * 100.0 / SUM(Total_Sales) OVER ()), 2) AS Sales_Share_Pct
FROM CitySales
ORDER BY City_Rank ASC
LIMIT 5;


-- ==============================================================================
-- Query 3: Monthly Revenue Trend with MoM Growth % and Cumulative YTD Revenue
-- Business Value: Evaluates financial trajectory, seasonal acceleration,
-- and Month-over-Month growth velocity using LAG() and cumulative SUM() windowing.
-- ==============================================================================
WITH MonthlyAgg AS (
    SELECT 
        Year,
        Month,
        Month_Name,
        COUNT(*) AS Order_Count,
        ROUND(SUM(Total_Purchase_Value), 2) AS Monthly_Revenue
    FROM transactions
    GROUP BY Year, Month, Month_Name
)
SELECT 
    Year,
    Month,
    Month_Name,
    Order_Count,
    Monthly_Revenue,
    ROUND(
        COALESCE(
            ((Monthly_Revenue - LAG(Monthly_Revenue, 1) OVER (ORDER BY Year, Month)) * 100.0) 
            / LAG(Monthly_Revenue, 1) OVER (ORDER BY Year, Month),
            0.0
        ), 
        2
    ) AS MoM_Growth_Pct,
    ROUND(SUM(Monthly_Revenue) OVER (ORDER BY Year, Month), 2) AS Cumulative_YTD_Revenue
FROM MonthlyAgg
ORDER BY Year, Month;


-- ==============================================================================
-- Query 4: Revenue by Category and by Region with Regional Share
-- Business Value: Cross-dimensional matrix evaluating category penetration
-- within each geographic region using PARTITION BY window functions.
-- ==============================================================================
WITH CatRegionAgg AS (
    SELECT 
        Region,
        Product_Category,
        COUNT(*) AS Order_Count,
        ROUND(SUM(Total_Purchase_Value), 2) AS Total_Revenue
    FROM transactions
    GROUP BY Region, Product_Category
)
SELECT 
    Region,
    Product_Category,
    Order_Count,
    Total_Revenue,
    ROUND((Total_Revenue * 100.0 / SUM(Total_Revenue) OVER (PARTITION BY Region)), 2) AS Regional_Share_Pct,
    ROUND((Total_Revenue * 100.0 / SUM(Total_Revenue) OVER ()), 2) AS Total_Portfolio_Share_Pct,
    RANK() OVER (PARTITION BY Region ORDER BY Total_Revenue DESC) AS Category_Rank_In_Region
FROM CatRegionAgg
ORDER BY Region, Category_Rank_In_Region;


-- ==============================================================================
-- Query 5: Repeat vs. One-Time Customer Comparison
-- Business Value: Quantifies customer retention health, contrasting order
-- volume, collective revenue, and AOV between new and loyal buyers.
-- ==============================================================================
WITH CustomerOrders AS (
    SELECT 
        Customer_ID,
        COUNT(*) AS Order_Count,
        SUM(Total_Purchase_Value) AS Customer_Spend
    FROM transactions
    GROUP BY Customer_ID
),
ClassifiedCustomers AS (
    SELECT 
        Customer_ID,
        Order_Count,
        Customer_Spend,
        CASE 
            WHEN Order_Count > 1 THEN 'Repeat'
            ELSE 'One-time'
        END AS Customer_Type
    FROM CustomerOrders
)
SELECT 
    Customer_Type,
    COUNT(*) AS Customer_Count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS Customer_Pct,
    ROUND(SUM(Customer_Spend), 2) AS Total_Revenue,
    ROUND(SUM(Customer_Spend) * 100.0 / SUM(SUM(Customer_Spend)) OVER (), 2) AS Revenue_Share_Pct,
    ROUND(AVG(Customer_Spend), 2) AS Avg_Spend_Per_Customer,
    ROUND(SUM(Customer_Spend) / SUM(Order_Count), 2) AS Average_Order_Value
FROM ClassifiedCustomers
GROUP BY Customer_Type
ORDER BY Total_Revenue DESC;


-- ==============================================================================
-- Query 6: Top 10 Customers by Revenue with Portfolio Share & Cumulative Sum
-- Business Value: Focuses executive attention on VIP revenue drivers and
-- measures concentration risk via running totals and portfolio % shares.
-- ==============================================================================
WITH RankedCustomers AS (
    SELECT 
        Customer_ID,
        Customer_Name,
        City,
        Region,
        COUNT(*) AS Order_Count,
        ROUND(SUM(Total_Purchase_Value), 2) AS Total_Revenue
    FROM transactions
    GROUP BY Customer_ID, Customer_Name, City, Region
)
SELECT 
    RANK() OVER (ORDER BY Total_Revenue DESC) AS Revenue_Rank,
    Customer_ID,
    Customer_Name,
    City,
    Region,
    Order_Count,
    Total_Revenue,
    ROUND((Total_Revenue * 100.0 / SUM(Total_Revenue) OVER ()), 2) AS Revenue_Share_Pct,
    ROUND(SUM(Total_Revenue) OVER (ORDER BY Total_Revenue DESC), 2) AS Cumulative_Revenue
FROM RankedCustomers
ORDER BY Revenue_Rank ASC
LIMIT 10;


-- ==============================================================================
-- Query 7: Customers Inactive for 90+ Days (Lapsed / Churn Risk Cohort)
-- Business Value: Pinpoints high-value buyers who haven't purchased within the
-- last quarter, prioritized for win-back outreach based on lifetime spend.
-- ==============================================================================
WITH LatestDatasetDate AS (
    SELECT MAX(Purchase_Date) AS Cutoff_Date FROM transactions
),
CustomerActivity AS (
    SELECT 
        Customer_ID,
        Customer_Name,
        City,
        Region,
        COUNT(*) AS Lifetime_Orders,
        ROUND(SUM(Total_Purchase_Value), 2) AS Lifetime_Spend,
        MAX(Purchase_Date) AS Last_Purchase_Date,
        ROUND(JULIANDAY((SELECT Cutoff_Date FROM LatestDatasetDate)) - JULIANDAY(MAX(Purchase_Date))) AS Days_Inactive
    FROM transactions
    GROUP BY Customer_ID, Customer_Name, City, Region
)
SELECT 
    Customer_ID,
    Customer_Name,
    City,
    Region,
    Lifetime_Orders,
    Lifetime_Spend,
    Last_Purchase_Date,
    CAST(Days_Inactive AS INTEGER) AS Days_Inactive,
    RANK() OVER (ORDER BY Days_Inactive DESC) AS Inactivity_Rank
FROM CustomerActivity
WHERE Days_Inactive >= 90
ORDER BY Lifetime_Spend DESC;


-- ==============================================================================
-- Query 8: Average Order Value & Revenue by RFM Customer Segment
-- Business Value: Assesses segment-level commercial yield by joining transactions
-- with RFM customer segment classifications.
-- ==============================================================================
SELECT 
    c.RFM_Segment,
    COUNT(DISTINCT c.Customer_ID) AS Customer_Count,
    COUNT(t.Purchase_Date) AS Total_Orders,
    ROUND(SUM(t.Total_Purchase_Value), 2) AS Total_Revenue,
    ROUND(AVG(t.Total_Purchase_Value), 2) AS Average_Order_Value,
    ROUND(SUM(t.Total_Purchase_Value) * 100.0 / SUM(SUM(t.Total_Purchase_Value)) OVER (), 2) AS Revenue_Share_Pct
FROM customers c
JOIN transactions t ON c.Customer_ID = t.Customer_ID
GROUP BY c.RFM_Segment
ORDER BY Total_Revenue DESC;
