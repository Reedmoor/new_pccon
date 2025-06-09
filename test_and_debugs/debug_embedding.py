#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладочный скрипт для выяснения различий в инициализации GigaChatEmbeddings
"""

import os
from langchain_gigachat.embeddings import GigaChatEmbeddings
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# Отключаем предупреждения
urllib3.disable_warnings(InsecureRequestWarning)

def test_embedding_py_method():
    """Тестирование метода из embedding.py"""
    print("=== Метод из embedding.py ===")
    
    try:
        # Настройка переменных окружения как в embedding.py
        credentials = "MjZjYjAwNzUtZTllZS00YjkxLWJlOGEtYjk5N2FjMzA3ZjBmOjQ3ZTVmZmM4LTJiZGQtNDU1OC1iNDdkLTBiZmJmZDNmNWI4Ng=="
        os.environ["GIGACHAT_CREDENTIALS"] = credentials
        os.environ["GIGACHAT_SCOPE"] = "GIGACHAT_API_PERS"
        
        # Создаем экземпляр как в embedding.py
        embeddings_model = GigaChatEmbeddings(
            credentials=credentials,
            scope="GIGACHAT_API_PERS",
            verify_ssl_certs=False
        )
        
        # Тестируем
        test_embeddings = embeddings_model.embed_documents(["Тестовый запрос"])
        print(f"✅ Успех! Размер: {len(test_embeddings[0])}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_product_comparator_method():
    """Тестирование метода из product_comparator.py"""
    print("\n=== Метод из product_comparator.py ===")
    
    try:
        # Очищаем переменные окружения
        if "GIGACHAT_CREDENTIALS" in os.environ:
            del os.environ["GIGACHAT_CREDENTIALS"]
        if "GIGACHAT_SCOPE" in os.environ:
            del os.environ["GIGACHAT_SCOPE"]
        
        credentials = "MjZjYjAwNzUtZTllZS00YjkxLWJlOGEtYjk5N2FjMzA3ZjBmOjQ3ZTVmZmM4LTJiZGQtNDU1OC1iNDdkLTBiZmJmZDNmNWI4Ng=="
        
        # Настройка как в обновленном product_comparator.py
        os.environ["GIGACHAT_CREDENTIALS"] = credentials
        os.environ["GIGACHAT_SCOPE"] = "GIGACHAT_API_PERS"
        
        embeddings = GigaChatEmbeddings(
            credentials=credentials,
            scope="GIGACHAT_API_PERS", 
            verify_ssl_certs=False
        )
        
        # Тестируем
        test_embeddings = embeddings.embed_documents(["Тестовый запрос"])
        print(f"✅ Успех! Размер: {len(test_embeddings[0])}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_minimal_init():
    """Минимальная инициализация только с credentials"""
    print("\n=== Минимальная инициализация ===")
    
    try:
        credentials = "MjZjYjAwNzUtZTllZS00YjkxLWJlOGEtYjk5N2FjMzA3ZjBmOjQ3ZTVmZmM4LTJiZGQtNDU1OC1iNDdkLTBiZmJmZDNmNWI4Ng=="
        
        embeddings = GigaChatEmbeddings(
            credentials=credentials,
            verify_ssl_certs=False
        )
        
        # Тестируем
        test_embeddings = embeddings.embed_documents(["Тестовый запрос"])
        print(f"✅ Успех! Размер: {len(test_embeddings[0])}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_from_env():
    """Инициализация только из переменных окружения"""
    print("\n=== Инициализация из переменных окружения ===")
    
    try:
        credentials = "MjZjYjAwNzUtZTllZS00YjkxLWJlOGEtYjk5N2FjMzA3ZjBmOjQ3ZTVmZmM4LTJiZGQtNDU1OC1iNDdkLTBiZmJmZDNmNWI4Ng=="
        
        os.environ["GIGACHAT_CREDENTIALS"] = credentials
        os.environ["GIGACHAT_SCOPE"] = "GIGACHAT_API_PERS"
        
        # Без явного указания credentials
        embeddings = GigaChatEmbeddings(verify_ssl_certs=False)
        
        # Тестируем
        test_embeddings = embeddings.embed_documents(["Тестовый запрос"])
        print(f"✅ Успех! Размер: {len(test_embeddings[0])}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("Отладка инициализации GigaChatEmbeddings")
    print("=" * 50)
    
    results = []
    results.append(("embedding.py метод", test_embedding_py_method()))
    results.append(("product_comparator.py метод", test_product_comparator_method()))
    results.append(("Минимальная инициализация", test_minimal_init()))
    results.append(("Из переменных окружения", test_from_env()))
    
    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТЫ:")
    for name, success in results:
        status = "✅ РАБОТАЕТ" if success else "❌ НЕ РАБОТАЕТ"
        print(f"{name:25} {status}") 