#!/usr/bin/env python3
"""
Менеджер локальных данных парсера
Управляет файлами в папке data с правильным именованием и организацией
"""

import json
import os
import shutil
import logging
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('local_data_manager')

class LocalDataManager:
    def __init__(self, data_dir: Path = None, server_url: str = "http://127.0.0.1:5000"):
        """
        Менеджер локальных данных
        
        Args:
            data_dir: Путь к папке с данными
            server_url: URL сервера для отправки данных
        """
        self.server_url = server_url.rstrip('/')
        
        # Пути к директориям
        current_dir = Path(__file__).parent
        self.root_dir = current_dir.parent
        self.data_dir = data_dir or self.root_dir / "data"
        self.local_data_dir = self.root_dir / "local_data"
        
        # Создаем директории если не существуют
        self.data_dir.mkdir(exist_ok=True)
        self.local_data_dir.mkdir(exist_ok=True)
        
        logger.info(f"Data Manager initialized")
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Local data directory: {self.local_data_dir}")
        logger.info(f"Server URL: {self.server_url}")
    
    def detect_category_from_data(self, products: List[Dict]) -> str:
        """
        Определяет категорию товаров из данных
        
        Args:
            products: Список товаров
            
        Returns:
            Название категории
        """
        if not products:
            return "unknown"
        
        # Ищем категорию в первом товаре
        first_product = products[0]
        categories = first_product.get('categories', [])
        
        # Ищем самую специфичную категорию (последнюю в списке)
        for category in reversed(categories):
            name = category.get('name', '').strip()
            if name and name not in ['Комплектующие для ПК', 'Основные комплектующие для ПК']:
                return name
        
        # Если не нашли специфичную категорию, возвращаем последнюю
        if categories:
            return categories[-1].get('name', 'unknown')
        
        return "unknown"
    
    def get_category_short_name(self, category: str) -> str:
        """
        Получает короткое название категории для имени файла
        
        Args:
            category: Полное название категории
            
        Returns:
            Короткое название для файла
        """
        mapping = {
            "Видеокарты": "videokarty",
            "Процессоры": "processory", 
            "Материнские платы": "materinskie_platy",
            "Оперативная память": "operativnaya_pamyat",
            "Блоки питания": "bloki_pitaniya",
            "Кулеры для процессоров": "kulery",
            "Жесткие диски": "zhestkie_diski",
            "SSD накопители": "ssd_sata",
            "SSD M.2 накопители": "ssd_m2",
            "Корпуса": "korpusa"
        }
        
        # Ищем точное совпадение
        for full_name, short_name in mapping.items():
            if full_name.lower() in category.lower():
                return short_name
        
        # Если не нашли, создаем из названия
        return category.lower().replace(' ', '_').replace('.', '_')
    
    def organize_data_files(self):
        """
        Организует файлы в data директории с правильными именами
        """
        logger.info("🗂️ Organizing data files...")
        
        # Ищем все файлы с данными парсера
        data_files = list(self.data_dir.glob("local_parser_data_*.json"))
        
        if not data_files:
            logger.info("No parser data files found")
            return
        
        logger.info(f"Found {len(data_files)} data files to organize")
        
        organized_count = 0
        for file_path in sorted(data_files):
            try:
                # Читаем данные
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Определяем структуру данных
                products = data.get('products', []) if isinstance(data, dict) else data
                
                if not products:
                    logger.warning(f"Empty file: {file_path.name}")
                    continue
                
                # Определяем категорию
                category = self.detect_category_from_data(products)
                short_category = self.get_category_short_name(category)
                
                # Создаем новое имя файла
                timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
                new_filename = f"local_{short_category}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
                new_path = self.local_data_dir / new_filename
                
                # Копируем файл с новым именем
                shutil.copy2(file_path, new_path)
                
                # Создаем метаданные
                metadata = {
                    'category': category,
                    'short_category': short_category,
                    'product_count': len(products),
                    'original_file': file_path.name,
                    'organized_at': datetime.now().isoformat(),
                    'file_size': file_path.stat().st_size
                }
                
                # Сохраняем метаданные
                metadata_path = new_path.with_suffix('.meta.json')
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✅ Organized: {file_path.name} -> {new_filename}")
                logger.info(f"   Category: {category} ({len(products)} products)")
                
                organized_count += 1
                
            except Exception as e:
                logger.error(f"❌ Failed to organize {file_path.name}: {e}")
        
        logger.info(f"🎉 Organized {organized_count} files")
    
    def get_organized_files(self) -> List[Dict]:
        """
        Получает список организованных файлов с метаданными
        
        Returns:
            Список информации о файлах
        """
        files_info = []
        
        # Ищем все организованные файлы
        data_files = list(self.local_data_dir.glob("local_*.json"))
        data_files = [f for f in data_files if not f.name.endswith('.meta.json')]
        
        for file_path in sorted(data_files, key=lambda x: x.stat().st_mtime, reverse=True):
            metadata_path = file_path.with_suffix('.meta.json')
            
            try:
                # Читаем метаданные если есть
                metadata = {}
                if metadata_path.exists():
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                
                # Читаем основные данные
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                products = data.get('products', []) if isinstance(data, dict) else data
                
                file_info = {
                    'path': file_path,
                    'name': file_path.name,
                    'category': metadata.get('category', 'Unknown'),
                    'short_category': metadata.get('short_category', 'unknown'),
                    'product_count': len(products),
                    'file_size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime),
                    'metadata': metadata
                }
                
                files_info.append(file_info)
                
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
        
        return files_info
    
    def upload_file_to_server(self, file_path: Path, category: str) -> bool:
        """
        Отправляет файл на сервер
        
        Args:
            file_path: Путь к файлу
            category: Категория товаров
            
        Returns:
            True если успешно
        """
        try:
            # Читаем данные
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            products = data.get('products', []) if isinstance(data, dict) else data
            
            if not products:
                logger.warning(f"No products in {file_path.name}")
                return False
            
            # Подготавливаем payload
            payload = {
                'products': products,
                'source': 'local_data_manager',
                'category': category,
                'file_name': file_path.name,
                'timestamp': datetime.now().isoformat(),
                'parser_version': '3.0'
            }
            
            # Отправляем на сервер
            logger.info(f"Uploading {len(products)} products from {category}...")
            
            response = requests.post(
                f"{self.server_url}/api/upload-products",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Successfully uploaded: {result.get('message')}")
                return True
            else:
                logger.error(f"❌ Server returned status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to upload {file_path.name}: {e}")
            return False
    
    def upload_all_to_server(self):
        """
        Отправляет все организованные файлы на сервер
        """
        files_info = self.get_organized_files()
        
        if not files_info:
            logger.info("No organized files found to upload")
            return
        
        logger.info(f"📤 Uploading {len(files_info)} files to server...")
        
        success_count = 0
        total_products = 0
        
        for file_info in files_info:
            logger.info(f"\n📂 Uploading: {file_info['category']}")
            logger.info(f"   File: {file_info['name']}")
            logger.info(f"   Products: {file_info['product_count']}")
            
            if self.upload_file_to_server(file_info['path'], file_info['category']):
                success_count += 1
                total_products += file_info['product_count']
            else:
                logger.error(f"❌ Failed to upload {file_info['name']}")
        
        logger.info(f"\n🎉 Upload summary:")
        logger.info(f"   Success: {success_count}/{len(files_info)} files")
        logger.info(f"   Total products uploaded: {total_products:,}")
    
    def show_statistics(self):
        """
        Показывает статистику по локальным данным
        """
        logger.info("📊 Local Data Statistics")
        logger.info("=" * 50)
        
        # Статистика по data директории
        data_files = list(self.data_dir.glob("local_parser_data_*.json"))
        logger.info(f"📁 Raw data files: {len(data_files)}")
        
        # Статистика по организованным файлам
        organized_files = self.get_organized_files()
        logger.info(f"🗂️ Organized files: {len(organized_files)}")
        
        if organized_files:
            # Группируем по категориям
            categories = {}
            for file_info in organized_files:
                category = file_info['category']
                if category not in categories:
                    categories[category] = {'files': 0, 'products': 0}
                categories[category]['files'] += 1
                categories[category]['products'] += file_info['product_count']
            
            logger.info("\n📂 By categories:")
            for category, stats in categories.items():
                logger.info(f"   {category}: {stats['files']} files, {stats['products']} products")
            
            total_products = sum(f['product_count'] for f in organized_files)
            logger.info(f"\n🎯 Total products: {total_products:,}")

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Local data manager')
    parser.add_argument('--server-url', type=str, default='http://127.0.0.1:5000', help='Server URL')
    parser.add_argument('--organize', action='store_true', help='Organize data files')
    parser.add_argument('--upload', action='store_true', help='Upload organized files to server')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--all', action='store_true', help='Organize and upload')
    
    args = parser.parse_args()
    
    # Инициализация менеджера
    manager = LocalDataManager(server_url=args.server_url)
    
    try:
        if args.stats:
            manager.show_statistics()
        elif args.organize:
            manager.organize_data_files()
        elif args.upload:
            manager.upload_all_to_server()
        elif args.all:
            manager.organize_data_files()
            manager.upload_all_to_server()
        else:
            # По умолчанию показываем статистику
            manager.show_statistics()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    exit(main()) 