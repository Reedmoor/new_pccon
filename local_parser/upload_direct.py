#!/usr/bin/env python3
"""
Прямая загрузка на удаленный сервер - упрощенная версия
Использовать: python upload_direct.py
"""

import os
import sys
import json
import logging
import requests
import urllib3
from pathlib import Path
from datetime import datetime

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

# Настройки
SERVER_URL = "http://k4db-jl2g-6d7c.gw-1a.dockhost.net"
TIMEOUT = 120

def find_data_files():
    """Поиск файлов с данными"""
    files = []
    
    # Старый парсер
    old_parser_file = Path("../old_dns_parser/product_data.json")
    if old_parser_file.exists():
        files.append(("Старый парсер", str(old_parser_file)))
    
    # Локальные данные
    import glob
    data_files = glob.glob("../data/local_parser_data_*.json")
    if data_files:
        latest_file = max(data_files, key=os.path.getmtime)
        files.append(("Локальные данные", latest_file))
    
    return files

def upload_data(file_path, url):
    """Загрузка данных на сервер"""
    try:
        logger.info(f"📁 Читаю файл: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Извлекаем продукты
        if isinstance(data, dict):
            products = data.get('products', [])
            if not products and 'product_data' in data:
                products = data['product_data']
        else:
            products = data if isinstance(data, list) else []
        
        if not products:
            logger.error("❌ Нет товаров в файле")
            return False
        
        logger.info(f"📊 Найдено товаров: {len(products)}")
        
        # Определяем категорию
        category = "unknown"
        if products:
            categories = products[0].get('categories', [])
            for cat in reversed(categories):
                name = cat.get('name', '').strip()
                if name and name not in ['Комплектующие для ПК', 'Основные комплектующие для ПК']:
                    category = name
                    break
        
        logger.info(f"📂 Категория: {category}")
        
        # Подготовка данных
        payload = {
            'products': products,
            'source': 'direct_upload',
            'upload_type': 'local_parser',
            'category': category,
            'timestamp': datetime.now().isoformat(),
            'product_count': len(products)
        }
        
        # Создаем сессию
        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'DirectUpload/1.0'
        })
        session.verify = False
        
        # Пробуем разные endpoints
        endpoints = ["/api/upload-products", "/upload-products", "/api/upload"]
        
        for endpoint in endpoints:
            try:
                upload_url = f"{url}{endpoint}"
                logger.info(f"🚀 Загружаю на: {upload_url}")
                
                response = session.post(upload_url, json=payload, timeout=TIMEOUT)
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Успешно загружено: {result.get('message', 'OK')}")
                    logger.info(f"   Импортировано: {result.get('imported_count', len(products))} товаров")
                    return True
                elif response.status_code in [404, 405]:
                    logger.info(f"   Endpoint {endpoint} не найден, пробую следующий...")
                    continue
                else:
                    logger.error(f"   Ошибка {response.status_code}: {response.text[:200]}")
                    
            except requests.exceptions.SSLError:
                # Пробуем HTTP вместо HTTPS
                if url.startswith('https://'):
                    http_url = upload_url.replace('https://', 'http://')
                    logger.info(f"   Пробую HTTP: {http_url}")
                    try:
                        response = session.post(http_url, json=payload, timeout=TIMEOUT)
                        if response.status_code == 200:
                            result = response.json()
                            logger.info(f"✅ Успешно загружено через HTTP: {result.get('message', 'OK')}")
                            return True
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"   Ошибка для {endpoint}: {e}")
                continue
        
        logger.error("❌ Все endpoints не работают")
        return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        return False

def test_connection(url):
    """Тестирование подключения"""
    try:
        session = requests.Session()
        session.verify = False
        
        endpoints = ["/api/health", "/health", "/", ""]
        
        for endpoint in endpoints:
            try:
                test_url = f"{url}{endpoint}"
                response = session.get(test_url, timeout=15)
                
                if response.status_code == 200:
                    logger.info(f"✅ Подключение успешно через {endpoint}")
                    return True
                    
            except requests.exceptions.SSLError:
                if url.startswith('https://'):
                    http_url = test_url.replace('https://', 'http://')
                    try:
                        response = session.get(http_url, timeout=15)
                        if response.status_code == 200:
                            logger.info(f"✅ Подключение успешно через HTTP: {endpoint}")
                            return True
                    except:
                        continue
            except:
                continue
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        return False

def main():
    """Основная функция"""
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                   🚀 ПРЯМАЯ ЗАГРУЗКА НА УДАЛЕННЫЙ СЕРВЕР                    ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    logger.info(f"🎯 Сервер: {SERVER_URL}")
    
    # Тестируем подключение
    logger.info("🧪 Проверяю подключение...")
    if not test_connection(SERVER_URL):
        logger.error("❌ Не удается подключиться к серверу")
        input("\nНажмите Enter для выхода...")
        return 1
    
    # Ищем файлы
    logger.info("🔍 Ищу файлы с данными...")
    files = find_data_files()
    
    if not files:
        logger.error("❌ Файлы с данными не найдены")
        logger.info("💡 Сначала запустите парсинг: parse_category.bat")
        input("\nНажмите Enter для выхода...")
        return 1
    
    # Показываем файлы
    logger.info(f"📁 Найдено файлов: {len(files)}")
    for i, (desc, path) in enumerate(files, 1):
        logger.info(f"   {i}. {desc}: {path}")
    
    # Выбираем файл (берем первый)
    selected_file = files[0][1]
    logger.info(f"📤 Загружаю: {selected_file}")
    
    # Загружаем
    if upload_data(selected_file, SERVER_URL):
        logger.info(f"🎉 Загрузка завершена успешно!")
        logger.info(f"🌐 Проверьте результат: {SERVER_URL}")
    else:
        logger.error("❌ Ошибка загрузки")
        
        # Пробуем HTTPS если был HTTP
        if SERVER_URL.startswith('http://'):
            https_url = SERVER_URL.replace('http://', 'https://')
            logger.info(f"🔄 Пробую HTTPS: {https_url}")
            if upload_data(selected_file, https_url):
                logger.info(f"🎉 Загрузка через HTTPS успешна!")
                logger.info(f"🌐 Проверьте результат: {https_url}")
            else:
                logger.error("❌ HTTPS тоже не работает")
    
    print()
    input("Нажмите Enter для выхода...")
    return 0

if __name__ == "__main__":
    exit(main()) 