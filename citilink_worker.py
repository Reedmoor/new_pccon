#!/usr/bin/env python3
"""
Рабочий процесс для контейнера парсинга Citilink
Предоставляет API для управления парсингом Citilink и отправки данных
"""

import os
import sys
import json
import logging
import time
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
import subprocess
import requests

# Добавляем пути к модулям
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "app" / "utils" / "Citi_parser"))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/citilink_worker.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('citilink_worker')

app = Flask(__name__)

# Глобальные переменные для отслеживания состояния
parser_status = {
    'status': 'idle',  # idle, running, completed, error
    'current_task': None,
    'start_time': None,
    'end_time': None,
    'products_parsed': 0,
    'error_message': None,
    'progress': 0,
    'category': None
}

def update_status(status, task=None, products=0, error=None, progress=0, category=None):
    """Обновление статуса парсера"""
    parser_status['status'] = status
    parser_status['current_task'] = task
    parser_status['products_parsed'] = products
    parser_status['error_message'] = error
    parser_status['progress'] = progress
    if category:
        parser_status['category'] = category
    
    if status == 'running' and parser_status['start_time'] is None:
        parser_status['start_time'] = datetime.now().isoformat()
        parser_status['end_time'] = None
    elif status in ['completed', 'error']:
        parser_status['end_time'] = datetime.now().isoformat()

def run_citilink_parsing_task(category, server_url="http://pcconf.ru"):
    """Запуск задачи парсинга Citilink в отдельном потоке"""
    try:
        update_status('running', 'Initializing Citilink parser', 0, None, 10, category)
        logger.info(f"Starting Citilink parsing task for category: {category}")
        
        # Переходим в папку Citilink парсера
        citi_parser_dir = current_dir / "app" / "utils" / "Citi_parser"
        os.chdir(citi_parser_dir)
        
        # Создаем .env файл с категорией
        env_content = f"CATEGORY={category}"
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        logger.info(f"Created .env file with category: {category}")
        
        update_status('running', f'Parsing Citilink category: {category}', 0, None, 30, category)
        
        # Запускаем парсер Citilink
        result = subprocess.run(
            [sys.executable, 'main.py'],
            cwd=citi_parser_dir,
            capture_output=True,
            text=True,
            timeout=1800  # 30 минут
        )
        
        if result.returncode == 0:
            # Парсинг успешен, читаем последний дамп citilink_*.json
            products_count = 0
            products_data = []
            products_file = None
            citilink_flat = citi_parser_dir / 'data' / 'citilink'

            if citilink_flat.is_dir():
                dumps = sorted(citilink_flat.glob('citilink_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
                if dumps:
                    products_file = dumps[0]

            if products_file and products_file.exists():
                try:
                    with open(products_file, 'r', encoding='utf-8') as f:
                        products_data = json.load(f)
                    products_count = len(products_data)
                    target_file = Path('/app/data') / f'citilink_{category}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                    with open(target_file, 'w', encoding='utf-8') as f:
                        json.dump(products_data, f, ensure_ascii=False, indent=2)
                    logger.info(f"Citilink data saved to: {target_file}")
                except Exception as e:
                    logger.error(f"Error reading Citilink results: {e}")
            
            update_status('running', 'Sending data to server', products_count, None, 90, category)
            
            # Отправляем данные на сервер через API (сразу в БД)
            try:
                upload_url = f"{server_url.rstrip('/')}/api/upload-products"
                response = requests.post(upload_url, json={
                    'products': products_data,
                    'source': 'citilink',
                    'upload_type': 'single_file',
                    'category': category,
                }, timeout=180)
                
                if response.status_code == 200:
                    logger.info("Data successfully sent to main server")
                else:
                    logger.warning(f"Failed to send data to server: HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"Error sending data to server: {e}")
            
            update_status('completed', f'Successfully parsed {products_count} products from {category}', products_count, None, 100, category)
            logger.info(f"Citilink parsing completed successfully. Products: {products_count}")
        else:
            error_msg = f"Citilink parser failed with return code {result.returncode}"
            if result.stderr:
                error_msg += f": {result.stderr}"
            update_status('error', 'Citilink parsing failed', 0, error_msg, 100, category)
            logger.error(error_msg)
    
    except subprocess.TimeoutExpired:
        error_msg = "Citilink parser timed out after 30 minutes"
        update_status('error', 'Parsing timeout', 0, error_msg, 100, category)
        logger.error(error_msg)
    except Exception as e:
        error_msg = str(e)
        update_status('error', 'Citilink parsing failed', 0, error_msg, 0, category)
        logger.error(f"Citilink parsing task failed: {error_msg}")
    finally:
        # Возвращаемся в исходную директорию
        os.chdir(current_dir)

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья контейнера"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'citilink-parser'
    })

@app.route('/status', methods=['GET'])
def get_status():
    """Получение текущего статуса парсера"""
    return jsonify(parser_status)

@app.route('/start-parsing', methods=['POST'])
def start_parsing():
    """Запуск парсинга Citilink"""
    if parser_status['status'] == 'running':
        return jsonify({
            'success': False,
            'message': 'Parsing is already running'
        }), 400
    
    data = request.get_json() or {}
    category = data.get('category', None)
    server_url = data.get('server_url', 'http://pcconf.ru')
    
    if not category:
        return jsonify({
            'success': False,
            'message': 'Category is required for Citilink parser'
        }), 400
    
    # Сброс статуса
    parser_status.update({
        'status': 'idle',
        'current_task': None,
        'start_time': None,
        'end_time': None,
        'products_parsed': 0,
        'error_message': None,
        'progress': 0,
        'category': None
    })
    
    # Запуск парсинга в отдельном потоке
    parsing_thread = threading.Thread(
        target=run_citilink_parsing_task,
        args=(category, server_url),
        daemon=True
    )
    parsing_thread.start()
    
    return jsonify({
        'success': True,
        'message': f'Citilink parsing started for category: {category}',
        'category': category,
        'server_url': server_url
    })

@app.route('/available-categories', methods=['GET'])
def get_available_categories():
    """Получение доступных категорий для парсинга Citilink"""
    citilink_categories = [
        'videokarty',
        'processory',
        'materinskie-platy',
        'moduli-pamyati',
        'bloki-pitaniya',
        'korpusa',
        'sistemy-ohlazhdeniya-processora',
        'ssd-nakopiteli',
        'zhestkie-diski'
    ]
    
    return jsonify({
        'categories': citilink_categories
    })

@app.route('/stop-parsing', methods=['POST'])
def stop_parsing():
    """Остановка парсинга"""
    if parser_status['status'] != 'running':
        return jsonify({
            'success': False,
            'message': 'No parsing task is currently running'
        }), 400
    
    update_status('error', 'Manually stopped', parser_status['products_parsed'], 'Manually stopped by user', parser_status['progress'])
    
    return jsonify({
        'success': True,
        'message': 'Parsing stopped'
    })

@app.route('/data/local', methods=['GET'])
def get_local_data():
    """Получение локально сохраненных данных"""
    try:
        data_dir = Path('/app/data')
        local_files = list(data_dir.glob('citilink_*.json'))
        
        if not local_files:
            return jsonify({
                'success': False,
                'message': 'No local Citilink data files found'
            }), 404
        
        # Получаем информацию о всех файлах
        files_info = []
        for file_path in local_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                files_info.append({
                    'file': str(file_path.name),
                    'path': str(file_path),
                    'count': len(data),
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    'size': file_path.stat().st_size
                })
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'files': files_info,
            'total_files': len(files_info)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/data/send', methods=['POST'])
def send_data_to_main_server():
    """Отправка локальных данных на основной сервер"""
    try:
        data = request.get_json() or {}
        server_url = data.get('server_url', 'http://pcconf.ru')
        file_name = data.get('file_name', None)
        
        # Получаем локальные данные
        data_dir = Path('/app/data')
        
        if file_name:
            target_file = data_dir / file_name
            if not target_file.exists():
                return jsonify({
                    'success': False,
                    'message': f'File {file_name} not found'
                }), 404
            files_to_send = [target_file]
        else:
            files_to_send = list(data_dir.glob('citilink_*.json'))
        
        if not files_to_send:
            return jsonify({
                'success': False,
                'message': 'No Citilink data files found'
            }), 404
        
        total_products = 0
        sent_files = []
        
        for file_path in files_to_send:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    products_data = json.load(f)
                
                # Отправляем данные через API основного сервера
                upload_url = f"{server_url.rstrip('/')}/api/upload-products"
                response = requests.post(upload_url, json={
                    'products': products_data,
                    'source': 'citilink',
                    'upload_type': 'single_file',
                })
                
                if response.status_code == 200:
                    total_products += len(products_data)
                    sent_files.append({
                        'file': file_path.name,
                        'products': len(products_data),
                        'status': 'success'
                    })
                else:
                    sent_files.append({
                        'file': file_path.name,
                        'products': len(products_data),
                        'status': 'failed',
                        'error': f'HTTP {response.status_code}'
                    })
                    
            except Exception as e:
                sent_files.append({
                    'file': file_path.name,
                    'status': 'error',
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'message': f'Processed {len(sent_files)} files, sent {total_products} products',
            'total_products': total_products,
            'files': sent_files,
            'server_url': server_url
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    """Получение логов парсера"""
    try:
        logs_dir = Path('/app/logs')
        log_files = list(logs_dir.glob('*.log'))
        
        if not log_files:
            return jsonify({
                'success': False,
                'message': 'No log files found'
            }), 404
        
        # Получаем самый свежий лог
        latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
        
        with open(latest_log, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Возвращаем последние 1000 строк
        lines = log_content.split('\n')
        if len(lines) > 1000:
            lines = lines[-1000:]
        
        return jsonify({
            'success': True,
            'logs': '\n'.join(lines),
            'file': str(latest_log),
            'total_lines': len(lines)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting Citilink Parser Worker on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=False) 