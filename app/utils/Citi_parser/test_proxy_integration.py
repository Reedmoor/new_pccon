#!/usr/bin/env python3
"""
Тестирование интеграции прокси в парсер Citilink
"""

import logging
import time
from request_handler import request, get_proxy_status
from queries import url, PRODUCTS_QUERY, PRODUCT_VARIABLE
from proxy_config import is_proxy_enabled, get_proxy_list

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def test_proxy_request():
    """Тестирует запрос через прокси"""
    print("🔍 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ ПРОКСИ В ПАРСЕР CITILINK")
    print("=" * 60)
    
    # Проверяем настройки
    print(f"📋 Прокси включены: {'✅' if is_proxy_enabled() else '❌'}")
    print(f"📊 Количество прокси: {len(get_proxy_list())}")
    print()
    
    # Показываем список прокси
    print("📋 СПИСОК ПРОКСИ:")
    for i, proxy in enumerate(get_proxy_list(), 1):
        proxy_display = f"{proxy.split(':')[0]}:{proxy.split(':')[1]}"
        print(f"  {i}. {proxy_display}")
    print()
    
    # Тестируем запрос к API Citilink
    print("🔄 Тестирование запроса к API Citilink...")
    
    try:
        start_time = time.time()
        
        # Выполняем тестовый запрос для категории "processory"
        test_data = request(
            url, 
            PRODUCTS_QUERY, 
            PRODUCT_VARIABLE("processory", 1), 
            "тестового запроса товаров"
        )
        
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        if test_data and 'data' in test_data:
            print(f"✅ Запрос успешен!")
            print(f"⏱️  Время отклика: {response_time}ms")
            
            # Проверяем структуру ответа
            if 'productsFilter' in test_data['data']:
                products = test_data['data']['productsFilter']['record'].get('products', [])
                print(f"📦 Получено товаров: {len(products)}")
                
                if products:
                    first_product = products[0]
                    print(f"🔸 Первый товар: {first_product.get('name', 'N/A')}")
                    print(f"🔸 ID: {first_product.get('id', 'N/A')}")
                    print(f"🔸 Цена: {first_product.get('price', {}).get('current', 'N/A')}")
            else:
                print("⚠️ Неожиданная структура ответа")
        else:
            print("❌ Получен пустой или некорректный ответ")
            
    except Exception as e:
        print(f"❌ Ошибка при выполнении запроса: {e}")
    
    # Показываем статус прокси
    print("\n📊 СТАТУС ПРОКСИ:")
    proxy_status = get_proxy_status()
    for proxy_name, status in proxy_status.items():
        current_mark = "🔵" if status['current'] else "⚪"
        active_mark = "✅" if status['active'] else "❌"
        print(f"  {current_mark} {proxy_name} - {active_mark} (неудач: {status['failures']})")

def test_multiple_requests():
    """Тестирует несколько запросов для проверки ротации прокси"""
    print("\n🔄 ТЕСТИРОВАНИЕ РОТАЦИИ ПРОКСИ")
    print("-" * 40)
    
    for i in range(5):
        print(f"\nЗапрос #{i+1}:")
        try:
            start_time = time.time()
            
            # Выполняем запрос
            test_data = request(
                url, 
                PRODUCTS_QUERY, 
                PRODUCT_VARIABLE("processory", 1), 
                f"тестового запроса #{i+1}"
            )
            
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            
            if test_data and 'data' in test_data:
                print(f"  ✅ Успех! Время: {response_time}ms")
            else:
                print(f"  ❌ Неудача")
                
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
        
        # Показываем текущий активный прокси
        proxy_status = get_proxy_status()
        current_proxy = None
        for proxy_name, status in proxy_status.items():
            if status['current']:
                current_proxy = proxy_name
                break
        
        if current_proxy:
            print(f"  🔵 Текущий прокси: {current_proxy}")
        
        # Небольшая пауза между запросами
        time.sleep(2)

if __name__ == "__main__":
    test_proxy_request()
    test_multiple_requests()
    
    print("\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО") 