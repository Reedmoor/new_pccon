import json
import os
import sys
import logging
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from random import randint, choice
from time import sleep as pause
import shutil
import time

# Настройка логирования для Docker
def setup_logging():
    """Настройка логирования с учетом прав доступа в Docker"""
    log_file = None
    
    # Попробуем различные места для лог файла
    log_paths = [
        '/app/logs/dns_parser.log',
        '/app/data/dns_parser.log', 
        '/home/parser/dns_parser.log',
        'dns_parser.log'
    ]
    
    for path in log_paths:
        try:
            # Создаем директорию если нужно
            log_dir = os.path.dirname(path) if os.path.dirname(path) else '.'
            if not os.path.exists(log_dir) and log_dir != '.':
                os.makedirs(log_dir, exist_ok=True)
            
            # Проверяем возможность записи
            with open(path, 'a') as test_file:
                pass
            log_file = path
            break
        except (PermissionError, OSError):
            continue
    
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),  # Всегда выводим в stdout
            *([logging.FileHandler(log_file, encoding='utf-8')] if log_file else [])
        ]
    )
    
    logger = logging.getLogger('dns_links_parser')
    if log_file:
        logger.info(f"Логирование настроено, файл: {log_file}")
    else:
        logger.warning("Не удалось создать лог файл, используется только stdout")
    
    return logger

# Инициализация логгера
logger = setup_logging()

def get_random_user_agent():
    """Возвращает случайный User-Agent для обхода детекции."""
    user_agents = [
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    ]
    return choice(user_agents)


def simulate_human_behavior(driver):
    """Имитирует человеческое поведение на странице."""
    try:
        # Случайная задержка
        pause(randint(2, 5))
        
        # Имитация движения мыши
        actions = ActionChains(driver)
        
        # Случайные координаты для движения мыши
        x_offset = randint(100, 800)
        y_offset = randint(100, 600)
        
        actions.move_by_offset(x_offset, y_offset).perform()
        pause(randint(1, 3))
        
        # Случайный скроллинг
        driver.execute_script(f"window.scrollTo(0, {randint(100, 500)});")
        pause(randint(1, 2))
        
        # Еще один скролл
        driver.execute_script(f"window.scrollTo(0, {randint(200, 800)});")
        pause(randint(1, 3))
        
    except Exception as e:
        print(f"Warning: Could not simulate human behavior: {e}")


def save_urls_to_file(urls, filename="urls.txt"):
    """
    Сохраняет список URL-адресов в текстовый файл, по одному URL на строку.
    
    Args:
        urls: Список URL-адресов для сохранения
        filename: Имя файла для сохранения (по умолчанию urls.txt)
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            for url in urls:
                f.write(f"{url}\n")
        print(f"Сохранено {len(urls)} URL-адресов в файл {filename}")
    except Exception as e:
        print(f"Ошибка при сохранении URL-адресов в файл: {e}")


def backup_categories_file():
    """Create a backup of categories.json file if it doesn't exist already."""
    source_file = 'categories.json'
    backup_file = 'categories_backup.json'
    
    if not os.path.exists(backup_file) and os.path.exists(source_file):
        shutil.copy2(source_file, backup_file)
        print(f"Created backup file: {backup_file}")
    
    # If categories.json doesn't exist but backup does, restore from backup
    if not os.path.exists(source_file) and os.path.exists(backup_file):
        restore_categories_file()


def restore_categories_file():
    """Restore categories.json from the backup file."""
    backup_file = 'categories_backup.json'
    target_file = 'categories.json'
    
    if os.path.exists(backup_file):
        shutil.copy2(backup_file, target_file)
        print(f"Restored {target_file} from backup")
    else:
        print(f"Warning: Backup file {backup_file} not found!")


def filter_categories_by_name(category_name=None):
    """
    Фильтрует категории в файле categories.json по имени категории.
    Если category_name равен None или пустой строке, возвращает все категории.
    
    Args:
        category_name: Имя категории для фильтрации (например, 'videokarty')
    """
    backup_file = 'categories_backup.json'
    
    # Если резервной копии нет, сначала создаем ее
    if not os.path.exists(backup_file) and os.path.exists('categories.json'):
        backup_categories_file()
    
    # Если все еще нет файла резервной копии, выходим
    if not os.path.exists(backup_file):
        print(f"Резервная копия {backup_file} не найдена.")
        return
    
    # Загружаем данные из резервной копии
    with open(backup_file, 'r', encoding='utf-8') as f:
        all_categories = json.load(f)
    
    # Если категория не указана, используем все категории
    if not category_name:
        with open('categories.json', 'w', encoding='utf-8') as f:
            json.dump(all_categories, f, ensure_ascii=False, indent=4)
        print("Используем все категории")
        return
    
    # Фильтруем категории
    filtered_categories = []
    for item in all_categories:
        if 'categories' in item:
            filtered_item = {"categories": {}}
            for cat_name, cat_data in item['categories'].items():
                if cat_name == category_name:
                    filtered_item["categories"][cat_name] = cat_data
                    filtered_categories.append(filtered_item)
                    break
    
    # Если не нашли нужную категорию
    if not filtered_categories:
        print(f"Категория '{category_name}' не найдена. Используем все категории.")
        with open('categories.json', 'w', encoding='utf-8') as f:
            json.dump(all_categories, f, ensure_ascii=False, indent=4)
    else:
        with open('categories.json', 'w', encoding='utf-8') as f:
            json.dump(filtered_categories, f, ensure_ascii=False, indent=4)
        print(f"Файл categories.json обновлен для категории: {category_name}")


def get_urls_from_page(driver):
    """ Collects all product links on the current page with improved selectors. """
    soup = BeautifulSoup(driver.page_source, 'lxml')
    
    # Отладочная информация
    page_title = soup.find('title')
    print(f"Page title: {page_title.text if page_title else 'No title'}")
    
    # Проверяем, что мы на правильной странице каталога
    if page_title and any(word in page_title.text.lower() for word in ['403', 'forbidden', 'access denied']):
        print("ERROR: Page access forbidden!")
        return []
    
    # Улучшенные селекторы для поиска ссылок на товары
    selectors_to_try = [
        # Основные селекторы DNS
        'a.catalog-product__name.ui-link.ui-link_black',
        'a[class*="catalog-product__name"]',
        'a.catalog-product__name',
        
        # Альтернативные селекторы для карточек товаров
        'a[class*="product-card"] [class*="name"]',
        'a[class*="product-item"] [class*="title"]',
        '.catalog-product .product-name a',
        '.product-card-top__name a',
        
        # Общие селекторы для ссылок на товары
        'a[href*="/product/"]',
        'a[data-testid*="product"]',
        'a[class*="product-link"]',
        
        # Селекторы для различных структур каталога
        '.catalog-products a[href*="product"]',
        '.products-list a[href*="product"]',
        '.product-list-item a',
        '.catalog-product a',
        
        # Дополнительные селекторы
        '[data-id*="product"] a',
        '.product-title a',
        '.item-title a'
    ]
    
    found_elements = []
    used_selector = None
    
    for selector in selectors_to_try:
        try:
            elements = soup.select(selector)
            print(f"Selector '{selector}' found {len(elements)} elements")
            
            # Фильтруем элементы, оставляя только те, которые ведут на товары
            filtered_elements = []
            for element in elements:
                href = element.get('href', '')
                if href and '/product/' in href:
                    filtered_elements.append(element)
            
            print(f"After filtering: {len(filtered_elements)} product links")
            
            if filtered_elements:
                found_elements = filtered_elements
                used_selector = selector
                break
                
        except Exception as e:
            print(f"Error with selector '{selector}': {e}")
            continue
    
    if not found_elements:
        print("No product links found with primary selectors. Trying fallback approach...")
        
        # Fallback: ищем любые ссылки с "product" в href
        all_links = soup.find_all('a', href=True)
        product_links = []
        
        for link in all_links:
            href = link.get('href', '')
            if '/product/' in href and href.startswith('/'):
                # Дополнительная проверка: ссылка должна содержать ID товара
                if len(href.split('/')) >= 3:  # /product/id/name/
                    product_links.append(link)
        
        print(f"Fallback found {len(product_links)} links with '/product/' in href")
        
        if product_links:
            found_elements = product_links[:50]  # Ограничиваем количество
            used_selector = "fallback: a[href*='/product/']"
        else:
            # Последняя попытка: сохраняем HTML для анализа
            debug_file = f'debug_page_{int(time.time())}.html'
            try:
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print(f"No product links found. HTML saved to {debug_file}")
            except Exception as e:
                print(f"Could not save debug HTML: {e}")
            
            return []
    
    # Извлекаем URL-адреса из найденных элементов
    urls = []
    base_url = 'https://www.dns-shop.ru'
    
    for element in found_elements:
        href = element.get('href')
        if href:
            # Нормализуем URL
            if href.startswith('/'):
                full_url = base_url + href
            elif href.startswith('http'):
                full_url = href
            else:
                continue  # Пропускаем относительные ссылки без /
            
            # Проверяем, что это действительно ссылка на товар
            if '/product/' in full_url and full_url not in urls:
                urls.append(full_url)
    
    print(f"Successfully extracted {len(urls)} unique product URLs using selector: {used_selector}")
    
    # Дополнительная проверка: если нашли слишком мало ссылок, возможно структура сайта изменилась
    if len(urls) < 5:
        print("WARNING: Found fewer than 5 product links. Site structure may have changed.")
        
        # Попробуем найти любые элементы, которые могут содержать ссылки на товары
        potential_containers = soup.select('.catalog-product, .product-item, .product-card, [class*="product"]')
        print(f"Found {len(potential_containers)} potential product containers")
        
        for container in potential_containers[:10]:  # Анализируем первые 10
            links_in_container = container.find_all('a', href=True)
            for link in links_in_container:
                href = link.get('href', '')
                if '/product/' in href and href.startswith('/'):
                    full_url = base_url + href
                    if full_url not in urls:
                        urls.append(full_url)
    
    return urls


def get_all_category_page_urls(driver, url_to_parse, limit=None, callback=None):
    """ Get category URL and parse links from it with a limit. 
    If callback is provided, it will be called with each URL one by one. """
    
    # Сначала загружаем главную страницу для имитации человеческого поведения
    try:
        print("Loading main page first...")
        driver.get("https://www.dns-shop.ru/")
        
        # Имитируем человеческое поведение на главной странице
        simulate_human_behavior(driver)
        
        # Проверяем, что главная страница загрузилась
        main_soup = BeautifulSoup(driver.page_source, 'lxml')
        main_title = main_soup.find('title')
        print(f"Main page title: {main_title.text if main_title else 'No title'}")
        
        if main_title and "403" in main_title.text:
            print("ERROR: Main page also returns 403!")
            return []
        else:
            print("Main page loaded successfully")
            
    except Exception as e:
        print(f"Warning: Could not load main page: {e}")
    
    page = 1
    urls = set()  # Using a set to avoid duplicates
    parsed_count = 0

    while len(urls) < limit if limit else True:
        url = url_to_parse.format(page=page)
        print(f"Loading page: {url}")
        
        try:
            driver.get(url)
            
            # Увеличиваем задержку и добавляем имитацию поведения
            pause(randint(4, 8))
            
            # Имитируем человеческое поведение
            simulate_human_behavior(driver)
            
            soup = BeautifulSoup(driver.page_source, 'lxml')

            # Get links from current page
            page_urls = get_urls_from_page(driver)
            
            # Если нашли товары, имитируем еще немного активности
            if page_urls:
                print(f"Found {len(page_urls)} products on page {page}")
                # Еще немного скроллинга если нашли товары
                driver.execute_script(f"window.scrollTo(0, {randint(300, 1000)});")
                pause(randint(2, 4))
            else:
                print(f"No products found on page {page}")

            # Add to the set of URLs and process each URL one by one if callback provided
            for link in page_urls:
                if link not in urls:  # Check if it's a new URL
                    urls.add(link)
                    parsed_count += 1
                    
                    # If callback is provided, call it with the URL
                    if callback:
                        print(f"Processing URL {parsed_count}: {link}")
                        callback(driver, link)
                        
                # Check if we've reached the limit
                if limit and parsed_count >= limit:
                    print(f'Reached limit of {limit} URLs for this category')
                    break
                    
            if limit and parsed_count >= limit:
                break

            # Check for "Next page" button
            next_button = soup.find('a', class_="pagination-widget__page-link pagination-widget__page-link_next")
            if not next_button or 'disabled' in next_button.get('class', []):
                print("No next page found, stopping pagination")
                break

            page += 1
            
        except Exception as e:
            print(f"Error loading page {page}: {e}")
            break

    print(f'Total {len(urls)} unique links collected from category (limit: {limit}).')
    return list(urls)[:limit] if limit else list(urls)  # Convert back to list and respect the limit


def get_links_from_json(file_path="categories_full.json"):
    """Extracts links from categories_full.json."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found. Make sure the JSON file exists.")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Adjust the key depending on your `categories_full.json` structure
    links = [f"https://www.dns-shop.ru{item['url']}" for item in data if "url" in item]
    return links


def generate_urls_from_json(json_data):
    urls_to_parse = []

    # Обработка структуры данных в categories.json
    for item in json_data:
        if 'categories' in item:
            for category_name, category_data in item['categories'].items():
                if 'url' in category_data:
                    base_url = 'https://www.dns-shop.ru'
                    full_url = base_url + category_data['url'] + '&p={page}'
                    urls_to_parse.append(full_url)

    return urls_to_parse


def main(product_callback=None, limit_per_category=5, category_name=None):
    """
    Parse product links and optionally process each product immediately.
    
    Args:
        product_callback: Function that takes (driver, url) to process each product
        limit_per_category: Number of products to parse from each category
        category_name: Имя категории для парсинга (например, 'videokarty')
    
    Returns:
        List of parsed product URLs
    """
    # Создаем резервную копию файла категорий
    backup_categories_file()
    
    # Фильтруем категории в соответствии с запросом
    filter_categories_by_name(category_name)
    
    # Получаем случайный User-Agent
    random_ua = get_random_user_agent()
    print(f"Using random User-Agent: {random_ua}")
    
    # Настройка Chrome для Docker окружения и обхода антибот-защиты
    options = Options()
    # options.add_argument('--headless')  # Временно отключаем headless режим
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--disable-ipc-flooding-protection')
    options.add_argument('--window-size=1920,1080')
    
    # Дополнительные опции для обхода антибот-защиты
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument(f'--user-agent={random_ua}')  # Используем случайный User-Agent
    # Убираем проблемные experimental options для совместимости
    # options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-logging')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-sync')
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    options.add_argument('--disable-plugins-discovery')
    options.add_argument('--disable-component-extensions-with-background-pages')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-client-side-phishing-detection')
    options.add_argument('--disable-hang-monitor')
    options.add_argument('--disable-prompt-on-repost')
    options.add_argument('--disable-domain-reliability')
    options.add_argument('--disable-component-update')
    options.add_argument('--disable-background-downloads')
    options.add_argument('--disable-add-to-shelf')
    options.add_argument('--disable-datasaver-prompt')
    options.add_argument('--disable-desktop-notifications')
    options.add_argument('--disable-features=TranslateUI,BlinkGenPropertyTrees')
    
    # Для Docker окружения без дисплея
    options.add_argument('--virtual-time-budget=5000')
    options.add_argument('--run-all-compositor-stages-before-draw')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-features=TranslateUI,BlinkGenPropertyTrees,VizDisplayCompositor')
    
    # Дополнительные опции для обхода детекции
    options.add_argument('--disable-automation')
    options.add_argument('--disable-useAutomationExtension')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-extensions-file-access-check')
    options.add_argument('--disable-extensions-http-throttling')
    options.add_argument('--aggressive-cache-discard')
    
    # Попробуем найти Chrome бинарный файл
    chrome_binary_paths = [
        '/usr/bin/google-chrome-stable',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium'
    ]
    
    chrome_binary = None
    for path in chrome_binary_paths:
        if os.path.exists(path):
            chrome_binary = path
            break
    
    if chrome_binary:
        print(f"Using Chrome binary: {chrome_binary}")
    else:
        print("Chrome binary not found, trying without explicit path")
    
    # Настройка виртуального дисплея для Docker
    try:
        import subprocess
        subprocess.run(['Xvfb', ':99', '-screen', '0', '1920x1080x24'], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        os.environ['DISPLAY'] = ':99'
        print("Virtual display started")
    except:
        print("Could not start virtual display, continuing without it")
        # Если не удалось запустить виртуальный дисплей, включаем headless
        options.add_argument('--headless')
    
    try:
        # Получаем путь к совместимому ChromeDriver через webdriver-manager
        print("Getting compatible ChromeDriver with webdriver-manager...")
        chromedriver_path = ChromeDriverManager().install()
        print(f"ChromeDriver path: {chromedriver_path}")
        
        # Используем undetected-chromedriver для обхода антибот-защиты
        print("Initializing undetected Chrome driver...")
        driver = uc.Chrome(
            options=options,
            driver_executable_path=chromedriver_path,
            browser_executable_path=chrome_binary if chrome_binary else None,
            version_main=None,  # Автоматическое определение версии
            use_subprocess=True  # Использовать subprocess для лучшей стабильности
        )
        
        # Дополнительные настройки для обхода детекции (без CDP команд которые могут вызывать ошибки)
        try:
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            driver.execute_script("Object.defineProperty(navigator, 'platform', {get: () => 'Linux x86_64'})")
            print("Additional anti-detection scripts applied")
        except Exception as e:
            print(f"Warning: Could not apply anti-detection scripts: {e}")
        
        print("Undetected Chrome driver initialized successfully")
    except Exception as e:
        print(f"Error initializing Chrome driver: {e}")
        return []

    try:
        # Parse the JSON data from the provided document
        with open('categories.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Generate URLs
        urls_to_parse = generate_urls_from_json(data)

        # Print the generated URLs
        print("URLs to parse:")
        for url in urls_to_parse:
            print(url)

        # Set to store all unique product URLs
        all_product_urls = set()

        for index, url in enumerate(urls_to_parse):
            print(f'Getting all links from category {index + 1}:')
            parsed_urls = get_all_category_page_urls(driver, url, limit=limit_per_category, callback=product_callback)
            all_product_urls.update(parsed_urls)

        print(f"Total unique product URLs collected: {len(all_product_urls)}")
        
        # Сохраняем все собранные URL-адреса в файл
        all_urls_list = list(all_product_urls)
        save_urls_to_file(all_urls_list)
            
        return all_urls_list
    
    finally:
        driver.quit()
        print('Link parsing and processing complete!')


if __name__ == '__main__':
    # Если скрипт запускается напрямую, можно передать категорию через аргументы командной строки
    category = None
    if len(sys.argv) > 1:
        category = sys.argv[1]
    main(category_name=category)