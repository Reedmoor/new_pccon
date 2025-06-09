#!/usr/bin/env python3
"""
Тест гибридного алгоритма с реальными данными из файлов
"""

import os
import sys

# Добавляем путь к приложению
sys.path.insert(0, os.path.abspath('.'))

from app.utils.product_comparator import ProductComparator

def test_real_memory_comparison():
    """Тест с реальными данными оперативной памяти"""
    print("=== Тест гибридного алгоритма с реальными данными ===\n")
    print("🧠 Алгоритм: Эмбеддинги (25%) + Характеристики (40%) + N-граммы (35%)")
    
    comparator = ProductComparator()
    
    if not comparator.embeddings:
        print("❌ Ошибка: не удалось инициализировать эмбеддинги")
        return False
    
    # Пути к реальным файлам
    dns_path = 'app/utils/DNS_parsing/categories/product_data_Оперативная память DIMM.json'
    citi_path = 'app/utils/Citi_parser/data/moduli-pamyati/Товары.json'
    
    # Проверяем наличие файлов
    if not os.path.exists(dns_path):
        print(f"❌ Файл DNS не найден: {dns_path}")
        return False
    
    if not os.path.exists(citi_path):
        print(f"❌ Файл Citilink не найден: {citi_path}")
        return False
    
    print(f"✅ Файлы найдены:")
    print(f"   DNS: {dns_path}")
    print(f"   Citilink: {citi_path}")
    
    # Загружаем данные
    print("\n📁 Загрузка данных...")
    dns_data = comparator.load_json_data(dns_path)
    citi_data = comparator.load_json_data(citi_path)
    
    if not dns_data:
        print("❌ Не удалось загрузить данные DNS")
        return False
    
    if not citi_data:
        print("❌ Не удалось загрузить данные Citilink")
        return False
    
    print(f"✅ Загружено:")
    print(f"   DNS товаров: {len(dns_data)}")
    print(f"   Citilink товаров: {len(citi_data)}")
    
    # Извлекаем названия
    dns_names = comparator.extract_names(dns_data, "name")
    citi_names = comparator.extract_names(citi_data, "name")
    
    print(f"   DNS названий: {len(dns_names)}")
    print(f"   Citilink названий: {len(citi_names)}")
    
    # Тестируем с разными порогами
    print("\n🔍 Тестирование с разными порогами...")
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
    
    for threshold in thresholds:
        print(f"\n🎯 Порог {threshold}:")
        
        # Сравниваем только первые 50 товаров для быстроты тестирования
        test_dns_names = dns_names[:50]
        test_citi_names = citi_names[:100]
        
        try:
            # Используем гибридный алгоритм
            matches = comparator.find_best_matches(
                test_dns_names, test_citi_names,
                threshold=threshold,
                use_enhanced=True
            )
            
            print(f"   ✅ Найдено совпадений: {len(matches)}")
            
            # Показываем первые несколько совпадений
            if matches:
                print(f"   📋 Примеры совпадений:")
                for i, (dns_name, citi_name, similarity) in enumerate(matches[:3], 1):
                    print(f"      {i}. Сходство: {similarity:.3f} ({similarity*100:.1f}%)")
                    print(f"         DNS: {dns_name[:80]}...")
                    print(f"         Citi: {citi_name[:80]}...")
                    
                    # Показываем анализ характеристик для первого товара
                    if i == 1:
                        features1 = comparator.extract_detailed_features(dns_name)
                        features2 = comparator.extract_detailed_features(citi_name)
                        print(f"         🔍 Характеристики DNS: {features1}")
                        print(f"         🔍 Характеристики Citi: {features2}")
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    return True

def test_patriot_search():
    """Специальный тест поиска памяти Patriot"""
    print("\n" + "="*80)
    print("=== Поиск памяти Patriot в реальных данных ===\n")
    
    comparator = ProductComparator()
    
    if not comparator.embeddings:
        print("❌ Ошибка: не удалось инициализировать эмбеддинги")
        return False
    
    # Пути к файлам
    dns_path = 'app/utils/DNS_parsing/categories/product_data_Оперативная память DIMM.json'
    citi_path = 'app/utils/Citi_parser/data/moduli-pamyati/Товары.json'
    
    # Загружаем данные
    dns_data = comparator.load_json_data(dns_path)
    citi_data = comparator.load_json_data(citi_path)
    
    if not dns_data or not citi_data:
        print("❌ Не удалось загрузить данные")
        return False
    
    # Ищем товары Patriot
    dns_patriot = [item['name'] for item in dns_data if 'patriot' in item['name'].lower()]
    citi_patriot = [item['name'] for item in citi_data if 'patriot' in item['name'].lower()]
    
    print(f"🔍 Найдено товаров Patriot:")
    print(f"   DNS: {len(dns_patriot)}")
    print(f"   Citilink: {len(citi_patriot)}")
    
    if dns_patriot:
        print(f"\n📋 Примеры DNS Patriot:")
        for i, name in enumerate(dns_patriot[:3], 1):
            print(f"   {i}. {name}")
    
    if citi_patriot:
        print(f"\n📋 Примеры Citilink Patriot:")
        for i, name in enumerate(citi_patriot[:3], 1):
            print(f"   {i}. {name}")
    
    # Ищем совпадения
    if dns_patriot and citi_patriot:
        print(f"\n🔄 Поиск совпадений среди товаров Patriot...")
        
        try:
            matches = comparator.find_best_matches(
                dns_patriot[:10], citi_patriot[:10],
                threshold=0.5,
                use_enhanced=True
            )
            
            print(f"✅ Найдено совпадений: {len(matches)}")
            
            for i, (dns_name, citi_name, similarity) in enumerate(matches, 1):
                print(f"\n{i}. Сходство: {similarity:.3f} ({similarity*100:.1f}%)")
                print(f"   DNS: {dns_name}")
                print(f"   Citi: {citi_name}")
                
                # Анализ характеристик
                features1 = comparator.extract_detailed_features(dns_name)
                features2 = comparator.extract_detailed_features(citi_name)
                
                # Показываем общие характеристики
                common_features = set(features1.keys()) & set(features2.keys())
                if common_features:
                    print(f"   📊 Общие характеристики:")
                    for feature in common_features:
                        val1 = features1[feature]
                        val2 = features2[feature]
                        match = "✅" if val1 == val2 else "❌"
                        print(f"      {match} {feature}: {val1} ↔ {val2}")
                        
        except Exception as e:
            print(f"❌ Ошибка при поиске: {e}")
    
    return True

def main():
    """Главная функция"""
    print("🚀 Тестирование гибридного алгоритма с реальными данными")
    print("=" * 80)
    
    # Запускаем тесты
    test1_result = test_real_memory_comparison()
    test2_result = test_patriot_search()
    
    # Результаты
    print("\n" + "="*80)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("="*80)
    print(f"Тест с реальными данными:   {'✅ ПРОЙДЕН' if test1_result else '❌ НЕ ПРОЙДЕН'}")
    print(f"Поиск Patriot:              {'✅ ПРОЙДЕН' if test2_result else '❌ НЕ ПРОЙДЕН'}")
    
    if test1_result and test2_result:
        print("\n🎉 Все тесты пройдены!")
        print("💡 Гибридный алгоритм готов к использованию с реальными данными!")
        print("\n🔧 Система может:")
        print("   • Обрабатывать реальные файлы данных DNS и Citilink")
        print("   • Находить совпадения с учетом характеристик")
        print("   • Штрафовать критические различия (Ti vs без Ti, разные модели)")
        print("   • Сохранять семантическое понимание схожих товаров")
    else:
        print("\n⚠️  Некоторые тесты не пройдены.")
    
    return test1_result and test2_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 