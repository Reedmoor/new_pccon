#!/usr/bin/env python3
"""
Скрипт для отладки определения типа товара
"""

import json
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def determine_product_type(categories):
    """
    Определяем тип товара на основе категорий (копия из standardize.py)
    """
    category_str = ' '.join(categories).lower()
    
    print(f"🔍 Анализ категорий: '{category_str}'")
    
    # Проверяем все возможные типы товаров
    checks = [
        (['материнская плата', 'материнские платы', 'motherboard'], 'motherboard'),
        (['блок питания', 'блоки питания', 'power supply'], 'power_supply'),
        (['кулер', 'охлаждение', 'cooler', 'cooling', 'охлаждения процессора', 'системы охлаждения процессора', 'устройство охлаждения', 'кулеры для процессоров'], 'cooler'),
        (['процессор', 'процессоры', 'cpu', 'processor'], 'processor'),
        (['видеокарта', 'видеокарты', 'gpu', 'graphics card'], 'graphics_card'),
        (['оперативная память', 'память dimm', 'ram', 'memory', 'модули памяти'], 'ram'),
        (['жесткий диск', 'жесткие диски', 'ssd', 'hdd', 'накопитель', 'storage', 'ssd накопители', 'ssd m.2 накопители', 'ssd m_2 накопители', 'твердотельный накопитель', 'накопители ssd'], 'hard_drive'),
        (['корпус', 'case', 'корпуса'], 'case'),
    ]
    
    for terms, product_type in checks:
        found_terms = [term for term in terms if term in category_str]
        if found_terms:
            print(f"✅ Найден тип {product_type}: совпадения с {found_terms}")
            return product_type
        else:
            print(f"❌ Не найден тип {product_type}: нет совпадений с {terms[:3]}...")
    
    print(f"⚠️ Тип не определен - присваиваем 'other'")
    return 'other'

def standardize_characteristics_debug(source_data, vendor):
    """
    Отладочная версия стандартизации характеристик
    """
    print(f"\n🔧 СТАНДАРТИЗАЦИЯ ТОВАРА ОТ {vendor.upper()}")
    print("=" * 50)
    
    standardized = {
        "vendor_specific": {},
    }
    
    if vendor.lower() == 'dns':
        print("📊 Обработка DNS данных...")
        
        standardized["id"] = source_data.get("id")
        standardized["product_name"] = source_data.get("name")
        standardized["price_discounted"] = source_data.get("price_discounted")
        standardized["price_original"] = source_data.get("price_original")
        standardized["rating"] = source_data.get("rating")
        standardized["number_of_reviews"] = source_data.get("number_of_reviews")
        standardized["images"] = source_data.get("images", [])
        standardized["product_url"] = source_data.get("url")
        
        # Извлекаем категории
        categories = [cat.get("name") for cat in source_data.get("categories", [])]
        standardized["category"] = categories
        
        print(f"📂 Категории: {categories}")
        
        # Определяем тип товара
        product_type = determine_product_type(categories)
        standardized["product_type"] = product_type
        
        print(f"🏷️ Определенный тип: {product_type}")
        
        # Обрабатываем характеристики
        characteristics = {}
        chars_data = source_data.get("characteristics", {})
        print(f"📋 Количество групп характеристик: {len(chars_data)}")
        
        for group_name, props in chars_data.items():
            print(f"   • {group_name}: {len(props)} характеристик")
            for prop in props:
                prop_title = prop.get("title")
                prop_value = prop.get("value")
                characteristics[prop_title] = prop_value
    
    standardized["characteristics"] = characteristics
    return standardized

def debug_ardor_product():
    """Отладка обработки корпуса ARDOR GAMING"""
    print("🔍 ОТЛАДКА ОБРАБОТКИ КОРПУСА ARDOR GAMING")
    print("=" * 60)
    
    # Читаем товар из JSON
    json_file = "../data/local_parser_data_20250607_151208.json"
    target_product = None
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        # Ищем ARDOR GAMING Rare M
        for product in products:
            name = product.get('name') or ''
            if 'ARDOR GAMING Rare M' in name:
                target_product = product
                print(f"✅ Найден товар: {name}")
                break
        
        if not target_product:
            print("❌ Товар ARDOR GAMING Rare M не найден!")
            return
            
    except Exception as e:
        print(f"❌ Ошибка чтения JSON: {e}")
        return
    
    # Отладочная стандартизация
    std_product = standardize_characteristics_debug(target_product, 'dns')
    
    print(f"\n📋 РЕЗУЛЬТАТ СТАНДАРТИЗАЦИИ:")
    print(f"   Название: {std_product.get('product_name')}")
    print(f"   Тип: {std_product.get('product_type')}")
    print(f"   Цена скидочная: {std_product.get('price_discounted')}")
    print(f"   Цена оригинальная: {std_product.get('price_original')}")
    print(f"   Категории: {std_product.get('category')}")
    print(f"   URL: {std_product.get('product_url')}")
    
    # Проверяем, будет ли товар сохранен
    print(f"\n🔍 ПРОВЕРКА СОХРАНЕНИЯ:")
    
    # Проверяем обязательные поля
    required_fields = ['product_name', 'product_type']
    missing_fields = []
    
    for field in required_fields:
        value = std_product.get(field)
        if not value or value == "":
            missing_fields.append(field)
            print(f"   ❌ {field}: отсутствует или пустое")
        else:
            print(f"   ✅ {field}: {value}")
    
    if missing_fields:
        print(f"\n❌ ПРОБЛЕМА: Отсутствуют обязательные поля: {missing_fields}")
        print("   Товар не будет сохранен в базу данных!")
    else:
        print(f"\n✅ Все обязательные поля присутствуют")
        print("   Товар должен быть сохранен в базу данных")
    
    # Дополнительные проверки
    if std_product.get('product_type') == 'other':
        print(f"\n⚠️ ВНИМАНИЕ: Тип товара 'other' - возможно проблема с определением типа")

if __name__ == "__main__":
    debug_ardor_product() 