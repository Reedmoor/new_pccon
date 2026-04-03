#!/usr/bin/env python3
"""
Простой тест загрузки на исправленный удаленный сервер
"""

import json
import requests
import urllib3

# Отключаем SSL предупреждения
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_upload():
    # Настройки
    server_url = "http://k4db-jl2g-6d7c.gw-1a.dockhost.net"
    data_file = "../data/local_parser_data_20250607_203655.json"
    
    print("🔄 Тестирую исправленный удаленный сервер...")
    print(f"🎯 Сервер: {server_url}")
    
    # Создаем сессию с принудительным HTTP
    session = requests.Session()
    session.verify = False  # Отключаем SSL проверку
    session.allow_redirects = False  # Отключаем автоматические перенаправления
    session.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'TestUpload/1.0'
    })
    
    # Проверяем подключение
    try:
        health_response = session.get(f"{server_url}/api/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Сервер доступен: {health_data['server']}")
            print(f"📊 Товаров в базе: {health_data['product_count']}")
        else:
            print(f"❌ Сервер недоступен: {health_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    # Читаем данные
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        print(f"📁 Загружено товаров из файла: {len(products)}")
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return
    
    # Отправляем данные
    payload = {
        'products': products,
        'source': 'test_upload',
        'upload_type': 'local_parser',
        'category': 'Видеокарты'
    }
    
    try:
        print("🚀 Отправляю данные...")
        print(f"🔗 URL: {server_url}/api/upload-products")
        
        response = session.post(
            f"{server_url}/api/upload-products", 
            json=payload, 
            timeout=180
        )
        
        print(f"📡 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("🎉 УСПЕШНО ЗАГРУЖЕНО!")
            print(f"   📊 Импортировано: {result.get('imported_count', 0)}")
            print(f"   📄 Сообщение: {result.get('message', 'N/A')}")
            if 'import_result' in result:
                import_result = result['import_result']
                print(f"   ✅ Добавлено: {import_result.get('added_count', 0)}")
                print(f"   ❌ Ошибок: {import_result.get('error_count', 0)}")
        else:
            print(f"❌ Ошибка загрузки: {response.status_code}")
            print(f"   Ответ: {response.text[:500]}...")
    
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

if __name__ == "__main__":
    test_upload()
    input("\nНажмите Enter для выхода...") 