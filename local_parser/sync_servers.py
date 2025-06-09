#!/usr/bin/env python3
"""
Скрипт для синхронизации данных между серверами
ИСТОЧНИК: 127.0.0.1:5001 -> НАЗНАЧЕНИЕ: 127.0.0.1:5000 (Docker)
"""

import requests
import json
import logging
import argparse
import time
from datetime import datetime
from typing import Dict, List, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sync_servers')

class ServerSynchronizer:
    def __init__(self, source_url="http://127.0.0.1:5001", target_url="http://127.0.0.1:5000"):
        """
        Синхронизатор данных между серверами
        
        Args:
            source_url: URL исходного сервера (5001)
            target_url: URL целевого сервера (Docker 5000)
        """
        self.source_url = source_url.rstrip('/')
        self.target_url = target_url.rstrip('/')
        self.session = requests.Session()
        
        logger.info(f"Server Synchronizer initialized")
        logger.info(f"Source server (FROM): {self.source_url}")
        logger.info(f"Target server (TO): {self.target_url}")
    
    def test_connections(self) -> Dict[str, bool]:
        """Тестирование соединения с обоими серверами"""
        results = {}
        
        # Тестируем исходный сервер (5001)
        logger.info(f"🔍 Testing source server: {self.source_url}")
        try:
            # Пробуем разные эндпоинты для проверки доступности
            test_endpoints = ["/health", "/", "/api/status", "/status"]
            source_available = False
            
            for endpoint in test_endpoints:
                try:
                    response = self.session.get(f"{self.source_url}{endpoint}", timeout=5)
                    if response.status_code in [200, 404, 405]:  # Любой ответ означает что сервер работает
                        logger.info(f"✅ Source server (5001) connection successful via {endpoint}")
                        source_available = True
                        break
                except:
                    continue
            
            results['source'] = source_available
            if not source_available:
                logger.error("❌ Source server (5001) not responding")
        except Exception as e:
            logger.error(f"❌ Failed to connect to source server: {e}")
            results['source'] = False
        
        # Тестируем целевой сервер (5000 - Docker)
        logger.info(f"🔍 Testing target server: {self.target_url}")
        try:
            response = self.session.get(f"{self.target_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ Target server (Docker 5000) connection successful")
                results['target'] = True
            else:
                logger.error(f"❌ Target server returned status {response.status_code}")
                results['target'] = False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to connect to target server: {e}")
            results['target'] = False
        
        return results
    
    def get_data_from_source(self) -> Optional[List[Dict]]:
        """Получение данных с исходного сервера (5001)"""
        logger.info("📥 Fetching data from source server (5001)...")
        
        # Пробуем разные эндпоинты для получения данных
        endpoints_to_try = [
            "/api/export-products",
            "/api/products",
            "/api/parser-data", 
            "/api/export-data",
            "/api/all-products",
            "/products",
            "/data"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                logger.info(f"Trying endpoint: {endpoint}")
                response = self.session.get(f"{self.source_url}{endpoint}", timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Определяем структуру данных
                    if isinstance(data, list):
                        products = data
                    elif isinstance(data, dict):
                        if 'products' in data:
                            products = data['products']
                        elif 'data' in data:
                            products = data['data']
                        elif 'items' in data:
                            products = data['items']
                        else:
                            # Если это один объект, оборачиваем в список
                            products = [data]
                    else:
                        logger.warning(f"Unexpected data format from {endpoint}")
                        continue
                    
                    if products:
                        logger.info(f"✅ Found {len(products)} products from {endpoint}")
                        return products
                    else:
                        logger.warning(f"No products in response from {endpoint}")
                
                elif response.status_code == 404:
                    logger.debug(f"Endpoint {endpoint} not found (404)")
                else:
                    logger.warning(f"Endpoint {endpoint} returned status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error accessing {endpoint}: {e}")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from {endpoint}: {e}")
        
        logger.error("❌ Could not retrieve data from any endpoint on source server")
        return None
    
    def send_data_to_target(self, products: List[Dict]) -> bool:
        """Отправка данных на целевой сервер (Docker 5000)"""
        if not products:
            logger.warning("No products to send")
            return False
        
        logger.info(f"📤 Sending {len(products)} products to target server (Docker 5000)...")
        
        try:
            # Подготавливаем payload для Docker API с уникальным именем
            current_time = datetime.now()
            payload = {
                'products': products,
                'source': 'server_sync_5001_to_5000',
                'category': self._detect_category(products),
                'file_name': f'sync_data_{current_time.strftime("%Y%m%d_%H%M%S")}.json',
                'timestamp': current_time.isoformat(),
                'parser_version': '3.0',
                'upload_type': 'server_sync',
                'sync_id': f'sync_{current_time.timestamp()}',  # Уникальный ID синхронизации
                'replace_existing': True  # Флаг для замены существующих данных
            }
            
            # Отправляем на Docker сервер
            response = self.session.post(
                f"{self.target_url}/api/upload-products",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Successfully synced data: {result.get('message')}")
                return True
            else:
                logger.error(f"❌ Target server returned status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to send data to target server: {e}")
            return False
    
    def _detect_category(self, products: List[Dict]) -> str:
        """Определяет основную категорию товаров"""
        if not products:
            return "unknown"
        
        # Анализируем категории в первых нескольких товарах
        categories = {}
        for product in products[:10]:  # Берем первые 10 товаров
            product_categories = product.get('categories', [])
            for category in product_categories:
                name = category.get('name', '').strip()
                if name and name not in ['Комплектующие для ПК', 'Основные комплектующие для ПК']:
                    categories[name] = categories.get(name, 0) + 1
        
        # Возвращаем самую частую категорию
        if categories:
            most_common = max(categories.items(), key=lambda x: x[1])
            return most_common[0]
        
        return "mixed_categories"
    
    def sync_data(self) -> Dict:
        """Основная функция синхронизации данных"""
        logger.info("🔄 Starting server synchronization...")
        logger.info(f"   FROM: {self.source_url} (port 5001)")
        logger.info(f"   TO: {self.target_url} (port 5000 Docker)")
        
        # Проверяем соединения
        connections = self.test_connections()
        
        if not connections.get('source', False):
            return {
                'success': False,
                'error': 'Cannot connect to source server (5001)',
                'synced_products': 0
            }
        
        if not connections.get('target', False):
            return {
                'success': False,
                'error': 'Cannot connect to target server (Docker 5000)',
                'synced_products': 0
            }
        
        # Получаем данные с исходного сервера
        products = self.get_data_from_source()
        
        if not products:
            return {
                'success': False,
                'error': 'No data found on source server',
                'synced_products': 0
            }
        
        # Отправляем данные на целевой сервер
        if self.send_data_to_target(products):
            return {
                'success': True,
                'synced_products': len(products),
                'message': f'Successfully synced {len(products)} products'
            }
        else:
            return {
                'success': False,
                'error': 'Failed to send data to target server',
                'synced_products': 0
            }
    
    def get_source_server_info(self) -> Dict:
        """Получение информации о исходном сервере"""
        logger.info("📊 Getting source server information...")
        
        info_endpoints = [
            "/api/status",
            "/api/info", 
            "/api/parser-status",
            "/status",
            "/info"
        ]
        
        for endpoint in info_endpoints:
            try:
                response = self.session.get(f"{self.source_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Server info from {endpoint}:")
                    logger.info(f"   {json.dumps(data, indent=2, ensure_ascii=False)}")
                    return data
            except:
                continue
        
        logger.warning("Could not get server information")
        return {}


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Sync data from server 5001 to Docker server 5000')
    parser.add_argument('--source-url', type=str, default='http://127.0.0.1:5001', 
                       help='Source server URL (default: http://127.0.0.1:5001)')
    parser.add_argument('--target-url', type=str, default='http://127.0.0.1:5000', 
                       help='Target Docker server URL (default: http://127.0.0.1:5000)')
    parser.add_argument('--test-only', action='store_true', 
                       help='Only test connections to both servers')
    parser.add_argument('--info', action='store_true', 
                       help='Get information about source server')
    parser.add_argument('--sync', action='store_true', 
                       help='Perform synchronization')
    
    args = parser.parse_args()
    
    # Инициализация синхронизатора
    synchronizer = ServerSynchronizer(
        source_url=args.source_url, 
        target_url=args.target_url
    )
    
    try:
        if args.test_only:
            logger.info("🔍 Testing connections to both servers...")
            connections = synchronizer.test_connections()
            
            if connections.get('source') and connections.get('target'):
                logger.info("✅ Both servers are accessible")
                return 0
            else:
                logger.error("❌ One or both servers are not accessible")
                return 1
        
        elif args.info:
            synchronizer.get_source_server_info()
            return 0
        
        elif args.sync:
            logger.info("🚀 Starting synchronization...")
            result = synchronizer.sync_data()
            
            if result['success']:
                logger.info(f"✅ Synchronization completed successfully!")
                logger.info(f"   Synced products: {result['synced_products']}")
                return 0
            else:
                logger.error(f"❌ Synchronization failed: {result['error']}")
                return 1
        
        else:
            # По умолчанию выполняем синхронизацию
            logger.info("🚀 Starting default synchronization...")
            result = synchronizer.sync_data()
            
            if result['success']:
                logger.info(f"✅ Synchronization completed!")
                logger.info(f"   Synced {result['synced_products']} products from 5001 to 5000")
                return 0
            else:
                logger.error(f"❌ Synchronization failed: {result['error']}")
                return 1
    
    except KeyboardInterrupt:
        logger.info("Synchronization interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    exit(main()) 