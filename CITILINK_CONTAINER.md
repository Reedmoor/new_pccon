# Контейнер Парсинга Citilink

## Описание

Легкий контейнер только для парсинга Citilink (без Selenium), который работает через API запросы и не блокирует основное приложение.

## Настройки Контейнера

### Параметры для создания контейнера:

- **Имя контейнера**: `citilink-parser`
- **Образ**: `python:3.11-slim`
- **Количество реплик**: 1
- **Процессор**: 1 CPU (20% резервирования)
- **Память**: 512 MiB (достаточно для API запросов)
- **Порт**: 5001
- **Переменные окружения**:
  - `PYTHONPATH=/app`

### Команда инициализации:
```bash
pip install Flask==3.0.0 requests==2.31.0 lxml==4.9.3 python-dotenv==1.0.0 psutil==5.9.6
```

### Команда выполнения:
```bash
python citilink_worker.py
```

## Зависимости (requirements-citilink.txt)
```
Flask==3.0.0
requests==2.31.0
lxml==4.9.3
python-dotenv==1.0.0
psutil==5.9.6
```

## Файловая структура в контейнере

```
/app/
├── citilink_worker.py        # Основной API сервер
├── app/utils/Citi_parser/    # Citilink парсер
├── data/                     # Папка для сохранения данных
└── logs/                     # Логи контейнера
```

## API Endpoints

### Проверка состояния
- `GET /health` - Проверка здоровья контейнера
- `GET /status` - Текущий статус парсера

### Управление парсингом
- `POST /start-parsing` - Запуск парсинга Citilink
- `POST /stop-parsing` - Остановка парсинга
- `GET /available-categories` - Доступные категории Citilink

### Данные
- `GET /data/local` - Локально сохраненные данные
- `POST /data/send` - Отправка данных на основной сервер

### Логи
- `GET /logs` - Получение логов парсера

## Запуск парсинга

### Citilink Парсер
```json
POST /start-parsing
{
  "category": "videokarty",
  "server_url": "http://pcconf.ru"
}
```

## Доступные категории Citilink

- videokarty
- processory
- materinskie-platy
- moduli-pamyati
- bloki-pitaniya
- korpusa
- sistemy-ohlazhdeniya-processora
- ssd-nakopiteli
- zhestkie-diski

## Интеграция с основным приложением

Основное приложение может управлять контейнером через API:

### Обновленные API роуты в admin.py:
```python
# Замените URL в admin.py с "http://parsing:5001" на "http://citilink-parser:5001"
parser_url = "http://citilink-parser:5001"
```

## Преимущества

1. **Легкий**: Только 512 MiB памяти, без Chrome/Selenium
2. **Быстрый**: Парсинг через API запросы
3. **Независимый**: Не блокирует основное приложение
4. **Простой**: Минимум зависимостей
5. **Надежный**: API запросы стабильнее браузерной автоматизации

## Пример использования

### 1. Запуск парсинга видеокарт:
```bash
curl -X POST http://citilink-parser:5001/start-parsing \
  -H "Content-Type: application/json" \
  -d '{"category": "videokarty", "server_url": "http://pcconf.ru"}'
```

### 2. Проверка статуса:
```bash
curl http://citilink-parser:5001/status
```

### 3. Получение данных:
```bash
curl http://citilink-parser:5001/data/local
```

## Мониторинг

- Логи: `/app/logs/citilink_worker.log`
- Статус через: `GET /status`
- Данные в: `/app/data/citilink_*.json`

## Простая настройка

### Если используете готовый образ:

1. **Образ**: `python:3.11-slim`
2. **Команда инициализации**:
   ```bash
   pip install Flask requests lxml python-dotenv psutil
   ```
3. **Команда выполнения**:
   ```bash
   python -c "
   from flask import Flask, jsonify
   app = Flask(__name__)
   
   @app.route('/health')
   def health():
       return jsonify({'status': 'healthy', 'service': 'citilink-parser'})
   
   @app.route('/status')
   def status():
       return jsonify({'status': 'idle', 'message': 'Citilink parser ready'})
   
   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=5001)
   "
   ```

Этот вариант создаст базовый контейнер, который можно затем расширить загрузкой полного кода. 