#!/usr/bin/env python3
"""
Scheduler service для планирования задач парсинга
"""

import os
import time
import logging
import schedule
import redis
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ParserScheduler:
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

    def schedule_citilink_parsing(self):
        """Планирование парсинга Citilink"""
        logger.info("Scheduling Citilink parsing task")
        
        # Здесь будет логика отправки задачи в очередь
        if self.redis_client:
            task_data = {
                'type': 'parse_citilink',
                'category': 'sistemy-ohlazhdeniya-processora--kulery-dlya-processora',
                'timestamp': datetime.now().isoformat()
            }
            try:
                self.redis_client.lpush('parser_queue', str(task_data))
                logger.info("Citilink parsing task added to queue")
            except Exception as e:
                logger.error(f"Failed to add task to queue: {e}")

    def schedule_dns_parsing(self, category=None):
        """Планирование парсинга DNS для конкретной категории"""
        category_name = category or 'all_categories'
        logger.info(f"Scheduling DNS parsing task for category: {category_name}")
        
        # Здесь будет логика отправки задачи в очередь
        if self.redis_client:
            task_data = {
                'type': 'parse_dns',
                'category': category,
                'timestamp': datetime.now().isoformat()
            }
            try:
                self.redis_client.lpush('parser_queue', str(task_data))
                logger.info(f"DNS parsing task for '{category_name}' added to queue")
            except Exception as e:
                logger.error(f"Failed to add task to queue: {e}")

    def schedule_monthly_dns_parsing(self):
        """Планирование ежемесячного полного парсинга DNS"""
        logger.info("Scheduling monthly DNS parsing - all categories")
        
        # Парсим разные категории с задержкой
        dns_categories = [
            'videokarty',  # Видеокарты  
            'processory',  # Процессоры
            'materinskie-platy',  # Материнские платы
            'moduli-pamyati',  # Оперативная память
            'sistemy-ohlazhdeniya-processora',  # CPU кулеры
            'bloki-pitaniya',  # Блоки питания
            'korpusa',  # Корпуса
            'zhestkie-diski',  # Жесткие диски
            'ssd-nakopiteli'  # SSD накопители
        ]
        
        for category in dns_categories:
            self.schedule_dns_parsing(category)
            logger.info(f"Scheduled DNS parsing for category: {category}")
    
    def run(self):
        """Запуск планировщика"""
        logger.info("Starting Parser Scheduler...")
        
        # Планируем задачи
        # Citilink парсинг раз в месяц (1-го числа в 1:00 ночи)
        schedule.every().month.at("01:00").do(self.schedule_citilink_parsing)
        
        # DNS парсинг раз в месяц (1-го числа в 2:00 ночи)
        schedule.every().month.at("02:00").do(self.schedule_monthly_dns_parsing)
        
        logger.info("Scheduled tasks:")
        logger.info("- Citilink parsing: monthly on 1st day at 01:00")
        logger.info("- DNS parsing (all categories): monthly on 1st day at 02:00")
        
        # Запускаем планировщик
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Проверяем каждую минуту
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)

def main():
    """Главная функция"""
    scheduler = ParserScheduler()
    scheduler.run()

if __name__ == '__main__':
    main() 