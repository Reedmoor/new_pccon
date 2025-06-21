import requests
import time
import logging
import os
import signal
import sys

# Исключение для принудительной остановки парсера
class ParserStoppedException(Exception):
    pass

# Глобальная переменная для отслеживания сигнала остановки
_stop_requested = False

def signal_handler(signum, frame):
    """Обработчик сигналов для принудительной остановки"""
    global _stop_requested
    _stop_requested = True
    logging.info("🛑 ПОЛУЧЕН СИГНАЛ ОСТАНОВКИ! Принудительное завершение парсера...")
    raise ParserStoppedException("Парсер остановлен сигналом")

# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def check_stop_flag():
    """Проверяет наличие файла-флага остановки или глобального флага"""
    global _stop_requested
    
    if _stop_requested:
        raise ParserStoppedException("Парсер остановлен сигналом")
    
    stop_flag_file = 'STOP_PARSER.flag'
    if os.path.exists(stop_flag_file):
        logging.info("🛑 ОБНАРУЖЕН ФАЙЛ-ФЛАГ ОСТАНОВКИ! Принудительное завершение парсера...")
        _stop_requested = True
        raise ParserStoppedException("Парсер остановлен пользователем")

def request(url, query, variables, name_request, max_retries=3):
    """Выполняет запрос с улучшенной обработкой остановки"""
    retries = 0
    
    while retries < max_retries:
        try:
            # Проверяем флаг остановки перед каждым запросом
            check_stop_flag()
            
            logging.info(f"Отправка запроса к {url}, для получения данных об {name_request}")
            response = requests.post(url=url, json={"query": query, "variables": variables}, timeout=30)
            
            if response.status_code == 200:
                logging.info("Запрос успешно выполнен")
                return response.json()
            elif response.status_code == 429:
                retries += 1
                wait_time = min(2 ** retries, 10)  # Экспоненциальное увеличение времени ожидания до максимума 10 сек
                logging.warning(f"Слишком много запросов. Ожидание {wait_time} сек перед повторной попыткой... (попытка {retries}/{max_retries})")
                
                # Проверяем флаг остановки каждую секунду во время ожидания
                for i in range(wait_time):
                    check_stop_flag()
                    time.sleep(1)
                    
            else:
                logging.error(f"Ошибка HTTP: {response.status_code}, Ответ: {response.text}")
                retries += 1
                if retries < max_retries:
                    logging.info(f"Повторная попытка через 2 секунды... (попытка {retries}/{max_retries})")
                    time.sleep(2)
                    
        except ParserStoppedException:
            # Пробрасываем исключение остановки дальше
            raise
        except requests.exceptions.RequestException as e:
            retries += 1
            logging.error(f"Ошибка сети при выполнении запроса: {str(e)}")
            if retries < max_retries:
                logging.info(f"Повторная попытка через 2 секунды... (попытка {retries}/{max_retries})")
                time.sleep(2)
            else:
                raise
        except Exception as e:
            logging.error(f"Произошла ошибка при выполнении запроса: {str(e)}")
            raise
    
    # Если все попытки исчерпаны
    raise Exception(f"Не удалось выполнить запрос после {max_retries} попыток")