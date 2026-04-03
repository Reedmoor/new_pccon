import requests
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class ProxyManager:
    def __init__(self, proxy_list=None):
        self.proxy_list = proxy_list or []
        self.current_index = 0
        self.working_proxies = []
        self.lock = threading.Lock()
        
    def add_proxy(self, host, http_port, socks5_port, username, password):
        """Добавляет новый прокси в список"""
        proxy = {
            'host': host,
            'http_port': http_port,
            'socks5_port': socks5_port,
            'username': username,
            'password': password
        }
        self.proxy_list.append(proxy)
        logging.info(f"Добавлен прокси: {host}:{http_port}")
        
    def get_proxy_dict(self, proxy_info, use_socks=False):
        """Конвертирует информацию о прокси в формат requests"""
        port = proxy_info['socks5_port'] if use_socks else proxy_info['http_port']
        protocol = 'socks5' if use_socks else 'http'
        
        proxy_url = f"{protocol}://{proxy_info['username']}:{proxy_info['password']}@{proxy_info['host']}:{port}"
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def test_single_proxy(self, proxy_info, timeout=10):
        """Тестирует один прокси"""
        try:
            proxy_dict = self.get_proxy_dict(proxy_info)
            
            # Тестируем с коротким timeout
            response = requests.get('https://httpbin.org/ip', proxies=proxy_dict, timeout=timeout)
            
            if response.status_code == 200:
                ip_info = response.json()
                logging.info(f"✅ Прокси {proxy_info['host']}:{proxy_info['http_port']} работает. IP: {ip_info.get('origin', 'unknown')}")
                return True, proxy_info, ip_info.get('origin', 'unknown')
            else:
                logging.warning(f"❌ Прокси {proxy_info['host']}:{proxy_info['http_port']} вернул код {response.status_code}")
                return False, proxy_info, None
                
        except Exception as e:
            logging.warning(f"❌ Прокси {proxy_info['host']}:{proxy_info['http_port']} не работает: {str(e)}")
            return False, proxy_info, None
    
    def test_all_proxies(self, timeout=10, max_workers=3):
        """Тестирует все прокси параллельно"""
        if not self.proxy_list:
            logging.warning("Список прокси пуст")
            return []
        
        logging.info(f"🧪 Тестируем {len(self.proxy_list)} прокси...")
        working_proxies = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Запускаем тесты параллельно
            future_to_proxy = {
                executor.submit(self.test_single_proxy, proxy, timeout): proxy 
                for proxy in self.proxy_list
            }
            
            for future in as_completed(future_to_proxy):
                is_working, proxy_info, ip = future.result()
                if is_working:
                    working_proxies.append(proxy_info)
        
        self.working_proxies = working_proxies
        logging.info(f"✅ Найдено {len(working_proxies)} рабочих прокси из {len(self.proxy_list)}")
        return working_proxies
    
    def get_next_proxy(self, use_working_only=True):
        """Получает следующий прокси из списка"""
        with self.lock:
            proxy_source = self.working_proxies if use_working_only and self.working_proxies else self.proxy_list
            
            if not proxy_source:
                return None
            
            proxy = proxy_source[self.current_index]
            self.current_index = (self.current_index + 1) % len(proxy_source)
            
            return self.get_proxy_dict(proxy)
    
    def remove_proxy(self, host, port):
        """Удаляет прокси из списка"""
        self.proxy_list = [p for p in self.proxy_list if not (p['host'] == host and p['http_port'] == port)]
        self.working_proxies = [p for p in self.working_proxies if not (p['host'] == host and p['http_port'] == port)]
        logging.info(f"Удален прокси: {host}:{port}")
    
    def get_proxy_stats(self):
        """Возвращает статистику по прокси"""
        return {
            'total_proxies': len(self.proxy_list),
            'working_proxies': len(self.working_proxies),
            'current_index': self.current_index
        }

# Функция для быстрого тестирования
def quick_test_proxies():
    """Быстрое тестирование всех прокси"""
    from request_handler import PROXY_LIST
    
    manager = ProxyManager(PROXY_LIST)
    working = manager.test_all_proxies(timeout=5)
    
    print(f"\n📊 Результаты тестирования:")
    print(f"Всего прокси: {len(PROXY_LIST)}")
    print(f"Рабочих прокси: {len(working)}")
    
    if working:
        print("\n✅ Рабочие прокси:")
        for proxy in working:
            print(f"  - {proxy['host']}:{proxy['http_port']}")
    
    return working

if __name__ == "__main__":
    quick_test_proxies() 