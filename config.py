import os
from dotenv import load_dotenv

load_dotenv()  # Загрузка переменных из .env файла

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:123456@localhost:5432/uipc'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-key'

# Убрано создание engine и connection при импорте
# Это должно происходить через Flask-SQLAlchemy в приложении