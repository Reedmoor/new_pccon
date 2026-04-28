import requests
import time
import logging
import os
import signal
import sys
import random

# Список прокси
PROXY_LIST = [
    {
        'host': '194.156.0.61',
        'http_port': 64604,
        'socks5_port': 64605,
        'username': 'iXya3sZg',
        'password': 'L51Gzyra'
    },
    {
        'host': '45.140.64.215',
        'http_port': 62474,
        'socks5_port': 62475,
        'username': 'iXya3sZg',
        'password': 'L51Gzyra'
    },
    {
        'host': '91.191.184.244',
        'http_port': 63478,
        'socks5_port': 63479,
        'username': 'iXya3sZg',
        'password': 'L51Gzyra'
    }
]

# Глобальная переменная для отслеживания текущего прокси
current_proxy_index = 0
# Прокси по умолчанию выключены. Включаются только вручную через enable_proxy().
use_proxy = False

def get_next_proxy():
    """Получает следующий прокси из списка"""
    global current_proxy_index
    if not PROXY_LIST:
        return None
    
    proxy = PROXY_LIST[current_proxy_index]
    current_proxy_index = (current_proxy_index + 1) % len(PROXY_LIST)
    
    # Используем HTTP прокси
    proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['http_port']}"
    
    return {
        'http': proxy_url,
        'https': proxy_url
    }

def test_proxy(proxy_dict):
    """Тестирует работоспособность прокси"""
    try:
        # Уменьшенный timeout для быстрого тестирования
        test_response = requests.get('https://httpbin.org/ip', proxies=proxy_dict, timeout=5)
        if test_response.status_code == 200:
            logging.info(f"Прокси работает. IP: {test_response.json().get('origin', 'unknown')}")
            return True
    except Exception as e:
        logging.warning(f"Прокси не работает: {e}")
    return False

def test_all_proxies():
    """Тестирует все прокси и выводит результаты"""
    logging.info("🧪 Тестируем все прокси...")
    working_count = 0
    
    for i, proxy_info in enumerate(PROXY_LIST):
        proxy_dict = get_next_proxy()
        proxy_host = f"{proxy_info['host']}:{proxy_info['http_port']}"
        
        logging.info(f"Тестируем прокси {i+1}/{len(PROXY_LIST)}: {proxy_host}")
        
        # Уменьшенный timeout для быстрого тестирования
        try:
            test_response = requests.get('https://httpbin.org/ip', proxies=proxy_dict, timeout=3)
            if test_response.status_code == 200:
                working_count += 1
                ip_info = test_response.json()
                logging.info(f"✅ Прокси {proxy_host} работает. IP: {ip_info.get('origin', 'unknown')}")
            else:
                logging.warning(f"❌ Прокси {proxy_host} вернул код {test_response.status_code}")
        except Exception as e:
            logging.warning(f"❌ Прокси {proxy_host} не работает: {str(e)}")
    
    logging.info(f"📊 Результат: {working_count}/{len(PROXY_LIST)} прокси работают")
    return working_count > 0

def enable_proxy():
    """Принудительно включает использование прокси"""
    global use_proxy
    use_proxy = True
    logging.info("🔄 Прокси принудительно включены")

def disable_proxy():
    """Отключает использование прокси"""
    global use_proxy
    use_proxy = False
    logging.info("🔄 Прокси отключены")

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
    """Выполняет запрос с улучшенной обработкой остановки и поддержкой прокси"""
    global use_proxy
    retries = 0
    proxy_retries = 0
    current_proxies = None
    
    while retries < max_retries:
        try:
            # Проверяем флаг остановки перед каждым запросом
            check_stop_flag()
            
            # Если используем прокси или это первая попытка с прокси
            if use_proxy and current_proxies is None:
                current_proxies = get_next_proxy()
                if current_proxies:
                    logging.info(f"Используем прокси: {current_proxies['http'].split('@')[1] if '@' in current_proxies['http'] else 'unknown'}")
            
            logging.info(f"Отправка запроса к {url}, для получения данных об {name_request}")
            
            # Выполняем запрос с прокси или без
            if current_proxies:
                response = requests.post(
                    url=url, 
                    json={"query": query, "variables": variables}, 
                    timeout=30,
                    proxies=current_proxies
                )
            else:
                response = requests.post(
                    url=url, 
                    json={"query": query, "variables": variables}, 
                    timeout=30
                )
            
            if response.status_code == 200:
                logging.info("Запрос успешно выполнен")
                return response.json()
                
            elif response.status_code == 429:
                retries += 1
                wait_time = min(2 ** retries, 10)
                logging.warning(f"Слишком много запросов. Ожидание {wait_time} сек перед повторной попыткой... (попытка {retries}/{max_retries})")
                
                # Прокси НЕ включаем автоматически.
                if use_proxy and proxy_retries < len(PROXY_LIST):
                    # Переключаемся на следующий прокси
                    logging.info("🔄 Переключаемся на следующий прокси")
                    current_proxies = get_next_proxy()
                    proxy_retries += 1
                
                # Проверяем флаг остановки каждую секунду во время ожидания
                for i in range(wait_time):
                    check_stop_flag()
                    time.sleep(1)
                    
            elif response.status_code in [403, 502, 503, 504]:
                # Ошибки блокировки - автоподключение прокси отключено
                logging.warning(f"Получена ошибка блокировки {response.status_code}")
                if use_proxy and proxy_retries < len(PROXY_LIST):
                    logging.info("🔄 Переключаемся на следующий прокси")
                    current_proxies = get_next_proxy()
                    proxy_retries += 1
                    retries += 1
                else:
                    logging.error("Прокси отключены или закончились, блокировка остается")
                    retries += 1
                    
                if retries < max_retries:
                    logging.info(f"Повторная попытка через 3 секунды... (попытка {retries}/{max_retries})")
                    time.sleep(3)
            else:
                logging.error(f"Ошибка HTTP: {response.status_code}, Ответ: {response.text}")
                retries += 1
                if retries < max_retries:
                    logging.info(f"Повторная попытка через 2 секунды... (попытка {retries}/{max_retries})")
                    time.sleep(2)
                    
        except ParserStoppedException:
            # Пробрасываем исключение остановки дальше
            raise
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as e:
            logging.warning(f"Ошибка соединения: {str(e)}")
            
            if use_proxy and proxy_retries < len(PROXY_LIST):
                # Переключаемся на следующий прокси
                logging.info("🔄 Переключаемся на следующий прокси")
                current_proxies = get_next_proxy()
                proxy_retries += 1
            
            retries += 1
            if retries < max_retries:
                logging.info(f"Повторная попытка через 3 секунды... (попытка {retries}/{max_retries})")
                time.sleep(3)
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