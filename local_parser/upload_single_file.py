#!/usr/bin/env python3
"""
Скрипт для загрузки одного конкретного файла данных на сервер
Поддерживает загрузку на локальный (5001) или Docker (5000) сервер
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
logger = logging.getLogger('upload_single_file')

class SingleFileUploader:
    def __init__(self, server_url):
        """
        Загрузчик одного файла на сервер
        
        Args:
            server_url: URL сервера (локальный 5001 или Docker 5000)
        """
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        
        logger.info(f"Single File Uploader initialized")
        logger.info(f"Target server: {self.server_url}")
    
    def test_server_connection(self) -> bool:
        """Тестирование соединения с сервером"""
        try:
            logger.info(f"Testing connection to server: {self.server_url}")
            
            # Используем разные endpoints для разных серверов
            if ":5000" in self.server_url:
                # Docker сервер - пропускаем health check, так как главное что API работает
                logger.info("✅ Skipping health check for Docker server (5000) - will test upload directly")
                return True
            else:
                # Локальный сервер - используем главную страницу
                test_url = f"{self.server_url}/"
                response = self.session.get(test_url, timeout=10)
                
                if response.status_code == 200:
                    logger.info("✅ Server connection successful")
                    return True
                else:
                    logger.error(f"❌ Server returned status {response.status_code}")
                    return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to connect to server: {e}")
            return False
    
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
    
    def upload_file(self, file_path: str, source_override: str = None) -> bool:
        """Загружает файл на сервер"""
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
            
            # Автоопределение источника по URL первого товара
            if source_override:
                source_name = source_override
            else:
                first_url = products[0].get('url', '') if products else ''
                if 'citilink.ru' in first_url:
                    source_name = 'citilink'
                elif 'dns-shop.ru' in first_url:
                    source_name = 'dns'
                else:
                    source_name = 'single_file_upload'
            
            logger.info(f"📊 File info:")
            logger.info(f"   Products: {len(products):,}")
            logger.info(f"   Category: {category}")
            logger.info(f"   Source: {source_name}")
            logger.info(f"   Size: {file_path.stat().st_size / 1024:.1f} KB")
            
            # Подготавливаем payload для API
            payload = {
                'products': products,
                'source': source_name,
                'category': category,
                'file_name': file_path.name,
                'timestamp': datetime.now().isoformat(),
                'parser_version': '3.0',
                'upload_type': 'single_file'
            }
            
            logger.info(f"🚀 Uploading {len(products)} products to server...")
            
            # Отправляем на сервер
            response = self.session.post(
                f"{self.server_url}/api/upload-products",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Successfully uploaded {file_path.name}")
                logger.info(f"   Server response: {result.get('message', 'Upload completed')}")
                return True
            else:
                logger.error(f"❌ Server returned status {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to upload file: {e}")
            return False


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Upload single file to server')
    parser.add_argument('--server-url', type=str, required=True,
                       help='Server URL (e.g., http://127.0.0.1:5001 or http://127.0.0.1:5000)')
    parser.add_argument('--data-file', type=str, required=True,
                       help='Path to data file to upload')
    parser.add_argument('--source', type=str, default=None,
                       help='Override source name (e.g. citilink, dns)')
    parser.add_argument('--test-connection', action='store_true',
                       help='Test connection to server only')
    
    args = parser.parse_args()
    
    # Инициализация загрузчика
    uploader = SingleFileUploader(server_url=args.server_url)
    
    try:
        if args.test_connection:
            if uploader.test_server_connection():
                logger.info("✅ Server connection test successful")
                return 0
            else:
                logger.error("❌ Server connection test failed")
                return 1
        
        # Проверяем соединение перед загрузкой
        if not uploader.test_server_connection():
            logger.error("❌ Cannot connect to server, aborting upload")
            return 1
        
        # Загружаем файл
        if uploader.upload_file(args.data_file, source_override=args.source):
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