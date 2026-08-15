# Data Model

Customer360 uses a PostgreSQL star schema. `warehouse.fact_sales` is the fact
table; customer, product, location, channel, and date are dimensions.

## Fact grain

`warehouse.fact_sales` contains one row per source order, identified by the
unique `order_id`. The project does not model order lines. Measures are
`quantity`, `unit_price`, `discount`, and `total_amount`.

| Foreign key | Dimension |
| --- | --- |
| `customer_key` | `dim_customer.customer_key` |
| `product_key` | `dim_product.product_key` |
| `location_key` | `dim_location.location_key` |
| `channel_key` | `dim_channel.channel_key` |
| `date_key` | `dim_date.date_key` |

## SCD Type 2 dimensions

`dim_customer` and `dim_product` preserve versions using the same technical
fields:

| Column | Purpose |
| --- | --- |
| Surrogate key | Unique warehouse version identifier |
| Business key | `customer_id` or `product_id` |
| `row_hash` | Hash of controlled tracked source attributes |
| `effective_from` | Start of the version's effective range |
| `effective_to` | End of the version's effective range; null for a current row |
| `is_current` | Identifies the active version |
| `is_deleted` | Marks a version expired by an operation-marker delete |
| `source_system` | Synthetic source-domain label |
| `created_at`, `updated_at` | Warehouse audit timestamps |

Customer tracked attributes include name, contact and address fields, segment,
loyalty tier, and signup date. Product tracked attributes include name,
category, subcategory, brand, supplier, unit cost, and selling price.

Partial unique indexes enforce at most one current customer row per
`customer_id` and one current product row per `product_id`.

## Stable dimensions

- `dim_location` stores country, state, city, postal code, and region for each
  `location_id`.
- `dim_channel` stores name, type, and platform for each `channel_id`.
- `dim_date` stores one calendar row per date from 2023-01-01 through
  2025-12-31, keyed as `YYYYMMDD`.

Location and channel use repeat-safe insert-on-conflict loading. The date
dimension is populated by the repeat-safe database bootstrap.

## Attribution boundary

During a sales load, customer and product business identifiers resolve to the
dimension versions that are current and active at load time. The fact therefore
does not prove event-time historical attribution to the version effective on
the original order date. Event-time attribution would require an effective
range lookup for each order.

## Integrity and transaction boundary

Primary keys, foreign keys, business-key uniqueness, current-row uniqueness,
measure checks, and fact join indexes protect the model. Each table load uses
its own transaction; the complete pipeline is not one atomic transaction.
Earlier successful table loads and independently persisted rejected records can
remain committed if a later table fails. Repeat-safe loading is the recovery
contract for this local project.

The model supports revenue, order, product, customer, region, channel,
discount, and time-based analysis. It contains no tax measure.
