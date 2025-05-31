# Database Rebuild Guide

This guide explains how to rebuild the database with the new unified product model.

## Overview

Instead of migrating the existing database, we'll rebuild it from scratch with the new schema. This process involves:

1. Dropping all existing tables
2. Creating new tables with the unified product model
3. Importing products from JSON files

## Step 1: Rebuild Database

Run the following command to drop all tables and recreate them with the new schema:

```bash
python -m app.utils.standardization.create_db
```

This will:
- Drop all existing tables
- Create new tables based on the models in `app/models/models.py`
- Create an admin user if it doesn't exist

## Step 2: Import Products

Run the following command to import products from JSON files:

```bash
python -m app.utils.standardization.import_products
```

This will:
- Process product data from Citilink and DNS JSON files
- Standardize the product characteristics
- Save the products to the unified_products table

## Step 3: Test the Database

Run the following command to test the database:

```bash
python -m test_unified_model
```

This will create a test product, add it to the database, and query it to ensure everything is working correctly.

## Advantages of the Unified Product Model

The unified product model offers several advantages:

1. **Flexibility**: You can store any type of component with any set of characteristics
2. **Standardization**: All products use the same format, making it easier to compare and search
3. **Extensibility**: You can easily add support for new product types without changing the database schema
4. **Vendor Independence**: Products from different vendors can be stored in the same table with standardized characteristics

## Troubleshooting

If you encounter any issues during the rebuild process, check the following:

- Make sure all required modules are installed
- Check that the JSON files exist at the specified paths
- Verify that the database connection is working properly
- Look for errors in the console output

If you need to start over, simply run the create_db.py script again to reset the database. 