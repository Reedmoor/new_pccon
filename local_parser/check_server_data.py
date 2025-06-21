#!/usr/bin/env python3
"""
Скрипт для проверки данных на Docker сервере
"""

import requests
import json
from datetime import datetime

def check_docker_server():
    """Проверка Docker сервера"""
    server_url = "https://pcconf.ru"
    
    print("🐳 Проверка Docker сервера...")
    print(f"   URL: {server_url}")
    
    try:
        # Проверяем health endpoint
        response = requests.get(f"{server_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Docker сервер доступен")
            print(f"   Статус: {data.get('status', 'unknown')}")
            print(f"   Время сервера: {data.get('timestamp', 'unknown')}")
            print(f"   Количество продуктов: {data.get('product_count', 'unknown')}")
            
            # Проверяем API endpoint
            try:
                api_response = requests.get(f"{server_url}/api/parser-status", timeout=10)
                if api_response.status_code == 200:
                    print("✅ API доступен")
                    api_data = api_response.json()
                    if 'recent_uploads' in api_data:
                        uploads = api_data['recent_uploads']
                        print(f"   Последних загрузок: {len(uploads)}")
                        if uploads:
                            latest = uploads[0]
                            print(f"   Последняя загрузка: {latest.get('filename', 'unknown')}")
                            print(f"   Товаров: {latest.get('product_count', 'unknown')}")
                else:
                    print(f"⚠️ API недоступен (код {api_response.status_code})")
            except Exception as e:
                print(f"⚠️ Ошибка API: {e}")
            
            return True
        else:
            print(f"❌ Docker сервер вернул код {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения к Docker серверу: {e}")
        return False

def check_web_interface():
    """Проверка веб-интерфейса"""
    print("\n🌐 Проверка веб-интерфейса...")
    
    try:
        # Проверяем главную страницу
        response = requests.get("https://pcconf.ru", timeout=10)
        if response.status_code == 200:
            print("✅ Главная страница доступна")
            print("   https://pcconf.ru")
            print("   Админ панель:")
            print("   https://pcconf.ru/api/parser-status")
            return True
        else:
            print(f"❌ Веб-интерфейс недоступен (код {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка веб-интерфейса: {e}")
        return False

def check_server_status():
    """Проверка статуса сервера"""
    server_url = "https://pcconf.ru"
    
    print("🔍 Проверка статуса сервера...")
    print(f"   URL: {server_url}")
    
    try:
        # Проверяем основную страницу
        response = requests.get(f"{server_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Сервер доступен")
            print(f"   Статус: {data.get('status', 'unknown')}")
            print(f"   Время сервера: {data.get('timestamp', 'unknown')}")
            print(f"   Количество продуктов: {data.get('product_count', 'unknown')}")
            return True
        else:
            print(f"❌ Сервер вернул код {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения к серверу: {e}")
        return False

if __name__ == "__main__":
    check_docker_server()
    check_web_interface()
    
    print("\n" + "=" * 50)
    print("🎯 Для просмотра данных в браузере:")
    print("   http://127.0.0.1:5000")
    print("\n📊 Для проверки через API:")
    print("   http://127.0.0.1:5000/api/parser-status") 