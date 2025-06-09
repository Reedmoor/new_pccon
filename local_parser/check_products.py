#!/usr/bin/env python3
"""
Скрипт для проверки товаров в базе данных
"""

import requests
import json
from datetime import datetime

def check_products_on_server(server_url="http://127.0.0.1:5001"):
    """Проверка товаров на сервере"""
    print(f"🔍 Проверка товаров на сервере: {server_url}")
    print("=" * 60)
    
    try:
        # Проверяем экспорт товаров
        response = requests.get(f"{server_url}/api/export-products", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            
            print(f"✅ Найдено товаров в базе: {len(products):,}")
            
            # Группируем по категориям
            categories = {}
            for product in products:
                category = product.get('product_type', 'unknown')
                if category not in categories:
                    categories[category] = []
                categories[category].append(product)
            
            print(f"\n📊 Товары по категориям:")
            for category, items in categories.items():
                print(f"   • {category}: {len(items):,} товаров")
                
                # Показываем несколько примеров
                if len(items) > 0:
                    print(f"     Примеры:")
                    for i, item in enumerate(items[:3]):
                        name = item.get('name', 'Без названия')
                        price = item.get('price_discounted', 0)
                        print(f"       {i+1}. {name} - {price}₽")
                    if len(items) > 3:
                        print(f"       ... и еще {len(items) - 3} товаров")
                print()
            
            # Последние добавленные товары
            print(f"🕒 Последние добавленные товары:")
            recent_products = sorted(products, key=lambda x: x.get('id', 0), reverse=True)[:5]
            for i, product in enumerate(recent_products, 1):
                name = product.get('name', 'Без названия')
                category = product.get('product_type', 'unknown')
                price = product.get('price_discounted', 0)
                print(f"   {i}. {name} ({category}) - {price}₽")
                
        else:
            print(f"❌ Ошибка получения данных: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    
    print("\n" + "=" * 60)
    print(f"💡 Для доступа к админ-панели:")
    print(f"   • Сервер 5001: {server_url}/admin")
    print(f"   • Docker 5000: http://127.0.0.1:5000/admin")

def check_recent_uploads(server_url="http://127.0.0.1:5001"):
    """Проверка последних загрузок"""
    print(f"\n📤 Последние загрузки на {server_url}:")
    print("-" * 40)
    
    try:
        response = requests.get(f"{server_url}/api/parser-status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            uploads = data.get('recent_uploads', [])
            
            if uploads:
                for i, upload in enumerate(uploads, 1):
                    filename = upload.get('filename', 'unknown')
                    count = upload.get('product_count', 0)
                    time = upload.get('upload_time', 'unknown')
                    size_mb = upload.get('file_size', 0) / 1024 / 1024
                    
                    print(f"   {i}. {filename}")
                    print(f"      Товаров: {count:,}, Размер: {size_mb:.1f} MB")
                    print(f"      Время: {time}")
                    print()
            else:
                print("   Нет данных о загрузках")
                
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    print("🔍 ПРОВЕРКА ТОВАРОВ В БАЗЕ ДАННЫХ")
    print("=" * 60)
    
    # Проверяем товары
    check_products_on_server()
    
    # Проверяем последние загрузки
    check_recent_uploads() 