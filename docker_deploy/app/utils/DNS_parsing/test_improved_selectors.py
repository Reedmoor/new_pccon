#!/usr/bin/env python3
"""
Тест улучшенных селекторов DNS парсера
"""

import os
import sys
import json
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('dns_selector_test')

def test_product_parsing():
    """Тестирование парсинга товара с улучшенными селекторами"""
    
    # Тестовые URL товаров разных категорий
    test_urls = [
        "https://www.dns-shop.ru/product/414e9c60e254ed20/materinskaa-plata-msi-b650-gaming-plus-wifi/",
        "https://www.dns-shop.ru/product/a67afeaff7bbd9cb/robot-pylesos-dreame-x40-ultra-complete-belyj/",
        "https://www.dns-shop.ru/product/bc7d5030dfce3330/videokarta-msi-geforce-rtx-4060-ventus-2x-black-8g-oc/"
    ]
    
    logger.info(f"Testing product parsing with {len(test_urls)} URLs")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(test_urls),
        "successful_tests": 0,
        "failed_tests": 0,
        "results": []
    }
    
    for i, url in enumerate(test_urls, 1):
        logger.info(f"\n=== Test {i}/{len(test_urls)}: {url} ===")
        
        test_result = {
            "url": url,
            "success": False,
            "errors": [],
            "extracted_data": {}
        }
        
        try:
            from productDetailsParser import parse_characteristics_page
            
            # Инициализируем драйвер аналогично основному скрипту
            import undetected_chromedriver as uc
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
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
                    break
            
            if chrome_binary:
                options.binary_location = chrome_binary
            
            # Инициализация драйвера
            in_docker = os.path.exists('/.dockerenv') or os.environ.get('DISPLAY') == ':99'
            if in_docker:
                # В Docker используем ChromeDriver из домашней директории
                chromedriver_paths = ['/home/parser/chromedriver', '/usr/local/bin/chromedriver']
                chromedriver_path = None
                for path in chromedriver_paths:
                    if os.path.exists(path) and os.access(path, os.X_OK):
                        chromedriver_path = path
                        break
            else:
                chromedriver_path = ChromeDriverManager().install()
            
            driver = uc.Chrome(
                options=options,
                driver_executable_path=chromedriver_path,
                browser_executable_path=chrome_binary if chrome_binary else None
            )
            
            # Парсим товар
            product_data = parse_characteristics_page(driver, url)
            
            if product_data:
                test_result["success"] = True
                test_result["extracted_data"] = {
                    "name": product_data.get('name'),
                    "price_discounted": product_data.get('price_discounted'),
                    "price_original": product_data.get('price_original'),
                    "categories_count": len(product_data.get('categories', [])),
                    "characteristics_groups": len(product_data.get('characteristics', {})),
                    "images_count": len(product_data.get('images', [])),
                    "brand_name": product_data.get('brand_name'),
                    "rating": product_data.get('rating'),
                    "number_of_reviews": product_data.get('number_of_reviews')
                }
                
                results["successful_tests"] += 1
                
                logger.info("✅ SUCCESS:")
                logger.info(f"  Name: {product_data.get('name')}")
                logger.info(f"  Price: {product_data.get('price_discounted')} (original: {product_data.get('price_original')})")
                logger.info(f"  Categories: {len(product_data.get('categories', []))}")
                logger.info(f"  Characteristics: {len(product_data.get('characteristics', {}))} groups")
                logger.info(f"  Images: {len(product_data.get('images', []))}")
                logger.info(f"  Brand: {product_data.get('brand_name')}")
                logger.info(f"  Rating: {product_data.get('rating')} ({product_data.get('number_of_reviews')} reviews)")
                
            else:
                test_result["errors"].append("No product data extracted")
                results["failed_tests"] += 1
                logger.error("❌ FAILED: No product data extracted")
            
            driver.quit()
            
        except Exception as e:
            test_result["errors"].append(str(e))
            results["failed_tests"] += 1
            logger.error(f"❌ FAILED: {str(e)}")
            try:
                driver.quit()
            except:
                pass
        
        results["results"].append(test_result)
    
    # Сохраняем результаты
    with open('selector_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n=== SUMMARY ===")
    logger.info(f"Total tests: {results['total_tests']}")
    logger.info(f"Successful: {results['successful_tests']}")
    logger.info(f"Failed: {results['failed_tests']}")
    logger.info(f"Success rate: {(results['successful_tests']/results['total_tests']*100):.1f}%")
    logger.info(f"Results saved to: selector_test_results.json")
    
    return results["successful_tests"] == results["total_tests"]

def test_links_parsing():
    """Тестирование парсинга ссылок на товары"""
    
    logger.info("\n=== Testing links parsing ===")
    
    # Тестовые URL категорий
    test_category_urls = [
        "https://www.dns-shop.ru/catalog/17a892f816404e77/videokarty/?p=1",
        "https://www.dns-shop.ru/catalog/17a899cd16404e77/processory/?p=1",
        "https://www.dns-shop.ru/catalog/17a89aab16404e77/materinskie-platy/?p=1"
    ]
    
    try:
        from linksParser import get_urls_from_page
        import undetected_chromedriver as uc
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox') 
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Поиск Chrome бинарника
        chrome_binary_paths = [
            '/usr/bin/google-chrome-stable',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser'
        ]
        
        chrome_binary = None
        for path in chrome_binary_paths:
            if os.path.exists(path):
                chrome_binary = path
                break
        
        if chrome_binary:
            options.binary_location = chrome_binary
        
        # Инициализация драйвера
        in_docker = os.path.exists('/.dockerenv') or os.environ.get('DISPLAY') == ':99'
        if in_docker:
            chromedriver_paths = ['/home/parser/chromedriver', '/usr/local/bin/chromedriver']
            chromedriver_path = None
            for path in chromedriver_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    chromedriver_path = path
                    break
        else:
            chromedriver_path = ChromeDriverManager().install()
        
        driver = uc.Chrome(
            options=options,
            driver_executable_path=chromedriver_path,
            browser_executable_path=chrome_binary if chrome_binary else None
        )
        
        total_links = 0
        
        for i, url in enumerate(test_category_urls, 1):
            logger.info(f"\nTesting category {i}: {url}")
            driver.get(url)
            
            # Ждем загрузки страницы
            import time
            time.sleep(3)
            
            links = get_urls_from_page(driver)
            total_links += len(links)
            
            logger.info(f"Found {len(links)} product links")
            if links:
                logger.info(f"Example links:")
                for link in links[:3]:
                    logger.info(f"  - {link}")
        
        driver.quit()
        
        logger.info(f"\nTotal links found across all categories: {total_links}")
        return total_links > 0
        
    except Exception as e:
        logger.error(f"Links parsing test failed: {e}")
        return False

def main():
    """Основная функция тестирования"""
    logger.info("=== DNS Parser Improved Selectors Test ===")
    
    tests_passed = 0
    total_tests = 2
    
    # Тест парсинга товаров
    if test_product_parsing():
        tests_passed += 1
        logger.info("✅ Product parsing test PASSED")
    else:
        logger.error("❌ Product parsing test FAILED")
    
    # Тест парсинга ссылок
    if test_links_parsing():
        tests_passed += 1
        logger.info("✅ Links parsing test PASSED")
    else:
        logger.error("❌ Links parsing test FAILED")
    
    logger.info(f"\n=== FINAL RESULTS ===")
    logger.info(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        logger.info("🎉 All tests PASSED! Improved selectors are working correctly.")
        return 0
    else:
        logger.error("💥 Some tests FAILED. Check the logs for details.")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 