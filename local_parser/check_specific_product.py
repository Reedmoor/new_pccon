#!/usr/bin/env python3
"""
Скрипт для поиска конкретного товара на сервере
"""

import requests
import json
import sys

def search_product(product_name, server_url="http://127.0.0.1:5001"):
    """Поиск товара по названию"""
    print(f"🔍 Поиск товара: '{product_name}'")
    print(f"📡 На сервере: {server_url}")
    print("=" * 60)
    
    try:
        # Получаем все товары
        response = requests.get(f"{server_url}/api/export-products", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            
            print(f"✅ Всего товаров в базе: {len(products):,}")
            
            # Ищем товары с похожим названием
            matching_products = []
            for product in products:
                name = product.get('name', '').lower()
                if product_name.lower() in name:
                    matching_products.append(product)
            
            print(f"🎯 Найдено совпадений: {len(matching_products)}")
            
            if matching_products:
                print(f"\n📋 Найденные товары:")
                for i, product in enumerate(matching_products, 1):
                    print(f"\n   {i}. {product.get('name', 'Без названия')}")
                    print(f"      ID: {product.get('id', 'N/A')}")
                    print(f"      Категория: {product.get('product_type', 'N/A')}")
                    print(f"      Цена: {product.get('price_discounted', 'N/A')}₽")
                    print(f"      Производитель: {product.get('manufacturer', 'N/A')}")
                    print(f"      URL: {product.get('url', 'N/A')}")
                    
                    # Показываем характеристики
                    specs = product.get('specifications', [])
                    if specs:
                        print(f"      Характеристики:")
                        for spec in specs[:3]:  # первые 3
                            key = spec.get('key', 'N/A')
                            value = spec.get('value', 'N/A')
                            print(f"        • {key}: {value}")
                        if len(specs) > 3:
                            print(f"        ... и еще {len(specs) - 3} характеристик")
            else:
                print(f"\n❌ Товар '{product_name}' не найден!")
                
                # Попробуем найти похожие корпуса
                print(f"\n🔍 Поиск похожих корпусов...")
                case_products = [p for p in products if p.get('product_type') == 'case']
                print(f"   Всего корпусов: {len(case_products)}")
                
                if case_products:
                    print(f"   Примеры корпусов в базе:")
                    for i, product in enumerate(case_products[:10], 1):
                        name = product.get('name', 'Без названия')
                        print(f"     {i}. {name}")
                        
        else:
            print(f"❌ Ошибка получения данных: {response.status_code}")
            print(f"   Ответ сервера: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    search_name = "ARDOR GAMING Rare M6"
    
    if len(sys.argv) > 1:
        search_name = " ".join(sys.argv[1:])
    
    print(f"🔍 ПОИСК ТОВАРА В БАЗЕ ДАННЫХ")
    print("=" * 60)
    
    search_product(search_name) 