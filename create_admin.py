#!/usr/bin/env python3
"""
Скрипт для создания администратора и инициализации базы данных
"""

from app import create_app, db
from app.models.models import User, UnifiedProduct
import sys

def create_admin():
    """Создание администратора"""
    app = create_app()
    
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        
        # Проверяем, есть ли уже администратор
        admin = User.query.filter_by(email='admin@pccon.com').first()
        
        if admin:
            print("Администратор уже существует!")
            print(f"Email: {admin.email}")
            print(f"Роль: {admin.role}")
        else:
            # Создаем администратора
            admin = User(
                name='Администратор',
                email='admin@pccon.com',
                role='admin'
            )
            admin.set_password('admin')  # Пароль: admin
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Администратор создан успешно!")
            print("Email: admin@pccon.com")
            print("Пароль: admin")
            print("Роль: admin")
        
        # Выводим статистику
        users_count = User.query.count()
        products_count = UnifiedProduct.query.count()
        
        print(f"\n📊 Статистика базы данных:")
        print(f"Пользователей: {users_count}")
        print(f"Товаров: {products_count}")
        
        print(f"\n🔗 Ссылки:")
        print(f"Главная: http://localhost:5001/")
        print(f"Админ панель: http://localhost:5001/admin/")
        print(f"Локальный парсер: http://localhost:5001/admin/local-parser")

if __name__ == '__main__':
    create_admin() 