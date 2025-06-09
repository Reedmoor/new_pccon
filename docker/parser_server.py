#!/usr/bin/env python3
"""
Parser Server для Docker контейнера
Запускает парсеры через API интерфейс
"""

import os
import sys
import logging
from flask import Flask, request, jsonify
import threading
import time

# Добавляем путь к парсерам
sys.path.append('/app/parsers')

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/parser_server.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервиса"""
    return jsonify({"status": "healthy", "service": "parser"}), 200

@app.route('/parse/citilink', methods=['POST'])
def parse_citilink():
    """Запуск парсера Citilink"""
    try:
        data = request.json
        category = data.get('category', '')
        
        logger.info(f"Starting Citilink parsing for category: {category}")
        
        # Здесь должен быть код запуска парсера Citilink
        # Пока возвращаем успешный ответ
        
        return jsonify({
            "status": "success",
            "message": f"Citilink parsing started for category: {category}"
        }), 200
        
    except Exception as e:
        logger.error(f"Error in Citilink parsing: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/parse/dns', methods=['POST'])
def parse_dns():
    """Запуск парсера DNS"""
    try:
        data = request.json
        category = data.get('category', '')
        
        logger.info(f"Starting DNS parsing for category: {category}")
        
        # Здесь должен быть код запуска парсера DNS
        # Пока возвращаем успешный ответ
        
        return jsonify({
            "status": "success",
            "message": f"DNS parsing started for category: {category}"
        }), 200
        
    except Exception as e:
        logger.error(f"Error in DNS parsing: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Получение статуса парсеров"""
    return jsonify({
        "parsers": {
            "citilink": "ready",
            "dns": "ready"
        }
    }), 200

if __name__ == '__main__':
    logger.info("Starting Parser Server...")
    app.run(host='0.0.0.0', port=5001, debug=False) 