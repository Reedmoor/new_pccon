#!/usr/bin/env python3
"""
Финальный тест загрузки на удаленный сервер с правильной обработкой HTTPS
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import ssl

def test_upload():
    # Настройки
    server_url = "https://k4db-jl2g-6d7c.gw-1a.dockhost.net"  # Используем HTTPS
    data_file = "../data/local_parser_data_20250607_203655.json"
    
    print("🔄 Финальный тест удаленного сервера...")
    print(f"🎯 Сервер: {server_url}")
    
    # Создаем SSL контекст, который игнорирует ошибки сертификата
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Проверяем подключение
    try:
        health_req = urllib.request.Request(f"{server_url}/api/health")
        health_req.add_header('User-Agent', 'TestUpload/1.0')
        
        with urllib.request.urlopen(health_req, timeout=10, context=ssl_context) as response:
            health_data = json.loads(response.read().decode('utf-8'))
            print(f"✅ Сервер доступен: {health_data['server']}")
            print(f"📊 Товаров в базе: {health_data['product_count']}")
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
        'source': 'final_test',
        'upload_type': 'local_parser',
        'category': 'Видеокарты'
    }
    
    try:
        print("🚀 Отправляю данные через HTTPS...")
        print(f"🔗 URL: {server_url}/api/upload-products")
        
        # Подготавливаем данные
        json_data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        print(f"📊 Размер данных: {len(json_data)/1024:.1f} KB")
        
        # Создаем запрос
        req = urllib.request.Request(
            f"{server_url}/api/upload-products",
            data=json_data,
            method='POST'
        )
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        req.add_header('User-Agent', 'FinalTestUpload/1.0')
        req.add_header('Content-Length', str(len(json_data)))
        
        # Отправляем с SSL контекстом
        with urllib.request.urlopen(req, timeout=180, context=ssl_context) as response:
            status_code = response.getcode()
            print(f"📡 Статус ответа: {status_code}")
            
            if status_code == 200:
                result_data = response.read().decode('utf-8')
                result = json.loads(result_data)
                print("🎉 УСПЕШНО ЗАГРУЖЕНО!")
                print(f"   📊 Импортировано: {result.get('imported_count', 0)}")
                print(f"   📄 Сообщение: {result.get('message', 'N/A')}")
                if 'import_result' in result:
                    import_result = result['import_result']
                    print(f"   ✅ Добавлено: {import_result.get('added_count', 0)}")
                    print(f"   ❌ Ошибок: {import_result.get('error_count', 0)}")
            else:
                print(f"❌ Ошибка загрузки: {status_code}")
    
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP ошибка: {e.code} - {e.reason}")
        try:
            error_response = e.read().decode('utf-8')
            print(f"   Ответ: {error_response[:500]}...")
        except:
            pass
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

if __name__ == "__main__":
    test_upload()
    input("\nНажмите Enter для выхода...") 