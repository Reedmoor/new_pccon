#!/usr/bin/env python3
"""
PCCONF.RU Uploader
Отправка данных парсера на pcconf.ru
"""

import os
import sys
import json
import logging
import requests
import urllib3
import time
import glob
from pathlib import Path
from datetime import datetime
import argparse

# Отключаем предупреждения
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('upload_to_pcconf.log')
    ]
)
logger = logging.getLogger('upload_to_pcconf')

# URL сервера - используем HTTP
PCCONF_URL = "http://pcconf.ru"
TIMEOUT = 180  # увеличенный таймаут для больших файлов

class PCConfUploader:
    def __init__(self, server_url=None):
        """
        Загрузчик данных на pcconf.ru
        
        Args:
            server_url: URL сервера (по умолчанию: PCCONF_URL)
        """
        # Используем HTTP версию URL
        if server_url:
            if server_url.startswith("https://"):
                self.server_url = server_url.replace("https://", "http://")
                logger.info(f"[HTTP-ONLY] Converted HTTPS to HTTP: {self.server_url}")
            else:
                self.server_url = server_url.rstrip('/')
        else:
            self.server_url = PCCONF_URL
            
        # Создаем простую сессию
        self.session = requests.Session()
        self.session.verify = False
        
        logger.info(f"PCConf Uploader initialized")
        logger.info(f"Target server: {self.server_url}")
        logger.info(f"Protocol: HTTP only")
    
    def test_connection(self) -> bool:
        """Тестирование соединения с сервером"""
        try:
            logger.info(f"Testing connection to server: {self.server_url}")
            
            # Пробуем разные endpoints для проверки
            test_endpoints = [
                "/api/health",
                "/health", 
                "/",
                "/api/status",
                "/nginx-health"  # Добавлен nginx health check
            ]
            
            for endpoint in test_endpoints:
                try:
                    url = f"{self.server_url}{endpoint}"
                    logger.info(f"Trying endpoint: {url}")
                    
                    response = self.session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        logger.info(f"[SUCCESS] Connection successful via {endpoint}")
                        try:
                            result = response.json()
                            logger.info(f"   Response: {result}")
                        except:
                            logger.info(f"   Response (text): {response.text[:100]}")
                        return True
                    else:
                        logger.info(f"   Endpoint {endpoint} returned status {response.status_code}")
                        
                except Exception as req_err:
                    logger.warning(f"   Error for {endpoint}: {req_err}")
                    continue
            
            logger.error("[ERROR] All endpoints failed")
            return False
                
        except Exception as e:
            logger.error(f"[ERROR] Failed to connect to server: {e}")
            return False
    
    def test_connection_with_fallback(self) -> bool:
        """Тестирование соединения с автоматическим переключением на HTTP"""
        # Сначала пробуем обычное соединение
        if self.test_connection():
            return True
            
        # Если не получилось и используется HTTPS, пробуем HTTP
        if self.server_url.startswith("https://"):
            logger.info("[RETRY] Trying HTTP connection instead of HTTPS...")
            http_url = self.server_url.replace("https://", "http://")
            self.server_url = http_url
            self.session.headers.update({'Host': http_url.split('//')[1]})
            
            # Пробуем подключиться снова
            return self.test_connection()
            
        return False
    
    def detect_category(self, products):
        """Определяет категорию товаров"""
        if not products:
            return "unknown"
        
        first_product = products[0]
        categories = first_product.get('categories', [])
        
        for category in reversed(categories):
            name = category.get('name', '').strip()
            if name and name not in ['Комплектующие для ПК', 'Основные комплектующие для ПК']:
                return name
        
        if categories:
            return categories[-1].get('name', 'unknown')
        
        return "unknown"
    
    def upload_products(self, products, source="local_parser") -> bool:
        """Отправка данных на сервер"""
        try:
            logger.info(f"[UPLOAD] Sending {len(products)} products to pcconf.ru...")
            
            category = self.detect_category(products)
            
            # Подготавливаем payload для API
            payload = {
                'products': products,
                'source': source,
                'upload_type': 'local_parser',
                'category': category,
                'timestamp': datetime.now().isoformat(),
                'product_count': len(products)
            }
            
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
                    url = f"{self.server_url}{endpoint}"
                    logger.info(f"Trying upload to: {url}")
                    
                    response = self.session.post(
                        url,
                        json=payload,
                        timeout=TIMEOUT
                    )
                    
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            logger.info(f"[SUCCESS] Successfully uploaded data: {result.get('message', 'Success')}")
                            logger.info(f"   Imported: {result.get('imported_count', 0)} products")
                        except:
                            logger.info(f"[SUCCESS] Upload successful (status 200)")
                            logger.info(f"   Response: {response.text[:200]}...")
                        return True
                    elif response.status_code in [404, 405]:
                        logger.info(f"   Endpoint {endpoint} not found, trying next...")
                        continue
                    else:
                        logger.error(f"   Endpoint {endpoint} returned status {response.status_code}")
                        logger.error(f"   Response: {response.text[:200]}")
                        
                except requests.exceptions.RequestException as req_err:
                    logger.error(f"   Request error for {endpoint}: {req_err}")
                    continue
            
            logger.error("[ERROR] All endpoints failed")
            return False
                
        except Exception as e:
            logger.error(f"[ERROR] Failed to upload products: {e}")
            return False
    
    def upload_file(self, file_path) -> bool:
        """Загрузка данных из файла"""
        try:
            logger.info(f"[FILE] Reading file: {file_path}")
            
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
                logger.error("[ERROR] No products found in file")
                return False
            
            logger.info(f"[INFO] Found {len(products)} products")
            
            # Загружаем продукты
            return self.upload_products(products)
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to read file: {e}")
            return False
    
    def find_latest_parser_data(self):
        """Поиск последних данных парсера"""
        try:
            # Ищем в папке data
            project_root = Path(__file__).resolve().parent.parent
            data_dir = project_root / "data"
            
            if not data_dir.exists():
                logger.error(f"[ERROR] Data directory not found: {data_dir}")
                return None
            
            # Ищем файлы с префиксом local_parser_data_
            local_files = list(data_dir.glob("local_parser_data_*.json"))
            if not local_files:
                logger.error("[ERROR] No local_parser_data files found")
                return None
            
            # Фильтруем файлы по минимальному размеру
            MIN_FILE_SIZE = 100000  # 100KB минимум
            valid_files = [f for f in local_files if f.stat().st_size > MIN_FILE_SIZE]
            
            if not valid_files:
                logger.warning("[WARNING] All found files are too small, possibly corrupted")
                valid_files = local_files
            
            # Файлы за последние 24 часа
            now = time.time()
            recent_files = [f for f in valid_files if (now - f.stat().st_mtime) < 86400]
            
            if recent_files:
                # Среди недавних файлов выбираем самый большой
                selected_file = max(recent_files, key=lambda f: f.stat().st_size)
                logger.info(f"[FILE] Selected recent file: {selected_file.name} ({selected_file.stat().st_size:,} bytes)")
            else:
                # Берем самый большой среди всех валидных файлов
                selected_file = max(valid_files, key=lambda f: f.stat().st_size)
                logger.info(f"[FILE] Selected largest file: {selected_file.name} ({selected_file.stat().st_size:,} bytes)")
            
            return selected_file
            
        except Exception as e:
            logger.error(f"[ERROR] Error finding latest parser data: {e}")
            return None
    
    def upload_latest_parser_data(self) -> bool:
        """Загрузка последних данных парсера"""
        latest_file = self.find_latest_parser_data()
        
        if not latest_file:
            return False
        
        return self.upload_file(latest_file)

def main():
    """Основная функция"""
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description='Загрузка данных на pcconf.ru')
    parser.add_argument('--url', type=str, help='Альтернативный URL сервера')
    parser.add_argument('--file', type=str, help='Путь к файлу для загрузки')
    args = parser.parse_args()
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                      ЗАГРУЗКА НА PCCONF.RU                                  ║")
    print("║                         HTTP ONLY                                            ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Создаем загрузчик
    server_url = args.url if args.url else PCCONF_URL
    
    # Конвертируем HTTPS в HTTP для совместимости
    if server_url.startswith("https://"):
        server_url = server_url.replace("https://", "http://")
        print(f"[HTTP-ONLY] Converted to HTTP: {server_url}")
    
    uploader = PCConfUploader(server_url)
    
    logger.info(f"[CONFIG] Target server: {server_url}")
    logger.info(f"[CONFIG] Protocol: HTTP only")
    
    # Тестируем соединение
    print("🔍 Тестирование соединения...")
    if not uploader.test_connection_with_fallback():
        print("❌ ОШИБКА: Не удалось подключиться к серверу")
        print("   Проверьте:")
        print("   1. Запущен ли сервер")
        print("   2. Доступен ли сервер по HTTP")
        print("   3. Правильность URL")
        return 1
    
    print("✅ Соединение установлено")
    
    # Загружаем данные
    if args.file:
        print(f"📁 Загрузка из файла: {args.file}")
        success = uploader.upload_file(args.file)
    else:
        print("🔍 Поиск последних данных парсера...")
        success = uploader.upload_latest_parser_data()
    
    if success:
        print("✅ УСПЕХ: Данные успешно загружены!")
        return 0
    else:
        print("❌ ОШИБКА: Не удалось загрузить данные")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 