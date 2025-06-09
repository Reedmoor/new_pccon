#!/usr/bin/env python3
"""
Скрипт для отправки локально спарсенных данных на Docker сервер
Изменяет направление потока данных: локальный парсинг -> Docker сервер
"""

import os
import sys
import json
import logging
import requests
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('upload_to_docker')

class LocalToDockerUploader:
    def __init__(self, docker_server_url="http://127.0.0.1:5000"):
        """
        Загрузчик локальных данных на Docker сервер
        
        Args:
            docker_server_url: URL Docker сервера
        """
        self.docker_server_url = docker_server_url.rstrip('/')
        self.session = requests.Session()
        
        # Пути к директориям
        current_dir = Path(__file__).parent
        self.root_dir = current_dir.parent
        self.data_dir = self.root_dir / "data"
        self.local_data_dir = self.root_dir / "local_data"
        
        logger.info(f"Local to Docker Uploader initialized")
        logger.info(f"Docker server: {self.docker_server_url}")
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Local data directory: {self.local_data_dir}")
    
    def test_docker_connection(self) -> bool:
        """Тестирование соединения с Docker сервером"""
        try:
            logger.info(f"Testing connection to Docker server: {self.docker_server_url}")
            response = self.session.get(f"{self.docker_server_url}/health", timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Docker server connection successful")
                return True
            else:
                logger.error(f"❌ Docker server returned status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to connect to Docker server: {e}")
            return False
    
    def get_local_data_files(self) -> List[Dict]:
        """Получает список локальных файлов данных для отправки"""
        data_files = []
        
        # Сканируем папку data
        for pattern in ["local_parser_data_*.json", "product_data.json"]:
            files = list(self.data_dir.glob(pattern))
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    products = data.get('products', []) if isinstance(data, dict) else data
                    
                    if products:
                        data_files.append({
                            'path': file_path,
                            'name': file_path.name,
                            'product_count': len(products),
                            'size': file_path.stat().st_size,
                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime),
                            'category': self._detect_category(products)
                        })
                except Exception as e:
                    logger.warning(f"Could not process {file_path.name}: {e}")
        
        # Сканируем папку local_data
        local_files = list(self.local_data_dir.glob("local_*.json"))
        local_files = [f for f in local_files if not f.name.endswith('.meta.json')]
        
        for file_path in local_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                products = data.get('products', []) if isinstance(data, dict) else data
                
                if products:
                    # Проверяем метаданные
                    metadata_path = file_path.with_suffix('.meta.json')
                    category = "unknown"
                    if metadata_path.exists():
                        try:
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                category = metadata.get('category', category)
                        except:
                            pass
                    
                    data_files.append({
                        'path': file_path,
                        'name': file_path.name,
                        'product_count': len(products),
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime),
                        'category': category
                    })
            except Exception as e:
                logger.warning(f"Could not process {file_path.name}: {e}")
        
        # Сортируем по дате модификации (новые первыми)
        data_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return data_files
    
    def _detect_category(self, products: List[Dict]) -> str:
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
    
    def upload_file_to_docker(self, file_info: Dict) -> bool:
        """Отправляет файл на Docker сервер"""
        try:
            file_path = file_info['path']
            category = file_info['category']
            
            # Читаем данные
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            products = data.get('products', []) if isinstance(data, dict) else data
            
            if not products:
                logger.warning(f"No products in {file_path.name}")
                return False
            
            # Подготавливаем payload для Docker API
            payload = {
                'products': products,
                'source': 'local_parser_to_docker',
                'category': category,
                'file_name': file_path.name,
                'timestamp': datetime.now().isoformat(),
                'parser_version': '3.0',
                'upload_type': 'local_to_docker'
            }
            
            logger.info(f"Uploading {len(products)} products from {category} to Docker server...")
            
            # Отправляем на Docker сервер
            response = self.session.post(
                f"{self.docker_server_url}/api/upload-products",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=120  # Увеличенный таймаут для больших файлов
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Successfully uploaded {file_path.name}: {result.get('message')}")
                return True
            else:
                logger.error(f"❌ Docker server returned status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to upload {file_info['name']}: {e}")
            return False
    
    def upload_all_to_docker(self, cleanup_after_upload=False) -> Dict:
        """Отправляет все локальные данные на Docker сервер"""
        # Проверяем соединение с Docker сервером
        if not self.test_docker_connection():
            return {
                'success': False,
                'error': 'Cannot connect to Docker server',
                'uploaded_files': 0,
                'total_products': 0
            }
        
        # Получаем список файлов
        data_files = self.get_local_data_files()
        
        if not data_files:
            logger.info("No local data files found to upload")
            return {
                'success': True,
                'message': 'No files to upload',
                'uploaded_files': 0,
                'total_products': 0
            }
        
        logger.info(f"Found {len(data_files)} local data files to upload to Docker server")
        
        # Показываем что будем загружать
        logger.info("\n📋 Files to upload:")
        total_products_to_upload = 0
        for i, file_info in enumerate(data_files, 1):
            logger.info(f"  {i:2d}. {file_info['name']}")
            logger.info(f"      Category: {file_info['category']}")
            logger.info(f"      Products: {file_info['product_count']:,}")
            logger.info(f"      Size: {file_info['size'] / 1024:.1f} KB")
            logger.info(f"      Modified: {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
            total_products_to_upload += file_info['product_count']
        
        logger.info(f"\n🎯 Total products to upload: {total_products_to_upload:,}")
        
        # Загружаем файлы
        uploaded_files = 0
        uploaded_products = 0
        failed_files = []
        successful_files = []
        
        for file_info in data_files:
            logger.info(f"\n📤 Uploading: {file_info['name']}")
            
            if self.upload_file_to_docker(file_info):
                uploaded_files += 1
                uploaded_products += file_info['product_count']
                successful_files.append(file_info)
                
                # Очищаем локальный файл после успешной загрузки (если включена очистка)
                if cleanup_after_upload:
                    try:
                        self._cleanup_uploaded_file(file_info['path'])
                        logger.info(f"🗑️ Cleaned up local file: {file_info['name']}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup {file_info['name']}: {e}")
            else:
                failed_files.append(file_info)
        
        # Итоговая статистика
        logger.info(f"\n🎉 Upload to Docker server completed!")
        logger.info(f"   Success: {uploaded_files}/{len(data_files)} files")
        logger.info(f"   Products uploaded: {uploaded_products:,}")
        
        if failed_files:
            logger.warning(f"   Failed files: {len(failed_files)}")
            for file_info in failed_files:
                logger.warning(f"     - {file_info['name']}")
        
        return {
            'success': uploaded_files > 0,
            'uploaded_files': uploaded_files,
            'total_files': len(data_files),
            'total_products': uploaded_products,
            'failed_files': len(failed_files),
            'successful_files': [f['name'] for f in successful_files],
            'failed_file_names': [f['name'] for f in failed_files]
        }
    
    def _cleanup_uploaded_file(self, file_path: Path):
        """Очищает загруженный файл и связанные метаданные"""
        # Удаляем основной файл
        if file_path.exists():
            file_path.unlink()
        
        # Удаляем метаданные если есть
        metadata_path = file_path.with_suffix('.meta.json')
        if metadata_path.exists():
            metadata_path.unlink()
    
    def show_local_data_status(self):
        """Показывает статус локальных данных"""
        data_files = self.get_local_data_files()
        
        if not data_files:
            logger.info("📁 No local data files found")
            return
        
        logger.info(f"📁 Found {len(data_files)} local data files:")
        
        total_products = 0
        total_size = 0
        categories = set()
        
        for i, file_info in enumerate(data_files, 1):
            logger.info(f"\n  {i:2d}. {file_info['name']}")
            logger.info(f"      Category: {file_info['category']}")
            logger.info(f"      Products: {file_info['product_count']:,}")
            logger.info(f"      Size: {file_info['size'] / 1024:.1f} KB")
            logger.info(f"      Modified: {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            total_products += file_info['product_count']
            total_size += file_info['size']
            categories.add(file_info['category'])
        
        logger.info(f"\n📊 Summary:")
        logger.info(f"   Total files: {len(data_files)}")
        logger.info(f"   Total products: {total_products:,}")
        logger.info(f"   Total size: {total_size / 1024 / 1024:.1f} MB")
        logger.info(f"   Categories: {len(categories)}")
        logger.info(f"   Category list: {', '.join(sorted(categories))}")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Upload local parsed data to Docker server')
    parser.add_argument('--docker-url', type=str, default='http://127.0.0.1:5000', 
                       help='Docker server URL (default: http://127.0.0.1:5000)')
    parser.add_argument('--status', action='store_true', 
                       help='Show local data status only')
    parser.add_argument('--upload', action='store_true', 
                       help='Upload all local data to Docker server')
    parser.add_argument('--cleanup', action='store_true', 
                       help='Clean up local files after successful upload')
    parser.add_argument('--test-connection', action='store_true', 
                       help='Test connection to Docker server only')
    
    args = parser.parse_args()
    
    # Инициализация загрузчика
    uploader = LocalToDockerUploader(docker_server_url=args.docker_url)
    
    try:
        if args.test_connection:
            if uploader.test_docker_connection():
                logger.info("✅ Docker server connection test successful")
                return 0
            else:
                logger.error("❌ Docker server connection test failed")
                return 1
        
        elif args.status:
            uploader.show_local_data_status()
            return 0
        
        elif args.upload:
            logger.info("🚀 Starting upload of local data to Docker server...")
            result = uploader.upload_all_to_docker(cleanup_after_upload=args.cleanup)
            
            if result['success']:
                logger.info("✅ Upload completed successfully!")
                return 0
            else:
                logger.error("❌ Upload failed")
                return 1
        
        else:
            # По умолчанию показываем статус
            uploader.show_local_data_status()
            logger.info("\nUse --upload to upload data to Docker server")
            logger.info("Use --test-connection to test Docker server connection")
            return 0
    
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    exit(main()) 