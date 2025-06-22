from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.models import Configuration, UnifiedProduct
from app.forms.config import ConfigurationForm

config_bp = Blueprint('config', __name__)

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
    form.motherboard_id.choices = [(0, 'Выберите материнскую плату...')] + [(m.id, m.product_name) for m in motherboards]
    form.supply_id.choices = [(0, 'Выберите блок питания...')] + [(p.id, p.product_name) for p in power_supplies]
    form.cpu_id.choices = [(0, 'Выберите процессор...')] + [(p.id, p.product_name) for p in processors]
    form.gpu_id.choices = [(0, 'Выберите видеокарту...')] + [(g.id, g.product_name) for g in graphics_cards]
    form.cooler_id.choices = [(0, 'Выберите кулер...')] + [(c.id, c.product_name) for c in coolers]
    form.ram_id.choices = [(0, 'Выберите оперативную память...')] + [(r.id, r.product_name) for r in rams]
    form.hdd_id.choices = [(0, 'Выберите жёсткий диск...')] + [(h.id, h.product_name) for h in hard_drives]
    form.frame_id.choices = [(0, 'Выберите корпус...')] + [(c.id, c.product_name) for c in cases]
    
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
    form.motherboard_id.choices = [(0, 'Выберите материнскую плату...')] + [(m.id, m.product_name) for m in motherboards]
    form.supply_id.choices = [(0, 'Выберите блок питания...')] + [(p.id, p.product_name) for p in power_supplies]
    form.cpu_id.choices = [(0, 'Выберите процессор...')] + [(p.id, p.product_name) for p in processors]
    form.gpu_id.choices = [(0, 'Выберите видеокарту...')] + [(g.id, g.product_name) for g in graphics_cards]
    form.cooler_id.choices = [(0, 'Выберите кулер...')] + [(c.id, c.product_name) for c in coolers]
    form.ram_id.choices = [(0, 'Выберите оперативную память...')] + [(r.id, r.product_name) for r in rams]
    form.hdd_id.choices = [(0, 'Выберите жёсткий диск...')] + [(h.id, h.product_name) for h in hard_drives]
    form.frame_id.choices = [(0, 'Выберите корпус...')] + [(c.id, c.product_name) for c in cases]
    
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
    
    # Получаем объекты компонентов напрямую
    components = {}
    total_price = 0
    
    if motherboard_id and motherboard_id != 0:
        motherboard = UnifiedProduct.query.get(motherboard_id)
        if motherboard:
            components['motherboard'] = motherboard
            if motherboard.price_discounted and motherboard.price_discounted > 0:
                total_price += motherboard.price_discounted
            elif motherboard.price_original and motherboard.price_original > 0:
                total_price += motherboard.price_original
    
    if supply_id and supply_id != 0:
        power_supply = UnifiedProduct.query.get(supply_id)
        if power_supply:
            components['power_supply'] = power_supply
            if power_supply.price_discounted and power_supply.price_discounted > 0:
                total_price += power_supply.price_discounted
            elif power_supply.price_original and power_supply.price_original > 0:
                total_price += power_supply.price_original
    
    if cpu_id and cpu_id != 0:
        processor = UnifiedProduct.query.get(cpu_id)
        if processor:
            components['processor'] = processor
            if processor.price_discounted and processor.price_discounted > 0:
                total_price += processor.price_discounted
            elif processor.price_original and processor.price_original > 0:
                total_price += processor.price_original
    
    if gpu_id and gpu_id != 0:
        graphics_card = UnifiedProduct.query.get(gpu_id)
        if graphics_card:
            components['graphics_card'] = graphics_card
            if graphics_card.price_discounted and graphics_card.price_discounted > 0:
                total_price += graphics_card.price_discounted
            elif graphics_card.price_original and graphics_card.price_original > 0:
                total_price += graphics_card.price_original
    
    if cooler_id and cooler_id != 0:
        cooler = UnifiedProduct.query.get(cooler_id)
        if cooler:
            components['cooler'] = cooler
            if cooler.price_discounted and cooler.price_discounted > 0:
                total_price += cooler.price_discounted
            elif cooler.price_original and cooler.price_original > 0:
                total_price += cooler.price_original
    
    if ram_id and ram_id != 0:
        ram = UnifiedProduct.query.get(ram_id)
        if ram:
            components['ram'] = ram
            if ram.price_discounted and ram.price_discounted > 0:
                total_price += ram.price_discounted
            elif ram.price_original and ram.price_original > 0:
                total_price += ram.price_original
    
    if hdd_id and hdd_id != 0:
        hard_drive = UnifiedProduct.query.get(hdd_id)
        if hard_drive:
            components['hard_drive'] = hard_drive
            if hard_drive.price_discounted and hard_drive.price_discounted > 0:
                total_price += hard_drive.price_discounted
            elif hard_drive.price_original and hard_drive.price_original > 0:
                total_price += hard_drive.price_original
    
    if frame_id and frame_id != 0:
        case = UnifiedProduct.query.get(frame_id)
        if case:
            components['case'] = case
            if case.price_discounted and case.price_discounted > 0:
                total_price += case.price_discounted
            elif case.price_original and case.price_original > 0:
                total_price += case.price_original
    
    # Проверяем совместимость между всеми компонентами
    issues = []
    components_list = list(components.values())
    
    for i, comp1 in enumerate(components_list):
        for comp2 in components_list[i+1:]:
            compatibility_result = comp1.is_compatible_with(comp2)
            if compatibility_result is not True:
                issues.append(compatibility_result)
    
    # Формируем ответ
    return jsonify({
        'total_price': float(total_price),
        'compatible': len(issues) == 0,
        'issues': issues
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
    limit = data.get('limit', 20)  # Ограничиваем количество результатов
    
    # Проверяем наличие обязательных параметров
    if not product_type:
        return jsonify({'error': 'Тип продукта не указан'}), 400
    
    # Выполняем поиск компонентов
    components_query = UnifiedProduct.query.filter_by(product_type=product_type)
    
    # Если есть поисковый запрос, фильтруем по нему
    if query:
        components_query = components_query.filter(UnifiedProduct.product_name.ilike(f'%{query}%'))
    
    # Сортируем по релевантности (сначала точные совпадения, потом по алфавиту)
    if query:
        # Точные совпадения в начале названия имеют приоритет
        components_query = components_query.order_by(
            UnifiedProduct.product_name.ilike(f'{query}%').desc(),
            UnifiedProduct.product_name
        )
    else:
        components_query = components_query.order_by(UnifiedProduct.product_name)
    
    # Ограничиваем количество результатов
    components = components_query.limit(limit).all()
    
    # Формируем ответ
    result = []
    for component in components:
        # Определяем цену для отображения
        price = None
        price_formatted = 'Цена не указана'
        if component.price_discounted is not None and component.price_discounted > 0:
            price = component.price_discounted
            price_formatted = f"{price:,.0f}".replace(',', ' ') + ' ₽'
        elif component.price_original is not None and component.price_original > 0:
            price = component.price_original
            price_formatted = f"{price:,.0f}".replace(',', ' ') + ' ₽'
            
        # Пропускаем компоненты без цены только если это не живой поиск
        if price is None and query:
            continue
        
        # Получаем характеристики для дополнительной информации
        characteristics = component.get_characteristics() if hasattr(component, 'get_characteristics') else {}
        
        # Формируем краткое описание
        description_parts = []
        if product_type == 'processor':
            if characteristics.get('core_count'):
                description_parts.append(f"{characteristics['core_count']} ядер")
            if characteristics.get('base_frequency'):
                description_parts.append(f"{characteristics['base_frequency']}")
        elif product_type == 'graphics_card':
            if characteristics.get('memory_size'):
                description_parts.append(f"{characteristics['memory_size']} ГБ")
            if characteristics.get('memory_type'):
                description_parts.append(characteristics['memory_type'])
        elif product_type == 'ram':
            if characteristics.get('memory_size'):
                description_parts.append(f"{characteristics['memory_size']} ГБ")
            if characteristics.get('memory_type'):
                description_parts.append(characteristics['memory_type'])
            if characteristics.get('frequency'):
                description_parts.append(f"{characteristics['frequency']} МГц")
        elif product_type == 'motherboard':
            if characteristics.get('socket'):
                description_parts.append(f"Socket {characteristics['socket']}")
            if characteristics.get('form_factor'):
                description_parts.append(characteristics['form_factor'])
        elif product_type == 'power_supply':
            if characteristics.get('wattage'):
                description_parts.append(f"{characteristics['wattage']} Вт")
        elif product_type == 'hard_drive':
            if characteristics.get('storage_capacity'):
                description_parts.append(f"{characteristics['storage_capacity']} ГБ")
            if characteristics.get('interface'):
                description_parts.append(characteristics['interface'])
        
        description = ' • '.join(description_parts[:3])  # Максимум 3 характеристики
        
        # Определяем иконку магазина
        vendor_icon = ''
        vendor_name = ''
        if component.vendor == 'dns':
            vendor_icon = '🟢'
            vendor_name = 'DNS'
        elif component.vendor == 'citilink':
            vendor_icon = '🔵'
            vendor_name = 'Citilink'
        else:
            vendor_icon = '⚪'
            vendor_name = component.vendor.title()
        
        # Получаем реальное изображение из JSON данных
        images = component.get_images()
        image_url = None
        if images and len(images) > 0:
            # Берем первое изображение из списка
            image_url = images[0]
        
        # Если нет изображения, используем заглушку
        if not image_url:
            image_url = f"/static/images/products/{product_type}_placeholder.jpg"
        
        result.append({
            'id': component.id,
            'name': component.product_name,
            'price': price,
            'price_formatted': price_formatted,
            'description': description,
            'vendor': component.vendor,
            'vendor_name': vendor_name,
            'vendor_icon': vendor_icon,
            'product_url': component.product_url,
            'image_url': image_url
        })
    
    return jsonify({
        'components': result,
        'total': len(result),
        'query': query
    })

@config_bp.route('/api/autocomplete-components', methods=['GET'])
@login_required
def autocomplete_components():
    """Endpoint для автодополнения поиска компонентов"""
    product_type = request.args.get('product_type')
    query = request.args.get('query', '').strip()
    limit = int(request.args.get('limit', 10))
    
    if not product_type or not query or len(query) < 2:
        return jsonify({'suggestions': []})
    
    # Ищем компоненты с названиями, содержащими запрос
    components = UnifiedProduct.query.filter(
        UnifiedProduct.product_type == product_type,
        UnifiedProduct.product_name.ilike(f'%{query}%')
    ).order_by(
        UnifiedProduct.product_name.ilike(f'{query}%').desc(),  # Приоритет для начала строки
        UnifiedProduct.product_name
    ).limit(limit).all()
    
    suggestions = []
    for component in components:
        # Определяем цену
        price_text = 'Цена не указана'
        if component.price_discounted and component.price_discounted > 0:
            price_text = f"{component.price_discounted:,.0f}".replace(',', ' ') + ' ₽'
        elif component.price_original and component.price_original > 0:
            price_text = f"{component.price_original:,.0f}".replace(',', ' ') + ' ₽'
        
        # Vendor icon
        vendor_icon = '🟢' if component.vendor == 'dns' else ('🔵' if component.vendor == 'citilink' else '⚪')
        
        # Получаем реальное изображение из JSON данных
        images = component.get_images()
        image_url = None
        if images and len(images) > 0:
            # Берем первое изображение из списка
            image_url = images[0]
        
        # Если нет изображения, используем заглушку
        if not image_url:
            image_url = f"/static/images/products/{product_type}_placeholder.jpg"
        
        suggestions.append({
            'id': component.id,
            'name': component.product_name,
            'price_text': price_text,
            'vendor_icon': vendor_icon,
            'image_url': image_url
        })
    
    return jsonify({'suggestions': suggestions}) 