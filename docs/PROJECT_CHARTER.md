# Customer 360 Analytics Data Warehouse

## Project Mission

Build an enterprise-style customer analytics data warehouse for a fictional retail company called NovaRetail.

The platform will integrate customer, order, product, location, and marketing data from multiple source systems into a centralized PostgreSQL warehouse.

The project will demonstrate:

- Data warehouse architecture
- Star schema modeling
- Schema mapping
- Data type standardization
- Change Data Capture
- Incremental loading
- Slowly Changing Dimension Type 2
- Data quality validation
- Rejected-record handling
- Business analytics
- Logging and testing

## Business Problem

NovaRetail receives data from multiple systems:

1. CRM system
2. Order management system
3. Product system
4. Marketing platform
5. Customer support system

These systems use different:

- Column names
- Data types
- Date formats
- Customer identifiers
- Currency formats
- Null representations
- Status values

The business currently cannot create a trusted 360-degree customer view.

The warehouse must:

- Standardize source schemas
- Match customer records
- Preserve customer history
- Load only changed data
- Prevent duplicate records
- Store rejected records
- Produce trusted business KPIs

## Primary Business Questions

- Who are the highest-value customers?
- What is customer lifetime value?
- Which customers purchase repeatedly?
- Which regions generate the most revenue?
- Which products and categories perform best?
- How does monthly revenue change?
- Which customer segments are growing?
- Which customers became inactive?
- How have customer addresses or segments changed over time?

## Core Warehouse Tables

### Fact Table

- fact_sales

### Dimension Tables

- dim_customer
- dim_product
- dim_date
- dim_location
- dim_channel

## Advanced Engineering Features

- CDC using updated_at watermarks and row hashes
- SCD Type 2 for customer history
- Source-to-target column mapping
- Data type normalization
- Quarantine table for rejected records
- Audit fields for pipeline traceability
- Incremental and idempotent loading
- PostgreSQL warehouse
- Automated tests
- Pipeline logging

## Success Criteria

The project is successful when:

1. Multiple source datasets are ingested.
2. Source columns are mapped to warehouse standards.
3. Invalid records are quarantined.
4. New and changed customers are detected.
5. Customer history is preserved using SCD Type 2.
6. Fact and dimension tables are populated.
7. Re-running the pipeline does not create duplicates.
8. Business KPIs can be queried from the warehouse.
9. Logs and tests confirm successful execution.
10. The project can be explained confidently in interviews.