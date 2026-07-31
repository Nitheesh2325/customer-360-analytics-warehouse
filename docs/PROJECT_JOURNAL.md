# Project Journal

## Day 1 — Project Initialization

### Completed

- Created customer-360-analytics-warehouse project.
- Created enterprise folder structure.
- Created architecture and project documentation.
- Selected NovaRetail as the fictional business.
- Selected PostgreSQL as the warehouse.
- Selected a star schema.
- Added CDC to the project scope.
- Added SCD Type 2 to the project scope.
- Added schema mapping and data type standardization.
- Added rejected-record quarantine handling.

### Current Phase

Business and architecture design.

### Next Step

Design source systems and define the star schema tables.

## Day 1 - Data Modeling Started

### Completed

- Defined the warehouse as a star schema.
- Defined the grain of fact_sales as one product per customer order.
- Designed dim_customer.
- Added surrogate and business keys.
- Added CDC row-hash support.
- Added SCD Type 2 history columns.

### Next Step

Design dim_product, dim_date, dim_location, dim_channel, and fact_sales.

## Day 1 - Product Dimension

### Completed

- Designed dim_product.
- Added business and surrogate keys.
- Added audit columns.
- Added CDC row hash support.

### Next Step

Design dim_location.

## Day 1 - Location Dimension

### Completed

- Designed dim_location.
- Added geographical attributes.
- Added business and surrogate keys.
- Added CDC row hash support.
- Added audit columns.

### Next Step

Design dim_channel.

## Day 1 - Channel Dimension

### Completed

- Designed dim_channel.
- Added channel information.
- Added business and surrogate keys.
- Added CDC row hash support.
- Added audit columns.

### Next Step

Design dim_date.

## Day 1 - Date Dimension

### Completed

- Designed dim_date.
- Added calendar attributes.
- Added reporting fields.
- Added primary key.

### Next Step

Design fact_sales.