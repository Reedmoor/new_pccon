import sys
from pathlib import Path
import json
import os
import traceback
import re

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

try:
    from app import db, create_app
    from app.models.models import UnifiedProduct
    from app.utils.standardization.standardize import (
        standardize_characteristics,
        convert_to_unified_product
    )
except ImportError:
    print("Error importing app modules. Make sure you're running this script from the project root.")
    sys.exit(1)

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

def detect_vendor_from_url(url):
    """Detect vendor from product URL"""
    if not url:
        return 'unknown'
    
    url_lower = url.lower()
    if 'citilink.ru' in url_lower:
        return 'citilink'
    elif 'dns-shop.ru' in url_lower:
        return 'dns'
    else:
        return 'unknown'

def detect_product_type(product_name):
    """Detect product type from product name"""
    if not product_name:
        return 'case'  # Default to case for korpusa category
    
    name_lower = product_name.lower()
    
    # More specific keyword matching
    if any(keyword in name_lower for keyword in ['корпус', 'case', 'tower', 'chassis']):
        return 'case'
    elif any(keyword in name_lower for keyword in ['процессор', 'cpu', 'processor', 'intel', 'amd ryzen']):
        return 'processor'
    elif any(keyword in name_lower for keyword in ['видеокарта', 'gpu', 'graphics', 'geforce', 'radeon']):
        return 'graphics_card'
    elif any(keyword in name_lower for keyword in ['материнская плата', 'motherboard', 'mainboard']):
        return 'motherboard'
    elif any(keyword in name_lower for keyword in ['блок питания', 'power supply', 'psu', 'вт']):
        return 'power_supply'
    elif any(keyword in name_lower for keyword in ['оперативная память', 'ram', 'memory', 'ddr']):
        return 'ram'
    elif any(keyword in name_lower for keyword in ['кулер', 'cooler', 'охлаждение']):
        return 'cooler'
    elif any(keyword in name_lower for keyword in ['ssd', 'hdd', 'накопитель', 'диск']):
        return 'hard_drive'
    else:
        return 'case'  # Default to case for korpusa

def import_products_from_data(products_data, source='local_parser'):
    """
    Import products from data list (for API usage)
    
    Args:
        products_data (list): List of product dictionaries
        source (str): Source identifier for logging
    
    Returns:
        dict: Import results
    """
    app = create_app()
    with app.app_context():
        print(f"🔄 Начинаем импорт {len(products_data)} товаров из {source}")
        
        added_count = 0
        error_count = 0
        results = []
        
        for idx, product in enumerate(products_data):
            try:
                # Detect vendor from URL
                vendor = detect_vendor_from_url(product.get('url', ''))
                print(f"📦 Обрабатываем товар {idx+1}: {product.get('name', 'Безымянный товар')} от {vendor}")
                
                # Detect product type
                product_type = detect_product_type(product.get('name', ''))
                
                # Standardize product data
                std_product = standardize_characteristics(product, vendor)
                std_product["vendor"] = vendor
                std_product["product_type"] = product_type
                
                # Ensure compatibility characteristics
                ensure_compatibility_characteristics(std_product)
                
                # Convert to UnifiedProduct
                unified_product = convert_to_unified_product(std_product)
                
                # Add to database
                db.session.add(unified_product)
                
                # Commit every 50 products
                if idx % 50 == 0 and idx > 0:
                    db.session.commit()
                    print(f"✅ Сохранено {idx} товаров...")
                
                added_count += 1
                results.append({
                    'name': product.get('name', 'Unknown'),
                    'type': product_type,
                    'vendor': vendor,
                    'status': 'success'
                })
                
            except Exception as e:
                error_count += 1
                error_msg = f"Ошибка при обработке товара {idx+1}: {str(e)}"
                print(f"❌ {error_msg}")
                
                results.append({
                    'name': product.get('name', 'Unknown'),
                    'status': 'error',
                    'error': str(e)
                })
                
                # Rollback this product and continue
                db.session.rollback()
        
        # Final commit
        try:
            db.session.commit()
            print(f"🎉 Импорт завершен! Добавлено: {added_count}, Ошибок: {error_count}")
            
            # Print statistics by product type
            print("\n📊 Статистика по типам товаров:")
            for product_type in ["case", "processor", "graphics_card", "motherboard", "power_supply", "ram", "cooler", "hard_drive"]:
                count = db.session.query(UnifiedProduct).filter(UnifiedProduct.product_type == product_type).count()
                if count > 0:
                    print(f"   {product_type}: {count} товаров")
            
            return {
                'success': True,
                'added_count': added_count,
                'error_count': error_count,
                'results': results
            }
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Ошибка при финальном сохранении: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'added_count': 0,
                'error_count': len(products_data)
            }

def import_products():
    """Import products using manual file mapping to product types"""
    app = create_app()
    with app.app_context():
        
        # Ручной маппинг файлов к типам продуктов
        file_mappings = {
            # Кулеры
            "app/utils/DNS_parsing/categories/product_data_Кулеры для процессоров.json": ("dns", "cooler"),
            "app/utils/Citi_parser/data/sistemy-ohlazhdeniya-processora/Товары.json": ("citilink", "cooler"),
            
            # Корпуса
            "app/utils/DNS_parsing/categories/product_data_Корпуса.json": ("dns", "case"),
            "app/utils/Citi_parser/data/korpusa/Товары.json": ("citilink", "case"),
            
            # Блоки питания
            "app/utils/DNS_parsing/categories/product_data_Блоки питания.json": ("dns", "power_supply"),
            "app/utils/Citi_parser/data/bloki-pitaniya/Товары.json": ("citilink", "power_supply"),
            
            # Материнские платы
            "app/utils/DNS_parsing/categories/product_data_Материнские платы.json": ("dns", "motherboard"),
            "app/utils/Citi_parser/data/materinskie-platy/Товары.json": ("citilink", "motherboard"),
            
            # Процессоры
            "app/utils/DNS_parsing/categories/product_data_Процессоры.json": ("dns", "processor"),
            "app/utils/Citi_parser/data/processory/Товары.json": ("citilink", "processor"),
            
            # Видеокарты
            "app/utils/DNS_parsing/categories/product_data_Видеокарты.json": ("dns", "graphics_card"),
            "app/utils/Citi_parser/data/videokarty/Товары.json": ("citilink", "graphics_card"),
            
            # Оперативная память
            "app/utils/DNS_parsing/categories/product_data_Оперативная память DIMM.json": ("dns", "ram"),
            "app/utils/Citi_parser/data/moduli-pamyati/Товары.json": ("citilink", "ram"),
            
            # Накопители (все типы объединяем в hard_drive)
            "app/utils/DNS_parsing/categories/product_data_SSD накопители.json": ("dns", "hard_drive"),
            "app/utils/DNS_parsing/categories/product_data_SSD M_2 накопители.json": ("dns", "hard_drive"),
            "app/utils/DNS_parsing/categories/product_data_Жесткие диски 3_5_.json": ("dns", "hard_drive"),
            "app/utils/Citi_parser/data/zhestkie-diski/Товары.json": ("citilink", "hard_drive"),
            "app/utils/Citi_parser/data/ssd-nakopiteli/Товары.json": ("citilink", "hard_drive"),
        }
        
        all_products = []
        
        print("Начинаем ручной импорт продуктов...")
        
        for file_path, (vendor, product_type) in file_mappings.items():
            if not os.path.exists(file_path):
                print(f"Файл не найден: {file_path}")
                continue
                
            try:
                print(f"Обработка {vendor} {product_type} из {file_path}...")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle both single product and list of products
                if isinstance(data, list):
                    products = data
                else:
                    products = [data]
                
                for product in products:
                    # Стандартизируем данные
                    std_product = standardize_characteristics(product, vendor)
                    std_product["vendor"] = vendor
                    # Принудительно устанавливаем правильный тип продукта
                    std_product["product_type"] = product_type
                    all_products.append(std_product)
                
                print(f"Найдено {len(products)} продуктов типа {product_type} от {vendor}")
                
            except Exception as e:
                print(f"Ошибка при обработке файла {file_path}: {str(e)}")
                continue
        
        print(f"Всего продуктов для импорта: {len(all_products)}")
        
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
            
            # Статистика по типам продуктов
            print("\nСтатистика по типам продуктов:")
            for product_type in ["cooler", "case", "power_supply", "motherboard", "processor", "graphics_card", "ram", "hard_drive"]:
                count = db.session.query(UnifiedProduct).filter(UnifiedProduct.product_type == product_type).count()
                print(f"{product_type}: {count} продуктов")
                
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка сохранения в базу данных: {str(e)}")
            traceback.print_exc()

if __name__ == "__main__":
    import_products() 