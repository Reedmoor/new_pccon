#!/bin/bash
set -e

echo "=== Запуск Конфигуратора ПК ==="

# Функция ожидания базы данных
wait_for_db() {
    echo "Ожидание готовности PostgreSQL..."
    echo "DATABASE_URL: $DATABASE_URL"
    
    # Даем PostgreSQL время на запуск (30 секунд)
    echo "Даем PostgreSQL время на инициализацию (30 секунд)..."
    sleep 30
    
    # Увеличиваем время ожидания до 120 секунд (60 попыток по 2 секунды)
    for i in {1..60}; do
        echo "Попытка $i/60: Проверяем подключение к PostgreSQL..."
        
        if python -c "
import psycopg2
import os
import sys
try:
    # Парсим DATABASE_URL для отладки
    db_url = os.environ.get('DATABASE_URL', '')
    print(f'Пытаемся подключиться к: {db_url}')
    
    if not db_url:
        print('ОШИБКА: DATABASE_URL пустая!')
        sys.exit(1)
    
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print(f'PostgreSQL версия: {version[0]}')
    cursor.close()
    conn.close()
    print('Подключение к БД успешно!')
    sys.exit(0)
except psycopg2.OperationalError as e:
    print(f'Ошибка подключения: {e}')
    sys.exit(1)
except Exception as e:
    print(f'Неожиданная ошибка: {e}')
    sys.exit(1)
        "; then
            echo "PostgreSQL готов для подключения!"
            return 0
        fi
        
        echo "PostgreSQL не готов, ожидаем 2 секунды..."
        sleep 2
    done
    
    echo "КРИТИЧЕСКАЯ ОШИБКА: PostgreSQL не готов после 120 секунд ожидания"
    echo "Проверьте:"
    echo "1. Запущен ли контейнер PostgreSQL"
    echo "2. Правильность DATABASE_URL: $DATABASE_URL"
    echo "3. Логи контейнера PostgreSQL"
    exit 1
}

# Инициализация базы данных
init_db() {
    echo "Инициализация базы данных..."
    
    python -c "
import sys
import traceback
try:
    from app import create_app, db
    print('Модули импортированы успешно')
    
    app = create_app()
    print('Flask приложение создано')
    
    with app.app_context():
        print('Создаем таблицы...')
        db.create_all()
        print('Таблицы базы данных созданы успешно!')
        
        # Проверяем созданные таблицы
        from sqlalchemy import text
        result = db.session.execute(text('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = :schema'), {'schema': 'public'})
        table_count = result.fetchone()[0]
        print(f'Создано таблиц: {table_count}')
        
except Exception as e:
    print(f'Ошибка при инициализации базы данных: {e}')
    traceback.print_exc()
    sys.exit(1)
    "
    
    if [ $? -eq 0 ]; then
        echo "База данных инициализирована успешно!"
    else
        echo "ОШИБКА: Не удалось инициализировать базу данных"
        exit 1
    fi
}

# Основная логика
main() {
    echo "Переменные окружения:"
    echo "FLASK_ENV: $FLASK_ENV"
    echo "DATABASE_URL: ${DATABASE_URL:0:50}..."
    echo "PYTHONPATH: $PYTHONPATH"
    
    # Проверяем обязательные переменные
    if [ -z "$DATABASE_URL" ]; then
        echo "КРИТИЧЕСКАЯ ОШИБКА: DATABASE_URL не установлена!"
        exit 1
    fi
    
    # Ожидаем готовности БД
    wait_for_db
    
    # Инициализируем БД
    init_db
    
    echo "=== Запуск веб-сервера ==="
    echo "Команда запуска: $@"
    
    # Запускаем приложение
    exec "$@"
}

# Запуск с обработкой ошибок
main "$@" || {
    echo "КРИТИЧЕСКАЯ ОШИБКА при запуске приложения"
    echo "Логи выше содержат детали ошибки"
    exit 1
} 