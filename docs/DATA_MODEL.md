# Customer 360 Analytics Warehouse - Data Model

## Warehouse Design

The warehouse uses a star schema.

### Fact Table

- fact_sales

### Dimension Tables

- dim_customer
- dim_product
- dim_date
- dim_location
- dim_channel

## Table Grain

### fact_sales

One row represents one product sold within one customer order.

This means one order containing three products creates three rows in fact_sales.

## dim_customer

Purpose:

Stores customer information and preserves historical customer changes using Slowly Changing Dimension Type 2.

Columns:

| Column | PostgreSQL Type | Purpose |
|---|---|---|
| customer_key | BIGSERIAL | Warehouse surrogate primary key |
| customer_id | INTEGER | Customer business identifier from source systems |
| customer_name | VARCHAR(150) | Standardized customer name |
| email | VARCHAR(255) | Customer email |
| phone | VARCHAR(30) | Customer phone |
| address | VARCHAR(255) | Customer street address |
| city | VARCHAR(100) | Customer city |
| state | VARCHAR(100) | Customer state |
| country | VARCHAR(100) | Customer country |
| customer_segment | VARCHAR(50) | Customer business segment |
| loyalty_tier | VARCHAR(50) | Customer loyalty level |
| signup_date | DATE | Customer registration date |
| row_hash | VARCHAR(64) | Detects attribute changes |
| effective_from | TIMESTAMP | Beginning of this customer version |
| effective_to | TIMESTAMP | End of this customer version |
| is_current | BOOLEAN | Identifies the active version |
| source_system | VARCHAR(50) | Originating source system |
| created_at | TIMESTAMP | Warehouse insert timestamp |
| updated_at | TIMESTAMP | Warehouse update timestamp |

Primary Key:

- customer_key

Business Key:

- customer_id

## dim_product

### Purpose

Stores standardized product information for analytics.

This dimension tracks product attributes and supports future product analysis.

| Column | PostgreSQL Type | Purpose |
|---------|-----------------|---------|
| product_key | BIGSERIAL | Warehouse surrogate primary key |
| product_id | INTEGER | Product business identifier |
| product_name | VARCHAR(150) | Standardized product name |
| category | VARCHAR(100) | Product category |
| subcategory | VARCHAR(100) | Product subcategory |
| brand | VARCHAR(100) | Product brand |
| supplier | VARCHAR(100) | Product supplier |
| unit_cost | NUMERIC(10,2) | Product cost |
| selling_price | NUMERIC(10,2) | Selling price |
| row_hash | VARCHAR(64) | Detects attribute changes |
| source_system | VARCHAR(50) | Source system |
| created_at | TIMESTAMP | Warehouse insert timestamp |
| updated_at | TIMESTAMP | Warehouse update timestamp |

Primary Key:

- product_key

## dim_location

### Purpose

Stores standardized geographical information for customers, stores, and sales reporting.

| Column | PostgreSQL Type | Purpose |
|---------|-----------------|---------|
| location_key | BIGSERIAL | Warehouse surrogate primary key |
| location_id | INTEGER | Business identifier from source systems |
| country | VARCHAR(100) | Country |
| state | VARCHAR(100) | State or province |
| city | VARCHAR(100) | City |
| postal_code | VARCHAR(20) | ZIP or postal code |
| region | VARCHAR(100) | Sales region |
| row_hash | VARCHAR(64) | Detects attribute changes |
| source_system | VARCHAR(50) | Source application |
| created_at | TIMESTAMP | Warehouse insert timestamp |
| updated_at | TIMESTAMP | Warehouse update timestamp |

Primary Key:

- location_key

Business Key:

- location_id

## dim_channel

### Purpose

Stores the sales channel information used to identify where each order originated.

Examples include online, mobile app, physical store, marketplace, and partner channels.

| Column | PostgreSQL Type | Purpose |
|---------|-----------------|---------|
| channel_key | BIGSERIAL | Warehouse surrogate primary key |
| channel_id | INTEGER | Business identifier from source systems |
| channel_name | VARCHAR(100) | Sales channel name |
| channel_type | VARCHAR(100) | Type of sales channel |
| platform | VARCHAR(100) | Platform or application name |
| row_hash | VARCHAR(64) | Detects attribute changes |
| source_system | VARCHAR(50) | Originating source system |
| created_at | TIMESTAMP | Warehouse insert timestamp |
| updated_at | TIMESTAMP | Warehouse update timestamp |

Primary Key:

- channel_key

Business Key:

- channel_id

## dim_date

### Purpose

Stores calendar information for reporting and time-based analytics.

| Column | PostgreSQL Type | Purpose |
|---------|-----------------|---------|
| date_key | INTEGER | Warehouse date key (YYYYMMDD) |
| full_date | DATE | Calendar date |
| day | SMALLINT | Day of month |
| month | SMALLINT | Month number |
| month_name | VARCHAR(20) | Month name |
| quarter | SMALLINT | Quarter |
| year | SMALLINT | Year |
| week_number | SMALLINT | Week number |
| day_name | VARCHAR(20) | Day name |
| is_weekend | BOOLEAN | Weekend indicator |
| created_at | TIMESTAMP | Warehouse record creation timestamp |
| updated_at | TIMESTAMP | Warehouse record last update timestamp |

Primary Key:

- date_key


## fact_sales

### Purpose

Stores every sales transaction in the warehouse.

Each row represents one completed sale made by a customer.

This table connects all dimension tables and contains the measurable business values used for reporting and analytics.

### Columns

| Column | PostgreSQL Type | Purpose |
|---|---|---|
| sales_key | BIGSERIAL | Surrogate primary key for each warehouse sales record |
| order_id | VARCHAR(50) | Original order identifier from the source system |
| customer_key | BIGINT | Foreign key to dim_customer |
| product_key | BIGINT | Foreign key to dim_product |
| location_key | BIGINT | Foreign key to dim_location |
| channel_key | BIGINT | Foreign key to dim_channel |
| date_key | INTEGER | Foreign key to dim_date |
| quantity | INTEGER | Number of units sold |
| unit_price | NUMERIC(12,2) | Selling price for one unit |
| discount_amount | NUMERIC(12,2) | Discount applied to the sale |
| tax_amount | NUMERIC(12,2) | Tax charged on the sale |
| gross_amount | NUMERIC(14,2) | Amount before discount |
| net_amount | NUMERIC(14,2) | Final amount after discount and tax |
| source_system | VARCHAR(50) | Source system that produced the record |
| created_at | TIMESTAMP | Warehouse record creation timestamp |
| updated_at | TIMESTAMP | Warehouse record last update timestamp |

Primary Key:

- sales_key

Foreign Keys:

- customer_key → dim_customer.customer_key
- product_key → dim_product.product_key
- location_key → dim_location.location_key
- channel_key → dim_channel.channel_key
- date_key → dim_date.date_key


### Grain

The grain of the fact_sales table is:

**One row represents one product sold in one completed customer order.**

Example:

Order ID: ORD1001

| Product | Quantity |
|---------|----------|
| Laptop | 1 |
| Mouse | 2 |
| Keyboard | 1 |

This order generates **three rows** in fact_sales because each product line is stored separately.


### Business Purpose

The fact_sales table stores measurable business events.

It is used to answer business questions such as:

- Total revenue
- Monthly sales
- Best-selling products
- Customer Lifetime Value (CLV)
- Sales by region
- Sales by channel
- Average Order Value (AOV)
- Discount analysis
- Tax analysis