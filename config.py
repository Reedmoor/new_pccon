import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()  # Загрузка переменных из .env файла

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:123456@localhost:5432/uipc'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-key'

engine = create_engine('postgresql://postgres:123456@localhost:5432/uipc')
connection = engine.connect()