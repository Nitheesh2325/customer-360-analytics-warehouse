# Customer 360 Analytics Warehouse

## Star Schema ER Diagram

```text
                         +----------------------+
                         |     dim_customer     |
                         |----------------------|
                         | customer_key (PK)    |
                         | customer_id          |
                         | customer_name        |
                         | email                |
                         | customer_segment     |
                         | loyalty_tier         |
                         +----------+-----------+
                                    |
                                    |
                                    v
+----------------------+    +-------+--------+    +----------------------+
|     dim_product      |    |    fact_sales  |    |     dim_location     |
|----------------------|    |----------------|    |----------------------|
| product_key (PK)     |<---| product_key FK |--->| location_key (PK)    |
| product_id           |    | customer_key FK|    | location_id          |
| product_name         |    | location_key FK|    | country              |
| category             |    | channel_key FK |    | state                |
| subcategory          |    | date_key FK    |    | city                 |
| brand                |    | order_id       |    | region               |
| unit_cost            |    | quantity       |    +----------------------+
| selling_price        |    | unit_price     |
+----------------------+    | discount       |
                            | total_amount   |
                            +-------+--------+
                                    |
                         +----------+-----------+
                         |                      |
                         v                      v
                +------------------+   +------------------+
                |   dim_channel    |   |     dim_date     |
                |------------------|   |------------------|
                | channel_key (PK) |   | date_key (PK)    |
                | channel_id       |   | full_date        |
                | channel_name     |   | day              |
                | channel_type     |   | month            |
                | platform         |   | quarter          |
                +------------------+   | year             |
                                       | day_name         |
                                       | is_weekend       |
                                       +------------------+
```

## Relationship Summary

- `fact_sales.customer_key` references `dim_customer.customer_key`
- `fact_sales.product_key` references `dim_product.product_key`
- `fact_sales.location_key` references `dim_location.location_key`
- `fact_sales.channel_key` references `dim_channel.channel_key`
- `fact_sales.date_key` references `dim_date.date_key`

This design follows a star schema where the fact table stores measurable business events and dimension tables provide descriptive context.