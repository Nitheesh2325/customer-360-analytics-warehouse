# Engineering Decisions

## Decision 001 — Use PostgreSQL

### Decision

PostgreSQL will be used as the warehouse database.

### Reason

PostgreSQL is more realistic than SQLite for a warehouse portfolio project because it supports:

- Strong data types
- Constraints
- Indexes
- Transactions
- Upserts
- Multiple schemas
- Better concurrency
- Production-style SQL

### Alternative Considered

SQLite

### Why Not Selected

SQLite was already used in RetailSync. This project must demonstrate a more enterprise-oriented database.

---

## Decision 002 — Use a Star Schema

### Decision

The warehouse will use:

- fact_sales
- dim_customer
- dim_product
- dim_date
- dim_location
- dim_channel

### Reason

A star schema simplifies analytical queries and separates measurable business events from descriptive attributes.

---

## Decision 003 — Implement CDC

### Decision

The pipeline will process only new or changed records after the initial load.

### Detection Methods

- updated_at watermark
- business key comparison
- row hash comparison

### Reason

Reloading the entire dataset is inefficient and unrealistic for production pipelines.

---

## Decision 004 — Implement SCD Type 2

### Decision

dim_customer will preserve historical customer changes.

### Tracked Changes

- address
- city
- state
- customer segment
- loyalty tier
- email status

### Reason

The business must analyze customer behavior using the customer attributes that were valid at the time.

---

## Decision 005 — Implement Schema Mapping

### Decision

Source column names will be mapped to warehouse-standard names.

### Example

- CustomerID -> customer_id
- CustName -> customer_name
- SignupDate -> signup_date
- TotalSpend -> total_spend

### Reason

Different source systems commonly use inconsistent naming conventions.

---

## Decision 006 — Implement Data Type Standardization

### Decision

Source values will be converted to warehouse-required data types.

### Examples

- "00125" -> 125
- "$1,245.50" -> 1245.50
- "07/14/2026" -> 2026-07-14
- "Yes" -> TRUE
- "NULL" -> SQL NULL

### Reason

A warehouse must enforce consistent types before analytics.

---

## Decision 007 — Use a Quarantine Layer

### Decision

Invalid records will not be silently deleted.

They will be stored with:

- source system
- record identifier
- rejection reason
- rejected timestamp
- raw payload

### Reason

Rejected records must remain traceable for debugging and auditing.