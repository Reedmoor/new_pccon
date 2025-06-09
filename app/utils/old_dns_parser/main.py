try:
    # When imported as a module
    from . import productDetailsParser, linksParser
except ImportError:
    # When run as a script
    import productDetailsParser, linksParser
import sys

def main(category_name=None, limit_per_category=5):
    """
    Основная функция для запуска парсера DNS.
    
    Args:
        category_name: Название категории для парсинга (из выпадающего списка scrape.html)
        limit_per_category: Количество товаров для парсинга в каждой категории
    """
    # Сначала парсим ссылки на товары с использованием переданной категории
    product_urls = linksParser.main(
        product_callback=None,  # Не обрабатываем товары сразу
        limit_per_category=limit_per_category,
        category_name=category_name
    )
    
    # Затем парсим детали товаров
    productDetailsParser.main()
    
    return product_urls

if __name__ == '__main__':
    # Поддержка передачи категории через аргументы командной строки
    category = None
    if len(sys.argv) > 1:
        category = sys.argv[1]
        
    # Поддержка передачи лимита через аргументы командной строки
    limit = 5
    if len(sys.argv) > 2:
        try:
            limit = int(sys.argv[2])
        except ValueError:
            pass
            
    main(category_name=category, limit_per_category=limit)