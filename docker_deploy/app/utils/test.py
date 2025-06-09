import json
import numpy as np
import os
from langchain_gigachat.embeddings import GigaChatEmbeddings
from typing import List, Dict, Tuple, Union, Any

class JSONNameComparator:
    def __init__(self, credentials: str):
        """
        Инициализация компаратора с GigaChatEmbeddings
        
        Args:
            credentials: ключ авторизации для GigaChat
        """
        self.embeddings = GigaChatEmbeddings(
            credentials=credentials, 
            verify_ssl_certs=False
        )
    
    def load_json_data(self, file_path: str) -> List[Dict]:
        """
        Загрузка данных из JSON файла
        
        Args:
            file_path: путь к JSON файлу
            
        Returns:
            список словарей из JSON
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_names(self, data: List[Dict], name_key: str = "name") -> List[str]:
        """
        Извлечение названий из данных JSON
        
        Args:
            data: список словарей
            name_key: ключ для названия (по умолчанию "name")
            
        Returns:
            список названий
        """
        names = []
        for item in data:
            if name_key in item:
                names.append(item[name_key])
        return names
    
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Получение эмбеддингов для списка текстов
        
        Args:
            texts: список текстов
            
        Returns:
            массив эмбеддингов
        """
        embeddings_result = self.embeddings.embed_documents(texts)
        return np.array(embeddings_result)
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Вычисление косинусного сходства между двумя векторами
        
        Args:
            vec1, vec2: векторы для сравнения
            
        Returns:
            значение косинусного сходства
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def find_best_matches(self, names1: List[str], names2: List[str], 
                         threshold: float = 0.7) -> List[Tuple[str, str, float]]:
        """
        Поиск наилучших совпадений между двумя списками названий
        
        Args:
            names1, names2: списки названий для сравнения
            threshold: минимальный порог сходства
            
        Returns:
            список кортежей (название1, название2, сходство)
        """
        # Получаем эмбеддинги для обеих групп названий
        embeddings1 = self.get_embeddings(names1)
        embeddings2 = self.get_embeddings(names2)
        
        matches = []
        
        # Сравниваем каждое название из первого списка с каждым из второго
        for i, name1 in enumerate(names1):
            best_similarity = 0.0
            best_match = None
            best_name2 = None
            
            for j, name2 in enumerate(names2):
                similarity = self.cosine_similarity(embeddings1[i], embeddings2[j])
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = (name1, name2, similarity)
                    best_name2 = name2
            
            # Добавляем совпадение, если оно превышает порог
            if best_match and best_similarity >= threshold:
                matches.append(best_match)
        
        return matches
    
    def compare_storage_categories(self, threshold: float = 0.7) -> Dict[str, List[Tuple[str, str, float]]]:
        """
        Сравнение категорий накопителей DNS с модулями памяти Citilink
        
        Args:
            threshold: минимальный порог сходства
            
        Returns:
            словарь с результатами сравнения по категориям
        """
        # Пути к файлам DNS
        dns_paths = {
            'SSD M.2': os.path.join(os.path.dirname(__file__), 'DNS_parsing', 'categories', 'product_data_SSD M_2 накопители.json'),
            'SSD': os.path.join(os.path.dirname(__file__), 'DNS_parsing', 'categories', 'product_data_SSD накопители.json'),
            'HDD': os.path.join(os.path.dirname(__file__), 'DNS_parsing', 'categories', 'product_data_Жесткие диски 3_5_.json')
        }
        
        # Путь к модулям памяти в Citilink
        citi_memory_path = os.path.join(os.path.dirname(__file__), 'Citi_parser', 'data', 'moduli-pamyati', 'Товары.json')
        
        # Загрузка данных
        results = {}
        
        try:
            # Загружаем данные Citilink один раз
            with open(citi_memory_path, 'r', encoding='utf-8') as f:
                citi_data = json.load(f)
            citi_names = [item.get('name', '') for item in citi_data]
            
            # Обрабатываем каждую категорию DNS
            for category, path in dns_paths.items():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        dns_data = json.load(f)
                    
                    print(f"\n{'='*50}")
                    print(f"Обработка категории: {category}")
                    print(f"Загружено {len(dns_data)} товаров из DNS")
                    print(f"Загружено {len(citi_data)} товаров из Citilink")
                    
                    # Извлекаем названия товаров
                    dns_names = [item.get('name', '') for item in dns_data]
                    
                    # Находим совпадения
                    matches = self.find_best_matches(dns_names, citi_names, threshold)
                    
                    # Сохраняем результаты
                    results[category] = matches
                    
                    # Выводим статистику
                    print(f"Найдено {len(matches)} совпадений (порог: {threshold})")
                    
                    # Выводим примеры совпадений (первые 3)
                    if matches:
                        print("\nПримеры совпадений:")
                        for name1, name2, similarity in matches[:3]:
                            print(f"- '{name1}' ↔ '{name2}' (сходство: {similarity:.4f})")
                    
                except Exception as e:
                    print(f"Ошибка при обработке категории {category}: {str(e)}")
                    results[category] = []
            
            return results
            
        except Exception as e:
            print(f"Критическая ошибка при загрузке данных: {str(e)}")
            return {}
    
    def compare_json_files(self, file1_path: str, file2_path: str, 
                          name_key: str = "name", threshold: float = 0.7) -> List[Tuple[str, str, float]]:
        """
        Сравнение названий из двух JSON файлов
        
        Args:
            file1_path, file2_path: пути к JSON файлам
            name_key: ключ для названия в JSON
            threshold: минимальный порог сходства
            
        Returns:
            список совпадений
        """
        # Загружаем данные из файлов
        data1 = self.load_json_data(file1_path)
        data2 = self.load_json_data(file2_path)
        
        # Извлекаем названия
        names1 = self.extract_names(data1, name_key)
        names2 = self.extract_names(data2, name_key)
        
        print(f"Найдено {len(names1)} названий в первом файле")
        print(f"Найдено {len(names2)} названий во втором файле")
        
        # Находим совпадения
        matches = self.find_best_matches(names1, names2, threshold)
        
        return matches

# Пример использования
def get_user_category_choice(dns_categories_map, citi_categories_map):
    print("\nВыберите категорию из DNS:")
    for i, name in enumerate(dns_categories_map.keys()):
        print(f"{i+1}. {name}")
    while True:
        try:
            dns_choice_idx = int(input(f"Введите номер (1-{len(dns_categories_map)}): ")) - 1
            if 0 <= dns_choice_idx < len(dns_categories_map):
                dns_selected_category_name = list(dns_categories_map.keys())[dns_choice_idx]
                dns_file_name = dns_categories_map[dns_selected_category_name]
                break
            else:
                print("Неверный номер. Попробуйте снова.")
        except ValueError:
            print("Пожалуйста, введите число.")

    print("\nВыберите категорию из Citilink:")
    for i, name in enumerate(citi_categories_map.keys()):
        print(f"{i+1}. {name}")
    while True:
        try:
            citi_choice_idx = int(input(f"Введите номер (1-{len(citi_categories_map)}): ")) - 1
            if 0 <= citi_choice_idx < len(citi_categories_map):
                citi_selected_category_name = list(citi_categories_map.keys())[citi_choice_idx]
                citi_folder_name = citi_categories_map[citi_selected_category_name]
                break
            else:
                print("Неверный номер. Попробуйте снова.")
        except ValueError:
            print("Пожалуйста, введите число.")
            
    dns_file_path = os.path.join(os.path.dirname(__file__), 'DNS_parsing', 'categories', dns_file_name)
    citi_file_path = os.path.join(os.path.dirname(__file__), 'Citi_parser', 'data', citi_folder_name, 'Товары.json')
    
    return dns_file_path, citi_file_path, dns_selected_category_name, citi_selected_category_name

if __name__ == "__main__":
    credentials = "MjZjYjAwNzUtZTllZS00YjkxLWJlOGEtYjk5N2FjMzA3ZjBmOjc2OTg3Y2IzLTFkZGYtNDI3NC05ZTNiLTc0ZjQ0OGM3MDQxZQ=="
    comparator = JSONNameComparator(credentials)

    # Определение доступных категорий
    dns_categories_map = {
        "SSD M_2 накопители": "product_data_SSD M_2 накопители.json",
        "SSD накопители": "product_data_SSD накопители.json",
        "Видеокарты": "product_data_Видеокарты.json",
        "Жесткие диски 3_5_": "product_data_Жесткие диски 3_5_.json",
        "Кулеры для процессоров": "product_data_Кулеры для процессоров.json",
        "Оперативная память DIMM": "product_data_Оперативная память DIMM.json",
        "Процессоры": "product_data_Процессоры.json"
    }

    citi_categories_map = {
        "Блоки питания": "bloki-pitaniya",
        "Корпуса": "korpusa",
        "Материнские платы": "materinskie-platy",
        "Модули памяти": "moduli-pamyati",
        "Процессоры": "processory",
        "Вентиляторы для корпуса": "ventilyatory-dlya-korpusa",
        "Видеокарты": "videokarty",
        "Жесткие диски": "zhestkie-diski"
    }

    dns_file, citi_file, dns_cat_name, citi_cat_name = get_user_category_choice(dns_categories_map, citi_categories_map)

    print(f"\nСравнение: '{dns_cat_name}' (DNS) vs '{citi_cat_name}' (Citilink)")
    try:
        matches = comparator.compare_json_files(dns_file, citi_file, threshold=0.6)
        
        if matches:
            print("\nНайденные совпадения:")
            print("-" * 80)
            for name1, name2, similarity in matches:
                print(f"'{name1}' ({dns_cat_name}) ↔ '{name2}' ({citi_cat_name})")
                print(f"Сходство: {similarity:.4f}")
                print("-" * 80)
        else:
            print("Совпадений не найдено.")
            
    except FileNotFoundError as e:
        print(f"Ошибка: Файл не найден. Убедитесь, что пути к файлам верны: {e}")
    except Exception as e:
        print(f"Произошла ошибка при сравнении: {e}")