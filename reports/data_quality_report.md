# Customer 360 Analytics Warehouse

## Data Quality Report

### Pipeline Summary

| Metric | Value |
|---------|-------|
| Tables Processed | 5 |
| Total Records | 25 |
| Records Loaded | 25 |
| Duplicate Records Skipped | 0 (First Run) |
| Duplicate Records Skipped (Re-run) | 25 |
| Failed Records | 0 |

---

## Table Summary

### dim_customer

Rows: 5

Status:
- Loaded Successfully

Checks:
- No duplicate customer_id
- No NULL customer names
- Business key validated

---

### dim_product

Rows: 5

Status:
- Loaded Successfully

Checks:
- No duplicate product_id
- Prices validated
- Categories available

---

### dim_location

Rows: 5

Status:
- Loaded Successfully

Checks:
- Location IDs unique
- Cities populated

---

### dim_channel

Rows: 5

Status:
- Loaded Successfully

Checks:
- Channel IDs unique
- Channel names standardized

---

### fact_sales

Rows: 5

Status:
- Loaded Successfully

Checks:
- Foreign Keys valid
- Total Amount populated
- Customer Keys exist
- Product Keys exist
- Channel Keys exist

---

## ETL Validation

✔ Extraction Successful

✔ Transformation Successful

✔ Cleaning Successful

✔ Loading Successful

✔ Duplicate Prevention Verified

✔ ETL Logging Enabled

---

## Business Validation

Verified Queries

✔ Total Revenue

✔ Total Orders

✔ Average Order Value

✔ Top Customers

✔ Revenue by Category

✔ Revenue by Sales Channel

---

Overall Pipeline Health

🟢 PASS

Production Ready:
YES