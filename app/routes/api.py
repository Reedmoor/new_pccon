from flask import Blueprint, request, jsonify, render_template
from app import db
from app.utils.standardization.import_products import import_products
import json
import logging
import subprocess
import os
import sys
from datetime import datetime
from pathlib import Path
import requests
import threading

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

# Глобальное хранилище уведомлений (в продакшене лучше использовать Redis/DB)
_notifications_lock = threading.Lock()
_notifications_storage = []

def add_notification(notification_data):
    """Добавить уведомление в хранилище"""
    with _notifications_lock:
        _notifications_storage.append(notification_data)
        # Оставляем только последние 50 уведомлений
        if len(_notifications_storage) > 50:
            _notifications_storage.pop(0)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint для синхронизации серверов"""
    try:
        from app.models.models import UnifiedProduct
        # Проверяем доступность базы данных
        product_count = UnifiedProduct.query.count()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'product_count': product_count,
            'server': 'pccon_web',
            'version': '1.0'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'server': 'pccon_web'
        }), 500

@api_bp.route('/upload-products', methods=['POST'])
def upload_products():
    """API endpoint для получения данных от локального парсера"""
    try:
        # Проверяем, что получили JSON данные
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        # Проверяем структуру данных
        if not data or 'products' not in data:
            return jsonify({'error': 'Missing products data'}), 400
        
        products = data['products']
        if not isinstance(products, list):
            return jsonify({'error': 'Products must be a list'}), 400
        
        # Определяем тип загрузки
        upload_type = data.get('upload_type', 'local_parser')
        source = data.get('source', 'unknown')
        
        logger.info(f"Received {len(products)} products from {source} (type: {upload_type})")
        
        # Для серверной синхронизации НЕ сохраняем файлы локально
        if upload_type == 'server_sync':
            logger.info("Server sync detected - importing directly to database without saving files")
            
            # Создаем временные данные только в памяти для импорта
            try:
                # Импортируем товары напрямую в базу данных
                from app.utils.standardization.import_products import import_products_from_data
                
                # Импортируем напрямую из данных без сохранения файла
                result = import_products_from_data(products, source=source)
                
                # Создаем уведомление о синхронизации
                sync_notification = {
                    'type': 'server_sync',
                    'source': source,
                    'products_count': len(products),
                    'timestamp': datetime.now().isoformat(),
                    'sync_id': data.get('sync_id', 'unknown'),
                    'status': 'success'
                }
                
                # Добавляем уведомление в хранилище
                add_notification(sync_notification)
                
                # Сохраняем уведомление (в будущем можно отправлять через WebSocket)
                logger.info(f"📨 SYNC NOTIFICATION: {sync_notification}")
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully synced {len(products)} products from server',
                    'imported_count': len(products),
                    'upload_type': upload_type,
                    'source': source,
                    'notification': sync_notification,
                    'files_saved': False  # Файлы НЕ сохраняются при синхронизации
                }), 200
                
            except Exception as import_error:
                logger.error(f"Error importing synced products: {import_error}")
                return jsonify({
                    'success': False,
                    'error': f'Server sync failed: {str(import_error)}',
                    'received_count': len(products),
                    'upload_type': upload_type
                }), 500
        
        # Для локального парсера сохраняем файлы как обычно
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_filename = f"local_parser_data_{timestamp}.json"
            temp_path = f"data/{temp_filename}"
            
            # Создаем директорию если не существует
            os.makedirs('data', exist_ok=True)
            
            # Сохраняем данные в том же формате, что ожидает import_products
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved products data to {temp_path}")
            
            # Создаем уведомление о локальном парсинге (НЕ импортируем сразу)
            parse_notification = {
                'type': 'local_parsing',
                'source': source,
                'products_count': len(products),
                'timestamp': datetime.now().isoformat(),
                'filename': temp_filename,
                'status': 'saved',  # Изменили статус на 'saved'
                'note': 'Data saved to file. Run import_products() to import into database.'
            }
            
            # Добавляем уведомление в хранилище
            add_notification(parse_notification)
            
            logger.info(f"📨 PARSE NOTIFICATION: {parse_notification}")
            
            return jsonify({
                'success': True,
                'message': f'Successfully received and saved {len(products)} products to file. Use import_products() to import into database.',
                'received_count': len(products),
                'filename': temp_filename,
                'upload_type': upload_type,
                'notification': parse_notification,
                'files_saved': True,
                'imported_to_db': False  # Не импортировано в БД
            }), 200
    
    except Exception as e:
        logger.error(f"Error in upload_products endpoint: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@api_bp.route('/parser-status', methods=['GET'])
def parser_status():
    """Получение статуса парсера и последних загрузок"""
    try:
        # Проверяем последние файлы с данными
        import glob
        from datetime import datetime, timedelta
        
        # Ищем файлы резервных копий локального парсера
        data_files = glob.glob('data/local_parser_data_*.json')
        data_files.sort(key=os.path.getmtime, reverse=True)
        
        recent_uploads = []
        for file_path in data_files[:10]:  # Последние 10 файлов
            try:
                stat = os.stat(file_path)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                upload_info = {
                    'filename': os.path.basename(file_path),
                    'upload_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'file_size': stat.st_size,
                    'product_count': len(data.get('products', [])) if isinstance(data, dict) else len(data)
                }
                recent_uploads.append(upload_info)
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
        
        response_data = {
            'status': 'ok',
            'server_time': datetime.now().isoformat(),
            'recent_uploads': recent_uploads
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting parser status: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/run-parser', methods=['POST'])
def run_parser():
    """Запуск локального парсера через веб-интерфейс"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        mode = data.get('mode')
        if not mode:
            return jsonify({'error': 'Mode is required'}), 400
        
        # Путь к обёртке old_dns_parser
        current_dir = Path(__file__).parent.parent.parent
        local_parser_dir = current_dir / 'local_parser'
        parser_script = local_parser_dir / 'dns_parser_wrapper.py'
        
        if not parser_script.exists():
            return jsonify({'error': 'DNS parser wrapper script not found'}), 404
        
        # Подготавливаем команду для запуска
        cmd = [sys.executable, str(parser_script)]
        
        # Проверяем параметр отображения браузера
        show_browser = data.get('show_browser', True)
        logger.info(f"Show browser parameter: {show_browser}")
        
        # old_dns_parser всегда показывает браузер, поэтому headless не поддерживается
        if not show_browser:
            logger.warning("Headless mode not supported with old_dns_parser - browser will be visible")
        
        if mode == 'test':
            cmd.append('--test-only')
        elif mode == 'single_product':
            # old_dns_parser не поддерживает парсинг одного товара
            return jsonify({'error': 'Single product parsing not supported with old DNS parser'}), 400
        elif mode == 'category':
            category = data.get('category')
            limit = data.get('limit', 5)
            if not category:
                return jsonify({'error': 'Category is required for category mode'}), 400
            cmd.extend(['--category', category, '--limit', str(limit)])
        else:
            return jsonify({'error': f'Unknown mode: {mode}'}), 400
        
        # Добавляем URL сервера
        cmd.extend(['--server-url', 'https://pcconf.ru'])
        
        # Запускаем парсер
        logger.info(f"Starting parser with command: {' '.join(cmd)}")
        
        # Для видимого режима используем batch-файл на Windows
        if show_browser and mode != 'test':
            # Для видимого браузера используем batch-файл
            import subprocess
            import os
            
            # Путь к batch-файлу для видимого режима
            batch_file = local_parser_dir / 'run_visible_parser.bat'
            
            # Подготавливаем аргументы для batch-файла (без python и путь к скрипту)
            batch_args = []
            skip_next = False
            for i, arg in enumerate(cmd):
                if skip_next:
                    skip_next = False
                    continue
                if 'python' in arg.lower():
                    continue
                if 'dns_parser_wrapper.py' in arg:
                    continue
                batch_args.append(arg)
            
            # Запускаем batch-файл в новом окне
            batch_cmd = ['cmd', '/c', 'start', str(batch_file)] + batch_args
            logger.info(f"Running visible mode with batch command: {' '.join(batch_cmd)}")
            
            process = subprocess.Popen(
                batch_cmd,
                cwd=str(local_parser_dir),
                shell=True
            )
            
            # Для batch-файла не можем получить реальный PID, поэтому возвращаем успех сразу
            return jsonify({
                'status': 'started',
                'message': 'Parser started in visible mode - new console window should open',
                'mode': mode,
                'command': ' '.join(batch_args),
                'note': 'Check for new console window with browser'
            })
        else:
            # Для headless режима или теста используем обычный запуск
            process = subprocess.Popen(
                cmd,
                cwd=str(local_parser_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Даем процессу немного времени на запуск
            import time
            time.sleep(1)
            
            # Проверяем статус процесса
            poll = process.poll()
            if poll is None:
                # Процесс еще выполняется
                return jsonify({
                    'status': 'started',
                    'message': f'Parser started successfully with PID {process.pid}',
                    'mode': mode,
                    'command': ' '.join(cmd)
                })
            elif poll == 0:
                # Процесс завершился успешно (для тестового режима)
                stdout, stderr = process.communicate()
                return jsonify({
                    'status': 'completed',
                    'message': 'Parser completed successfully',
                    'output': stdout,
                    'mode': mode
                })
            else:
                # Процесс завершился с ошибкой
                stdout, stderr = process.communicate()
                return jsonify({
                    'status': 'error',
                    'message': f'Parser failed with exit code {poll}',
                    'error': stderr,
                    'output': stdout
                }), 500
        
    except Exception as e:
        logger.error(f"Error running parser: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/test-visible-browser', methods=['POST'])
def test_visible_browser():
    """Тестовый endpoint для запуска видимого браузера"""
    try:
        # Путь к тестовому скрипту
        current_dir = Path(__file__).parent.parent.parent
        local_parser_dir = current_dir / 'local_parser'
        test_script = local_parser_dir / 'test_web_browser.py'
        
        if not test_script.exists():
            return jsonify({'error': 'Test script not found'}), 404
        
        # Команда для тестирования видимого браузера
        cmd = [sys.executable, str(test_script), '--server-url', 'http://localhost:5001']
        
        logger.info(f"Starting visible browser test with command: {' '.join(cmd)}")
        
        # Запускаем процесс
        import subprocess
        import os
        
        # Переменные окружения
        env = os.environ.copy()
        
        process = subprocess.Popen(
            cmd,
            cwd=str(local_parser_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Даем процессу время на запуск
        import time
        time.sleep(2)
        
        # Проверяем статус
        poll = process.poll()
        if poll is None:
            return jsonify({
                'status': 'started',
                'message': 'Visible browser test started successfully',
                'pid': process.pid,
                'command': ' '.join(cmd)
            })
        else:
            stdout, stderr = process.communicate()
            return jsonify({
                'status': 'completed',
                'message': 'Browser test completed',
                'output': stdout,
                'error': stderr
            })
        
    except Exception as e:
        logger.error(f"Error starting visible browser test: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/import-to-docker', methods=['POST'])
def import_to_docker():
    """Импорт существующих данных на Docker сервер"""
    try:
        # Путь к скрипту импорта
        current_dir = Path(__file__).parent.parent.parent
        local_parser_dir = current_dir / 'local_parser'
        import_script = local_parser_dir / 'upload_existing_data.py'
        
        # Проверяем существование скрипта
        if not import_script.exists():
            return jsonify({'error': 'Import script not found'}), 404
        
        # Команда для запуска импорта
        cmd = [sys.executable, str(import_script), '--server-url', 'https://pcconf.ru']
        
        logger.info(f"Starting import with command: {' '.join(cmd)}")
        
        # Запускаем импорт
        process = subprocess.Popen(
            cmd,
            cwd=str(local_parser_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Ждем завершения (максимум 60 секунд)
        try:
            stdout, stderr = process.communicate(timeout=60)
            
            if process.returncode == 0:
                # Парсим вывод для получения статистики
                lines = stdout.split('\n')
                imported_count = 0
                categories = []
                
                for line in lines:
                    # Ищем общее количество загруженных товаров
                    if 'Total products uploaded:' in line:
                        try:
                            imported_count = int(line.split(':')[-1].strip().replace(',', ''))
                        except:
                            pass
                    # Ищем обработанные категории
                    elif '📂 Processing:' in line:
                        try:
                            category = line.split('📂 Processing:')[-1].strip()
                            if category and category not in categories:
                                categories.append(category)
                        except:
                            pass
                    # Также ищем успешные загрузки
                    elif 'Successfully uploaded' in line and 'products from' in line:
                        try:
                            # Извлекаем название категории из сообщения
                            parts = line.split('products from')
                            if len(parts) > 1:
                                category = parts[1].split('...')[0].strip()
                                if category and category not in categories:
                                    categories.append(category)
                        except:
                            pass
                
                # Если не нашли в логах, попробуем найти в финальной сводке
                if imported_count == 0:
                    for line in lines:
                        if 'Success:' in line and 'files' in line:
                            try:
                                # Ищем что-то вроде "Success: 10/10 files"
                                parts = line.split('/')
                                if len(parts) > 1:
                                    success_count = int(parts[0].split(':')[-1].strip())
                                    # Приблизительная оценка если не нашли точное число
                                    if success_count > 0 and imported_count == 0:
                                        imported_count = success_count * 30  # примерно 30 товаров на категорию
                            except:
                                pass
                
                return jsonify({
                    'status': 'success',
                    'message': 'Data imported successfully to Docker server',
                    'imported_count': imported_count,
                    'categories': categories,
                    'success_files': len(categories),
                    'output': stdout
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Import failed with exit code {process.returncode}',
                    'error': stderr,
                    'output': stdout
                }), 500
                
        except subprocess.TimeoutExpired:
            process.kill()
            return jsonify({
                'status': 'timeout',
                'message': 'Import process timed out (60 seconds)',
                'note': 'Large datasets may take longer. Check Docker server manually.'
            }), 408
        
    except Exception as e:
        logger.error(f"Error running import: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/test-connection', methods=['GET'])
def test_connection():
    """Простой endpoint для тестирования соединения"""
    return jsonify({
        'status': 'ok',
        'message': 'Local parser API is working',
        'server_time': datetime.now().isoformat()
    }), 200

@api_bp.route('/local-data-manager', methods=['POST'])
def local_data_manager():
    """Управление локальными данными через веб-интерфейс"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        action = data.get('action')
        if not action:
            return jsonify({'error': 'Action is required'}), 400
        
        # Путь к менеджеру данных
        current_dir = Path(__file__).parent.parent.parent
        local_parser_dir = current_dir / 'local_parser'
        manager_script = local_parser_dir / 'local_data_manager.py'
        
        if not manager_script.exists():
            return jsonify({'error': 'Local data manager script not found'}), 404
        
        # Подготавливаем команду
        cmd = [sys.executable, str(manager_script), '--server-url', 'https://pcconf.ru']
        
        if action == 'stats':
            cmd.append('--stats')
        elif action == 'organize':
            cmd.append('--organize')
        elif action == 'upload':
            cmd.append('--upload')
        elif action == 'all':
            cmd.append('--all')
        else:
            return jsonify({'error': f'Unknown action: {action}'}), 400
        
        logger.info(f"Running local data manager with command: {' '.join(cmd)}")
        
        # Запускаем менеджер
        process = subprocess.Popen(
            cmd,
            cwd=str(local_parser_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Ждем завершения (максимум 60 секунд)
        try:
            stdout, stderr = process.communicate(timeout=60)
            
            if process.returncode == 0:
                # Парсим вывод для получения статистики
                lines = stdout.split('\n')
                stats = {}
                categories = []
                
                for line in lines:
                    if 'Raw data files:' in line:
                        try:
                            stats['raw_files'] = int(line.split(':')[-1].strip())
                        except:
                            pass
                    elif 'Organized files:' in line:
                        try:
                            stats['organized_files'] = int(line.split(':')[-1].strip())
                        except:
                            pass
                    elif 'Total products:' in line:
                        try:
                            total_str = line.split(':')[-1].strip().replace(',', '')
                            stats['total_products'] = int(total_str)
                        except:
                            pass
                    elif line.strip().startswith('✅ Organized:'):
                        try:
                            # Извлекаем информацию об организованном файле
                            parts = line.split('->')
                            if len(parts) > 1:
                                new_filename = parts[1].strip()
                                categories.append(new_filename)
                        except:
                            pass
                
                return jsonify({
                    'status': 'success',
                    'message': f'Local data manager completed successfully ({action})',
                    'action': action,
                    'stats': stats,
                    'categories': categories,
                    'output': stdout
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Local data manager failed with exit code {process.returncode}',
                    'error': stderr,
                    'output': stdout
                }), 500
                
        except subprocess.TimeoutExpired:
            process.kill()
            return jsonify({
                'status': 'timeout',
                'message': 'Local data manager timed out (60 seconds)',
                'note': 'Operation may still be running in background.'
            }), 408
        
    except Exception as e:
        logger.error(f"Error running local data manager: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/export-products', methods=['GET'])
def export_products():
    """Экспорт всех продуктов из базы данных для синхронизации между серверами"""
    try:
        from app.models.models import UnifiedProduct
        
        # Получаем параметры запроса
        limit = request.args.get('limit', type=int)
        category = request.args.get('category', type=str)
        
        # Базовый запрос
        query = UnifiedProduct.query
        
        # Фильтрация по типу продукта если указано
        if category:
            query = query.filter_by(product_type=category)
        
        # Ограничение количества если указано
        if limit:
            query = query.limit(limit)
        
        # Получаем продукты
        products = query.all()
        
        logger.info(f"Exporting {len(products)} products for server synchronization")
        
        # Преобразуем в формат совместимый с синхронизацией
        exported_products = []
        for product in products:
            product_data = {
                'id': product.id,
                'name': product.product_name,
                'price_discounted': float(product.price_discounted) if product.price_discounted else None,
                'price_original': float(product.price_original) if product.price_original else None,
                'vendor': product.vendor,
                'url': product.product_url,
                'availability': product.availability,
                'product_type': product.product_type,
                'images': product.get_images(),
                'characteristics': product.get_characteristics(),
                'rating': product.rating,
                'number_of_reviews': product.number_of_reviews
            }
            
            # Добавляем категории в том же формате что ожидает синхронизация
            categories = []
            if product.product_type:
                categories.append({
                    'name': product.product_type.replace('_', ' ').title(),
                    'url': f'/products/{product.product_type}'
                })
            
            product_data['categories'] = categories
            
            # Добавляем brand_name для совместимости
            characteristics = product.get_characteristics()
            if characteristics and 'brand' in characteristics:
                product_data['brand_name'] = characteristics['brand']
            
            exported_products.append(product_data)
        
        return jsonify({
            'success': True,
            'products': exported_products,
            'total_count': len(exported_products),
            'export_time': datetime.now().isoformat(),
            'filters': {
                'category': category,
                'limit': limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error exporting products: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to export products: {str(e)}'
        }), 500

@api_bp.route('/products', methods=['GET'])
def get_products():
    """Альтернативный эндпоинт для получения продуктов (алиас для export-products)"""
    return export_products()

@api_bp.route('/export-and-send-to-docker', methods=['POST'])
def export_and_send_to_docker():
    """Экспорт данных из локальной базы и отправка на Docker сервер"""
    try:
        from app.models.models import UnifiedProduct
        
        # Получаем все продукты из локальной базы
        products = UnifiedProduct.query.all()
        
        if not products:
            return jsonify({
                'success': False,
                'error': 'No products found in local database'
            }), 404
        
        logger.info(f"Exporting {len(products)} products to send to Docker server")
        
        # Преобразуем в формат для отправки
        exported_products = []
        for product in products:
            product_data = {
                'id': product.id,
                'name': product.product_name,
                'price_discounted': float(product.price_discounted) if product.price_discounted else None,
                'price_original': float(product.price_original) if product.price_original else None,
                'vendor': product.vendor,
                'url': product.product_url,
                'availability': product.availability,
                'product_type': product.product_type,
                'images': product.get_images(),
                'characteristics': product.get_characteristics(),
                'rating': product.rating,
                'number_of_reviews': product.number_of_reviews
            }
            
            # Добавляем категории
            categories = []
            if product.product_type:
                categories.append({
                    'name': product.product_type.replace('_', ' ').title(),
                    'url': f'/products/{product.product_type}'
                })
            
            product_data['categories'] = categories
            
            # Добавляем brand_name для совместимости
            characteristics = product.get_characteristics()
            if characteristics and 'brand' in characteristics:
                product_data['brand_name'] = characteristics['brand']
            
            exported_products.append(product_data)
        
        # Подготавливаем payload для Docker сервера
        current_time = datetime.now()
        payload = {
            'products': exported_products,
            'source': 'local_export_to_docker',
            'upload_type': 'manual_export',
            'timestamp': current_time.isoformat(),
            'export_id': f'export_{current_time.timestamp()}',
            'total_products': len(exported_products)
        }
        
        # Отправляем на Docker сервер
        docker_url = 'https://pcconf.ru'
        try:
            response = requests.post(
                f"{docker_url}/api/upload-products",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully sent {len(exported_products)} products to Docker server")
                
                return jsonify({
                    'success': True,
                    'sent_count': len(exported_products),
                    'docker_server': docker_url,
                    'message': 'Products successfully sent to Docker server',
                    'docker_response': result
                }), 200
            else:
                logger.error(f"Docker server returned status {response.status_code}: {response.text}")
                return jsonify({
                    'success': False,
                    'error': f'Docker server error: {response.status_code} - {response.text}'
                }), 500
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Docker server: {e}")
            return jsonify({
                'success': False,
                'error': f'Cannot connect to Docker server: {str(e)}'
            }), 500
        
    except Exception as e:
        logger.error(f"Error in export_and_send_to_docker: {e}")
        return jsonify({
            'success': False,
            'error': f'Export error: {str(e)}'
        }), 500

@api_bp.route('/check-docker-status', methods=['GET'])
def check_docker_status():
    """Проверка статуса Docker сервера"""
    try:
        import requests
        
        docker_url = 'https://pcconf.ru'
        
        try:
            response = requests.get(f"{docker_url}/health", timeout=10)
            
            if response.status_code == 200:
                return jsonify({
                    'docker_available': True,
                    'docker_url': docker_url,
                    'status': 'online',
                    'response_time': response.elapsed.total_seconds()
                }), 200
            else:
                return jsonify({
                    'docker_available': False,
                    'docker_url': docker_url,
                    'status': f'HTTP {response.status_code}',
                    'error': 'Docker server returned non-200 status'
                }), 200
                
        except requests.exceptions.RequestException as e:
            return jsonify({
                'docker_available': False,
                'docker_url': docker_url,
                'status': 'offline',
                'error': f'Connection failed: {str(e)}'
            }), 200
        
    except Exception as e:
        logger.error(f"Error checking Docker status: {e}")
        return jsonify({
            'docker_available': False,
            'error': f'Status check error: {str(e)}'
        }), 500

@api_bp.route('/import-notifications', methods=['GET'])
def get_import_notifications():
    """Получение уведомлений о импорте"""
    try:
        with _notifications_lock:
            # Возвращаем последние 20 уведомлений
            recent_notifications = list(reversed(_notifications_storage[-20:]))
        
        return jsonify({
            'success': True,
            'notifications': recent_notifications,
            'total_count': len(_notifications_storage)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({
            'success': False,
            'error': f'Notifications error: {str(e)}',
            'notifications': []
        }), 500 