import json
import os
import re
import sys
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

try:
    from app import db
    from app.models.models import UnifiedProduct
except ImportError:
    print("Error importing app modules. Make sure you're running this script from the project root.")
    sys.exit(1)

# Mapping dictionaries to standardize characteristics from different vendors
# These mappings will grow as more products are added
CHARACTERISTIC_MAPPING = {
    # General mappings
    "Бренд": "brand",
    "Модель": "model",
    "Гарантия": "warranty",
    "Гарантия продавца / производителя": "warranty",
    
    # GPU specific mappings
    "Видеочипсет": "gpu_model",
    "Графический процессор": "gpu_model",
    "Частота графического процессора": "base_clock",
    "Штатная частота работы видеочипа": "base_clock",
    "Турбочастота": "boost_clock",
    "Техпроцесс": "technology_process",
    "Максимальное разрешение": "max_resolution",
    "Число процессоров (ядер) CUDA": "cuda_cores",
    "Количество универсальных процессоров (ALU)": "cuda_cores",
    "Архитектура графического процессора": "architecture",
    "Микроархитектура": "architecture",
    
    # Memory specific mappings
    "Объем видеопамяти": "memory_size",
    "Тип видеопамяти": "memory_type",
    "Тип памяти": "memory_type",
    "Частота видеопамяти": "memory_clock",
    "Эффективная частота памяти": "memory_clock",
    "Разрядность шины видеопамяти": "memory_bus",
    "Разрядность шины памяти": "memory_bus",
    "Пропускная способность памяти": "memory_bandwidth",
    "Максимальная пропускная способность памяти": "memory_bandwidth",
    
    # Cooling specific mappings
    "Система охлаждения": "cooling_system",
    "Количество вентиляторов": "fan_count",
    "Тип охлаждения": "cooling_type",
    
    # Power specific mappings
    "Рекомендуемая мощность БП": "recommended_psu",
    "Энергопотребление": "power_consumption",
    "Разъемы питания": "power_connectors",
    
    # Motherboard specific mappings
    "Сокет": "socket",
    "Чипсет": "chipset",
    "Форм-фактор": "form_factor",
    "Поддерживаемые процессоры": "supported_cpus",
    
    # CPU specific mappings
    "Сокет процессора": "socket",
    "Количество ядер": "core_count",
    "Количество потоков": "thread_count",
    "Базовая частота процессора": "base_clock",
    "Максимальная частота в режиме Turbo": "boost_clock",
    "Кэш L3": "l3_cache",
    
    # RAM specific mappings
    "Объем оперативной памяти": "memory_size",
    "Тип оперативной памяти": "memory_type",
    "Частота памяти": "memory_clock",
    "Количество модулей в комплекте": "module_count",
    
    # Case specific mappings
    "Форм-фактор материнской платы": "supported_form_factors",
    "Типоразмер корпуса": "case_size",
    "Максимальная длина видеокарты": "max_gpu_length",
    "Максимальная высота кулера": "max_cooler_height",
    
    # Storage specific mappings
    "Объем накопителя": "storage_capacity",
    "Интерфейс подключения": "interface",
    "Скорость чтения": "read_speed",
    "Скорость записи": "write_speed",
    
    # Thickness and size mappings
    "Толщина видеокарты": "thickness",
    "Количество занимаемых слотов расширения": "slots"
}

# Value standardization mappings
VALUE_MAPPING = {
    # Convert various memory size formats to GB
    "memory_size": {
        r"(\d+)\s*ГБ": lambda x: int(x),
        r"(\d+)": lambda x: int(x)
    },
    # Convert various clock speeds to MHz
    "base_clock": {
        r"(\d+)\s*МГц": lambda x: int(x),
        r"(\d+)\s*МГц\s*\((\d+)\s*МГц,\s*в режиме Boost\)": lambda x: int(x)
    },
    "boost_clock": {
        r"(\d+)\s*МГц": lambda x: int(x)
    },
    # Convert memory bus widths to bits
    "memory_bus": {
        r"(\d+)\s*bit": lambda x: int(x),
        r"(\d+)\s*бит": lambda x: int(x)
    },
    # Convert power consumption to watts
    "power_consumption": {
        r"(\d+)\s*Вт": lambda x: int(x),
        r"(\d+)": lambda x: int(x)
    },
    # Convert recommended PSU to watts
    "recommended_psu": {
        r"(\d+)\s*Вт": lambda x: int(x),
        r"(\d+)": lambda x: int(x)
    }
}

def extract_value(value_str, field_name):
    """Extract standardized value from string based on field name"""
    if field_name not in VALUE_MAPPING:
        return value_str
        
    for pattern, converter in VALUE_MAPPING[field_name].items():
        match = re.match(pattern, str(value_str))
        if match:
            return converter(match.group(1))
    
    return value_str

def standardize_characteristics(source_data, vendor):
    """
    Standardize characteristics from different vendors into a unified format
    
    Args:
        source_data (dict): Raw product data from vendor
        vendor (str): Vendor name (e.g., 'citilink', 'dns')
        
    Returns:
        dict: Standardized characteristics
    """
    standardized = {
        "vendor_specific": {},  # Store any vendor-specific data that doesn't map to standard fields
    }
    
    # Extract basic product information
    if vendor.lower() == 'citilink':
        standardized["id"] = source_data.get("id")
        standardized["product_name"] = source_data.get("name")
        standardized["price_discounted"] = source_data.get("price")
        standardized["price_original"] = source_data.get("price_old")
        standardized["rating"] = source_data.get("rating")
        standardized["number_of_reviews"] = source_data.get("reviews")
        standardized["images"] = source_data.get("images", [])
        standardized["product_url"] = source_data.get("url")
        standardized["category"] = [cat.get("name") for cat in source_data.get("categories", [])]
        
        # Determine product type based on category
        product_type = determine_product_type(standardized["category"])
        standardized["product_type"] = product_type
        
        # Process characteristics
        characteristics = {}
        for prop_group in source_data.get("properties", []):
            group_name = prop_group.get("name")
            for prop in prop_group.get("properties", []):
                prop_name = prop.get("name")
                prop_value = prop.get("value")
                
                # Map to standardized field if available
                std_field = CHARACTERISTIC_MAPPING.get(prop_name)
                if std_field:
                    characteristics[std_field] = extract_value(prop_value, std_field)
                else:
                    # Store in vendor-specific section if no mapping exists
                    if group_name not in standardized["vendor_specific"]:
                        standardized["vendor_specific"][group_name] = {}
                    standardized["vendor_specific"][group_name][prop_name] = prop_value
        
    elif vendor.lower() == 'dns':
        standardized["id"] = source_data.get("id")
        standardized["product_name"] = source_data.get("name")
        standardized["price_discounted"] = source_data.get("price_discounted")
        standardized["price_original"] = source_data.get("price_original")
        standardized["rating"] = source_data.get("rating")
        standardized["number_of_reviews"] = source_data.get("number_of_reviews")
        standardized["images"] = source_data.get("images", [])
        standardized["product_url"] = source_data.get("url")
        standardized["category"] = [cat.get("name") for cat in source_data.get("categories", [])]
        
        # Determine product type based on category
        product_type = determine_product_type(standardized["category"])
        standardized["product_type"] = product_type
        
        # Process characteristics
        characteristics = {}
        for group_name, props in source_data.get("characteristics", {}).items():
            for prop in props:
                prop_name = prop.get("title")
                prop_value = prop.get("value")
                
                # Map to standardized field if available
                std_field = CHARACTERISTIC_MAPPING.get(prop_name)
                if std_field:
                    characteristics[std_field] = extract_value(prop_value, std_field)
                else:
                    # Store in vendor-specific section if no mapping exists
                    if group_name not in standardized["vendor_specific"]:
                        standardized["vendor_specific"][group_name] = {}
                    standardized["vendor_specific"][group_name][prop_name] = prop_value
    
    standardized["characteristics"] = characteristics
    return standardized

def determine_product_type(categories):
    """
    Determine product type based on categories
    
    Args:
        categories (list): List of category names
        
    Returns:
        str: Product type (motherboard, processor, graphics_card, etc.)
    """
    category_str = ' '.join(categories).lower()
    
    if any(term in category_str for term in ['материнская плата', 'материнские платы', 'motherboard']):
        return 'motherboard'
    elif any(term in category_str for term in ['процессор', 'процессоры', 'cpu', 'processor']):
        return 'processor'
    elif any(term in category_str for term in ['видеокарта', 'видеокарты', 'gpu', 'graphics card']):
        return 'graphics_card'
    elif any(term in category_str for term in ['блок питания', 'блоки питания', 'power supply']):
        return 'power_supply'
    elif any(term in category_str for term in ['оперативная память', 'память', 'ram', 'memory']):
        return 'ram'
    elif any(term in category_str for term in ['жесткий диск', 'ssd', 'hdd', 'накопитель', 'storage']):
        return 'hard_drive'
    elif any(term in category_str for term in ['кулер', 'охлаждение', 'cooler', 'cooling']):
        return 'cooler'
    elif any(term in category_str for term in ['корпус', 'case', 'корпуса']):
        return 'case'
    else:
        return 'other'

def convert_to_unified_product(standardized_data):
    """
    Convert standardized data to UnifiedProduct model instance
    
    Args:
        standardized_data (dict): Standardized product data
        
    Returns:
        UnifiedProduct: Instance of UnifiedProduct model
    """
    product = UnifiedProduct(
        product_name=standardized_data.get("product_name"),
        price_discounted=standardized_data.get("price_discounted"),
        price_original=standardized_data.get("price_original"),
        rating=standardized_data.get("rating"),
        number_of_reviews=standardized_data.get("number_of_reviews"),
        vendor=standardized_data.get("vendor", "unknown"),
        product_url=standardized_data.get("product_url", ""),
        availability=True,  # Default to available
        product_type=standardized_data.get("product_type", "other")
    )
    
    # Set JSON fields
    product.set_images(standardized_data.get("images", []))
    product.set_characteristics(standardized_data.get("characteristics", {}))
    product.set_category(standardized_data.get("category", []))
    
    return product

def process_file(file_path, vendor):
    """
    Process a JSON file with product data and standardize it
    
    Args:
        file_path (str): Path to JSON file
        vendor (str): Vendor name
        
    Returns:
        list: List of standardized products
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both single product and list of products
        if isinstance(data, list):
            products = data
        else:
            products = [data]
        
        standardized_products = []
        for product in products:
            std_product = standardize_characteristics(product, vendor)
            std_product["vendor"] = vendor
            standardized_products.append(std_product)
            
        return standardized_products
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return []

def save_to_json(standardized_products, output_file):
    """Save standardized products to a JSON file for inspection"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(standardized_products, f, ensure_ascii=False, indent=2)
    print(f"Saved standardized data to {output_file}")

def main():
    """Main function to process files and save to database"""
    # Example usage
    citilink_file = "app/utils/Citi_parser/Товары.json"
    dns_file = "app/utils/DNS_parsing/product_data.json"
    
    # Process files
    print("Processing Citilink data...")
    citilink_products = process_file(citilink_file, "citilink")
    print(f"Found {len(citilink_products)} products from Citilink")
    
    print("Processing DNS data...")
    dns_products = process_file(dns_file, "dns")
    print(f"Found {len(dns_products)} products from DNS")
    
    # Save standardized data to JSON for inspection
    save_to_json(citilink_products + dns_products, "standardized_products.json")
    
    # Convert to UnifiedProduct instances
    unified_products = []
    for product in citilink_products + dns_products:
        unified_product = convert_to_unified_product(product)
        unified_products.append(unified_product)
    
    # Save to database
    print("Saving to database...")
    for product in unified_products:
        db.session.add(product)
    
    try:
        db.session.commit()
        print(f"Successfully added {len(unified_products)} products to database")
    except Exception as e:
        db.session.rollback()
        print(f"Error saving to database: {e}")
        print(str(e))

if __name__ == "__main__":
    main() 