import sys
from pathlib import Path
import json
import os
import glob
import traceback

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

try:
    from app import db, create_app
    from app.models.models import UnifiedProduct
    from app.utils.standardization.standardize import (
        process_file,
        convert_to_unified_product
    )
except ImportError:
    print("Error importing app modules. Make sure you're running this script from the project root.")
    sys.exit(1)

def import_products():
    """Import products from JSON files"""
    app = create_app()
    with app.app_context():
        # Define paths to Citilink category JSON files
        citilink_data_dir = "app/utils/Citi_parser/data"
        citilink_files = glob.glob(os.path.join(citilink_data_dir, "*", "Товары.json"))
        
        if not citilink_files:
            print(f"Error: No category files found in {citilink_data_dir}")
            return
        
        # DNS files - main file and category-specific files
        dns_file = "app/utils/DNS_parsing/product_data.json"
        dns_category_dir = "app/utils/DNS_parsing/categories"
        dns_category_files = []
        
        # Check if the categories directory exists and get all product_data_*.json files
        if os.path.exists(dns_category_dir):
            dns_category_files = glob.glob(os.path.join(dns_category_dir, "product_data_*.json"))
            print(f"Найдено {len(dns_category_files)} категорий продуктов DNS")
        
        # Verify main DNS file exists
        if not os.path.exists(dns_file) and not dns_category_files:
            print(f"Error: No DNS product files found")
            return
        
        # Process Citilink files
        citilink_products = []
        for file in citilink_files:
            try:
                print(f"Обработка данных Citilink из {file}...")
                products = process_file(file, "citilink")
                print(f"Найдено {len(products)} продуктов в {file}")
                citilink_products.extend(products)
            except Exception as e:
                print(f"Error processing file {file}: {str(e)}")
                continue
        print(f"Всего продуктов Citilink: {len(citilink_products)}")
        
        # Process DNS files
        dns_products = []
        
        # First try to process category-specific files
        for file in dns_category_files:
            try:
                category_name = os.path.basename(file).replace('product_data_', '').replace('.json', '')
                print(f"Обработка данных DNS из категории {category_name}...")
                products = process_file(file, "dns")
                print(f"Найдено {len(products)} продуктов в категории {category_name}")
                dns_products.extend(products)
            except Exception as e:
                print(f"Error processing DNS category file {file}: {str(e)}")
                continue
        
        # If no category files were processed or they were empty, try the main file
        if not dns_products and os.path.exists(dns_file):
            try:
                print("Обработка основного файла DNS...")
                products = process_file(dns_file, "dns")
                print(f"Найдено {len(products)} продуктов в основном файле DNS")
                dns_products.extend(products)
            except Exception as e:
                print(f"Error processing main DNS file: {str(e)}")
        
        print(f"Всего продуктов DNS: {len(dns_products)}")
        
        # Save to database
        print("Сохранение в базу данных...")
        
        # Clear existing products first
        try:
            print("Удаление существующих продуктов...")
            db.session.query(UnifiedProduct).delete()
            db.session.commit()
        except Exception as e:
            print(f"Ошибка при удалении существующих продуктов: {str(e)}")
            db.session.rollback()
        
        # Convert to UnifiedProduct instances and save one by one
        added_count = 0
        error_count = 0
        
        all_products = citilink_products + dns_products
        print(f"Всего продуктов для импорта: {len(all_products)}")
        
        for idx, product_data in enumerate(all_products):
            try:
                # Ensure all required characteristics for compatibility checks are present
                ensure_compatibility_characteristics(product_data)
                
                # Convert data to UnifiedProduct
                unified_product = convert_to_unified_product(product_data)
                
                # Add to session
                db.session.add(unified_product)
                
                # Commit every 100 products to avoid memory issues
                if idx % 100 == 0:
                    db.session.commit()
                    print(f"Сохранено {idx} продуктов...")
                
                added_count += 1
            except Exception as e:
                error_count += 1
                print(f"Ошибка при сохранении продукта {idx}: {str(e)}")
                # Print the problematic product data for debugging
                print(f"Проблемные данные: {product_data.get('product_name', 'No name')}")
                traceback.print_exc()
                
                # Rollback and continue
                db.session.rollback()
        
        # Final commit
        try:
            db.session.commit()
            print(f"Успешно добавлено {added_count} продуктов в базу данных. Ошибок: {error_count}")
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка сохранения в базу данных: {str(e)}")
            traceback.print_exc()

def ensure_compatibility_characteristics(product_data):
    """
    Ensure all required characteristics for compatibility checks are present
    
    Args:
        product_data (dict): Standardized product data
    """
    characteristics = product_data.get("characteristics", {})
    product_type = product_data.get("product_type", "other")
    
    # Define default values based on product type
    if product_type == 'motherboard':
        if 'socket' not in characteristics:
            characteristics['socket'] = ''
        if 'form_factor' not in characteristics:
            characteristics['form_factor'] = ''
        if 'memory_type' not in characteristics:
            characteristics['memory_type'] = ''
            
    elif product_type == 'processor':
        if 'socket' not in characteristics:
            characteristics['socket'] = ''
        if 'power_consumption' not in characteristics:
            characteristics['power_consumption'] = 0
        if 'core_count' not in characteristics:
            characteristics['core_count'] = 0
        if 'thread_count' not in characteristics:
            characteristics['thread_count'] = 0
            
    elif product_type == 'graphics_card':
        if 'power_consumption' not in characteristics:
            characteristics['power_consumption'] = 0
        if 'length' not in characteristics:
            characteristics['length'] = 0
        if 'memory_size' not in characteristics:
            characteristics['memory_size'] = 0
            
    elif product_type == 'ram':
        if 'memory_type' not in characteristics:
            characteristics['memory_type'] = ''
        if 'memory_size' not in characteristics:
            characteristics['memory_size'] = 0
            
    elif product_type == 'power_supply':
        if 'wattage' not in characteristics:
            characteristics['wattage'] = 0
            
    elif product_type == 'cooler':
        if 'cooler_height' not in characteristics:
            characteristics['cooler_height'] = 0
            
    elif product_type == 'case':
        if 'supported_form_factors' not in characteristics:
            characteristics['supported_form_factors'] = []
        if 'max_gpu_length' not in characteristics:
            characteristics['max_gpu_length'] = 0
        if 'max_cooler_height' not in characteristics:
            characteristics['max_cooler_height'] = 0
            
    elif product_type == 'hard_drive':
        if 'storage_capacity' not in characteristics:
            characteristics['storage_capacity'] = 0
            
    # Update the product data with the ensured characteristics
    product_data["characteristics"] = characteristics

if __name__ == "__main__":
    import_products() 