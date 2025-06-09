import time
import logging
import os
import json
from lxml import html
from dotenv import load_dotenv
from request_handler import request
from queries import (url, PRODUCTS_QUERY, PRODUCT_VARIABLE)
from data_processors import product_answer, rating_answer, review_answer

load_dotenv()

# Текущая категория для обработки
category = os.getenv('CATEGORY')

# В начале файла добавляем настройку логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parser.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Функция для создания директорий, если их нет
def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Создана директория: {directory}")

# Функция для обработки одной категории
def fetch_products_for_category(category_name):
    logging.info(f"Начало парсинга категории: {category_name}")

    # Создаем директорию для категории
    category_dir = os.path.join('data', category_name)
    ensure_directory_exists(category_dir)
    
    # Пути к файлам для данной категории
    products_file = os.path.join(category_dir, 'Товары.json')
    reviews_file = os.path.join(category_dir, 'Отзывы.json')
    articles_file = os.path.join(category_dir, 'Обзоры.json')
    
    # Также создадим копию в корневой директории для совместимости
    ensure_directory_exists('data')

    # Очищаем файлы перед записью
    for filename in [products_file, reviews_file, articles_file]:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('[\n')
    
    # Счетчики для отслеживания первых элементов
    first_product = True
    first_rating = True
    first_review = True

    current_page_products = 1
    has_next_page_products = True
    
    # Список для хранения всех товаров данной категории
    all_products = []

    while has_next_page_products:
        logging.info(f"Обработка страницы продукта №{current_page_products}")

        try:
            # Получаем данные из API
            product_request_data = request(url, PRODUCTS_QUERY, PRODUCT_VARIABLE(category_name, current_page_products), "всех продуктов")
            
            # Проверяем наличие необходимых полей в ответе
            if not product_request_data:
                logging.error(f"Получен пустой ответ от API для страницы {current_page_products}")
                break
                
            if 'data' not in product_request_data:
                logging.error(f"Поле 'data' отсутствует в ответе API для страницы {current_page_products}")
                logging.error(f"Получен ответ: {product_request_data}")
                break
                
            if 'productsFilter' not in product_request_data['data']:
                logging.error(f"Поле 'productsFilter' отсутствует в ответе API для страницы {current_page_products}")
                logging.error(f"Структура data: {product_request_data['data'].keys()}")
                break
                
            if 'record' not in product_request_data['data']['productsFilter']:
                logging.error(f"Поле 'record' отсутствует в productsFilter для страницы {current_page_products}")
                logging.error(f"Структура productsFilter: {product_request_data['data']['productsFilter'].keys()}")
                break
                
            record = product_request_data['data']['productsFilter']['record']
            
            if 'pageInfo' not in record:
                logging.error(f"Поле 'pageInfo' отсутствует в record для страницы {current_page_products}")
                logging.error(f"Структура record: {record.keys()}")
                break
                
            if 'hasNextPage' not in record['pageInfo']:
                logging.error(f"Поле 'hasNextPage' отсутствует в pageInfo для страницы {current_page_products}")
                logging.error(f"Структура pageInfo: {record['pageInfo'].keys()}")
                break
                
            # Проверка на наличие следующей страницы
            has_next_page_products = record['pageInfo']['hasNextPage']
            
            # Проверяем наличие продуктов в ответе
            if 'products' not in record:
                logging.error(f"Поле 'products' отсутствует в record для страницы {current_page_products}")
                logging.error(f"Структура record: {record.keys()}")
                break
                
            # Обрабатываем каждый продукт
            for product in record['products']:
                try:
                    # Сохраняем продукт в файл категории
                    first_product = product_answer(product, first_product, products_file)
                    
                    # Сохраняем продукт в списке для совместимости
                    all_products.append(product)
                    
                    # first_rating = rating_answer(product['id'], first_rating, reviews_file)
                    # first_review = review_answer(product['id'], first_review, articles_file)
                    
                    logging.info(f"Продукт {int(product['id'])} успешно обработан")
                    time.sleep(2)
                except Exception as product_error:
                    logging.error(f"Ошибка при обработке продукта: {str(product_error)}")
                    logging.error(f"Структура продукта: {product}")
                    continue
        except Exception as page_error:
            logging.error(f"Ошибка при обработке страницы {current_page_products}: {str(page_error)}")
            break
            
        current_page_products += 1
        
        # Ограничение на количество страниц для тестирования
        if current_page_products > 10:
            logging.warning("Достигнуто ограничение на количество страниц (10). Завершение парсинга.")
            break

    # Закрываем файлы категории
    for filename in [products_file, reviews_file, articles_file]:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write('\n]')
    
    # Сохраняем собранные товары
    if all_products:
        # Создаем объединенный файл для совместимости со старым кодом
        with open('Товары.json', 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Обработка категории {category_name} успешно завершена")
        logging.info(f"Данные сохранены в директории: {category_dir}")
        logging.info(f"Общее количество товаров: {len(all_products)}")
    else:
        logging.warning(f"Не удалось получить товары для категории {category_name}")
        # Создаем пустой файл
        with open('Товары.json', 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    
    return all_products

# Основная функция
def main():
    if not category:
        logging.error("Ошибка: категория не указана в .env файле")
        return
    
    # Обрабатываем категорию
    products = fetch_products_for_category(category)
    
    # Для обратной совместимости, сохраним общий файл в стандартном формате
    with open('Товары.json', 'w', encoding='utf-8') as f:
        f.write('[\n')
        for i, product in enumerate(products):
            json_str = json.dumps(product, ensure_ascii=False)
            if i < len(products) - 1:
                f.write(json_str + ',\n')
            else:
                f.write(json_str + '\n')
        f.write(']')
    
    logging.info(f"Также создан объединенный файл 'Товары.json' для совместимости")

if __name__ == "__main__":
    main()