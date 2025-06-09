import os
from app import create_app, db

# Создаем приложение
app = create_app()

@app.cli.command("init-db")
def init_db():
    """Создание всех моделей базы данных."""
    db.create_all()
    print("База данных инициализирована.")

@app.before_first_request
def create_tables():
    """Автоматическое создание таблиц при первом запросе."""
    try:
        db.create_all()
        print("Таблицы созданы успешно")
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")

if __name__ == '__main__':
    # Для локальной разработки
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode) 