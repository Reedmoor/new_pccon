#!/usr/bin/env python3
"""
Скрипт для тестирования настройки DNS парсера в Docker контейнере
"""

import os
import sys
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('dns_parser_test')

def test_chrome_setup():
    """Тестирование настройки Chrome в Docker"""
    logger.info("Testing Chrome setup in Docker environment...")
    
    # Проверяем наличие Chrome
    chrome_paths = [
        '/usr/bin/google-chrome-stable',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium'
    ]
    
    chrome_binary = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_binary = path
            logger.info(f"Found Chrome binary: {chrome_binary}")
            break
    
    if not chrome_binary:
        logger.error("No Chrome binary found!")
        return False
    
    # Проверяем ChromeDriver
    chromedriver_paths = [
        '/home/parser/chromedriver',
        '/usr/local/bin/chromedriver',
        '/usr/bin/chromedriver'
    ]
    
    chromedriver_path = None
    for path in chromedriver_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            chromedriver_path = path
            logger.info(f"Found accessible ChromeDriver: {chromedriver_path}")
            break
    
    if not chromedriver_path:
        logger.error("No accessible ChromeDriver found!")
        return False
    
    # Настройка Chrome опций
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--single-process')
    options.add_argument('--disable-background-networking')
    options.binary_location = chrome_binary
    
    # Тестируем Chrome WebDriver
    try:
        logger.info("Testing undetected Chrome driver...")
        driver = uc.Chrome(
            options=options,
            driver_executable_path=chromedriver_path,
            browser_executable_path=chrome_binary
        )
        
        # Тестируем загрузку простой страницы
        driver.get("https://httpbin.org/ip")
        logger.info(f"Page title: {driver.title}")
        logger.info("Successfully loaded test page")
        
        driver.quit()
        logger.info("Chrome driver test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Chrome driver test FAILED: {e}")
        
        # Fallback тест с обычным WebDriver
        try:
            logger.info("Testing regular Chrome driver as fallback...")
            driver = webdriver.Chrome(options=options)
            driver.get("https://httpbin.org/ip")
            logger.info(f"Fallback page title: {driver.title}")
            driver.quit()
            logger.info("Fallback Chrome driver test PASSED")
            return True
        except Exception as fallback_error:
            logger.error(f"Fallback Chrome driver test also FAILED: {fallback_error}")
            return False

def test_file_permissions():
    """Тестирование прав доступа к файлам"""
    logger.info("Testing file permissions...")
    
    test_dirs = [
        '/app/data',
        '/app/logs', 
        '/app/parsers/dns',
        '.'
    ]
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            readable = os.access(test_dir, os.R_OK)
            writable = os.access(test_dir, os.W_OK)
            logger.info(f"{test_dir}: readable={readable}, writable={writable}")
        else:
            logger.warning(f"{test_dir}: does not exist")

def test_network_connectivity():
    """Тестирование сетевого подключения"""
    logger.info("Testing network connectivity...")
    
    import requests
    
    test_urls = [
        'https://httpbin.org/ip',
        'https://www.dns-shop.ru',
        'https://google.com'
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            logger.info(f"{url}: status={response.status_code}")
        except Exception as e:
            logger.error(f"{url}: failed - {e}")

def main():
    """Основная функция тестирования"""
    logger.info("Starting DNS parser Docker setup test...")
    
    # Проверяем среду выполнения
    in_docker = os.path.exists('/.dockerenv') or os.environ.get('DISPLAY') == ':99'
    logger.info(f"Running in Docker: {in_docker}")
    
    # Выполняем тесты
    tests_passed = 0
    total_tests = 3
    
    if test_file_permissions():
        tests_passed += 1
    
    if test_network_connectivity():
        tests_passed += 1
    
    if test_chrome_setup():
        tests_passed += 1
    
    logger.info(f"Tests completed: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        logger.info("All tests PASSED - DNS parser should work correctly")
        return 0
    else:
        logger.error("Some tests FAILED - DNS parser may have issues")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 