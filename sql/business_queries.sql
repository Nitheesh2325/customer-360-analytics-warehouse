/*
============================================================
Customer 360 Analytics Warehouse
Business Analytics Queries
============================================================

Purpose:
Provide business-facing analytics using the
warehouse.sales_analytics view.

The view hides complex warehouse joins and exposes
clean analytical columns for reporting.

Direct warehouse-table queries are still used for:
- row-count validation
- average order value
- foreign-key relationship validation
============================================================
*/


-- =========================================================
-- 1. Total Revenue
-- =========================================================

SELECT
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM warehouse.sales_analytics;


-- =========================================================
-- 2. Total Orders
-- =========================================================

SELECT
    COUNT(*) AS total_orders
FROM warehouse.sales_analytics;


-- =========================================================
-- 3. Top 10 Customers by Revenue
-- =========================================================

SELECT
    customer_id,
    customer_name,
    COUNT(*) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM warehouse.sales_analytics
GROUP BY
    customer_id,
    customer_name
ORDER BY total_revenue DESC
LIMIT 10;


-- =========================================================
-- 4. Top 10 Products by Revenue
-- =========================================================

SELECT
    product_id,
    product_name,
    category,
    SUM(quantity) AS units_sold,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM warehouse.sales_analytics
GROUP BY
    product_id,
    product_name,
    category
ORDER BY total_revenue DESC
LIMIT 10;


-- =========================================================
-- 5. Revenue by Product Category
-- =========================================================

SELECT
    category,
    COUNT(*) AS total_orders,
    SUM(quantity) AS units_sold,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM warehouse.sales_analytics
GROUP BY category
ORDER BY total_revenue DESC;


-- =========================================================
-- 6. Revenue by Sales Channel
-- =========================================================

SELECT
    channel_name,
    channel_type,
    COUNT(*) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM warehouse.sales_analytics
GROUP BY
    channel_name,
    channel_type
ORDER BY total_revenue DESC;


-- =========================================================
-- 7. Revenue by Region
-- =========================================================

SELECT
    region,
    country,
    COUNT(*) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM warehouse.sales_analytics
GROUP BY
    region,
    country
ORDER BY total_revenue DESC;


-- =========================================================
-- 8. Monthly Revenue Trend
-- =========================================================

SELECT
    year,
    month,
    month_name,
    COUNT(*) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM warehouse.sales_analytics
GROUP BY
    year,
    month,
    month_name
ORDER BY
    year,
    month;


-- =========================================================
-- 9. Customer Segment Performance
-- =========================================================

SELECT
    customer_segment,
    COUNT(DISTINCT customer_id) AS customer_count,
    COUNT(*) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS average_order_value
FROM warehouse.sales_analytics
GROUP BY customer_segment
ORDER BY total_revenue DESC;


-- =========================================================
-- 10. Loyalty Tier Performance
-- =========================================================

SELECT
    loyalty_tier,
    COUNT(DISTINCT customer_id) AS customer_count,
    COUNT(*) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM warehouse.sales_analytics
GROUP BY loyalty_tier
ORDER BY total_revenue DESC;


-- =========================================================
-- 11. Average Order Value
-- =========================================================

SELECT
    ROUND(AVG(total_amount), 2) AS average_order_value
FROM warehouse.sales_analytics;


-- =========================================================
-- 12. Revenue by Year
-- =========================================================

SELECT
    year,
    COUNT(*) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM warehouse.sales_analytics
GROUP BY year
ORDER BY year;


-- =========================================================
-- 13. Revenue by State
-- =========================================================

SELECT
    state,
    country,
    COUNT(*) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM warehouse.sales_analytics
GROUP BY
    state,
    country
ORDER BY total_revenue DESC;


-- =========================================================
-- 14. Highest Average-Value Customers
-- =========================================================

SELECT
    customer_id,
    customer_name,
    COUNT(*) AS total_orders,
    ROUND(AVG(total_amount), 2) AS average_order_value,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM warehouse.sales_analytics
GROUP BY
    customer_id,
    customer_name
HAVING COUNT(*) >= 5
ORDER BY average_order_value DESC
LIMIT 10;


-- =========================================================
-- 15. Repeat Customers
-- =========================================================

SELECT
    customer_id,
    customer_name,
    COUNT(*) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM warehouse.sales_analytics
GROUP BY
    customer_id,
    customer_name
HAVING COUNT(*) > 1
ORDER BY total_orders DESC, total_revenue DESC
LIMIT 20;


-- =========================================================
-- 16. Weekend vs Weekday Revenue
-- =========================================================

SELECT
    CASE
        WHEN is_weekend = TRUE THEN 'Weekend'
        ELSE 'Weekday'
    END AS day_type,
    COUNT(*) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS average_order_value
FROM warehouse.sales_analytics
GROUP BY is_weekend
ORDER BY total_revenue DESC;


-- =========================================================
-- 17. Warehouse Table Row Counts
-- =========================================================

SELECT
    'dim_customer' AS table_name,
    COUNT(*) AS total_rows
FROM warehouse.dim_customer

UNION ALL

SELECT
    'dim_product',
    COUNT(*)
FROM warehouse.dim_product

UNION ALL

SELECT
    'dim_location',
    COUNT(*)
FROM warehouse.dim_location

UNION ALL

SELECT
    'dim_channel',
    COUNT(*)
FROM warehouse.dim_channel

UNION ALL

SELECT
    'dim_date',
    COUNT(*)
FROM warehouse.dim_date

UNION ALL

SELECT
    'fact_sales',
    COUNT(*)
FROM warehouse.fact_sales;


-- =========================================================
-- 18. Warehouse Relationship Validation
-- =========================================================

SELECT
    COUNT(*) AS total_sales_rows,

    COUNT(*) FILTER (
        WHERE c.customer_key IS NULL
    ) AS missing_customer_keys,

    COUNT(*) FILTER (
        WHERE p.product_key IS NULL
    ) AS missing_product_keys,

    COUNT(*) FILTER (
        WHERE l.location_key IS NULL
    ) AS missing_location_keys,

    COUNT(*) FILTER (
        WHERE ch.channel_key IS NULL
    ) AS missing_channel_keys,

    COUNT(*) FILTER (
        WHERE d.date_key IS NULL
    ) AS missing_date_keys

FROM warehouse.fact_sales f

LEFT JOIN warehouse.dim_customer c
    ON f.customer_key = c.customer_key

LEFT JOIN warehouse.dim_product p
    ON f.product_key = p.product_key

LEFT JOIN warehouse.dim_location l
    ON f.location_key = l.location_key

LEFT JOIN warehouse.dim_channel ch
    ON f.channel_key = ch.channel_key

LEFT JOIN warehouse.dim_date d
    ON f.date_key = d.date_key;


-- =========================================================
-- 19. SCD Type 2 Customer History Validation
-- =========================================================

SELECT
    customer_id,
    customer_name,
    customer_segment,
    loyalty_tier,
    effective_from,
    effective_to,
    is_current
FROM warehouse.dim_customer
WHERE customer_id IN (
    SELECT customer_id
    FROM warehouse.dim_customer
    GROUP BY customer_id
    HAVING COUNT(*) > 1
)
ORDER BY
    customer_id,
    effective_from;


-- =========================================================
-- 20. SCD Type 2 Product History Validation
-- =========================================================

SELECT
    product_id,
    product_name,
    category,
    selling_price,
    effective_from,
    effective_to,
    is_current
FROM warehouse.dim_product
WHERE product_id IN (
    SELECT product_id
    FROM warehouse.dim_product
    GROUP BY product_id
    HAVING COUNT(*) > 1
)
ORDER BY
    product_id,
    effective_from;