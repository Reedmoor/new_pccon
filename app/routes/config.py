from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.models import Configuration, UnifiedProduct
from app.forms.config import ConfigurationForm
import logging

logger = logging.getLogger(__name__)

config_bp = Blueprint('config', __name__)

def format_product_choice(product):
    """Форматирует опцию товара с названием, ценой, рейтингом и источником"""
    if not product:
        return ""
    
    # Определяем цену для отображения
    price = None
    price_text = ""
    if product.price_discounted is not None and product.price_discounted > 0:
        price = product.price_discounted
        formatted_price = "{:,.0f}".format(price).replace(",", " ")
        price_text = f" • {formatted_price} ₽"
    elif product.price_original is not None and product.price_original > 0:
        price = product.price_original
        formatted_price = "{:,.0f}".format(price).replace(",", " ")
        price_text = f" • {formatted_price} ₽"
    else:
        price_text = " • Цена не указана"
    
    # Определяем источник (магазин)
    vendor_text = ""
    if product.vendor:
        vendor_name = product.vendor.upper()
        if vendor_name == "CITILINK":
            vendor_text = " • 🛒 Ситилинк"
        elif vendor_name == "DNS":
            vendor_text = " • 🛒 DNS"
        else:
            vendor_text = f" • 🛒 {vendor_name}"
    
    # Определяем рейтинг и отзывы
    rating_text = ""
    if product.rating is not None and product.rating > 0:
        # Округляем рейтинг до одного знака после запятой
        rating_formatted = f"{product.rating:.1f}"
        rating_text = f" • ⭐ {rating_formatted}"
        
        # Добавляем количество отзывов если есть
        if product.number_of_reviews is not None and product.number_of_reviews > 0:
            if product.number_of_reviews == 1:
                reviews_word = "отзыв"
            elif 2 <= product.number_of_reviews <= 4:
                reviews_word = "отзыва"
            else:
                reviews_word = "отзывов"
            rating_text += f" ({product.number_of_reviews} {reviews_word})"
    
    # Собираем итоговую строку
    # Ограничиваем длину названия продукта для лучшего отображения
    product_name = product.product_name
    if len(product_name) > 60:
        product_name = product_name[:57] + "..."
    
    result = f"{product_name}{price_text}{vendor_text}{rating_text}"
    
    return result

@config_bp.route('/')
@login_required
def my_configs():
    configs = Configuration.query.filter_by(user_id=current_user.id).all()
    return render_template('config/my_configs.html', configs=configs)

@config_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_config():
    form = ConfigurationForm()
    
    # Get components for dropdowns
    motherboards = UnifiedProduct.query.filter_by(product_type='motherboard').all()
    power_supplies = UnifiedProduct.query.filter_by(product_type='power_supply').all()
    processors = UnifiedProduct.query.filter_by(product_type='processor').all()
    graphics_cards = UnifiedProduct.query.filter_by(product_type='graphics_card').all()
    coolers = UnifiedProduct.query.filter_by(product_type='cooler').all()
    rams = UnifiedProduct.query.filter_by(product_type='ram').all()
    hard_drives = UnifiedProduct.query.filter_by(product_type='hard_drive').all()
    cases = UnifiedProduct.query.filter_by(product_type='case').all()
    
    # Set choices for each dropdown
    form.motherboard_id.choices = [(0, 'Выберите материнскую плату...')] + [(m.id, format_product_choice(m)) for m in motherboards]
    form.supply_id.choices = [(0, 'Выберите блок питания...')] + [(p.id, format_product_choice(p)) for p in power_supplies]
    form.cpu_id.choices = [(0, 'Выберите процессор...')] + [(p.id, format_product_choice(p)) for p in processors]
    form.gpu_id.choices = [(0, 'Выберите видеокарту...')] + [(g.id, format_product_choice(g)) for g in graphics_cards]
    form.cooler_id.choices = [(0, 'Выберите кулер...')] + [(c.id, format_product_choice(c)) for c in coolers]
    form.ram_id.choices = [(0, 'Выберите оперативную память...')] + [(r.id, format_product_choice(r)) for r in rams]
    form.hdd_id.choices = [(0, 'Выберите жёсткий диск...')] + [(h.id, format_product_choice(h)) for h in hard_drives]
    form.frame_id.choices = [(0, 'Выберите корпус...')] + [(c.id, format_product_choice(c)) for c in cases]
    
    if form.validate_on_submit():
        config = Configuration(
            name=form.name.data,
            user_id=current_user.id
        )
        
        # Set component IDs, converting 0 to None
        config.motherboard_id = form.motherboard_id.data if form.motherboard_id.data != 0 else None
        config.supply_id = form.supply_id.data if form.supply_id.data != 0 else None
        config.cpu_id = form.cpu_id.data if form.cpu_id.data != 0 else None
        config.gpu_id = form.gpu_id.data if form.gpu_id.data != 0 else None
        config.cooler_id = form.cooler_id.data if form.cooler_id.data != 0 else None
        config.ram_id = form.ram_id.data if form.ram_id.data != 0 else None
        config.hdd_id = form.hdd_id.data if form.hdd_id.data != 0 else None
        config.frame_id = form.frame_id.data if form.frame_id.data != 0 else None
        
        db.session.add(config)
        db.session.commit()
        
        flash('Конфигурация успешно создана!', 'success')
        return redirect(url_for('config.my_configs'))
    
    return render_template('config/new_config.html', form=form)

@config_bp.route('/<int:config_id>')
@login_required
def view_config(config_id):
    config = Configuration.query.get_or_404(config_id)
    
    # Check if the config belongs to the current user
    if config.user_id != current_user.id and not current_user.is_admin():
        flash('У вас нет доступа к этой конфигурации', 'danger')
        return redirect(url_for('config.my_configs'))
    
    # Check compatibility
    compatibility_issues = config.check_compatibility()
    
    # Calculate total price
    total_price = config.total_price()
    
    return render_template('config/view_config.html', config=config, issues=compatibility_issues, total_price=total_price)

@config_bp.route('/<int:config_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_config(config_id):
    config = Configuration.query.get_or_404(config_id)
    
    # Check if the config belongs to the current user
    if config.user_id != current_user.id and not current_user.is_admin():
        flash('У вас нет доступа к редактированию этой конфигурации', 'danger')
        return redirect(url_for('config.my_configs'))
    
    form = ConfigurationForm()
    
    # Get components for dropdowns
    motherboards = UnifiedProduct.query.filter_by(product_type='motherboard').all()
    power_supplies = UnifiedProduct.query.filter_by(product_type='power_supply').all()
    processors = UnifiedProduct.query.filter_by(product_type='processor').all()
    graphics_cards = UnifiedProduct.query.filter_by(product_type='graphics_card').all()
    coolers = UnifiedProduct.query.filter_by(product_type='cooler').all()
    rams = UnifiedProduct.query.filter_by(product_type='ram').all()
    hard_drives = UnifiedProduct.query.filter_by(product_type='hard_drive').all()
    cases = UnifiedProduct.query.filter_by(product_type='case').all()
    
    # Set choices for each dropdown
    form.motherboard_id.choices = [(0, 'Выберите материнскую плату...')] + [(m.id, format_product_choice(m)) for m in motherboards]
    form.supply_id.choices = [(0, 'Выберите блок питания...')] + [(p.id, format_product_choice(p)) for p in power_supplies]
    form.cpu_id.choices = [(0, 'Выберите процессор...')] + [(p.id, format_product_choice(p)) for p in processors]
    form.gpu_id.choices = [(0, 'Выберите видеокарту...')] + [(g.id, format_product_choice(g)) for g in graphics_cards]
    form.cooler_id.choices = [(0, 'Выберите кулер...')] + [(c.id, format_product_choice(c)) for c in coolers]
    form.ram_id.choices = [(0, 'Выберите оперативную память...')] + [(r.id, format_product_choice(r)) for r in rams]
    form.hdd_id.choices = [(0, 'Выберите жёсткий диск...')] + [(h.id, format_product_choice(h)) for h in hard_drives]
    form.frame_id.choices = [(0, 'Выберите корпус...')] + [(c.id, format_product_choice(c)) for c in cases]
    
    if form.validate_on_submit():
        config.name = form.name.data
        
        # Set component IDs, converting 0 to None
        config.motherboard_id = form.motherboard_id.data if form.motherboard_id.data != 0 else None
        config.supply_id = form.supply_id.data if form.supply_id.data != 0 else None
        config.cpu_id = form.cpu_id.data if form.cpu_id.data != 0 else None
        config.gpu_id = form.gpu_id.data if form.gpu_id.data != 0 else None
        config.cooler_id = form.cooler_id.data if form.cooler_id.data != 0 else None
        config.ram_id = form.ram_id.data if form.ram_id.data != 0 else None
        config.hdd_id = form.hdd_id.data if form.hdd_id.data != 0 else None
        config.frame_id = form.frame_id.data if form.frame_id.data != 0 else None
        
        db.session.commit()
        
        flash('Конфигурация успешно обновлена!', 'success')
        return redirect(url_for('config.view_config', config_id=config.conf_id))
    elif request.method == 'GET':
        # Populate form with existing data
        form.name.data = config.name
        form.motherboard_id.data = config.motherboard_id or 0
        form.supply_id.data = config.supply_id or 0
        form.cpu_id.data = config.cpu_id or 0
        form.gpu_id.data = config.gpu_id or 0
        form.cooler_id.data = config.cooler_id or 0
        form.ram_id.data = config.ram_id or 0
        form.hdd_id.data = config.hdd_id or 0
        form.frame_id.data = config.frame_id or 0
    
    return render_template('config/edit_config.html', form=form, config=config)

@config_bp.route('/<int:config_id>/delete', methods=['POST'])
@login_required
def delete_config(config_id):
    config = Configuration.query.get_or_404(config_id)
    
    # Check if the config belongs to the current user
    if config.user_id != current_user.id and not current_user.is_admin():
        flash('У вас нет доступа к удалению этой конфигурации', 'danger')
        return redirect(url_for('config.my_configs'))
    
    db.session.delete(config)
    db.session.commit()
    
    flash('Конфигурация успешно удалена!', 'success')
    return redirect(url_for('config.my_configs'))

@config_bp.route('/api/compatibility-check', methods=['POST'])
@login_required
def compatibility_check():
    data = request.json
    
    # Get component IDs
    motherboard_id = data.get('motherboard_id')
    cpu_id = data.get('cpu_id')
    gpu_id = data.get('gpu_id')
    ram_id = data.get('ram_id')
    case_id = data.get('case_id')
    
    # Get components
    components = {}
    if motherboard_id:
        components['motherboard'] = UnifiedProduct.query.get(motherboard_id)
    if cpu_id:
        components['cpu'] = UnifiedProduct.query.get(cpu_id)
    if gpu_id:
        components['gpu'] = UnifiedProduct.query.get(gpu_id)
    if ram_id:
        components['ram'] = UnifiedProduct.query.get(ram_id)
    if case_id:
        components['case'] = UnifiedProduct.query.get(case_id)
    
    # Check compatibility between all components
    issues = []
    components_list = list(components.values())
    
    for i, comp1 in enumerate(components_list):
        for comp2 in components_list[i+1:]:
            if not comp1.is_compatible_with(comp2):
                issues.append(f"{comp1.product_type.capitalize()} ({comp1.product_name}) is not compatible with "
                             f"{comp2.product_type.capitalize()} ({comp2.product_name})")
    
    return jsonify({
        'compatible': len(issues) == 0,
        'issues': issues
    })

@config_bp.route('/api/config-info', methods=['POST'])
@login_required
def get_config_info():
    """Endpoint для получения информации о цене и совместимости"""
    data = request.json
    
    # Получаем ID компонентов из запроса
    motherboard_id = data.get('motherboard_id', 0)
    supply_id = data.get('supply_id', 0)
    cpu_id = data.get('cpu_id', 0)
    gpu_id = data.get('gpu_id', 0)
    cooler_id = data.get('cooler_id', 0)
    ram_id = data.get('ram_id', 0)
    hdd_id = data.get('hdd_id', 0)
    frame_id = data.get('frame_id', 0)
    
    # Собираем компоненты для расчета цены
    component_ids = []
    if motherboard_id and motherboard_id != 0:
        component_ids.append(motherboard_id)
    if supply_id and supply_id != 0:
        component_ids.append(supply_id)
    if cpu_id and cpu_id != 0:
        component_ids.append(cpu_id)
    if gpu_id and gpu_id != 0:
        component_ids.append(gpu_id)
    if cooler_id and cooler_id != 0:
        component_ids.append(cooler_id)
    if ram_id and ram_id != 0:
        component_ids.append(ram_id)
    if hdd_id and hdd_id != 0:
        component_ids.append(hdd_id)
    if frame_id and frame_id != 0:
        component_ids.append(frame_id)
    
    # Рассчитываем общую стоимость напрямую
    total_price = 0
    selected_components = []
    
    if component_ids:
        components = UnifiedProduct.query.filter(UnifiedProduct.id.in_(component_ids)).all()
        for component in components:
            # Определяем цену компонента
            price = None
            if component.price_discounted is not None and component.price_discounted > 0:
                price = int(component.price_discounted)
            elif component.price_original is not None and component.price_original > 0:
                price = int(component.price_original)
            
            if price is not None:
                total_price += price
                selected_components.append({
                    'id': component.id,
                    'name': component.product_name,
                    'price': price,
                    'type': component.product_type
                })
    
    # Простая проверка совместимости (без создания временной конфигурации)
    compatibility_issues = []
    compatible = True
    
    # Пока используем простую логику - если выбраны основные компоненты, считаем совместимыми
    # В будущем можно добавить более сложную логику проверки
    if motherboard_id and cpu_id:
        # Получаем материнскую плату и процессор для проверки сокета
        try:
            motherboard = UnifiedProduct.query.get(motherboard_id) if motherboard_id != 0 else None
            processor = UnifiedProduct.query.get(cpu_id) if cpu_id != 0 else None
            
            if motherboard and processor:
                mb_chars = motherboard.get_characteristics()
                cpu_chars = processor.get_characteristics()
                
                mb_socket = mb_chars.get('socket', '').upper()
                cpu_socket = cpu_chars.get('socket', '').upper()
                
                if mb_socket and cpu_socket and mb_socket != cpu_socket:
                    compatibility_issues.append(f"Несовместимые сокеты: {mb_socket} (материнская плата) и {cpu_socket} (процессор)")
                    compatible = False
        except Exception as e:
            logger.error(f"Ошибка проверки совместимости: {e}")
    
    # Формируем ответ
    return jsonify({
        'total_price': float(total_price),
        'compatible': compatible,
        'issues': compatibility_issues,
        'components': selected_components  # Добавляем информацию о выбранных компонентах для отладки
    })

@config_bp.route('/api/filter-components', methods=['POST'])
@login_required
def filter_components():
    """Endpoint для фильтрации компонентов по различным критериям"""
    data = request.json
    
    # Получаем параметры фильтрации
    product_type = data.get('product_type')
    form_factor = data.get('form_factor')
    socket = data.get('socket')
    memory_type = data.get('memory_type')
    max_price = data.get('max_price')
    min_frequency = data.get('min_frequency')
    
    # Основной запрос фильтрации
    query = UnifiedProduct.query.filter_by(product_type=product_type)
    
    # Применяем дополнительные фильтры
    if max_price:
        # Конвертируем в float для надежности
        max_price = float(max_price)
        # Фильтр по цене с учетом как скидочной, так и оригинальной цены
        query = query.filter(
            db.or_(
                db.and_(UnifiedProduct.price_discounted.isnot(None), UnifiedProduct.price_discounted <= max_price),
                db.and_(
                    db.or_(UnifiedProduct.price_discounted.is_(None), UnifiedProduct.price_discounted > max_price),
                    UnifiedProduct.price_original <= max_price
                )
            )
        )
    
    # Получаем результаты
    results = query.all()
    
    # Фильтруем по характеристикам, которые хранятся в JSON
    filtered_results = []
    for product in results:
        chars = product.get_characteristics()
        
        # Фильтр по форм-фактору (для материнских плат)
        if form_factor and product_type == 'motherboard':
            if chars.get('form_factor') != form_factor:
                continue
        
        # Фильтр по сокету
        if socket:
            if product_type == 'motherboard' or product_type == 'processor':
                if chars.get('socket') != socket:
                    continue
        
        # Фильтр по типу памяти
        if memory_type:
            if product_type == 'motherboard' or product_type == 'ram':
                if chars.get('memory_type') != memory_type:
                    continue
        
        # Фильтр по частоте (для процессоров)
        if min_frequency and product_type == 'processor':
            # Проверяем наличие значения частоты и конвертируем в числовые значения
            base_clock = chars.get('base_clock')
            if not base_clock:
                continue
                
            try:
                # Преобразуем строковые значения в числовые при необходимости
                base_clock_val = float(base_clock) if isinstance(base_clock, str) else float(base_clock)
                min_freq_val = float(min_frequency) * 1000  # переводим ГГц в МГц
                
                if base_clock_val < min_freq_val:
                    continue
            except (ValueError, TypeError):
                # В случае ошибки преобразования пропускаем этот компонент
                continue
        
        # Определяем цену для отображения
        price = None
        if product.price_discounted is not None and product.price_discounted > 0:
            price = product.price_discounted
        elif product.price_original is not None and product.price_original > 0:
            price = product.price_original
        
        # Добавляем продукт в результаты
        filtered_results.append({
            'id': product.id,
            'name': product.product_name,
            'price': price,
            'characteristics': chars,
            'vendor': product.vendor,
            'product_url': product.product_url
        })
    
    return jsonify({
        'components': filtered_results
    })

@config_bp.route('/api/search-components', methods=['POST'])
@login_required
def search_components():
    """Endpoint для поиска компонентов по запросу"""
    data = request.json
    
    # Получаем тип продукта и поисковый запрос
    product_type = data.get('product_type')
    query = data.get('query', '').strip()
    
    # Проверяем наличие обязательных параметров
    if not product_type:
        return jsonify({'error': 'Тип продукта не указан'}), 400
    
    # Выполняем поиск компонентов
    components_query = UnifiedProduct.query.filter_by(product_type=product_type)
    
    # Если есть поисковый запрос, фильтруем по нему
    if query:
        components_query = components_query.filter(UnifiedProduct.product_name.ilike(f'%{query}%'))
    
    # Получаем результаты
    components = components_query.all()
    
    # Формируем ответ
    result = []
    for component in components:
        # Определяем цену для отображения
        price = None
        if component.price_discounted is not None and component.price_discounted > 0:
            price = component.price_discounted
        elif component.price_original is not None and component.price_original > 0:
            price = component.price_original
            
        # Пропускаем компоненты без цены
        if price is None:
            continue
        
        result.append({
            'id': component.id,
            'name': component.product_name,
            'price': price,
            'vendor': component.vendor,
            'product_url': component.product_url
        })
    
    return jsonify({
        'components': result
    }) 