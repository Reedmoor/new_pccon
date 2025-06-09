import json
import os
import sys
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from random import randint
from time import sleep as pause
import shutil


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
    """ Collects all product links on the current page. """
    soup = BeautifulSoup(driver.page_source, 'lxml')
    elements = soup.find_all('a', class_="catalog-product__name ui-link ui-link_black")
    return list(map(
        lambda element: 'https://www.dns-shop.ru' + element.get("href"),
        elements
    ))


def get_all_category_page_urls(driver, url_to_parse, limit=None, callback=None):
    """ Get category URL and parse links from it with a limit. 
    If callback is provided, it will be called with each URL one by one. """
    page = 1
    urls = set()  # Using a set to avoid duplicates
    parsed_count = 0

    while len(urls) < limit if limit else True:
        url = url_to_parse.format(page=page)
        driver.get(url)
        pause(randint(2, 4))

        soup = BeautifulSoup(driver.page_source, 'lxml')

        # Get links from current page
        page_urls = get_urls_from_page(driver)

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
            break

        page += 1

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
    
    driver = uc.Chrome()
    

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