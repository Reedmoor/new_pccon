#!/usr/bin/env python3
"""
Тест улучшенной антибот-защиты DNS парсера
"""

import os
import sys
import json
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('dns_antibot_test')

def test_enhanced_antibot():
    """Тестирование улучшенной антибот-защиты"""
    
    test_urls = [
        "https://www.dns-shop.ru/",
        "https://www.dns-shop.ru/product/414e9c60e254ed20/materinskaa-plata-msi-b650-gaming-plus-wifi/",
        "https://www.dns-shop.ru/catalog/17a892f816404e77/videokarty/?p=1"
    ]
    
    logger.info(f"Testing enhanced anti-bot protection with {len(test_urls)} URLs")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(test_urls),
        "successful_loads": 0,
        "blocked_loads": 0,
        "failed_loads": 0,
        "results": []
    }
    
    try:
        from enhanced_antibot import init_enhanced_driver, enhanced_page_load, check_for_blocking
        
        # Инициализируем драйвер
        logger.info("Initializing enhanced anti-bot driver...")
        driver = init_enhanced_driver()
        
        for i, url in enumerate(test_urls, 1):
            logger.info(f"\n=== Test {i}/{len(test_urls)}: {url} ===")
            
            test_result = {
                "url": url,
                "success": False,
                "blocked": False,
                "error": None,
                "title": None,
                "content_length": 0
            }
            
            try:
                # Пытаемся загрузить страницу
                success = enhanced_page_load(driver, url, max_retries=2)
                
                if success:
                    # Проверяем на блокировку
                    blocked = check_for_blocking(driver)
                    test_result["blocked"] = blocked
                    test_result["title"] = driver.title
                    test_result["content_length"] = len(driver.page_source)
                    
                    if not blocked:
                        test_result["success"] = True
                        results["successful_loads"] += 1
                        logger.info(f"✅ SUCCESS: Page loaded successfully")
                        logger.info(f"  Title: {driver.title}")
                        logger.info(f"  Content length: {len(driver.page_source)} chars")
                    else:
                        results["blocked_loads"] += 1
                        logger.warning(f"🚫 BLOCKED: Page was blocked by anti-bot")
                        logger.warning(f"  Title: {driver.title}")
                else:
                    results["failed_loads"] += 1
                    test_result["error"] = "Failed to load page after retries"
                    logger.error(f"❌ FAILED: Could not load page after retries")
                    
            except Exception as e:
                test_result["error"] = str(e)
                results["failed_loads"] += 1
                logger.error(f"❌ ERROR: {str(e)}")
            
            results["results"].append(test_result)
        
        driver.quit()
        
    except Exception as e:
        logger.error(f"Failed to initialize or run test: {e}")
        return False
    
    # Сохраняем результаты
    with open('antibot_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n=== ANTIBOT TEST SUMMARY ===")
    logger.info(f"Total tests: {results['total_tests']}")
    logger.info(f"Successful loads: {results['successful_loads']}")
    logger.info(f"Blocked loads: {results['blocked_loads']}")
    logger.info(f"Failed loads: {results['failed_loads']}")
    
    success_rate = results['successful_loads'] / results['total_tests'] * 100
    logger.info(f"Success rate: {success_rate:.1f}%")
    logger.info(f"Results saved to: antibot_test_results.json")
    
    # Считаем тест успешным если хотя бы один URL загрузился успешно
    return results['successful_loads'] > 0

def test_product_parsing_with_antibot():
    """Тестирование парсинга товара с улучшенной антибот-защитой"""
    
    logger.info("\n=== Testing product parsing with enhanced anti-bot ===")
    
    test_url = "https://www.dns-shop.ru/product/414e9c60e254ed20/materinskaa-plata-msi-b650-gaming-plus-wifi/"
    
    try:
        from enhanced_antibot import init_enhanced_driver, enhanced_page_load
        from productDetailsParser import parse_characteristics_page
        
        # Инициализируем драйвер
        driver = init_enhanced_driver()
        
        # Парсим товар с использованием улучшенной защиты
        product_data = parse_characteristics_page(driver, test_url)
        
        driver.quit()
        
        if product_data:
            logger.info("✅ Product parsing with anti-bot PASSED")
            logger.info(f"  Product name: {product_data.get('name')}")
            logger.info(f"  Price: {product_data.get('price_discounted')}")
            logger.info(f"  Categories: {len(product_data.get('categories', []))}")
            logger.info(f"  Characteristics: {len(product_data.get('characteristics', {}))}")
            return True
        else:
            logger.error("❌ Product parsing with anti-bot FAILED")
            return False
            
    except Exception as e:
        logger.error(f"Product parsing test failed: {e}")
        return False

def main():
    """Основная функция тестирования"""
    logger.info("=== DNS Enhanced Anti-Bot Protection Test ===")
    
    tests_passed = 0
    total_tests = 2
    
    # Тест загрузки страниц
    if test_enhanced_antibot():
        tests_passed += 1
        logger.info("✅ Enhanced anti-bot test PASSED")
    else:
        logger.error("❌ Enhanced anti-bot test FAILED")
    
    # Тест парсинга товара
    if test_product_parsing_with_antibot():
        tests_passed += 1
        logger.info("✅ Product parsing with anti-bot test PASSED")
    else:
        logger.error("❌ Product parsing with anti-bot test FAILED")
    
    logger.info(f"\n=== FINAL RESULTS ===")
    logger.info(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed >= 1:  # Хотя бы один тест должен пройти
        logger.info("🎉 Anti-bot protection is working!")
        return 0
    else:
        logger.error("💥 All anti-bot tests FAILED. Check DNS blocking.")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 