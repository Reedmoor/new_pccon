from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required
from app.forms.comparison import ProductComparisonForm
from app.utils.product_comparator import ProductComparator, get_comparator
import logging
import os
import glob
from app.models.models import UnifiedProduct
import json

logger = logging.getLogger(__name__)

comparison_bp = Blueprint('comparison', __name__, url_prefix='/comparison')

@comparison_bp.route('/')
@login_required
def index():
    """Главная страница сравнения товаров"""
    form = ProductComparisonForm()
    return render_template('comparison/index.html', form=form)

@comparison_bp.route('/compare', methods=['POST'])
@login_required
def compare_products():
    """Сравнение товаров из JSON файлов"""
    try:
        form = ProductComparisonForm()
        
        if not form.validate_on_submit():
            flash('Ошибка валидации формы', 'error')
            return redirect(url_for('comparison.index'))
        
        category = form.category.data
        threshold = form.threshold.data
        
        # Функция для поиска последнего файла DNS данных
        def get_latest_dns_data_file():
            """Находит самый последний файл local_parser_data_*.json"""
            search_paths = [
                'data/local_parser_data_*.json',
                '/app/data/local_parser_data_*.json'
            ]
            
            latest_file = None
            latest_time = 0
            
            for pattern in search_paths:
                files = glob.glob(pattern)
                for file_path in files:
                    try:
                        file_time = os.path.getmtime(file_path)
                        if file_time > latest_time:
                            latest_time = file_time
                            latest_file = file_path
                    except OSError:
                        continue
            
            return latest_file

        # Функция для поиска последнего файла Citilink данных
        def get_latest_citilink_data_file():
            """Находит самый последний файл citilink_data_*.json или общий файл"""
            search_paths = [
                'data/citilink_data_*.json',
                '/app/data/citilink_data_*.json',
                'app/utils/Citi_parser/Товары.json',  # Общий файл в локальной разработке
                '/app/utils/Citi_parser/Товары.json'   # Общий файл в контейнере
            ]
            
            latest_file = None
            latest_time = 0
            
            for path_pattern in search_paths:
                if '*' in path_pattern:
                    # Это паттерн для glob
                    files = glob.glob(path_pattern)
                    for file_path in files:
                        try:
                            file_time = os.path.getmtime(file_path)
                            if file_time > latest_time:
                                latest_time = file_time
                                latest_file = file_path
                        except OSError:
                            continue
                else:
                    # Это конкретный путь
                    if os.path.exists(path_pattern):
                        try:
                            file_time = os.path.getmtime(path_pattern)
                            if file_time > latest_time:
                                latest_time = file_time
                                latest_file = path_pattern
                        except OSError:
                            continue
            
            return latest_file

        # Карта категорий для JSON файлов (с fallback для локальной разработки)
        latest_dns_file = get_latest_dns_data_file()
        latest_citilink_file = get_latest_citilink_data_file()
        logger.info(f"Последний файл DNS данных: {latest_dns_file}")
        logger.info(f"Последний файл Citilink данных: {latest_citilink_file}")
        
        category_mapping = {
            'ram': {
                'dns': ['/app/data/DNS_parsing/categories/product_data_Оперативная память DIMM.json',
                        '/app/utils/DNS_parsing/categories/product_data_Оперативная память DIMM.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['/app/data/Citi_parser/data/moduli-pamyati/Товары.json',
                         '/app/utils/Citi_parser/data/moduli-pamyati/Товары.json'] +
                        ([latest_citilink_file] if latest_citilink_file else []),
                'dns_label': 'Оперативная память DIMM',
                'citi_label': 'Модули памяти'
            },
            'gpu': {
                'dns': ['/app/data/DNS_parsing/categories/product_data_Видеокарты.json',
                        '/app/utils/DNS_parsing/categories/product_data_Видеокарты.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['/app/data/Citi_parser/data/videokarty/Товары.json',
                         '/app/utils/Citi_parser/data/videokarty/Товары.json'] +
                        ([latest_citilink_file] if latest_citilink_file else []),
                'dns_label': 'Видеокарты',
                'citi_label': 'Видеокарты'
            },
            'cpu': {
                'dns': ['/app/data/DNS_parsing/categories/product_data_Процессоры.json',
                        '/app/utils/DNS_parsing/categories/product_data_Процессоры.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['/app/utils/Citi_parser/data/processory/Товары.json',
                         'app/utils/Citi_parser/data/processory/Товары.json',
                         '/app/data/Citi_parser/data/processory/Товары.json'] +
                        ([latest_citilink_file] if latest_citilink_file else []),
                'dns_label': 'Процессоры',
                'citi_label': 'Процессоры'
            },
            'storage': {
                'dns': [
                    ['/app/data/DNS_parsing/categories/product_data_SSD накопители.json',
                     '/app/data/DNS_parsing/categories/product_data_SSD M_2 накопители.json',
                     '/app/data/DNS_parsing/categories/product_data_Жесткие диски 3_5_.json'],
                    ['/app/utils/DNS_parsing/categories/product_data_SSD накопители.json',
                     '/app/utils/DNS_parsing/categories/product_data_SSD M_2 накопители.json',
                     '/app/utils/DNS_parsing/categories/product_data_Жесткие диски 3_5_.json']
                ] + ([[latest_dns_file]] if latest_dns_file else []),
                'citi': [
                    ['/app/data/Citi_parser/data/ssd-nakopiteli/Товары.json',
                     '/app/data/Citi_parser/data/zhestkie-diski/Товары.json'],
                    ['/app/utils/Citi_parser/data/ssd-nakopiteli/Товары.json',
                     '/app/utils/Citi_parser/data/zhestkie-diski/Товары.json']
                ] + ([[latest_citilink_file]] if latest_citilink_file else []),
                'dns_label': 'Накопители (SSD, HDD)',
                'citi_label': 'Накопители (SSD, HDD)'
            },
            'motherboard': {
                'dns': ['/app/data/DNS_parsing/categories/product_data_Материнские платы.json',
                        '/app/utils/DNS_parsing/categories/product_data_Материнские платы.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['/app/data/Citi_parser/data/materinskie-platy/Товары.json',
                         '/app/utils/Citi_parser/data/materinskie-platy/Товары.json'] +
                        ([latest_citilink_file] if latest_citilink_file else []),
                'dns_label': 'Материнские платы',
                'citi_label': 'Материнские платы'
            },
            'psu': {
                'dns': ['/app/data/DNS_parsing/categories/product_data_Блоки питания.json',
                        '/app/utils/DNS_parsing/categories/product_data_Блоки питания.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['/app/data/Citi_parser/data/bloki-pitaniya/Товары.json',
                         '/app/utils/Citi_parser/data/bloki-pitaniya/Товары.json'] +
                        ([latest_citilink_file] if latest_citilink_file else []),
                'dns_label': 'Блоки питания',
                'citi_label': 'Блоки питания'
            },
            'cooler': {
                'dns': ['/app/data/DNS_parsing/categories/product_data_Кулеры для процессоров.json',
                        '/app/utils/DNS_parsing/categories/product_data_Кулеры для процессоров.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['/app/data/Citi_parser/data/sistemy-ohlazhdeniya-processora/Товары.json',
                         '/app/utils/Citi_parser/data/sistemy-ohlazhdeniya-processora/Товары.json'] +
                        ([latest_citilink_file] if latest_citilink_file else []),
                'dns_label': 'Кулеры для процессоров',
                'citi_label': 'Системы охлаждения процессора'
            },
            'case': {
                'dns': ['/app/data/DNS_parsing/categories/product_data_Корпуса.json',
                        '/app/utils/DNS_parsing/categories/product_data_Корпуса.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['/app/data/Citi_parser/data/korpusa/Товары.json',
                         '/app/utils/Citi_parser/data/korpusa/Товары.json'] +
                        ([latest_citilink_file] if latest_citilink_file else []),
                'dns_label': 'Корпуса',
                'citi_label': 'Корпуса'
            }
        }
        
        # Функция для фильтрации DNS данных по категории
        def filter_dns_by_category(data, category):
            """Фильтрует данные DNS по категории"""
            if not data:
                return []
            
            logger.info(f"Фильтрация DNS для категории {category}, исходных товаров: {len(data)}")
            
            category_filters = {
                'gpu': ['Видеокарты', 'videokarty'],
                'cpu': ['Процессоры', 'processory'],
                'ram': ['Оперативная память', 'moduli-pamyati'],
                'storage': ['SSD', 'ssd', 'Жесткие диски', 'zhestkie-diski', 'накопители'],
                'motherboard': ['Материнские платы', 'materinskie-platy'],
                'psu': ['Блоки питания', 'bloki-pitaniya'],
                'cooler': ['Кулеры', 'sistemy-ohlazhdeniya'],
                'case': ['Корпуса', 'korpusa']
            }
            
            if category not in category_filters:
                logger.warning(f"Категория {category} не найдена в DNS фильтрах")
                return data
            
            filters = category_filters[category]
            logger.info(f"Используемые DNS фильтры для {category}: {filters}")
            filtered_data = []
            
            for item in data:
                found_match = False
                
                # Проверяем категории товара
                if 'categories' in item and item['categories']:
                    for cat in item['categories']:
                        if cat and 'name' in cat and cat['name']:  # Проверяем что cat не None и name существует
                            cat_name = cat['name'].lower()
                            if any(f.lower() in cat_name for f in filters):
                                filtered_data.append(item)
                                found_match = True
                                break
                
                # Если нет категорий, фильтруем по названию товара
                if not found_match and 'name' in item and item['name']:
                    item_name = item['name'].lower()
                    if any(f.lower() in item_name for f in filters):
                        filtered_data.append(item)
            
            logger.info(f"После фильтрации DNS {category}: {len(filtered_data)} товаров из {len(data)}")
            
            # Покажем несколько примеров отфильтрованных товаров
            if filtered_data:
                sample_names = [item.get('name', 'Без названия') for item in filtered_data[:3]]
                logger.info(f"Примеры отфильтрованных DNS товаров: {sample_names}")
            
            return filtered_data
        
        # Функция для фильтрации Citilink данных по категории
        def filter_citilink_by_category(data, category):
            """Фильтрует данные Citilink по категории"""
            if not data:
                return []
            
            # Убираем неправильную логику с проверкой размера файла
            # Фильтруем всегда, если получили общий файл
            logger.info(f"Фильтрация Citilink для категории {category}, исходных товаров: {len(data)}")
            
            category_filters = {
                'gpu': ['видеокарт', 'videocard', 'graphics'],
                'cpu': ['процессор', 'processor', 'cpu'],
                'ram': ['память', 'memory', 'dimm', 'оперативн'],
                'storage': ['ssd', 'диск', 'накопител', 'disk', 'storage'],
                'motherboard': ['материнск', 'motherboard', 'мат. плат'],
                'psu': ['блок питания', 'power supply', 'psu'],
                'cooler': ['кулер', 'cooler', 'охлажден'],
                'case': ['корпус', 'case']
            }
            
            if category not in category_filters:
                logger.warning(f"Категория {category} не найдена в фильтрах")
                return data
            
            filters = category_filters[category]
            logger.info(f"Используемые фильтры для {category}: {filters}")
            filtered_data = []
            
            for item in data:
                item_name = ""
                if 'name' in item and item['name']:
                    item_name = item['name'].lower()
                elif 'title' in item and item['title']:
                    item_name = item['title'].lower()
                
                if item_name and any(f.lower() in item_name for f in filters):
                    filtered_data.append(item)
            
            logger.info(f"После фильтрации Citilink {category}: {len(filtered_data)} товаров из {len(data)}")
            
            # Покажем несколько примеров отфильтрованных товаров
            if filtered_data:
                sample_names = [item.get('name', item.get('title', 'Без названия')) for item in filtered_data[:3]]
                logger.info(f"Примеры отфильтрованных товаров: {sample_names}")
            
            return filtered_data
        
        # Функция для поиска существующего файла из списка путей
        def find_existing_file(paths):
            """Возвращает первый существующий файл из списка путей"""
            if isinstance(paths, str):
                logger.info(f"Проверяем путь: {paths}")
                exists = os.path.exists(paths)
                logger.info(f"Файл {'найден' if exists else 'не найден'}: {paths}")
                return paths if exists else None
            for path in paths:
                logger.info(f"Проверяем путь: {path}")
                exists = os.path.exists(path)
                logger.info(f"Файл {'найден' if exists else 'не найден'}: {path}")
                if exists:
                    return path
            return None
        
        # Функция для поиска существующих файлов для storage (список списков)
        def find_existing_files(paths_list):
            """Для storage - возвращает первый набор путей где все файлы существуют"""
            logger.info(f"find_existing_files вызвана с: {paths_list}")
            if not isinstance(paths_list[0], list):
                # Обычная категория, не storage
                logger.info("Обычная категория, используем find_existing_file")
                return find_existing_file(paths_list)
            
            logger.info("Storage категория, проверяем наборы путей")
            for i, path_set in enumerate(paths_list):
                logger.info(f"Проверяем набор {i}: {path_set}")
                all_exist = all(os.path.exists(path) for path in path_set)
                logger.info(f"Все файлы в наборе {i} {'найдены' if all_exist else 'не найдены'}")
                if all_exist:
                    return path_set
            return None
        
        # Проверяем существование категории
        if category not in category_mapping:
            flash(f'Категория "{category}" не поддерживается', 'error')
            return redirect(url_for('comparison.index'))
        
        cat_info = category_mapping[category]
        logger.info(f"Сравнение категории: {category}")
        logger.info(f"DNS пути: {cat_info['dns']}")
        logger.info(f"Citi пути: {cat_info['citi']}")
        
        # Создаем компаратор
        comparator = get_comparator()
        
        # Загружаем данные из JSON файлов (специальная обработка для storage)
        if category == 'storage':
            # Объединяем данные из нескольких файлов
            dns_data = []
            citi_data = []
            
            # Находим существующие DNS файлы
            dns_paths = find_existing_files(cat_info['dns'])
            if dns_paths:
                if len(dns_paths) == 1 and 'local_parser_data' in dns_paths[0]:
                    # Общий файл DNS - загружаем и фильтруем
                    logger.info("Загружаем общий файл DNS для storage")
                    dns_file = find_existing_file(dns_paths)
                    if dns_file:
                        with open(dns_file, 'r', encoding='utf-8') as f:
                            if 'local_parser_data_' in dns_file:
                                general_data = json.load(f)
                                dns_data = filter_dns_by_category(general_data, category)
                            else:
                                dns_data = json.load(f)
                    logger.info(f"После фильтрации storage: {len(dns_data)} товаров из {len(dns_data) if dns_data else 0}")
                else:
                    # Отдельные файлы по категориям
                    for dns_path in dns_paths:
                        dns_file = find_existing_file(dns_path)
                        if dns_file:
                            with open(dns_file, 'r', encoding='utf-8') as f:
                                if 'local_parser_data_' in dns_file:
                                    general_data = json.load(f)
                                    dns_data.extend(filter_dns_by_category(general_data, category))
                        else:
                                    dns_data.extend(json.load(f))
            
            # Находим существующие Citilink файлы  
            citi_paths = find_existing_files(cat_info['citi'])
            if citi_paths:
                for citi_path in citi_paths:
                    citi_file = find_existing_file(citi_path)
                    if citi_file:
                        with open(citi_file, 'r', encoding='utf-8') as f:
                            if 'citilink_data_' in citi_file or ('Товары.json' in citi_file and latest_citilink_file and latest_citilink_file == citi_file):
                                logger.info(f"Загружаем общий файл Citilink для {category}")
                                general_data = json.load(f)
                                citi_data.extend(filter_citilink_by_category(general_data, category))
                                logger.info(f"После фильтрации Citilink {category}: {len(citi_data)} товаров из {len(general_data)}")
                            else:
                                citi_data.extend(json.load(f))
        else:
            # Находим существующие файлы для обычных категорий
            dns_path = find_existing_file(cat_info['dns'])
            citi_path = find_existing_file(cat_info['citi'])
            
            # Проверяем существование файлов
            if not dns_path or not citi_path:
                flash(f'Файлы данных для категории "{category}" не найдены', 'error')
                return redirect(url_for('comparison.index'))
            
            # Загружаем данные
            dns_file = find_existing_file(cat_info['dns'])
            citi_file = find_existing_file(cat_info['citi'])
            
            dns_data = []
            citi_data = []
            
            if dns_file:
                with open(dns_file, 'r', encoding='utf-8') as f:
                    if 'local_parser_data_' in dns_file:
                        general_data = json.load(f)
                        dns_data = filter_dns_by_category(general_data, category)
                    else:
                        dns_data = json.load(f)
            
            if citi_file:
                with open(citi_file, 'r', encoding='utf-8') as f:
                    if 'citilink_data_' in citi_file or ('Товары.json' in citi_file and latest_citilink_file and latest_citilink_file == citi_file):
                        logger.info(f"Загружаем общий файл Citilink для {category}")
                        general_data = json.load(f)
                        citi_data = filter_citilink_by_category(general_data, category)
                        logger.info(f"После фильтрации Citilink {category}: {len(citi_data)} товаров из {len(general_data)}")
                    else:
                        citi_data = json.load(f)
        
        if not dns_data or not citi_data:
            flash(f'Недостаточно данных для сравнения категории "{cat_info["dns_label"]}". DNS: {len(dns_data) if dns_data else 0}, Citilink: {len(citi_data) if citi_data else 0}', 'error')
            return redirect(url_for('comparison.index'))
        
        # Извлекаем названия товаров
        dns_names = comparator.extract_names(dns_data, "name")
        citi_names = comparator.extract_names(citi_data, "name")
        
        # Ищем совпадения с использованием гибридного алгоритма
        matches = comparator.find_best_matches(
            dns_names, citi_names, 
            threshold=threshold,
            use_enhanced=True
        )
        
        # Создаем детальные результаты с ценами
        detailed_matches = []
        total_dns_cheaper = 0
        total_citi_cheaper = 0
        price_differences = []
        
        for dns_name, citi_name, similarity in matches:
            # Находим соответствующие товары в данных JSON
            dns_item = next((item for item in dns_data if item["name"] == dns_name), None)
            citi_item = next((item for item in citi_data if item["name"] == citi_name), None)
            
            if dns_item and citi_item:
                # Извлекаем цены
                dns_price = comparator._extract_price(dns_item)
                citi_price = comparator._extract_price(citi_item)
                
                match_data = {
                    'dns_name': dns_name,
                    'citi_name': citi_name,
                    'similarity': similarity,
                    'dns_price': dns_price,
                    'citi_price': citi_price,
                    'dns_url': dns_item.get('url', '#'),
                    'citi_url': citi_item.get('url', '#'),
                    'dns_brand': dns_item.get('brand_name', ''),
                    'citi_brand': citi_item.get('brand', '')
                }
                
                # Рассчитываем разность цен
                if dns_price and citi_price:
                    difference = citi_price - dns_price  # Положительное значение означает, что DNS дешевле
                    price_differences.append(difference)
                    
                    if difference > 0:
                        total_dns_cheaper += 1
                        match_data['cheaper_store'] = 'dns'
                    elif difference < 0:
                        total_citi_cheaper += 1
                        match_data['cheaper_store'] = 'citi'
                    else:
                        match_data['cheaper_store'] = 'equal'
                    
                    match_data['price_difference'] = difference
                else:
                    match_data['cheaper_store'] = 'unknown'
                    match_data['price_difference'] = None
                
                detailed_matches.append(match_data)
        
        # Рассчитываем статистику цен
        price_stats = {}
        if price_differences:
            price_stats = {
                'count': len(price_differences),
                'average_difference': sum(price_differences) / len(price_differences),
                'min_difference': min(price_differences),
                'max_difference': max(price_differences),
                'dns_cheaper_count': total_dns_cheaper,
                'citi_cheaper_count': total_citi_cheaper,
                'equal_price_count': len([d for d in price_differences if d == 0])
            }
        
        # Формируем результат
        result = {
            'dns_category': cat_info['dns_label'],
            'citi_category': cat_info['citi_label'],
            'dns_count': len(dns_data),
            'citi_count': len(citi_data),
            'matches_count': len(detailed_matches),
            'matches': detailed_matches,
            'threshold': threshold,
            'price_statistics': price_stats
        }
        
        return render_template('comparison/results.html',
                             category=category,
                             threshold=threshold,
                             result=result,
                             is_quick_compare=False)
    
    except Exception as e:
        logger.error(f"Ошибка при сравнении товаров: {str(e)}")
        flash(f'Произошла ошибка при сравнении: {str(e)}', 'error')
        return redirect(url_for('comparison.index'))

@comparison_bp.route('/api/categories')
def get_categories():
    """API для получения доступных категорий"""
    try:
        # Упрощенный список категорий - возвращаем все, которые есть в маппинге
        categories = [
            {'value': 'ram', 'label': 'Оперативная память'},
            {'value': 'gpu', 'label': 'Видеокарты'},
            {'value': 'cpu', 'label': 'Процессоры'},
            {'value': 'storage', 'label': 'Накопители (SSD, HDD)'},
            {'value': 'motherboard', 'label': 'Материнские платы'},
            {'value': 'psu', 'label': 'Блоки питания'},
            {'value': 'cooler', 'label': 'Кулеры для процессоров'},
            {'value': 'case', 'label': 'Корпуса'}
        ]
        
        return jsonify(categories)
    except Exception as e:
        logger.error(f"Ошибка получения категорий: {str(e)}")
        return jsonify({'error': str(e)}), 500

@comparison_bp.route('/quick-compare/<category>')
@login_required
def quick_compare(category):
    """Быстрое сравнение с предустановленными параметрами"""
    try:
        # Функции для поиска последних файлов (копия из основной функции)
        def get_latest_dns_data_file():
            """Находит самый последний файл local_parser_data_*.json"""
            search_paths = [
                'data/local_parser_data_*.json',
                '/app/data/local_parser_data_*.json'
            ]
            
            latest_file = None
            latest_time = 0
            
            for pattern in search_paths:
                files = glob.glob(pattern)
                for file_path in files:
                    try:
                        file_time = os.path.getmtime(file_path)
                        if file_time > latest_time:
                            latest_time = file_time
                            latest_file = file_path
                    except OSError:
                        continue
            
            return latest_file

        def get_latest_citilink_data_file():
            """Находит самый последний файл citilink_data_*.json или общий файл"""
            search_paths = [
                'data/citilink_data_*.json',
                '/app/data/citilink_data_*.json',
                'app/utils/Citi_parser/Товары.json',
                '/app/utils/Citi_parser/Товары.json'
            ]
            
            latest_file = None
            latest_time = 0
            
            for path_pattern in search_paths:
                if '*' in path_pattern:
                    files = glob.glob(path_pattern)
                    for file_path in files:
                        try:
                            file_time = os.path.getmtime(file_path)
                            if file_time > latest_time:
                                latest_time = file_time
                                latest_file = file_path
                        except OSError:
                            continue
                else:
                    if os.path.exists(path_pattern):
                        try:
                            file_time = os.path.getmtime(path_pattern)
                            if file_time > latest_time:
                                latest_time = file_time
                                latest_file = path_pattern
                        except OSError:
                            continue
            
            return latest_file

        # Получаем последние файлы
        latest_dns_file = get_latest_dns_data_file()
        latest_citilink_file = get_latest_citilink_data_file()
        
        # Функции фильтрации (копии из основной функции)
        def filter_dns_by_category(data, category):
            """Фильтрует данные DNS по категории"""
            if not data:
                return []
            
            logger.info(f"Фильтрация DNS для категории {category}, исходных товаров: {len(data)}")
            
            category_filters = {
                'gpu': ['Видеокарты', 'videokarty'],
                'cpu': ['Процессоры', 'processory'],
                'ram': ['Оперативная память', 'moduli-pamyati'],
                'storage': ['SSD', 'ssd', 'Жесткие диски', 'zhestkie-diski', 'накопители'],
                'motherboard': ['Материнские платы', 'materinskie-platy'],
                'psu': ['Блоки питания', 'bloki-pitaniya'],
                'cooler': ['Кулеры', 'sistemy-ohlazhdeniya'],
                'case': ['Корпуса', 'korpusa']
            }
            
            if category not in category_filters:
                logger.warning(f"Категория {category} не найдена в DNS фильтрах")
                return data
            
            filters = category_filters[category]
            logger.info(f"Используемые DNS фильтры для {category}: {filters}")
            filtered_data = []
            
            for item in data:
                found_match = False
                
                # Проверяем категории товара
                if 'categories' in item and item['categories']:
                    for cat in item['categories']:
                        if cat and 'name' in cat and cat['name']:  # Проверяем что cat не None и name существует
                            cat_name = cat['name'].lower()
                            if any(f.lower() in cat_name for f in filters):
                                filtered_data.append(item)
                                found_match = True
                                break
                
                # Если нет категорий, фильтруем по названию товара
                if not found_match and 'name' in item and item['name']:
                    item_name = item['name'].lower()
                    if any(f.lower() in item_name for f in filters):
                        filtered_data.append(item)
            
            logger.info(f"После фильтрации DNS {category}: {len(filtered_data)} товаров из {len(data)}")
            
            # Покажем несколько примеров отфильтрованных товаров
            if filtered_data:
                sample_names = [item.get('name', 'Без названия') for item in filtered_data[:3]]
                logger.info(f"Примеры отфильтрованных DNS товаров: {sample_names}")
            
            return filtered_data

        def filter_citilink_by_category(data, category):
            """Фильтрует данные Citilink по категории"""
            if not data:
                return []
            
            # Убираем неправильную логику с проверкой размера файла
            # Фильтруем всегда, если получили общий файл
            logger.info(f"Фильтрация Citilink для категории {category}, исходных товаров: {len(data)}")
            
            category_filters = {
                'gpu': ['видеокарт', 'videocard', 'graphics'],
                'cpu': ['процессор', 'processor', 'cpu'],
                'ram': ['память', 'memory', 'dimm', 'оперативн'],
                'storage': ['ssd', 'диск', 'накопител', 'disk', 'storage'],
                'motherboard': ['материнск', 'motherboard', 'мат. плат'],
                'psu': ['блок питания', 'power supply', 'psu'],
                'cooler': ['кулер', 'cooler', 'охлажден'],
                'case': ['корпус', 'case']
            }
            
            if category not in category_filters:
                logger.warning(f"Категория {category} не найдена в фильтрах")
                return data
            
            filters = category_filters[category]
            logger.info(f"Используемые фильтры для {category}: {filters}")
            filtered_data = []
            
            for item in data:
                item_name = ""
                if 'name' in item and item['name']:
                    item_name = item['name'].lower()
                elif 'title' in item and item['title']:
                    item_name = item['title'].lower()
                
                if item_name and any(f.lower() in item_name for f in filters):
                    filtered_data.append(item)
            
            logger.info(f"После фильтрации Citilink {category}: {len(filtered_data)} товаров из {len(data)}")
            
            # Покажем несколько примеров отфильтрованных товаров
            if filtered_data:
                sample_names = [item.get('name', item.get('title', 'Без названия')) for item in filtered_data[:3]]
                logger.info(f"Примеры отфильтрованных товаров: {sample_names}")
            
            return filtered_data
        
        # Используем ту же карта категорий что и в основной функции
        category_mapping = {
            'ram': {
                'dns': ['/app/data/DNS_parsing/categories/product_data_Оперативная память DIMM.json',
                        '/app/utils/DNS_parsing/categories/product_data_Оперативная память DIMM.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['/app/data/Citi_parser/data/moduli-pamyati/Товары.json',
                         '/app/utils/Citi_parser/data/moduli-pamyati/Товары.json'] +
                        ([latest_citilink_file] if latest_citilink_file else []),
                'dns_label': 'Оперативная память DIMM',
                'citi_label': 'Модули памяти'
            },
            'gpu': {
                'dns': ['/app/data/DNS_parsing/categories/product_data_Видеокарты.json',
                        '/app/utils/DNS_parsing/categories/product_data_Видеокарты.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['/app/data/Citi_parser/data/videokarty/Товары.json',
                         '/app/utils/Citi_parser/data/videokarty/Товары.json'] +
                        ([latest_citilink_file] if latest_citilink_file else []),
                'dns_label': 'Видеокарты',
                'citi_label': 'Видеокарты'
            },
            'cpu': {
                'dns': ['/app/data/DNS_parsing/categories/product_data_Процессоры.json',
                        '/app/utils/DNS_parsing/categories/product_data_Процессоры.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['/app/utils/Citi_parser/data/processory/Товары.json',
                         'app/utils/Citi_parser/data/processory/Товары.json',
                         '/app/data/Citi_parser/data/processory/Товары.json'] +
                        ([latest_citilink_file] if latest_citilink_file else []),
                'dns_label': 'Процессоры',
                'citi_label': 'Процессоры'
            },
            'storage': {
                'dns': [
                    ['/app/data/DNS_parsing/categories/product_data_SSD накопители.json',
                     '/app/data/DNS_parsing/categories/product_data_SSD M_2 накопители.json',
                     '/app/data/DNS_parsing/categories/product_data_Жесткие диски 3_5_.json'],
                    ['/app/utils/DNS_parsing/categories/product_data_SSD накопители.json',
                     '/app/utils/DNS_parsing/categories/product_data_SSD M_2 накопители.json',
                     '/app/utils/DNS_parsing/categories/product_data_Жесткие диски 3_5_.json']
                ] + ([[latest_dns_file]] if latest_dns_file else []),
                'citi': [
                    ['/app/data/Citi_parser/data/ssd-nakopiteli/Товары.json',
                     '/app/data/Citi_parser/data/zhestkie-diski/Товары.json'],
                    ['/app/utils/Citi_parser/data/ssd-nakopiteli/Товары.json',
                     '/app/utils/Citi_parser/data/zhestkie-diski/Товары.json']
                ] + ([[latest_citilink_file]] if latest_citilink_file else []),
                'dns_label': 'Накопители (SSD, HDD)',
                'citi_label': 'Накопители (SSD, HDD)'
            },
            'motherboard': {
                'dns': ['/app/data/DNS_parsing/categories/product_data_Материнские платы.json',
                        '/app/utils/DNS_parsing/categories/product_data_Материнские платы.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['/app/data/Citi_parser/data/materinskie-platy/Товары.json',
                         '/app/utils/Citi_parser/data/materinskie-platy/Товары.json'] +
                        ([latest_citilink_file] if latest_citilink_file else []),
                'dns_label': 'Материнские платы',
                'citi_label': 'Материнские платы'
            },
            'psu': {
                'dns': ['/app/data/DNS_parsing/categories/product_data_Блоки питания.json',
                        '/app/utils/DNS_parsing/categories/product_data_Блоки питания.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['/app/data/Citi_parser/data/bloki-pitaniya/Товары.json',
                         '/app/utils/Citi_parser/data/bloki-pitaniya/Товары.json'] +
                        ([latest_citilink_file] if latest_citilink_file else []),
                'dns_label': 'Блоки питания',
                'citi_label': 'Блоки питания'
            },
            'cooler': {
                'dns': ['/app/data/DNS_parsing/categories/product_data_Кулеры для процессоров.json',
                        '/app/utils/DNS_parsing/categories/product_data_Кулеры для процессоров.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['/app/data/Citi_parser/data/sistemy-ohlazhdeniya-processora/Товары.json',
                         '/app/utils/Citi_parser/data/sistemy-ohlazhdeniya-processora/Товары.json'] +
                        ([latest_citilink_file] if latest_citilink_file else []),
                'dns_label': 'Кулеры для процессоров',
                'citi_label': 'Системы охлаждения процессора'
            },
            'case': {
                'dns': ['/app/data/DNS_parsing/categories/product_data_Корпуса.json',
                        '/app/utils/DNS_parsing/categories/product_data_Корпуса.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['/app/data/Citi_parser/data/korpusa/Товары.json',
                         '/app/utils/Citi_parser/data/korpusa/Товары.json'] +
                        ([latest_citilink_file] if latest_citilink_file else []),
                'dns_label': 'Корпуса',
                'citi_label': 'Корпуса'
            }
        }
        
        # Функции поиска файлов (те же что и в основной функции)
        def find_existing_file(paths):
            """Возвращает первый существующий файл из списка путей"""
            if isinstance(paths, str):
                logger.info(f"Проверяем путь: {paths}")
                exists = os.path.exists(paths)
                logger.info(f"Файл {'найден' if exists else 'не найден'}: {paths}")
                return paths if exists else None
            for path in paths:
                logger.info(f"Проверяем путь: {path}")
                exists = os.path.exists(path)
                logger.info(f"Файл {'найден' if exists else 'не найден'}: {path}")
                if exists:
                    return path
            return None
        
        def find_existing_files(paths_list):
            """Для storage - возвращает первый набор путей где все файлы существуют"""
            logger.info(f"find_existing_files вызвана с: {paths_list}")
            if not isinstance(paths_list[0], list):
                # Обычная категория, не storage
                logger.info("Обычная категория, используем find_existing_file")
                return find_existing_file(paths_list)
            
            logger.info("Storage категория, проверяем наборы путей")
            for i, path_set in enumerate(paths_list):
                logger.info(f"Проверяем набор {i}: {path_set}")
                all_exist = all(os.path.exists(path) for path in path_set)
                logger.info(f"Все файлы в наборе {i} {'найдены' if all_exist else 'не найдены'}")
                if all_exist:
                    return path_set
            return None
        
        if category not in category_mapping:
            flash(f'Категория "{category}" не поддерживается', 'error')
            return redirect(url_for('comparison.index'))
        
        cat_info = category_mapping[category]
        
        # Создаем компаратор
        comparator = get_comparator()
        
        # Загружаем данные (специальная обработка для storage)
        if category == 'storage':
            # Объединяем данные из нескольких файлов
            dns_data = []
            citi_data = []
            
            # Находим существующие DNS файлы
            dns_paths = find_existing_files(cat_info['dns'])
            if dns_paths:
                if len(dns_paths) == 1 and 'local_parser_data' in dns_paths[0]:
                    # Общий файл DNS - загружаем и фильтруем
                    logger.info("Загружаем общий файл DNS для storage")
                    dns_file = find_existing_file(dns_paths)
                    if dns_file:
                        with open(dns_file, 'r', encoding='utf-8') as f:
                            if 'local_parser_data_' in dns_file:
                                general_data = json.load(f)
                                dns_data = filter_dns_by_category(general_data, category)
                            else:
                                dns_data = json.load(f)
                    logger.info(f"После фильтрации storage: {len(dns_data)} товаров из {len(dns_data) if dns_data else 0}")
                else:
                    # Отдельные файлы по категориям
                    for dns_path in dns_paths:
                        dns_file = find_existing_file(dns_path)
                        if dns_file:
                            with open(dns_file, 'r', encoding='utf-8') as f:
                                if 'local_parser_data_' in dns_file:
                                    general_data = json.load(f)
                                    dns_data.extend(filter_dns_by_category(general_data, category))
                        else:
                                    dns_data.extend(json.load(f))
            
            # Находим существующие Citilink файлы  
            citi_paths = find_existing_files(cat_info['citi'])
            if citi_paths:
                for citi_path in citi_paths:
                    citi_file = find_existing_file(citi_path)
                    if citi_file:
                        with open(citi_file, 'r', encoding='utf-8') as f:
                            if 'citilink_data_' in citi_file or ('Товары.json' in citi_file and latest_citilink_file and latest_citilink_file == citi_file):
                                logger.info(f"Загружаем общий файл Citilink для {category}")
                                general_data = json.load(f)
                                citi_data.extend(filter_citilink_by_category(general_data, category))
                                logger.info(f"После фильтрации Citilink {category}: {len(citi_data)} товаров из {len(general_data)}")
                            else:
                                citi_data.extend(json.load(f))
        else:
            # Находим существующие файлы для обычных категорий
            dns_path = find_existing_file(cat_info['dns'])
            citi_path = find_existing_file(cat_info['citi'])
            
            # Проверяем существование файлов
            if not dns_path or not citi_path:
                flash(f'Файлы данных для категории "{category}" не найдены', 'error')
                return redirect(url_for('comparison.index'))
            
            # Загружаем данные
            dns_file = find_existing_file(cat_info['dns'])
            citi_file = find_existing_file(cat_info['citi'])
            
            dns_data = []
            citi_data = []
            
            if dns_file:
                with open(dns_file, 'r', encoding='utf-8') as f:
                    if 'local_parser_data_' in dns_file:
                        general_data = json.load(f)
                        dns_data = filter_dns_by_category(general_data, category)
                    else:
                        dns_data = json.load(f)
            
            if citi_file:
                with open(citi_file, 'r', encoding='utf-8') as f:
                    if 'citilink_data_' in citi_file or ('Товары.json' in citi_file and latest_citilink_file and latest_citilink_file == citi_file):
                        logger.info(f"Загружаем общий файл Citilink для {category}")
                        general_data = json.load(f)
                        citi_data = filter_citilink_by_category(general_data, category)
                        logger.info(f"После фильтрации Citilink {category}: {len(citi_data)} товаров из {len(general_data)}")
                    else:
                        citi_data = json.load(f)
        
        if not dns_data or not citi_data:
            flash('Не удалось загрузить данные для сравнения', 'error')
            return redirect(url_for('comparison.index'))
        
        # Извлекаем названия
        dns_names = comparator.extract_names(dns_data, "name")
        citi_names = comparator.extract_names(citi_data, "name")
        
        # Быстрое сравнение с порогом 0.6 и гибридным алгоритмом
        matches = comparator.find_best_matches(
            dns_names, citi_names, 
            threshold=0.6,
            use_enhanced=True  # Используем гибридный алгоритм!
        )
        
        # Создаем детальные результаты
        detailed_matches = []
        total_dns_cheaper = 0
        total_citi_cheaper = 0
        price_differences = []
        
        for dns_name, citi_name, similarity in matches:
            dns_item = next((item for item in dns_data if item["name"] == dns_name), None)
            citi_item = next((item for item in citi_data if item["name"] == citi_name), None)
            
            if dns_item and citi_item:
                dns_price = comparator._extract_price(dns_item)
                citi_price = comparator._extract_price(citi_item)
                
                match_data = {
                    'dns_name': dns_name,
                    'citi_name': citi_name,
                    'similarity': similarity,
                    'dns_price': dns_price,
                    'citi_price': citi_price,
                    'dns_url': dns_item.get('url', '#'),
                    'citi_url': citi_item.get('url', '#'),
                    'dns_brand': dns_item.get('brand_name', ''),
                    'citi_brand': citi_item.get('brand', '')
                }
                
                if dns_price and citi_price:
                    difference = citi_price - dns_price  # Положительное значение означает, что DNS дешевле
                    price_differences.append(difference)
                    
                    if difference > 0:
                        total_dns_cheaper += 1
                        match_data['cheaper_store'] = 'dns'
                    elif difference < 0:
                        total_citi_cheaper += 1
                        match_data['cheaper_store'] = 'citi'
                    else:
                        match_data['cheaper_store'] = 'equal'
                    
                    match_data['price_difference'] = difference
                else:
                    match_data['cheaper_store'] = 'unknown'
                    match_data['price_difference'] = None
                
                detailed_matches.append(match_data)
        
        # Рассчитываем статистику
        price_stats = {}
        if price_differences:
            price_stats = {
                'count': len(price_differences),
                'average_difference': sum(price_differences) / len(price_differences),
                'min_difference': min(price_differences),
                'max_difference': max(price_differences),
                'dns_cheaper_count': total_dns_cheaper,
                'citi_cheaper_count': total_citi_cheaper,
                'equal_price_count': len([d for d in price_differences if d == 0])
            }
        
        # Формируем результат
        result = {
            'dns_category': category_mapping[category]['dns_label'],
            'citi_category': category_mapping[category]['citi_label'],
            'dns_count': len(dns_data),
            'citi_count': len(citi_data),
            'matches_count': len(detailed_matches),
            'matches': detailed_matches,
            'threshold': 0.6,
            'price_statistics': price_stats
        }
        
        return render_template('comparison/results.html',
                             category=category,
                             threshold=0.6,
                             result=result,
                             is_quick_compare=True)
    
    except Exception as e:
        logger.error(f"Ошибка при быстром сравнении: {str(e)}")
        flash(f'Произошла ошибка: {str(e)}', 'error')
        return redirect(url_for('comparison.index')) 

@comparison_bp.route('/clear-cache', methods=['POST'])
@login_required
def clear_cache():
    """Очистка кэша эмбеддингов"""
    try:
        comparator = get_comparator()
        cache_size_before = comparator.get_cache_size()
        comparator.clear_embeddings_cache()
        cache_size_after = comparator.get_cache_size()
        
        flash(f'Кэш очищен! Удалено {cache_size_before} записей.', 'success')
        logger.info(f"Кэш эмбеддингов очищен. Размер до очистки: {cache_size_before}, после: {cache_size_after}")
        
        return jsonify({
            'success': True,
            'message': f'Кэш очищен! Удалено {cache_size_before} записей.',
            'cache_size_before': cache_size_before,
            'cache_size_after': cache_size_after
        })
    
    except Exception as e:
        logger.error(f"Ошибка при очистке кэша: {str(e)}")
        flash(f'Ошибка при очистке кэша: {str(e)}', 'error')
        
        return jsonify({
            'success': False,
            'message': f'Ошибка при очистке кэша: {str(e)}'
        }), 500 