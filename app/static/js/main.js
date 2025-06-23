/**
 * Основной JavaScript файл для приложения конфигуратора ПК
 */

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всплывающих подсказок Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Функция для фильтрации компонентов
    function setupComponentFilters() {
        const filterForms = document.querySelectorAll('.component-filter-form');
        
        filterForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(form);
                const componentType = form.dataset.componentType;
                const minPrice = formData.get('min_price');
                const maxPrice = formData.get('max_price');
                
                // Формирование URL для запроса с параметрами фильтра
                let url = `/config/filter?type=${componentType}`;
                if (minPrice) url += `&min_price=${minPrice}`;
                if (maxPrice) url += `&max_price=${maxPrice}`;
                
                // Добавление дополнительных фильтров в зависимости от типа компонента
                if (componentType === 'motherboard') {
                    const formFactor = formData.get('form');
                    const socket = formData.get('socket');
                    if (formFactor) url += `&form=${formFactor}`;
                    if (socket) url += `&socket=${socket}`;
                } else if (componentType === 'processor') {
                    const socket = formData.get('socket');
                    const minFreq = formData.get('min_freq');
                    if (socket) url += `&socket=${socket}`;
                    if (minFreq) url += `&min_freq=${minFreq}`;
                }
                
                // AJAX запрос для получения отфильтрованных компонентов
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        updateComponentList(componentType, data);
                    })
                    .catch(error => {
                        console.error('Ошибка при получении компонентов:', error);
                    });
            });
        });
    }
    
    // Функция обновления списка компонентов после фильтрации
    function updateComponentList(componentType, components) {
        const selectElement = document.getElementById(`${componentType}_id`);
        if (!selectElement) return;
        
        // Сохраняем текущее выбранное значение
        const currentValue = selectElement.value;
        
        // Очищаем существующие опции
        selectElement.innerHTML = '<option value="">-- Выберите компонент --</option>';
        
        // Добавляем новые опции на основе полученных данных
        components.forEach(component => {
            const option = document.createElement('option');
            option.value = component.id;
            
            // Форматируем в новом стиле с дополнительной информацией
            let displayText = component.name;
            
            // Ограничиваем длину названия
            if (displayText.length > 60) {
                displayText = displayText.substring(0, 57) + "...";
            }
            
            // Добавляем цену
            if (component.price !== null && component.price > 0) {
                const formattedPrice = new Intl.NumberFormat('ru-RU').format(component.price);
                displayText += ` • ${formattedPrice} ₽`;
            } else {
                displayText += ' • Цена не указана';
            }
            
            // Добавляем магазин если есть
            if (component.vendor) {
                const vendorName = component.vendor.toUpperCase();
                if (vendorName === "CITILINK") {
                    displayText += " • 🛒 Ситилинк";
                } else if (vendorName === "DNS") {
                    displayText += " • 🛒 DNS";
                } else {
                    displayText += ` • 🛒 ${vendorName}`;
                }
            }
            
            option.textContent = displayText;
            selectElement.appendChild(option);
        });
        
        // Восстанавливаем выбранное значение, если оно существует в новом списке
        if (currentValue) {
            const exists = Array.from(selectElement.options).some(option => option.value === currentValue);
            if (exists) {
                selectElement.value = currentValue;
            }
        }
        
        // Вызываем событие изменения для обновления расчетов
        const event = new Event('change');
        selectElement.dispatchEvent(event);
    }
    
    // Проверка совместимости компонентов
    function checkCompatibility() {
        const motherboardSelect = document.getElementById('motherboard_id');
        const cpuSelect = document.getElementById('cpu_id');
        const ramSelect = document.getElementById('ram_id');
        const gpuSelect = document.getElementById('gpu_id');
        const powerSupplySelect = document.getElementById('supply_id');
        
        if (!motherboardSelect || !cpuSelect || !ramSelect || !gpuSelect || !powerSupplySelect) {
            return;
        }
        
        const compatibilityDisplay = document.getElementById('compatibilityCheck');
        if (!compatibilityDisplay) return;
        
        // Простая проверка, просто чтобы показать принцип
        // В реальном приложении тут был бы AJAX-запрос для проверки совместимости на сервере
        
        if (motherboardSelect.value && cpuSelect.value && ramSelect.value) {
            compatibilityDisplay.innerHTML = '<i class="fas fa-check-circle me-2"></i>Компоненты совместимы';
            compatibilityDisplay.className = 'alert alert-success';
        } else {
            compatibilityDisplay.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i>Выберите основные компоненты для проверки совместимости';
            compatibilityDisplay.className = 'alert alert-info';
        }
    }
    
    // Переменная для дебаунсинга
    let priceCalculationTimeout = null;
    
    // Расчет итоговой стоимости конфигурации
    function calculateTotalPrice() {
        // Очищаем предыдущий таймаут
        if (priceCalculationTimeout) {
            clearTimeout(priceCalculationTimeout);
        }
        
        // Устанавливаем новый таймаут для дебаунсинга
        priceCalculationTimeout = setTimeout(() => {
            calculateTotalPriceImmediate();
        }, 100); // Задержка 100мс для предотвращения слишком частых вызовов
    }
    
    // Немедленный расчет цены (внутренняя функция)
    function calculateTotalPriceImmediate() {
        const priceDisplay = document.getElementById('totalPrice');
        if (!priceDisplay) return;
        
        const selects = document.querySelectorAll('form select[id$="_id"]');
        let total = 0;
        let foundPrices = [];
        
        selects.forEach(select => {
            if (select.value && select.value !== '0' && select.value !== '') {
                const selectedOption = select.options[select.selectedIndex];
                if (!selectedOption) return;
                
                const text = selectedOption.textContent;
                
                // Новый формат: "Название продукта • 12 345 ₽ • 🛒 Ситилинк • ⭐ 4.5 (10 отзывов)"
                // Ищем цену после символа • и перед символом ₽
                
                let priceMatch = null;
                let extractedPrice = null;
                
                // Основной паттерн для нового формата: "• число ₽"
                priceMatch = text.match(/•\s*([0-9\s]+)\s*₽/);
                if (priceMatch) {
                    // Убираем все пробелы из числа
                    const priceStr = priceMatch[1].replace(/\s/g, '');
                    extractedPrice = parseInt(priceStr, 10);
                } else {
                    // Поддержка других форматов
                    
                    // Формат: "Название (12 345 ₽)"
                    priceMatch = text.match(/\(([0-9\s,.]+)\s*₽\)/);
                    if (priceMatch) {
                        const priceStr = priceMatch[1].replace(/[\s,.]/g, '');
                        extractedPrice = parseInt(priceStr, 10);
                    } else {
                        // Формат: "Название - 12345 руб"
                        priceMatch = text.match(/(\d+)\s*руб/);
                        if (priceMatch) {
                            extractedPrice = parseInt(priceMatch[1], 10);
                        }
                    }
                }
                
                // Добавляем цену если она валидна
                if (extractedPrice && !isNaN(extractedPrice) && extractedPrice > 0) {
                    total += extractedPrice;
                    foundPrices.push({
                        component: select.id,
                        name: text.substring(0, 50) + (text.length > 50 ? '...' : ''),
                        price: extractedPrice
                    });
                }
            }
        });
        
        // Обновляем отображение цены
        if (priceDisplay) {
            priceDisplay.textContent = total.toLocaleString('ru-RU') + ' ₽';
        }
        
        // Логируем для отладки (только если есть цены)
        if (foundPrices.length > 0) {
            console.log('📊 Расчет цены:', {
                total: total,
                components: foundPrices
            });
        } else {
            console.log('💰 Итоговая цена: 0 ₽ (компоненты не выбраны или без цен)');
        }
    }
    
    // Инициализация обработчиков событий
    function initEventListeners() {
        const componentSelects = document.querySelectorAll('form select[id$="_id"]');
        
        componentSelects.forEach(select => {
            select.addEventListener('change', function() {
                checkCompatibility();
                calculateTotalPrice();
            });
        });
    }
    
    // Вызов функций инициализации
    setupComponentFilters();
    initEventListeners();
    checkCompatibility();
    calculateTotalPrice();
}); 