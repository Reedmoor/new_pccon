#!/usr/bin/env python3
"""
Скрипт для отладки загрузки конкретного товара
"""

import requests
import json

def debug_product_upload():
    """Отладка загрузки товара ARDOR GAMING Rare M6"""
    print("🔍 ОТЛАДКА ЗАГРУЗКИ ТОВАРА")
    print("=" * 60)
    
    # Ищем товар в JSON
    json_file = "../data/local_parser_data_20250607_151208.json"
    target_product = None
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        print(f"📊 Всего товаров в JSON: {len(products)}")
        
        # Ищем ARDOR GAMING Rare M6
        for product in products:
            name = product.get('name') or ''
            if 'ARDOR GAMING Rare M' in name:
                target_product = product
                print(f"✅ Найден товар: {name}")
                break
        
        if not target_product:
            print("❌ Товар ARDOR GAMING Rare M не найден в JSON!")
            return
            
    except Exception as e:
        print(f"❌ Ошибка чтения JSON: {e}")
        return
    
    # Анализируем структуру товара
    print(f"\n📋 АНАЛИЗ ТОВАРА:")
    print(f"   Название: {target_product.get('name')}")
    print(f"   ID: {target_product.get('id')}")
    print(f"   URL: {target_product.get('url')}")
    print(f"   Цена скидочная: {target_product.get('price_discounted')}")
    print(f"   Цена оригинальная: {target_product.get('price_original')}")
    print(f"   Рейтинг: {target_product.get('rating')}")
    print(f"   Отзывы: {target_product.get('number_of_reviews')}")
    print(f"   Бренд: {target_product.get('brand_name')}")
    print(f"   Категории: {len(target_product.get('categories', []))}")
    print(f"   Изображения: {len(target_product.get('images', []))}")
    print(f"   Характеристики: {len(target_product.get('characteristics', {}))}")
    
    # Проверяем обязательные поля
    print(f"\n🔍 ПРОВЕРКА ОБЯЗАТЕЛЬНЫХ ПОЛЕЙ:")
    required_fields = ['name', 'url', 'price_original']
    missing_fields = []
    
    for field in required_fields:
        value = target_product.get(field)
        if value is None or value == "":
            missing_fields.append(field)
            print(f"   ❌ {field}: отсутствует")
        else:
            print(f"   ✅ {field}: {value}")
    
    if missing_fields:
        print(f"\n❌ Отсутствуют обязательные поля: {missing_fields}")
    else:
        print(f"\n✅ Все обязательные поля присутствуют")
    
    # Попробуем загрузить один товар на сервер
    print(f"\n🚀 ПОПЫТКА ЗАГРУЗКИ НА СЕРВЕР:")
    print("-" * 40)
    
    try:
        # Подготавливаем данные для загрузки
        upload_data = {
            "products": [target_product]
        }
        
        # Отправляем на сервер
        response = requests.post(
            "http://127.0.0.1:5001/api/upload-products",
            json=upload_data,
            timeout=30
        )
        
        print(f"📡 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Успешно!")
            print(f"   Полный ответ сервера: {result}")
            print(f"   Обработано товаров: {result.get('processed_count', 'N/A')}")
            print(f"   Добавлено: {result.get('added_count', 'N/A')}")
            print(f"   Обновлено: {result.get('updated_count', 'N/A')}")
            print(f"   Ошибок: {result.get('error_count', 'N/A')}")
            
            if result.get('errors'):
                print(f"   Ошибки:")
                for error in result.get('errors', []):
                    print(f"     • {error}")
            
            # Проверяем также другие возможные поля ответа
            for key, value in result.items():
                if key not in ['processed_count', 'added_count', 'updated_count', 'error_count', 'errors']:
                    print(f"   {key}: {value}")
                    
        else:
            print(f"❌ Ошибка загрузки: {response.status_code}")
            print(f"   Ответ сервера: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
    
    # Дополнительная проверка структуры товара
    print(f"\n🔍 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА:")
    print("-" * 40)
    print(f"Структура категорий:")
    for i, cat in enumerate(target_product.get('categories', []), 1):
        print(f"   {i}. {cat.get('name')} - {cat.get('url')}")
    
    print(f"\nХарактеристики товара:")
    chars = target_product.get('characteristics', {})
    for group_name, group_chars in chars.items():
        print(f"   {group_name}:")
        for char in group_chars[:2]:  # первые 2
            print(f"     • {char.get('title')}: {char.get('value')}")
        if len(group_chars) > 2:
            print(f"     ... и еще {len(group_chars) - 2}")
    
    print(f"\nИзображения:")
    for i, img in enumerate(target_product.get('images', [])[:3], 1):
        print(f"   {i}. {img[:60]}...")
    
    # Проверяем результат
    print(f"\n🔍 ПРОВЕРКА РЕЗУЛЬТАТА:")
    print("-" * 40)
    
    try:
        response = requests.get("http://127.0.0.1:5001/api/export-products", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            
            # Ищем наш товар
            found = False
            for product in products:
                name = product.get('name', '')
                if 'ARDOR GAMING Rare M' in name:
                    found = True
                    print(f"✅ Товар найден на сервере!")
                    print(f"   ID: {product.get('id')}")
                    print(f"   Название: {name}")
                    print(f"   Цена: {product.get('price_discounted')}₽")
                    break
            
            if not found:
                print(f"❌ Товар НЕ найден на сервере после загрузки")
                
        else:
            print(f"❌ Ошибка проверки: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")

if __name__ == "__main__":
    debug_product_upload() 