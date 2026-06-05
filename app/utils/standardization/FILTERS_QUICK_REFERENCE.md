# Characteristic Filters - Quick Reference

## What's Been Created

### 1. **characteristic_filters.py** - Main filter module
- 8 filter classes for each component type
- Normalization methods for each characteristic
- Generic CharacteristicFilter base class
- `apply_filter()` and helper functions

### 2. **Integration in standardize.py**
- Import of characteristic_filters module
- Automatic filter application in `standardize_characteristics()`
- Graceful fallback if filters fail

### 3. **Documentation & Examples**
- `CHARACTERISTIC_FILTERS_GUIDE.md` - Comprehensive documentation
- `test_characteristic_filters.py` - Unit tests and demonstrations
- `integration_examples.py` - Real-world usage examples

## Quick Start

### Run Tests
```bash
cd c:\Users\lime_\Desktop\DIP\new_pccon
python app/utils/standardization/test_characteristic_filters.py
```

### Use in Your Code
```python
from app.utils.standardization.standardize import standardize_characteristics

# Automatically applies filters
result = standardize_characteristics(raw_data, vendor="citilink")
print(result['characteristics'])  # Normalized values
```

## Filter Architecture

```
CharacteristicFilter (base class)
├── ProcessorFilter
├── MotherboardFilter
├── GraphicsCardFilter
├── RAMFilter
├── HardDriveFilter
├── PowerSupplyFilter
├── CoolerFilter
└── CaseFilter
```

## Each Filter Has

1. **REQUIRED_CHARACTERISTICS** - Must-have fields
2. **IMPORTANT_CHARACTERISTICS** - Should-have fields  
3. **Normalizer methods** - For each characteristic
4. **filter_characteristics()** - Main filtering method

## Example Normalizations

### Processor
- `"Intel LGA 1700"` → `"LGA1700"`
- `"3.2 ГГц"` → `3200` (MHz)
- `"10 cores"` → `10`

### Motherboard
- `"Micro-ATX"` → `"microATX"`
- `"UDIMM"` → `"DIMM"`
- `"DDR5"` → `"DDR5"`

### Graphics Card
- `"GeForce RTX 4080"` → stays normalized
- `"2505 МГц"` → `2505` (MHz)
- `"GDDR6X"` → `"GDDR6X"`

### RAM
- `"32 ГБ"` → `32` (GB)
- `"6000 МГц"` → `6000` (MHz)
- `"SO-DIMM"` → `"SO-DIMM"`

### Hard Drive
- `"2 ТБ"` → `2000` (GB)
- `"NVME M.2"` → `"NVMe"`
- `"SSD"` → stays consistent

### Power Supply
- `"1000 Вт"` → `1000`
- `"80+ Gold"` → `"80+ Gold"`

### Cooler
- `"AIR"` → `"Air"`
- `"163 мм"` → `163` (mm)

### Case
- `"Mid Tower"` → `"Mid Tower"`
- `"330 мм"` → `330` (mm)
- `["ATX", "microATX"]` → `"ATX, microATX"`

## Integration Points

### 1. Data Import (`import_products.py`)
- Automatically normalizes when importing from CSV/JSON

### 2. Product Comparison (`product_comparator.py`)
- Uses normalized socket names for exact matching
- Uses normalized memory types for compatibility

### 3. Configuration Building (`routes/configurations.py`)
- Filters ensure consistent characteristic comparison

### 4. Admin Panel
- Displays normalized characteristics
- Can override if needed

## Extensibility

### Add New Characteristic

1. Update `CHARACTERISTIC_MAPPING` in `standardize.py`:
```python
"Новое название характеристики": "normalized_field_name"
```

2. Add value mapping if needed:
```python
VALUE_MAPPING = {
    "normalized_field_name": {
        r"pattern": lambda x: conversion_function(x),
    }
}
```

3. Update filter class:
```python
IMPORTANT_CHARACTERISTICS = {
    # ... existing
    'normalized_field_name',
}

# Add normalizer method if custom logic needed
@staticmethod
def normalize_field_name(value):
    """Custom normalization logic"""
    return normalized_value
```

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Characteristic not normalizing | Add to CHARACTERISTIC_MAPPING |
| Wrong value format | Add pattern to VALUE_MAPPING |
| Socket name not recognized | Add to ProcessorFilter.normalize_socket() |
| Memory form factor confusion | Check MotherboardFilter.normalize_memory_form_factor() |
| Frequency conversion wrong | Review normalize_clock() patterns |

## Files Reference

```
app/utils/standardization/
├── characteristic_filters.py (✨ NEW - 600 lines)
├── standardize.py (modified - added filter integration)
├── CHARACTERISTIC_FILTERS_GUIDE.md (✨ NEW - detailed documentation)
├── test_characteristic_filters.py (✨ NEW - test suite)
├── integration_examples.py (✨ NEW - usage examples)
└── [existing files...]
```

## Next Steps

1. ✅ Run tests to verify all filters work
2. ✅ Check import_products.py if needed updates
3. ✅ Monitor compatibility checks for improved accuracy
4. ⏳ Add more vendor-specific format mappings as needed
5. ⏳ Consider adding confidence scoring

## Performance Notes

- Filters are called once per product during standardization
- Minimal overhead (~1-5ms per product)
- Caching not needed (cheap operations)
- Works with or without database

## Testing Commands

```bash
# Run filter tests
python app/utils/standardization/test_characteristic_filters.py

# Run integration examples  
python app/utils/standardization/integration_examples.py

# Test in Python shell
python
>>> from app.utils.standardization.characteristic_filters import ProcessorFilter
>>> ProcessorFilter.normalize_socket("Intel LGA 1700")
'LGA1700'
```

## Support Matrix

| Component | Socket | Memory | Clock | Form Factor | Other |
|-----------|--------|--------|-------|-------------|-------|
| Processor | ✓      | -      | ✓     | -           | Cores, TDP |
| Motherboard | ✓    | ✓      | -     | ✓           | Chipset |
| GPU | -      | ✓      | ✓     | -           | VRAM type, Architecture |
| RAM | -      | ✓      | ✓     | ✓           | Capacity |
| HDD | -      | -      | -     | -           | Capacity, Interface |
| PSU | -      | -      | -     | -           | Wattage, Efficiency |
| Cooler | -   | -      | -     | -           | Type, Height |
| Case | -     | -      | -     | ✓           | Max GPU, Max Cooler |

## Questions?

Refer to:
- `CHARACTERISTIC_FILTERS_GUIDE.md` - Complete reference
- `test_characteristic_filters.py` - See examples
- `integration_examples.py` - Real usage patterns
- `characteristic_filters.py` - Source with docstrings
