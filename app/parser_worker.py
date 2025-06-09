#!/usr/bin/env python3
"""
Parser Worker для обработки задач парсинга из Redis очереди
"""

import os
import time
import json
import logging
import redis
import subprocess
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/parser_worker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ParserWorker:
    def __init__(self):
        # Подключение к Redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/2')
        try:
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    def execute_citilink_parsing(self):
        """Выполнение парсинга Citilink"""
        logger.info("Starting Citilink parsing...")
        
        try:
            # Запускаем Citilink парсер
            cmd = [
                'python', '/app/app/utils/Citi_parser/scrape.py',
                'sistemy-ohlazhdeniya-processora'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 час максимум
            )
            
            if result.returncode == 0:
                logger.info("Citilink parsing completed successfully")
                return True
            else:
                logger.error(f"Citilink parsing failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Citilink parsing timed out")
            return False
        except Exception as e:
            logger.error(f"Error executing Citilink parsing: {e}")
            return False

    def execute_dns_parsing(self, category=None):
        """Выполнение парсинга DNS"""
        category_name = category or 'all_categories'
        logger.info(f"Starting DNS parsing for category: {category_name}")
        
        try:
            # Запускаем DNS парсер
            if category:
                cmd = [
                    'python', '/app/app/utils/DNS_parsing/main.py',
                    category, '20'  # 20 товаров на категорию
                ]
            else:
                cmd = ['python', '/app/app/utils/DNS_parsing/main.py', '20']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 час максимум
            )
            
            if result.returncode == 0:
                logger.info(f"DNS parsing for '{category_name}' completed successfully")
                return True
            else:
                logger.error(f"DNS parsing for '{category_name}' failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"DNS parsing for '{category_name}' timed out")
            return False
        except Exception as e:
            logger.error(f"Error executing DNS parsing for '{category_name}': {e}")
            return False

    def process_task(self, task_data_str):
        """Обработка одной задачи"""
        try:
            # Парсим данные задачи
            task_data = eval(task_data_str)  # Простой способ, в продакшене лучше json
            task_type = task_data.get('type')
            category = task_data.get('category')
            timestamp = task_data.get('timestamp')
            
            logger.info(f"Processing task: {task_type}, category: {category}, timestamp: {timestamp}")
            
            if task_type == 'parse_citilink':
                return self.execute_citilink_parsing()
            elif task_type == 'parse_dns':
                return self.execute_dns_parsing(category)
            else:
                logger.warning(f"Unknown task type: {task_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing task: {e}")
            return False

    def run(self):
        """Запуск воркера"""
        logger.info("Starting Parser Worker...")
        
        if not self.redis_client:
            logger.error("Cannot start worker without Redis connection")
            return
        
        while True:
            try:
                # Получаем задачу из очереди (блокирующая операция с таймаутом)
                task = self.redis_client.brpop('parser_queue', timeout=60)
                
                if task:
                    queue_name, task_data = task
                    task_data_str = task_data.decode('utf-8')
                    
                    logger.info(f"Received task from queue: {task_data_str}")
                    
                    # Обрабатываем задачу
                    success = self.process_task(task_data_str)
                    
                    if success:
                        logger.info("Task completed successfully")
                    else:
                        logger.error("Task failed")
                        
                    # Небольшая пауза между задачами
                    time.sleep(5)
                    
            except KeyboardInterrupt:
                logger.info("Worker stopped by user")
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                time.sleep(60)

def main():
    """Главная функция"""
    worker = ParserWorker()
    worker.run()

if __name__ == '__main__':
    main() 