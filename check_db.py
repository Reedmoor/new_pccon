#!/usr/bin/env python3
"""
Простой скрипт для проверки подключения к PostgreSQL
Используется для отладки проблем с базой данных
"""

import os
import psycopg2
import sys
import time

def check_connection():
    """Проверяет подключение к PostgreSQL"""
    
    database_url = os.getenv('DATABASE_URL', 'postgresql://pccon_user:12345@db:5432/pccon_db')
    
    print(f"Проверяем подключение к: {database_url}")
    print(f"Переменные окружения:")
    print(f"  FLASK_ENV: {os.getenv('FLASK_ENV', 'не установлена')}")
    print(f"  PYTHONPATH: {os.getenv('PYTHONPATH', 'не установлена')}")
    
    try:
        # Попытка подключения
        print("Подключаемся к PostgreSQL...")
        conn = psycopg2.connect(database_url)
        
        # Выполняем тестовый запрос
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        print(f"✅ Успешно! PostgreSQL версия: {version[0]}")
        
        # Проверяем существующие таблицы
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"📋 Найдено таблиц: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("⚠️  Таблицы не найдены - возможно база данных не инициализирована")
        
        cursor.close()
        conn.close()
        
        print("🎉 Подключение к PostgreSQL работает корректно!")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        print("\n🔍 Возможные причины:")
        print("  1. PostgreSQL сервер не запущен")
        print("  2. Неправильные учетные данные")
        print("  3. Сетевые проблемы")
        print("  4. PostgreSQL еще не готов к подключениям")
        return False
        
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def wait_and_check(max_attempts=10, delay=3):
    """Ожидает готовности PostgreSQL с несколькими попытками"""
    
    print(f"🔄 Начинаем проверку с {max_attempts} попытками (интервал {delay}с)")
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n--- Попытка {attempt}/{max_attempts} ---")
        
        if check_connection():
            return True
            
        if attempt < max_attempts:
            print(f"⏳ Ожидаем {delay} секунд до следующей попытки...")
            time.sleep(delay)
    
    print(f"\n💥 Не удалось подключиться после {max_attempts} попыток")
    return False

if __name__ == "__main__":
    print("=== Проверка подключения к PostgreSQL ===")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--wait':
        success = wait_and_check()
    else:
        success = check_connection()
    
    sys.exit(0 if success else 1) 