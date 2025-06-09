#!/usr/bin/env python3
"""
Улучшенный модуль для обхода антибот-защиты DNS
"""

import os
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import logging

logger = logging.getLogger('dns_antibot')

def get_enhanced_chrome_options():
    """Получить улучшенные опции Chrome для обхода антибот-защиты"""
    options = Options()
    
    # Базовые опции
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # Обход детекции автоматизации
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--exclude-switches=enable-automation')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-first-run')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-infobars')
    
    # Симуляция реального браузера
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--disable-ipc-flooding-protection')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-client-side-phishing-detection')
    options.add_argument('--disable-hang-monitor')
    options.add_argument('--disable-prompt-on-repost')
    options.add_argument('--disable-domain-reliability')
    options.add_argument('--disable-component-update')
    options.add_argument('--disable-background-downloads')
    options.add_argument('--disable-add-to-shelf')
    options.add_argument('--disable-datasaver-prompt')
    options.add_argument('--disable-desktop-notifications')
    
    # Реалистичный User-Agent
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
    ]
    options.add_argument(f'--user-agent={random.choice(user_agents)}')
    
    # Для Docker окружения
    in_docker = os.path.exists('/.dockerenv') or os.environ.get('DISPLAY') == ':99'
    if in_docker:
        options.add_argument('--headless')  # В Docker обязательно headless
        options.add_argument('--single-process')
        options.add_argument('--disable-background-networking')
    
    return options

def init_enhanced_driver():
    """Инициализировать драйвер с улучшенным обходом антибот-защиты"""
    options = get_enhanced_chrome_options()
    
    # Поиск Chrome бинарника
    chrome_binary_paths = [
        '/usr/bin/google-chrome-stable',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium'
    ]
    
    chrome_binary = None
    for path in chrome_binary_paths:
        if os.path.exists(path):
            chrome_binary = path
            logger.info(f"Found Chrome binary: {chrome_binary}")
            break
    
    if chrome_binary:
        options.binary_location = chrome_binary
    
    # Определение пути к ChromeDriver
    in_docker = os.path.exists('/.dockerenv') or os.environ.get('DISPLAY') == ':99'
    if in_docker:
        chromedriver_paths = ['/home/parser/chromedriver', '/usr/local/bin/chromedriver']
        chromedriver_path = None
        for path in chromedriver_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                chromedriver_path = path
                logger.info(f"Using ChromeDriver: {chromedriver_path}")
                break
        
        if not chromedriver_path:
            logger.error("No accessible ChromeDriver found in Docker")
            raise RuntimeError("ChromeDriver not found")
    else:
        chromedriver_path = ChromeDriverManager().install()
        logger.info(f"Downloaded ChromeDriver: {chromedriver_path}")
    
    # Инициализация undetected-chromedriver
    try:
        driver = uc.Chrome(
            options=options,
            driver_executable_path=chromedriver_path,
            browser_executable_path=chrome_binary if chrome_binary else None,
            version_main=None,
            use_subprocess=True
        )
        
        # Дополнительные настройки после инициализации
        try:
            # Скрываем webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Переопределяем plugins
            driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            
            # Переопределяем languages
            driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU', 'ru', 'en-US', 'en']})")
            
            # Переопределяем platform
            driver.execute_script("Object.defineProperty(navigator, 'platform', {get: () => 'Win32'})")
            
            # Устанавливаем реалистичные размеры экрана
            driver.execute_script("Object.defineProperty(screen, 'width', {get: () => 1920})")
            driver.execute_script("Object.defineProperty(screen, 'height', {get: () => 1080})")
            
            logger.info("Applied anti-detection scripts")
        except Exception as e:
            logger.warning(f"Could not apply some anti-detection scripts: {e}")
        
        logger.info("Enhanced Chrome driver initialized successfully")
        return driver
        
    except Exception as e:
        logger.error(f"Failed to initialize enhanced Chrome driver: {e}")
        raise

def simulate_human_browsing(driver, url, wait_time=(3, 7)):
    """Имитация человеческого поведения при загрузке страницы"""
    logger.info(f"Loading page with human simulation: {url}")
    
    # Сначала загружаем главную страницу для разогрева
    try:
        logger.info("Warming up with main page...")
        driver.get("https://www.dns-shop.ru/")
        time.sleep(random.uniform(2, 4))
        
        # Простая имитация активности на главной странице
        try:
            # Случайные движения мыши
            actions = ActionChains(driver)
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, 1800)
                y = random.randint(100, 1000)
                actions.move_by_offset(x, y)
                time.sleep(random.uniform(0.1, 0.3))
            actions.perform()
            
            # Случайный скроллинг
            driver.execute_script(f"window.scrollTo(0, {random.randint(100, 500)});")
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            logger.warning(f"Could not simulate mouse activity: {e}")
            
    except Exception as e:
        logger.warning(f"Could not warm up with main page: {e}")
    
    # Теперь загружаем целевую страницу
    driver.get(url)
    
    # Ждем загрузки
    wait_time_sec = random.uniform(*wait_time)
    logger.info(f"Waiting {wait_time_sec:.1f} seconds for page load...")
    time.sleep(wait_time_sec)
    
    # Дополнительная имитация активности
    try:
        # Проверяем заголовок страницы
        title = driver.title.lower()
        if any(word in title for word in ['403', 'forbidden', 'access denied', 'bot', 'captcha']):
            logger.warning(f"Detected blocking page: {title}")
            return False
        
        # Случайный скроллинг по странице
        for _ in range(random.randint(2, 5)):
            scroll_position = random.randint(100, 1000)
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(random.uniform(0.5, 1.5))
        
        # Возвращаемся в начало
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(random.uniform(1, 2))
        
        logger.info("Human browsing simulation completed")
        return True
        
    except Exception as e:
        logger.warning(f"Error in human browsing simulation: {e}")
        return True  # Продолжаем даже если симуляция не удалась

def check_for_blocking(driver):
    """Проверка на блокировку антибот-системой"""
    try:
        title = driver.title.lower()
        page_source = driver.page_source.lower()
        
        blocking_indicators = [
            '403', 'forbidden', 'access denied', 'captcha', 'cloudflare',
            'just a moment', 'checking your browser', 'bot detection',
            'security check', 'please wait', 'verifying you are human'
        ]
        
        for indicator in blocking_indicators:
            if indicator in title or indicator in page_source[:1000]:
                logger.warning(f"Detected blocking indicator: {indicator}")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking for blocking: {e}")
        return False

def enhanced_page_load(driver, url, max_retries=3):
    """Улучшенная загрузка страницы с повторными попытками"""
    for attempt in range(max_retries):
        logger.info(f"Attempt {attempt + 1}/{max_retries} to load: {url}")
        
        try:
            success = simulate_human_browsing(driver, url)
            
            if not success:
                logger.warning(f"Attempt {attempt + 1} failed - detected blocking")
                if attempt < max_retries - 1:
                    wait_time = random.uniform(10, 20)
                    logger.info(f"Waiting {wait_time:.1f} seconds before retry...")
                    time.sleep(wait_time)
                continue
            
            # Дополнительная проверка на блокировку
            if check_for_blocking(driver):
                logger.warning(f"Attempt {attempt + 1} blocked by anti-bot")
                if attempt < max_retries - 1:
                    wait_time = random.uniform(15, 30)
                    logger.info(f"Waiting {wait_time:.1f} seconds before retry...")
                    time.sleep(wait_time)
                continue
            
            logger.info(f"Successfully loaded page on attempt {attempt + 1}")
            return True
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed with error: {e}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(5, 10))
    
    logger.error(f"All {max_retries} attempts failed to load: {url}")
    return False 