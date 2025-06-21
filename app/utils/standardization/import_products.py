import sys
from pathlib import Path
import json
import os
import traceback
import re
import time
import glob

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
        if 'memory_form_factor' not in characteristics:
            characteristics['memory_form_factor'] = ''
            
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
        if 'memory_form_factor' not in characteristics:
            characteristics['memory_form_factor'] = ''
            
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

def detect_product_type(product_name, product_categories=None):
    """Detect product type from product name and categories"""
    if not product_name:
        return 'other'
    
    name_lower = product_name.lower()
    
    # Сначала проверяем категории, если они есть
    if product_categories:
        for category in product_categories:
            cat_name = category.get('name', '').lower() if isinstance(category, dict) else ''
            if 'видеокарт' in cat_name or 'gpu' in cat_name or 'graphics' in cat_name:
                return 'graphics_card'
            elif 'процессор' in cat_name or 'cpu' in cat_name or 'processor' in cat_name:
                return 'processor'
            elif 'материнск' in cat_name or 'motherboard' in cat_name or 'mainboard' in cat_name:
                return 'motherboard'
            elif 'оперативн' in cat_name and 'памят' in cat_name:
                return 'ram'
            elif 'память' in cat_name and 'dimm' in cat_name:
                return 'ram'
            elif 'корпус' in cat_name or 'case' in cat_name:
                return 'case'
            elif 'блок' in cat_name and 'питан' in cat_name:
                return 'power_supply'
            elif 'кулер' in cat_name or 'охлажден' in cat_name or 'cooler' in cat_name:
                return 'cooler'
            elif 'ssd' in cat_name or ('диск' in cat_name) or 'накопител' in cat_name:
                return 'hard_drive'
    
    # Если категории не помогли, анализируем название товара
    if any(keyword in name_lower for keyword in ['видеокарта', 'gpu', 'graphics', 'geforce', 'radeon', 'gtx', 'rtx']):
        return 'graphics_card'
    elif any(keyword in name_lower for keyword in ['процессор', 'cpu', 'processor']):
        return 'processor'
    elif any(keyword in name_lower for keyword in ['intel core', 'amd ryzen', 'intel pentium', 'amd fx']):
        return 'processor'
    elif any(keyword in name_lower for keyword in ['материнская плата', 'motherboard', 'mainboard', 'мат. плата']):
        return 'motherboard'
    elif any(keyword in name_lower for keyword in ['блок питания', 'power supply', 'psu']) or (name_lower.endswith(' вт') or ' вт ' in name_lower):
        return 'power_supply'
    elif any(keyword in name_lower for keyword in ['оперативная память', 'ram', 'memory', 'ddr4', 'ddr5', 'dimm']):
        return 'ram'
    elif any(keyword in name_lower for keyword in ['кулер', 'cooler', 'охлаждение', 'вентилятор']):
        return 'cooler'
    elif any(keyword in name_lower for keyword in ['ssd', 'hdd', 'накопитель', 'диск', 'жесткий']):
        return 'hard_drive'
    elif any(keyword in name_lower for keyword in ['корпус', 'case', 'tower', 'chassis']):
        return 'case'
    else:
        return 'other'

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
                product_categories = product.get('categories', [])
                product_type = product.get('detected_product_type') or detect_product_type(product.get('name', ''), product_categories)
                
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
        
        # Получаем последний локальный файл DNS
        latest_local_file = None
        local_files = glob.glob('data/local_parser_data_*.json')
        
        if local_files:
            # Находим самый свежий файл
            latest_local_file = max(local_files, key=os.path.getmtime)
            print(f"Найден локальный файл DNS: {latest_local_file}")
        else:
            print("Локальные файлы DNS не найдены")
        
        # Маппинг категорий из парсеров в унифицированные типы продуктов
        category_mapping = {
            # DNS категории
            'Видеокарты': 'graphics_card',
            'Процессоры': 'processor',
            'Материнские платы': 'motherboard',
            'Оперативная память': 'ram',
            'Корпуса': 'case',
            'Блоки питания': 'power_supply',
            'Кулеры': 'cooler',
            'Жесткие диски': 'hard_drive',
            'SSD M.2': 'hard_drive',
            'SSD SATA': 'hard_drive',
            
            # Citilink категории (имена директорий)
            'videokarty': 'graphics_card',
            'processory': 'processor',
            'materinskie-platy': 'motherboard',
            'moduli-pamyati': 'ram',
            'korpusa': 'case',
            'bloki-pitaniya': 'power_supply',
            'sistemy-ohlazhdeniya-processora': 'cooler',
            'zhestkie-diski': 'hard_drive',
            'ssd-nakopiteli': 'hard_drive',
            'ssd-m2': 'hard_drive',
            'ssd-sata': 'hard_drive'
        }

        # Ручной маппинг файлов к типам продуктов
        file_mappings = {
            # Кулеры
            "app/utils/old_dns_parser/product_data.json": ("dns", "cooler"),
            "app/utils/Citi_parser/data/sistemy-ohlazhdeniya-processora/Товары.json": ("citilink", "cooler"),
            
            # Корпуса
            "app/utils/old_dns_parser/product_data.json": ("dns", "case"),
            "app/utils/Citi_parser/data/korpusa/Товары.json": ("citilink", "case"),
            
            # Блоки питания
            "app/utils/old_dns_parser/product_data.json": ("dns", "power_supply"),
            "app/utils/Citi_parser/data/bloki-pitaniya/Товары.json": ("citilink", "power_supply"),
            
            # Материнские платы
            "app/utils/old_dns_parser/product_data.json": ("dns", "motherboard"),
            "app/utils/Citi_parser/data/materinskie-platy/Товары.json": ("citilink", "motherboard"),
            
            # Процессоры
            "app/utils/old_dns_parser/product_data.json": ("dns", "processor"),
            "app/utils/Citi_parser/data/processory/Товары.json": ("citilink", "processor"),
            
            # Видеокарты
            "app/utils/old_dns_parser/product_data.json": ("dns", "graphics_card"),
            "app/utils/Citi_parser/data/videokarty/Товары.json": ("citilink", "graphics_card"),
            
            # Оперативная память
            "app/utils/old_dns_parser/product_data.json": ("dns", "ram"),
            "app/utils/Citi_parser/data/moduli-pamyati/Товары.json": ("citilink", "ram"),
            
            # Накопители (все типы объединяем в hard_drive)
            "app/utils/old_dns_parser/product_data.json": ("dns", "hard_drive"),
            "app/utils/Citi_parser/data/zhestkie-diski/Товары.json": ("citilink", "hard_drive"),
            "app/utils/Citi_parser/data/ssd-nakopiteli/Товары.json": ("citilink", "hard_drive")
        }
        
        all_products = []
        
        print("Начинаем импорт продуктов...")
        
        # Обрабатываем локальный файл DNS
        dns_loaded = False
        if latest_local_file:
            try:
                print(f"Обработка локального файла DNS: {latest_local_file}")
                
                with open(latest_local_file, 'r', encoding='utf-8') as f:
                    local_data = json.load(f)
                
                # Группируем товары по категориям из данных
                products_by_category = {}
                
                if isinstance(local_data, list):
                    for product in local_data:
                        # Проверяем, что у продукта есть имя
                        if not product.get('name'):
                            print(f"Пропускаем товар без имени: {product.get('id', 'ID неизвестен')}")
                            continue
                            
                        # Определяем категорию по данным товара
                        categories = product.get('categories', [])
                        category_name = None
                        
                        # Ищем нужную категорию в списке категорий
                        if categories:
                            for cat in categories:
                                if not isinstance(cat, dict):
                                    continue
                                    
                                cat_name = cat.get('name', '').lower()
                                if 'видеокарт' in cat_name:
                                    category_name = 'graphics_card'
                                elif 'процессор' in cat_name:
                                    category_name = 'processor'
                                elif 'материнск' in cat_name:
                                    category_name = 'motherboard'
                                elif ('памят' in cat_name and 'оперативн' in cat_name) or 'dimm' in cat_name:
                                    category_name = 'ram'
                                elif 'корпус' in cat_name:
                                    category_name = 'case'
                                elif ('блок' in cat_name and 'питан' in cat_name) or 'бп' in cat_name:
                                    category_name = 'power_supply'
                                elif 'кулер' in cat_name or 'охлажден' in cat_name:
                                    category_name = 'cooler'
                                elif 'ssd' in cat_name or 'диск' in cat_name or 'накопител' in cat_name:
                                    category_name = 'hard_drive'
                                
                                if category_name:
                                    break
                        
                        # Если категорию не определили, пытаемся по названию товара
                        if not category_name:
                            product_name = product.get('name', '').lower()
                            if 'видеокарт' in product_name or 'graphics card' in product_name:
                                category_name = 'graphics_card'
                            elif 'процессор' in product_name or 'cpu' in product_name:
                                category_name = 'processor'
                            elif 'материнск' in product_name or 'motherboard' in product_name:
                                category_name = 'motherboard'
                            elif ('оперативн' in product_name and 'памят' in product_name) or 'ram' in product_name or 'dimm' in product_name:
                                category_name = 'ram'
                            elif 'корпус' in product_name or 'case' in product_name:
                                category_name = 'case'
                            elif 'блок питан' in product_name or 'power supply' in product_name:
                                category_name = 'power_supply'
                            elif 'кулер' in product_name or 'cooler' in product_name:
                                category_name = 'cooler'
                            elif 'ssd' in product_name or 'жесткий диск' in product_name or 'hdd' in product_name or 'накопитель' in product_name:
                                category_name = 'hard_drive'
                            else:
                                # Если не смогли определить категорию, пропускаем товар
                                print(f"Не удалось определить категорию для товара: {product.get('name', 'Без имени')}")
                                continue
                        
                        if category_name not in products_by_category:
                            products_by_category[category_name] = []
                        products_by_category[category_name].append(product)
                
                # Обрабатываем каждую категорию
                for category_name, products in products_by_category.items():
                    print(f"Обработка категории DNS {category_name}: {len(products)} товаров")
                    
                    for product in products:
                        try:
                            # Стандартизируем данные
                            std_product = standardize_characteristics(product, "dns")
                            std_product["vendor"] = "dns"
                            std_product["product_type"] = category_name
                            all_products.append(std_product)
                        except Exception as e:
                            print(f"Ошибка при обработке товара {product.get('name', 'Без имени')}: {str(e)}")
                
                print(f"Загружено {len(products_by_category.get('motherboard', []))} материнских плат из локального файла DNS")
                print(f"Загружено {sum(len(products) for products in products_by_category.values())} товаров из локального файла DNS")
                dns_loaded = True
                
            except Exception as e:
                print(f"Ошибка при обработке локального файла: {str(e)}")
                traceback.print_exc()
        
        # Обрабатываем все доступные файлы Citilink из папки data
        citilink_data_dir = os.path.join('app', 'utils', 'Citi_parser', 'data')
        if os.path.exists(citilink_data_dir):
            # Перебираем все директории категорий
            for category_dir in os.listdir(citilink_data_dir):
                category_path = os.path.join(citilink_data_dir, category_dir)
                if os.path.isdir(category_path):
                    products_file = os.path.join(category_path, 'Товары.json')
                    if os.path.exists(products_file):
                        try:
                            # Определяем тип продукта по имени директории
                            product_type = category_mapping.get(category_dir, None)
                            if not product_type:
                                print(f"Неизвестная категория Citilink: {category_dir}, пропускаем")
                                continue
                                
                            print(f"Обработка категории Citilink {category_dir} ({product_type})")
                            
                            with open(products_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            if isinstance(data, list):
                                products = data
                            else:
                                products = [data]
                            
                            print(f"Загружено {len(products)} товаров из {products_file}")
                            
                            for product in products:
                                # Стандартизируем данные
                                std_product = standardize_characteristics(product, "citilink")
                                std_product["vendor"] = "citilink"
                                std_product["product_type"] = product_type
                                all_products.append(std_product)
                            
                            print(f"Добавлено {len(products)} товаров типа {product_type} от citilink")
                        except Exception as e:
                            print(f"Ошибка при обработке файла {products_file}: {str(e)}")
                            traceback.print_exc()
        
        # Обрабатываем данные DNS из old_dns_parser только если не загружены из локального файла
        dns_file = os.path.join('app', 'utils', 'old_dns_parser', 'product_data.json')
        if os.path.exists(dns_file) and not dns_loaded:
            try:
                print(f"Обработка данных DNS из {dns_file} (локальный файл не найден)")
                
                with open(dns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    # Группируем товары по категориям из данных
                    products_by_category = {}
                    
                    for product in data:
                        # Проверяем, что у продукта есть имя
                        if not product.get('name'):
                            print(f"Пропускаем товар DNS без имени: {product.get('id', 'ID неизвестен')}")
                            continue
                            
                        # Определяем категорию по данным товара
                        category_name = None
                        
                        # Проверяем категорию товара
                        if 'category' in product:
                            category = product.get('category', '')
                            if isinstance(category, str):
                                category_name = category_mapping.get(category, None)
                        
                        # Если категория не определена, пропускаем товар
                        if not category_name:
                            continue
                        
                        if category_name not in products_by_category:
                            products_by_category[category_name] = []
                        products_by_category[category_name].append(product)
                    
                    # Обрабатываем каждую категорию
                    for category_name, products in products_by_category.items():
                        print(f"Обработка категории DNS {category_name}: {len(products)} товаров")
                        
                        for product in products:
                            # Стандартизируем данные
                            std_product = standardize_characteristics(product, "dns")
                            std_product["vendor"] = "dns"
                            std_product["product_type"] = category_name
                            all_products.append(std_product)
                    
                    print(f"Загружено {len(data)} товаров из DNS (старый парсер)")
                    
                else:
                    print(f"Ошибка: данные DNS не являются списком")
            except Exception as e:
                print(f"Ошибка при обработке файла {dns_file}: {str(e)}")
                traceback.print_exc()
        elif dns_loaded:
            print("Данные DNS уже загружены из локального файла, пропускаем старый парсер")
        
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