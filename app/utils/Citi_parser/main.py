import time
import logging
import os
import json
import signal
import sys
from lxml import html
from dotenv import load_dotenv
from datetime import datetime
from request_handler import request, ParserStoppedException, check_stop_flag, test_all_proxies, enable_proxy, disable_proxy, use_proxy
from queries import (url, PRODUCTS_QUERY, PRODUCT_VARIABLE)
from data_processors import product_answer

load_dotenv()

# Глобальная переменная для отслеживания остановки
_parser_stopped = False

def signal_handler(signum, frame):
    """Обработчик сигналов для главного процесса"""
    global _parser_stopped
    _parser_stopped = True
    logging.info("🛑 ПОЛУЧЕН СИГНАЛ ОСТАНОВКИ В ГЛАВНОМ ПРОЦЕССЕ!")
    # Создаем файл-флаг для дочерних процессов
    with open('STOP_PARSER.flag', 'w') as f:
        f.write('STOP')

# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Текущая категория для обработки
category = os.getenv('CATEGORY')
max_products_env = os.getenv('MAX_PRODUCTS', '').strip()
try:
    max_products_limit = int(max_products_env) if max_products_env else 0
except ValueError:
    max_products_limit = 0

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

def load_existing_products(products_file):
    try:
        if os.path.exists(products_file):
            with open(products_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                return data
    except Exception as e:
        logging.warning(f"Не удалось прочитать предыдущие товары {products_file}: {e}")
    return []

# Функция для обработки одной категории
def fetch_products_for_category(category_name):
    global _parser_stopped
    logging.info(f"Начало парсинга категории: {category_name}")
    if max_products_limit > 0:
        logging.info(f"Лимит товаров: {max_products_limit}")
    else:
        logging.info("Лимит товаров не задан (без ограничения)")

    # Создаем директорию для всех Citilink данных
    ensure_directory_exists('data')
    data_dir = os.path.join('data', 'citilink')
    ensure_directory_exists(data_dir)
    
    # Единый файл для всех товаров
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    products_file = os.path.join(data_dir, f'citilink_{timestamp}.json')
    previous_products = []
    
    # Счетчик для отслеживания первых элементов
    first_product = True

    current_page_products = 1
    has_next_page_products = True
    
    # Список для хранения всех товаров данной категории
    all_products = []

    try:
        while has_next_page_products and not _parser_stopped:
            # Проверяем флаг остановки перед каждой страницей
            check_stop_flag()
            
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
                        # Проверяем флаг остановки перед каждым продуктом
                        check_stop_flag()
                        if _parser_stopped:
                            raise ParserStoppedException("Получен сигнал остановки")
                        
                        # Сохраняем продукт в файл категории и получаем нормализованный объект продукта.
                        first_product, parsed_product = product_answer(
                            product,
                            first_product,
                            products_file,
                            fetch_detailed_data=not _parser_stopped,
                            return_product=True
                        )
                        
                        # Сохраняем именно разобранный продукт (url/categories/properties), а не сырой GraphQL-объект.
                        all_products.append(parsed_product)
                        if max_products_limit > 0 and len(all_products) >= max_products_limit:
                            logging.info(f"Достигнут лимит товаров ({max_products_limit}), останавливаем парсинг")
                            has_next_page_products = False
                            break
                        
                        # Закомментированы дополнительные запросы для ускорения парсинга
                        # first_rating = rating_answer(product['id'], first_rating, reviews_file)
                        # first_review = review_answer(product['id'], first_review, articles_file)
                        
                        logging.info(f"Продукт {int(product['id'])} успешно обработан")
                        
                        # Уменьшили задержку для ускорения парсинга
                        if not _parser_stopped:
                            time.sleep(1)
                    except ParserStoppedException:
                        raise  # Пробрасываем исключение остановки
                    except Exception as product_error:
                        logging.error(f"Ошибка при обработке продукта: {str(product_error)}")
                        logging.error(f"Структура продукта: {product}")
                        continue
            except ParserStoppedException:
                raise  # Пробрасываем исключение остановки
            except Exception as page_error:
                logging.error(f"Ошибка при обработке страницы {current_page_products}: {str(page_error)}")
                break
                
            current_page_products += 1
            
            # Ограничение на количество страниц для тестирования
            if current_page_products > 10 and max_products_limit <= 0:
                logging.warning("Достигнуто ограничение на количество страниц (10). Завершение парсинга.")
                break
                
    except ParserStoppedException:
        logging.info("🛑 ПАРСЕР ОСТАНОВЛЕН ПОЛЬЗОВАТЕЛЕМ!")
        logging.info(f"✅ На момент остановки обработано {len(all_products)} товаров")
        
        # Сохраняем собранные до остановки товары
        if all_products:
            try:
                with open(products_file, 'w', encoding='utf-8') as f:
                    json.dump(all_products, f, ensure_ascii=False, indent=2)
                logging.info(f"💾 Сохранено {len(all_products)} товаров до остановки в {products_file}")
            except Exception as e:
                logging.error(f"Ошибка при сохранении товаров: {e}")
        
        # Удаляем файл-флаг остановки
        try:
            if os.path.exists('STOP_PARSER.flag'):
                os.remove('STOP_PARSER.flag')
        except Exception as e:
            logging.error(f"Ошибка при удалении файла флага: {e}")
        
        return all_products
    
    # Сохраняем собранные товары
    if all_products:
        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Обработка категории {category_name} успешно завершена")
        logging.info(f"Данные сохранены в файл: {products_file}")
        logging.info(f"Общее количество товаров: {len(all_products)}")
    else:
        logging.warning(f"Не удалось получить товары для категории {category_name}")
    
    return all_products

# Основная функция
def main():
    global _parser_stopped
    
    if not category:
        logging.error("Ошибка: категория не указана в .env файле")
        return
    
    # Проверяем и тестируем прокси при запуске
    if use_proxy:
        logging.info("🔄 Прокси включены через переменную окружения USE_PROXY=true")
        test_all_proxies()
    else:
        logging.info("ℹ️  Прокси отключены. Для включения установите USE_PROXY=true в .env файле")
        logging.info("ℹ️  Или используйте команду: python -c \"from request_handler import enable_proxy; enable_proxy()\"")
    
    try:
        # Обрабатываем категорию
        products = fetch_products_for_category(category)
        if not products:
            logging.warning("Новые товары не получены")
            return 0
        
        logging.info(f"Успешно получено {len(products)} товаров из категории {category}")
        logging.info(f"Данные сохранены в формат: data/citilink/citilink_{{timestamp}}.json")
        
    except ParserStoppedException:
        logging.info("🏁 ПАРСИНГ ЗАВЕРШЕН ПО ТРЕБОВАНИЮ ПОЛЬЗОВАТЕЛЯ")
        # При остановке пользователем возвращаем код 0 (успешное завершение)
        return 0
    except Exception as e:
        logging.error(f"Критическая ошибка парсера: {e}")
        return 1
    finally:
        # Очищаем файл-флаг при выходе
        try:
            if os.path.exists('STOP_PARSER.flag'):
                os.remove('STOP_PARSER.flag')
        except:
            pass

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code if exit_code is not None else 0)