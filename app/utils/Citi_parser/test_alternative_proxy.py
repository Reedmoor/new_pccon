#!/usr/bin/env python3
"""
Альтернативный тест прокси с разными методами
"""
import requests
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

def test_proxy_simple(proxy_info):
    """Простой тест прокси"""
    print(f"\n🧪 Тестируем прокси: {proxy_info['host']}:{proxy_info['http_port']}")
    
    # HTTP прокси
    proxy_url = f"http://{proxy_info['username']}:{proxy_info['password']}@{proxy_info['host']}:{proxy_info['http_port']}"
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    test_urls = [
        'http://httpbin.org/ip',  # HTTP вместо HTTPS
        'https://httpbin.org/ip',  # HTTPS
        'http://icanhazip.com',    # Альтернативный сервис
    ]
    
    for url in test_urls:
        try:
            print(f"  🔗 Тестируем {url}...")
            response = requests.get(url, proxies=proxies, timeout=10)
            if response.status_code == 200:
                print(f"  ✅ Успешно! Ответ: {response.text[:100]}...")
                return True
            else:
                print(f"  ❌ Код ответа: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Ошибка: {str(e)[:100]}...")
    
    return False

def test_proxy_without_auth(proxy_info):
    """Тест прокси без авторизации (на случай если она не нужна)"""
    print(f"\n🔓 Тестируем без авторизации: {proxy_info['host']}:{proxy_info['http_port']}")
    
    proxy_url = f"http://{proxy_info['host']}:{proxy_info['http_port']}"
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    try:
        response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=5)
        if response.status_code == 200:
            print(f"  ✅ Работает без авторизации! IP: {response.json().get('origin', 'unknown')}")
            return True
        else:
            print(f"  ❌ Код ответа: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Ошибка: {str(e)[:100]}...")
    
    return False

def test_direct_connection():
    """Тест прямого соединения для сравнения"""
    print(f"\n🌐 Тестируем прямое соединение...")
    try:
        response = requests.get('http://httpbin.org/ip', timeout=5)
        if response.status_code == 200:
            ip = response.json().get('origin', 'unknown')
            print(f"  ✅ Прямое соединение работает. Ваш IP: {ip}")
            return True
    except Exception as e:
        print(f"  ❌ Прямое соединение не работает: {e}")
    return False

def main():
    print("🔍 Детальное тестирование прокси")
    print("=" * 60)
    
    # Сначала тестируем прямое соединение
    if not test_direct_connection():
        print("❌ Проблемы с интернет-соединением!")
        return 1
    
    working_proxies = 0
    
    for i, proxy in enumerate(PROXY_LIST, 1):
        print(f"\n{'='*60}")
        print(f"Прокси {i}/{len(PROXY_LIST)}")
        
        # Тест с авторизацией
        if test_proxy_simple(proxy):
            working_proxies += 1
            continue
            
        # Тест без авторизации
        if test_proxy_without_auth(proxy):
            working_proxies += 1
            continue
            
        print(f"  💀 Прокси {proxy['host']} полностью не работает")
    
    print(f"\n{'='*60}")
    print(f"📊 ИТОГО: {working_proxies}/{len(PROXY_LIST)} прокси работают")
    
    if working_proxies == 0:
        print("❌ Ни один прокси не работает!")
        print("💡 Возможные причины:")
        print("   - Срок действия прокси истек")
        print("   - Неверные данные авторизации")
        print("   - Прокси заблокированы провайдером")
        print("   - Прокси требуют специальной настройки")
        return 1
    else:
        print(f"✅ {working_proxies} прокси готовы к использованию!")
        return 0

if __name__ == "__main__":
    exit(main()) 