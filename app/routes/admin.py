import os
import sys
import subprocess
import json
import glob
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models.models import UnifiedProduct, User, Configuration
from app.forms.admin import UnifiedProductForm
from app.auth import login_required, admin_required
from app.logger import get_logger
from flask_login import current_user
from pathlib import Path

logger = get_logger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Добавляем фильтр для получения текущей даты и времени
@admin_bp.app_template_filter('now')
def _jinja2_filter_now():
    return datetime.now()

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Count products by type using the UnifiedProduct model
    motherboards_count = UnifiedProduct.query.filter_by(product_type='motherboard').count()
    power_supplies_count = UnifiedProduct.query.filter_by(product_type='power_supply').count()
    processors_count = UnifiedProduct.query.filter_by(product_type='processor').count()
    gpus_count = UnifiedProduct.query.filter_by(product_type='graphics_card').count()
    coolers_count = UnifiedProduct.query.filter_by(product_type='cooler').count()
    rams_count = UnifiedProduct.query.filter_by(product_type='ram').count()
    hdds_count = UnifiedProduct.query.filter_by(product_type='hard_drive').count()
    cases_count = UnifiedProduct.query.filter_by(product_type='case').count()
    
    return render_template('admin/dashboard.html', 
                          counts={
                              'motherboards': motherboards_count,
                              'power_supplies': power_supplies_count,
                              'processors': processors_count,
                              'gpus': gpus_count,
                              'coolers': coolers_count,
                              'rams': rams_count,
                              'hdds': hdds_count,
                              'cases': cases_count
                          })

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('Вы не можете изменить свои права администратора', 'danger')
    else:
        if user.role == 'admin':
            user.role = 'user'
            flash(f'Пользователь {user.name} больше не администратор', 'success')
        else:
            user.role = 'admin'
            flash(f'Пользователь {user.name} теперь администратор', 'success')
        db.session.commit()
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('Вы не можете удалить самого себя', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f'Пользователь {user.name} успешно удален', 'success')
    return redirect(url_for('admin.users'))

# Unified product routes for all components
@admin_bp.route('/products')
@login_required
@admin_required
def products():
    product_type = request.args.get('type', 'all')
    sort_by = request.args.get('sort', None)
    sort_dir = request.args.get('dir', 'asc')
    
    # Start with base query
    query = UnifiedProduct.query
    
    # Filter by product type if specified
    if product_type != 'all':
        query = query.filter_by(product_type=product_type)
    
    # Apply sorting
    if sort_by == 'vendor':
        if sort_dir == 'desc':
            query = query.order_by(UnifiedProduct.vendor.desc())
        else:
            query = query.order_by(UnifiedProduct.vendor)
    elif sort_by == 'price_low':
        query = query.order_by(UnifiedProduct.price_discounted)
    elif sort_by == 'price_high':
        query = query.order_by(UnifiedProduct.price_discounted.desc())
    elif sort_by == 'name':
        if sort_dir == 'desc':
            query = query.order_by(UnifiedProduct.product_name.desc())
        else:
            query = query.order_by(UnifiedProduct.product_name)
    
    # Execute query
    products = query.all()
    
    # For brand sorting (since brand is in JSON characteristics), we need to sort after query
    if sort_by == 'brand':
        products = sorted(products, 
                         key=lambda p: p.get_characteristics().get('brand', '').lower() if p.get_characteristics().get('brand') else '',
                         reverse=(sort_dir == 'desc'))
    
    return render_template('admin/products/index.html', 
                          products=products, 
                          current_type=product_type,
                          sort_by=sort_by,
                          sort_dir=sort_dir)

@admin_bp.route('/products/motherboards')
@login_required
@admin_required
def motherboards():
    sort_by = request.args.get('sort', None)
    sort_dir = request.args.get('dir', 'asc')
    return redirect(url_for('admin.products', type='motherboard', sort=sort_by, dir=sort_dir))

@admin_bp.route('/products/processors')
@login_required
@admin_required
def processors():
    sort_by = request.args.get('sort', None)
    sort_dir = request.args.get('dir', 'asc')
    return redirect(url_for('admin.products', type='processor', sort=sort_by, dir=sort_dir))

@admin_bp.route('/products/graphics_cards')
@login_required
@admin_required
def graphics_cards():
    sort_by = request.args.get('sort', None)
    sort_dir = request.args.get('dir', 'asc')
    return redirect(url_for('admin.products', type='graphics_card', sort=sort_by, dir=sort_dir))

@admin_bp.route('/products/rams')
@login_required
@admin_required
def rams():
    sort_by = request.args.get('sort', None)
    sort_dir = request.args.get('dir', 'asc')
    return redirect(url_for('admin.products', type='ram', sort=sort_by, dir=sort_dir))

@admin_bp.route('/products/hard_drives')
@login_required
@admin_required
def hard_drives():
    sort_by = request.args.get('sort', None)
    sort_dir = request.args.get('dir', 'asc')
    return redirect(url_for('admin.products', type='hard_drive', sort=sort_by, dir=sort_dir))

@admin_bp.route('/products/power_supplies')
@login_required
@admin_required
def power_supplies():
    sort_by = request.args.get('sort', None)
    sort_dir = request.args.get('dir', 'asc')
    return redirect(url_for('admin.products', type='power_supply', sort=sort_by, dir=sort_dir))

@admin_bp.route('/products/coolers')
@login_required
@admin_required
def coolers():
    sort_by = request.args.get('sort', None)
    sort_dir = request.args.get('dir', 'asc')
    return redirect(url_for('admin.products', type='cooler', sort=sort_by, dir=sort_dir))

@admin_bp.route('/products/cases')
@login_required
@admin_required
def cases():
    sort_by = request.args.get('sort', None)
    sort_dir = request.args.get('dir', 'asc')
    return redirect(url_for('admin.products', type='case', sort=sort_by, dir=sort_dir))

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    product_type = request.args.get('type', 'other')
    form = UnifiedProductForm()
    
    if form.validate_on_submit():
        product = UnifiedProduct(
            product_name=form.product_name.data,
            price_discounted=form.price_discounted.data,
            price_original=form.price_original.data,
            vendor=form.vendor.data,
            product_url=form.product_url.data,
            availability=True,
            product_type=product_type
        )
        
        # Process characteristics from the form
        try:
            additional_chars = request.form.get('additional_characteristics', '{}')
            characteristics = json.loads(additional_chars)
            
            # Add brand and model if provided
            if form.brand.data:
                characteristics['brand'] = form.brand.data
            if form.model.data:
                characteristics['model'] = form.model.data
                
        except json.JSONDecodeError:
            flash('Ошибка при обработке характеристик', 'danger')
            characteristics = {}
            if form.brand.data:
                characteristics['brand'] = form.brand.data
            if form.model.data:
                characteristics['model'] = form.model.data
        
        # Set images
        if form.image_url.data:
            product.set_images([form.image_url.data])
            
        # Set characteristics
        product.set_characteristics(characteristics)
        
        # Add to database
        db.session.add(product)
        db.session.commit()
        
        flash(f'Продукт "{product.product_name}" успешно добавлен!', 'success')
        return redirect(url_for('admin.products', type=product_type))
    
    return render_template('admin/products/add_product.html', form=form, product_type=product_type)

@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = UnifiedProduct.query.get_or_404(product_id)
    form = UnifiedProductForm()
    characteristics = product.get_characteristics()
    
    if form.validate_on_submit():
        # Update basic product information
        product.product_name = form.product_name.data
        product.price_discounted = form.price_discounted.data
        product.price_original = form.price_original.data
        product.vendor = form.vendor.data
        product.product_url = form.product_url.data
        
        # Process characteristics from the form
        try:
            additional_chars = request.form.get('additional_characteristics', '{}')
            updated_characteristics = json.loads(additional_chars)
        except json.JSONDecodeError:
            flash('Ошибка при обработке характеристик', 'danger')
            updated_characteristics = {}
        
        # Update images
        if form.image_url.data:
            product.set_images([form.image_url.data])
            
        # Update characteristics
        product.set_characteristics(updated_characteristics)
        
        # Update database
        db.session.commit()
        
        flash(f'Продукт "{product.product_name}" успешно обновлен!', 'success')
        return redirect(url_for('admin.products', type=product.product_type))
    
    # Pre-populate form with existing data
    form.product_name.data = product.product_name
    form.price_discounted.data = product.price_discounted
    form.price_original.data = product.price_original
    form.vendor.data = product.vendor
    form.product_url.data = product.product_url
    
    # Pre-populate image URL (first one if there are multiple)
    images = product.get_images()
    if images and len(images) > 0:
        form.image_url.data = images[0]
    
    return render_template('admin/products/edit_product.html', form=form, product=product)

@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = UnifiedProduct.query.get_or_404(product_id)
    product_type = product.product_type
    db.session.delete(product)
    db.session.commit()
    flash('Продукт успешно удален', 'success')
    return redirect(url_for('admin.products', type=product_type))

@admin_bp.route('/import')
@login_required
@admin_required
def import_data():
    return render_template('admin/import.html')

@admin_bp.route('/run_import', methods=['POST'])
@login_required
@admin_required
def run_import():
    import_type = request.form.get('import_type')
    
    if import_type == 'create_db':
        # Import and run the create_db script
        try:
            from app.utils.standardization.create_db import recreate_database
            recreate_database()
            flash('База данных успешно пересоздана', 'success')
        except Exception as e:
            flash(f'Ошибка при пересоздании базы данных: {str(e)}', 'danger')
    
    elif import_type == 'import_products':
        # Import and run the import_products script
        try:
            from app.utils.standardization.import_products import import_products
            import_products()
            flash('Продукты успешно импортированы', 'success')
        except Exception as e:
            flash(f'Ошибка при импорте продуктов: {str(e)}', 'danger')
    
    return redirect(url_for('admin.import_data'))

@admin_bp.route('/scrape', methods=['GET', 'POST'])
@login_required
@admin_required
def scrape():
    # Get existing parser results if available
    dns_results = []
    citilink_results = []
    env_citilink_category = os.environ.get('CATEGORY', '')
    dns_categories = []
    citilink_categories = []
    
    try:
        # Проверяем локальные данные DNS в папке data/
        project_root = Path(__file__).resolve().parent.parent.parent
        data_dir = project_root / "data"
        
        if data_dir.exists():
            # Ищем самый свежий файл локального парсера
            local_files = list(data_dir.glob("local_parser_data_*.json"))
            if local_files:
                latest_local_file = max(local_files, key=lambda f: f.stat().st_mtime)
                try:
                    with open(latest_local_file, 'r', encoding='utf-8') as f:
                        local_data = json.load(f)
                    
                    if isinstance(local_data, list) and local_data:
                        dns_results = local_data
                        
                        # Группируем по категориям
                        categories_count = {}
                        for product in local_data:
                            categories = product.get('categories', [])
                            for cat in categories:
                                cat_name = cat.get('name', '')
                                if cat_name and cat_name not in ['Комплектующие для ПК', 'Основные комплектующие для ПК']:
                                    if cat_name not in categories_count:
                                        categories_count[cat_name] = 0
                                    categories_count[cat_name] += 1
                        
                        # Создаем dns_categories для отображения
                        for cat_name, count in categories_count.items():
                            dns_categories.append({
                                'name': cat_name,
                                'count': count,
                                'file': str(latest_local_file),
                                'slug': cat_name.lower().replace(' ', '_')
                            })
                        
                        logger.info(f"Загружены локальные данные DNS: {len(local_data)} товаров из {len(categories_count)} категорий")
                        
                except Exception as e:
                    logger.error(f"Ошибка чтения локального файла DNS {latest_local_file}: {str(e)}")
            
            # Также проверяем основной файл product_data.json
            main_file = data_dir / "product_data.json"
            if main_file.exists() and not dns_results:
                try:
                    with open(main_file, 'r', encoding='utf-8') as f:
                        main_data = json.load(f)
                    
                    if isinstance(main_data, list) and main_data:
                        dns_results = main_data
                        logger.info(f"Загружены данные DNS из основного файла: {len(main_data)} товаров")
                        
                except Exception as e:
                    logger.error(f"Ошибка чтения основного файла DNS: {str(e)}")
        
        # Если локальные данные не найдены, проверяем старую структуру категорий
        if not dns_results:
            # Пробуем найти категории DNS в старой структуре
            dns_categories_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'DNS_parsing', 'categories')
            if os.path.exists(dns_categories_dir):
                category_files = glob.glob(os.path.join(dns_categories_dir, "product_data_*.json"))
                for cat_file in category_files:
                    cat_name = os.path.basename(cat_file).replace('product_data_', '').replace('.json', '')
                    try:
                        with open(cat_file, 'r', encoding='utf-8') as f:
                            cat_products = json.load(f)
                            
                            # Отображаемое имя категории DNS
                            display_name = cat_name
                            if 'videokarty' in cat_name.lower() or 'gpu' in cat_name.lower():
                                display_name = 'Видеокарты'
                            elif 'processor' in cat_name.lower() or 'cpu' in cat_name.lower():
                                display_name = 'Процессоры'
                            elif 'motherboard' in cat_name.lower() or 'materinskie' in cat_name.lower():
                                display_name = 'Материнские платы'
                            elif 'power' in cat_name.lower() or 'pitaniya' in cat_name.lower():
                                display_name = 'Блоки питания'
                            elif 'memory' in cat_name.lower() or 'pamyati' in cat_name.lower() or 'ram' in cat_name.lower():
                                display_name = 'Модули памяти'
                            elif 'case' in cat_name.lower() or 'korpus' in cat_name.lower():
                                display_name = 'Корпуса'
                            elif 'cooler' in cat_name.lower() or 'cooling' in cat_name.lower():
                                display_name = 'Кулеры для процессора'
                            elif 'ssd' in cat_name.lower():
                                display_name = 'SSD накопители'
                            elif 'hdd' in cat_name.lower() or 'hard' in cat_name.lower():
                                display_name = 'Жесткие диски'
                            else:
                                # Делаем первую букву заглавной
                                display_name = cat_name.replace('_', ' ').replace('-', ' ').title()
                            
                            dns_categories.append({
                                'name': display_name,
                                'count': len(cat_products),
                                'file': cat_file,
                                'slug': cat_name
                            })
                            # Add these products to the overall results
                            dns_results.extend(cat_products)
                    except Exception as e:
                        logger.error(f'Ошибка чтения категории DNS {cat_name}: {str(e)}')
        
        # Если все еще нет результатов, пробуем найти основной файл product_data.json из старой структуры
        if not dns_categories:
            dns_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'DNS_parsing', 'product_data.json')
            if os.path.exists(dns_file_path):
                with open(dns_file_path, 'r', encoding='utf-8') as f:
                    dns_results = json.load(f)
                    # Проверяем и обрабатываем формат данных
                    for item in dns_results:
                        # Добавляем поля, если их нет
                        if 'price_discounted' not in item and 'price_original' not in item:
                            if 'price' in item:
                                item['price_original'] = item['price']
                                item['price_discounted'] = item['price']
                        
                        # Проверяем наличие категории
                        if 'categories' not in item or not item['categories']:
                            item['categories'] = []
                            
                        # Логгируем загруженные данные
                        logger.info(f"Загружен продукт DNS: {item.get('name')}")
            else:
                logger.warning(f"Файл результатов DNS парсера не найден ни в локальных данных, ни в старой структуре")
                
    except Exception as e:
        logger.error(f'Ошибка чтения результатов DNS парсера: {str(e)}')
        flash(f'Ошибка чтения результатов DNS парсера: {str(e)}', 'warning')
    
    try:
        # Проверяем сначала категории Citilink
        citilink_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'Citi_parser', 'data')
        if os.path.exists(citilink_data_dir):
            # Получаем список категорий
            for category_dir in os.listdir(citilink_data_dir):
                cat_dir_path = os.path.join(citilink_data_dir, category_dir)
                if os.path.isdir(cat_dir_path):
                    cat_products_file = os.path.join(cat_dir_path, 'Товары.json')
                    if os.path.exists(cat_products_file):
                        try:
                            with open(cat_products_file, 'r', encoding='utf-8') as f:
                                cat_products = json.load(f)
                                # Отображаемое имя категории
                                display_name = category_dir
                                if category_dir == 'videokarty':
                                    display_name = 'Видеокарты'
                                elif category_dir == 'processory':
                                    display_name = 'Процессоры'
                                elif category_dir == 'materinskie-platy':
                                    display_name = 'Материнские платы'
                                elif category_dir == 'bloki-pitaniya':
                                    display_name = 'Блоки питания'
                                elif category_dir == 'moduli-pamyati':
                                    display_name = 'Модули памяти'
                                elif category_dir == 'korpusa':
                                    display_name = 'Корпуса'
                                elif category_dir == 'sistemy-ohlazhdeniya-processora':
                                    display_name = 'Кулеры для процессора'
                                elif category_dir == 'ssd-nakopiteli':
                                    display_name = 'SSD накопители'
                                elif category_dir == 'zhestkie-diski':
                                    display_name = 'Жесткие диски'
                                
                                citilink_categories.append({
                                    'name': display_name,
                                    'count': len(cat_products),
                                    'file': cat_products_file,
                                    'slug': category_dir
                                })
                                # Добавляем продукты в общий список
                                citilink_results.extend(cat_products)
                        except Exception as e:
                            logger.error(f'Ошибка чтения категории Citilink {category_dir}: {str(e)}')
        
        # Если категории не найдены, пробуем найти основной файл Товары.json
        if not citilink_categories:
            citilink_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'Citi_parser', 'Товары.json')
            if os.path.exists(citilink_file_path):
                with open(citilink_file_path, 'r', encoding='utf-8') as f:
                    try:
                        # Try to load the file directly
                        citilink_results = json.load(f)
                    except json.JSONDecodeError:
                        # If that fails, read content and then load
                        f.seek(0)  # Go back to the beginning of the file
                        content = f.read()
                        if content.endswith(',\n]'):
                            content = content.replace(',\n]', '\n]')
                        citilink_results = json.loads(content)
                    
                    # Debugging information
                    logger.info(f"Загружено {len(citilink_results)} товаров Citilink")
                    if len(citilink_results) > 0:
                        # Process each item to ensure consistent structure
                        for item in citilink_results:
                            # Make sure required fields exist
                            if 'categories' not in item or not item['categories']:
                                item['categories'] = []
                        
                        logger.info(f"Пример первого товара: {citilink_results[0].get('name')} - {citilink_results[0].get('price')}")
            else:
                logger.warning(f"Файл результатов Citilink парсера не найден по пути: {citilink_file_path}")
    except Exception as e:
        logger.error(f'Ошибка чтения результатов Citilink парсера: {str(e)}')
        flash(f'Ошибка чтения результатов Citilink парсера: {str(e)}', 'warning')
    
    # Try to read category from .env file if not in environment
    if not env_citilink_category:
        try:
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('CATEGORY='):
                            env_citilink_category = line.strip().split('=', 1)[1]
                            break
        except Exception as e:
            logger.error(f"Error reading .env file: {e}")
            print(f"Error reading .env file: {e}")
    
    return render_template('admin/scrape.html', 
                           dns_results=dns_results, 
                           citilink_results=citilink_results,
                           env_citilink_category=env_citilink_category,
                           dns_categories=dns_categories,
                           citilink_categories=citilink_categories)

@admin_bp.route('/run-dns-parser', methods=['POST'])
@login_required
@admin_required
def run_dns_parser():
    category = request.form.get('dns_category', '')
    max_items = request.form.get('dns_max_items', '20')
    
    try:
        # Get path to DNS parser directory
        dns_parser_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'DNS_parsing')
        
        # Set MAX_ITEMS environment variable
        os.environ['MAX_ITEMS'] = max_items
        
        # Change to DNS parser directory
        current_dir = os.getcwd()
        os.chdir(dns_parser_dir)
        
        # Add the DNS parser directory to Python path
        if dns_parser_dir not in sys.path:
            sys.path.insert(0, dns_parser_dir)
        
        # Run the DNS parser with the selected category
        try:
            # Use the system Python interpreter
            python_executable = sys.executable
            
            if category:
                flash(f'Парсер DNS будет запущен для категории "{category}"', 'info')
                # Run script with category parameter
                subprocess.run([python_executable, 'main.py', category, max_items], check=True, cwd=dns_parser_dir)
            else:
                flash('Парсер DNS будет запущен для всех категорий', 'info')
                # Run script without category parameter
                subprocess.run([python_executable, 'main.py'], check=True, cwd=dns_parser_dir)
        except Exception as e:
            flash(f'Парсер DNS завершился с ошибкой: {str(e)}', 'warning')
        
        # Change back to original directory
        os.chdir(current_dir)
        
        # Read results - check both main file and category files
        try:
            # Check for category-specific files first
            categories_dir = os.path.join(dns_parser_dir, 'categories')
            total_products = 0
            category_files_found = False
            
            if os.path.exists(categories_dir):
                category_files = glob.glob(os.path.join(categories_dir, "product_data_*.json"))
                if category_files:
                    category_files_found = True
                    for cat_file in category_files:
                        cat_name = os.path.basename(cat_file).replace('product_data_', '').replace('.json', '')
                        with open(cat_file, 'r', encoding='utf-8') as f:
                            cat_results = json.load(f)
                            total_products += len(cat_results)
                            logger.info(f"Категория {cat_name}: {len(cat_results)} товаров")
            
            # Check main file if needed
            if not category_files_found:
                items_file = os.path.join(dns_parser_dir, 'product_data.json')
                if os.path.exists(items_file):
                    with open(items_file, 'r', encoding='utf-8') as f:
                        results = json.load(f)
                        total_products = len(results)
            
            if total_products > 0:
                flash(f'Парсер DNS успешно выполнен. Получено {total_products} товаров.', 'success')
                
                # Ensure products are imported after parsing
                try:
                    logger.info("Запуск импорта товаров после парсинга DNS")
                    from app.utils.standardization.import_products import import_products
                    import_products()
                    logger.info("Импорт товаров успешно завершен")
                    flash('Товары успешно импортированы в базу данных', 'success')
                except Exception as import_error:
                    logger.error(f"Ошибка при импорте товаров: {import_error}")
                    flash(f'Возникла ошибка при импорте товаров: {str(import_error)}', 'warning')
            else:
                flash('Файлы с результатами не найдены или пусты. Проверьте парсер.', 'warning')
        except Exception as f:
            flash(f'Не удалось прочитать результаты парсера DNS: {str(f)}', 'warning')
    except Exception as e:
        flash(f'Ошибка при запуске парсера DNS: {str(e)}', 'danger')
    
    return redirect(url_for('admin.scrape'))

@admin_bp.route('/run-citilink-parser', methods=['POST'])
@login_required
@admin_required
def run_citilink_parser():
    category = request.form.get('citilink_category', '')
    
    if not category:
        flash('Необходимо выбрать категорию для парсинга Citilink', 'warning')
        return redirect(url_for('admin.scrape'))
    
    try:
        # Get path to Citilink parser directory
        citilink_parser_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'Citi_parser')
        
        # Create the .env file with only the selected category (cross-platform way)
        env_file_path = os.path.join(citilink_parser_dir, ".env")
        env_content = f"CATEGORY={category}"
        
        # Write .env file using Python (cross-platform)
        try:
            with open(env_file_path, 'w', encoding='utf-8') as env_file:
                env_file.write(env_content)
            logger.info(f"Created .env file with category: {category}")
        except Exception as env_error:
            logger.error(f"Failed to create .env file: {env_error}")
            flash(f'Ошибка создания .env файла: {str(env_error)}', 'danger')
            return redirect(url_for('admin.scrape'))
        
        # Set environment variable for the current process
        os.environ['CATEGORY'] = category
        
        # Change to Citilink parser directory
        current_dir = os.getcwd()
        os.chdir(citilink_parser_dir)
        
        # Add the Citilink parser directory to Python path
        if citilink_parser_dir not in sys.path:
            sys.path.insert(0, citilink_parser_dir)
        
        # Run the Citilink parser
        try:
            # Use the system Python interpreter
            python_executable = sys.executable
            
            flash(f'Парсер Citilink будет запущен для категории "{category}"', 'info')
            # Run the script
            subprocess.run([python_executable, 'main.py'], check=True, cwd=citilink_parser_dir)
        except Exception as e:
            flash(f'Парсер Citilink завершился с ошибкой: {str(e)}', 'warning')
        
        # Change back to original directory
        os.chdir(current_dir)
        
        # Read results with improved error handling
        try:
            items_file = os.path.join(citilink_parser_dir, 'data', category, 'Товары.json')
            if os.path.exists(items_file):
                with open(items_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                    # Handle empty or malformed JSON files
                    if not content:
                        logger.warning(f"Empty JSON file: {items_file}")
                        flash('Файл с результатами пуст. Возможно, парсер не смог получить данные.', 'warning')
                        return redirect(url_for('admin.scrape'))
                    
                    # Fix common JSON issues
                    if content.endswith(','):
                        content = content[:-1]  # Remove trailing comma
                    
                    if content.endswith(',\n]'):
                        content = content.replace(',\n]', '\n]')
                    
                    if content.endswith(',]'):
                        content = content.replace(',]', ']')
                    
                    # Try to parse JSON
                    try:
                        results = json.loads(content)
                    except json.JSONDecodeError as json_error:
                        logger.error(f"JSON decode error in {items_file}: {json_error}")
                        logger.error(f"File content preview: {content[:200]}...")
                        flash(f'Ошибка парсинга JSON файла: {str(json_error)}. Проверьте корректность данных.', 'warning')
                        return redirect(url_for('admin.scrape'))
                
                if results:
                    flash(f'Парсер Citilink успешно выполнен. Получено {len(results)} товаров.', 'success')
                    
                    # Ensure products are imported after parsing
                    try:
                        logger.info("Запуск импорта товаров после парсинга Citilink")
                        from app.utils.standardization.import_products import import_products
                        import_products()
                        logger.info("Импорт товаров успешно завершен")
                        flash('Товары успешно импортированы в базу данных', 'success')
                    except Exception as import_error:
                        logger.error(f"Ошибка при импорте товаров: {import_error}")
                        flash(f'Возникла ошибка при импорте товаров: {str(import_error)}', 'warning')
                else:
                    flash('Парсер выполнен, но не получено товаров. Проверьте настройки парсера.', 'warning')
            else:
                # Try alternative file location
                alt_items_file = os.path.join(citilink_parser_dir, 'Товары.json')
                if os.path.exists(alt_items_file):
                    flash('Файл с результатами найден в альтернативном расположении', 'info')
                    # Process alternative file with same logic...
                else:
                    flash('Файл с результатами не найден. Проверьте парсер.', 'warning')
        except Exception as f:
            logger.error(f"Error reading Citilink parser results: {f}")
            flash(f'Не удалось прочитать результаты парсера Citilink: {str(f)}', 'warning')
    except Exception as e:
        logger.error(f"Error running Citilink parser: {e}")
        flash(f'Ошибка при запуске парсера Citilink: {str(e)}', 'danger')
    
    return redirect(url_for('admin.scrape'))

@admin_bp.route('/view-logs')
@login_required
@admin_required
def view_logs():
    """Просмотр логов парсеров"""
    log_file = request.args.get('file', 'dns_parser.log')
    
    # Список разрешенных файлов логов
    allowed_logs = ['dns_parser.log', 'app/utils/Citi_parser/parser.log']
    
    if log_file not in allowed_logs:
        return jsonify({"error": "File not allowed"}), 403
    
    try:
        # Определяем полный путь к файлу лога
        if log_file.startswith('app/'):
            log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', log_file)
        else:
            log_path = log_file
        
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Возвращаем последние 500 строк, если файл очень большой
            lines = content.split('\n')
            if len(lines) > 500:
                content = '\n'.join(lines[-500:])
            
            return jsonify({"content": content})
        else:
            return jsonify({"error": "Log file not found"})
    except Exception as e:
        return jsonify({"error": str(e)})

@admin_bp.route('/clear-dns-parser-results')
@login_required
@admin_required
def clear_dns_parser_results():
    """Очистить результаты DNS парсера"""
    try:
        # Получаем путь к файлу с результатами
        dns_parser_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'DNS_parsing')
        product_data_file = os.path.join(dns_parser_dir, 'product_data.json')
        urls_file = os.path.join(dns_parser_dir, 'urls.txt')
        
        # Очищаем файл с результатами
        if os.path.exists(product_data_file):
            with open(product_data_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)
            logger.info("Файл с результатами DNS парсера очищен")
            
        # Очищаем файл с URL-адресами
        if os.path.exists(urls_file):
            with open(urls_file, 'w', encoding='utf-8') as f:
                f.write("")
            logger.info("Файл с URL-адресами DNS парсера очищен")
        
        # Очищаем файлы категорий
        categories_dir = os.path.join(dns_parser_dir, 'categories')
        if os.path.exists(categories_dir):
            category_files = glob.glob(os.path.join(categories_dir, "product_data_*.json"))
            for cat_file in category_files:
                cat_name = os.path.basename(cat_file).replace('product_data_', '').replace('.json', '')
                with open(cat_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=4)
                logger.info(f"Файл категории {cat_name} очищен")
            
        flash('Результаты DNS парсера успешно очищены', 'success')
    except Exception as e:
        logger.error(f"Ошибка при очистке результатов DNS парсера: {e}")
        flash(f'Ошибка при очистке результатов: {str(e)}', 'danger')
        
    return redirect(url_for('admin.scrape'))

@admin_bp.route('/clear-citilink-parser-results')
@login_required
@admin_required
def clear_citilink_parser_results():
    """Очистить результаты Citilink парсера"""
    try:
        # Получаем путь к файлу с результатами
        citilink_parser_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'Citi_parser')
        products_file = os.path.join(citilink_parser_dir, 'Товары.json')
        reviews_file = os.path.join(citilink_parser_dir, 'Отзывы.json')
        
        # Очищаем файлы с результатами
        if os.path.exists(products_file):
            with open(products_file, 'w', encoding='utf-8') as f:
                f.write("[]")
            logger.info("Файл с товарами Citilink парсера очищен")
            
        if os.path.exists(reviews_file):
            with open(reviews_file, 'w', encoding='utf-8') as f:
                f.write("[]")
            logger.info("Файл с отзывами Citilink парсера очищен")
            
        # Очищаем файлы категорий
        data_dir = os.path.join(citilink_parser_dir, 'data')
        if os.path.exists(data_dir):
            for category_dir in os.listdir(data_dir):
                category_path = os.path.join(data_dir, category_dir)
                if os.path.isdir(category_path):
                    # Очищаем файлы категории
                    cat_products_file = os.path.join(category_path, 'Товары.json')
                    cat_reviews_file = os.path.join(category_path, 'Отзывы.json')
                    cat_articles_file = os.path.join(category_path, 'Обзоры.json')
                    
                    for file_path in [cat_products_file, cat_reviews_file, cat_articles_file]:
                        if os.path.exists(file_path):
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write("[]")
                            logger.info(f"Файл {os.path.basename(file_path)} в категории {category_dir} очищен")
            
        flash('Результаты Citilink парсера успешно очищены', 'success')
    except Exception as e:
        logger.error(f"Ошибка при очистке результатов Citilink парсера: {e}")
        flash(f'Ошибка при очистке результатов: {str(e)}', 'danger')
        
    return redirect(url_for('admin.scrape'))

@admin_bp.route('/run-all-parsers')
@login_required
@admin_required
def run_all_parsers():
    """Запустить оба парсера последовательно"""
    try:
        # Сначала запускаем парсер DNS
        dns_parser_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'DNS_parsing')
        python_executable = sys.executable
        
        # Создаем директорию для категорий DNS, если её нет
        dns_categories_dir = os.path.join(dns_parser_dir, "categories")
        if not os.path.exists(dns_categories_dir):
            os.makedirs(dns_categories_dir)
            logger.info(f"Создана директория для категорий DNS: {dns_categories_dir}")
        
        # Устанавливаем переменные окружения
        os.environ['MAX_ITEMS'] = '20'  # По умолчанию парсим 20 товаров
        
        # Запускаем DNS парсер
        logger.info("Запуск DNS парсера")
        current_dir = os.getcwd()
        os.chdir(dns_parser_dir)
        
        subprocess.run([python_executable, 'main.py'], check=True, cwd=dns_parser_dir)
        
        os.chdir(current_dir)
        
        # Затем запускаем парсер Citilink
        citilink_parser_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'Citi_parser')
        
        # Получаем список категорий для парсинга Citilink
        categories = ["videokarty", "processory", "materinskie-platy", "operativnaya-pamyat", "bloki-pitaniya"]
        
        for category in categories:
            # Создаем .env файл с категорией для Citilink парсера
            env_setup_cmd = f'Set-Content -Path "{os.path.join(citilink_parser_dir, ".env")}" -Value "CATEGORY={category}"'
            subprocess.run(['powershell', '-Command', env_setup_cmd], check=True)
            
            # Устанавливаем переменную окружения
            os.environ['CATEGORY'] = category
            
            logger.info(f"Запуск Citilink парсера для категории: {category}")
            os.chdir(citilink_parser_dir)
            
            # Запускаем парсер
            subprocess.run([python_executable, 'main.py'], check=True, cwd=citilink_parser_dir)
            
            # Возвращаемся в исходную директорию между запусками
            os.chdir(current_dir)
        
        # Убедимся, что товары импортированы после завершения всех парсеров
        try:
            logger.info("Запуск импорта товаров после завершения всех парсеров")
            from app.utils.standardization.import_products import import_products
            import_products()
            logger.info("Импорт товаров успешно завершен")
            flash('Все парсеры успешно выполнены и товары импортированы в базу данных', 'success')
        except Exception as import_error:
            logger.error(f"Ошибка при импорте товаров: {import_error}")
            flash(f'Парсеры выполнены, но возникла ошибка при импорте товаров: {str(import_error)}', 'warning')
    except Exception as e:
        logger.error(f"Ошибка при запуске парсеров: {e}")
        flash(f'Ошибка при запуске парсеров: {str(e)}', 'danger')
        
    return redirect(url_for('admin.scrape'))

@admin_bp.route('/api/citilink-category-data')
@login_required
@admin_required
def get_citilink_category_data():
    """API endpoint для получения данных определенной категории из Citilink парсера"""
    category = request.args.get('category', '')
    
    try:
        # Получаем путь к директории Citilink парсера
        citilink_parser_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'Citi_parser')
        
        # Если указана категория, пытаемся загрузить данные из категории
        if category:
            category_file = os.path.join(citilink_parser_dir, 'data', category, 'Товары.json')
            
            if os.path.exists(category_file):
                with open(category_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Обработка потенциальных проблем с форматом JSON
                    if content.endswith(',\n]'):
                        content = content.replace(',\n]', '\n]')
                    products = json.loads(content)
                    return jsonify({"success": True, "products": products, "category": category})
            else:
                # Если файл категории не найден, сообщаем об ошибке
                return jsonify({"success": False, "error": f"Файл с данными для категории {category} не найден"}), 404
        
        # Если категория не указана, загружаем данные из основного файла
        main_file = os.path.join(citilink_parser_dir, 'Товары.json')
        if os.path.exists(main_file):
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.endswith(',\n]'):
                    content = content.replace(',\n]', '\n]')
                products = json.loads(content)
                return jsonify({"success": True, "products": products, "category": "all"})
        else:
            # Если основной файл не найден, сообщаем об ошибке
            return jsonify({"success": False, "error": "Файл с общими данными не найден"}), 404
    
    except Exception as e:
        logger.error(f"Ошибка при получении данных категории: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@admin_bp.route('/download-parser-results/<parser>')
@login_required
@admin_required
def download_parser_results(parser):
    """Download parser results for the specified parser."""
    if parser == 'dns':
        file_path = os.path.join(current_app.root_path, 'utils', 'DNS_parsing', 'Товары.json')
        filename = 'dns_products.json'
    elif parser == 'citilink':
        file_path = os.path.join(current_app.root_path, 'utils', 'Citi_parser', 'Товары.json')
        filename = 'citilink_products.json'
    else:
        flash('Неверный тип парсера', 'error')
        return redirect(url_for('admin.scrape'))
    
    if not os.path.exists(file_path):
        flash(f'Файл с результатами парсера {parser} не найден', 'error')
        return redirect(url_for('admin.scrape'))
    
    try:
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
    except Exception as e:
        flash(f'Ошибка при скачивании файла: {str(e)}', 'error')
        return redirect(url_for('admin.scrape'))

@admin_bp.route('/stop-citilink-parser', methods=['POST'])
@login_required
@admin_required
def stop_citilink_parser():
    """Остановка парсера Citilink с сохранением данных"""
    try:
        import psutil
        import signal
        from app.utils.standardization.import_products import import_products_from_data
        
        # Найти процессы парсера Citilink
        stopped_processes = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Проверяем командную строку процесса
                cmdline = proc.info['cmdline']
                if cmdline and any('Citi_parser' in str(cmd) or 'main.py' in str(cmd) for cmd in cmdline):
                    if any('python' in str(cmd).lower() for cmd in cmdline):
                        logger.info(f"Останавливаю процесс парсера Citilink: PID {proc.info['pid']}")
                        proc.terminate()  # Мягкая остановка
                        stopped_processes += 1
                        
                        # Если процесс не остановился через 5 секунд, принудительно завершаем
                        try:
                            proc.wait(timeout=5)
                        except psutil.TimeoutExpired:
                            proc.kill()  # Принудительная остановка
                            
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Импортируем собранные данные после остановки
        imported_count = 0
        try:
            # Ищем все файлы данных Citilink
            citilink_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'Citi_parser', 'data')
            if os.path.exists(citilink_data_dir):
                for category_dir in os.listdir(citilink_data_dir):
                    cat_dir_path = os.path.join(citilink_data_dir, category_dir)
                    if os.path.isdir(cat_dir_path):
                        cat_products_file = os.path.join(cat_dir_path, 'Товары.json')
                        if os.path.exists(cat_products_file):
                            try:
                                with open(cat_products_file, 'r', encoding='utf-8') as f:
                                    products = json.load(f)
                                    if products:
                                        # Импортируем продукты
                                        result = import_products_from_data(products, source=f'citilink_{category_dir}')
                                        imported_count += result.get('added_count', 0)
                                        logger.info(f"Импортировано {result.get('added_count', 0)} товаров из категории {category_dir}")
                            except Exception as e:
                                logger.error(f"Ошибка импорта категории {category_dir}: {e}")
                                
        except Exception as import_error:
            logger.error(f"Ошибка при импорте данных: {import_error}")
        
        if stopped_processes > 0:
            if imported_count > 0:
                flash(f'Остановлено {stopped_processes} процессов парсера Citilink. Импортировано {imported_count} товаров в базу данных.', 'success')
            else:
                flash(f'Остановлено {stopped_processes} процессов парсера Citilink. Данные для импорта не найдены.', 'warning')
        else:
            if imported_count > 0:
                flash(f'Активные процессы парсера Citilink не найдены. Импортировано {imported_count} товаров в базу данных.', 'info')
            else:
                flash('Активные процессы парсера Citilink не найдены. Данные для импорта отсутствуют.', 'info')
            
    except ImportError:
        flash('Библиотека psutil не установлена. Невозможно остановить процессы.', 'warning')
    except Exception as e:
        logger.error(f"Ошибка при остановке парсера Citilink: {e}")
        flash(f'Ошибка при остановке парсера Citilink: {str(e)}', 'danger')
        
    return redirect(url_for('admin.scrape'))

@admin_bp.route('/stop-dns-parser', methods=['POST'])
@login_required
@admin_required
def stop_dns_parser():
    """Остановка парсера DNS"""
    try:
        import psutil
        
        # Найти процессы парсера DNS
        stopped_processes = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any('DNS_parsing' in str(cmd) or 'dns_parser' in str(cmd) for cmd in cmdline):
                    if any('python' in str(cmd).lower() for cmd in cmdline):
                        logger.info(f"Останавливаю процесс парсера DNS: PID {proc.info['pid']}")
                        proc.terminate()
                        stopped_processes += 1
                        
                        try:
                            proc.wait(timeout=5)
                        except psutil.TimeoutExpired:
                            proc.kill()
                            
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if stopped_processes > 0:
            flash(f'Остановлено {stopped_processes} процессов парсера DNS', 'success')
        else:
            flash('Активные процессы парсера DNS не найдены', 'info')
            
    except ImportError:
        flash('Библиотека psutil не установлена. Невозможно остановить процессы.', 'warning')
    except Exception as e:
        logger.error(f"Ошибка при остановке парсера DNS: {e}")
        flash(f'Ошибка при остановке парсера: {str(e)}', 'danger')
    
    return redirect(url_for('admin.scrape'))

@admin_bp.route('/fix-citilink-json', methods=['POST'])
@login_required
@admin_required
def fix_citilink_json():
    """Исправление проблемных JSON файлов Citilink"""
    try:
        import glob
        
        citilink_parser_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'Citi_parser')
        data_dir = os.path.join(citilink_parser_dir, 'data')
        
        if not os.path.exists(data_dir):
            flash('Папка с данными Citilink не найдена', 'warning')
            return redirect(url_for('admin.scrape'))
        
        fixed_files = 0
        removed_files = 0
        
        # Найти все JSON файлы
        json_pattern = os.path.join(data_dir, '**', '*.json')
        json_files = glob.glob(json_pattern, recursive=True)
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                # Если файл пустой или содержит только пробелы
                if not content or content.isspace():
                    logger.info(f"Удаляю пустой файл: {json_file}")
                    os.remove(json_file)
                    removed_files += 1
                    continue
                
                # Попытка парсинга JSON
                try:
                    json.loads(content)
                    # Файл корректный, пропускаем
                    continue
                except json.JSONDecodeError:
                    # Файл некорректный, пытаемся исправить
                    logger.info(f"Исправляю файл: {json_file}")
                    
                    # Убираем висячие запятые
                    if content.endswith(','):
                        content = content[:-1]
                    
                    if content.endswith(',\n]'):
                        content = content.replace(',\n]', '\n]')
                    
                    if content.endswith(',]'):
                        content = content.replace(',]', ']')
                    
                    # Пытаемся снова распарсить
                    try:
                        json.loads(content)
                        # Записываем исправленный файл
                        with open(json_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        fixed_files += 1
                        logger.info(f"Файл исправлен: {json_file}")
                    except json.JSONDecodeError:
                        # Если всё ещё не удается, удаляем файл
                        logger.warning(f"Не удалось исправить файл, удаляю: {json_file}")
                        os.remove(json_file)
                        removed_files += 1
                        
            except Exception as file_error:
                logger.error(f"Ошибка обработки файла {json_file}: {file_error}")
        
        if fixed_files > 0 or removed_files > 0:
            flash(f'Обработка завершена: исправлено {fixed_files} файлов, удалено {removed_files} файлов', 'success')
        else:
            flash('Проблемные файлы не найдены', 'info')
            
    except Exception as e:
        logger.error(f"Ошибка при исправлении JSON файлов: {e}")
        flash(f'Ошибка при исправлении файлов: {str(e)}', 'danger')
    
    return redirect(url_for('admin.scrape'))

@admin_bp.route('/clear-database', methods=['POST'])
@login_required
@admin_required
def clear_database():
    """Очистка всех данных о продуктах из базы данных"""
    try:
        # Импортируем модель Configuration
        from app.models.models import Configuration
        
        # Сначала удаляем все конфигурации (чтобы избежать ошибок внешних ключей)
        Configuration.query.delete()
        
        # Затем удаляем все продукты
        UnifiedProduct.query.delete()
        
        # Подтверждаем изменения
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'База данных успешно очищена'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при очистке базы данных: {e}")
        return jsonify({
            'success': False,
            'message': f'Ошибка при очистке базы данных: {str(e)}'
        }), 500

@admin_bp.route('/api/product-arrivals')
@login_required
@admin_required
def get_product_arrivals():
    """API endpoint для получения информации о поступлениях товаров"""
    try:
        # Получаем статистику по типам товаров
        total_products = UnifiedProduct.query.count()
        
        # Статистика по категориям
        categories_stats = []
        product_types = ['processor', 'graphics_card', 'motherboard', 'ram', 'hard_drive', 'power_supply', 'cooler', 'case']
        
        for product_type in product_types:
            count = UnifiedProduct.query.filter_by(product_type=product_type).count()
            if count > 0:
                # Получаем последний добавленный товар этого типа
                last_product = UnifiedProduct.query.filter_by(product_type=product_type).order_by(UnifiedProduct.id.desc()).first()
                
                # Определяем русское название
                type_names = {
                    'processor': 'Процессоры',
                    'graphics_card': 'Видеокарты', 
                    'motherboard': 'Материнские платы',
                    'ram': 'Оперативная память',
                    'hard_drive': 'Жесткие диски',
                    'power_supply': 'Блоки питания',
                    'cooler': 'Кулеры',
                    'case': 'Корпуса'
                }
                
                categories_stats.append({
                    'type': product_type,
                    'name': type_names.get(product_type, product_type.title()),
                    'count': count,
                    'last_id': last_product.id if last_product else None,
                    'last_name': last_product.product_name if last_product else None
                })
        
        # Получаем последние 10 добавленных товаров
        recent_products = UnifiedProduct.query.order_by(UnifiedProduct.id.desc()).limit(10).all()
        recent_list = []
        for product in recent_products:
            recent_list.append({
                'id': product.id,
                'name': product.product_name[:50] + '...' if len(product.product_name) > 50 else product.product_name,
                'type': product.product_type,
                'vendor': product.vendor,
                'price': product.price_discounted or product.price_original or 0
            })
        
        # Проверяем наличие файлов парсеров для определения последних импортов
        import_info = []
        
        # Проверяем DNS файлы
        dns_parser_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'DNS_parsing')
        dns_categories_dir = os.path.join(dns_parser_dir, 'categories')
        if os.path.exists(dns_categories_dir):
            category_files = glob.glob(os.path.join(dns_categories_dir, "product_data_*.json"))
            for cat_file in category_files:
                try:
                    file_stat = os.stat(cat_file)
                    import_time = datetime.fromtimestamp(file_stat.st_mtime)
                    cat_name = os.path.basename(cat_file).replace('product_data_', '').replace('.json', '')
                    
                    with open(cat_file, 'r', encoding='utf-8') as f:
                        cat_products = json.load(f)
                    
                    import_info.append({
                        'source': 'DNS',
                        'category': cat_name.replace('_', ' ').title(),
                        'count': len(cat_products),
                        'last_update': import_time.strftime('%d.%m.%Y %H:%M'),
                        'timestamp': import_time.timestamp()
                    })
                except Exception as e:
                    logger.error(f"Ошибка чтения файла {cat_file}: {e}")
        
        # Проверяем Citilink файлы
        citilink_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'Citi_parser', 'data')
        if os.path.exists(citilink_data_dir):
            for category_dir in os.listdir(citilink_data_dir):
                cat_dir_path = os.path.join(citilink_data_dir, category_dir)
                if os.path.isdir(cat_dir_path):
                    cat_products_file = os.path.join(cat_dir_path, 'Товары.json')
                    if os.path.exists(cat_products_file):
                        try:
                            file_stat = os.stat(cat_products_file)
                            import_time = datetime.fromtimestamp(file_stat.st_mtime)
                            
                            with open(cat_products_file, 'r', encoding='utf-8') as f:
                                cat_products = json.load(f)
                            
                            # Определяем читаемое имя категории
                            display_names = {
                                'videokarty': 'Видеокарты',
                                'processory': 'Процессоры',
                                'materinskie-platy': 'Материнские платы',
                                'bloki-pitaniya': 'Блоки питания',
                                'moduli-pamyati': 'Модули памяти',
                                'korpusa': 'Корпуса',
                                'sistemy-ohlazhdeniya-processora': 'Кулеры',
                                'ssd-nakopiteli': 'SSD накопители',
                                'zhestkie-diski': 'Жесткие диски'
                            }
                            
                            import_info.append({
                                'source': 'Citilink',
                                'category': display_names.get(category_dir, category_dir.title()),
                                'count': len(cat_products),
                                'last_update': import_time.strftime('%d.%m.%Y %H:%M'),
                                'timestamp': import_time.timestamp()
                            })
                        except Exception as e:
                            logger.error(f"Ошибка чтения файла Citilink {cat_products_file}: {e}")
        
        # Сортируем импорты по времени (новые сначала)
        import_info.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'total_products': total_products,
            'categories_stats': categories_stats,
            'recent_products': recent_list,
            'import_history': import_info[:20]  # Последние 20 импортов
        })
    except Exception as e:
        logger.error(f"Ошибка получения информации о поступлениях: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500 