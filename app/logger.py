import logging
import os
from datetime import datetime

def get_logger(name):
    """Создает и настраивает логгер"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Настройка уровня логирования
        logger.setLevel(logging.INFO)
        
        # Создание форматера
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Файловый обработчик (опционально)
        try:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            # Если не удается создать файловый логгер, продолжаем только с консольным
            pass
    
    return logger 