#!/bin/bash
set -e

echo "=== Запуск Конфигуратора ПК ==="

# Функция ожидания базы данных
wait_for_db() {
    echo "Ожидание готовности PostgreSQL..."
    
    for i in {1..30}; do
        if python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close()
    print('БД готова!')
except:
    exit(1)
        "; then
            echo "PostgreSQL готов для подключения!"
            return 0
        fi
        echo "Попытка $i/30: PostgreSQL не готов, ожидаем 2 секунды..."
        sleep 2
    done
    
    echo "Ошибка: PostgreSQL не готов после 60 секунд ожидания"
    exit 1
}

# Инициализация базы данных
init_db() {
    echo "Инициализация базы данных..."
    python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Таблицы базы данных созданы успешно!')
    "
}

# Основная логика
main() {
    # Ожидаем готовности БД
    wait_for_db
    
    # Инициализируем БД
    init_db
    
    echo "=== Запуск веб-сервера ==="
    # Запускаем приложение
    exec "$@"
}

# Запуск
main "$@" 
 