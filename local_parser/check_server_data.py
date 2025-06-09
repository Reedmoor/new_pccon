#!/usr/bin/env python3
"""
Скрипт для проверки данных на Docker сервере
"""

import requests
import json
from datetime import datetime

def check_docker_server():
    """Проверка данных на Docker сервере"""
    server_url = "http://127.0.0.1:5000"
    
    print("🔍 Проверка данных на Docker сервере...")
    print(f"📡 Сервер: {server_url}")
    print("=" * 50)
    
    try:
        # Проверяем API статуса
        response = requests.get(f"{server_url}/api/parser-status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            uploads = data.get('recent_uploads', [])
            
            print(f"✅ Сервер доступен (статус: {response.status_code})")
            print(f"📊 Всего загрузок: {len(uploads)}")
            
            if uploads:
                print("\n📋 Последние загрузки:")
                total_products = 0
                
                for i, upload in enumerate(uploads[:10], 1):
                    filename = upload.get('filename', 'Unknown')
                    product_count = upload.get('product_count', 0)
                    upload_time = upload.get('upload_time', '')
                    file_size = upload.get('file_size', 0)
                    
                    total_products += product_count
                    
                    # Форматируем время
                    try:
                        dt = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                        time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        time_str = upload_time
                    
                    size_kb = file_size / 1024 if file_size > 0 else 0
                    
                    print(f"  {i:2d}. {filename}")
                    print(f"      📦 {product_count:,} товаров")
                    print(f"      🕒 {time_str}")
                    print(f"      💾 {size_kb:.1f} KB")
                    print()
                
                print(f"🎯 Общее количество товаров во всех загрузках: {total_products:,}")
                
                # Показываем самую свежую загрузку
                latest = uploads[0]
                print(f"\n🔥 Последняя загрузка:")
                print(f"   Файл: {latest.get('filename')}")
                print(f"   Товаров: {latest.get('product_count')} ")
                print(f"   Время: {latest.get('upload_time')}")
                
            else:
                print("❌ Загрузок не найдено")
                
        else:
            print(f"❌ Ошибка сервера: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к серверу")
        print("   Убедитесь что Docker сервер запущен на порту 5000")
        
    except requests.exceptions.Timeout:
        print("❌ Таймаут подключения к серверу")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def check_web_interface():
    """Проверка веб-интерфейса"""
    server_url = "http://127.0.0.1:5000"
    
    print("\n" + "=" * 50)
    print("🌐 Проверка веб-интерфейса...")
    
    try:
        response = requests.get(server_url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Веб-интерфейс доступен: {server_url}")
            print("   Откройте ссылку в браузере для просмотра товаров")
        else:
            print(f"❌ Веб-интерфейс недоступен: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка веб-интерфейса: {e}")

if __name__ == "__main__":
    check_docker_server()
    check_web_interface()
    
    print("\n" + "=" * 50)
    print("🎯 Для просмотра данных в браузере:")
    print("   http://127.0.0.1:5000")
    print("\n📊 Для проверки через API:")
    print("   http://127.0.0.1:5000/api/parser-status") 