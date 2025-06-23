"""
Конфигурация прокси для парсера Citilink
"""

# Рабочие SOCKS5 прокси (проверены и работают)
SOCKS5_PROXIES = [
    "91.191.184.244:63479:iXya3sZg:L51Gzyra",
    "45.140.64.215:62475:iXya3sZg:L51Gzyra",
    "194.156.0.61:64605:iXya3sZg:L51Gzyra"
]

# Настройки прокси
PROXY_SETTINGS = {
    'use_proxy': True,          # Включить/выключить использование прокси
    'max_failures': 3,          # Максимальное количество неудач для прокси
    'rotation_enabled': True,   # Ротация прокси
    'request_delay': 1,         # Задержка между запросами (секунды)
    'timeout': 30,              # Таймаут запроса (секунды)
}

def get_proxy_list():
    """Возвращает список активных прокси"""
    return SOCKS5_PROXIES.copy()

def is_proxy_enabled():
    """Проверяет включены ли прокси"""
    return PROXY_SETTINGS['use_proxy']

def get_proxy_timeout():
    """Возвращает таймаут для запросов через прокси"""
    return PROXY_SETTINGS['timeout']

def get_request_delay():
    """Возвращает задержку между запросами"""
    return PROXY_SETTINGS['request_delay']

def get_max_failures():
    """Возвращает максимальное количество неудач для прокси"""
    return PROXY_SETTINGS['max_failures'] 