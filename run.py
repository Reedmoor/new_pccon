import os
import time
import sys
from app import create_app, db

# Создаем приложение
app = create_app()

def wait_for_database(max_retries=30, delay=2):
    """Ожидание готовности базы данных"""
    print("Ожидание готовности базы данных...")
    
    for attempt in range(max_retries):
        try:
            with app.app_context():
                # Пытаемся выполнить простой запрос
                db.engine.execute('SELECT 1')
                print("База данных готова!")
                return True
        except Exception as e:
            print(f"Попытка {attempt + 1}/{max_retries}: БД не готова ({e})")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    print("ОШИБКА: База данных не готова после всех попыток")
    return False

def init_database():
    """Инициализация базы данных"""
    try:
        with app.app_context():
            print("Создание таблиц базы данных...")
            db.create_all()
            
            # Проверяем созданные таблицы
            result = db.engine.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            )
            table_count = result.fetchone()[0]
            print(f"Успешно! Создано таблиц: {table_count}")
            return True
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        return False

@app.cli.command("init-db")
def init_db():
    """Создание всех моделей базы данных."""
    if wait_for_database():
        if init_database():
            print("База данных инициализирована успешно!")
        else:
            sys.exit(1)
    else:
        sys.exit(1)

# Автоматическая инициализация при запуске в production
if os.environ.get('FLASK_ENV') == 'production':
    print("=== Production режим: автоматическая инициализация БД ===")
    if wait_for_database():
        init_database()
    else:
        print("КРИТИЧЕСКАЯ ОШИБКА: Не удается подключиться к БД")
        # В production не останавливаем приложение, а продолжаем запуск
        # Возможно, БД станет доступна позже

if __name__ == '__main__':
    # Для локальной разработки
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode) 