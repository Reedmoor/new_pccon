#!/usr/bin/env python3
"""
Скрипт для проверки товаров с нулевой ценой
"""

import requests
import json

def check_zero_price_products():
    """Проверка товаров с нулевой ценой"""
    print("🔍 АНАЛИЗ ТОВАРОВ С НУЛЕВОЙ ЦЕНОЙ")
    print("=" * 60)
    
    # Читаем JSON файл
    json_file = "../data/local_parser_data_20250607_151208.json"
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # JSON файл содержит список товаров напрямую
        if isinstance(json_data, list):
            products = json_data
        else:
            products = json_data.get('products', [])
        
        print(f"📊 Всего товаров в JSON: {len(products):,}")
        
        # Анализируем цены в JSON
        zero_price_products = []
        valid_price_products = []
        
        for product in products:
            price_discounted = product.get('price_discounted', 0)
            if price_discounted == 0 or price_discounted is None:
                zero_price_products.append(product)
            else:
                valid_price_products.append(product)
        
        print(f"❌ Товаров с нулевой/отсутствующей ценой в JSON: {len(zero_price_products):,}")
        print(f"✅ Товаров с валидной ценой в JSON: {len(valid_price_products):,}")
        
        # Группируем товары с нулевой ценой по категориям
        zero_by_category = {}
        for product in zero_price_products:
            # Определяем категорию по URL или названию
            category = "unknown"
            url = product.get('url', '')
            name = product.get('name') or ''
            name = name.lower()
            
            if 'korpus' in url or 'корпус' in name:
                category = 'case'
            elif 'videocard' in url or 'видеокарта' in name:
                category = 'graphics_card'
            elif 'ram' in url or 'оперативная память' in name:
                category = 'ram'
            elif 'processor' in url or 'процессор' in name:
                category = 'processor'
            elif 'cooler' in url or 'кулер' in name:
                category = 'cooler'
            elif 'power' in url or 'блок питания' in name:
                category = 'power_supply'
            elif 'motherboard' in url or 'материнская плата' in name:
                category = 'motherboard'
            elif 'ssd' in url or 'накопитель' in name:
                category = 'hard_drive'
            
            if category not in zero_by_category:
                zero_by_category[category] = []
            zero_by_category[category].append(product)
        
        print(f"\n📊 Товары с нулевой ценой по категориям:")
        for category, items in zero_by_category.items():
            print(f"   • {category}: {len(items):,} товаров")
            # Показываем примеры
            for i, item in enumerate(items[:2]):
                name = item.get('name') or 'Без названия'
                name_short = name[:50] + "..." if len(name) > 50 else name
                price_orig = item.get('price_original', 0)
                print(f"     {i+1}. {name_short} (оригинальная: {price_orig}₽)")
            if len(items) > 2:
                print(f"     ... и еще {len(items) - 2} товаров")
            print()
            
    except Exception as e:
        print(f"❌ Ошибка чтения JSON: {e}")
        return
    
    # Проверяем товары на сервере
    print(f"\n🌐 ПРОВЕРКА ТОВАРОВ НА СЕРВЕРЕ")
    print("-" * 40)
    
    try:
        response = requests.get("http://127.0.0.1:5001/api/export-products", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            server_products = data.get('products', [])
            
            print(f"📊 Всего товаров на сервере: {len(server_products):,}")
            
            # Анализируем цены на сервере
            server_zero_price = []
            server_valid_price = []
            
            for product in server_products:
                price = product.get('price_discounted')
                if price == 0 or price is None:
                    server_zero_price.append(product)
                else:
                    server_valid_price.append(product)
            
            print(f"❌ Товаров с нулевой ценой на сервере: {len(server_zero_price):,}")
            print(f"✅ Товаров с валидной ценой на сервере: {len(server_valid_price):,}")
            
            # Группируем по категориям на сервере
            server_zero_by_category = {}
            for product in server_zero_price:
                category = product.get('product_type', 'unknown')
                if category not in server_zero_by_category:
                    server_zero_by_category[category] = []
                server_zero_by_category[category].append(product)
            
            print(f"\n📊 Товары с нулевой ценой на сервере по категориям:")
            for category, items in server_zero_by_category.items():
                print(f"   • {category}: {len(items):,} товаров")
                
        else:
            print(f"❌ Ошибка получения данных с сервера: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка подключения к серверу: {e}")

if __name__ == "__main__":
    check_zero_price_products() 