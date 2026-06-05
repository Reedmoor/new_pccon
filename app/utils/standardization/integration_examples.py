"""
Integration examples showing how to use characteristic filters in the application.
These examples demonstrate real-world usage patterns.
"""

import json
from app.utils.standardization.standardize import standardize_characteristics, convert_to_unified_product
from app.utils.standardization.characteristic_filters import (
    apply_filter,
    get_required_characteristics,
    get_important_characteristics,
)
from app.models.models import UnifiedProduct


# ============================================================================
# Example 1: Standardize and validate Citilink processor data
# ============================================================================

def example_standardize_citilink_processor():
    """
    Shows how Citilink processor data is standardized and validated
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Standardize Citilink Processor Data")
    print("="*70)
    
    # Raw Citilink processor data
    raw_citilink_processor = {
        "id": "123456",
        "name": "Intel Core i7-13700K",
        "url": "https://www.citilink.ru/product/...",
        "price": 299990,
        "price_old": 349990,
        "rating": 4.8,
        "reviews": 245,
        "images": ["image1.jpg", "image2.jpg"],
        "categories": [{"name": "Процессоры"}],
        "properties": [
            {
                "properties": [
                    {"name": "Сокет процессора", "value": "Intel LGA 1700"},
                    {"name": "Количество ядер", "value": "8 P-cores + 8 E-cores"},
                    {"name": "Количество потоков", "value": "24"},
                    {"name": "Базовая частота процессора", "value": "3.4 ГГц"},
                    {"name": "Максимальная частота в режиме Turbo", "value": "5.4 ГГц"},
                    {"name": "Кэш L3", "value": "30 МБ"},
                    {"name": "Тепловыделение (TDP)", "value": "125 Вт"},
                ]
            }
        ]
    }
    
    # Standardize
    std_data = standardize_characteristics(raw_citilink_processor, vendor="citilink")
    
    print("\nOriginal socket format:", raw_citilink_processor['properties'][0]['properties'][0]['value'])
    print("Standardized socket:", std_data['characteristics'].get('socket'))
    
    print("\nOriginal core count:", raw_citilink_processor['properties'][0]['properties'][1]['value'])
    print("Standardized core count:", std_data['characteristics'].get('core_count'))
    
    print("\nOriginal clock formats:")
    print("  Base:", raw_citilink_processor['properties'][0]['properties'][3]['value'])
    print("  Boost:", raw_citilink_processor['properties'][0]['properties'][4]['value'])
    print("Standardized clock values (MHz):")
    print("  Base:", std_data['characteristics'].get('base_clock'))
    print("  Boost:", std_data['characteristics'].get('boost_clock'))
    
    print("\nProduct type detected:", std_data['product_type'])
    print("Required characteristics present:", 
          all(key in std_data['characteristics'] for key in get_required_characteristics('processor')))


# ============================================================================
# Example 2: Standardize and validate DNS graphics card data
# ============================================================================

def example_standardize_dns_gpu():
    """
    Shows how DNS graphics card data is standardized
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Standardize DNS Graphics Card Data")
    print("="*70)
    
    # Raw DNS graphics card data
    raw_dns_gpu = {
        "id": "gpu_12345",
        "name": "Palit GeForce RTX 5070 Infinity 3 OC",
        "url": "https://www.dns-shop.ru/product/...",
        "price_discounted": 58499,
        "price_original": 0,
        "rating": 4.85,
        "number_of_reviews": 280,
        "categories": [{"name": "Видеокарты"}],
        "characteristics": {
            "Основные параметры": [
                {"title": "Графический процессор", "value": "GeForce RTX 5070"},
                {"title": "Микроархитектура", "value": "NVIDIA Blackwell"},
            ],
            "Спецификации видеопроцессора": [
                {"title": "Штатная частота работы видеочипа", "value": "2325 МГц"},
                {"title": "Турбочастота", "value": "2542 МГц"},
            ],
            "Спецификации видеопамяти": [
                {"title": "Объем видеопамяти", "value": "12 ГБ"},
                {"title": "Тип памяти", "value": "GDDR7"},
                {"title": "Разрядность шины памяти", "value": "192 бит"},
            ]
        }
    }
    
    # Standardize
    std_data = standardize_characteristics(raw_dns_gpu, vendor="dns")
    
    print("\nGPU Model:", std_data['characteristics'].get('gpu_model'))
    print("Architecture:", std_data['characteristics'].get('architecture'))
    print("Memory Size:", std_data['characteristics'].get('memory_size'), "GB")
    print("Memory Type:", std_data['characteristics'].get('memory_type'))
    print("Memory Bus:", std_data['characteristics'].get('memory_bus'), "bit")
    print("Clock speeds (MHz):")
    print("  Base:", std_data['characteristics'].get('base_clock'))
    print("  Boost:", std_data['characteristics'].get('boost_clock'))
    
    print("\nProduct type detected:", std_data['product_type'])
    print("Required characteristics present:", 
          all(key in std_data['characteristics'] for key in get_required_characteristics('graphics_card')))


# ============================================================================
# Example 3: Validate compatibility before purchase suggestion
# ============================================================================

def example_check_compatibility():
    """
    Shows how filters help with compatibility checking
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Use Filtered Data for Compatibility Checking")
    print("="*70)
    
    # Motherboard with normalized characteristics
    motherboard = {
        'socket': 'LGA1700',
        'form_factor': 'ATX',
        'memory_type': 'DDR5',
        'memory_form_factor': 'DIMM',
    }
    
    # CPU with normalized characteristics
    cpu = {
        'socket': 'LGA1700',
        'core_count': 10,
        'power_consumption': 125,
    }
    
    # RAM with normalized characteristics
    ram = {
        'memory_size': 32,
        'memory_type': 'DDR5',
        'memory_form_factor': 'DIMM',
    }
    
    print("\nMotherboard socket:", motherboard['socket'])
    print("CPU socket:", cpu['socket'])
    print("Socket compatibility:", motherboard['socket'] == cpu['socket'])
    
    print("\nMotherboard memory type:", motherboard['memory_type'])
    print("RAM memory type:", ram['memory_type'])
    print("RAM memory form factor:", ram['memory_form_factor'])
    print("RAM type compatibility:", motherboard['memory_type'] == ram['memory_type'])
    print("RAM form factor compatibility:", motherboard['memory_form_factor'] == ram['memory_form_factor'])
    
    print("\nAll required characteristics normalized correctly ✓")


# ============================================================================
# Example 4: Create UnifiedProduct with filtered characteristics
# ============================================================================

def example_create_unified_product():
    """
    Shows how to create a unified product with properly filtered characteristics
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Create UnifiedProduct from Filtered Data")
    print("="*70)
    
    # Start with raw data
    raw_product = {
        "id": "mb_123",
        "name": "ASUS ROG Strix Z790-E Gaming WiFi",
        "price": 599.99,
        "price_old": 699.99,
        "rating": 4.9,
        "reviews": 157,
        "images": ["mb1.jpg"],
        "url": "https://example.com/motherboard",
        "categories": [{"name": "Материнские платы"}],
        "characteristics": {
            "Сокет": "LGA 1700",
            "Форм-фактор": "ATX",
            "Чипсет": "Z790",
            "Тип памяти": "DDR5",
            "Форм-фактор памяти": "DIMM"
        }
    }
    
    # Standardize with vendor-specific parsing
    std_data = standardize_characteristics(raw_product, vendor="generic")
    std_data['vendor'] = 'generic'
    
    print("\nStandardized data:")
    print("Product type:", std_data['product_type'])
    print("Characteristics:")
    for key, value in std_data['characteristics'].items():
        print(f"  {key}: {value}")
    
    # Convert to UnifiedProduct model
    unified_product = convert_to_unified_product(std_data)
    
    print("\nUnifiedProduct created:")
    print("Product name:", unified_product.product_name)
    print("Vendor:", unified_product.vendor)
    print("Product type:", unified_product.product_type)
    print("Price:", unified_product.price_discounted)
    print("Characteristics (parsed):")
    chars = unified_product.get_characteristics()
    for key, value in chars.items():
        print(f"  {key}: {value}")
    
    print("\n✓ UnifiedProduct ready for database storage")


# ============================================================================
# Example 5: Batch process products and filter validation
# ============================================================================

def example_batch_filter_validation():
    """
    Shows how to batch process products and validate their characteristics
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Batch Process and Validate Characteristics")
    print("="*70)
    
    products = [
        {
            "name": "Intel Core i5-13600K",
            "categories": [{"name": "Процессоры"}],
            "characteristics": {
                "socket": "LGA1700",
                "core_count": "6 P-cores + 8 E-cores",
                "base_clock": "3.5 ГГц",
            }
        },
        {
            "name": "AMD Ryzen 7 7700X",
            "categories": [{"name": "Процессоры"}],
            "characteristics": {
                "socket": "Socket AM5",
                "core_count": "8",
                "base_clock": "4.5 GHz",
            }
        },
        {
            "name": "Kingston Fury Beast 32GB DDR5",
            "categories": [{"name": "Оперативная память"}],
            "characteristics": {
                "memory_size": "32 ГБ",
                "memory_type": "DDR5",
                "memory_form_factor": "DIMM",
                "memory_clock": "6000 МГц",
            }
        },
    ]
    
    results = []
    for product in products:
        std_data = standardize_characteristics(product, vendor="mixed")
        product_type = std_data['product_type']
        required_chars = get_required_characteristics(product_type)
        
        # Check if all required characteristics are present
        has_required = all(
            key in std_data['characteristics'] 
            for key in required_chars
        )
        
        results.append({
            'name': product['name'],
            'type': product_type,
            'required_chars': required_chars,
            'has_all_required': has_required,
            'characteristics': std_data['characteristics']
        })
        
        print(f"\n{product['name']}")
        print(f"  Type: {product_type}")
        print(f"  Required: {', '.join(required_chars)}")
        print(f"  Has all required: {'✓' if has_all_required else '✗'}")
        print(f"  Normalized characteristics: {std_data['characteristics']}")


# ============================================================================
# Main
# ============================================================================

def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("CHARACTERISTIC FILTERS - INTEGRATION EXAMPLES")
    print("="*70)
    
    example_standardize_citilink_processor()
    example_standardize_dns_gpu()
    example_check_compatibility()
    example_create_unified_product()
    example_batch_filter_validation()
    
    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED")
    print("="*70)


if __name__ == "__main__":
    main()
