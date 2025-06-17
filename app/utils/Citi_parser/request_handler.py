import requests
import time
import logging
import os

# Исключение для принудительной остановки парсера
class ParserStoppedException(Exception):
    pass

def check_stop_flag():
    """Проверяет наличие файла-флага остановки"""
    stop_flag_file = 'STOP_PARSER.flag'
    if os.path.exists(stop_flag_file):
        logging.info("🛑 ОБНАРУЖЕН ФАЙЛ-ФЛАГ ОСТАНОВКИ! Принудительное завершение парсера...")
        raise ParserStoppedException("Парсер остановлен пользователем")

def request(url, query, variables, name_request):
    while True:
        try:
            # Проверяем флаг остановки перед каждым запросом
            check_stop_flag()
            
            logging.info(f"Отправка запроса к {url}, для получения данных об {name_request}")
            response = requests.post(url=url, json={"query": query, "variables": variables})
            
            if response.status_code == 200:
                logging.info("Запрос успешно выполнен")
                return response.json()
            elif response.status_code == 429:
                logging.warning("Слишком много запросов. Ожидание перед повторной попыткой...")
                
                # Проверяем флаг остановки во время ожидания
                for i in range(5):
                    check_stop_flag()
                    time.sleep(1)
                    
            else:
                logging.error(f"Ошибка HTTP: {response.status_code}, Ответ: {response.text}")
        except ParserStoppedException:
            # Пробрасываем исключение остановки дальше
            raise
        except Exception as e:
            logging.error(f"Произошла ошибка при выполнении запроса: {str(e)}")
            raise