import re
import json
import os
import logging
from typing import List, Dict, Tuple
import numpy as np
from langchain_gigachat import GigaChatEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='ram_price_comparison.log'
)
logger = logging.getLogger(__name__)

def normalize_product_name(name: str) -> str:
    """
    Нормализация названия товара для лучшего сравнения
    """
    # Приводим к нижнему регистру
    normalized = name.lower()
    
    # Удаляем лишние пробелы и специальные символы
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    
    # Стандартизируем обозначения памяти
    normalized = re.sub(r'\b8\s*гб\b|\b8\s*gb\b', '8gb', normalized)
    normalized = re.sub(r'\b16\s*гб\b|\b16\s*gb\b', '16gb', normalized)
    normalized = re.sub(r'\b32\s*гб\b|\b32\s*gb\b', '32gb', normalized)
    
    # Стандартизируем частоты
    normalized = re.sub(r'\b2400\s*мгц\b|\b2400\s*mhz\b', '2400mhz', normalized)
    normalized = re.sub(r'\b2666\s*мгц\b|\b2666\s*mhz\b', '2666mhz', normalized)
    normalized = re.sub(r'\b3200\s*мгц\b|\b3200\s*mhz\b', '3200mhz', normalized)
    
    # Удаляем общие слова
    words_to_remove = ['оперативная', 'память', 'модуль', 'dimm', 'ret', 'ddr4', 'ddr3']
    for word in words_to_remove:
        normalized = re.sub(r'\b' + word + r'\b', '', normalized)
    
    # Убираем лишние пробелы
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized

def extract_key_features(name: str) -> Dict[str, str]:
    """
    Извлечение ключевых характеристик из названия товара
    """
    features = {}
    
    # Извлекаем бренд
    brands = ['patriot', 'kingston', 'corsair', 'crucial', 'samsung', 'hynix', 'gskill', 'adata']
    for brand in brands:
        if brand in name.lower():
            features['brand'] = brand
            break
    
    # Извлекаем объем памяти
    memory_match = re.search(r'(\d+)\s*(?:гб|gb)', name.lower())
    if memory_match:
        features['capacity'] = memory_match.group(1) + 'gb'
    
    # Извлекаем частоту
    freq_match = re.search(r'(\d{4})\s*(?:мгц|mhz)', name.lower())
    if freq_match:
        features['frequency'] = freq_match.group(1) + 'mhz'
    
    # Извлекаем модель/серию
    model_patterns = [
        r'signature\s*(\w+)',
        r'fury\s*(\w+)',
        r'vengeance\s*(\w+)',
        r'ripjaws\s*(\w+)'
    ]
    
    for pattern in model_patterns:
        match = re.search(pattern, name.lower())
        if match:
            features['series'] = match.group(0)
            break
    
    return features

def calculate_feature_similarity(features1: Dict, features2: Dict) -> float:
    """
    Вычисление сходства на основе ключевых характеристик
    """
    score = 0.0
    total_weight = 0.0
    
    # Веса для различных характеристик
    weights = {
        'brand': 0.3,
        'capacity': 0.4,
        'frequency': 0.2,
        'series': 0.1
    }
    
    for feature, weight in weights.items():
        if feature in features1 and feature in features2:
            if features1[feature] == features2[feature]:
                score += weight
        total_weight += weight
    
    return score / total_weight if total_weight > 0 else 0.0

def create_enhanced_description(item: Dict) -> str:
    """
    Создание улучшенного описания товара для эмбеддингов
    """
    name = item.get('name', '')
    brand = item.get('brand_name', '')
    
    # Нормализуем название
    normalized_name = normalize_product_name(name)
    
    # Извлекаем ключевые характеристики
    features = extract_key_features(name)
    
    # Создаем структурированное описание
    description_parts = []
    
    if brand:
        description_parts.append(f"бренд {brand.lower()}")
    
    if 'capacity' in features:
        description_parts.append(f"память {features['capacity']}")
    
    if 'frequency' in features:
        description_parts.append(f"частота {features['frequency']}")
    
    if 'series' in features:
        description_parts.append(f"серия {features['series']}")
    
    # Добавляем нормализованное название
    description_parts.append(normalized_name)
    
    return ' '.join(description_parts)

def find_similar_products_simple(dns_data: List[Dict], citilink_data: List[Dict], 
                               threshold: float = 0.4, max_dns_items: int = 50, 
                               max_citilink_items: int = 100) -> List[Tuple]:
    """
    Простой поиск похожих товаров с ограничением количества
    """
    if not dns_data or not citilink_data:
        logger.error("Не удалось загрузить данные из одного или обоих источников")
        return []
    
    # Ограничиваем количество товаров для обработки
    dns_data_limited = dns_data[:max_dns_items]
    citilink_data_limited = citilink_data[:max_citilink_items]
    
    print(f"Обрабатываем {len(dns_data_limited)} товаров DNS и {len(citilink_data_limited)} товаров Citilink")
    
    # Настройка эмбеддингов
    os.environ["GIGACHAT_CREDENTIALS"] = "MjZjYjAwNzUtZTllZS00YjkxLWJlOGEtYjk5N2FjMzA3ZjBmOjc2OTg3Y2IzLTFkZGYtNDI3NC05ZTNiLTc0ZjQ0OGM3MDQxZQ=="
    os.environ["GIGACHAT_SCOPE"] = "GIGACHAT_API_PERS"
    
    embeddings_model = GigaChatEmbeddings(
        credentials=os.environ["GIGACHAT_CREDENTIALS"],
        scope=os.environ["GIGACHAT_SCOPE"],
        verify_ssl_certs=False
    )
    
    # Подготовка документов без сложных метаданных
    dns_documents = []
    dns_items_map = {}
    
    print("Обработка товаров DNS...")
    for item in dns_data_limited:
        # Используем только название и бренд
        name = item.get('name', '')
        brand = item.get('brand_name', '')
        description = f"{name} {brand}".strip()
        
        item_id = str(id(item))
        dns_items_map[item_id] = item
        
        dns_documents.append(Document(
            page_content=description,
            metadata={
                "id": item_id,
                "name": name[:100]  # Ограничиваем длину для метаданных
            }
        ))
    
    citilink_documents = []
    citilink_items_map = {}
    
    print("Обработка товаров Citilink...")
    for item in citilink_data_limited:
        name = item.get('name', '')
        description = name.strip()
        
        item_id = str(id(item))
        citilink_items_map[item_id] = item
        
        citilink_documents.append(Document(
            page_content=description,
            metadata={
                "id": item_id,
                "name": name[:100]  # Ограничиваем длину для метаданных
            }
        ))
    
    print("Создание векторного хранилища...")
    dns_vectorstore = Chroma.from_documents(
        documents=dns_documents,
        embedding=embeddings_model,
        collection_name="dns_products_simple"
    )
    
    similar_pairs = []
    print("Поиск похожих товаров...")
    
    for i, citilink_doc in enumerate(citilink_documents):
        try:
            # Ищем похожие товары
            similar_docs = dns_vectorstore.similarity_search_with_score(
                citilink_doc.page_content,
                k=5
            )
            
            for dns_doc, distance in similar_docs:
                # Преобразуем расстояние в сходство
                similarity = 1 / (1 + distance)
                
                if similarity > threshold:
                    dns_item = dns_items_map.get(dns_doc.metadata.get("id"))
                    citilink_item = citilink_items_map.get(citilink_doc.metadata.get("id"))
                    
                    if dns_item and citilink_item:
                        similar_pairs.append((dns_item, citilink_item, similarity))
                        
        except Exception as e:
            print(f"Ошибка при обработке товара {i}: {e}")
            continue
    
    # Удаляем дубликаты и сортируем
    unique_pairs = {}
    for dns_item, citilink_item, similarity in similar_pairs:
        key = (dns_item.get('name', ''), citilink_item.get('name', ''))
        if key not in unique_pairs or unique_pairs[key][2] < similarity:
            unique_pairs[key] = (dns_item, citilink_item, similarity)
    
    result = list(unique_pairs.values())
    result.sort(key=lambda x: x[2], reverse=True)
    
    return result

def load_dns_ram_data():
    """Загрузка данных об оперативной памяти из DNS"""
    try:
        file_path = os.path.join('app', 'utils', 'DNS_parsing', 'categories',
                                 'product_data_Оперативная память DIMM.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Ошибка загрузки данных DNS: {e}")
        return []

def load_citilink_ram_data():
    """Загрузка данных об оперативной памяти из Citilink"""
    try:
        file_path = os.path.join('app', 'utils', 'Citi_parser', 'data', 'moduli-pamyati', 'Товары.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Ошибка загрузки данных Citilink: {e}")
        return []

def simple_embedding_comparison():
    """Простой режим сравнения товаров с ограничениями"""
    print("\n=== Простое сравнение товаров с ограничениями ===\n")

    # Загрузка данных
    dns_data = load_dns_ram_data()
    citilink_data = load_citilink_ram_data()

    if not dns_data or not citilink_data:
        print("Ошибка: Не удалось загрузить данные из одного или обоих источников")
        return

    print(f"Всего загружено {len(dns_data)} товаров из DNS и {len(citilink_data)} товаров из Citilink")
    
    print("Поиск похожих товаров (ограничено первыми 50 DNS и 100 Citilink товарами)...")
    similar_pairs = find_similar_products_simple(
        dns_data, citilink_data, 
        threshold=0.4, 
        max_dns_items=50, 
        max_citilink_items=100
    )
    
    if not similar_pairs:
        print("Не найдено похожих товаров")
        return
    
    print(f"\nНайдено {len(similar_pairs)} пар похожих товаров")
    
    for i, (dns_item, citilink_item, similarity) in enumerate(similar_pairs[:15], 1):
        dns_price = dns_item.get('price_original', 'Нет данных')
        citilink_price = citilink_item.get('price', 'Нет данных')
        
        print(f"\n{i}. Сходство: {similarity:.4f}")
        print(f"DNS: {dns_item['name']} - {dns_price} руб.")
        print(f"Citilink: {citilink_item['name']} - {citilink_price} руб.")
    
    # Сохраняем результаты
    results = {
        "total_pairs": len(similar_pairs),
        "pairs": [
            {
                "similarity": similarity,
                "dns_item": {
                    "name": dns_item["name"],
                    "price": dns_item.get("price_original", "Нет данных"),
                    "url": dns_item.get("url", "")
                },
                "citilink_item": {
                    "name": citilink_item["name"],
                    "price": citilink_item.get("price", "Нет данных"),
                    "url": citilink_item.get("url", "")
                }
            }
            for dns_item, citilink_item, similarity in similar_pairs
        ]
    }
    
    with open('simple_comparison_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nРезультаты сохранены в файл simple_comparison_results.json")

# Запуск простого сравнения
if __name__ == "__main__":
    simple_embedding_comparison()