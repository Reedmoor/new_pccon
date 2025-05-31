from app import create_app, db
from sqlalchemy import text

def test_sqlalchemy_connection():
    """Тестирует подключение к БД через SQLAlchemy"""
    app = create_app()
    print("Создано приложение Flask")
    
    with app.app_context():
        try:
            # Проверка подключения с явным указанием текстового запроса
            result = db.session.execute(text('SELECT 1')).scalar()
            print(f"Подключение к БД через SQLAlchemy успешно! Результат запроса: {result}")
            return True
        except Exception as e:
            print(f"Ошибка подключения через SQLAlchemy: {e}")
            return False

if __name__ == "__main__":
    test_sqlalchemy_connection() 