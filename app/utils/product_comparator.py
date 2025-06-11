import json
import numpy as np
import os
import re
try:
    from langchain_gigachat.embeddings import GigaChatEmbeddings
    GIGACHAT_AVAILABLE = True
except ImportError:
    GigaChatEmbeddings = None
    GIGACHAT_AVAILABLE = False
    print("Предупреждение: langchain_gigachat не установлен. Функция сравнения будет работать только на основе характеристик.")
from typing import List, Dict, Tuple, Set
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductComparator:
    def __init__(self, credentials: str = None):
        """
        Инициализация компаратора с GigaChatEmbeddings и анализом характеристик
        
        Args:
            credentials: ключ авторизации для GigaChat
        """
        if not credentials:
            credentials = os.environ.get("GIGACHAT_CREDENTIALS", "MjZjYjAwNzUtZTllZS00YjkxLWJlOGEtYjk5N2FjMzA3ZjBmOjQ3ZTVmZmM4LTJiZGQtNDU1OC1iNDdkLTBiZmJmZDNmNWI4Ng==")
        
        # Инициализация кэша для embeddings
        self.embeddings_cache = {}
        
        # Настройка переменных окружения для GigaChat (как в рабочем embedding.py)
        os.environ["GIGACHAT_CREDENTIALS"] = credentials
        os.environ["GIGACHAT_SCOPE"] = "GIGACHAT_API_PERS"
        
        if GIGACHAT_AVAILABLE:
            try:
                self.embeddings = GigaChatEmbeddings(
                    credentials=credentials,
                    scope="GIGACHAT_API_PERS", 
                    verify_ssl_certs=False
                )
                logger.info("GigaChatEmbeddings инициализирован успешно")
            except Exception as e:
                logger.error(f"Ошибка инициализации GigaChatEmbeddings: {e}")
                self.embeddings = None
        else:
            logger.warning("GigaChat недоступен - используется только сравнение характеристик")
            self.embeddings = None
    
    def load_json_data(self, file_path: str) -> List[Dict]:
        """
        Загрузка данных из JSON файла
        
        Args:
            file_path: путь к JSON файлу
            
        Returns:
            список словарей из JSON
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки данных из {file_path}: {e}")
            return []
    
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
    
    def extract_detailed_features(self, name: str) -> Dict[str, any]:
        """
        Извлечение детальных характеристик из названия товара
        
        Args:
            name: название товара
            
        Returns:
            словарь с характеристиками
        """
        name_lower = name.lower()
        features = {}
        
        # Извлекаем бренд (расширенный список)
        brands = [
            'nvidia', 'amd', 'intel', 'asus', 'msi', 'gigabyte', 'evga', 'zotac', 
            'palit', 'gainward', 'powercolor', 'sapphire', 'corsair', 'gskill', 
            'kingston', 'crucial', 'patriot', 'hyperx', 'adata', 'samsung',
            'western digital', 'wd', 'seagate', 'toshiba', 'transcend', 'pny',
            'team', 'goodram', 'aorus', 'inno3d', 'galax', 'kfa2'
        ]
        for brand in brands:
            if brand in name_lower:
                features['brand'] = brand
                break
        
        # Извлекаем модели видеокарт
        gpu_patterns = [
            r'rtx\s*(\d{4})\s*(ti|super)?',      # RTX 4090, RTX 4090 Ti
            r'gtx\s*(\d{4})\s*(ti|super)?',      # GTX 1660 Ti
            r'rx\s*(\d{4})\s*(xt|pro|xtx)?',     # RX 7800 XT, RX 7900 XTX
            r'arc\s*([a-z]\d+)',                 # Intel Arc A770
            r'radeon\s*(\d{4})',                 # Radeon 7800
            r'geforce\s*(\d{4})',                # GeForce 1660
        ]
        
        for pattern in gpu_patterns:
            match = re.search(pattern, name_lower)
            if match:
                features['gpu_model'] = match.group(1)
                if len(match.groups()) > 1 and match.group(2):
                    features['gpu_variant'] = match.group(2)
                break
        
        # Извлекаем модели процессоров
        cpu_patterns = [
            r'i(\d)-(\d{4,5})[a-z]*',            # i5-12400, i7-13700K
            r'ryzen\s*(\d)\s*(\d{4})[a-z]*',     # Ryzen 5 5600X
            r'(\d{4,5})[a-z]*\s*(?:cpu|процессор)', # 12400 CPU
            r'core\s*(\d{4,5})[a-z]*',           # Core 12400
        ]
        
        for pattern in cpu_patterns:
            match = re.search(pattern, name_lower)
            if match:
                if 'i\\d' in pattern:
                    features['cpu_series'] = f"i{match.group(1)}"
                    features['cpu_model'] = match.group(2)
                elif 'ryzen' in pattern:
                    features['cpu_series'] = f"ryzen{match.group(1)}"
                    features['cpu_model'] = match.group(2)
                else:
                    features['cpu_model'] = match.group(1)
                break
        
        # Извлекаем объем памяти (более точные паттерны)
        memory_patterns = [
            r'(\d+)\s*(?:gb|гб)(?:\s|$)',
            r'(\d+)\s*(?:tb|тб)(?:\s|$)',
            r'(\d+)gb',
            r'(\d+)гб',
        ]
        
        memory_sizes = []
        for pattern in memory_patterns:
            matches = re.findall(pattern, name_lower)
            if matches:
                memory_sizes.extend([int(m) for m in matches])
        
        if memory_sizes:
            features['memory_sizes'] = list(set(memory_sizes))  # Убираем дубликаты
            features['max_memory'] = max(memory_sizes)
            features['min_memory'] = min(memory_sizes)
        
        # Извлекаем частоты
        freq_patterns = [
            r'(\d{4})\s*(?:mhz|мгц)',
            r'(\d\.\d)\s*(?:ghz|ггц)',
            r'(\d{4})mhz',
            r'(\d{4})мгц',
        ]
        
        frequencies = []
        for pattern in freq_patterns:
            matches = re.findall(pattern, name_lower)
            if matches:
                if 'ghz' in pattern or 'ггц' in pattern:
                    frequencies.extend([float(f) * 1000 for f in matches])  # Конвертируем в MHz
                else:
                    frequencies.extend([int(f) for f in matches])
        
        if frequencies:
            features['frequencies'] = frequencies
            features['max_frequency'] = max(frequencies)
        
        # Извлекаем типы памяти/интерфейсов
        tech_patterns = [
            r'ddr(\d)',
            r'gddr(\d+)',
            r'nvme',
            r'sata',
            r'pcie\s*(\d\.\d|\d+)',
            r'm\.2',
            r'dimm',
            r'so-dimm',
        ]
        
        for pattern in tech_patterns:
            match = re.search(pattern, name_lower)
            if match:
                if 'ddr' in pattern and 'gddr' not in pattern:
                    features['memory_type'] = f"ddr{match.group(1)}"
                elif 'gddr' in pattern:
                    features['video_memory_type'] = f"gddr{match.group(1)}"
                elif 'pcie' in pattern:
                    features['interface'] = f"pcie{match.group(1)}"
                elif pattern in ['nvme', 'sata', 'm\\.2', 'dimm', 'so-dimm']:
                    tech_type = pattern.replace('\\.', '.')
                    if tech_type in ['nvme', 'sata', 'm.2']:
                        features['storage_type'] = tech_type
                    elif tech_type in ['dimm', 'so-dimm']:
                        features['form_factor'] = tech_type
        
        # Извлекаем серийные номера и коды
        serial_patterns = [
            r'([a-z]{2,4}\d{2,}[a-z]*\d*)',      # PSD48G240081
            r'(\[.*?\])',                        # [PSD48G240081]
        ]
        
        serials = []
        for pattern in serial_patterns:
            matches = re.findall(pattern, name_lower)
            if matches:
                serials.extend(matches)
        
        if serials:
            features['serials'] = [s.strip('[]') for s in serials]
        
        return features
    
    def generate_ngrams(self, text: str, n: int = 3) -> Set[str]:
        """
        Генерация N-грамм из текста
        
        Args:
            text: исходный текст
            n: размер N-граммы
            
        Returns:
            множество N-грамм
        """
        # Очищаем и нормализуем текст
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        ngrams = set()
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            ngrams.add(ngram)
        
        return ngrams
    
    def calculate_feature_similarity(self, features1: Dict, features2: Dict) -> float:
        """
        Вычисление сходства на основе характеристик
        
        Args:
            features1, features2: словари с характеристиками
            
        Returns:
            оценка сходства от 0 до 1
        """
        if not features1 or not features2:
            return 0.0
        
        score = 0.0
        total_weight = 0.0
        
        # Веса для различных характеристик
        weights = {
            'brand': 0.20,           # Бренд важен
            'gpu_model': 0.30,       # Модель GPU критически важна
            'gpu_variant': 0.25,     # Ti/Super/XT очень важны
            'cpu_series': 0.15,      # Серия CPU важна
            'cpu_model': 0.30,       # Модель CPU критически важна
            'max_memory': 0.20,      # Максимальный объем памяти
            'memory_type': 0.15,     # Тип памяти
            'storage_type': 0.10,    # Тип накопителя
            'form_factor': 0.10,     # Форм-фактор
            'serials': 0.20,         # Серийные номера важны для точности
        }
        
        for feature, weight in weights.items():
            if feature in features1 and feature in features2:
                val1 = features1[feature]
                val2 = features2[feature]
                
                if feature in ['gpu_model', 'cpu_model']:
                    # Для моделей CPU/GPU - очень строгое сравнение
                    if val1 == val2:
                        score += weight
                    elif isinstance(val1, str) and isinstance(val2, str):
                        try:
                            num1 = int(re.findall(r'\d+', val1)[0]) if re.findall(r'\d+', val1) else 0
                            num2 = int(re.findall(r'\d+', val2)[0]) if re.findall(r'\d+', val2) else 0
                            
                            # Очень строгие штрафы за разные модели
                            diff = abs(num1 - num2)
                            if diff == 0:
                                score += weight
                            elif diff <= 25:   # Очень близкие модели (7700 vs 7750)
                                score += weight * 0.9
                            elif diff <= 50:   # Близкие модели (7700 vs 7750)
                                score += weight * 0.7
                            elif diff <= 100:  # Разные модели (7700 vs 7800)
                                score += weight * 0.2  # Большой штраф
                            # Более далекие модели почти не засчитываются
                        except:
                            pass
                elif feature == 'serials':
                    # Для серийных номеров - проверяем пересечение
                    if isinstance(val1, list) and isinstance(val2, list):
                        similarity = self._compare_serials(val1, val2)
                        score += weight * similarity
                    elif val1 == val2:
                        score += weight
                elif feature == 'max_memory':
                    # Для объема памяти - точное совпадение предпочтительнее
                    if val1 == val2:
                        score += weight
                    else:
                        ratio = min(val1, val2) / max(val1, val2)
                        if ratio >= 0.9:  # Очень близкие объемы
                            score += weight * ratio
                        elif ratio >= 0.5:  # Умеренно близкие объемы
                            score += weight * ratio * 0.5
                else:
                    # Для остальных характеристик - точное совпадение
                    if val1 == val2:
                        score += weight
                        
                total_weight += weight
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _compare_serials(self, serials1: List[str], serials2: List[str]) -> float:
        """Сравнение серийных номеров с учетом частичных совпадений"""
        if not serials1 or not serials2:
            return 0.0
        
        max_similarity = 0.0
        
        for s1 in serials1:
            for s2 in serials2:
                # Проверяем точное совпадение
                if s1 == s2:
                    return 1.0
                
                # Проверяем частичное совпадение (общие символы)
                if len(s1) >= 4 and len(s2) >= 4:
                    # Считаем общие подстроки длиной >= 4
                    common_parts = 0
                    total_parts = 0
                    for i in range(len(s1) - 3):
                        substr = s1[i:i+4]
                        total_parts += 1
                        if substr in s2:
                            common_parts += 1
                    
                    if total_parts > 0:
                        similarity = common_parts / total_parts
                        max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def calculate_ngram_similarity(self, text1: str, text2: str, n: int = 3) -> float:
        """
        Вычисление сходства на основе N-грамм
        
        Args:
            text1, text2: тексты для сравнения
            n: размер N-граммы
            
        Returns:
            оценка сходства от 0 до 1
        """
        ngrams1 = self.generate_ngrams(text1, n)
        ngrams2 = self.generate_ngrams(text2, n)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_penalty(self, features1: Dict, features2: Dict) -> float:
        """
        Вычисление штрафа за критические различия
        
        Args:
            features1, features2: характеристики товаров
            
        Returns:
            штраф от 0 до 1
        """
        penalty = 0.0
        
        # КРИТИЧЕСКИЙ штраф за разные варианты GPU (Ti vs без Ti, Super vs обычный)
        if ('gpu_variant' in features1) != ('gpu_variant' in features2):
            penalty += 0.6  # Очень большой штраф
        elif 'gpu_variant' in features1 and 'gpu_variant' in features2:
            if features1['gpu_variant'] != features2['gpu_variant']:
                penalty += 0.4  # Ti vs Super тоже штрафуется
        
        # Большой штраф за разные бренды
        if 'brand' in features1 and 'brand' in features2:
            if features1['brand'] != features2['brand']:
                penalty += 0.4
        
        # Критический штраф за сильно разные модели
        for model_key in ['gpu_model', 'cpu_model']:
            if model_key in features1 and model_key in features2:
                try:
                    val1 = features1[model_key]
                    val2 = features2[model_key]
                    
                    if isinstance(val1, str) and isinstance(val2, str):
                        num1 = int(re.findall(r'\d+', val1)[0]) if re.findall(r'\d+', val1) else 0
                        num2 = int(re.findall(r'\d+', val2)[0]) if re.findall(r'\d+', val2) else 0
                        
                        diff = abs(num1 - num2)
                        if diff > 300:  # Очень разные модели
                            penalty += 0.8
                        elif diff > 100:  # Разные модели (7700 vs 7800)
                            penalty += 0.5  # Большой штраф
                        elif diff > 50:   # Умеренно разные модели  
                            penalty += 0.2
                except:
                    pass
        
        # Штраф за кратно разные объемы памяти
        if 'max_memory' in features1 and 'max_memory' in features2:
            ratio = max(features1['max_memory'], features2['max_memory']) / min(features1['max_memory'], features2['max_memory'])
            if ratio > 4:  # Разница в 4 раза и больше
                penalty += 0.3
            elif ratio > 2:  # Разница в 2 раза
                penalty += 0.1
        
        return min(penalty, 0.95)  # Максимальный штраф 95%
    
    def enhanced_similarity(self, name1: str, name2: str, semantic_sim: float) -> float:
        """
        Гибридное сходство: семантика + характеристики + N-граммы
        
        Args:
            name1, name2: названия товаров
            semantic_sim: семантическое сходство от эмбеддингов
            
        Returns:
            итоговая оценка сходства
        """
        # Извлекаем характеристики
        features1 = self.extract_detailed_features(name1)
        features2 = self.extract_detailed_features(name2)
        
        # Вычисляем сходство характеристик
        feature_sim = self.calculate_feature_similarity(features1, features2)
        
        # Вычисляем сходство N-грамм разных размеров
        ngram3_sim = self.calculate_ngram_similarity(name1, name2, 3)
        ngram5_sim = self.calculate_ngram_similarity(name1, name2, 5)
        
        # Простое слово-в-слово сходство
        words1 = set(re.findall(r'\w+', name1.lower()))
        words2 = set(re.findall(r'\w+', name2.lower()))
        word_sim = len(words1.intersection(words2)) / len(words1.union(words2)) if words1.union(words2) else 0
        
        # Комбинируем метрики с весами - характеристики получают больший вес
        weights = {
            'semantic': 0.25,   # Семантическое сходство (снижаем вес)
            'features': 0.40,   # Характеристики - главное (увеличиваем вес)
            'ngram3': 0.15,     # 3-граммы
            'ngram5': 0.10,     # 5-граммы  
            'words': 0.10,      # Общие слова
        }
        
        final_score = (
            weights['semantic'] * semantic_sim +
            weights['features'] * feature_sim +
            weights['ngram3'] * ngram3_sim +
            weights['ngram5'] * ngram5_sim +
            weights['words'] * word_sim
        )
        
        # Применяем штрафы за критические различия
        penalty = self.calculate_penalty(features1, features2)
        final_score *= (1 - penalty)
        
        return max(0.0, min(1.0, final_score))
    
    def get_embeddings(self, texts: List[str], batch_size: int = 100) -> np.ndarray:
        """
        Получение эмбеддингов для списка текстов с батчингом и кэшированием
        
        Args:
            texts: список текстов
            batch_size: размер батча для обработки (по умолчанию 100)
            
        Returns:
            массив эмбеддингов
        """
        if not self.embeddings:
            raise Exception("Эмбеддинги не инициализированы")
        
        if not texts:
            return np.array([])
        
        try:
            # ВРЕМЕННО ОТКЛЮЧЕНО КЭШИРОВАНИЕ ДЛЯ ОТЛАДКИ
            # all_embeddings = []
            # texts_to_process = []
            # cached_embeddings = {}
            
            # # Проверяем кэш для каждого текста
            # for i, text in enumerate(texts):
            #     if text in self.embeddings_cache:
            #         cached_embeddings[i] = self.embeddings_cache[text]
            #     else:
            #         texts_to_process.append((i, text))
            
            # logger.info(f"Найдено в кэше: {len(cached_embeddings)} из {len(texts)} текстов")
            
            # # Обрабатываем только новые тексты батчами
            # if texts_to_process:
            #     new_embeddings = {}
            #     texts_only = [text for _, text in texts_to_process]
                
            #     for i in range(0, len(texts_only), batch_size):
            #         batch = texts_only[i:i + batch_size]
            #         batch_indices = [idx for idx, _ in texts_to_process[i:i + batch_size]]
                    
            #         logger.info(f"Обработка батча {i//batch_size + 1}: {len(batch)} новых текстов")
                    
            #         batch_embeddings = self.embeddings.embed_documents(batch)
                    
            #         # Сохраняем в кэш и в результат
            #         for j, (idx, text) in enumerate(texts_to_process[i:i + batch_size]):
            #             embedding = batch_embeddings[j]
            #             self.embeddings_cache[text] = embedding
            #             new_embeddings[idx] = embedding
                
            #     # Объединяем кэшированные и новые embeddings
            #     for i in range(len(texts)):
            #         if i in cached_embeddings:
            #             all_embeddings.append(cached_embeddings[i])
            #         elif i in new_embeddings:
            #             all_embeddings.append(new_embeddings[i])
            # else:
            #     # Все embeddings найдены в кэше
            #     for i in range(len(texts)):
            #         all_embeddings.append(cached_embeddings[i])
            
            # logger.info(f"Получено {len(all_embeddings)} эмбеддингов для {len(texts)} текстов")
            # logger.info(f"Размер кэша: {len(self.embeddings_cache)} текстов")
            # return np.array(all_embeddings)
            
            # ПРОСТАЯ ВЕРСИЯ БЕЗ КЭШИРОВАНИЯ
            logger.info(f"Получение эмбеддингов для {len(texts)} текстов (кэширование отключено)")
            all_embeddings = self.embeddings.embed_documents(texts)
            logger.info(f"Получено {len(all_embeddings)} эмбеддингов")
            return np.array(all_embeddings)
            
        except Exception as e:
            logger.error(f"Ошибка получения эмбеддингов: {e}")
            raise
    
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
                         threshold: float = 0.7, use_enhanced: bool = True) -> List[Tuple[str, str, float]]:
        """
        Поиск наилучших совпадений между двумя списками названий
        
        Args:
            names1, names2: списки названий для сравнения
            threshold: минимальный порог сходства
            use_enhanced: использовать гибридный алгоритм (семантика + характеристики)
            
        Returns:
            список кортежей (название1, название2, сходство)
        """
        if not names1 or not names2:
            return []
        
        try:
            # Получаем эмбеддинги для обеих групп названий
            embeddings1 = self.get_embeddings(names1)
            embeddings2 = self.get_embeddings(names2)
            
            matches = []
            
            # Сравниваем каждое название из первого списка с каждым из второго
            for i, name1 in enumerate(names1):
                best_similarity = 0.0
                best_match = None
                
                for j, name2 in enumerate(names2):
                    # Семантическое сходство от эмбеддингов
                    semantic_sim = self.cosine_similarity(embeddings1[i], embeddings2[j])
                    
                    if use_enhanced:
                        # Используем гибридный алгоритм: семантика + характеристики
                        similarity = self.enhanced_similarity(name1, name2, semantic_sim)
                    else:
                        # Используем только семантическое сходство
                        similarity = semantic_sim
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = (name1, name2, similarity)
                
                # Добавляем совпадение, если оно превышает порог
                if best_match and best_similarity >= threshold:
                    matches.append(best_match)
            
            return matches
        except Exception as e:
            logger.error(f"Ошибка при поиске совпадений: {e}")
            return []
    
    def compare_categories(self, dns_category: str, citi_category: str, 
                          threshold: float = 0.7) -> Dict:
        """
        Сравнение конкретных категорий DNS и Citilink
        
        Args:
            dns_category: название категории DNS
            citi_category: название категории Citilink  
            threshold: минимальный порог сходства
            
        Returns:
            словарь с результатами сравнения
        """
        # Карта категорий DNS
        dns_categories_map = {
            "SSD M_2 накопители": "product_data_SSD M_2 накопители.json",
            "SSD накопители": "product_data_SSD накопители.json",
            "Видеокарты": "product_data_Видеокарты.json",
            "Жесткие диски 3_5_": "product_data_Жесткие диски 3_5_.json",
            "Кулеры для процессоров": "product_data_Кулеры для процессоров.json",
            "Оперативная память DIMM": "product_data_Оперативная память DIMM.json",
            "Процессоры": "product_data_Процессоры.json"
        }
        
        # Карта категорий Citilink
        citi_categories_map = {
            "Блоки питания": "bloki-pitaniya",
            "Корпуса": "korpusa",
            "Материнские платы": "materinskie-platy",
            "Модули памяти": "moduli-pamyati",
            "Процессоры": "processory",
            "Кулеры для процессора": "sistemy-ohlazhdeniya-processora",
            "Видеокарты": "videokarty",
            "Жесткие диски": "zhestkie-diski"
        }
        
        # Проверяем существование категорий
        if dns_category not in dns_categories_map:
            return {"error": f"Категория DNS '{dns_category}' не найдена"}
        
        if citi_category not in citi_categories_map:
            return {"error": f"Категория Citilink '{citi_category}' не найдена"}
        
        # Формируем пути к файлам с fallback логикой
        dns_filename = dns_categories_map[dns_category]
        citi_dirname = citi_categories_map[citi_category]
        
        # Возможные пути для DNS файлов (контейнер и локальная разработка)
        dns_paths = [
            f"/app/data/DNS_parsing/categories/{dns_filename}",
            os.path.join(os.path.dirname(__file__), 'DNS_parsing', 'categories', dns_filename)
        ]
        
        # Возможные пути для Citilink файлов (контейнер и локальная разработка)
        citi_paths = [
            f"/app/data/Citi_parser/data/{citi_dirname}/Товары.json",
            os.path.join(os.path.dirname(__file__), 'Citi_parser', 'data', citi_dirname, 'Товары.json')
        ]
        
        # Функция для поиска существующего файла
        def find_existing_file(paths):
            for path in paths:
                if os.path.exists(path):
                    return path
            return None
        
        # Ищем существующие файлы
        dns_file_path = find_existing_file(dns_paths)
        citi_file_path = find_existing_file(citi_paths)
        
        if not dns_file_path:
            return {"error": f"Файл данных DNS для категории '{dns_category}' не найден"}
        
        if not citi_file_path:
            return {"error": f"Файл данных Citilink для категории '{citi_category}' не найден"}
        
        try:
            # Загружаем данные
            dns_data = self.load_json_data(dns_file_path)
            citi_data = self.load_json_data(citi_file_path)
            
            if not dns_data or not citi_data:
                return {"error": "Не удалось загрузить данные из одного или обоих файлов"}
            
            # Извлекаем названия
            dns_names = self.extract_names(dns_data)
            citi_names = self.extract_names(citi_data)
            
            # Находим совпадения
            matches = self.find_best_matches(dns_names, citi_names, threshold)
            
            # Создаем карты для быстрого поиска товаров по названию
            dns_map = {item['name']: item for item in dns_data}
            citi_map = {item['name']: item for item in citi_data}
            
            # Обогащаем результаты полной информацией о товарах
            enriched_matches = []
            price_differences = []
            
            for dns_name, citi_name, similarity in matches:
                dns_item = dns_map.get(dns_name)
                citi_item = citi_map.get(citi_name)
                
                if dns_item and citi_item:
                    # Извлекаем цены
                    dns_price = self._extract_price(dns_item)
                    citi_price = self._extract_price(citi_item)
                    
                    price_diff = None
                    if dns_price and citi_price:
                        price_diff = citi_price - dns_price
                        price_differences.append(price_diff)
                    
                    enriched_matches.append({
                        'dns_name': dns_name,
                        'citi_name': citi_name,
                        'similarity': similarity,
                        'dns_price': dns_price,
                        'citi_price': citi_price,
                        'price_difference': price_diff,
                        'dns_url': dns_item.get('url', ''),
                        'citi_url': citi_item.get('url', ''),
                        'dns_brand': dns_item.get('brand_name', ''),
                        'citi_brand': citi_item.get('brand', '')
                    })
            
            # Статистика по ценам
            price_stats = self._calculate_price_statistics(price_differences)
            
            return {
                "dns_category": dns_category,
                "citi_category": citi_category,
                "dns_count": len(dns_data),
                "citi_count": len(citi_data),
                "matches_count": len(enriched_matches),
                "matches": enriched_matches,
                "threshold": threshold,
                "price_statistics": price_stats
            }
            
        except Exception as e:
            logger.error(f"Ошибка при сравнении категорий: {e}")
            return {"error": str(e)}
    
    def _extract_price(self, item: Dict) -> float:
        """Извлечение цены из товара"""
        try:
            # Для DNS
            if 'price_original' in item:
                price = item['price_original']
            # Для Citilink
            elif 'price' in item:
                price = item['price']
            else:
                return None
            
            # Если цена - это словарь (может прийти из стандартизации)
            if isinstance(price, dict):
                # Проверяем ключи из стандартизации
                if 'current' in price:
                    price = price['current']
                elif 'old' in price:
                    price = price['old']
                elif 'value' in price:
                    price = price['value']
                elif 'amount' in price:
                    price = price['amount']
                else:
                    logger.warning(f"Неизвестная структура цены-словаря: {price}")
                    return None
            
            # Проверяем что это число или строка
            if isinstance(price, (int, float)):
                return float(price)
            elif isinstance(price, str):
                try:
                    # Убираем все нечисловые символы кроме точки и запятой
                    price_clean = ''.join(c for c in price if c.isdigit() or c in '.,')
                    price_clean = price_clean.replace(',', '.')
                    return float(price_clean) if price_clean else None
                except (ValueError, TypeError):
                    return None
            else:
                logger.warning(f"Неожиданный тип цены: {type(price)}, значение: {price}")
                return None
        except Exception as e:
            logger.error(f"Ошибка извлечения цены из товара: {e}, товар: {item.get('name', 'Неизвестно')}")
            return None
    
    def _calculate_price_statistics(self, price_differences: List[float]) -> Dict:
        """Вычисление статистики по ценам"""
        if not price_differences:
            return {}
        
        # Фильтруем валидные разности
        valid_diffs = [diff for diff in price_differences if diff is not None]
        
        if not valid_diffs:
            return {}
        
        return {
            'count': len(valid_diffs),
            'average_difference': sum(valid_diffs) / len(valid_diffs),
            'min_difference': min(valid_diffs),
            'max_difference': max(valid_diffs),
            'dns_cheaper_count': len([d for d in valid_diffs if d > 0]),
            'citi_cheaper_count': len([d for d in valid_diffs if d < 0]),
            'equal_price_count': len([d for d in valid_diffs if d == 0])
        }
    
    def get_available_categories(self) -> Dict[str, List[str]]:
        """
        Получение списка доступных категорий
        
        Returns:
            словарь с категориями DNS и Citilink
        """
        dns_categories = [
            "SSD M_2 накопители",
            "SSD накопители", 
            "Видеокарты",
            "Жесткие диски 3_5_",
            "Кулеры для процессоров",
            "Оперативная память DIMM",
            "Процессоры"
        ]
        
        citi_categories = [
            "Блоки питания",
            "Корпуса",
            "Материнские платы",
            "Модули памяти",
            "Процессоры",
            "Кулеры для процессора",
            "Видеокарты",
            "Жесткие диски"
        ]
        
        return {
            "dns_categories": dns_categories,
            "citi_categories": citi_categories
        }
    
    def clear_embeddings_cache(self):
        """Очистка кэша эмбеддингов"""
        # cache_size = len(self.embeddings_cache)
        # self.embeddings_cache.clear()
        # logger.info(f"Кэш очищен: удалено {cache_size} записей")
        # return cache_size
        logger.info("Кэширование отключено - нечего очищать")
        return 0
    
    def get_cache_size(self):
        """Получение размера кэша"""
        # return len(self.embeddings_cache)
        return 0

# Глобальный экземпляр компаратора
_comparator_instance = None

def get_comparator():
    """Получение глобального экземпляра компаратора"""
    global _comparator_instance
    if _comparator_instance is None:
        _comparator_instance = ProductComparator()
    return _comparator_instance 