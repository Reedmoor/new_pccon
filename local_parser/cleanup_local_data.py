#!/usr/bin/env python3
"""
Скрипт для очистки дублирующих локальных JSON файлов
Анализирует папку local_data и удаляет старые дубли
"""

import os
import json
import glob
import logging
from datetime import datetime
from typing import Dict, List, Set
from pathlib import Path
import re

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cleanup_local_data')

class LocalDataCleaner:
    def __init__(self, data_dir="../local_data"):
        """
        Очистка дублирующих локальных файлов
        
        Args:
            data_dir: Путь к папке с локальными данными
        """
        self.data_dir = Path(data_dir).resolve()
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        
        logger.info(f"Local Data Cleaner initialized")
        logger.info(f"Data directory: {self.data_dir}")
    
    def analyze_files(self) -> Dict:
        """Анализирует все файлы в папке local_data"""
        logger.info("🔍 Analyzing local data files...")
        
        # Паттерн для локальных файлов: local_CATEGORY_TIMESTAMP.json
        pattern = r"local_([^_]+(?:_[^_]+)*)_(\d{8}_\d{6})\.(?:json|meta\.json)$"
        
        files_by_category = {}
        meta_files = {}
        json_files = {}
        
        # Сканируем все файлы
        for file_path in self.data_dir.glob("*.json"):
            match = re.match(pattern, file_path.name)
            if match:
                category = match.group(1)
                timestamp = match.group(2)
                
                if file_path.name.endswith('.meta.json'):
                    if category not in meta_files:
                        meta_files[category] = []
                    meta_files[category].append({
                        'path': file_path,
                        'timestamp': timestamp,
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                    })
                else:  # .json файлы
                    if category not in json_files:
                        json_files[category] = []
                    json_files[category].append({
                        'path': file_path,
                        'timestamp': timestamp,
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                    })
        
        # Объединяем информацию
        all_categories = set(list(meta_files.keys()) + list(json_files.keys()))
        
        for category in all_categories:
            files_by_category[category] = {
                'json_files': json_files.get(category, []),
                'meta_files': meta_files.get(category, []),
                'total_files': len(json_files.get(category, [])) + len(meta_files.get(category, []))
            }
        
        return files_by_category
    
    def get_duplicates_analysis(self) -> Dict:
        """Анализирует дубли по категориям"""
        files_by_category = self.analyze_files()
        
        duplicates = {}
        unique_categories = {}
        total_files = 0
        total_duplicates = 0
        total_size = 0
        duplicate_size = 0
        
        for category, files_info in files_by_category.items():
            json_files = files_info['json_files']
            meta_files = files_info['meta_files']
            
            total_files += len(json_files) + len(meta_files)
            
            # Если есть дубли по категории
            if len(json_files) > 1 or len(meta_files) > 1:
                # Сортируем по времени (новые первыми)
                json_files.sort(key=lambda x: x['timestamp'], reverse=True)
                meta_files.sort(key=lambda x: x['timestamp'], reverse=True)
                
                duplicates[category] = {
                    'json_files': {
                        'latest': json_files[0] if json_files else None,
                        'duplicates': json_files[1:] if len(json_files) > 1 else []
                    },
                    'meta_files': {
                        'latest': meta_files[0] if meta_files else None,
                        'duplicates': meta_files[1:] if len(meta_files) > 1 else []
                    }
                }
                
                # Подсчитываем статистику
                json_dups = len(json_files) - 1 if len(json_files) > 1 else 0
                meta_dups = len(meta_files) - 1 if len(meta_files) > 1 else 0
                total_duplicates += json_dups + meta_dups
                
                # Размер дублей
                for dup in json_files[1:]:
                    duplicate_size += dup['size']
                for dup in meta_files[1:]:
                    duplicate_size += dup['size']
            
            else:
                unique_categories[category] = files_info
            
            # Общий размер
            for file_info in json_files + meta_files:
                total_size += file_info['size']
        
        return {
            'duplicates': duplicates,
            'unique_categories': unique_categories,
            'stats': {
                'total_files': total_files,
                'total_duplicates': total_duplicates,
                'total_size_mb': total_size / 1024 / 1024,
                'duplicate_size_mb': duplicate_size / 1024 / 1024,
                'categories_with_duplicates': len(duplicates),
                'unique_categories': len(unique_categories)
            }
        }
    
    def show_analysis(self):
        """Показывает детальный анализ дублей"""
        analysis = self.get_duplicates_analysis()
        duplicates = analysis['duplicates']
        unique_categories = analysis['unique_categories']
        stats = analysis['stats']
        
        logger.info("="*70)
        logger.info("📊 АНАЛИЗ ЛОКАЛЬНЫХ ДУБЛИРУЮЩИХ ФАЙЛОВ")
        logger.info("="*70)
        
        if duplicates:
            logger.info(f"❌ Найдено {stats['categories_with_duplicates']} категорий с дублями:")
            
            for category, files_info in duplicates.items():
                json_info = files_info['json_files']
                meta_info = files_info['meta_files']
                
                logger.info(f"\n📂 Категория: {category}")
                
                # JSON файлы
                if json_info['latest']:
                    logger.info(f"   📄 JSON файлы:")
                    latest = json_info['latest']
                    logger.info(f"      ✅ Оставить: {latest['path'].name}")
                    logger.info(f"         Размер: {latest['size'] / 1024:.1f} KB")
                    logger.info(f"         Время: {latest['timestamp']}")
                    
                    if json_info['duplicates']:
                        logger.info(f"      ❌ Удалить {len(json_info['duplicates'])} дублей:")
                        for dup in json_info['duplicates']:
                            logger.info(f"         • {dup['path'].name} ({dup['size'] / 1024:.1f} KB)")
                
                # Meta файлы
                if meta_info['latest']:
                    logger.info(f"   📝 Meta файлы:")
                    latest = meta_info['latest']
                    logger.info(f"      ✅ Оставить: {latest['path'].name}")
                    
                    if meta_info['duplicates']:
                        logger.info(f"      ❌ Удалить {len(meta_info['duplicates'])} дублей:")
                        for dup in meta_info['duplicates']:
                            logger.info(f"         • {dup['path'].name}")
        
        if unique_categories:
            logger.info(f"\n✅ Уникальные категории ({len(unique_categories)}):")
            for category, files_info in unique_categories.items():
                json_count = len(files_info['json_files'])
                meta_count = len(files_info['meta_files'])
                logger.info(f"   • {category} - {json_count} JSON + {meta_count} meta")
        
        # Итоговая статистика
        logger.info(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
        logger.info(f"   Всего файлов: {stats['total_files']}")
        logger.info(f"   Дублей к удалению: {stats['total_duplicates']}")
        logger.info(f"   Общий размер: {stats['total_size_mb']:.1f} MB")
        logger.info(f"   Размер дублей: {stats['duplicate_size_mb']:.1f} MB")
        logger.info(f"   Освободится места: {stats['duplicate_size_mb']:.1f} MB")
        logger.info(f"   Останется файлов: {stats['total_files'] - stats['total_duplicates']}")
        
        if not duplicates:
            logger.info("✅ Дублирующих файлов не найдено!")
    
    def simulate_cleanup(self):
        """Симуляция очистки (показывает что будет удалено)"""
        analysis = self.get_duplicates_analysis()
        duplicates = analysis['duplicates']
        stats = analysis['stats']
        
        if not duplicates:
            logger.info("✅ Нет дублей для удаления")
            return
        
        logger.info("🔍 СИМУЛЯЦИЯ ОЧИСТКИ (файлы НЕ удаляются):")
        logger.info("="*50)
        
        files_to_delete = []
        
        for category, files_info in duplicates.items():
            json_duplicates = files_info['json_files']['duplicates']
            meta_duplicates = files_info['meta_files']['duplicates']
            
            logger.info(f"\n📂 {category}:")
            
            for dup in json_duplicates:
                logger.info(f"🗑️  JSON: {dup['path'].name} ({dup['size'] / 1024:.1f} KB)")
                files_to_delete.append(str(dup['path']))
            
            for dup in meta_duplicates:
                logger.info(f"🗑️  Meta: {dup['path'].name}")
                files_to_delete.append(str(dup['path']))
        
        logger.info(f"\n📊 РЕЗУЛЬТАТ СИМУЛЯЦИИ:")
        logger.info(f"   Файлов к удалению: {len(files_to_delete)}")
        logger.info(f"   Освободится места: {stats['duplicate_size_mb']:.1f} MB")
        logger.info(f"   Останется файлов: {stats['total_files'] - len(files_to_delete)}")
    
    def cleanup_duplicates(self, dry_run=True):
        """Реальная очистка дублей"""
        analysis = self.get_duplicates_analysis()
        duplicates = analysis['duplicates']
        
        if not duplicates:
            logger.info("✅ Нет дублей для удаления")
            return 0
        
        if dry_run:
            logger.info("🔍 DRY RUN - файлы НЕ будут удалены")
        else:
            logger.info("⚠️  РЕАЛЬНАЯ ОЧИСТКА - файлы БУДУТ удалены!")
        
        deleted_count = 0
        
        for category, files_info in duplicates.items():
            json_duplicates = files_info['json_files']['duplicates']
            meta_duplicates = files_info['meta_files']['duplicates']
            
            # Удаляем JSON дубли
            for dup in json_duplicates:
                try:
                    if not dry_run:
                        dup['path'].unlink()
                    logger.info(f"🗑️  Удален: {dup['path'].name}")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"❌ Ошибка удаления {dup['path'].name}: {e}")
            
            # Удаляем meta дубли
            for dup in meta_duplicates:
                try:
                    if not dry_run:
                        dup['path'].unlink()
                    logger.info(f"🗑️  Удален: {dup['path'].name}")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"❌ Ошибка удаления {dup['path'].name}: {e}")
        
        return deleted_count


def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cleanup duplicate local data files')
    parser.add_argument('--data-dir', type=str, default='../local_data',
                       help='Local data directory (default: ../local_data)')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze duplicate files')
    parser.add_argument('--simulate', action='store_true',
                       help='Simulate cleanup (show what would be deleted)')
    parser.add_argument('--cleanup', action='store_true',
                       help='Perform real cleanup (DELETE files)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Dry run mode (default: true)')
    
    args = parser.parse_args()
    
    try:
        cleaner = LocalDataCleaner(data_dir=args.data_dir)
        
        if args.analyze:
            cleaner.show_analysis()
        elif args.simulate:
            cleaner.simulate_cleanup()
        elif args.cleanup:
            if not args.dry_run:
                # Подтверждение для реального удаления
                response = input("⚠️  Вы уверены что хотите удалить дублирующие файлы? (y/N): ")
                if response.lower() != 'y':
                    logger.info("Операция отменена")
                    return 0
            
            deleted = cleaner.cleanup_duplicates(dry_run=args.dry_run)
            logger.info(f"✅ Обработано файлов: {deleted}")
        else:
            # По умолчанию показываем анализ
            cleaner.show_analysis()
            logger.info("\n💡 Команды:")
            logger.info("   --simulate  - симуляция очистки")
            logger.info("   --cleanup   - реальная очистка (с подтверждением)")
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == '__main__':
    exit(main()) 