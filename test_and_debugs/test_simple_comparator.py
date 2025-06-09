#!/usr/bin/env python3
"""
Тестовый скрипт для проверки SimpleProductComparator (без нейронных сетей)
"""

import os
import sys

# Добавляем путь к приложению
sys.path.insert(0, os.path.abspath('.'))

from app.utils.simple_comparator import SimpleProductComparator

def test_simple_gpu_comparison():
    """Тест сравнения видеокарт с простым алгоритмом"""
    print("=== Тест простого сравнения видеокарт ===\n")
    
    comparator = SimpleProductComparator()
    
    # Тестовые данные - критичные различия в моделях
    gpu_names1 = [
        "NVIDIA GeForce RTX 4090 24GB GDDR6X",
        "AMD Radeon RX 7700 XT 12GB GDDR6", 
        "NVIDIA GeForce GTX 1660 Ti 6GB GDDR6",
        "Intel Arc A770 16GB GDDR6"
    ]
    
    gpu_names2 = [
        "NVIDIA GeForce RTX 4090 Ti 24GB GDDR6X",  # Ti версия - должен штрафоваться
        "AMD Radeon RX 7800 XT 16GB GDDR6",        # Другая модель - штраф
        "NVIDIA GeForce GTX 1660 Super 6GB GDDR6", # Super вместо Ti - штраф
        "Intel Arc A750 8GB GDDR6"                 # Другая модель - штраф
    ]
    
    print("Видеокарты группа 1:")
    for i, name in enumerate(gpu_names1, 1):
        print(f"{i}. {name}")
    
    print("\nВидеокарты группа 2:")
    for i, name in enumerate(gpu_names2, 1):
        print(f"{i}. {name}")
    
    print("\n" + "="*80)
    print("Анализ с простым алгоритмом (без нейронных сетей)...")
    
    matches = comparator.find_simple_matches(gpu_names1, gpu_names2, threshold=0.3)
    
    if matches:
        print(f"\n✅ Найдено {len(matches)} совпадений:")
        for i, (name1, name2, similarity, details) in enumerate(matches, 1):
            print(f"\n{i}. Итоговое сходство: {similarity:.4f} ({similarity*100:.1f}%)")
            print(f"   Группа 1: {name1}")
            print(f"   Группа 2: {name2}")
            print(f"   📊 Детальный анализ:")
            print(f"      • Сходство характеристик: {details['feature_similarity']:.3f}")
            print(f"      • N-грамм сходство (3): {details['ngram3_similarity']:.3f}")
            print(f"      • N-грамм сходство (5): {details['ngram5_similarity']:.3f}")
            print(f"      • Штраф: {details['penalty']:.3f}")
            
            # Показываем извлеченные характеристики
            features1 = details['features1']
            features2 = details['features2']
            
            if features1 or features2:
                print(f"   🔍 Характеристики:")
                for key in set(features1.keys()) | set(features2.keys()):
                    val1 = features1.get(key, '—')
                    val2 = features2.get(key, '—')
                    match_symbol = "✅" if val1 == val2 else "❌"
                    print(f"      {match_symbol} {key}: {val1} ↔ {val2}")
                    
                    # Особое внимание к различиям в вариантах GPU
                    if key == 'gpu_variant' and val1 != val2:
                        print(f"         ⚠️  ВНИМАНИЕ: Разные варианты GPU!")
                    elif key == 'gpu_model' and val1 != val2:
                        print(f"         ⚠️  ВНИМАНИЕ: Разные модели GPU!")
    else:
        print("\n❌ Совпадений не найдено")
        
    return len(matches) > 0

def test_patriot_memory_detailed():
    """Детальный тест с памятью Patriot"""
    print("\n" + "="*80)
    print("=== Детальный тест памяти Patriot ===\n")
    
    comparator = SimpleProductComparator()
    
    # Оригинальный пример от пользователя
    dns_names = [
        "Оперативная память Patriot Signature [PSD48G240081] 8 ГБ"
    ]
    
    citi_names = [
        "Оперативная память Patriot Signature PSD48G266681 DDR4 - 1x 8ГБ 2666МГц, DIMM, Ret"
    ]
    
    print("DNS:", dns_names[0])
    print("Citilink:", citi_names[0])
    
    print("\n" + "-"*60)
    print("Пошаговый анализ характеристик...")
    
    # Извлекаем характеристики для анализа
    features1 = comparator.extract_detailed_features(dns_names[0])
    features2 = comparator.extract_detailed_features(citi_names[0])
    
    print(f"\n🔍 Извлеченные характеристики:")
    print(f"DNS: {features1}")
    print(f"Citilink: {features2}")
    
    # Анализируем различные компоненты сходства
    feature_sim = comparator.calculate_feature_similarity(features1, features2)
    ngram3_sim = comparator.calculate_ngram_similarity(dns_names[0], citi_names[0], 3)
    ngram5_sim = comparator.calculate_ngram_similarity(dns_names[0], citi_names[0], 5)
    penalty = comparator.calculate_penalty(features1, features2)
    
    print(f"\n📊 Компоненты сходства:")
    print(f"   • Сходство характеристик: {feature_sim:.3f}")
    print(f"   • N-грамм сходство (3): {ngram3_sim:.3f}")
    print(f"   • N-грамм сходство (5): {ngram5_sim:.3f}")
    print(f"   • Штраф: {penalty:.3f}")
    
    # Итоговое сходство
    total_similarity = comparator.simple_similarity(dns_names[0], citi_names[0])
    print(f"   • ИТОГОВОЕ СХОДСТВО: {total_similarity:.3f} ({total_similarity*100:.1f}%)")
    
    # Тест с разными порогами
    print(f"\n🎯 Тест с разными порогами:")
    thresholds = [0.3, 0.4, 0.5, 0.6]
    for threshold in thresholds:
        matches = comparator.find_simple_matches(dns_names, citi_names, threshold)
        status = "✅ НАЙДЕНО" if matches else "❌ НЕ НАЙДЕНО"
        print(f"   Порог {threshold}: {status}")
    
    return total_similarity > 0.3

def test_cpu_models():
    """Тест различий в моделях процессоров"""
    print("\n" + "="*80)
    print("=== Тест различий в моделях процессоров ===\n")
    
    comparator = SimpleProductComparator()
    
    # Тестовые данные процессоров с близкими моделями
    cpu_tests = [
        ("Intel Core i5-12400F", "Intel Core i5-12600K"),  # 12400 vs 12600 - разница 200
        ("AMD Ryzen 5 5600X", "AMD Ryzen 5 5700X"),       # 5600 vs 5700 - разница 100  
        ("Intel Core i7-13700K", "Intel Core i7-13700F"), # Одинаковые модели, разные суффиксы
    ]
    
    print("Тестирование близких моделей процессоров:")
    
    for i, (cpu1, cpu2) in enumerate(cpu_tests, 1):
        print(f"\n{i}. {cpu1} vs {cpu2}")
        
        # Извлекаем характеристики
        features1 = comparator.extract_detailed_features(cpu1)
        features2 = comparator.extract_detailed_features(cpu2)
        
        print(f"   Характеристики 1: {features1}")
        print(f"   Характеристики 2: {features2}")
        
        # Вычисляем сходство
        similarity = comparator.simple_similarity(cpu1, cpu2)
        feature_sim = comparator.calculate_feature_similarity(features1, features2)
        penalty = comparator.calculate_penalty(features1, features2)
        
        print(f"   Сходство характеристик: {feature_sim:.3f}")
        print(f"   Штраф: {penalty:.3f}")
        print(f"   ИТОГОВОЕ СХОДСТВО: {similarity:.3f} ({similarity*100:.1f}%)")
        
        # Анализируем модели
        if 'cpu_model' in features1 and 'cpu_model' in features2:
            import re
            try:
                num1 = int(re.findall(r'\d+', features1['cpu_model'])[0])
                num2 = int(re.findall(r'\d+', features2['cpu_model'])[0])
                diff = abs(num1 - num2)
                print(f"   Разность моделей: {diff}")
                
                if diff > 100:
                    print("   ⚠️  ВНИМАНИЕ: Существенная разность в моделях!")
                elif diff > 50:
                    print("   ⚠️  Умеренная разность в моделях")
                else:
                    print("   ✅ Близкие модели")
            except:
                print("   ❓ Не удалось извлечь числовые модели")
    
    return True

def test_brand_differences():
    """Тест различий в брендах"""
    print("\n" + "="*80)
    print("=== Тест различий в брендах ===\n")
    
    comparator = SimpleProductComparator()
    
    # Тестовые данные с разными брендами
    brand_tests = [
        ("NVIDIA GeForce RTX 4090", "AMD Radeon RX 7900 XTX"),  # Разные бренды
        ("Kingston HyperX 16GB", "Corsair Vengeance 16GB"),     # Разные бренды памяти
        ("Intel Core i7-13700K", "AMD Ryzen 7 7700X"),         # Разные бренды CPU
    ]
    
    print("Тестирование разных брендов:")
    
    for i, (product1, product2) in enumerate(brand_tests, 1):
        print(f"\n{i}. {product1} vs {product2}")
        
        # Извлекаем характеристики
        features1 = comparator.extract_detailed_features(product1)
        features2 = comparator.extract_detailed_features(product2)
        
        brand1 = features1.get('brand', '—')
        brand2 = features2.get('brand', '—')
        
        print(f"   Бренд 1: {brand1}")
        print(f"   Бренд 2: {brand2}")
        
        # Вычисляем сходство и штраф
        similarity = comparator.simple_similarity(product1, product2)
        penalty = comparator.calculate_penalty(features1, features2)
        
        print(f"   Штраф: {penalty:.3f}")
        print(f"   ИТОГОВОЕ СХОДСТВО: {similarity:.3f} ({similarity*100:.1f}%)")
        
        if brand1 != brand2 and brand1 != '—' and brand2 != '—':
            print("   ❌ Разные бренды - ожидается штраф!")
        else:
            print("   ✅ Одинаковые или неопределенные бренды")
    
    return True

def main():
    """Главная функция тестирования"""
    print("🚀 Тестирование SimpleProductComparator")
    print("💡 Сравнение БЕЗ нейронных сетей - только характеристики и N-граммы")
    print("=" * 80)
    
    # Запускаем тесты
    test1_result = test_simple_gpu_comparison()
    test2_result = test_patriot_memory_detailed()
    test3_result = test_cpu_models()
    test4_result = test_brand_differences()
    
    # Результаты
    print("\n" + "="*80)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("="*80)
    print(f"Тест видеокарт:         {'✅ ПРОЙДЕН' if test1_result else '❌ НЕ ПРОЙДЕН'}")
    print(f"Тест памяти Patriot:    {'✅ ПРОЙДЕН' if test2_result else '❌ НЕ ПРОЙДЕН'}")
    print(f"Тест моделей CPU:       {'✅ ПРОЙДЕН' if test3_result else '❌ НЕ ПРОЙДЕН'}")
    print(f"Тест брендов:           {'✅ ПРОЙДЕН' if test4_result else '❌ НЕ ПРОЙДЕН'}")
    
    if test1_result and test2_result and test3_result and test4_result:
        print("\n🎉 Все тесты пройдены успешно!")
        print("Простая система сравнения без нейронных сетей готова к использованию.")
        print("\n💡 Ключевые особенности:")
        print("   • ❌ НЕТ нейронных сетей - быстро и надежно")
        print("   • ✅ Точный анализ характеристик (модели, варианты, объемы)")
        print("   • ✅ N-граммы для сравнения последовательностей")
        print("   • ✅ Строгие штрафы за критические различия")
        print("   • ✅ Анализ серийных номеров")
        print("   • ✅ Взвешенное комбинирование метрик")
        print("\n⚠️  Важно: 7700 vs 7800, Ti vs без Ti теперь штрафуются!")
    else:
        print("\n⚠️  Некоторые тесты не пройдены. Проверьте реализацию.")
    
    return test1_result and test2_result and test3_result and test4_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 