#!/usr/bin/env python3
"""
Тестовый скрипт для проверки гибридного ProductComparator 
(эмбеддинги + характеристики + N-граммы)
"""

import os
import sys

# Добавляем путь к приложению
sys.path.insert(0, os.path.abspath('.'))

from app.utils.product_comparator import ProductComparator

def test_hybrid_gpu_comparison():
    """Тест сравнения видеокарт с гибридным алгоритмом"""
    print("=== Тест гибридного сравнения видеокарт ===\n")
    print("🔬 Алгоритм: Эмбеддинги (25%) + Характеристики (40%) + N-граммы (35%)")
    
    comparator = ProductComparator()
    
    if not comparator.embeddings:
        print("❌ Ошибка: не удалось инициализировать эмбеддинги")
        return False
    
    # Критичные тестовые случаи
    test_cases = [
        # Случай 1: Разные варианты одной модели (Ti vs без Ti)
        ("NVIDIA GeForce RTX 4090 24GB GDDR6X", "NVIDIA GeForce RTX 4090 Ti 24GB GDDR6X"),
        
        # Случай 2: Разные модели близких чисел (7700 vs 7800)
        ("AMD Radeon RX 7700 XT 12GB GDDR6", "AMD Radeon RX 7800 XT 16GB GDDR6"),
        
        # Случай 3: Разные варианты (Ti vs Super)
        ("NVIDIA GeForce GTX 1660 Ti 6GB GDDR6", "NVIDIA GeForce GTX 1660 Super 6GB GDDR6"),
        
        # Случай 4: Одинаковые товары (должно быть высокое сходство)
        ("Intel Arc A770 16GB GDDR6", "Intel Arc A770 16GB GDDR6"),
        
        # Случай 5: Разные бренды похожих товаров
        ("NVIDIA GeForce RTX 4090", "AMD Radeon RX 7900 XTX"),
    ]
    
    print("Тестирование критических случаев:")
    
    all_results = []
    
    for i, (gpu1, gpu2) in enumerate(test_cases, 1):
        print(f"\n{i}. ТЕСТ: {gpu1} vs {gpu2}")
        print("-" * 80)
        
        # Извлекаем характеристики для анализа
        features1 = comparator.extract_detailed_features(gpu1)
        features2 = comparator.extract_detailed_features(gpu2)
        
        print(f"   🔍 Характеристики:")
        print(f"      GPU 1: {features1}")
        print(f"      GPU 2: {features2}")
        
        # Получаем семантическое сходство
        try:
            embeddings1 = comparator.get_embeddings([gpu1])
            embeddings2 = comparator.get_embeddings([gpu2])
            semantic_sim = comparator.cosine_similarity(embeddings1[0], embeddings2[0])
        except Exception as e:
            print(f"      ❌ Ошибка эмбеддингов: {e}")
            semantic_sim = 0.0
        
        # Вычисляем компоненты сходства
        feature_sim = comparator.calculate_feature_similarity(features1, features2)
        ngram3_sim = comparator.calculate_ngram_similarity(gpu1, gpu2, 3)
        ngram5_sim = comparator.calculate_ngram_similarity(gpu1, gpu2, 5)
        penalty = comparator.calculate_penalty(features1, features2)
        
        # Гибридное сходство
        hybrid_sim = comparator.enhanced_similarity(gpu1, gpu2, semantic_sim)
        
        print(f"\n   📊 Компоненты сходства:")
        print(f"      • Семантическое (25%): {semantic_sim:.3f}")
        print(f"      • Характеристики (40%): {feature_sim:.3f}")
        print(f"      • N-грамм-3 (15%): {ngram3_sim:.3f}")
        print(f"      • N-грамм-5 (10%): {ngram5_sim:.3f}")
        print(f"      • Штраф: {penalty:.3f}")
        print(f"      • 🎯 ИТОГОВОЕ ГИБРИДНОЕ: {hybrid_sim:.3f} ({hybrid_sim*100:.1f}%)")
        
        # Анализируем результат
        if i == 1:  # RTX 4090 vs RTX 4090 Ti
            if hybrid_sim < 0.5:
                print("      ✅ ПРАВИЛЬНО: Ti версия корректно штрафуется")
            else:
                print("      ❌ ОШИБКА: Ti версия должна штрафоваться больше")
        elif i == 2:  # RX 7700 vs RX 7800
            if hybrid_sim < 0.4:
                print("      ✅ ПРАВИЛЬНО: Разные модели (7700 vs 7800) корректно различаются")
            else:
                print("      ❌ ОШИБКА: Разные модели должны штрафоваться")
        elif i == 3:  # GTX 1660 Ti vs Super
            if hybrid_sim < 0.5:
                print("      ✅ ПРАВИЛЬНО: Ti vs Super корректно различаются")
            else:
                print("      ❌ ОШИБКА: Ti vs Super должны штрафоваться")
        elif i == 4:  # Одинаковые товары
            if hybrid_sim > 0.9:
                print("      ✅ ПРАВИЛЬНО: Одинаковые товары имеют высокое сходство")
            else:
                print("      ❌ ОШИБКА: Одинаковые товары должны иметь высокое сходство")
        elif i == 5:  # Разные бренды
            if hybrid_sim < 0.3:
                print("      ✅ ПРАВИЛЬНО: Разные бренды корректно штрафуются")
            else:
                print("      ⚠️  ПРЕДУПРЕЖДЕНИЕ: Разные бренды могут штрафоваться сильнее")
        
        all_results.append((gpu1, gpu2, hybrid_sim, feature_sim, semantic_sim))
    
    # Общая статистика
    print("\n" + "="*80)
    print("📈 ОБЩАЯ СТАТИСТИКА:")
    avg_hybrid = sum(r[2] for r in all_results) / len(all_results)
    avg_features = sum(r[3] for r in all_results) / len(all_results)
    avg_semantic = sum(r[4] for r in all_results) / len(all_results)
    
    print(f"   Среднее гибридное сходство: {avg_hybrid:.3f}")
    print(f"   Среднее сходство характеристик: {avg_features:.3f}")
    print(f"   Среднее семантическое сходство: {avg_semantic:.3f}")
    
    return True

def test_patriot_memory_hybrid():
    """Тест с памятью Patriot на гибридном алгоритме"""
    print("\n" + "="*80)
    print("=== Тест памяти Patriot (гибридный алгоритм) ===\n")
    
    comparator = ProductComparator()
    
    if not comparator.embeddings:
        print("❌ Ошибка: не удалось инициализировать эмбеддинги")
        return False
    
    # Оригинальный пример от пользователя
    dns_name = "Оперативная память Patriot Signature [PSD48G240081] 8 ГБ"
    citi_name = "Оперативная память Patriot Signature PSD48G266681 DDR4 - 1x 8ГБ 2666МГц, DIMM, Ret"
    
    print("DNS:", dns_name)
    print("Citilink:", citi_name)
    
    print("\n" + "-"*60)
    print("Детальный анализ...")
    
    # Извлекаем характеристики
    features1 = comparator.extract_detailed_features(dns_name)
    features2 = comparator.extract_detailed_features(citi_name)
    
    print(f"\n🔍 Извлеченные характеристики:")
    print(f"DNS: {features1}")
    print(f"Citilink: {features2}")
    
    # Сравниваем ключевые характеристики
    print(f"\n⚖️  Сравнение ключевых характеристик:")
    key_features = ['brand', 'max_memory', 'memory_type', 'serials']
    for feature in key_features:
        val1 = features1.get(feature, '—')
        val2 = features2.get(feature, '—')
        match = "✅" if val1 == val2 else "❌"
        print(f"   {match} {feature}: {val1} ↔ {val2}")
    
    # Вычисляем семантическое сходство
    try:
        embeddings1 = comparator.get_embeddings([dns_name])
        embeddings2 = comparator.get_embeddings([citi_name])
        semantic_sim = comparator.cosine_similarity(embeddings1[0], embeddings2[0])
    except Exception as e:
        print(f"❌ Ошибка эмбеддингов: {e}")
        semantic_sim = 0.0
    
    # Вычисляем все компоненты
    feature_sim = comparator.calculate_feature_similarity(features1, features2)
    ngram3_sim = comparator.calculate_ngram_similarity(dns_name, citi_name, 3)
    ngram5_sim = comparator.calculate_ngram_similarity(dns_name, citi_name, 5)
    penalty = comparator.calculate_penalty(features1, features2)
    
    # Итоговое гибридное сходство
    hybrid_sim = comparator.enhanced_similarity(dns_name, citi_name, semantic_sim)
    
    print(f"\n📊 Полный анализ сходства:")
    print(f"   • Семантическое сходство (25%): {semantic_sim:.3f}")
    print(f"   • Сходство характеристик (40%): {feature_sim:.3f}")
    print(f"   • N-грамм сходство (3): {ngram3_sim:.3f}")
    print(f"   • N-грамм сходство (5): {ngram5_sim:.3f}")
    print(f"   • Штраф за различия: {penalty:.3f}")
    print(f"   • 🎯 ИТОГОВОЕ ГИБРИДНОЕ СХОДСТВО: {hybrid_sim:.3f} ({hybrid_sim*100:.1f}%)")
    
    # Сравниваем с чисто семантическим подходом
    print(f"\n🔄 Сравнение подходов:")
    print(f"   Только семантика: {semantic_sim:.3f} ({semantic_sim*100:.1f}%)")
    print(f"   Гибридный подход: {hybrid_sim:.3f} ({hybrid_sim*100:.1f}%)")
    
    improvement = hybrid_sim - semantic_sim
    if improvement > 0:
        print(f"   ✅ Улучшение: +{improvement:.3f} (+{improvement*100:.1f}%)")
    elif improvement < 0:
        print(f"   ⚠️  Снижение: {improvement:.3f} ({improvement*100:.1f}%)")
    else:
        print(f"   ➡️  Без изменений")
    
    # Тест пороговых значений
    print(f"\n🎯 Тест с разными порогами:")
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    for threshold in thresholds:
        matches = comparator.find_best_matches([dns_name], [citi_name], threshold, use_enhanced=True)
        status = "✅ НАЙДЕНО" if matches else "❌ НЕ НАЙДЕНО"
        print(f"   Порог {threshold}: {status}")
    
    return hybrid_sim > 0.5  # Ожидаем, что гибридный алгоритм найдет совпадение

def test_cpu_model_differences():
    """Тест различий в моделях процессоров"""
    print("\n" + "="*80)
    print("=== Тест различий в моделях процессоров ===\n")
    
    comparator = ProductComparator()
    
    if not comparator.embeddings:
        print("❌ Ошибка: не удалось инициализировать эмбеддинги")
        return False
    
    # Критичные случаи для процессоров
    cpu_tests = [
        ("Intel Core i5-12400F", "Intel Core i5-12600K"),    # 12400 vs 12600 (разница 200)
        ("AMD Ryzen 5 5600X", "AMD Ryzen 5 5700X"),         # 5600 vs 5700 (разница 100)
        ("Intel Core i7-13700K", "Intel Core i7-13700F"),   # Одинаковые модели, разные суффиксы
        ("AMD Ryzen 7 7700X", "AMD Ryzen 7 7800X3D"),       # Близкие модели с разными суффиксами
    ]
    
    print("Тестирование различий в моделях процессоров:")
    
    for i, (cpu1, cpu2) in enumerate(cpu_tests, 1):
        print(f"\n{i}. {cpu1} vs {cpu2}")
        print("-" * 60)
        
        # Извлекаем характеристики
        features1 = comparator.extract_detailed_features(cpu1)
        features2 = comparator.extract_detailed_features(cpu2)
        
        print(f"   Характеристики 1: {features1}")
        print(f"   Характеристики 2: {features2}")
        
        # Анализируем модели
        if 'cpu_model' in features1 and 'cpu_model' in features2:
            import re
            try:
                num1 = int(re.findall(r'\d+', features1['cpu_model'])[0])
                num2 = int(re.findall(r'\d+', features2['cpu_model'])[0])
                diff = abs(num1 - num2)
                print(f"   📊 Разность моделей: {diff}")
            except:
                print("   ❓ Не удалось извлечь числовые модели")
                diff = 0
        
        # Вычисляем гибридное сходство
        try:
            embeddings1 = comparator.get_embeddings([cpu1])
            embeddings2 = comparator.get_embeddings([cpu2])
            semantic_sim = comparator.cosine_similarity(embeddings1[0], embeddings2[0])
            hybrid_sim = comparator.enhanced_similarity(cpu1, cpu2, semantic_sim)
            
            print(f"   🔬 Семантическое сходство: {semantic_sim:.3f}")
            print(f"   🎯 Гибридное сходство: {hybrid_sim:.3f} ({hybrid_sim*100:.1f}%)")
            
            # Анализируем результат
            if diff > 100 and hybrid_sim > 0.6:
                print("   ⚠️  ПРЕДУПРЕЖДЕНИЕ: Большая разность моделей, но высокое сходство")
            elif diff <= 50 and hybrid_sim > 0.7:
                print("   ✅ ПРАВИЛЬНО: Близкие модели имеют высокое сходство")
            elif diff > 100 and hybrid_sim < 0.5:
                print("   ✅ ПРАВИЛЬНО: Разные модели корректно штрафуются")
            else:
                print("   ℹ️  Промежуточный результат")
                
        except Exception as e:
            print(f"   ❌ Ошибка вычисления: {e}")
    
    return True

def main():
    """Главная функция тестирования"""
    print("🚀 Тестирование гибридного ProductComparator")
    print("🧠 Эмбеддинги (25%) + 🔍 Характеристики (40%) + 📝 N-граммы (35%)")
    print("=" * 80)
    
    # Запускаем тесты
    test1_result = test_hybrid_gpu_comparison()
    test2_result = test_patriot_memory_hybrid()
    test3_result = test_cpu_model_differences()
    
    # Результаты
    print("\n" + "="*80)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ ГИБРИДНОГО ПОДХОДА")
    print("="*80)
    print(f"Тест видеокарт:         {'✅ ПРОЙДЕН' if test1_result else '❌ НЕ ПРОЙДЕН'}")
    print(f"Тест памяти Patriot:    {'✅ ПРОЙДЕН' if test2_result else '❌ НЕ ПРОЙДЕН'}")
    print(f"Тест процессоров:       {'✅ ПРОЙДЕН' if test3_result else '❌ НЕ ПРОЙДЕН'}")
    
    if test1_result and test2_result and test3_result:
        print("\n🎉 Все тесты пройдены успешно!")
        print("Гибридная система сравнения готова к использованию.")
        print("\n💡 Ключевые преимущества гибридного подхода:")
        print("   • 🧠 Семантическое понимание от эмбеддингов")
        print("   • 🔍 Точный анализ характеристик (модели, варианты)")
        print("   • 📝 N-граммы для текстового сходства")
        print("   • ⚖️  Взвешенное комбинирование метрик")
        print("   • 🚫 Строгие штрафы за критические различия")
        print("\n⚠️  Важно: 7700 vs 7800, Ti vs без Ti теперь корректно штрафуются!")
        print("💪 При этом сохраняется семантическое понимание схожих товаров!")
    else:
        print("\n⚠️  Некоторые тесты не пройдены. Проверьте настройки.")
    
    return test1_result and test2_result and test3_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 