-- ==============================================================================
-- analysis_queries.sql
-- ------------------------------------------------------------------------------
-- Purpose:
--   Core analytical SQL queries for Customer Purchase Pattern Analyzer.
--   Executed against the SQLite database populated by the analytics pipeline.
-- ==============================================================================

-- 1. Total revenue and order count
SELECT 
    COUNT(DISTINCT purchase_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS total_customers,
    ROUND(SUM(purchase_amount), 2) AS total_revenue,
    ROUND(AVG(purchase_amount), 2) AS average_order_value
FROM transactions;

-- 2. Top 5 product categories by revenue
SELECT 
    product_category,
    COUNT(*) AS total_items_sold,
    ROUND(SUM(purchase_amount), 2) AS category_revenue,
    ROUND(AVG(purchase_amount), 2) AS avg_item_price
FROM transactions
GROUP BY product_category
ORDER BY category_revenue DESC
LIMIT 5;

-- 3. Top 5 cities by sales volume
SELECT 
    city,
    COUNT(*) AS transaction_count,
    ROUND(SUM(purchase_amount), 2) AS total_spend
FROM transactions
GROUP BY city
ORDER BY total_spend DESC
LIMIT 5;

-- 4. Customer spending distribution & repeat buyers
SELECT 
    customer_id,
    COUNT(*) AS purchase_count,
    ROUND(SUM(purchase_amount), 2) AS lifetime_spend,
    ROUND(AVG(purchase_amount), 2) AS avg_order_value
FROM transactions
GROUP BY customer_id
ORDER BY lifetime_spend DESC;
