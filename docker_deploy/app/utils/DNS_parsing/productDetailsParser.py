import os
import sys
import json
import scrapy
import time
import logging

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from random import randint
from time import sleep as pause
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from tqdm import tqdm
try:
    from .reviewParser import parse_reviews
except ImportError:
    from reviewParser import parse_reviews
from datetime import datetime

# Получаем абсолютный путь к корневой директории проекта
project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
# Устанавливаем путь к лог-файлу
log_file_path = os.path.join(project_root, 'dns_parser.log')

# Настроим логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('dns_parser')

TEST_URL = "https://www.dns-shop.ru/product/a67afeaff7bbd9cb/robot-pylesos-dreame-x40-ultra-complete-belyj/"

def save_product_data(data, filename="product_data.json"):
    """
    Save or update product data in a JSON file.
    
    If the URL already exists in the file, update the data.
    Otherwise, append the new data.
    """
    try:
        # Check if the file exists
        if not os.path.exists(filename):
            # Create a new file with just this item
            with open(filename, "w", encoding="utf-8") as f:
                json.dump([data], f, ensure_ascii=False, indent=4)
            logger.info(f"Created new file {filename} with first product data")
            return
            
        # Read the existing data
        with open(filename, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                # If file exists but is not valid JSON, create it new
                existing_data = []
                
        # Check if the product already exists in the data
        found = False
        for i, item in enumerate(existing_data):
            if item.get('url') == data.get('url'):
                # Update the existing item with new data
                existing_data[i] = data
                found = True
                logger.info(f"Updated existing product data for {data.get('url')}")
                break
                
        # If product not found, append it
        if not found:
            existing_data.append(data)
            logger.info(f"Added new product data for {data.get('url')}")
            
        # Write back the updated data
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
            
    except Exception as e:
        logger.error(f"Error saving product data to JSON: {e}")
        import traceback
        traceback.print_exc()

def clean_price(price_str):
    if not price_str:
        return None

    # Remove non-digit characters
    cleaned_price = ''.join(char for char in price_str if char.isdigit())

    try:
        return int(cleaned_price)
    except ValueError:
        return None

def parse_breadcrumbs(driver):
    soup = BeautifulSoup(driver.page_source, 'lxml')

    # Find the breadcrumb list
    breadcrumb_list = soup.find('ol', class_='breadcrumb-list')

    # If no breadcrumb list found, return empty list
    if not breadcrumb_list:
        return []

    # Parse categories
    categories = []
    for item in breadcrumb_list.find_all('li', class_='breadcrumb-list__item'):
        # Skip the last item (current page)
        if 'breadcrumb_last' in item.get('class', []):
            continue

        # Find the link
        link = item.find('a', class_='ui-link')
        if link:
            categories.append({
                'url': f"https://www.dns-shop.ru{link.get('href', '')}",
                'name': link.find('span').text.strip()
            })

    if len(categories) > 2:
        categories = categories[1:-1]

    return categories


def parse_characteristics(driver):
    try:
        # Сначала прокручиваем страницу вниз, чтобы элемент загрузился
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
        time.sleep(2)  # Даем время для загрузки элементов

        characteristics_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'product-card__characteristics'))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", characteristics_element)
        time.sleep(1)  # Даем время для полной загрузки после прокрутки

        # Нажимаем на кнопку "Развернуть все"
        try:
            expand_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'product-characteristics__expand'))
            )
            expand_button.click()
            time.sleep(2)  # Даем время для обновления характеристик
        except Exception as e:
            logger.warning(f"Не удалось нажать на кнопку 'Развернуть все': {e}")
    except Exception as e:
        logger.warning(f"Не удалось найти или прокрутить до характеристик: {e}")
        return {}

    soup = BeautifulSoup(driver.page_source, 'lxml')
    characteristics = {}

    # Находим основной контейнер с характеристиками
    content = soup.find('div', class_='product-characteristics-content')
    if not content:
        logger.warning("Контейнер с характеристиками не найден в HTML")
        return characteristics

    # Проходим по всем группам характеристик, включая скрытые (с классом __ovh)
    all_groups = content.find_all('div', class_=lambda c: c and ('product-characteristics__group' in c))
    for group in all_groups:
        group_title = group.find('div', class_='product-characteristics__group-title')
        if group_title:
            group_name = group_title.text.strip()
            characteristics[group_name] = []

            # Проходим по всем характеристикам в группе
            items = group.find_all('li', class_='product-characteristics__spec')
            for item in items:
                title_element = item.find('span', class_='product-characteristics__spec-title-content')
                value_element = item.find('div', class_='product-characteristics__spec-value')

                if title_element and value_element:
                    title = title_element.text.strip()
                    value = value_element.text.strip()

                    # Удаляем лишние пробелы и переносы строк
                    title = ' '.join(title.split())
                    value = ' '.join(value.split())

                    characteristics[group_name].append({
                        "title": title,
                        "value": value
                    })

    return characteristics

def extract_images(driver, max_images=5):
    """Extract images using Selenium"""
    images = []

    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # Сначала найдем и кликнем на миниатюру
    try:
        thumbnail = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'product-images-slider__img.tns-complete'))
        )
        thumbnail.click()

        # Ждем появления просмотрщика изображений
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'media-viewer-image__main'))
        )
    except Exception as e:
        logger.warning(f"Error clicking thumbnail: {e}")
        return []

    while len(images) < max_images:  # Ограничиваем количество фотографий
        # Get current page source and parse it
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Проверяем наличие контейнера с классом media-viewer-image__main_with-desc
        if soup.find('div', class_='media-viewer-image__main.media-viewer-image__main_with-desc'):
            logger.debug("Found container with description, stopping parsing")
            break

        # Find the main media viewer container
        media_viewer = soup.find('div', class_='media-viewer-image__main')

        if not media_viewer:
            break

        # Find the main image
        main_img = media_viewer.find('img', class_='media-viewer-image__main-img')

        if main_img and 'src' in main_img.attrs:
            images.append(main_img['src'])
            logger.debug(f"Found image {len(images)}/{max_images}")

        if len(images) >= max_images:
            break

        try:
            right_control = driver.find_element(By.CSS_SELECTOR,
                                                'div.media-viewer-image__main > div.media-viewer-image__control_right')
            right_control.click()
            time.sleep(0.5)

        except Exception as e:
            logger.warning(f"Error clicking or finding next button: {e}")
            break

    return list(dict.fromkeys(images))


def parse_product_data(driver):
    """Extract rating and review_count"""
    soup = BeautifulSoup(driver.page_source, 'lxml')

    # Находим JSON-LD скрипт
    script = soup.find('script', type='application/ld+json')
    if script:
        try:
            data = json.loads(script.string)

            rating = data.get('aggregateRating', {}).get('ratingValue')
            review_count = data.get('aggregateRating', {}).get('reviewCount')

            return {
                "rating": float(rating) if rating else None,
                "number_of_reviews": int(review_count) if review_count else None
            }
        except json.JSONDecodeError:
            logger.warning("Ошибка при парсинге JSON-LD")

    return {
        "rating": None,
        "number_of_reviews": None
    }

def parse_characteristics_page(driver, url):
    """Parse product page details."""
    driver.get(url)
    pause(randint(2, 3))

    soup = BeautifulSoup(driver.page_source, 'lxml')
    selector = scrapy.Selector(text=driver.page_source)

    def safe_text(soup, tag, class_=None, attribute=None):
        """Safely extract text from a tag."""
        element = soup.find(tag, class_=class_)
        if not element:
            return None
        if attribute:
            return element.get(attribute)
        return element.text.strip()

    def safe_list(soup, tag, class_=None, attribute=None):
        """Safely extract a list of texts or attributes from multiple tags."""
        elements = soup.find_all(tag, class_=class_)
        if not elements:
            return []
        if attribute:
            return [el.get(attribute) for el in elements if el.get(attribute)]
        return [el.text.strip() for el in elements]
        
    def logo():
        """Extract brand name from JSON-LD data."""
        json_ld_scripts = selector.xpath(
            "//script[@type='application/ld+json' and contains(text(), 'Product')]/text()").getall()
        brand_name = None
        for script_text in json_ld_scripts:
            try:
                json_data = json.loads(script_text)
                if 'brand' in json_data and isinstance(json_data['brand'], dict):
                    brand_name = json_data['brand'].get('name')
                    break
            except json.JSONDecodeError:
                continue
        return brand_name

    # Extract functions
    categories = parse_breadcrumbs(driver)
    characteristics = parse_characteristics(driver)
    images = extract_images(driver)
    product_data = parse_product_data(driver)

    # Extract product details
    item = {
        "id": selector.xpath("//div[@class='product-card-top__code']/text()").get(),
        "url": url,
        "categories": categories,
        "images": images,
        "name": safe_text(soup, 'div', class_="product-card-top__name"),
        "price_discounted": clean_price(selector.xpath("//div[contains(@class, 'product-buy__price_active')]/text()").get()) or 0,
        "price_original": clean_price(selector.xpath("//span[@class='product-buy__prev']/text()").get()) or
                          clean_price(selector.xpath("//div[@class='product-buy__price']/text()").get()),
        "rating": product_data['rating'],
        "number_of_reviews": product_data['number_of_reviews'],
        "brand_name": logo(),
        "description": safe_text(soup, 'div', class_="product-card-description-text"),
        "characteristics": characteristics,
        "drivers": safe_list(soup, 'a', class_="product-card-description-drivers__item-link", attribute='href'),
        "last_updated": datetime.now().isoformat()
    }

    logger.info(f"Parsed product: {item['name']}")
    return item


def process_single_url(driver, url):
    """Process a single product URL and save the data."""
    logger.info(f"Processing URL: {url}")
    try:
        product_data = parse_characteristics_page(driver, url)
        if product_data:
            # Save to a single JSON file
            save_product_data(product_data)
            logger.info(f"Saved data for product: {product_data.get('name')}")
        else:
            logger.warning(f"Failed to parse product data for {url}")
    except Exception as e:
        logger.error(f"Error processing URL {url}: {e}")
        import traceback
        traceback.print_exc()


def main():
    """
    Main function to parse product details.
    It can be called in two ways:
    1. After linksParser to process all collected URLs
    2. Standalone to process URLs from a file
    """
    try:
        # Проверяем, существует ли файл с результатами, если нет - создаем пустой
        if not os.path.exists('product_data.json'):
            with open('product_data.json', 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)
            logger.info("Создан пустой файл product_data.json")
        
        driver = uc.Chrome(version_main=135)

        # Check if urls.txt exists and process from it
        if os.path.exists('urls.txt'):
            logger.info("Reading URLs from urls.txt")
            with open('urls.txt', 'r') as file:
                urls = [line.strip() for line in file if line.strip()]
                
            total_urls = len(urls)
            logger.info(f"Found {total_urls} URLs to process")
            
            for i, url in enumerate(urls, 1):
                logger.info(f"Processing URL {i}/{total_urls}: {url}")
                process_single_url(driver, url)
                
        else:
            logger.warning("urls.txt not found. No URLs to process.")
            
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            driver.quit()
        except:
            pass
        logger.info("Product details parsing complete!")

if __name__ == '__main__':
    main()