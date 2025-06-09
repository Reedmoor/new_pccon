#!/usr/bin/env python3
"""
Скрипт для отправки данных на Docker парсер-сервер
Использует API endpoints парсер-сервера
"""

import os
import sys
import json
import logging
import requests
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('upload_to_parser_server')

class ParserServerUploader:
    def __init__(self, parser_server_url="http://127.0.0.1:5000"):
        """
        Загрузчик данных на парсер-сервер
        
        Args:
            parser_server_url: URL парсер-сервера Docker
        """
        self.parser_server_url = parser_server_url.rstrip('/')
        self.session = requests.Session()
        
        logger.info(f"Parser Server Uploader initialized")
        logger.info(f"Target parser server: {self.parser_server_url}")
    
    def test_parser_connection(self) -> bool:
        """Тестирование соединения с парсер-сервером"""
        try:
            logger.info(f"Testing connection to parser server: {self.parser_server_url}")
            
            # Проверяем health endpoint парсер-сервера
            response = self.session.get(f"{self.parser_server_url}/health", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Parser server connection successful: {result.get('service', 'unknown')}")
                return True
            else:
                logger.error(f"❌ Parser server returned status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to connect to parser server: {e}")
            return False
    
    def get_parser_status(self) -> Dict:
        """Получение статуса парсеров"""
        try:
            response = self.session.get(f"{self.parser_server_url}/status", timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get parser status: {response.status_code}")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting parser status: {e}")
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
    
    def send_dns_data(self, products: List[Dict], category: str) -> bool:
        """Отправка данных через DNS API парсер-сервера"""
        try:
            logger.info(f"🚀 Sending {len(products)} products from {category} to DNS API...")
            
            # Подготавливаем payload для DNS API
            payload = {
                'category': category,
                'products': products,
                'source': 'local_old_dns_parser',
                'timestamp': datetime.now().isoformat(),
                'product_count': len(products)
            }
            
            # Отправляем через DNS API парсер-сервера
            response = self.session.post(
                f"{self.parser_server_url}/parse/dns",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Successfully sent data via DNS API: {result.get('message')}")
                return True
            else:
                logger.error(f"❌ DNS API returned status {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to send data via DNS API: {e}")
            return False
    
    def upload_file(self, file_path: str) -> bool:
        """Загружает файл на парсер-сервер"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                logger.error(f"❌ File not found: {file_path}")
                return False
            
            logger.info(f"📁 Reading file: {file_path.name}")
            
            # Читаем данные
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            products = data.get('products', []) if isinstance(data, dict) else data
            
            if not products:
                logger.error(f"❌ No products found in {file_path.name}")
                return False
            
            category = self.detect_category(products)
            
            logger.info(f"📊 File info:")
            logger.info(f"   Products: {len(products):,}")
            logger.info(f"   Category: {category}")
            logger.info(f"   Size: {file_path.stat().st_size / 1024:.1f} KB")
            
            # Отправляем данные через DNS API
            return self.send_dns_data(products, category)
                
        except Exception as e:
            logger.error(f"❌ Failed to upload file: {e}")
            return False


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Upload data to Docker parser server')
    parser.add_argument('--parser-url', type=str, default='http://127.0.0.1:5000',
                       help='Parser server URL (default: http://127.0.0.1:5000)')
    parser.add_argument('--data-file', type=str, required=True,
                       help='Path to data file to upload')
    parser.add_argument('--test-connection', action='store_true',
                       help='Test connection to parser server only')
    parser.add_argument('--status', action='store_true',
                       help='Show parser status only')
    
    args = parser.parse_args()
    
    # Инициализация загрузчика
    uploader = ParserServerUploader(parser_server_url=args.parser_url)
    
    try:
        if args.test_connection:
            if uploader.test_parser_connection():
                logger.info("✅ Parser server connection test successful")
                return 0
            else:
                logger.error("❌ Parser server connection test failed")
                return 1
        
        if args.status:
            status = uploader.get_parser_status()
            if status:
                logger.info(f"📊 Parser status: {status}")
                return 0
            else:
                logger.error("❌ Failed to get parser status")
                return 1
        
        # Проверяем соединение перед загрузкой
        if not uploader.test_parser_connection():
            logger.error("❌ Cannot connect to parser server, aborting upload")
            return 1
        
        # Показываем статус парсеров
        status = uploader.get_parser_status()
        if status:
            logger.info(f"📊 Available parsers: {status.get('parsers', {})}")
        
        # Загружаем файл
        if uploader.upload_file(args.data_file):
            logger.info("✅ File upload completed successfully!")
            return 0
        else:
            logger.error("❌ File upload failed")
            return 1
    
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    exit(main()) 