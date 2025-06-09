#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки работы ProductComparator с GigaChat
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.product_comparator import ProductComparator

def test_gigachat_embeddings():
    """Тестирование GigaChat embeddings"""
    print("=== Тестирование GigaChat Embeddings ===")
    
    try:
        # Создаем компаратор
        comparator = ProductComparator()
        
        if comparator.embeddings is None:
            print("❌ GigaChat недоступен - тест пропущен")
            return False
        
        # Тестовые тексты
        test_texts = [
            "Память Kingston ValueRAM 8GB DDR4-2666",
            "Оперативная память Kingston 8 ГБ DDR4 2666 МГц", 
            "Видеокарта NVIDIA GeForce RTX 4090"
        ]
        
        print(f"Получение эмбеддингов для {len(test_texts)} текстов...")
        embeddings = comparator.get_embeddings(test_texts)
        
        print(f"✅ Эмбеддинги получены успешно!")
        print(f"   Количество: {len(embeddings)}")
        print(f"   Размер эмбеддинга: {len(embeddings[0])}")
        
        # Тестируем сходство
        similarity = comparator.cosine_similarity(embeddings[0], embeddings[1])
        print(f"   Сходство Kingston память: {similarity:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_product_matching():
    """Тестирование сопоставления товаров"""
    print("\n=== Тестирование сопоставления товаров ===")
    
    try:
        comparator = ProductComparator()
        
        # Тестовые списки товаров
        dns_products = [
            "Память Kingston ValueRAM 8GB DDR4-2666 CL19 [KVR26N19S8/8]",
            "Память Corsair Vengeance LPX 16GB DDR4-3200 CL16 [CMK16GX4M1E3200C16]"
        ]
        
        citi_products = [
            "Оперативная память Kingston ValueRAM 8 ГБ DDR4 2666 МГц [KVR26N19S8/8]",
            "Модуль памяти Corsair Vengeance LPX 16GB DDR4 3200MHz CL16",
            "Память ADATA XPG Spectrix D41 RGB 16GB DDR4-3000 CL16"
        ]
        
        print(f"DNS товары: {len(dns_products)}")
        print(f"Citilink товары: {len(citi_products)}")
        
        # Поиск совпадений
        matches = comparator.find_best_matches(
            dns_products, 
            citi_products, 
            threshold=0.5
        )
        
        print(f"\n✅ Найдено совпадений: {len(matches)}")
        
        for i, (dns_name, citi_name, similarity) in enumerate(matches, 1):
            print(f"\n{i}. Совпадение (сходство: {similarity:.3f}):")
            print(f"   DNS: {dns_name}")
            print(f"   Citi: {citi_name}")
            
            # Анализ характеристик
            dns_features = comparator.extract_detailed_features(dns_name)
            citi_features = comparator.extract_detailed_features(citi_name)
            feature_sim = comparator.calculate_feature_similarity(dns_features, citi_features)
            
            print(f"   Сходство характеристик: {feature_sim:.3f}")
            print(f"   DNS характеристики: {dns_features}")
            print(f"   Citi характеристики: {citi_features}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Тестирование ProductComparator с GigaChat")
    print("=" * 50)
    
    success = True
    
    # Тест 1: GigaChat embeddings
    success &= test_gigachat_embeddings()
    
    # Тест 2: Сопоставление товаров
    success &= test_product_matching()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Все тесты прошли успешно!")
    else:
        print("❌ Некоторые тесты завершились с ошибкой") 