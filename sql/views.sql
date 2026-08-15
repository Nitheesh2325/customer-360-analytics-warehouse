CREATE OR REPLACE VIEW warehouse.sales_analytics AS

SELECT

    f.sales_key,
    f.order_id,
    d.full_date,
    d.month,
    d.month_name,
    d.year,
    d.is_weekend,

    c.customer_id,
    c.customer_name,
    c.customer_segment,
    c.loyalty_tier,

    p.product_id,
    p.product_name,
    p.category,

    l.city,
    l.state,
    l.country,
    l.region,

    ch.channel_name,
    ch.channel_type,

    f.quantity,
    f.unit_price,
    f.total_amount

FROM warehouse.fact_sales f

JOIN warehouse.dim_customer c
ON f.customer_key = c.customer_key

JOIN warehouse.dim_product p
ON f.product_key = p.product_key

JOIN warehouse.dim_location l
ON f.location_key = l.location_key

JOIN warehouse.dim_channel ch
ON f.channel_key = ch.channel_key

JOIN warehouse.dim_date d
ON f.date_key = d.date_key;

