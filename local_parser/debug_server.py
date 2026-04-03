#!/usr/bin/env python3
"""
Детальная диагностика серверов
"""

import requests
import json
import urllib3
from datetime import datetime

# Отключаем SSL предупреждения
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_server(base_url, name):
    """Тестирование сервера"""
    print(f"\n{'='*60}")
    print(f"🔍 ДИАГНОСТИКА: {name}")
    print(f"🌐 URL: {base_url}")
    print(f"{'='*60}")
    
    session = requests.Session()
    session.verify = False
    session.headers.update({
        'User-Agent': 'ServerDiagnostic/1.0',
        'Accept': 'application/json, text/html, */*'
    })
    
    # Тестируем различные endpoints
    endpoints = [
        ("", "Главная страница"),
        ("/", "Корень"),
        ("/api", "API корень"),
        ("/api/health", "Health check"),
        ("/api/status", "Статус"),
        ("/api/parser-status", "Статус парсера"),
        ("/api/upload-products", "Загрузка товаров"),
        ("/upload-products", "Альтернативная загрузка"),
        ("/api/upload", "Общая загрузка"),
        ("/upload", "Простая загрузка")
    ]
    
    results = {}
    
    for endpoint, description in endpoints:
        test_url = f"{base_url}{endpoint}"
        try:
            print(f"\n📍 Проверяю: {description}")
            print(f"   URL: {test_url}")
            
            # GET запрос
            response = session.get(test_url, timeout=10)
            status = response.status_code
            content_type = response.headers.get('content-type', 'unknown')
            
            print(f"   ✅ GET {status} | {content_type}")
            
            # Показываем начало ответа
            if status == 200:
                text = response.text[:200].strip()
                if text:
                    print(f"   📄 Ответ: {text}...")
                
                # Если это JSON
                if 'application/json' in content_type:
                    try:
                        data = response.json()
                        print(f"   📊 JSON: {data}")
                    except:
                        pass
            elif status == 404:
                print(f"   ❌ Не найден")
            elif status == 405:
                print(f"   ⚠️  Метод не разрешен (возможно, нужен POST)")
                
                # Пробуем POST для upload endpoints
                if 'upload' in endpoint:
                    try:
                        test_data = {
                            'products': [{'name': 'test', 'price': 100}],
                            'source': 'diagnostic',
                            'upload_type': 'test'
                        }
                        post_response = session.post(test_url, json=test_data, timeout=10)
                        print(f"   🔄 POST {post_response.status_code}")
                        if post_response.status_code != 405:
                            text = post_response.text[:200].strip()
                            print(f"   📄 POST ответ: {text}...")
                    except Exception as e:
                        print(f"   ❌ POST ошибка: {e}")
            else:
                print(f"   ⚠️  Код {status}")
                
            results[endpoint] = {
                'status': status,
                'content_type': content_type,
                'working': status in [200, 201, 202]
            }
                
        except requests.exceptions.SSLError as e:
            print(f"   🔒 SSL ошибка: {e}")
            results[endpoint] = {'status': 'SSL_ERROR', 'working': False}
        except requests.exceptions.ConnectionError as e:
            print(f"   🚫 Не удается подключиться: {e}")
            results[endpoint] = {'status': 'CONNECTION_ERROR', 'working': False}
        except requests.exceptions.Timeout:
            print(f"   ⏰ Таймаут")
            results[endpoint] = {'status': 'TIMEOUT', 'working': False}
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            results[endpoint] = {'status': f'ERROR: {e}', 'working': False}
    
    # Итоги
    print(f"\n📊 ИТОГИ для {name}:")
    working_endpoints = [ep for ep, res in results.items() if res.get('working')]
    if working_endpoints:
        print(f"   ✅ Работающие endpoints: {', '.join(working_endpoints)}")
    else:
        print(f"   ❌ Рабочих endpoints не найдено")
    
    return results

def main():
    """Основная функция"""
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                    🔍 ДИАГНОСТИКА СЕРВЕРОВ                                   ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    
    # Проверяем оба сервера
    servers = [
        ("http://k4db-jl2g-6d7c.gw-1a.dockhost.net", "Текущий сервер (HTTP)"),
        ("https://k4db-jl2g-6d7c.gw-1a.dockhost.net", "Текущий сервер (HTTPS)"),
        ("https://pcconf.ru", "Новый домен (HTTPS)"),
        ("http://pcconf.ru", "Новый домен (HTTP)"),
        ("http://31.186.100.50", "По IP адресу (HTTP)"),
        ("https://31.186.100.50", "По IP адресу (HTTPS)")
    ]
    
    all_results = {}
    
    for url, name in servers:
        try:
            results = test_server(url, name)
            all_results[url] = results
        except KeyboardInterrupt:
            print("\n\n⏹️ Прервано пользователем")
            break
        except Exception as e:
            print(f"\n❌ Критическая ошибка для {name}: {e}")
    
    # Финальный отчет
    print(f"\n{'='*80}")
    print("📋 ФИНАЛЬНЫЙ ОТЧЕТ")
    print(f"{'='*80}")
    
    for url, results in all_results.items():
        working_count = sum(1 for res in results.values() if res.get('working'))
        total_count = len(results)
        print(f"\n🌐 {url}")
        print(f"   ✅ Работает: {working_count}/{total_count} endpoints")
        
        if working_count > 0:
            working = [ep for ep, res in results.items() if res.get('working')]
            print(f"   📍 Рабочие: {', '.join(working)}")
    
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    
    # Анализируем результаты
    has_working_server = False
    for url, results in all_results.items():
        working_endpoints = [ep for ep, res in results.items() if res.get('working')]
        if working_endpoints:
            has_working_server = True
            print(f"   ✅ Используйте {url}")
            
            # Проверяем наличие upload endpoints
            upload_endpoints = [ep for ep in working_endpoints if 'upload' in ep]
            if upload_endpoints:
                print(f"      📤 Доступна загрузка через: {', '.join(upload_endpoints)}")
            else:
                print(f"      ⚠️  Загрузка недоступна - нужно настроить API")
            break
    
    if not has_working_server:
        print(f"   ❌ Все серверы недоступны")
        print(f"   💡 Возможные причины:")
        print(f"      • Серверы не запущены")
        print(f"      • Неправильная конфигурация")
        print(f"      • Проблемы с сетью")
        print(f"      • Нужно развернуть приложение")
    
    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main() 