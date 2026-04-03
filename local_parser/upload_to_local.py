#!/usr/bin/env python3
"""
Загрузка данных на локальный Docker сервер
Исправлена для работы с локальными endpoints
"""

import os
import sys
import json
import logging
import requests
import urllib3
from pathlib import Path
from datetime import datetime

# Отключаем предупреждения
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

# Настройки для локального Docker
LOCAL_SERVER_URL = "http://127.0.0.1:5000"
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

def test_local_connection():
    """Тестирование подключения к локальному серверу"""
    try:
        session = requests.Session()
        session.timeout = 10
        
        # Пробуем разные endpoints
        endpoints = ["/", "/api/health", "/health", "/status", "/api/status"]
        
        for endpoint in endpoints:
            try:
                test_url = f"{LOCAL_SERVER_URL}{endpoint}"
                logger.info(f"🧪 Тестирую: {test_url}")
                
                response = session.get(test_url, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"✅ Локальный сервер доступен через: {endpoint}")
                    logger.info(f"   Статус: {response.status_code}")
                    
                    # Попробуем распарсить JSON
                    try:
                        data = response.json()
                        logger.info(f"   JSON ответ: {data}")
                    except:
                        logger.info(f"   HTML ответ (первые 100 символов): {response.text[:100]}...")
                    
                    return True
                else:
                    logger.info(f"   {endpoint}: статус {response.status_code}")
                    
            except Exception as e:
                logger.info(f"   {endpoint}: ошибка {e}")
                continue
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Общая ошибка подключения: {e}")
        return False

def upload_to_local(file_path):
    """Загрузка данных на локальный сервер"""
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
            'source': 'local_upload',
            'upload_type': 'local_parser',
            'category': category,
            'timestamp': datetime.now().isoformat(),
            'product_count': len(products)
        }
        
        # Создаем сессию
        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'LocalUpload/1.0'
        })
        
        # Пробуем разные endpoints для загрузки
        upload_endpoints = [
            "/api/upload-products",
            "/upload-products", 
            "/api/upload",
            "/upload",
            "/api/parser/upload",
            "/parser/upload"
        ]
        
        for endpoint in upload_endpoints:
            try:
                upload_url = f"{LOCAL_SERVER_URL}{endpoint}"
                logger.info(f"🚀 Пробую загрузку на: {upload_url}")
                
                response = session.post(upload_url, json=payload, timeout=TIMEOUT)
                
                logger.info(f"   Ответ: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        logger.info(f"✅ УСПЕШНО ЗАГРУЖЕНО!")
                        logger.info(f"   📝 Результат: {result}")
                        return True
                    except:
                        logger.info(f"✅ Загрузка успешна (статус 200)")
                        logger.info(f"   📄 Ответ: {response.text[:200]}...")
                        return True
                        
                elif response.status_code == 404:
                    logger.info(f"   {endpoint}: не найден")
                    continue
                elif response.status_code == 405:
                    logger.info(f"   {endpoint}: метод не разрешен")
                    continue
                else:
                    logger.warning(f"   {endpoint}: статус {response.status_code}")
                    logger.warning(f"   Ответ: {response.text[:200]}...")
                    continue
                    
            except Exception as e:
                logger.warning(f"   {endpoint}: ошибка {e}")
                continue
        
        logger.error("❌ Все endpoints не работают")
        return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        return False

def main():
    """Основная функция"""
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                   🐳 ЗАГРУЗКА НА ЛОКАЛЬНЫЙ DOCKER                           ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    logger.info(f"🎯 Локальный сервер: {LOCAL_SERVER_URL}")
    logger.info(f"🐳 Docker должен быть запущен: docker-compose up -d")
    
    # Тестируем подключение
    logger.info("🧪 Проверяю подключение к локальному Docker...")
    if not test_local_connection():
        logger.error("❌ Не удается подключиться к локальному серверу")
        logger.info("💡 Проверьте:")
        logger.info("   • Запущен ли Docker: docker ps")
        logger.info("   • Порт 5000: netstat -an | findstr :5000")
        logger.info("   • Логи: docker logs pccon_web")
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
    
    # Выбираем файл (берем первый)
    selected_file = files[0][1]
    logger.info(f"📤 Загружаю: {selected_file}")
    
    # Загружаем
    if upload_to_local(selected_file):
        logger.info(f"🎉 ЗАГРУЗКА НА ЛОКАЛЬНЫЙ DOCKER ЗАВЕРШЕНА!")
        logger.info(f"🌐 Проверьте результат: {LOCAL_SERVER_URL}")
        logger.info(f"💡 Данные теперь доступны в локальном Docker")
    else:
        logger.error("❌ Загрузка не удалась")
        logger.info("💡 Проверьте логи Docker: docker logs pccon_web")
    
    print()
    input("Нажмите Enter для выхода...")
    return 0

if __name__ == "__main__":
    exit(main()) 