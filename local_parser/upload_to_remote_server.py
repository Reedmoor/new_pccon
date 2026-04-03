#!/usr/bin/env python3
"""
Скрипт для отправки данных с локального парсера на удаленный захощенный сервер
Адаптация существующих скриптов для работы с удаленным сервером
"""

import os
import sys
import json
import logging
import requests
import argparse
import urllib3
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Отключаем предупреждения о непроверенных HTTPS запросах
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('upload_to_remote_server')

# URL сервера по умолчанию
DEFAULT_SERVER_URL = "http://k4db-jl2g-6d7c.gw-1a.dockhost.net"

class RemoteServerUploader:
    def __init__(self, remote_server_url=None, verify_ssl=False):
        """
        Загрузчик данных на удаленный сервер
        
        Args:
            remote_server_url: URL удаленного сервера (по умолчанию: k4db-jl2g-6d7c.gw-1a.dockhost.net)
            verify_ssl: Проверять ли SSL сертификаты (по умолчанию: False для захощенных серверов)
        """
        if remote_server_url is None:
            remote_server_url = DEFAULT_SERVER_URL
            
        self.remote_server_url = remote_server_url.rstrip('/')
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        
        # Настраиваем заголовки
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'LocalParser/1.0',
            'Accept': 'application/json'
        })
        
        # Отключаем проверку SSL для захощенных серверов
        self.session.verify = verify_ssl
        
        logger.info(f"Remote Server Uploader initialized")
        logger.info(f"Target server: {self.remote_server_url}")
        logger.info(f"SSL verification: {'enabled' if verify_ssl else 'disabled'}")
    
    def test_connection(self) -> bool:
        """Тестирование соединения с удаленным сервером"""
        try:
            logger.info(f"Testing connection to remote server: {self.remote_server_url}")
            
            # Пробуем разные endpoints для проверки
            test_endpoints = [
                "/api/health",
                "/health", 
                "/",
                ""
            ]
            
            for endpoint in test_endpoints:
                try:
                    url = f"{self.remote_server_url}{endpoint}"
                    logger.info(f"Trying endpoint: {url}")
                    
                    response = self.session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        logger.info(f"✅ Connection successful via {endpoint}")
                        try:
                            result = response.json()
                            logger.info(f"   Response: {result}")
                        except:
                            logger.info(f"   Response (text): {response.text[:100]}")
                        return True
                    else:
                        logger.info(f"   Endpoint {endpoint} returned status {response.status_code}")
                        
                except requests.exceptions.SSLError as ssl_err:
                    logger.warning(f"   SSL error for {endpoint}: {ssl_err}")
                    continue
                except requests.exceptions.RequestException as req_err:
                    logger.warning(f"   Request error for {endpoint}: {req_err}")
                    continue
            
            logger.error("❌ All endpoints failed")
            return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to remote server: {e}")
            return False
    
    def test_connection_with_fallback(self) -> bool:
        """Тестирование соединения с автоматическим переключением HTTPS/HTTP"""
        original_url = self.remote_server_url
        
        # Сначала пробуем исходный URL
        if self.test_connection():
            return True
        
        # Если не работает, пробуем альтернативы
        logger.info("🔄 Trying alternative connection methods...")
        
        # Пробуем с HTTP вместо HTTPS
        if original_url.startswith('https://'):
            logger.info("🔄 Trying HTTP instead of HTTPS...")
            self.remote_server_url = original_url.replace('https://', 'http://')
            if self.test_connection():
                logger.info(f"✅ HTTP connection successful: {self.remote_server_url}")
                return True
            
            # Возвращаем исходный URL
            self.remote_server_url = original_url
        
        # Пробуем с отключенной проверкой SSL
        if not self.verify_ssl:
            logger.info("🔄 Trying with SSL verification enabled...")
            self.verify_ssl = True
            self.session.verify = True
            if self.test_connection():
                logger.info("✅ Connection successful with SSL verification")
                return True
            
            # Возвращаем настройки
            self.verify_ssl = False
            self.session.verify = False
        
        logger.error("❌ All connection methods failed")
        return False
    
    def get_server_status(self) -> Dict:
        """Получение статуса удаленного сервера"""
        try:
            endpoints = ["/api/parser-status", "/api/status", "/status"]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(f"{self.remote_server_url}{endpoint}", timeout=15)
                    
                    if response.status_code == 200:
                        return response.json()
                        
                except requests.exceptions.RequestException:
                    continue
            
            logger.error("Failed to get server status from any endpoint")
            return {}
                
        except Exception as e:
            logger.error(f"Error getting server status: {e}")
            return {}
    
    def detect_category(self, products: List[Dict]) -> str:
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
    
    def upload_products(self, products: List[Dict], source: str = "local_parser") -> bool:
        """Отправка данных на удаленный сервер"""
        try:
            logger.info(f"🚀 Sending {len(products)} products to remote server...")
            
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
            upload_endpoints = ["/api/upload-products", "/upload-products", "/api/upload"]
            
            for endpoint in upload_endpoints:
                try:
                    url = f"{self.remote_server_url}{endpoint}"
                    logger.info(f"Trying upload to: {url}")
                    
                    response = self.session.post(
                        url,
                        json=payload,
                        timeout=180
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"✅ Successfully uploaded data: {result.get('message')}")
                        logger.info(f"   Imported: {result.get('imported_count', 0)} products")
                        return True
                    elif response.status_code in [404, 405]:
                        logger.info(f"   Endpoint {endpoint} not found, trying next...")
                        continue
                    else:
                        logger.error(f"   Endpoint {endpoint} returned status {response.status_code}")
                        logger.error(f"   Response: {response.text[:200]}")
                        
                except requests.exceptions.SSLError as ssl_err:
                    logger.error(f"   SSL error for {endpoint}: {ssl_err}")
                    # Пробуем с HTTP
                    if self.remote_server_url.startswith('https://'):
                        logger.info("   Trying HTTP due to SSL error...")
                        http_url = url.replace('https://', 'http://')
                        try:
                            response = self.session.post(
                                http_url,
                                json=payload,
                                timeout=180
                            )
                            if response.status_code == 200:
                                result = response.json()
                                logger.info(f"✅ Successfully uploaded via HTTP: {result.get('message')}")
                                logger.info(f"   Imported: {result.get('imported_count', 0)} products")
                                # Обновляем URL на HTTP для будущих запросов
                                self.remote_server_url = self.remote_server_url.replace('https://', 'http://')
                                return True
                        except Exception as http_err:
                            logger.error(f"   HTTP attempt also failed: {http_err}")
                    continue
                    
                except requests.exceptions.RequestException as req_err:
                    logger.error(f"   Request error for {endpoint}: {req_err}")
                    continue
            
            logger.error("❌ All upload endpoints failed")
            return False
                
        except Exception as e:
            logger.error(f"❌ Failed to upload data: {e}")
            return False
    
    def upload_file(self, file_path: str) -> bool:
        """Загружает файл на удаленный сервер"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                logger.error(f"❌ File not found: {file_path}")
                return False
            
            logger.info(f"📁 Reading file: {file_path.name}")
            
            # Читаем данные
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Извлекаем продукты из разных форматов
            if isinstance(data, dict):
                products = data.get('products', [])
                if not products and 'product_data' in data:
                    products = data['product_data']
            else:
                products = data if isinstance(data, list) else []
            
            if not products:
                logger.error(f"❌ No products found in {file_path.name}")
                return False
            
            category = self.detect_category(products)
            
            logger.info(f"📊 File info:")
            logger.info(f"   Products: {len(products):,}")
            logger.info(f"   Category: {category}")
            logger.info(f"   Size: {file_path.stat().st_size / 1024:.1f} KB")
            
            # Отправляем данные
            return self.upload_products(products, source=f"file:{file_path.name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to upload file: {e}")
            return False
    
    def upload_latest_parser_data(self) -> bool:
        """Загружает последний файл данных парсера на удаленный сервер"""
        try:
            # Ищем в папке старого парсера
            old_parser_file = Path("../old_dns_parser/product_data.json")
            if old_parser_file.exists():
                logger.info(f"📂 Found old parser data: {old_parser_file}")
                return self.upload_file(str(old_parser_file))
            
            # Ищем в локальных данных
            import glob
            data_files = glob.glob("../data/local_parser_data_*.json")
            if data_files:
                latest_file = max(data_files, key=os.path.getmtime)
                logger.info(f"📂 Found latest local data: {latest_file}")
                return self.upload_file(latest_file)
            
            logger.error("❌ No parser data files found")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to find parser data: {e}")
            return False


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Upload data to remote server')
    parser.add_argument('--server-url', type=str, default=DEFAULT_SERVER_URL,
                       help=f'Remote server URL (default: {DEFAULT_SERVER_URL})')
    parser.add_argument('--data-file', type=str,
                       help='Path to data file to upload')
    parser.add_argument('--latest', action='store_true',
                       help='Upload latest parser data file')
    parser.add_argument('--test-connection', action='store_true',
                       help='Test connection to remote server only')
    parser.add_argument('--status', action='store_true',
                       help='Show remote server status only')
    parser.add_argument('--verify-ssl', action='store_true',
                       help='Enable SSL certificate verification (default: disabled)')
    parser.add_argument('--diagnose', action='store_true',
                       help='Run comprehensive connection diagnostics')
    
    args = parser.parse_args()
    
    # Инициализация загрузчика
    uploader = RemoteServerUploader(remote_server_url=args.server_url, verify_ssl=args.verify_ssl)
    
    try:
        if args.diagnose:
            logger.info("🔍 Running connection diagnostics...")
            if uploader.test_connection_with_fallback():
                logger.info("✅ Diagnostics successful - connection is working")
                return 0
            else:
                logger.error("❌ Diagnostics failed - unable to connect")
                return 1
        
        if args.test_connection:
            if uploader.test_connection_with_fallback():
                logger.info("✅ Remote server connection test successful")
                return 0
            else:
                logger.error("❌ Remote server connection test failed")
                return 1
        
        if args.status:
            if not uploader.test_connection_with_fallback():
                logger.error("❌ Cannot connect to server for status check")
                return 1
                
            status = uploader.get_server_status()
            if status:
                logger.info(f"📊 Remote server status: {status}")
                return 0
            else:
                logger.error("❌ Failed to get remote server status")
                return 1
        
        # Проверяем соединение перед загрузкой
        if not uploader.test_connection_with_fallback():
            logger.error("❌ Cannot connect to remote server, aborting upload")
            return 1
        
        # Загружаем файл
        if args.data_file:
            if uploader.upload_file(args.data_file):
                logger.info("✅ File upload successful")
                return 0
            else:
                logger.error("❌ File upload failed")
                return 1
        
        # Загружаем последние данные
        if args.latest:
            if uploader.upload_latest_parser_data():
                logger.info("✅ Latest data upload successful")
                return 0
            else:
                logger.error("❌ Latest data upload failed")
                return 1
        
        # Если ничего не указано, загружаем последние данные
        logger.info("No specific action specified, uploading latest parser data...")
        if uploader.upload_latest_parser_data():
            logger.info("✅ Upload successful")
            return 0
        else:
            logger.error("❌ Upload failed")
            return 1
        
    except KeyboardInterrupt:
        logger.info("\n🚫 Upload cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 