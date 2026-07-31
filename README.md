# Customer 360 Analytics Warehouse

## Project Overview

The Customer 360 Analytics Warehouse is an end-to-end data engineering project that combines customer, product, location, channel, and sales data into a centralized PostgreSQL warehouse.

The project demonstrates how raw data from multiple source systems can be extracted, cleaned, transformed, validated, and loaded into a star-schema warehouse for business analytics.

The warehouse supports historical tracking using Slowly Changing Dimension Type 2, incremental loading, surrogate key resolution, data-quality validation, business reporting, and SQL performance optimization.

## Business Problem

Organizations often store customer and transaction data across separate systems such as CRM platforms, product systems, sales applications, location systems, and digital channels.

This makes it difficult to answer business questions such as:

- Who are the highest-value customers?
- Which products generate the most revenue?
- Which sales channels perform best?
- Which regions generate the highest sales?
- How do customer and product attributes change over time?
- Are all fact-table records connected to valid dimension records?

This project solves that problem by building a centralized Customer 360 analytics warehouse.

## Architecture

The pipeline follows this flow:

1. Source data is generated and stored in CSV files.
2. Python extracts the source data.
3. Column names and values are standardized.
4. Duplicate and invalid records are cleaned.
5. Customer and product dimensions are loaded using SCD Type 2.
6. Location and channel dimensions are loaded incrementally.
7. Business keys are resolved into surrogate keys.
8. Sales transactions are loaded into the fact table.
9. PostgreSQL views and SQL queries provide business analytics.
10. Indexes and execution plans are used for performance optimization.

## Tech Stack

- Python
- Pandas
- NumPy
- PostgreSQL
- SQLAlchemy
- Psycopg
- SQL
- VS Code
- pgAdmin
- Git
- GitHub

## Dataset

The generated dataset contains:

- 25,000 customers
- 2,000 products
- 500 locations
- 5 sales channels
- 400,000 sales transactions
- Date records covering 2023 through 2025

## Data Model

The warehouse uses a star schema.

### Dimension Tables

- `warehouse.dim_customer`
- `warehouse.dim_product`
- `warehouse.dim_location`
- `warehouse.dim_channel`
- `warehouse.dim_date`

### Fact Table

- `warehouse.fact_sales`

The fact table stores measurable sales activity and connects to the dimensions through surrogate keys.

## ETL Pipeline

The ETL pipeline contains the following modules:

- `extract.py` — reads source CSV files
- `transform.py` — standardizes columns and cleans records
- `load.py` — loads dimensions and fact data into PostgreSQL
- `scd2.py` — manages historical customer and product records
- `pipeline.py` — coordinates the full ETL process

The pipeline is idempotent, meaning repeated execution does not create duplicate fact records.

## Slowly Changing Dimension Type 2

Customer and product dimensions use SCD Type 2.

When a tracked attribute changes:

1. The current record is expired.
2. `effective_to` is populated.
3. `is_current` becomes false.
4. A new version is inserted.
5. The new version receives a new surrogate key.
6. Historical versions remain available for analysis.

A row hash is used to identify attribute changes efficiently.

## Surrogate Key Resolution

Source sales records contain business identifiers such as:

- `customer_id`
- `product_id`
- `location_id`
- `channel_id`
- `order_date`

Before loading the fact table, the pipeline resolves these values into warehouse surrogate keys:

- `customer_key`
- `product_key`
- `location_key`
- `channel_key`
- `date_key`

This ensures valid relationships between the fact and dimension tables.

## Business Analytics

The project includes SQL queries and reporting views for:

- Total revenue
- Total orders
- Top customers by revenue
- Top products by revenue
- Revenue by category
- Revenue by channel
- Revenue by region
- Monthly revenue trends
- Customer lifetime value
- Customer segmentation
- Inactive customers
- Foreign-key data-quality validation

## Performance Optimization

The fact table contains approximately 400,000 sales records.

Indexes were created on:

- `customer_key`
- `product_key`
- `location_key`
- `channel_key`
- `date_key`

PostgreSQL `EXPLAIN ANALYZE` was used to inspect query execution.

The optimized product revenue query completed in approximately 300 milliseconds and used:

- Parallel sequential scanning
- Hash joins
- Parallel workers
- Hash aggregation
- Top-N sorting

## Data Quality

The project validates:

- Duplicate business keys
- Missing required identifiers
- Missing customer relationships
- Missing product relationships
- Missing location relationships
- Missing channel relationships
- Missing date relationships
- Current SCD records
- Historical SCD records

The final warehouse validation confirmed zero missing foreign-key relationships.

## How to Run the Project

### Clone the repository

```bash
git clone https://github.com/Nitheesh2325/customer-360-analytics-warehouse.git
cd customer-360-analytics-warehouse
```

### Install dependencies

```bash
pip install pandas numpy sqlalchemy psycopg python-dotenv
```

### Create a .env file

```text
CUSTOMER360_DB_PASSWORD=your_postgresql_password
```

### Run the ETL pipeline

```bash
python -m etl.pipeline
```

## Project Structure

```text
customer-360-analytics-warehouse/
│
├── config/
├── data/
│   ├── customers.csv
│   ├── products.csv
│   ├── locations.csv
│   ├── channels.csv
│   └── sales.csv
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ARCHITECTURE_DIAGRAM.md
│   ├── DATA_MODEL.md
│   ├── ENGINEERING_DECISIONS.md
│   ├── ER_DIAGRAM.md
│   ├── INTERVIEW_GUIDE.md
│   ├── PROJECT_CHARTER.md
│   └── PROJECT_JOURNAL.md
│
├── etl/
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   ├── scd2.py
│   └── pipeline.py
│
├── screenshots/
├── scripts/
│   └── generate_large_dataset.py
│
├── sql/
│   ├── business_queries.sql
│   └── views.sql
│
├── tests/
├── .env.example
├── .gitignore
└── README.md