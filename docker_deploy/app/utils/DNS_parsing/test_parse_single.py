#!/usr/bin/env python3
"""
Простой тест парсинга одного товара DNS для проверки работы в Docker
"""

import os
import sys
import json
import logging
from productDetailsParser import parse_characteristics_page

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('dns_test')

def test_single_product():
    """Тестирование парсинга одного товара"""
    
    # Тестовый URL товара DNS
    test_url = "https://www.dns-shop.ru/product/414e9c60e254ed20/materinskaa-plata-msi-b650-gaming-plus-wifi/"
    
    logger.info(f"Testing product parsing for: {test_url}")
    
    try:
        # Импортируем и инициализируем драйвер из productDetailsParser
        from productDetailsParser import main as init_driver_and_parse
        
        # Создаем временный файл urls.txt только с одним URL
        with open('test_urls.txt', 'w') as f:
            f.write(test_url + '\n')
        
        # Переименовываем файл для использования парсером
        if os.path.exists('urls.txt'):
            os.rename('urls.txt', 'urls_backup.txt')
        os.rename('test_urls.txt', 'urls.txt')
        
        # Запускаем парсинг
        init_driver_and_parse()
        
        # Восстанавливаем исходный файл
        os.rename('urls.txt', 'test_urls.txt')
        if os.path.exists('urls_backup.txt'):
            os.rename('urls_backup.txt', 'urls.txt')
        
        # Проверяем результат
        if os.path.exists('product_data.json'):
            with open('product_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Парсинг завершен. Получено {len(data)} товаров")
                
                if data:
                    product = data[-1]  # Последний товар
                    logger.info(f"Товар: {product.get('name', 'Без названия')}")
                    logger.info(f"Цена: {product.get('price_discounted', 'Не указана')}")
                    logger.info(f"Категории: {len(product.get('categories', []))}")
                    logger.info(f"Характеристики: {len(product.get('characteristics', {}))}")
                    
                    return True
        else:
            logger.error("Файл результатов не создан")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return False

if __name__ == '__main__':
    logger.info("=== Тест парсинга одного товара DNS ===")
    success = test_single_product()
    
    if success:
        logger.info("✅ Тест ПРОШЕЛ успешно!")
        sys.exit(0)
    else:
        logger.error("❌ Тест ПРОВАЛЕН!")
        sys.exit(1) 