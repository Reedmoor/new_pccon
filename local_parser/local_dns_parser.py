#!/usr/bin/env python3
"""
Локальный DNS парсер для Windows
Парсит данные локально и отправляет на сервер
"""

import os
import sys
import json
import logging
import requests
import time
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path
from datetime import datetime
import argparse

# Добавляем путь к модулям парсера
current_dir = Path(__file__).parent
parser_modules_dir = current_dir.parent / "app" / "utils" / "old_dns_parser"
sys.path.insert(0, str(parser_modules_dir))

# Импортируем модули парсера
from productDetailsParser import parse_characteristics_page, extract_images, parse_characteristics, parse_product_data, parse_breadcrumbs
from linksParser import get_urls_from_page, generate_urls_from_json

# Настройка логирования
log_file = current_dir / 'local_dns_parser.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)
logger = logging.getLogger('local_dns_parser')

# Создаем дополнительный файловый логгер для детальных логов
detailed_log_file = current_dir / f'parser_session_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
detailed_handler = logging.FileHandler(detailed_log_file, encoding='utf-8')
detailed_handler.setLevel(logging.DEBUG)
detailed_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
detailed_handler.setFormatter(detailed_formatter)

# Создаем отдельный логгер для детальных логов
detailed_logger = logging.getLogger('detailed_parser')
detailed_logger.addHandler(detailed_handler)
detailed_logger.setLevel(logging.DEBUG)

class LocalDNSParser:
    def __init__(self, server_url="https://pcconf.ru"):
        """
        Инициализация локального парсера
        
        Args:
            server_url: URL сервера для отправки данных (Docker сервер по умолчанию)
        """
        self.server_url = server_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Настройки для парсинга
        self.max_retries = 3
        self.delay_between_requests = 1.0
        self.products = []
        
        # Настройка локального логирования
        self.session_start = datetime.now()
        self.log_messages = []
        
        # Логируем начало сессии
        self.log_detailed(f"Parser session started: {self.session_start.isoformat()}")
        self.log_detailed(f"Docker Server URL: {self.server_url}")
        
    def log_detailed(self, message, level='INFO'):
        """Детальное логирование в отдельный файл"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        
        # Добавляем в локальный список
        self.log_messages.append(log_entry)
        
        # Логируем через detailed_logger
        if level == 'ERROR':
            detailed_logger.error(message)
        elif level == 'WARNING':
            detailed_logger.warning(message)
        elif level == 'DEBUG':
            detailed_logger.debug(message)
        else:
            detailed_logger.info(message)
        
        # Также выводим в основной лог
        logger.info(f"[DETAILED] {message}")
    
    def save_session_log(self):
        """Сохранение полного лога сессии"""
        try:
            session_log_file = current_dir / f'session_log_{self.session_start.strftime("%Y%m%d_%H%M%S")}.txt'
            
            with open(session_log_file, 'w', encoding='utf-8') as f:
                f.write(f"DNS Parser Session Log\n")
                f.write(f"Session Start: {self.session_start.isoformat()}\n")
                f.write(f"Session End: {datetime.now().isoformat()}\n")
                f.write(f"Server URL: {self.server_url}\n")
                f.write(f"Total Messages: {len(self.log_messages)}\n")
                f.write(f"Parsed Products: {len(self.products)}\n")
                f.write("="*50 + "\n\n")
                
                for log_entry in self.log_messages:
                    f.write(log_entry + "\n")
                
                if self.products:
                    f.write("\n" + "="*50 + "\n")
                    f.write("PARSED PRODUCTS SUMMARY:\n")
                    f.write("="*50 + "\n")
                    for i, product in enumerate(self.products, 1):
                        f.write(f"{i}. {product.get('name', 'Unknown Product')}\n")
                        f.write(f"   URL: {product.get('url', 'N/A')}\n")
                        f.write(f"   Price: {product.get('price_discounted', 'N/A')}\n")
                        f.write("\n")
            
            logger.info(f"Session log saved to: {session_log_file}")
            return str(session_log_file)
            
        except Exception as e:
            logger.error(f"Failed to save session log: {e}")
            return None
    
    def init_chrome_driver(self, headless=False):
        """Инициализация Chrome драйвера для локальной работы"""
        logger.info(f"Initializing Chrome driver for local parsing... (headless={headless})")
        
        options = Options()
        
        # Настройки отображения
        if headless:
            logger.info("Running in HEADLESS mode (no browser window)")
            options.add_argument('--headless')
        else:
            logger.info("Running in VISIBLE mode (browser window will be shown)")
            # Убеждаемся, что окно видимое
            options.add_argument('--start-maximized')
        
        # Базовые опции
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Обход детекции автоматизации
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--exclude-switches=enable-automation')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-first-run')
        options.add_argument('--disable-default-apps')
        
        # Реалистичный User-Agent для Windows
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36')
        
        try:
            # Получаем путь к ChromeDriver через webdriver-manager
            chromedriver_path = ChromeDriverManager().install()
            logger.info(f"ChromeDriver path: {chromedriver_path}")
            
            # Исправляем путь если webdriver-manager вернул неправильный файл
            if 'THIRD_PARTY_NOTICES' in chromedriver_path:
                import os
                chrome_dir = os.path.dirname(chromedriver_path)
                chromedriver_exe = os.path.join(chrome_dir, 'chromedriver.exe')
                if os.path.exists(chromedriver_exe):
                    chromedriver_path = chromedriver_exe
                    logger.info(f"Fixed ChromeDriver path: {chromedriver_path}")
                else:
                    logger.error(f"ChromeDriver executable not found in {chrome_dir}")
                    return False
            
            # Используем undetected-chromedriver
            self.driver = uc.Chrome(
                options=options,
                driver_executable_path=chromedriver_path
            )
            
            # Дополнительные настройки для обхода детекции
            try:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
                self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU', 'ru', 'en-US', 'en']})")
                logger.info("Applied anti-detection scripts")
            except Exception as e:
                logger.warning(f"Could not apply anti-detection scripts: {e}")
            
            # Логируем информацию о режиме браузера
            if headless:
                logger.info("✅ Chrome driver initialized successfully in HEADLESS mode")
            else:
                logger.info("✅ Chrome driver initialized successfully in VISIBLE mode - browser window should be open!")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            return False
    
    def test_server_connection(self):
        """Тестирование соединения с сервером"""
        try:
            self.log_detailed(f"Testing connection to server: {self.server_url}")
            logger.info(f"Testing connection to server: {self.server_url}")
            response = self.session.get(f"{self.server_url}/api/test-connection", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                success_msg = f"✅ Server connection successful: {data.get('message')}"
                logger.info(success_msg)
                self.log_detailed(success_msg)
                return True
            else:
                error_msg = f"❌ Server returned status {response.status_code}"
                logger.error(error_msg)
                self.log_detailed(error_msg, 'ERROR')
                return False
                
        except requests.exceptions.RequestException as e:
            error_msg = f"❌ Failed to connect to server: {e}"
            logger.error(error_msg)
            self.log_detailed(error_msg, 'ERROR')
            return False
    
    def parse_single_product(self, url):
        """Парсинг одного товара"""
        self.log_detailed(f"Starting product parsing: {url}")
        logger.info(f"Parsing product: {url}")
        
        try:
            # Используем функцию из productDetailsParser
            product_data = parse_characteristics_page(self.driver, url)
            
            if product_data:
                self.products.append(product_data)
                success_msg = f"✅ Successfully parsed: {product_data.get('name', 'Unknown')}"
                logger.info(success_msg)
                self.log_detailed(success_msg)
                self.log_detailed(f"Product details: Price={product_data.get('price_discounted', 'N/A')}, Brand={product_data.get('brand_name', 'N/A')}")
                return product_data
            else:
                error_msg = f"❌ Failed to parse product: {url}"
                logger.warning(error_msg)
                self.log_detailed(error_msg, 'WARNING')
                return None
                
        except Exception as e:
            error_msg = f"❌ Error parsing product {url}: {e}"
            logger.error(error_msg)
            self.log_detailed(error_msg, 'ERROR')
            return None
    
    def parse_category_products(self, category_name, limit_per_category=5):
        """Парсинг товаров из категории"""
        logger.info(f"Parsing category: {category_name} (limit: {limit_per_category})")
        
        # Загружаем конфигурацию категорий
        categories_file = parser_modules_dir / "categories.json"
        if not categories_file.exists():
            logger.error(f"Categories file not found: {categories_file}")
            return []
        
        with open(categories_file, 'r', encoding='utf-8') as f:
            categories_data = json.load(f)
        
        # Генерируем URLs для категорий
        # Проверяем структуру данных и адаптируем к функции generate_urls_from_json
        if isinstance(categories_data, dict) and 'categories' in categories_data:
            # Новая структура - объект с полем categories
            adapted_data = [categories_data]
        elif isinstance(categories_data, list):
            # Старая структура - массив объектов
            adapted_data = categories_data
        else:
            logger.error(f"Unexpected categories.json structure: {type(categories_data)}")
            return []
        
        urls_to_parse = generate_urls_from_json(adapted_data)
        
        # Фильтруем по названию категории если указано
        if category_name:
            filtered_urls = []
            logger.info(f"Generated URLs: {urls_to_parse}")
            logger.info(f"Looking for category: {category_name}")
            
            for url in urls_to_parse:
                # Проверяем, содержит ли URL название категории
                if category_name.lower() in url.lower():
                    filtered_urls.append(url)
                    logger.info(f"✅ Matched URL: {url}")
                else:
                    logger.info(f"❌ Skipped URL: {url}")
            
            urls_to_parse = filtered_urls
        
        if not urls_to_parse:
            logger.warning(f"No URLs found for category: {category_name}")
            logger.info("Available categories in the file:")
            # Показываем доступные категории для отладки
            for item in categories_data:
                if 'categories' in item:
                    for cat_name, cat_data in item['categories'].items():
                        logger.info(f"  - {cat_name}: {cat_data['url']}")
            return []
        
        logger.info(f"Found {len(urls_to_parse)} category URLs")
        
        collected_urls = []
        
        # Собираем ссылки на товары
        for category_url in urls_to_parse:
            logger.info(f"Collecting product links from: {category_url}")
            
            try:
                formatted_url = category_url.format(page=1)
                self.driver.get(formatted_url)
                time.sleep(3)  # Ждем загрузки
                
                # Собираем ссылки на товары
                product_urls = get_urls_from_page(self.driver)
                collected_urls.extend(product_urls[:limit_per_category])
                
                logger.info(f"Collected {len(product_urls)} product URLs from category")
                
                if len(collected_urls) >= limit_per_category:
                    break
                    
            except Exception as e:
                logger.error(f"Error collecting URLs from {category_url}: {e}")
        
        # Ограничиваем общее количество
        collected_urls = collected_urls[:limit_per_category]
        logger.info(f"Total URLs to parse: {len(collected_urls)}")
        
        # Парсим товары
        parsed_count = 0
        for i, url in enumerate(collected_urls, 1):
            logger.info(f"Parsing product {i}/{len(collected_urls)}")
            
            product_data = self.parse_single_product(url)
            if product_data:
                parsed_count += 1
            
            # Пауза между запросами
            time.sleep(2)
        
        logger.info(f"Successfully parsed {parsed_count}/{len(collected_urls)} products")
        return self.products[-parsed_count:] if parsed_count > 0 else []
    
    def send_data_to_server(self, products=None):
        """Отправка данных на сервер"""
        if products is None:
            products = self.products
        
        if not products:
            logger.warning("No products to send")
            return False
        
        logger.info(f"Sending {len(products)} products to server...")
        
        try:
            payload = {
                'products': products,
                'source': 'local_parser',
                'timestamp': datetime.now().isoformat(),
                'parser_version': '1.0'
            }
            
            response = self.session.post(
                f"{self.server_url}/api/upload-products",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Successfully sent data to server: {result.get('message')}")
                return True
            else:
                logger.error(f"❌ Server returned status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to send data to server: {e}")
            return False
    
    def save_data_locally(self, filename=None):
        """Сохранение данных локально в папку data/dns для последующей отправки на Docker сервер"""
        if not self.products:
            logger.warning("No products to save")
            return False
        
        # Создаем папку data/dns если не существует
        current_dir = Path(__file__).parent
        data_dir = current_dir.parent / "data" / "dns"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dns_{timestamp}.json"
        
        filepath = data_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Saved {len(self.products)} products to {filepath}")
            self.log_detailed(f"Data saved locally: {filepath}")
            return str(filepath)
            
        except Exception as e:
            error_msg = f"Failed to save data locally: {e}"
            logger.error(f"❌ {error_msg}")
            self.log_detailed(error_msg, 'ERROR')
            return False
    
    def close(self):
        """Закрытие драйвера и сохранение логов"""
        # Логируем завершение сессии
        self.log_detailed("Closing parser session")
        self.log_detailed(f"Total products parsed: {len(self.products)}")
        self.log_detailed(f"Session duration: {datetime.now() - self.session_start}")
        
        # Сохраняем детальный лог сессии
        session_log_path = self.save_session_log()
        if session_log_path:
            logger.info(f"📝 Session log saved: {session_log_path}")
        
        # Закрываем драйвер
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome driver closed")
                self.log_detailed("Chrome driver closed successfully")
            except Exception as e:
                error_msg = f"Error closing Chrome driver: {e}"
                logger.error(error_msg)
                self.log_detailed(error_msg, 'ERROR')

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Local DNS Parser for Docker Server')
    parser.add_argument('--category', type=str, help='Category name to parse (e.g., videokarty)')
    parser.add_argument('--limit', type=int, default=5, help='Number of products to parse per category')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--server-url', type=str, default='https://pcconf.ru', help='Docker Server URL')
    parser.add_argument('--test-only', action='store_true', help='Only test Docker server connection')
    parser.add_argument('--product-url', type=str, help='Parse single product by URL')
    parser.add_argument('--save-only', action='store_true', help='Only save data locally, do not send to server')
    
    args = parser.parse_args()
    
    # Инициализация парсера с Docker сервером
    dns_parser = LocalDNSParser(server_url=args.server_url)
    
    try:
        # Тестируем соединение с Docker сервером
        if not args.save_only:
            logger.info("🔍 Testing connection to Docker server...")
            if not dns_parser.test_server_connection():
                logger.warning("⚠️ Cannot connect to Docker server. Data will be saved locally only.")
                logger.warning("   Start Docker server with: docker-compose up -d")
                args.save_only = True
        
        if args.test_only:
            logger.info("✅ Docker connection test completed")
            return 0
        
        # Инициализируем браузер
        logger.info("🌐 Initializing Chrome browser...")
        if not dns_parser.init_chrome_driver(headless=args.headless):
            logger.error("❌ Failed to initialize Chrome driver")
            return 1
        
        # Парсинг одного товара
        if args.product_url:
            logger.info(f"🔍 Parsing single product: {args.product_url}")
            product_data = dns_parser.parse_single_product(args.product_url)
            
            if product_data:
                # Сохраняем локально
                local_file = dns_parser.save_data_locally()
                
                # Отправляем на Docker сервер если доступен
                if not args.save_only:
                    if dns_parser.send_data_to_server([product_data]):
                        logger.info("✅ Product sent to Docker server successfully")
                    else:
                        logger.warning("⚠️ Failed to send to Docker server, but saved locally")
                
                logger.info("✅ Single product parsing completed")
                return 0
            else:
                logger.error("❌ Failed to parse product")
                return 1
        
        # Парсинг категории
        logger.info(f"🚀 Starting category parsing: {args.category or 'all categories'}")
        logger.info(f"📊 Limit per category: {args.limit}")
        
        products = dns_parser.parse_category_products(args.category, args.limit)
        
        if products:
            # Всегда сохраняем локально как резервную копию
            local_file = dns_parser.save_data_locally()
            logger.info(f"💾 Local backup saved: {local_file}")
            
            # Отправляем на Docker сервер если доступен
            if not args.save_only:
                logger.info("📤 Sending data to Docker server...")
                if dns_parser.send_data_to_server():
                    logger.info("✅ Data successfully sent to Docker server")
                    logger.info("🎉 Parsing and upload completed successfully!")
                else:
                    logger.warning("⚠️ Failed to send to Docker server")
                    logger.info("💾 Data saved locally. Use upload_to_docker.py to send later")
            else:
                logger.info("💾 Data saved locally only (as requested)")
                logger.info("📤 Use upload_to_docker.py to send to Docker server later")
            
            return 0
        else:
            logger.error("❌ No products were parsed")
            return 1
    
    except KeyboardInterrupt:
        logger.info("⏹️ Parsing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1
    finally:
        dns_parser.close()

if __name__ == '__main__':
    sys.exit(main()) 