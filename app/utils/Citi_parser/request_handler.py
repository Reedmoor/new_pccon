import requests
import time
import logging
import os
import signal
import sys
import random
from itertools import cycle
from proxy_config import get_proxy_list, is_proxy_enabled, get_proxy_timeout, get_max_failures

# Исключение для принудительной остановки парсера
class ParserStoppedException(Exception):
    pass

# Получаем список прокси из конфигурации
SOCKS5_PROXIES = get_proxy_list()

# Создаем циклический итератор для ротации прокси
_proxy_cycle = cycle(SOCKS5_PROXIES)
_current_proxy = None
_proxy_failures = {}

def get_next_proxy():
    """Получает следующий прокси из списка с учетом неудачных попыток"""
    global _current_proxy, _proxy_failures
    
    max_failures = get_max_failures()
    
    # Если текущий прокси работает, продолжаем его использовать
    if _current_proxy and _proxy_failures.get(_current_proxy, 0) < max_failures:
        return _current_proxy
    
    # Ищем рабочий прокси
    for _ in range(len(SOCKS5_PROXIES)):
        proxy = next(_proxy_cycle)
        if _proxy_failures.get(proxy, 0) < max_failures:
            _current_proxy = proxy
            return proxy
    
    # Если все прокси исчерпаны, сбрасываем счетчики и начинаем заново
    _proxy_failures.clear()
    _current_proxy = next(_proxy_cycle)
    return _current_proxy

def mark_proxy_failure(proxy):
    """Отмечает неудачную попытку для прокси"""
    global _proxy_failures
    _proxy_failures[proxy] = _proxy_failures.get(proxy, 0) + 1
    logging.warning(f"Прокси {proxy.split(':')[0]}:{proxy.split(':')[1]} неудача #{_proxy_failures[proxy]}")

def mark_proxy_success(proxy):
    """Сбрасывает счетчик неудач для успешного прокси"""
    global _proxy_failures
    if proxy in _proxy_failures:
        del _proxy_failures[proxy]

def get_proxy_config(proxy_string):
    """Преобразует строку прокси в конфигурацию для requests"""
    if not proxy_string:
        return None
    
    try:
        parts = proxy_string.split(':')
        if len(parts) != 4:
            return None
        
        ip, port, username, password = parts
        proxy_url = f"socks5://{username}:{password}@{ip}:{port}"
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    except Exception as e:
        logging.error(f"Ошибка при настройке прокси {proxy_string}: {e}")
        return None

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

def request(url, query, variables, name_request, max_retries=3, use_proxy=None):
    """Выполняет запрос с улучшенной обработкой остановки и поддержкой SOCKS5 прокси"""
    retries = 0
    
    # Если use_proxy не указан, используем настройку из конфигурации
    if use_proxy is None:
        use_proxy = is_proxy_enabled()
    
    # Получаем таймаут из конфигурации
    timeout = get_proxy_timeout()
    
    while retries < max_retries:
        current_proxy = None
        proxy_config = None
        
        if use_proxy:
            current_proxy = get_next_proxy()
            proxy_config = get_proxy_config(current_proxy)
            
            if proxy_config:
                proxy_display = f"{current_proxy.split(':')[0]}:{current_proxy.split(':')[1]}"
                logging.info(f"Использую SOCKS5 прокси: {proxy_display}")
            else:
                logging.warning("Не удалось настроить прокси, выполняю запрос без прокси")
        
        try:
            # Проверяем флаг остановки перед каждым запросом
            check_stop_flag()
            
            logging.info(f"Отправка запроса к {url}, для получения данных об {name_request}")
            
            # Выполняем запрос с прокси или без него
            if proxy_config:
                response = requests.post(
                    url=url, 
                    json={"query": query, "variables": variables}, 
                    proxies=proxy_config,
                    timeout=timeout
                )
            else:
                response = requests.post(
                    url=url, 
                    json={"query": query, "variables": variables}, 
                    timeout=timeout
                )
            
            if response.status_code == 200:
                if current_proxy:
                    mark_proxy_success(current_proxy)
                logging.info("Запрос успешно выполнен")
                return response.json()
            elif response.status_code == 429:
                retries += 1
                wait_time = min(2 ** retries, 10)  # Экспоненциальное увеличение времени ожидания до максимума 10 сек
                logging.warning(f"Слишком много запросов. Ожидание {wait_time} сек перед повторной попыткой... (попытка {retries}/{max_retries})")
                
                # Отмечаем неудачу прокси при rate limiting
                if current_proxy:
                    mark_proxy_failure(current_proxy)
                
                # Проверяем флаг остановки каждую секунду во время ожидания
                for i in range(wait_time):
                    check_stop_flag()
                    time.sleep(1)
                    
            else:
                logging.error(f"Ошибка HTTP: {response.status_code}, Ответ: {response.text}")
                if current_proxy:
                    mark_proxy_failure(current_proxy)
                retries += 1
                if retries < max_retries:
                    logging.info(f"Повторная попытка через 2 секунды... (попытка {retries}/{max_retries})")
                    time.sleep(2)
                    
        except ParserStoppedException:
            # Пробрасываем исключение остановки дальше
            raise
        except requests.exceptions.ProxyError as e:
            if current_proxy:
                mark_proxy_failure(current_proxy)
            retries += 1
            logging.error(f"Ошибка прокси {current_proxy}: {str(e)}")
            if retries < max_retries:
                logging.info(f"Переключение на другой прокси и повторная попытка... (попытка {retries}/{max_retries})")
                time.sleep(2)
            else:
                raise
        except requests.exceptions.RequestException as e:
            if current_proxy:
                mark_proxy_failure(current_proxy)
            retries += 1
            logging.error(f"Ошибка сети при выполнении запроса: {str(e)}")
            if retries < max_retries:
                logging.info(f"Повторная попытка через 2 секунды... (попытка {retries}/{max_retries})")
                time.sleep(2)
            else:
                raise
        except Exception as e:
            if current_proxy:
                mark_proxy_failure(current_proxy)
            logging.error(f"Произошла ошибка при выполнении запроса: {str(e)}")
            raise
    
    # Если все попытки исчерпаны
    raise Exception(f"Не удалось выполнить запрос после {max_retries} попыток")

def get_proxy_status():
    """Возвращает статус всех прокси"""
    max_failures = get_max_failures()
    status = {}
    for proxy in SOCKS5_PROXIES:
        proxy_display = f"{proxy.split(':')[0]}:{proxy.split(':')[1]}"
        failures = _proxy_failures.get(proxy, 0)
        status[proxy_display] = {
            'failures': failures,
            'active': failures < max_failures,
            'current': proxy == _current_proxy
        }
    return status