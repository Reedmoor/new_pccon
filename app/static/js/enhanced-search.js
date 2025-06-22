/**
 * Enhanced Component Search with Autocomplete
 * Улучшенный поиск компонентов с автодополнением
 */

class EnhancedComponentSearch {
    constructor(inputId, selectId, productType, apiUrl = '/api/autocomplete-components') {
        console.log(`Creating EnhancedComponentSearch for ${productType}`, { inputId, selectId, apiUrl });
        
        this.inputElement = document.getElementById(inputId);
        this.selectElement = document.getElementById(selectId);
        this.productType = productType;
        this.apiUrl = apiUrl;
        this.searchTimeout = null;
        this.activeIndex = -1;
        this.suggestions = [];
        
        console.log(`Elements found:`, { 
            input: !!this.inputElement, 
            select: !!this.selectElement 
        });
        
        this.init();
    }
    
    init() {
        if (!this.inputElement || !this.selectElement) {
            console.error('Search elements not found');
            return;
        }
        
        this.createSearchContainer();
        this.bindEvents();
    }
    
    createSearchContainer() {
        // Оборачиваем input в контейнер для автодополнения
        const container = document.createElement('div');
        container.className = 'search-autocomplete enhanced-search';
        
        // Создаем контейнер для input с кнопками
        const inputContainer = document.createElement('div');
        inputContainer.className = 'search-input-container';
        
        // Переносим input в новый контейнер
        this.inputElement.parentNode.insertBefore(container, this.inputElement);
        container.appendChild(inputContainer);
        inputContainer.appendChild(this.inputElement);
        
        // Добавляем кнопки
        const buttonsContainer = document.createElement('div');
        buttonsContainer.className = 'search-buttons';
        
        // Индикатор загрузки
        const loadingSpinner = document.createElement('div');
        loadingSpinner.className = 'search-loading';
        loadingSpinner.innerHTML = '<div class="search-spinner"></div>';
        buttonsContainer.appendChild(loadingSpinner);
        
        // Кнопка очистки
        const clearButton = document.createElement('button');
        clearButton.type = 'button';
        clearButton.className = 'search-btn clear-btn';
        clearButton.innerHTML = '×';
        clearButton.title = 'Очистить';
        clearButton.addEventListener('click', () => this.clearSearch());
        buttonsContainer.appendChild(clearButton);
        
        // Кнопка поиска
        const searchButton = document.createElement('button');
        searchButton.type = 'button';
        searchButton.className = 'search-btn';
        searchButton.innerHTML = '<i class="fas fa-search"></i>';
        searchButton.title = 'Поиск';
        searchButton.addEventListener('click', () => this.performFullSearch());
        buttonsContainer.appendChild(searchButton);
        
        inputContainer.appendChild(buttonsContainer);
        
        // Создаем dropdown для автодополнения
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'autocomplete-dropdown';
        container.appendChild(this.dropdown);
        
        this.loadingSpinner = loadingSpinner;
        this.searchButton = searchButton;
        this.clearButton = clearButton;
    }
    
    bindEvents() {
        // Автодополнение при вводе
        this.inputElement.addEventListener('input', (e) => {
            this.handleInput(e.target.value);
        });
        
        // Навигация клавишами
        this.inputElement.addEventListener('keydown', (e) => {
            this.handleKeyDown(e);
        });
        
        // Скрытие dropdown при клике вне
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-autocomplete')) {
                this.hideDropdown();
            }
        });
        
        // Фокус на input
        this.inputElement.addEventListener('focus', () => {
            if (this.suggestions.length > 0) {
                this.showDropdown();
            }
        });
    }
    
    handleInput(query) {
        clearTimeout(this.searchTimeout);
        
        if (query.length < 2) {
            this.hideDropdown();
            return;
        }
        
        // Задержка для избежания слишком частых запросов
        this.searchTimeout = setTimeout(() => {
            this.fetchSuggestions(query);
        }, 300);
    }
    
    async fetchSuggestions(query) {
        try {
            console.log(`Fetching suggestions for ${this.productType} with query: "${query}"`);
            this.showLoading(true);
            
            const url = new URL(this.apiUrl, window.location.origin);
            url.searchParams.append('product_type', this.productType);
            url.searchParams.append('query', query);
            url.searchParams.append('limit', '10');
            
            console.log(`API URL: ${url.toString()}`);
            
            const response = await fetch(url);
            console.log(`Response status: ${response.status}`);
            
            const data = await response.json();
            console.log(`API response:`, data);
            
            this.suggestions = data.suggestions || [];
            console.log(`Found ${this.suggestions.length} suggestions`);
            
            this.renderSuggestions();
            
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            this.suggestions = [];
            this.hideDropdown();
        } finally {
            this.showLoading(false);
        }
    }
    
    renderSuggestions() {
        this.dropdown.innerHTML = '';
        
        if (this.suggestions.length === 0) {
            this.hideDropdown();
            return;
        }
        
        this.suggestions.forEach((suggestion, index) => {
            const item = this.createSuggestionItem(suggestion, index);
            this.dropdown.appendChild(item);
        });
        
        this.showDropdown();
        this.activeIndex = -1;
    }
    
    createSuggestionItem(suggestion, index) {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.dataset.index = index;
        
        // Создаем изображение
        const image = document.createElement('img');
        image.className = 'autocomplete-image';
        image.src = suggestion.image_url;
        image.alt = suggestion.name;
        
        // Обработка ошибки загрузки изображения
        image.onerror = () => {
            // Скрываем неработающее изображение
            image.style.display = 'none';
            
            // Создаем контейнер с иконкой
            const iconContainer = document.createElement('div');
            iconContainer.className = 'autocomplete-image';
            iconContainer.innerHTML = this.getProductTypeIcon(this.productType);
            iconContainer.style.display = 'flex';
            iconContainer.style.alignItems = 'center';
            iconContainer.style.justifyContent = 'center';
            iconContainer.style.fontSize = '24px';
            iconContainer.style.backgroundColor = '#f8f9fa';
            iconContainer.style.border = '1px solid #e9ecef';
            iconContainer.style.borderRadius = '6px';
            
            // Заменяем изображение на иконку
            if (image.parentNode) {
                image.parentNode.insertBefore(iconContainer, image);
                image.parentNode.removeChild(image);
            }
        };
        
        // Создаем контент
        const content = document.createElement('div');
        content.className = 'autocomplete-content';
        
        const name = document.createElement('div');
        name.className = 'autocomplete-name';
        name.textContent = suggestion.name;
        name.title = suggestion.name;
        
        const priceRow = document.createElement('div');
        priceRow.className = 'autocomplete-price';
        
        const priceText = document.createElement('span');
        priceText.className = 'autocomplete-price-text';
        priceText.textContent = suggestion.price_text;
        
        const vendor = document.createElement('span');
        vendor.className = 'autocomplete-vendor';
        vendor.innerHTML = `${suggestion.vendor_icon} ${this.getVendorName(suggestion.vendor_icon)}`;
        
        priceRow.appendChild(priceText);
        priceRow.appendChild(vendor);
        
        content.appendChild(name);
        content.appendChild(priceRow);
        
        item.appendChild(image);
        item.appendChild(content);
        
        // Обработчик клика
        item.addEventListener('click', () => {
            this.selectSuggestion(suggestion);
        });
        
        return item;
    }
    
    getProductTypeIcon(productType) {
        const icons = {
            'processor': '🖥️',
            'graphics_card': '🎮',
            'motherboard': '🔌',
            'ram': '💾',
            'hard_drive': '💿',
            'power_supply': '🔋',
            'cooler': '❄️',
            'case': '📦'
        };
        return icons[productType] || '⚙️';
    }
    
    getVendorName(vendorIcon) {
        if (vendorIcon === '🟢') return 'DNS';
        if (vendorIcon === '🔵') return 'Citilink';
        return 'Другой';
    }
    
    selectSuggestion(suggestion) {
        // Обновляем input
        this.inputElement.value = suggestion.name;
        
        // Добавляем или обновляем option в select
        this.updateSelectOption(suggestion);
        
        // Скрываем dropdown
        this.hideDropdown();
        
        // Запускаем обновление информации о конфигурации если функция существует
        if (typeof updateConfigInfo === 'function') {
            updateConfigInfo();
        }
    }
    
    updateSelectOption(suggestion) {
        // Проверяем, есть ли уже такая опция
        let option = this.selectElement.querySelector(`option[value="${suggestion.id}"]`);
        
        if (!option) {
            // Создаем новую опцию
            option = document.createElement('option');
            option.value = suggestion.id;
            this.selectElement.appendChild(option);
        }
        
        // Обновляем текст и атрибуты
        option.textContent = `${suggestion.name} (${suggestion.price_text})`;
        option.selected = true;
        
        // Добавляем data-атрибуты
        option.dataset.price = suggestion.price_text;
        option.dataset.vendor = suggestion.vendor_icon;
    }
    
    handleKeyDown(e) {
        if (!this.dropdown.classList.contains('show')) {
            return;
        }
        
        const items = this.dropdown.querySelectorAll('.autocomplete-item');
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.activeIndex = Math.min(this.activeIndex + 1, items.length - 1);
                this.updateActiveItem(items);
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                this.activeIndex = Math.max(this.activeIndex - 1, -1);
                this.updateActiveItem(items);
                break;
                
            case 'Enter':
                e.preventDefault();
                if (this.activeIndex >= 0 && this.suggestions[this.activeIndex]) {
                    this.selectSuggestion(this.suggestions[this.activeIndex]);
                }
                break;
                
            case 'Escape':
                this.hideDropdown();
                this.inputElement.blur();
                break;
        }
    }
    
    updateActiveItem(items) {
        items.forEach((item, index) => {
            item.classList.toggle('active', index === this.activeIndex);
        });
    }
    
    showDropdown() {
        this.dropdown.classList.add('show');
    }
    
    hideDropdown() {
        this.dropdown.classList.remove('show');
        this.activeIndex = -1;
    }
    
    showLoading(show) {
        this.loadingSpinner.classList.toggle('show', show);
        this.searchButton.classList.toggle('loading', show);
    }
    
    clearSearch() {
        this.inputElement.value = '';
        this.hideDropdown();
        this.suggestions = [];
        
        // Сбрасываем select к первой опции
        if (this.selectElement.options.length > 0) {
            this.selectElement.selectedIndex = 0;
        }
        
        // Обновляем информацию о конфигурации
        if (typeof updateConfigInfo === 'function') {
            updateConfigInfo();
        }
    }
    
    async performFullSearch() {
        const query = this.inputElement.value.trim();
        if (!query) return;
        
        try {
            this.showLoading(true);
            
            const response = await fetch('/api/search-components', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    product_type: this.productType,
                    query: query,
                    limit: 50
                })
            });
            
            const data = await response.json();
            
            if (data.components && data.components.length > 0) {
                this.updateSelectWithResults(data.components);
            }
            
        } catch (error) {
            console.error('Error performing full search:', error);
        } finally {
            this.showLoading(false);
        }
    }
    
    updateSelectWithResults(components) {
        // Сохраняем первую опцию (Выберите...)
        const firstOption = this.selectElement.querySelector('option:first-child');
        
        // Очищаем select
        this.selectElement.innerHTML = '';
        
        // Возвращаем первую опцию
        if (firstOption) {
            this.selectElement.appendChild(firstOption);
        }
        
        // Добавляем найденные компоненты
        components.forEach(component => {
            const option = document.createElement('option');
            option.value = component.id;
            option.textContent = `${component.name} (${component.price_formatted})`;
            option.dataset.price = component.price_formatted;
            option.dataset.vendor = component.vendor_icon;
            this.selectElement.appendChild(option);
        });
        
        // Обновляем информацию о конфигурации
        if (typeof updateConfigInfo === 'function') {
            updateConfigInfo();
        }
    }
}

// Инициализация поиска для всех компонентов
document.addEventListener('DOMContentLoaded', function() {
    console.log('Enhanced search script loaded');
    
    // Определяем маппинг компонентов
    const searchConfigs = [
        { input: 'motherboardSearch', select: 'motherboard_id', type: 'motherboard' },
        { input: 'cpuSearch', select: 'cpu_id', type: 'processor' },
        { input: 'gpuSearch', select: 'gpu_id', type: 'graphics_card' },
        { input: 'ramSearch', select: 'ram_id', type: 'ram' },
        { input: 'hddSearch', select: 'hdd_id', type: 'hard_drive' },
        { input: 'supplySearch', select: 'supply_id', type: 'power_supply' },
        { input: 'coolerSearch', select: 'cooler_id', type: 'cooler' },
        { input: 'frameSearch', select: 'frame_id', type: 'case' }
    ];
    
    // Инициализируем поиск для каждого компонента
    searchConfigs.forEach(config => {
        const inputElement = document.getElementById(config.input);
        const selectElement = document.getElementById(config.select);
        
        console.log(`Checking ${config.input}: input=${!!inputElement}, select=${!!selectElement}`);
        
        if (inputElement && selectElement) {
            console.log(`Initializing search for ${config.type}`);
            new EnhancedComponentSearch(config.input, config.select, config.type);
        } else {
            console.warn(`Missing elements for ${config.type}: input=${!!inputElement}, select=${!!selectElement}`);
        }
    });
    
    console.log('Enhanced component search initialization completed');
}); 