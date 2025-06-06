from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from app import db
from app.models.models import User, UnifiedProduct
from app.forms.admin import UnifiedProductForm
from app.utils.price_comparison import run_price_comparison
from functools import wraps
from datetime import datetime
import os
import json
import subprocess
import sys
from app.utils.DNS_parsing import main as dns_parser
import logging
import glob

# Настройка логирования
logger = logging.getLogger('admin_panel')

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Добавляем фильтр для получения текущей даты и времени
@admin_bp.app_template_filter('now')
def _jinja2_filter_now():
    return datetime.now()


# Декоратор для проверки прав администратора
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('У вас нет прав администратора для доступа к этой странице', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

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
        # Пробуем найти категории DNS
        dns_categories_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'DNS_parsing', 'categories')
        if os.path.exists(dns_categories_dir):
            category_files = glob.glob(os.path.join(dns_categories_dir, "product_data_*.json"))
            for cat_file in category_files:
                cat_name = os.path.basename(cat_file).replace('product_data_', '').replace('.json', '')
                try:
                    with open(cat_file, 'r', encoding='utf-8') as f:
                        cat_products = json.load(f)
                        dns_categories.append({
                            'name': cat_name,
                            'count': len(cat_products),
                            'file': cat_file
                        })
                        # Add these products to the overall results
                        dns_results.extend(cat_products)
                except Exception as e:
                    logger.error(f'Ошибка чтения категории DNS {cat_name}: {str(e)}')
        
        # Если категории не найдены, пробуем найти основной файл product_data.json
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
                logger.warning(f"Файл результатов DNS парсера не найден по пути: {dns_file_path}")
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
        
        # Create the .env file with only the selected category
        env_content = f"CATEGORY={category}"
        
        # Create a command to directly run the PowerShell command to create/update .env file
        env_setup_cmd = f'Set-Content -Path "{os.path.join(citilink_parser_dir, ".env")}" -Value "CATEGORY={category}"'
        
        # Run the PowerShell command to create/update .env file
        subprocess.run(['powershell', '-Command', env_setup_cmd], check=True)
        
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
        
        # Read results
        try:
            items_file = os.path.join(citilink_parser_dir, 'Товары.json')
            if os.path.exists(items_file):
                with open(items_file, 'r', encoding='utf-8') as f:
                    try:
                        # Try to load the file directly
                        results = json.load(f)
                    except json.JSONDecodeError:
                        # If that fails, read content and then load
                        f.seek(0)  # Go back to the beginning of the file
                        content = f.read()
                        if content.endswith(',\n]'):
                            content = content.replace(',\n]', '\n]')
                        results = json.loads(content)
                
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
                flash('Файл с результатами не найден. Проверьте парсер.', 'warning')
        except Exception as f:
            flash(f'Не удалось прочитать результаты парсера Citilink: {str(f)}', 'warning')
    except Exception as e:
        flash(f'Ошибка при запуске парсера Citilink: {str(e)}', 'danger')
    
    return redirect(url_for('admin.scrape'))

@admin_bp.route('/price-comparison', methods=['GET', 'POST'])
@login_required
@admin_required
def price_comparison():
    results = []
    sort_by = request.args.get('sort_by', 'price_diff')  # Default sorting by price difference
    
    if request.method == 'POST':
        category = request.form.get('category')
        sort_by = request.form.get('sort_by', sort_by)
        
        if category:
            try:
                from app.utils.price_comparison import run_price_comparison
                
                # Map category values to DNS category names
                dns_category_mapping = {
                    'videokarty': 'Видеокарты',
                    'processory': 'Процессоры',
                    'materinskie-platy': 'Материнские платы',
                    'operativnaya-pamyat': 'Оперативная память',
                    'bloki-pitaniya': 'Блоки питания',
                    'moduli-pamyati': 'Модули памяти',
                    'korpusa': 'Корпуса',
                    'sistemy-ohlazhdeniya-processora': 'Кулеры для процессора',
                    'ssd-nakopiteli': 'SSD накопители',
                    'zhestkie-diski': 'Жесткие диски',
                    'kulery': 'Кулеры'
                }
                
                # Get the corresponding DNS category name
                dns_category = dns_category_mapping.get(category)
                
                # Run price comparison with selected category for both stores
                results = run_price_comparison(category, dns_category)
                
                # Sort results based on user selection
                if results:
                    if sort_by == 'price_diff':
                        # Sort by absolute price difference (default)
                        results.sort(key=lambda x: abs(x['price_difference']), reverse=True)
                    elif sort_by == 'price_diff_percent':
                        # Sort by percentage price difference
                        results.sort(key=lambda x: abs(x['price_difference_percent']), reverse=True)
                    elif sort_by == 'lowest_price':
                        # Sort by lowest price (from either store)
                        results.sort(key=lambda x: min(x['citilink_price'], x['dns_price']))
                    elif sort_by == 'highest_price':
                        # Sort by highest price (from either store)
                        results.sort(key=lambda x: max(x['citilink_price'], x['dns_price']), reverse=True)
                    elif sort_by == 'rating':
                        # Sort by average rating if available
                        results.sort(key=lambda x: (x['citilink_rating'] + x['dns_rating'])/2 if x['citilink_rating'] and x['dns_rating'] else 0, reverse=True)
                    elif sort_by == 'similarity':
                        # Sort by match confidence/similarity score
                        results.sort(key=lambda x: x['similarity_score'], reverse=True)
                    
                    logger.info(f"Found {len(results)} matching products between Citilink and DNS. Sorted by: {sort_by}")
                    flash(f'Найдено {len(results)} товаров с разницей в цене', 'success')
                else:
                    logger.warning(f"No matching products found for category: {category}")
                    flash('Не найдено товаров с сопоставимыми ценами. Попробуйте другие категории или запустите парсеры заново.', 'warning')
            except Exception as e:
                logger.error(f'Ошибка при сравнении цен: {str(e)}')
                flash(f'Ошибка при сравнении цен: {str(e)}', 'danger')
        else:
            flash('Необходимо указать категорию товаров', 'danger')
    
    return render_template('admin/price_comparison.html', results=results, sort_by=sort_by)

@admin_bp.route('/ram-comparison', methods=['GET', 'POST'])
@login_required
@admin_required
def ram_comparison():
    """Сравнение оперативной памяти с использованием GigaChat"""
    
    mode = request.args.get('mode', 'interactive')
    results = None
    analysis = None
    
    if request.method == 'POST':
        mode = request.form.get('mode', 'interactive')
        
        try:
            from app.utils.ram_price_comparison import auto_mode, interactive_mode, compare_all_ram_mode
            
            # Запускаем соответствующий режим сравнения
            if mode == 'auto':
                # В автоматическом режиме находим похожие модели и сравниваем их
                auto_mode()
                flash('Автоматическое сравнение RAM выполнено успешно', 'success')
            elif mode == 'compare_all':
                # Сравниваем все данные о RAM
                compare_all_ram_mode()
                flash('Полное сравнение данных о RAM выполнено успешно', 'success')
            else:
                # Интерактивный режим (по умолчанию) - перенаправляем на терминал
                flash('Для интерактивного режима запустите скрипт в терминале: python -m app.utils.ram_price_comparison --mode interactive', 'info')
                
            # Загружаем результаты анализа, если они есть
            if mode == 'auto' or mode == 'interactive':
                result_file = 'ram_comparison_result.json'
                if os.path.exists(result_file):
                    with open(result_file, 'r', encoding='utf-8') as f:
                        results = json.load(f)
                        analysis = results.get('analysis')
                        if analysis:
                            # Преобразуем текст анализа в HTML
                            analysis = analysis.replace('\n', '<br>')
                            analysis = analysis.replace('**', '<strong>').replace('**', '</strong>')
                            results['analysis'] = analysis
            elif mode == 'compare_all':
                result_file = 'ram_comparison_all.json'
                if os.path.exists(result_file):
                    with open(result_file, 'r', encoding='utf-8') as f:
                        results = json.load(f)
                        analysis = results.get('analysis')
                        if analysis:
                            # Преобразуем текст анализа в HTML
                            analysis = analysis.replace('\n', '<br>')
                            analysis = analysis.replace('**', '<strong>').replace('**', '</strong>')
                            results['analysis'] = analysis
                
        except Exception as e:
            logger.error(f'Ошибка при сравнении RAM: {str(e)}')
            flash(f'Ошибка при сравнении RAM: {str(e)}', 'danger')
    
    return render_template('admin/ram_comparison.html', mode=mode, results=results, analysis=analysis)

@admin_bp.route('/dns-parser')
@login_required
@admin_required
def dns_parser_status():
    """Страница статуса парсера DNS"""
    # Проверяем, является ли пользователь админом
    if not current_user.is_admin():
        flash('У вас нет доступа к этой странице', 'danger')
        return redirect(url_for('main.index'))
    
    # Получаем статус парсера
    status = {}
    status_file = os.path.join(current_app.root_path, 'utils/DNS_parsing/parsing_status.json')
    
    if os.path.exists(status_file):
        with open(status_file, 'r', encoding='utf-8') as f:
            try:
                status = json.load(f)
            except json.JSONDecodeError:
                status = {"error": "Invalid status file"}
    else:
        status = {"status": "Парсер еще не запускался"}
    
    # Форматируем даты для отображения
    if 'start_time' in status and status['start_time']:
        try:
            start_time = datetime.fromisoformat(status['start_time'])
            status['start_time_formatted'] = start_time.strftime('%d.%m.%Y %H:%M:%S')
        except:
            status['start_time_formatted'] = status['start_time']
    
    if 'last_updated' in status and status['last_updated']:
        try:
            last_updated = datetime.fromisoformat(status['last_updated'])
            status['last_updated_formatted'] = last_updated.strftime('%d.%m.%Y %H:%M:%S')
            
            # Вычисляем, сколько времени прошло с последнего обновления
            seconds_ago = (datetime.now() - last_updated).total_seconds()
            if seconds_ago < 60:
                status['last_updated_human'] = f"{int(seconds_ago)} сек. назад"
            elif seconds_ago < 3600:
                status['last_updated_human'] = f"{int(seconds_ago / 60)} мин. назад"
            else:
                status['last_updated_human'] = f"{int(seconds_ago / 3600)} ч. назад"
        except:
            status['last_updated_formatted'] = status['last_updated']
    
    return render_template('admin/dns_parser.html', status=status)

@admin_bp.route('/dns-parser/start', methods=['POST'])
@login_required
@admin_required
def start_dns_parser():
    """Запустить парсер DNS"""
    # Проверяем, является ли пользователь админом
    if not current_user.is_admin():
        return jsonify({"error": "У вас нет доступа к этой функции"}), 403
    
    try:
        # Получаем параметры из формы
        limit = int(request.form.get('limit', 5))
        continuous = request.form.get('continuous') == 'on'
        interval = int(request.form.get('interval', 24))
        
        # Добавляем путь к директории с парсером в sys.path
        parser_path = os.path.join(current_app.root_path, 'utils/DNS_parsing')
        if parser_path not in sys.path:
            sys.path.append(parser_path)
        
        # Запускаем парсер асинхронно
        result = dns_parser.start_parsing_async(
            limit_per_category=limit,
            continuous=continuous,
            interval_hours=interval
        )
        
        return jsonify({"success": True, "message": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/dns-parser/status', methods=['GET'])
@login_required
@admin_required
def get_dns_parser_status():
    """Получить текущий статус парсера DNS в формате JSON"""
    # Проверяем, является ли пользователь админом
    if not current_user.is_admin():
        return jsonify({"error": "У вас нет доступа к этой функции"}), 403
    
    status_file = os.path.join(current_app.root_path, 'utils/DNS_parsing/parsing_status.json')
    
    if os.path.exists(status_file):
        with open(status_file, 'r', encoding='utf-8') as f:
            try:
                status = json.load(f)
                
                # Добавляем время последнего обновления в формате для человека
                if 'last_updated' in status and status['last_updated']:
                    try:
                        last_updated = datetime.fromisoformat(status['last_updated'])
                        seconds_ago = (datetime.now() - last_updated).total_seconds()
                        if seconds_ago < 60:
                            status['last_updated_human'] = f"{int(seconds_ago)} сек. назад"
                        elif seconds_ago < 3600:
                            status['last_updated_human'] = f"{int(seconds_ago / 60)} мин. назад"
                        else:
                            status['last_updated_human'] = f"{int(seconds_ago / 3600)} ч. назад"
                    except:
                        pass
                
                return jsonify(status)
            except json.JSONDecodeError:
                return jsonify({"error": "Invalid status file"}), 500
    else:
        return jsonify({"status": "Парсер еще не запускался"}), 404

@admin_bp.route('/view-logs')
@login_required
@admin_required
def view_logs():
    """API endpoint to retrieve log files content"""
    log_file = request.args.get('file', 'dns_parser.log')
    
    # Validate the log file name to prevent directory traversal
    allowed_logs = ['dns_parser.log', 'price_comparison.log', 'app/utils/Citi_parser/parser.log']
    if log_file not in allowed_logs:
        return jsonify({"error": "Invalid log file requested"}), 400
    
    # Получаем абсолютный путь к корневой директории проекта
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # For app-relative paths
    if log_file.startswith('app/'):
        log_path = os.path.join(project_root, log_file)
    else:
        log_path = os.path.join(project_root, log_file)
    
    try:
        if os.path.exists(log_path):
            # Read last 100 lines to avoid massive responses
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_lines = lines[-100:] if len(lines) > 100 else lines
                content = ''.join(last_lines)
                
            return jsonify({"content": content})
        else:
            return jsonify({"content": f"Лог файл {log_file} не найден. Путь: {log_path}"})
    except Exception as e:
        return jsonify({"error": f"Ошибка чтения лог файла: {str(e)}"}), 500

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