# Система управления данными ПК (только BAT файлы)

Простая система для парсинга и синхронизации данных **БЕЗ веб-интерфейса** - только через bat файлы.

## 🔌 Важно: Порты серверов

- **🏠 Локальный сервер**: http://127.0.0.1:5001 (парсинг и локальные операции)
- **🐳 Docker сервер**: http://127.0.0.1:5000 (финальное хранение)
- **🌐 Удаленный сервер**: https://yourdomain.com (захощенный сервер)
- **📋 Подробнее**: см. файл `PORTS_INFO.md`

## 🚨 Быстрое исправление Python

**Если видите ошибку "python.exe не найден":**

```bash
# Запустите для диагностики и исправления:
fix_python.bat
```

## 🚀 Быстрый старт

### Главное меню
```bash
main_menu.bat
```
Интерактивное меню со всеми операциями.

### Новый workflow (через старый парсер):

#### 1. Парсинг категории
```bash
parse_category.bat
```
- Выбор категории из списка (1-10)
- Ввод количества товаров  
- **Прямой запуск старого парсера** (без wrapper)
- Результаты в `old_dns_parser/product_data.json`

#### 2. Загрузка данных из старого парсера
```bash
upload_from_old_parser.bat
```
- Загрузка на локальный сервер 5001
- Загрузка на Docker сервер 5000
- Выбор сервера перед загрузкой

#### 3. Загрузка на удаленный сервер (🆕 НОВОЕ!)
```bash
upload_to_remote.bat
```
- Загрузка на ваш захощенный сервер
- Интерактивная настройка URL
- Проверка подключения и статуса

#### Старый способ (импорт данных):
```bash
import_data.bat  
```
- Импорт локальных данных на 5001
- Синхронизация серверов 5001→5000
- Загрузка данных на Docker 5000
- Полный цикл через wrapper

## 📁 Основные BAT файлы

### Новые интерактивные файлы
- `main_menu.bat` - **Главное меню со всеми операциями**
- `parse_category.bat` - **Парсинг через старый парсер (прямой запуск)**
- `upload_from_old_parser.bat` - **Загрузка из old_dns_parser на сервер**
- `upload_to_remote.bat` - **🆕 Загрузка на удаленный сервер**
- `import_data.bat` - **Импорт с выбором типа операции (старый способ)**

### Python скрипты для удаленного сервера
- `upload_to_remote_server.py` - **🆕 Основной скрипт для удаленного сервера**
- `remote_config.json.template` - **🆕 Шаблон конфигурации**

### Python и настройки
- `fix_python.bat` - **🆘 БЫСТРОЕ исправление Python**
- `setup_python.bat` - Полная настройка Python окружения
- `get_python.bat` - Автоопределение команды Python

### Существующие файлы
- `sync_5001_to_5000_docker.bat` - Синхронизация серверов
- `test_docker_integration.bat` - Тестирование Docker
- `upload_existing_to_docker.bat` - Загрузка существующих данных

### Справочники
- `PORTS_INFO.md` - **📋 Подробная информация о портах**
- `REMOTE_IMPORT_GUIDE.md` - **🌐 Руководство по удаленному серверу**

## 🎯 Доступные категории

1. **videokarty** (Видеокарты)
2. **processory** (Процессоры) 
3. **operativnaya-pamyat** (Оперативная память)
4. **materinskie-platy** (Материнские платы)
5. **kulery** (Кулеры)
6. **korpusa** (Корпуса)
7. **bloki-pitaniya** (Блоки питания)
8. **zhestkie-diski** (Жесткие диски)
9. **ssd-m2** (SSD M.2 накопители)
10. **ssd-sata** (SSD SATA накопители)

⚠️ **Важно**: Используйте точные названия с дефисами, как указано выше!

## 🔧 Примеры использования

### Парсинг видеокарт
```bash
# Запустите parse_category.bat
# Выберите: 1 (videokarty)
# Введите количество: 20
# Подтвердите: y
# Данные сохранятся на локальный сервер 5001
```

### Парсинг SSD M.2
```bash
# Запустите parse_category.bat
# Выберите: 9 (ssd-m2)
# Введите количество: 15
# Подтвердите: y
```

### Синхронизация данных
```bash
# Запустите import_data.bat  
# Выберите: 2 (Синхронизация серверов)
# Данные перенесутся с 5001 на 5000
```

### Полный цикл
```bash
# Запустите import_data.bat
# Выберите: 4 (Полный цикл)
# Введите категорию: ssd-m2  (с дефисом!)
# Введите количество: 15
# Данные сохранятся на локальный сервер 5001
```

## 📊 Структура операций

```
main_menu.bat
├── 1. parse_category.bat      # Парсинг → old_dns_parser
├── 2. import_data.bat         # Импорт данных (старый способ)
│   ├── 1. Локальные данные → 5001
│   ├── 2. Синхронизация 5001 → 5000
│   ├── 3. Существующие данные → 5000
│   └── 4. Полный цикл → 5001
├── 3. sync_5001_to_5000_docker.bat
├── 4. upload_to_remote.bat    # 🆕 НОВЫЙ: загрузка на удаленный сервер
├── 5. analyze_duplicates      # Анализ дублей
├── 6. test_docker_integration.bat
├── 7. check_server_data.py    # Проверка данных
├── 8. local_data_manager.py   # Управление файлами
├── 9. upload_existing_to_docker.bat
├── 10. upload_from_old_parser.bat  # 🚀 НОВЫЙ: загрузка из старого парсера
└── 11. setup_python.bat       # Настройка Python
```

## 🔄 Рекомендуемый workflow:

### Для локального развертывания:
1. **Парсинг**: `parse_category.bat` → выбираете категорию → данные в `old_dns_parser/product_data.json`
2. **Загрузка**: `upload_from_old_parser.bat` → выбираете сервер (5001/5000) → данные на сервере
3. **Проверка**: открываете веб-интерфейс выбранного сервера

### Для удаленного сервера:
1. **Парсинг**: `parse_category.bat` → выбираете категорию → данные в `old_dns_parser/product_data.json`
2. **Загрузка на удаленный сервер**: `upload_to_remote.bat` → вводите URL → данные на удаленном сервере
3. **Проверка**: открываете ваш удаленный сайт в браузере

## ⚡ Быстрые команды

```bash
# Главное меню
main_menu.bat

# Исправление Python (ВАЖНО!)
fix_python.bat

# Парсинг конкретной категории
parse_category.bat

# Импорт данных  
import_data.bat

# Загрузка на удаленный сервер (НОВОЕ!)
upload_to_remote.bat

# Синхронизация
sync_5001_to_5000_docker.bat

# Тестирование
test_docker_integration.bat
```

## 🎮 Особенности интерфейса

- **Автоопределение Python** - скрипты сами найдут нужную команду
- **Правильные порты** - автоматически используют нужные порты
- **Интерактивный выбор** категорий и параметров
- **Валидация ввода** с проверкой корректности
- **Подтверждение операций** перед выполнением  
- **Цветной вывод** с иконками и статусами
- **Возврат в меню** после каждой операции
- **Обработка ошибок** с понятными сообщениями

## 🔍 Проверка результатов

После любой операции:
- **Локальный сервер**: http://127.0.0.1:5001
- **Docker сервер**: http://127.0.0.1:5000
- **Удаленный сервер**: https://yourdomain.com (ваш домен)
- **Статус серверов**: `test_docker_integration.bat`
- **Данные на серверах**: через главное меню → пункт 7

## 🌐 Удаленный сервер (НОВОЕ!)

### Быстрый старт с удаленным сервером
```bash
# 1. Запарсите данные локально
parse_category.bat

# 2. Загрузите на удаленный сервер
upload_to_remote.bat

# 3. Введите URL вашего сервера
# Пример: https://yourdomain.com

# 4. Выберите действие:
# - Проверить подключение
# - Загрузить последние данные
# - Проверить статус сервера
```

### Поддерживаемые форматы URL
- `https://yourdomain.com` (рекомендуется)
- `http://192.168.1.100:5000` (для тестирования)
- `https://subdomain.yourdomain.com`

### См. также
- `REMOTE_IMPORT_GUIDE.md` - Подробное руководство по удаленному серверу

## 🛠️ Устранение неполадок

### Python не найден
```bash
# ГЛАВНАЯ команда для исправления:
fix_python.bat

# Альтернативы:
setup_python.bat    # Полная настройка
main_menu.bat       # Пункт 11 - настройка Python
```

### Локальный сервер недоступен (5001)
```bash
# Запустите локальный сервер:
cd ..
python run.py
```

### Docker сервер недоступен (5000)
```bash
docker-compose up -d
test_docker_integration.bat
```

### Нет локальных данных
```bash
# Сначала парсинг
parse_category.bat
# Затем импорт
import_data.bat
```

### Много дублей
```bash
# Через главное меню:
main_menu.bat → пункт 4
```

## 🐍 Python конфигурация

Система автоматически ищет Python в следующем порядке:
1. **venv\Scripts\python.exe** (виртуальное окружение)
2. **python** (системная команда)
3. **python3** (альтернативная команда)
4. **py** (Python launcher)
5. Сохраненная команда в `python_cmd.txt`

## 📝 Логирование

Все операции выводят детальную информацию:
- ✅ Успешные операции
- ❌ Ошибки с описанием
- 📊 Статистика по товарам
- ⏱️ Время выполнения
- 🐍 Используемая команда Python
- 🔌 Используемые порты серверов 