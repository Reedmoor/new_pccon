from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required
from app.forms.comparison import ProductComparisonForm
from app.utils.product_comparator import ProductComparator, get_comparator
from app.utils.standardization.import_helpers import (
    compare_category_to_product_type,
    filter_products_by_compare_category,
)
import logging
import os
import glob
from app.models.models import UnifiedProduct
import json

logger = logging.getLogger(__name__)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def resolve_existing_path(path_value):
    """Resolve path across docker-like and local workspace styles."""
    if not path_value:
        return None

    normalized = str(path_value).replace('/', os.sep).replace('\\', os.sep)
    stripped = normalized.lstrip(os.sep)

    candidates = [
        normalized,
        stripped,
        os.path.join(PROJECT_ROOT, normalized),
        os.path.join(PROJECT_ROOT, stripped),
    ]

    for candidate in candidates:
        candidate_abs = os.path.abspath(candidate)
        if os.path.exists(candidate_abs):
            return candidate_abs
    return None


def category_to_product_type(category):
    return compare_category_to_product_type(category)


def find_existing_file(paths):
    if isinstance(paths, str):
        return resolve_existing_path(paths)
    for path in paths:
        resolved = resolve_existing_path(path)
        if resolved:
            return resolved
    return None


def _load_json_product_list(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "products" in data:
        return data["products"]
    if isinstance(data, list):
        return data
    return [data] if data else []


def find_existing_files(paths_list):
    """Для storage — набор путей; иначе один файл."""
    if not paths_list:
        return None
    if not isinstance(paths_list[0], list):
        return find_existing_file(paths_list)
    for path_set in paths_list:
        if all(resolve_existing_path(path) for path in path_set):
            return [resolve_existing_path(path) for path in path_set]
    return None


def load_vendor_products_for_compare(vendor, category, file_paths):
    """Сначала БД (product_type), иначе JSON с обязательной фильтрацией по категории."""
    db_products = load_products_from_db(vendor, category)
    if db_products:
        logger.info("%s для %s: %s товаров из БД", vendor, category, len(db_products))
        return db_products

    path = find_existing_file(file_paths)
    if not path:
        return []

    raw = _load_json_product_list(path)
    filtered = filter_products_by_compare_category(raw, category)
    logger.info(
        "%s для %s: %s товаров из %s (в файле было %s)",
        vendor, category, len(filtered), path, len(raw),
    )
    return filtered


def load_storage_products_for_compare(vendor, category, paths_list):
    """Несколько JSON-файлов (накопители), с фильтрацией по категории."""
    db_products = load_products_from_db(vendor, category)
    if db_products:
        return db_products
    resolved_paths = find_existing_files(paths_list)
    if not resolved_paths:
        return []
    if isinstance(resolved_paths, str):
        resolved_paths = [resolved_paths]
    combined = []
    for path in resolved_paths:
        combined.extend(filter_products_by_compare_category(_load_json_product_list(path), category))
    return combined


def serialize_unified_product(product):
    return {
        'name': product.product_name,
        'url': product.product_url,
        'price': product.price_discounted,
        'price_original': product.price_original,
        'brand': '',
        'brand_name': '',
        'categories': product.get_category() if hasattr(product, 'get_category') else [],
        'images': product.get_images() if hasattr(product, 'get_images') else [],
        'characteristics': product.get_characteristics() if hasattr(product, 'get_characteristics') else {},
    }


def load_products_from_db(vendor, category):
    product_type = category_to_product_type(category)
    if not product_type:
        return []

    products = (
        UnifiedProduct.query
        .filter_by(vendor=vendor, product_type=product_type)
        .all()
    )
    return [serialize_unified_product(product) for product in products]

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
                        except Exception as e:
                            logger.error(f"Ошибка при проверке файла {file_path}: {str(e)}")
                else:
                    # Это конкретный файл
                    if os.path.exists(path_pattern):
                        try:
                            file_time = os.path.getmtime(path_pattern)
                            if file_time > latest_time:
                                latest_time = file_time
                                latest_file = path_pattern
                        except Exception as e:
                            logger.error(f"Ошибка при проверке файла {path_pattern}: {str(e)}")
            
            logger.info(f"Найден последний файл DNS данных: {latest_file}")
            return latest_file

        # Функция для поиска последнего файла Citilink данных
        def get_latest_citilink_data_file():
            """Находит самый последний файл citilink_data_*.json или общий файл"""
            search_paths = [
                'data/citilink_data_*.json',
                '/app/data/citilink_data_*.json'
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

        # Получаем последние файлы данных
        latest_dns_file = get_latest_dns_data_file()
        latest_citilink_file = get_latest_citilink_data_file()
        
        # Маппинг категорий к файлам данных
        category_mapping = {
            'ram': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/moduli-pamyati/Товары.json',
                         '/app/utils/Citi_parser/data/moduli-pamyati/Товары.json'],
                'dns_label': 'Оперативная память DIMM',
                'citi_label': 'Модули памяти',
            },
            'gpu': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/videokarty/Товары.json',
                         '/app/utils/Citi_parser/data/videokarty/Товары.json'],
                'dns_label': 'Видеокарты',
                'citi_label': 'Видеокарты',
            },
            'cpu': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/processory/Товары.json',
                         '/app/utils/Citi_parser/data/processory/Товары.json'],
                'dns_label': 'Процессоры',
                'citi_label': 'Процессоры',
            },
            'motherboard': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/materinskie-platy/Товары.json',
                         '/app/utils/Citi_parser/data/materinskie-platy/Товары.json'],
                'dns_label': 'Материнские платы',
                'citi_label': 'Материнские платы',
            },
            'storage': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/zhestkie-diski/Товары.json',
                         '/app/utils/Citi_parser/data/zhestkie-diski/Товары.json',
                         'app/utils/Citi_parser/data/ssd-nakopiteli/Товары.json',
                         '/app/utils/Citi_parser/data/ssd-nakopiteli/Товары.json'],
                'dns_label': 'Накопители',
                'citi_label': 'Накопители',
            },
            'psu': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/bloki-pitaniya/Товары.json',
                         '/app/utils/Citi_parser/data/bloki-pitaniya/Товары.json'],
                'dns_label': 'Блоки питания',
                'citi_label': 'Блоки питания',
            },
            'cooler': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/sistemy-ohlazhdeniya-processora/Товары.json',
                         '/app/utils/Citi_parser/data/sistemy-ohlazhdeniya-processora/Товары.json'],
                'dns_label': 'Кулеры для процессоров',
                'citi_label': 'Системы охлаждения процессора',
            },
            'case': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/korpusa/Товары.json',
                         '/app/utils/Citi_parser/data/korpusa/Товары.json'],
                'dns_label': 'Корпуса',
                'citi_label': 'Корпуса',
            }
        }
        
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
        
        if category == 'storage':
            dns_data = load_storage_products_for_compare('dns', category, cat_info['dns'])
            citi_data = load_storage_products_for_compare('citilink', category, cat_info['citi'])
        else:
            dns_data = load_vendor_products_for_compare('dns', category, cat_info['dns'])
            citi_data = load_vendor_products_for_compare('citilink', category, cat_info['citi'])

        if not dns_data and not citi_data:
            flash(
                f'Нет данных для сравнения «{cat_info["dns_label"]}». '
                f'Запустите импорт или проверьте файлы парсера.',
                'error',
            )
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
        # Функция для поиска последнего файла DNS данных
        def get_latest_dns_data_file():
            """Находит самый последний файл local_parser_data_*.json"""
            search_paths = [
                'data/local_parser_data_*.json',
                '/app/data/local_parser_data_*.json'
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
                        except Exception as e:
                            logger.error(f"Ошибка при проверке файла {file_path}: {str(e)}")
                else:
                    # Это конкретный файл
                    if os.path.exists(path_pattern):
                        try:
                            file_time = os.path.getmtime(path_pattern)
                            if file_time > latest_time:
                                latest_time = file_time
                                latest_file = path_pattern
                        except Exception as e:
                            logger.error(f"Ошибка при проверке файла {path_pattern}: {str(e)}")
            
            logger.info(f"Найден последний файл DNS данных: {latest_file}")
            return latest_file

        # Функция для поиска последнего файла Citilink данных
        def get_latest_citilink_data_file():
            """Находит самый последний файл citilink_data_*.json или общий файл"""
            search_paths = [
                'data/citilink_data_*.json',
                '/app/data/citilink_data_*.json'
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
        
        category_mapping = {
            'ram': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/moduli-pamyati/Товары.json',
                         '/app/utils/Citi_parser/data/moduli-pamyati/Товары.json'],
                'dns_label': 'Оперативная память DIMM',
                'citi_label': 'Модули памяти',
            },
            'gpu': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/videokarty/Товары.json',
                         '/app/utils/Citi_parser/data/videokarty/Товары.json'],
                'dns_label': 'Видеокарты',
                'citi_label': 'Видеокарты',
            },
            'cpu': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/processory/Товары.json',
                         '/app/utils/Citi_parser/data/processory/Товары.json'],
                'dns_label': 'Процессоры',
                'citi_label': 'Процессоры',
            },
            'motherboard': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/materinskie-platy/Товары.json',
                         '/app/utils/Citi_parser/data/materinskie-platy/Товары.json'],
                'dns_label': 'Материнские платы',
                'citi_label': 'Материнские платы',
            },
            'storage': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/zhestkie-diski/Товары.json',
                         '/app/utils/Citi_parser/data/zhestkie-diski/Товары.json',
                         'app/utils/Citi_parser/data/ssd-nakopiteli/Товары.json',
                         '/app/utils/Citi_parser/data/ssd-nakopiteli/Товары.json'],
                'dns_label': 'Накопители',
                'citi_label': 'Накопители',
            },
            'psu': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/bloki-pitaniya/Товары.json',
                         '/app/utils/Citi_parser/data/bloki-pitaniya/Товары.json'],
                'dns_label': 'Блоки питания',
                'citi_label': 'Блоки питания',
            },
            'cooler': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/sistemy-ohlazhdeniya-processora/Товары.json',
                         '/app/utils/Citi_parser/data/sistemy-ohlazhdeniya-processora/Товары.json'],
                'dns_label': 'Кулеры для процессоров',
                'citi_label': 'Системы охлаждения процессора',
            },
            'case': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/korpusa/Товары.json',
                         '/app/utils/Citi_parser/data/korpusa/Товары.json'],
                'dns_label': 'Корпуса',
                'citi_label': 'Корпуса',
            }
        }
        
        if category not in category_mapping:
            flash(f'Категория "{category}" не поддерживается', 'error')
            return redirect(url_for('comparison.index'))
        
        cat_info = category_mapping[category]
        comparator = get_comparator()

        if category == 'storage':
            dns_data = load_storage_products_for_compare('dns', category, cat_info['dns'])
            citi_data = load_storage_products_for_compare('citilink', category, cat_info['citi'])
        else:
            dns_data = load_vendor_products_for_compare('dns', category, cat_info['dns'])
            citi_data = load_vendor_products_for_compare('citilink', category, cat_info['citi'])

        if not dns_data and not citi_data:
            flash(f'Нет данных для сравнения «{cat_info["dns_label"]}».', 'error')
            return redirect(url_for('comparison.index'))
        
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

@comparison_bp.route('/api/compare/<category>')
def api_compare(category):
    """API endpoint для сравнения товаров по категории"""
    try:
        threshold = float(request.args.get('threshold', 0.6))
        
        # Используем ту же логику что и в quick_compare
        logger.info(f"API сравнение категории: {category}")
        
        # Функция для поиска последнего файла DNS данных
        def get_latest_dns_data_file():
            """Находит самый последний файл local_parser_data_*.json"""
            search_paths = [
                'data/local_parser_data_*.json',
                '/app/data/local_parser_data_*.json'
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
                        except Exception as e:
                            logger.error(f"Ошибка при проверке файла {file_path}: {str(e)}")
                else:
                    if os.path.exists(path_pattern):
                        try:
                            file_time = os.path.getmtime(path_pattern)
                            if file_time > latest_time:
                                latest_time = file_time
                                latest_file = path_pattern
                        except Exception as e:
                            logger.error(f"Ошибка при проверке файла {path_pattern}: {str(e)}")
            
            logger.info(f"Найден последний файл DNS данных: {latest_file}")
            return latest_file

        latest_dns_file = get_latest_dns_data_file()

        # Маппинг категорий
        category_mapping = {
            'cpu': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/processory/Товары.json',
                         '/app/utils/Citi_parser/data/processory/Товары.json'],
                'dns_label': 'Процессоры',
                'citi_label': 'Процессоры',
            },
            'gpu': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/videokarty/Товары.json',
                         '/app/utils/Citi_parser/data/videokarty/Товары.json'],
                'dns_label': 'Видеокарты',
                'citi_label': 'Видеокарты',
            },
            'ram': {
                'dns': ['/app/utils/old_dns_parser/product_data.json',
                        'app/utils/old_dns_parser/product_data.json'] + 
                       ([latest_dns_file] if latest_dns_file else []),
                'citi': ['app/utils/Citi_parser/data/moduli-pamyati/Товары.json',
                         '/app/utils/Citi_parser/data/moduli-pamyati/Товары.json'],
                'dns_label': 'Оперативная память DIMM',
                'citi_label': 'Модули памяти',
            }
        }
        
        # Проверяем существование категории
        if category not in category_mapping:
            return jsonify({
                'status': 'error',
                'message': f'Категория "{category}" не поддерживается'
            }), 400
        
        cat_info = category_mapping[category]
        logger.info(f"API сравнение категории: {category}")
        logger.info(f"DNS пути: {cat_info['dns']}")
        logger.info(f"Citi пути: {cat_info['citi']}")
        
        dns_data = load_vendor_products_for_compare('dns', category, cat_info['dns'])
        citi_data = load_vendor_products_for_compare('citilink', category, cat_info['citi'])

        # Создаем компаратор
        comparator = get_comparator()
        
        # Извлекаем названия товаров
        dns_names = comparator.extract_names(dns_data, "name")
        citi_names = comparator.extract_names(citi_data, "name")
        
        # Выполняем сравнение
        matches = comparator.find_best_matches(
            dns_names, citi_names, 
            threshold=threshold,
            use_enhanced=True
        )
        
        # Создаем детальные результаты
        detailed_matches = []
        for dns_name, citi_name, similarity in matches:
            dns_item = next((item for item in dns_data if item["name"] == dns_name), None)
            citi_item = next((item for item in citi_data if item["name"] == citi_name), None)
            
            if dns_item and citi_item:
                detailed_matches.append({
                    'dns_name': dns_name,
                    'citi_name': citi_name,
                    'similarity': round(similarity, 3),
                    'dns_price': comparator._extract_price(dns_item),
                    'citi_price': comparator._extract_price(citi_item),
                    'dns_url': dns_item.get('url', '#'),
                    'citi_url': citi_item.get('url', '#')
                })
        
        return jsonify({
            'status': 'success',
            'category': category,
            'dns_count': len(dns_data),
            'citilink_count': len(citi_data),
            'matches_count': len(detailed_matches),
            'threshold': threshold,
            'matches': detailed_matches[:10]  # Возвращаем только первые 10 для API
        })
        
    except Exception as e:
        logger.error(f"Ошибка в API сравнения: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Произошла ошибка: {str(e)}'
        }), 500 