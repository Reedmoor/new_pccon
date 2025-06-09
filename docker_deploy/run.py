import os
from app import create_app, db

app = create_app()

@app.cli.command("init-db")
def init_db():
    """Создание всех моделей базы данных."""
    db.create_all()
    print("База данных инициализирована.")

if __name__ == '__main__':
    # Инициализация базы данных при первом запуске
    with app.app_context():
        try:
            db.create_all()
            print("База данных инициализирована")
        except Exception as e:
            print(f"Ошибка инициализации базы данных: {e}")
    
    # Запуск приложения
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 