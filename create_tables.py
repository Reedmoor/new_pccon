from app import create_app, db
from app.models.models import User, UnifiedProduct, Configuration

app = create_app()

def create_tables():
    """Создает таблицы в базе данных"""
    with app.app_context():
        print("Попытка создания таблиц...")
        try:
            db.create_all()
            print("Таблицы успешно созданы!")
            return True
        except Exception as e:
            print(f"Ошибка при создании таблиц: {e}")
            return False

if __name__ == "__main__":
    create_tables() 