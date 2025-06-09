#!/usr/bin/env python3
"""
Скрипт для очистки дублирующих JSON файлов на Docker сервере
Оставляет только последние файлы, удаляет старые дубли
"""

import requests
import json
import logging
from datetime import datetime
from typing import List, Dict

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cleanup_duplicates')

class DockerServerCleaner:
    def __init__(self, docker_url="http://127.0.0.1:5000"):
        """
        Очистка дублирующих файлов на Docker сервере
        
        Args:
            docker_url: URL Docker сервера
        """
        self.docker_url = docker_url.rstrip('/')
        self.session = requests.Session()
        
        logger.info(f"Docker Server Cleaner initialized")
        logger.info(f"Docker server: {self.docker_url}")
    
    def get_upload_files(self) -> List[Dict]:
        """Получает список загруженных файлов"""
        try:
            response = self.session.get(f"{self.docker_url}/api/parser-status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                uploads = data.get('recent_uploads', [])
                logger.info(f"Found {len(uploads)} upload files")
                return uploads
            else:
                logger.error(f"Failed to get uploads: status {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting upload files: {e}")
            return []
    
    def analyze_duplicates(self, uploads: List[Dict]) -> Dict:
        """Анализирует дубли файлов"""
        # Группируем файлы по количеству товаров
        groups = {}
        for upload in uploads:
            count = upload.get('product_count', 0)
            filename = upload.get('filename', '')
            
            if count not in groups:
                groups[count] = []
            groups[count].append(upload)
        
        # Находим дубли (файлы с одинаковым количеством товаров)
        duplicates = {}
        unique_files = {}
        
        for count, files in groups.items():
            if len(files) > 1:
                # Сортируем по времени (новые первыми)
                files.sort(key=lambda x: x.get('upload_time', ''), reverse=True)
                duplicates[count] = {
                    'latest': files[0],
                    'duplicates': files[1:],
                    'total_duplicates': len(files) - 1
                }
            else:
                unique_files[count] = files[0]
        
        return {
            'duplicates': duplicates,
            'unique_files': unique_files,
            'total_files': len(uploads)
        }
    
    def show_duplicate_analysis(self):
        """Показывает анализ дублирующих файлов"""
        uploads = self.get_upload_files()
        if not uploads:
            logger.info("No upload files found")
            return
        
        analysis = self.analyze_duplicates(uploads)
        duplicates = analysis['duplicates']
        unique_files = analysis['unique_files']
        
        logger.info("="*50)
        logger.info("📊 АНАЛИЗ ДУБЛИРУЮЩИХ ФАЙЛОВ")
        logger.info("="*50)
        
        if duplicates:
            logger.info(f"❌ Найдено {len(duplicates)} групп дублей:")
            
            total_duplicate_files = 0
            for count, group in duplicates.items():
                latest = group['latest']
                dups = group['duplicates']
                total_duplicate_files += len(dups)
                
                logger.info(f"\n🔢 Файлы с {count:,} товарами:")
                logger.info(f"   ✅ Оставить: {latest['filename']}")
                logger.info(f"      Время: {latest['upload_time']}")
                
                logger.info(f"   ❌ Удалить {len(dups)} дублей:")
                for dup in dups:
                    logger.info(f"      • {dup['filename']} ({dup['upload_time']})")
            
            logger.info(f"\n📋 ИТОГО:")
            logger.info(f"   Всего файлов: {analysis['total_files']}")
            logger.info(f"   Дублей к удалению: {total_duplicate_files}")
            logger.info(f"   Останется файлов: {analysis['total_files'] - total_duplicate_files}")
        
        if unique_files:
            logger.info(f"\n✅ Уникальные файлы ({len(unique_files)}):")
            for count, file_info in unique_files.items():
                logger.info(f"   • {file_info['filename']} - {count:,} товаров")
        
        if not duplicates:
            logger.info("✅ Дублирующих файлов не найдено!")
    
    def cleanup_duplicates_simulation(self):
        """Симуляция очистки дублей (показывает что будет удалено)"""
        uploads = self.get_upload_files()
        if not uploads:
            return
        
        analysis = self.analyze_duplicates(uploads)
        duplicates = analysis['duplicates']
        
        if not duplicates:
            logger.info("✅ Нет дублей для удаления")
            return
        
        logger.info("🔍 СИМУЛЯЦИЯ ОЧИСТКИ (файлы НЕ удаляются):")
        logger.info("="*50)
        
        total_to_delete = 0
        saved_space = 0
        
        for count, group in duplicates.items():
            dups = group['duplicates']
            
            for dup in dups:
                file_size = dup.get('file_size', 0)
                logger.info(f"🗑️  Будет удален: {dup['filename']}")
                logger.info(f"     Размер: {file_size / 1024:.1f} KB")
                logger.info(f"     Время: {dup['upload_time']}")
                total_to_delete += 1
                saved_space += file_size
        
        logger.info(f"\n📊 РЕЗУЛЬТАТ СИМУЛЯЦИИ:")
        logger.info(f"   Файлов к удалению: {total_to_delete}")
        logger.info(f"   Освободится места: {saved_space / 1024 / 1024:.1f} MB")
        logger.info(f"   Останется файлов: {analysis['total_files'] - total_to_delete}")


def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cleanup duplicate files on Docker server')
    parser.add_argument('--docker-url', type=str, default='http://127.0.0.1:5000',
                       help='Docker server URL (default: http://127.0.0.1:5000)')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze duplicate files')
    parser.add_argument('--simulate', action='store_true', 
                       help='Simulate cleanup (show what would be deleted)')
    
    args = parser.parse_args()
    
    cleaner = DockerServerCleaner(docker_url=args.docker_url)
    
    try:
        if args.analyze:
            cleaner.show_duplicate_analysis()
        elif args.simulate:
            cleaner.cleanup_duplicates_simulation()
        else:
            # По умолчанию показываем анализ
            cleaner.show_duplicate_analysis()
            logger.info("\n💡 Используйте --simulate для симуляции очистки")
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    exit(main()) 