#!/usr/bin/env python3
"""
Обёртка для old_dns_parser с интеграцией веб-интерфейса
"""

import os
import sys
import json
import logging
import requests
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import shutil

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('dns_wrapper')

class DNSParserWrapper:
    def __init__(self, server_url="http://127.0.0.1:5000", visible_browser=True):
        """
        Обёртка для old_dns_parser
        
        Args:
            server_url: URL сервера для отправки данных
            visible_browser: Показывать ли браузер (для old_dns_parser всегда видимый)
        """
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.visible_browser = visible_browser
        
        # Путь к old_dns_parser
        current_dir = Path(__file__).parent
        self.old_parser_dir = current_dir.parent / "app" / "utils" / "old_dns_parser"
        
        # Логируем настройки
        logger.info(f"DNS Parser Wrapper initialized")
        logger.info(f"Server URL: {self.server_url}")
        logger.info(f"Old parser directory: {self.old_parser_dir}")
        logger.info(f"Visible browser: {self.visible_browser}")
        
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
    
    def prepare_categories(self, category_name=None):
        """Подготовка файла категорий"""
        categories_file = self.old_parser_dir / "categories.json"
        backup_file = self.old_parser_dir / "categories_backup.json"
        
        # Восстанавливаем из backup если нужно
        if backup_file.exists():
            logger.info("Restoring categories from backup")
            shutil.copy(backup_file, categories_file)
        
        # Если указана конкретная категория, фильтруем
        if category_name:
            logger.info(f"Filtering categories for: {category_name}")
            try:
                with open(categories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Фильтруем категории
                filtered_data = []
                for item in data:
                    if 'categories' in item:
                        filtered_categories = {}
                        for cat_name, cat_data in item['categories'].items():
                            if category_name.lower() in cat_name.lower():
                                filtered_categories[cat_name] = cat_data
                        
                        if filtered_categories:
                            filtered_data.append({'categories': filtered_categories})
                
                # Сохраняем отфильтрованные категории
                with open(categories_file, 'w', encoding='utf-8') as f:
                    json.dump(filtered_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Categories filtered: {len(filtered_data)} items")
                
            except Exception as e:
                logger.error(f"Error filtering categories: {e}")
                return False
        
        return True
    
    def run_old_parser(self, category_name=None, limit=5):
        """Запуск old_dns_parser"""
        logger.info(f"Starting old DNS parser...")
        logger.info(f"Category: {category_name or 'all'}")
        logger.info(f"Limit: {limit}")
        
        # Подготавливаем категории
        if not self.prepare_categories(category_name):
            return False
        
        # Переходим в директорию old_dns_parser
        original_cwd = os.getcwd()
        try:
            os.chdir(self.old_parser_dir)
            logger.info(f"Changed directory to: {self.old_parser_dir}")
            
            # Добавляем путь в sys.path
            if str(self.old_parser_dir) not in sys.path:
                sys.path.insert(0, str(self.old_parser_dir))
            
            # Импортируем и запускаем main
            try:
                import main
                logger.info("🚀 Starting old_dns_parser main function...")
                logger.info("🎯 Browser window should open and show DNS-shop parsing process!")
                
                # Запускаем парсер
                product_urls = main.main(
                    category_name=category_name,
                    limit_per_category=limit
                )
                
                logger.info(f"✅ Old parser completed. Found {len(product_urls) if product_urls else 0} URLs")
                return True
                
            except Exception as e:
                logger.error(f"❌ Error running old parser: {e}")
                import traceback
                traceback.print_exc()
                return False
            
        finally:
            # Возвращаемся в исходную директорию
            os.chdir(original_cwd)
    
    def send_results_to_server(self):
        """Отправка результатов на сервер"""
        product_data_file = self.old_parser_dir / "product_data.json"
        
        if not product_data_file.exists():
            logger.warning("No product_data.json found")
            return False
        
        try:
            with open(product_data_file, 'r', encoding='utf-8') as f:
                all_products = json.load(f)
            
            if not all_products:
                logger.warning("No products in product_data.json")
                return False
            
            # Ищем только новые товары (добавленные в последние 5 минут)
            recent_products = []
            cutoff_time = datetime.now() - timedelta(minutes=5)
            
            for product in all_products:
                # Если есть поле last_updated, проверяем время
                if 'last_updated' in product:
                    try:
                        product_time = datetime.fromisoformat(product['last_updated'].replace('Z', '+00:00'))
                        if product_time.replace(tzinfo=None) > cutoff_time:
                            recent_products.append(product)
                    except:
                        continue
                # Если нет поля времени, то считаем товар новым (для совместимости)
                elif len(recent_products) < 10:  # Максимум 10 товаров без времени
                    recent_products.append(product)
            
            # Если не найдены недавние товары, берём последние несколько
            if not recent_products:
                logger.info("No recent products found by timestamp, taking last 5 products")
                recent_products = all_products[-5:] if len(all_products) >= 5 else all_products
            
            logger.info(f"Sending {len(recent_products)} NEW products to server (out of {len(all_products)} total)...")
            
            payload = {
                'products': recent_products,
                'source': 'old_dns_parser_new',
                'total_in_file': len(all_products),
                'new_products_count': len(recent_products),
                'timestamp': datetime.now().isoformat(),
                'parser_version': '2.0'
            }
            
            response = self.session.post(
                f"{self.server_url}/api/upload-products",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Successfully sent {len(recent_products)} NEW products to server: {result.get('message')}")
                return True
            else:
                logger.error(f"❌ Server returned status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to send data to server: {e}")
            return False

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='DNS Parser Wrapper')
    parser.add_argument('--category', type=str, help='Category name to parse (e.g., videokarty)')
    parser.add_argument('--limit', type=int, default=5, help='Number of products to parse per category')
    parser.add_argument('--server-url', type=str, default='http://127.0.0.1:5000', help='Server URL')
    parser.add_argument('--test-only', action='store_true', help='Only test server connection')
    parser.add_argument('--product-url', type=str, help='Parse single product by URL (not supported in old parser)')
    
    args = parser.parse_args()
    
    # Инициализация обёртки
    wrapper = DNSParserWrapper(server_url=args.server_url)
    
    try:
        # Тестируем соединение с сервером
        if not wrapper.test_server_connection():
            logger.error("Cannot connect to server. Please check server is running.")
            return 1
        
        if args.test_only:
            logger.info("✅ Connection test completed successfully")
            return 0
        
        if args.product_url:
            logger.error("Single product parsing not supported with old parser")
            return 1
        
        # Запускаем old_dns_parser
        logger.info("🎯 Starting DNS parsing with VISIBLE browser!")
        if wrapper.run_old_parser(args.category, args.limit):
            # Отправляем результаты на сервер
            if wrapper.send_results_to_server():
                logger.info("✅ Parsing completed successfully!")
                return 0
            else:
                logger.error("❌ Failed to send results to server")
                return 1
        else:
            logger.error("❌ Parsing failed")
            return 1
    
    except KeyboardInterrupt:
        logger.info("Parsing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 