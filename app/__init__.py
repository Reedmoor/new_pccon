from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
from datetime import datetime

# Загрузка переменных окружения
load_dotenv()

# Инициализация расширений
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# Function to get current datetime for templates
def get_now():
    return datetime.now()

def create_app():
    app = Flask(__name__)
    
    # Конфигурация
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')
    
    # Прямое указание параметров базы данных
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:12345@localhost:5432/uipc'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Отладочный вывод для проверки подключения к БД
    print(f"Попытка подключения к базе данных: postgresql://postgres:***@localhost:5432/uipc")
    
    # Инициализация расширений с приложением
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Регистрация blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.config import config_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(config_bp, url_prefix='/config')
    
    # Register functions for Jinja templates
    app.jinja_env.globals.update(abs=abs)
    app.jinja_env.globals.update(now=get_now)
    
    return app 