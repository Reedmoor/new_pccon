# Product Standardization Utilities

This package contains utilities for standardizing product data from different sources (e.g., Citilink, DNS) into a unified format.

## Files

- `standardize.py`: Main module containing functions for standardizing product characteristics
- `create_tables.py`: Script to create the necessary database tables
- `test_standardization.py`: Script to test the standardization process without saving to the database

## Usage

### 1. Create the database tables

```bash
python -m app.utils.standardization.create_tables
```

### 2. Test the standardization process

```bash
python -m app.utils.standardization.test_standardization
```

This will process the product data from both sources, find matching products, and display their standardized characteristics. It will also save the results to `standardized_test.json` for inspection.

### 3. Run the standardization process and save to the database

```bash
python -m app.utils.standardization.standardize
```

This will process the product data from both sources, standardize the characteristics, and save the results to the database.

## Extending the Mappings

To add support for new product types or sources, you can extend the `CHARACTERISTIC_MAPPING` and `VALUE_MAPPING` dictionaries in `standardize.py`.

### Adding a new characteristic mapping

```python
CHARACTERISTIC_MAPPING = {
    # Existing mappings...
    
    # New mappings
    "Новая характеристика": "new_characteristic",
}
```

### Adding a new value standardization rule

```python
VALUE_MAPPING = {
    # Existing mappings...
    
    # New mapping
    "new_characteristic": {
        r"(\d+)\s*единица": lambda x: int(x),
    }
}
```

## Adding Support for a New Source

To add support for a new source, you need to add a new case to the `standardize_characteristics` function in `standardize.py`:

```python
def standardize_characteristics(source_data, vendor):
    # Existing code...
    
    elif vendor.lower() == 'new_vendor':
        standardized["id"] = source_data.get("id")
        standardized["product_name"] = source_data.get("name")
        # Add other fields...
        
        # Process characteristics based on the source's data structure
        characteristics = {}
        # Extract and standardize characteristics...
        
        standardized["characteristics"] = characteristics
    
    # Rest of the function...
``` 