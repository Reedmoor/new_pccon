# Characteristic Filters Documentation

## Overview

The characteristic filter system standardizes component specifications across different vendors (Citilink, DNS, etc.). Each component type has its own filter class that:

1. **Normalizes characteristic names** - Maps vendor-specific names to standard field names
2. **Normalizes values** - Converts different formats (e.g., "3.2 ГГц" → 3200, "AM5" → "AM5")
3. **Validates required fields** - Ensures critical specifications are present
4. **Filters important fields** - Keeps only relevant characteristics for each component type

## Component Types & Key Characteristics

### 1. **Processor** (processor)

**Required characteristics:**
- `socket` - CPU socket type (LGA1700, AM5, etc.)
- `core_count` - Number of cores
- `base_clock` - Base frequency (normalized to MHz)

**Important characteristics:**
- `socket`
- `core_count`
- `thread_count` - Number of threads
- `base_clock` - Base frequency
- `boost_clock` - Boost frequency (normalized to MHz)
- `l3_cache` - L3 cache size
- `power_consumption` - TDP in watts

**Normalization examples:**
```python
# Socket normalization
"Intel LGA 1700" → "LGA1700"
"AMD Socket AM5" → "AM5"

# Clock normalization
"3.2 ГГц" → 3200 (MHz)
"5.6 GHz" → 5600 (MHz)
```

### 2. **Motherboard** (motherboard)

**Required characteristics:**
- `socket` - CPU socket (LGA1700, AM5, etc.)
- `form_factor` - Motherboard size (ATX, microATX, miniITX, etc.)

**Important characteristics:**
- `socket`
- `form_factor`
- `chipset` - Motherboard chipset
- `memory_type` - Supported RAM type (DDR4, DDR5)
- `memory_form_factor` - RAM form factor (DIMM, SO-DIMM)

**Normalization examples:**
```python
# Form factor normalization
"Micro-ATX" → "microATX"
"MINI-ITX" → "miniITX"

# Memory form factor normalization
"UDIMM" → "DIMM"
"SO-DIMM", "SODIMM", "SO DIMM" → "SO-DIMM"
"Registered DIMM" → "RDIMM"
```

### 3. **Graphics Card** (graphics_card)

**Required characteristics:**
- `gpu_model` - GPU model (RTX 4080, RX 7800 XT, etc.)
- `memory_size` - VRAM size in GB
- `memory_type` - VRAM type (GDDR6, GDDR6X, HBM2, etc.)

**Important characteristics:**
- `gpu_model`
- `architecture` - GPU architecture
- `base_clock` - Base clock (normalized to MHz)
- `boost_clock` - Boost clock (normalized to MHz)
- `memory_size` - VRAM in GB
- `memory_type` - VRAM type
- `memory_bus` - Memory bus width in bits
- `power_consumption` - Power consumption in watts

**Normalization examples:**
```python
# GPU model normalization
"NVIDIA GeForce RTX 4080" → "GeForce RTX 4080"

# Memory type normalization
"GDDR6X", "GDDR6x" → "GDDR6X"
"GDDR6", "GDDR6" → "GDDR6"

# Clock normalization (same as CPU)
"2505 МГц" → 2505
"2.7 GHz" → 2700
```

### 4. **RAM** (ram)

**Required characteristics:**
- `memory_size` - Size in GB
- `memory_type` - RAM type (DDR4, DDR5)
- `memory_form_factor` - Form factor (DIMM, SO-DIMM, etc.)

**Important characteristics:**
- `memory_size` - In GB
- `memory_type` - DDR type
- `memory_form_factor` - DIMM type
- `memory_clock` - Frequency (normalized to MHz)
- `memory_bus` - Bus width in bits

**Normalization examples:**
```python
# Size normalization
"32 ГБ" → 32
"16GB" → 16
"8 GB" → 8

# Type normalization
"DDR5" → "DDR5"
"UDIMM" → "DIMM"
```

### 5. **Hard Drive/SSD** (hard_drive)

**Required characteristics:**
- `storage_capacity` - Capacity in GB (normalized from TB)
- `interface` - Interface type (SATA, NVMe, M.2, etc.)

**Important characteristics:**
- `storage_capacity` - In GB
- `interface` - Connection type
- `read_speed` - Sequential read speed
- `write_speed` - Sequential write speed
- `form_factor` - Physical size

**Normalization examples:**
```python
# Capacity normalization
"2 ТБ" → 2000
"500GB" → 500
"1 TB" → 1000

# Interface normalization
"NVME M.2" → "NVMe"
"M2" → "M.2"
"PCIE" → "PCIe"
```

### 6. **Power Supply** (power_supply)

**Required characteristics:**
- `wattage` - Power supply wattage

**Important characteristics:**
- `wattage` - In watts
- `efficiency_rating` - 80+ rating (Bronze, Gold, Platinum)
- `modular_type` - Modular type
- `connectors` - Power connectors

**Normalization examples:**
```python
# Wattage normalization
"1000 Вт" → 1000
"850W" → 850

# Efficiency normalization
"80+ Gold", "GOLD" → "80+ Gold"
"Platinum" → "80+ Platinum"
```

### 7. **Cooler** (cooler)

**Required characteristics:**
- `cooling_type` - Type (Air, Liquid, Passive)

**Important characteristics:**
- `cooling_type` - Cooling method
- `cooler_height` - Height in mm
- `fan_count` - Number of fans
- `power_consumption` - Power in watts

**Normalization examples:**
```python
# Type normalization
"AIR" → "Air"
"LIQUID" → "Liquid"

# Height normalization
"163 мм" → 163
"160mm" → 160
```

### 8. **Case** (case)

**Required characteristics:**
- `case_size` - Size category (Full Tower, Mid Tower, etc.)

**Important characteristics:**
- `case_size` - Size category
- `supported_form_factors` - Supported MB form factors
- `max_gpu_length` - Max GPU length in mm
- `max_cooler_height` - Max cooler height in mm

**Normalization examples:**
```python
# Size normalization
"Mid Tower" → "Mid Tower"
"Micro-ATX" → "Mid Tower"
"SFF" → "SFF"

# Dimension normalization (to mm)
"330 мм" → 330
"280mm" → 280
```

## Usage

### Apply Filters Automatically

In the standardization pipeline, filters are automatically applied:

```python
from app.utils.standardization.standardize import standardize_characteristics

# Raw data from vendor
raw_product = {
    "name": "Intel Core i7-13700K",
    "price": 299.99,
    "categories": ["Процессоры"],
    "characteristics": {
        "socket": "Intel LGA1700",
        "core_count": "8 P-cores + 8 E-cores",
        "base_clock": "3.4 ГГц",
        # ... other fields
    }
}

# Standardize and apply filters
std_product = standardize_characteristics(raw_product, vendor="citilink")

# Result has normalized characteristics
print(std_product['characteristics']['socket'])  # "LGA1700"
print(std_product['characteristics']['base_clock'])  # 3400 (MHz)
print(std_product['characteristics']['core_count'])  # 16
```

### Apply Filters Manually

```python
from app.utils.standardization.characteristic_filters import apply_filter

characteristics = {
    "socket": "AMD Socket AM5",
    "core_count": "12",
    "base_clock": "3.5 ГГц"
}

filtered = apply_filter('processor', characteristics)
# Result: {'socket': 'AM5', 'core_count': 12, 'base_clock': 3500}
```

### Get Required/Important Characteristics

```python
from app.utils.standardization.characteristic_filters import (
    get_required_characteristics,
    get_important_characteristics
)

required = get_required_characteristics('processor')
# {'socket', 'core_count', 'base_clock'}

important = get_important_characteristics('processor')
# {'socket', 'core_count', 'thread_count', 'base_clock', 'boost_clock', 'l3_cache', 'power_consumption'}
```

### Custom Normalizers

Each filter class has normalizer methods you can call directly:

```python
from app.utils.standardization.characteristic_filters import ProcessorFilter

# Normalize individual values
socket = ProcessorFilter.normalize_socket("Intel LGA 1700")  # "LGA1700"
clock = ProcessorFilter.normalize_clock("3.2 ГГц")  # 3200
cores = ProcessorFilter.normalize_core_count("10 cores")  # 10
```

## Testing

Run the test suite to see filters in action:

```bash
python app/utils/standardization/test_characteristic_filters.py
```

This will show:
- Input values with mixed formats
- Normalized output values
- Required and important characteristics for each type

## Adding New Characteristics

To add support for a new characteristic:

1. **Add to CHARACTERISTIC_MAPPING** in `standardize.py`:
```python
CHARACTERISTIC_MAPPING = {
    # ... existing mappings
    "Частота памяти (внешняя)": "memory_external_frequency",  # New mapping
}
```

2. **Add VALUE_MAPPING** if needed (for format conversion):
```python
VALUE_MAPPING = {
    # ... existing mappings
    "memory_external_frequency": {
        r"(\d+)\s*МГц": lambda x: int(x),
        r"(\d+)\s*MHz": lambda x: int(x),
        # ... patterns
    }
}
```

3. **Update the appropriate Filter class**:
```python
class ProcessorFilter(CharacteristicFilter):
    IMPORTANT_CHARACTERISTICS = {
        # ... existing
        'memory_external_frequency',  # Add new characteristic
    }
    
    @staticmethod
    def filter_characteristics(characteristics):
        """Filter processor characteristics"""
        filtered = {}
        
        important_fields = {
            # ... existing
            'memory_external_frequency': lambda x: ProcessorFilter.normalize_clock(x),
        }
        
        # ... rest of method
```

## Compatibility with Comparison Logic

The normalized values from these filters are compatible with the product comparison system:

- **Socket matching**: Exact matching after normalization
- **Form factor matching**: Normalized names allow accurate comparison
- **Memory type matching**: DDR4 ≠ DDR5, SO-DIMM ≠ DIMM
- **Dimension checking**: All dimensions in mm for reliable comparisons

## Future Enhancements

Potential improvements:

1. **Tolerance-based matching** - Handle similar values (e.g., 3200MHz ≈ 3200MHz)
2. **More value mappings** - Add variant support for less common formats
3. **Validation ranges** - Check if values are within expected ranges
4. **Confidence scoring** - Rate how complete the characteristic data is
5. **Vendor-specific hints** - Store vendor-specific formatting patterns

## Troubleshooting

**Issue: Characteristic not being normalized**
- Check if the characteristic name is in `CHARACTERISTIC_MAPPING`
- Verify it's listed in the filter class's `IMPORTANT_CHARACTERISTICS`
- Run `test_characteristic_filters.py` to debug

**Issue: Incorrect value format**
- Add new patterns to `VALUE_MAPPING` for that field
- Test with `CharacteristicFilter.normalize_value()`

**Issue: Socket name not recognized**
- Add mapping to `ProcessorFilter.normalize_socket()` or `MotherboardFilter.normalize_socket()`

## References

- [standardize.py](./standardize.py) - Main standardization logic
- [characteristic_filters.py](./characteristic_filters.py) - Filter implementations
- [test_characteristic_filters.py](./test_characteristic_filters.py) - Test suite
