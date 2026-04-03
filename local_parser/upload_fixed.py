#!/usr/bin/env python3
"""
ИСПРАВЛЕННАЯ загрузка на удаленный сервер
Решает проблему с ошибкой 'characteristics' на сервере
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
SERVER_URL = "https://k4db-jl2g-6d7c.gw-1a.dockhost.net"
TIMEOUT = 120

def clean_product_data(product):
    """Очистка и нормализация данных товара"""
    cleaned = {}
    
    # Обязательные поля
    cleaned['name'] = str(product.get('name', 'Неизвестный товар')).strip()
    cleaned['price'] = float(product.get('price', 0))
    cleaned['url'] = str(product.get('url', '')).strip()
    
    # Опциональные поля
    if 'description' in product:
        cleaned['description'] = str(product['description']).strip()
    
    if 'image_url' in product:
        cleaned['image_url'] = str(product['image_url']).strip()
    
    if 'availability' in product:
        cleaned['availability'] = bool(product['availability'])
    
    # Категории - обязательно должны быть списком
    if 'categories' in product:
        categories = product['categories']
        if isinstance(categories, list):
            cleaned['categories'] = []
            for cat in categories:
                if isinstance(cat, dict) and 'name' in cat:
                    cleaned['categories'].append({
                        'name': str(cat['name']).strip(),
                        'url': str(cat.get('url', '')).strip()
                    })
                elif isinstance(cat, str):
                    cleaned['categories'].append({
                        'name': str(cat).strip(),
                        'url': ''
                    })
        else:
            cleaned['categories'] = []
    else:
        cleaned['categories'] = []
    
    # Характеристики - исправляем проблему с 'characteristics'
    if 'characteristics' in product:
        chars = product['characteristics']
        if isinstance(chars, dict):
            cleaned['characteristics'] = {}
            for key, value in chars.items():
                if key and value is not None:
                    cleaned['characteristics'][str(key).strip()] = str(value).strip()
        elif isinstance(chars, list):
            cleaned['characteristics'] = {}
            for item in chars:
                if isinstance(item, dict):
                    for key, value in item.items():
                        if key and value is not None:
                            cleaned['characteristics'][str(key).strip()] = str(value).strip()
        else:
            cleaned['characteristics'] = {}
    else:
        cleaned['characteristics'] = {}
    
    # Убираем пустые значения
    result = {}
    for key, value in cleaned.items():
        if value is not None and value != '' and value != [] and value != {}:
            result[key] = value
    
    return result

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
        
        # ОЧИЩАЕМ И НОРМАЛИЗУЕМ ДАННЫЕ
        logger.info("🧹 Очищаю и нормализую данные...")
        cleaned_products = []
        
        for i, product in enumerate(products):
            try:
                cleaned_product = clean_product_data(product)
                if cleaned_product.get('name') and cleaned_product.get('price', 0) > 0:
                    cleaned_products.append(cleaned_product)
                else:
                    logger.warning(f"⚠️  Пропускаю товар {i+1}: некорректные данные")
            except Exception as e:
                logger.warning(f"⚠️  Ошибка очистки товара {i+1}: {e}")
                continue
        
        if not cleaned_products:
            logger.error("❌ Нет валидных товаров после очистки")
            return False
        
        logger.info(f"✅ Подготовлено товаров: {len(cleaned_products)}")
        
        # Определяем категорию
        category = "unknown"
        if cleaned_products:
            categories = cleaned_products[0].get('categories', [])
            for cat in reversed(categories):
                name = cat.get('name', '').strip()
                if name and name not in ['Комплектующие для ПК', 'Основные комплектующие для ПК']:
                    category = name
                    break
        
        logger.info(f"📂 Категория: {category}")
        
        # Подготовка данных в правильном формате
        payload = {
            'products': cleaned_products,
            'source': 'fixed_upload',
            'upload_type': 'local_parser',
            'category': category,
            'timestamp': datetime.now().isoformat(),
            'product_count': len(cleaned_products),
            'version': '2.0_fixed'
        }
        
        # Создаем сессию
        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'FixedUpload/2.0',
            'Accept': 'application/json'
        })
        session.verify = False
        
        # Загружаем на проверенный endpoint
        upload_url = f"{url}/api/upload-products"
        logger.info(f"🚀 Загружаю на: {upload_url}")
        
        response = session.post(upload_url, json=payload, timeout=TIMEOUT)
        
        logger.info(f"📡 Ответ сервера: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"✅ УСПЕШНО ЗАГРУЖЕНО!")
                logger.info(f"   📝 Сообщение: {result.get('message', 'OK')}")
                
                if 'import_result' in result:
                    import_result = result['import_result']
                    added = import_result.get('added_count', 0)
                    errors = import_result.get('error_count', 0)
                    
                    logger.info(f"   📊 Добавлено: {added} товаров")
                    if errors > 0:
                        logger.warning(f"   ⚠️  Ошибок: {errors}")
                        
                        # Показываем первые ошибки
                        if 'results' in import_result:
                            error_results = [r for r in import_result['results'] if 'error' in r]
                            for i, error_result in enumerate(error_results[:3]):
                                logger.warning(f"      Ошибка {i+1}: {error_result.get('error', 'Unknown')[:100]}...")
                    
                else:
                    logger.info(f"   📊 Импортировано: {result.get('imported_count', len(cleaned_products))} товаров")
                
                return True
                
            except json.JSONDecodeError:
                logger.info(f"✅ Загрузка успешна (ответ не JSON)")
                logger.info(f"   📄 Ответ: {response.text[:200]}...")
                return True
                
        else:
            logger.error(f"❌ Ошибка {response.status_code}")
            logger.error(f"   📄 Ответ: {response.text[:300]}...")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        return False

def test_connection(url):
    """Тестирование подключения"""
    try:
        session = requests.Session()
        session.verify = False
        
        test_url = f"{url}/api/health"
        response = session.get(test_url, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                logger.info(f"✅ Сервер доступен: {data.get('server', 'unknown')}")
                logger.info(f"   📊 Товаров в базе: {data.get('product_count', 0)}")
                return True
            except:
                logger.info(f"✅ Сервер доступен")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        return False

def main():
    """Основная функция"""
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                   🛠️  ИСПРАВЛЕННАЯ ЗАГРУЗКА НА СЕРВЕР                      ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    logger.info(f"🎯 Сервер: {SERVER_URL}")
    logger.info(f"🔧 Версия: 2.0 (исправлены ошибки с characteristics)")
    
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
        size = os.path.getsize(path) / 1024
        logger.info(f"   {i}. {desc}: {path} ({size:.1f} KB)")
    
    # Выбираем файл (берем самый свежий)
    selected_file = files[0][1]
    logger.info(f"📤 Загружаю: {selected_file}")
    
    # Загружаем
    if upload_data(selected_file, SERVER_URL):
        logger.info(f"🎉 ЗАГРУЗКА ЗАВЕРШЕНА УСПЕШНО!")
        logger.info(f"🌐 Проверьте результат: {SERVER_URL}")
        logger.info(f"💡 Теперь данные доступны на вашем сайте")
    else:
        logger.error("❌ Загрузка не удалась")
        logger.info("💡 Попробуйте diagnose_servers.bat для диагностики")
    
    print()
    input("Нажмите Enter для выхода...")
    return 0

if __name__ == "__main__":
    exit(main()) 