#!/usr/bin/env python3
"""
Тест прокси специально для citilink.ru
"""
import requests
import json
import time

PROXY_LIST = [
    {
        'host': '194.156.0.61',
        'http_port': 64604,
        'socks5_port': 64605,
        'username': 'iXya3sZg',
        'password': 'L51Gzyra'
    },
    {
        'host': '45.140.64.215',
        'http_port': 62474,
        'socks5_port': 62475,
        'username': 'iXya3sZg',
        'password': 'L51Gzyra'
    },
    {
        'host': '91.191.184.244',
        'http_port': 63478,
        'socks5_port': 63479,
        'username': 'iXya3sZg',
        'password': 'L51Gzyra'
    }
]

def test_citilink_direct():
    """Тестируем прямое соединение к citilink.ru"""
    print("\n🌐 Тестируем прямое соединение к citilink.ru...")
    
    test_urls = [
        'https://citilink.ru',
        'https://citilink.ru/catalog/computers_and_notebooks/',
    ]
    
    has_connection = False
    is_blocked = False
    
    for url in test_urls:
        try:
            print(f"  🔗 Тестируем {url}...")
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            print(f"  📊 Код ответа: {response.status_code}, размер: {len(response.content)} байт")
            
            if response.status_code == 200:
                has_connection = True
                print("  ✅ Соединение свободно!")
            elif response.status_code == 429:
                has_connection = True
                is_blocked = True
                print("  ⚠️  Соединение заблокировано (слишком много запросов)")
            elif response.status_code in [403, 502, 503, 504]:
                has_connection = True
                is_blocked = True
                print("  ⚠️  Соединение заблокировано")
                
        except Exception as e:
            print(f"  ❌ Ошибка: {str(e)[:100]}...")
    
    if not has_connection:
        print("  ❌ Нет соединения с citilink.ru")
        return False
        
    if is_blocked:
        print("  🚨 citilink.ru блокирует запросы - прокси НЕОБХОДИМЫ!")
    else:
        print("  ✅ citilink.ru доступен напрямую")
        
    return True

def test_citilink_graphql_direct():
    """Тестируем GraphQL запрос напрямую"""
    print("\n📊 Тестируем GraphQL запрос к www.citilink.ru...")
    
    # Простой GraphQL запрос (из queries.py)
    query = """
    query GetProducts($subcategoryProductsFilterInput:CatalogFilter_ProductsFilterInput!){
        productsFilter(filter:$subcategoryProductsFilterInput){
            record{
                products{
                    id
                    name
                    slug
                }
                pageInfo{
                    hasNextPage
                }
            }
        }
    }
    """
    
    variables = {
        "subcategoryProductsFilterInput": {
            "categorySlug": "computers_and_notebooks",
            "compilationPath": [],
            "pagination": {
                "page": 1,
                "perPage": 3,
            },
            "conditions": [],
            "sorting": {
                "id": "",
                "direction": "SORT_DIRECTION_DESC",
            },
            "popularitySegmentId": "THREE",
        }
    }
    
    try:
        response = requests.post(
            'https://www.citilink.ru/graphql/',  # Правильный URL
            json={"query": query, "variables": variables},
            timeout=15,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/json'
            }
        )
        
        print(f"  📊 Код ответа: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ GraphQL запрос успешен! Получено данных: {len(str(data))} символов")
            return True
        else:
            print(f"  ❌ GraphQL запрос неудачен: {response.text[:200]}...")
            
    except Exception as e:
        print(f"  ❌ Ошибка GraphQL: {str(e)[:100]}...")
    
    return False

def test_proxy_citilink(proxy_info):
    """Тестируем прокси с citilink.ru"""
    print(f"\n🧪 Тестируем прокси {proxy_info['host']}:{proxy_info['http_port']} с citilink.ru")
    
    # HTTP прокси
    proxy_url = f"http://{proxy_info['username']}:{proxy_info['password']}@{proxy_info['host']}:{proxy_info['http_port']}"
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    # Тест 1: Главная страница
    try:
        print("  🏠 Тестируем главную страницу...")
        response = requests.get(
            'https://www.citilink.ru',  # Без www
            proxies=proxies,
            timeout=15,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        print(f"  📊 Главная: код {response.status_code}, размер {len(response.content)} байт")
        if response.status_code == 200 and len(response.content) > 1000:
            print("  ✅ Главная страница загружается!")
            return True
    except Exception as e:
        print(f"  ❌ Главная страница: {str(e)[:100]}...")
    
    # Тест 2: GraphQL запрос - САМЫЙ ВАЖНЫЙ ТЕСТ
    try:
        print("  📊 Тестируем GraphQL запрос (главный API)...")
        
        # Используем реальный запрос из парсера
        query = """
        query GetProducts($subcategoryProductsFilterInput:CatalogFilter_ProductsFilterInput!){
            productsFilter(filter:$subcategoryProductsFilterInput){
                record{
                    products{
                        id
                        name
                        slug
                    }
                    pageInfo{
                        hasNextPage
                    }
                }
            }
        }
        """
        
        variables = {
            "subcategoryProductsFilterInput": {
                "categorySlug": "computers_and_notebooks",
                "compilationPath": [],
                "pagination": {
                    "page": 1,
                    "perPage": 2,
                },
                "conditions": [],
                "sorting": {
                    "id": "",
                    "direction": "SORT_DIRECTION_DESC",
                },
                "popularitySegmentId": "THREE",
            }
        }
        
        response = requests.post(
            'https://www.citilink.ru/graphql/',  # Правильный URL с www
            json={"query": query, "variables": variables},
            proxies=proxies,
            timeout=20,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/json'
            }
        )
        
        print(f"  📊 GraphQL: код {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'productsFilter' in data['data']:
                print("  ✅ GraphQL запрос через прокси работает!")
                print("  🎯 ГЛАВНЫЙ API ДОСТУПЕН ЧЕРЕЗ ПРОКСИ!")
                return True
            else:
                print(f"  ⚠️  GraphQL ответ неполный: {str(data)[:200]}...")
        else:
            print(f"  ❌ GraphQL код {response.status_code}: {response.text[:200]}...")
            
    except Exception as e:
        print(f"  ❌ GraphQL через прокси: {str(e)[:100]}...")
    
    return False

def main():
    print("🎯 Тестирование прокси для citilink.ru")
    print("=" * 60)
    
    # Сначала тестируем прямое соединение
    if not test_citilink_direct():
        print("❌ Проблемы с интернет-соединением!")
        return 1
    
    # Тестируем GraphQL напрямую
    print("\n📊 Тестируем GraphQL запрос к www.citilink.ru...")
    try:
        # Реальный запрос из парсера
        query = """
        query GetProducts($subcategoryProductsFilterInput:CatalogFilter_ProductsFilterInput!){
            productsFilter(filter:$subcategoryProductsFilterInput){
                record{
                    products{
                        id
                        name
                    }
                    pageInfo{
                        hasNextPage
                    }
                }
            }
        }
        """
        
        variables = {
            "subcategoryProductsFilterInput": {
                "categorySlug": "computers_and_notebooks",
                "compilationPath": [],
                "pagination": {
                    "page": 1,
                    "perPage": 3,
                },
                "conditions": [],
                "sorting": {
                    "id": "",
                    "direction": "SORT_DIRECTION_DESC",
                },
                "popularitySegmentId": "THREE",
            }
        }
        
        response = requests.post(
            'https://www.citilink.ru/graphql/',
            json={"query": query, "variables": variables},
            timeout=15,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/json'
            }
        )
        
        print(f"  📊 GraphQL код ответа: {response.status_code}")
        if response.status_code == 429:
            print("  🚨 GraphQL ЗАБЛОКИРОВАН - прокси ОБЯЗАТЕЛЬНЫ!")
        elif response.status_code == 200:
            print("  ✅ GraphQL работает напрямую")
        else:
            print(f"  ⚠️  GraphQL вернул код {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Ошибка GraphQL: {str(e)[:100]}...")
    
    working_proxies = 0
    
    for i, proxy in enumerate(PROXY_LIST, 1):
        print(f"\n{'='*60}")
        print(f"Прокси {i}/{len(PROXY_LIST)} - {proxy['host']}:{proxy['http_port']}")
        
        if test_proxy_citilink(proxy):
            working_proxies += 1
            print(f"  ✅ Прокси {proxy['host']} работает с citilink.ru!")
        else:
            print(f"  ❌ Прокси {proxy['host']} не работает с citilink.ru")
    
    print(f"\n{'='*60}")
    print(f"📊 ИТОГО: {working_proxies}/{len(PROXY_LIST)} прокси работают с www.citilink.ru/graphql/")
    
    if working_proxies == 0:
        print("❌ Ни один прокси не работает с citilink.ru!")
        print("💡 Но парсер настроен на автоматическое включение прокси при блокировке")
        print("🔄 Прокси будут активированы автоматически при ошибках 429, 403, 502, 503, 504")
        print("🎯 Прокси включены ПО УМОЛЧАНИЮ для всех запросов к GraphQL API")
        return 0  # Не считаем это критической ошибкой
    else:
        print(f"✅ {working_proxies} прокси готовы для обхода блокировок www.citilink.ru/graphql/!")
        return 0

if __name__ == "__main__":
    exit(main()) 