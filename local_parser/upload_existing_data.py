#!/usr/bin/env python3
"""
Скрипт для загрузки существующих данных из папки DNS_parsing на Docker сервер
"""

import json
import requests
import os
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('upload_data')

class DataUploader:
    def __init__(self, server_url="http://127.0.0.1:5000"):
        """
        Загрузчик данных на сервер
        
        Args:
            server_url: URL сервера для отправки данных
        """
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        
        # Путь к готовым данным
        current_dir = Path(__file__).parent
        self.data_dir = current_dir.parent / "app" / "utils" / "DNS_parsing" / "categories"
        
        logger.info(f"Data Uploader initialized")
        logger.info(f"Server URL: {self.server_url}")
        logger.info(f"Data directory: {self.data_dir}")
        
    def test_server_connection(self):
        """Тестирование соединения с сервером"""
        try:
            logger.info(f"Testing connection to server: {self.server_url}")
            response = self.session.get(f"{self.server_url}/api/test-connection", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Server connection successful: {data.get('message')}")
                return True
            else:
                logger.error(f"❌ Server returned status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to connect to server: {e}")
            return False
    
    def get_available_data_files(self):
        """Получение списка доступных файлов с данными"""
        if not self.data_dir.exists():
            logger.error(f"Data directory not found: {self.data_dir}")
            return []
        
        json_files = list(self.data_dir.glob("product_data_*.json"))
        logger.info(f"Found {len(json_files)} data files")
        
        files_info = []
        for file_path in json_files:
            try:
                stat = file_path.stat()
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                file_info = {
                    'path': file_path,
                    'name': file_path.name,
                    'category': file_path.stem.replace('product_data_', ''),
                    'size': stat.st_size,
                    'product_count': len(data),
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                }
                files_info.append(file_info)
                
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
        
        # Сортируем по количеству товаров
        files_info.sort(key=lambda x: x['product_count'], reverse=True)
        return files_info
    
    def upload_data_file(self, file_path, category_name=None):
        """Отправка данных из файла на сервер"""
        try:
            logger.info(f"Loading data from: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            if not products:
                logger.warning(f"No products in {file_path}")
                return False
            
            logger.info(f"Uploading {len(products)} products from {category_name or file_path.name}...")
            
            payload = {
                'products': products,
                'source': 'existing_dns_data',
                'category': category_name or 'unknown',
                'file_name': file_path.name,
                'timestamp': datetime.now().isoformat(),
                'parser_version': '3.0'
            }
            
            response = self.session.post(
                f"{self.server_url}/api/upload-products",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=60  # Увеличиваем таймаут для больших файлов
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Successfully uploaded {len(products)} products: {result.get('message')}")
                return True
            else:
                logger.error(f"❌ Server returned status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to upload data: {e}")
            return False
    
    def upload_all_data(self):
        """Загрузка всех доступных данных"""
        files_info = self.get_available_data_files()
        
        if not files_info:
            logger.error("No data files found")
            return False
        
        logger.info(f"Found {len(files_info)} data files to upload")
        
        success_count = 0
        total_products = 0
        
        for file_info in files_info:
            logger.info(f"\n📂 Processing: {file_info['category']}")
            logger.info(f"   Products: {file_info['product_count']:,}")
            logger.info(f"   Size: {file_info['size'] / 1024:.1f} KB")
            
            if self.upload_data_file(file_info['path'], file_info['category']):
                success_count += 1
                total_products += file_info['product_count']
            else:
                logger.error(f"❌ Failed to upload {file_info['category']}")
        
        logger.info(f"\n🎉 Upload summary:")
        logger.info(f"   Success: {success_count}/{len(files_info)} files")
        logger.info(f"   Total products uploaded: {total_products:,}")
        
        return success_count > 0
    
    def upload_category(self, category_name):
        """Загрузка конкретной категории"""
        files_info = self.get_available_data_files()
        
        # Ищем файл с указанной категорией
        matching_file = None
        for file_info in files_info:
            if category_name.lower() in file_info['category'].lower():
                matching_file = file_info
                break
        
        if not matching_file:
            logger.error(f"Category '{category_name}' not found")
            logger.info("Available categories:")
            for file_info in files_info:
                logger.info(f"  - {file_info['category']} ({file_info['product_count']:,} products)")
            return False
        
        logger.info(f"📂 Uploading category: {matching_file['category']}")
        logger.info(f"   Products: {matching_file['product_count']:,}")
        
        return self.upload_data_file(matching_file['path'], matching_file['category'])

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Upload existing DNS data to server')
    parser.add_argument('--server-url', type=str, default='http://127.0.0.1:5000', help='Server URL')
    parser.add_argument('--category', type=str, help='Upload specific category only')
    parser.add_argument('--list-categories', action='store_true', help='List available categories')
    parser.add_argument('--test-only', action='store_true', help='Only test server connection')
    
    args = parser.parse_args()
    
    # Инициализация загрузчика
    uploader = DataUploader(server_url=args.server_url)
    
    try:
        # Тестируем соединение с сервером
        if not uploader.test_server_connection():
            logger.error("Cannot connect to server. Please check server is running.")
            return 1
        
        if args.test_only:
            logger.info("✅ Connection test completed successfully")
            return 0
        
        if args.list_categories:
            files_info = uploader.get_available_data_files()
            logger.info("\n📋 Available categories:")
            for file_info in files_info:
                logger.info(f"  📂 {file_info['category']}")
                logger.info(f"     Products: {file_info['product_count']:,}")
                logger.info(f"     Size: {file_info['size'] / 1024:.1f} KB")
                logger.info(f"     Modified: {file_info['modified'].strftime('%Y-%m-%d %H:%M')}")
                logger.info("")
            return 0
        
        if args.category:
            # Загружаем конкретную категорию
            if uploader.upload_category(args.category):
                logger.info("✅ Category uploaded successfully!")
                return 0
            else:
                logger.error("❌ Failed to upload category")
                return 1
        else:
            # Загружаем все данные
            logger.info("🚀 Starting upload of all available data...")
            if uploader.upload_all_data():
                logger.info("✅ All data uploaded successfully!")
                return 0
            else:
                logger.error("❌ Failed to upload data")
                return 1
    
    except KeyboardInterrupt:
        logger.info("Upload interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    exit(main()) 