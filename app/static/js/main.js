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
            option.textContent = `${component.name} - ${component.price} руб.`;
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
    
    // Расчет итоговой стоимости конфигурации
    function calculateTotalPrice() {
        const priceDisplay = document.getElementById('totalPrice');
        if (!priceDisplay) return;
        
        const selects = document.querySelectorAll('form select[id$="_id"]');
        let total = 0;
        
        selects.forEach(select => {
            if (select.value) {
                const selectedOption = select.options[select.selectedIndex];
                const priceMatch = selectedOption.textContent.match(/(\d+) руб/);
                if (priceMatch && priceMatch[1]) {
                    total += parseInt(priceMatch[1], 10);
                }
            }
        });
        
        priceDisplay.textContent = total.toLocaleString() + ' ₽';
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