#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных в production
"""

import os
import sys
import time
from app import create_app, db

def wait_for_db(max_retries=30, delay=2):
    """Ожидание готовности базы данных"""
    print("Ожидание готовности базы данных...")
    
    for attempt in range(max_retries):
        try:
            # Пытаемся подключиться к БД
            app = create_app()
            with app.app_context():
                db.engine.execute('SELECT 1')
            print("База данных готова!")
            return True
        except Exception as e:
            print(f"Попытка {attempt + 1}/{max_retries}: БД не готова ({e})")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    print("Не удалось дождаться готовности базы данных")
    return False

def init_database():
    """Инициализация базы данных"""
    print("Инициализация базы данных...")
    
    try:
        app = create_app()
        with app.app_context():
            # Создаем все таблицы
            db.create_all()
            print("Таблицы базы данных созданы успешно!")
            
            # Здесь можно добавить создание администратора или другие начальные данные
            
        return True
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        return False

if __name__ == "__main__":
    print("=== Инициализация базы данных ===")
    
    # Ждем готовности БД
    if not wait_for_db():
        sys.exit(1)
    
    # Инициализируем БД
    if not init_database():
        sys.exit(1)
    
    print("=== Инициализация завершена успешно ===") 