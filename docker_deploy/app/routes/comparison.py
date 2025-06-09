from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required
from app.forms.comparison import ProductComparisonForm
from app.utils.product_comparator import ProductComparator, get_comparator
import logging
import os
import glob

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
    """Сравнение товаров"""
    try:
        form = ProductComparisonForm()
        
        if not form.validate_on_submit():
            flash('Ошибка валидации формы', 'error')
            return redirect(url_for('comparison.index'))
        
        category = form.category.data
        threshold = form.threshold.data
        
        # Карта категорий для определения правильных путей
        category_mapping = {
            'ram': {
                'dns': 'app/utils/DNS_parsing/categories/product_data_Оперативная память DIMM.json',
                'citi': 'app/utils/Citi_parser/data/moduli-pamyati/Товары.json',
                'dns_label': 'Оперативная память DIMM',
                'citi_label': 'Модули памяти'
            },
            'gpu': {
                'dns': 'app/utils/DNS_parsing/categories/product_data_Видеокарты.json',
                'citi': 'app/utils/Citi_parser/data/videokarty/Товары.json',
                'dns_label': 'Видеокарты',
                'citi_label': 'Видеокарты'
            },
            'cpu': {
                'dns': 'app/utils/DNS_parsing/categories/product_data_Процессоры.json',
                'citi': 'app/utils/Citi_parser/data/processory/Товары.json',
                'dns_label': 'Процессоры',
                'citi_label': 'Процессоры'
            },
            'storage': {
                'dns': [
                    'app/utils/DNS_parsing/categories/product_data_SSD накопители.json',
                    'app/utils/DNS_parsing/categories/product_data_SSD M_2 накопители.json',
                    'app/utils/DNS_parsing/categories/product_data_Жесткие диски 3_5_.json'
                ],
                'citi': [
                    'app/utils/Citi_parser/data/ssd-nakopiteli/Товары.json',
                    'app/utils/Citi_parser/data/zhestkie-diski/Товары.json'
                ],
                'dns_label': 'Накопители (SSD, HDD)',
                'citi_label': 'Накопители (SSD, HDD)'
            },
            'motherboard': {
                'dns': 'app/utils/DNS_parsing/categories/product_data_Материнские платы.json',
                'citi': 'app/utils/Citi_parser/data/materinskie-platy/Товары.json',
                'dns_label': 'Материнские платы',
                'citi_label': 'Материнские платы'
            },
            'psu': {
                'dns': 'app/utils/DNS_parsing/categories/product_data_Блоки питания.json',
                'citi': 'app/utils/Citi_parser/data/bloki-pitaniya/Товары.json',
                'dns_label': 'Блоки питания',
                'citi_label': 'Блоки питания'
            },
            'cooler': {
                'dns': 'app/utils/DNS_parsing/categories/product_data_Кулеры для процессоров.json',
                'citi': 'app/utils/Citi_parser/data/sistemy-ohlazhdeniya-processora/Товары.json',
                'dns_label': 'Кулеры для процессоров',
                'citi_label': 'Системы охлаждения процессора'
            },
            'case': {
                'dns': 'app/utils/DNS_parsing/categories/product_data_Корпуса.json',
                'citi': 'app/utils/Citi_parser/data/korpusa/Товары.json',
                'dns_label': 'Корпуса',
                'citi_label': 'Корпуса'
            }
        }
        
        # Проверяем существование категории
        if category not in category_mapping:
            flash(f'Категория "{category}" не поддерживается', 'error')
            return redirect(url_for('comparison.index'))
        
        # Создаем компаратор
        comparator = get_comparator()
        
        # Загружаем данные (специальная обработка для storage)
        if category == 'storage':
            # Объединяем данные из нескольких файлов
            dns_data = []
            citi_data = []
            
            # Загружаем DNS файлы
            for dns_path in category_mapping[category]['dns']:
                if os.path.exists(dns_path):
                    file_data = comparator.load_json_data(dns_path)
                    if file_data:
                        if isinstance(file_data, list):
                            dns_data.extend(file_data)
                        else:
                            dns_data.append(file_data)
            
            # Загружаем Citilink файлы  
            for citi_path in category_mapping[category]['citi']:
                if os.path.exists(citi_path):
                    file_data = comparator.load_json_data(citi_path)
                    if file_data:
                        if isinstance(file_data, list):
                            citi_data.extend(file_data)
                        else:
                            citi_data.append(file_data)
        else:
            # Определяем пути к файлам для обычных категорий
            dns_path = category_mapping[category]['dns']
            citi_path = category_mapping[category]['citi']
            
            # Проверяем существование файлов
            if not os.path.exists(dns_path) or not os.path.exists(citi_path):
                flash(f'Файлы данных для категории "{category}" не найдены. DNS: {dns_path}, Citi: {citi_path}', 'error')
                return redirect(url_for('comparison.index'))
            
            # Загружаем данные
            dns_data = comparator.load_json_data(dns_path)
            citi_data = comparator.load_json_data(citi_path)
        
        if not dns_data or not citi_data:
            flash('Не удалось загрузить данные для сравнения', 'error')
            return redirect(url_for('comparison.index'))
        
        # Извлекаем названия
        dns_names = comparator.extract_names(dns_data, "name")
        citi_names = comparator.extract_names(citi_data, "name")
        
        # Ищем совпадения с использованием гибридного алгоритма
        matches = comparator.find_best_matches(
            dns_names, citi_names, 
            threshold=threshold,
            use_enhanced=True  # Используем гибридный алгоритм!
        )
        
        # Создаем детальные результаты с ценами
        detailed_matches = []
        total_dns_cheaper = 0
        total_citi_cheaper = 0
        price_differences = []
        
        for dns_name, citi_name, similarity in matches:
            # Находим соответствующие товары в исходных данных
            dns_item = next((item for item in dns_data if item["name"] == dns_name), None)
            citi_item = next((item for item in citi_data if item["name"] == citi_name), None)
            
            if dns_item and citi_item:
                # Извлекаем цены
                dns_price = comparator._extract_price(dns_item)
                citi_price = comparator._extract_price(citi_item)
                
                # Создаем ссылки на товары
                dns_link = dns_item.get('url', '#')
                citi_link = citi_item.get('url', '#')
                
                match_data = {
                    'dns_name': dns_name,
                    'citi_name': citi_name,
                    'similarity': similarity,
                    'dns_price': dns_price,
                    'citi_price': citi_price,
                    'dns_url': dns_link,
                    'citi_url': citi_link,
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
            'dns_category': category_mapping[category]['dns_label'],
            'citi_category': category_mapping[category]['citi_label'],
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
        # Карта категорий
        category_mapping = {
            'ram': {
                'dns': 'app/utils/DNS_parsing/categories/product_data_Оперативная память DIMM.json',
                'citi': 'app/utils/Citi_parser/data/moduli-pamyati/Товары.json',
                'dns_label': 'Оперативная память DIMM',
                'citi_label': 'Модули памяти'
            },
            'gpu': {
                'dns': 'app/utils/DNS_parsing/categories/product_data_Видеокарты.json',
                'citi': 'app/utils/Citi_parser/data/videokarty/Товары.json',
                'dns_label': 'Видеокарты',
                'citi_label': 'Видеокарты'
            },
            'cpu': {
                'dns': 'app/utils/DNS_parsing/categories/product_data_Процессоры.json',
                'citi': 'app/utils/Citi_parser/data/processory/Товары.json',
                'dns_label': 'Процессоры',
                'citi_label': 'Процессоры'
            },
            'storage': {
                'dns': [
                    'app/utils/DNS_parsing/categories/product_data_SSD накопители.json',
                    'app/utils/DNS_parsing/categories/product_data_SSD M_2 накопители.json',
                    'app/utils/DNS_parsing/categories/product_data_Жесткие диски 3_5_.json'
                ],
                'citi': [
                    'app/utils/Citi_parser/data/ssd-nakopiteli/Товары.json',
                    'app/utils/Citi_parser/data/zhestkie-diski/Товары.json'
                ],
                'dns_label': 'Накопители (SSD, HDD)',
                'citi_label': 'Накопители (SSD, HDD)'
            },
            'motherboard': {
                'dns': 'app/utils/DNS_parsing/categories/product_data_Материнские платы.json',
                'citi': 'app/utils/Citi_parser/data/materinskie-platy/Товары.json',
                'dns_label': 'Материнские платы',
                'citi_label': 'Материнские платы'
            },
            'psu': {
                'dns': 'app/utils/DNS_parsing/categories/product_data_Блоки питания.json',
                'citi': 'app/utils/Citi_parser/data/bloki-pitaniya/Товары.json',
                'dns_label': 'Блоки питания',
                'citi_label': 'Блоки питания'
            },
            'cooler': {
                'dns': 'app/utils/DNS_parsing/categories/product_data_Кулеры для процессоров.json',
                'citi': 'app/utils/Citi_parser/data/sistemy-ohlazhdeniya-processora/Товары.json',
                'dns_label': 'Кулеры для процессоров',
                'citi_label': 'Системы охлаждения процессора'
            },
            'case': {
                'dns': 'app/utils/DNS_parsing/categories/product_data_Корпуса.json',
                'citi': 'app/utils/Citi_parser/data/korpusa/Товары.json',
                'dns_label': 'Корпуса',
                'citi_label': 'Корпуса'
            }
        }
        
        if category not in category_mapping:
            flash(f'Категория "{category}" не поддерживается', 'error')
            return redirect(url_for('comparison.index'))
        
        # Создаем компаратор
        comparator = get_comparator()
        
        # Загружаем данные (специальная обработка для storage)
        if category == 'storage':
            # Объединяем данные из нескольких файлов
            dns_data = []
            citi_data = []
            
            # Загружаем DNS файлы
            for dns_path in category_mapping[category]['dns']:
                if os.path.exists(dns_path):
                    file_data = comparator.load_json_data(dns_path)
                    if file_data:
                        if isinstance(file_data, list):
                            dns_data.extend(file_data)
                        else:
                            dns_data.append(file_data)
            
            # Загружаем Citilink файлы  
            for citi_path in category_mapping[category]['citi']:
                if os.path.exists(citi_path):
                    file_data = comparator.load_json_data(citi_path)
                    if file_data:
                        if isinstance(file_data, list):
                            citi_data.extend(file_data)
                        else:
                            citi_data.append(file_data)
        else:
            # Определяем пути к файлам для обычных категорий
            dns_path = category_mapping[category]['dns']
            citi_path = category_mapping[category]['citi']
            
            # Проверяем существование файлов
            if not os.path.exists(dns_path) or not os.path.exists(citi_path):
                flash(f'Файлы данных для категории "{category}" не найдены', 'error')
                return redirect(url_for('comparison.index'))
            
            # Загружаем данные
            dns_data = comparator.load_json_data(dns_path)
            citi_data = comparator.load_json_data(citi_path)
        
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