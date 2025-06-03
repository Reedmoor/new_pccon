import json
import os
import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
import logging
import argparse
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='ram_price_comparison.log'
)
logger = logging.getLogger(__name__)

# Отключаем предупреждения о незащищенном соединении
urllib3.disable_warnings(InsecureRequestWarning)


def get_gigachat_token():
    """Получение токена для GigaChat API"""
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    payload = {
        'scope': 'GIGACHAT_API_PERS'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': 'af37cb18-f569-442c-8540-46165f646b24',
        'Authorization': 'basic MjZjYjAwNzUtZTllZS00YjkxLWJlOGEtYjk5N2FjMzA3ZjBmOmYwMjcyZTU5LWZiOTgtNDEzZS05MGJjLTFjNjk1MGEwODg1Zg=='
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        auth_data = json.loads(response.text)
        return auth_data['access_token']
    except Exception as e:
        logger.error(f"Ошибка получения токена: {e}")
        return None


def compare_ram_with_gigachat(dns_data, citilink_data):
    """Сравнение всех данных о RAM из DNS и Citilink с использованием GigaChat"""
    access_token = get_gigachat_token()
    if not access_token:
        logger.error("Не удалось получить токен доступа")
        return None

    # Формируем запрос к GigaChat
    chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    # Ограничиваем размер данных, чтобы не превысить лимиты API
    dns_sample = dns_data[:5] if len(dns_data) > 5 else dns_data
    citilink_sample = citilink_data[:5] if len(citilink_data) > 5 else citilink_data

    # Удаляем ненужные поля из данных для уменьшения размера запроса
    dns_clean = []
    for item in dns_sample:
        clean_item = {
            "id": item.get("id", ""),
            "name": item.get("name", ""),
            "price_original": item.get("price_original", 0),
            "brand_name": item.get("brand_name", ""),
            "characteristics": item.get("characteristics", {})
        }
        dns_clean.append(clean_item)

    citilink_clean = []
    for item in citilink_sample:
        clean_item = {
            "id": item.get("id", ""),
            "name": item.get("name", ""),
            "price": item.get("price", 0),
            "properties": item.get("properties", [])
        }
        citilink_clean.append(clean_item)

    prompt = f"""
    Проанализируй данные о RAM из двух магазинов (DNS и Citilink) и найди одинаковые товары.
    Для каждой пары одинаковых товаров проведи сравнение цен и характеристик.

    Данные DNS:
    {json.dumps(dns_clean, ensure_ascii=False, indent=2)}

    Данные Citilink:
    {json.dumps(citilink_clean, ensure_ascii=False, indent=2)}

    Для каждой найденной пары одинаковых товаров проведи анализ:
    1. Сравнение цен
    2. Сравнение технических характеристик
    3. Соотношение цена/качество
    4. Рекомендация по выбору

    Если одинаковых товаров не найдено, предложи наиболее похожие модели для сравнения.
    """

    payload = {
        "model": "GigaChat-2",
        "messages": [{"role": "user", "content": prompt}]
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    try:
        response = requests.request("POST", chat_url, headers=headers, json=payload, verify=False)
        result = json.loads(response.text)
        return result
    except Exception as e:
        logger.error(f"Ошибка при запросе к GigaChat: {e}")
        return None


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


def extract_ram_size(name):
    """Извлечение размера оперативной памяти из названия"""
    if "8 ГБ" in name or "8GB" in name.upper() or "8 GB" in name.upper() or "8гб" in name.lower():
        return 8
    elif "16 ГБ" in name or "16GB" in name.upper() or "16 GB" in name.upper() or "16гб" in name.lower():
        return 16
    elif "32 ГБ" in name or "32GB" in name.upper() or "32 GB" in name.upper() or "32гб" in name.lower():
        return 32
    elif "64 ГБ" in name or "64GB" in name.upper() or "64 GB" in name.upper() or "64гб" in name.lower():
        return 64
    return 0


def extract_ram_frequency(name):
    """Извлечение частоты оперативной памяти из названия"""
    import re
    # Ищем числа, за которыми следует "МГц" или "MHz"
    freq_match = re.search(r'(\d{3,4})\s*(?:МГц|MHz|МГц|Mhz)', name, re.IGNORECASE)
    if freq_match:
        return int(freq_match.group(1))
    return 0


def find_similar_ram_models(dns_data, citilink_data):
    """Поиск похожих моделей оперативной памяти в обоих магазинах"""
    if not dns_data or not citilink_data:
        logger.error("Не удалось загрузить данные из одного или обоих источников")
        return []

    similar_pairs = []

    # Более продвинутый алгоритм поиска похожих моделей
    for dns_ram in dns_data:
        dns_name = dns_ram["name"].lower()
        dns_brand = dns_ram["brand_name"].lower()
        dns_size = extract_ram_size(dns_ram["name"])
        dns_freq = extract_ram_frequency(dns_ram["name"])

        for citilink_ram in citilink_data:
            citilink_name = citilink_ram["name"].lower()

            # Проверяем наличие бренда в названии
            if dns_brand in citilink_name:
                citilink_size = extract_ram_size(citilink_ram["name"])
                citilink_freq = extract_ram_frequency(citilink_ram["name"])

                # Если совпадает размер и частота близка
                if dns_size == citilink_size and (
                        abs(dns_freq - citilink_freq) < 400 if dns_freq and citilink_freq else True):
                    similar_pairs.append((dns_ram, citilink_ram))
                    break  # Нашли подходящую пару, переходим к следующей DNS модели

    return similar_pairs


def filter_ram_by_brand(data, brand):
    """Фильтрация оперативной памяти по бренду"""
    return [item for item in data if brand.lower() in item["name"].lower() or
            (item.get("brand_name", "").lower() == brand.lower())]


def filter_ram_by_size(data, size):
    """Фильтрация оперативной памяти по объему"""
    return [item for item in data if extract_ram_size(item["name"]) == size]


def filter_ram_by_frequency(data, freq, tolerance=200):
    """Фильтрация оперативной памяти по частоте"""
    return [item for item in data if abs(extract_ram_frequency(item["name"]) - freq) <= tolerance]


def display_ram_list(ram_list, source=""):
    """Отображение списка оперативной памяти"""
    print(f"\n{source} RAM модули:")
    for i, ram in enumerate(ram_list):
        price = ram.get("price_original", ram.get("price", "Нет данных"))
        print(f"{i + 1}. {ram['name']} - {price} руб.")


def select_ram_from_list(ram_list, prompt_text):
    """Выбор оперативной памяти из списка"""
    while True:
        try:
            choice = int(input(prompt_text))
            if 1 <= choice <= len(ram_list):
                return ram_list[choice - 1]
            else:
                print(f"Пожалуйста, выберите число от 1 до {len(ram_list)}")
        except ValueError:
            print("Пожалуйста, введите число")


def compare_all_ram_mode():
    """Режим сравнения всех данных о RAM"""
    print("\n=== Сравнение всех данных о RAM из DNS и Citilink ===\n")

    # Загрузка данных
    dns_data = load_dns_ram_data()
    citilink_data = load_citilink_ram_data()

    if not dns_data or not citilink_data:
        print("Ошибка: Не удалось загрузить данные из одного или обоих источников")
        return

    print(f"Загружено {len(dns_data)} товаров из DNS и {len(citilink_data)} товаров из Citilink")
    print("Отправляем запрос к GigaChat для сравнения данных...")

    # Получаем анализ от GigaChat
    comparison_result = compare_ram_with_gigachat(dns_data, citilink_data)

    if comparison_result:
        # Извлекаем ответ от модели
        if 'choices' in comparison_result and comparison_result['choices']:
            analysis = comparison_result['choices'][0]['message']['content']

            # Сохраняем результат в JSON файл
            result = {
                "analysis": analysis
            }

            with open('ram_comparison_all.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            # Вывод результата в консоль
            print("\nРезультат сравнения RAM данных:")
            print(analysis)
            print("\nРезультат сохранен в файл ram_comparison_all.json")
        else:
            print(f"Ошибка: Некорректный формат ответа от GigaChat")
    else:
        print("Ошибка: Не удалось получить результат сравнения от GigaChat")


def interactive_mode():
    """Интерактивный режим выбора и сравнения оперативной памяти"""
    print("\n=== Сравнение цен на оперативную память ===\n")

    # Загрузка данных
    dns_data = load_dns_ram_data()
    citilink_data = load_citilink_ram_data()

    if not dns_data or not citilink_data:
        print("Ошибка: Не удалось загрузить данные из одного или обоих источников")
        return

    # Фильтрация по критериям
    print("Выберите критерий фильтрации:")
    print("1. По бренду")
    print("2. По объему памяти")
    print("3. По частоте")
    print("4. Показать все")

    filter_choice = input("Ваш выбор (1-4): ")

    filtered_dns = dns_data
    filtered_citilink = citilink_data

    if filter_choice == "1":
        brand = input("Введите название бренда (например, Kingston, Crucial, HyperX): ")
        filtered_dns = filter_ram_by_brand(dns_data, brand)
        filtered_citilink = filter_ram_by_brand(citilink_data, brand)
    elif filter_choice == "2":
        size = int(input("Введите объем памяти в ГБ (8, 16, 32, 64): "))
        filtered_dns = filter_ram_by_size(dns_data, size)
        filtered_citilink = filter_ram_by_size(citilink_data, size)
    elif filter_choice == "3":
        freq = int(input("Введите частоту в МГц (например, 3200): "))
        filtered_dns = filter_ram_by_frequency(dns_data, freq)
        filtered_citilink = filter_ram_by_frequency(citilink_data, freq)

    # Ограничиваем количество отображаемых элементов
    filtered_dns = filtered_dns[:20]
    filtered_citilink = filtered_citilink[:20]

    if not filtered_dns:
        print("Не найдено RAM модулей DNS по заданным критериям")
        return

    if not filtered_citilink:
        print("Не найдено RAM модулей Citilink по заданным критериям")
        return

    # Отображаем списки и предлагаем выбрать
    display_ram_list(filtered_dns, "DNS")
    dns_ram = select_ram_from_list(filtered_dns, "Выберите модель DNS (введите номер): ")

    display_ram_list(filtered_citilink, "Citilink")
    citilink_ram = select_ram_from_list(filtered_citilink, "Выберите модель Citilink (введите номер): ")

    # Получаем анализ от GigaChat
    print("\nОтправляем запрос к GigaChat для сравнения моделей...")

    # Используем старую функцию для сравнения двух товаров
    access_token = get_gigachat_token()
    if not access_token:
        print("Ошибка: Не удалось получить токен доступа")
        return

    # Формируем запрос к GigaChat
    chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    # Удаляем ненужные большие поля из данных для уменьшения размера запроса
    dns_clean = dns_ram.copy()
    citilink_clean = citilink_ram.copy()

    # Удаляем изображения, так как они не нужны для анализа
    if 'images' in dns_clean:
        dns_clean['images'] = [dns_clean['images'][0]] if dns_clean['images'] else []
    if 'images' in citilink_clean:
        citilink_clean['images'] = [citilink_clean['images'][0]] if citilink_clean['images'] else []

    # Удаляем другие потенциально большие поля
    for item in [dns_clean, citilink_clean]:
        if 'description' in item and isinstance(item['description'], str) and len(item['description']) > 1000:
            item['description'] = item['description'][:1000] + "..."
        if 'drivers' in item:
            item['drivers'] = []
        if 'documents' in item:
            item['documents'] = []

    prompt = f"""
    Сравни две модели оперативной памяти и определи, какая из них предлагает лучшее соотношение цена/качество:

    Модель 1 (DNS):
    {json.dumps(dns_clean, ensure_ascii=False, indent=2)}

    Модель 2 (Citilink):
    {json.dumps(citilink_clean, ensure_ascii=False, indent=2)}

    Проведи анализ по следующим критериям:
    1. Сравнение цен
    2. Сравнение технических характеристик (объем памяти, частота, тайминги и т.д.)
    3. Соотношение цена/качество
    4. Рекомендация по выбору
    """

    payload = {
        "model": "GigaChat-2",
        "messages": [{"role": "user", "content": prompt}]
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    try:
        response = requests.request("POST", chat_url, headers=headers, json=payload, verify=False)
        comparison_result = json.loads(response.text)

        # Извлекаем ответ от модели
        if 'choices' in comparison_result and comparison_result['choices']:
            analysis = comparison_result['choices'][0]['message']['content']

            # Сохраняем результат в JSON файл
            result = {
                "dns_model": {
                    "name": dns_ram["name"],
                    "price": dns_ram["price_original"],
                    "url": dns_ram["url"]
                },
                "citilink_model": {
                    "name": citilink_ram["name"],
                    "price": citilink_ram["price"],
                    "url": citilink_ram["url"]
                },
                "analysis": analysis
            }

            with open('ram_comparison_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            # Вывод результата в консоль
            print("\nРезультат сравнения оперативной памяти:")
            print(f"DNS: {dns_ram['name']} - {dns_ram['price_original']} руб.")
            print(f"Citilink: {citilink_ram['name']} - {citilink_ram['price']} руб.")
            print("\nАнализ:")
            print(analysis)
            print("\nРезультат сохранен в файл ram_comparison_result.json")
        else:
            print(f"Ошибка: Некорректный формат ответа от GigaChat")
    except Exception as e:
        print(f"Ошибка при запросе к GigaChat: {e}")


def auto_mode():
    """Автоматический режим сравнения похожих моделей оперативной памяти"""
    # Загрузка данных
    dns_data = load_dns_ram_data()
    citilink_data = load_citilink_ram_data()

    if not dns_data or not citilink_data:
        print("Ошибка: Не удалось загрузить данные из одного или обоих источников")
        return

    similar_pairs = find_similar_ram_models(dns_data, citilink_data)

    if not similar_pairs:
        print("Не найдено похожих моделей оперативной памяти")
        return

    # Берем первую пару для демонстрации
    dns_ram, citilink_ram = similar_pairs[0]

    print(f"Сравниваем модели: {dns_ram['name']} и {citilink_ram['name']}")

    # Получаем анализ от GigaChat
    # Используем старую функцию для сравнения двух товаров
    access_token = get_gigachat_token()
    if not access_token:
        print("Ошибка: Не удалось получить токен доступа")
        return

    # Формируем запрос к GigaChat
    chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    # Удаляем ненужные большие поля из данных для уменьшения размера запроса
    dns_clean = dns_ram.copy()
    citilink_clean = citilink_ram.copy()

    # Удаляем изображения, так как они не нужны для анализа
    if 'images' in dns_clean:
        dns_clean['images'] = [dns_clean['images'][0]] if dns_clean['images'] else []
    if 'images' in citilink_clean:
        citilink_clean['images'] = [citilink_clean['images'][0]] if citilink_clean['images'] else []

    # Удаляем другие потенциально большие поля
    for item in [dns_clean, citilink_clean]:
        if 'description' in item and isinstance(item['description'], str) and len(item['description']) > 1000:
            item['description'] = item['description'][:1000] + "..."
        if 'drivers' in item:
            item['drivers'] = []
        if 'documents' in item:
            item['documents'] = []

    prompt = f"""
    Сравни две модели оперативной памяти и определи, какая из них предлагает лучшее соотношение цена/качество:

    Модель 1 (DNS):
    {json.dumps(dns_clean, ensure_ascii=False, indent=2)}

    Модель 2 (Citilink):
    {json.dumps(citilink_clean, ensure_ascii=False, indent=2)}

    Проведи анализ по следующим критериям:
    1. Сравнение цен
    2. Сравнение технических характеристик (объем памяти, частота, тайминги и т.д.)
    3. Соотношение цена/качество
    4. Рекомендация по выбору
    """

    payload = {
        "model": "GigaChat-2",
        "messages": [{"role": "user", "content": prompt}]
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    try:
        response = requests.request("POST", chat_url, headers=headers, json=payload, verify=False)
        comparison_result = json.loads(response.text)

        # Извлекаем ответ от модели
        if 'choices' in comparison_result and comparison_result['choices']:
            analysis = comparison_result['choices'][0]['message']['content']

            # Сохраняем результат в JSON файл
            result = {
                "dns_model": {
                    "name": dns_ram["name"],
                    "price": dns_ram["price_original"],
                    "url": dns_ram["url"]
                },
                "citilink_model": {
                    "name": citilink_ram["name"],
                    "price": citilink_ram["price"],
                    "url": citilink_ram["url"]
                },
                "analysis": analysis
            }

            with open('ram_comparison_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            # Вывод результата в консоль
            print("\nРезультат сравнения оперативной памяти:")
            print(f"DNS: {dns_ram['name']} - {dns_ram['price_original']} руб.")
            print(f"Citilink: {citilink_ram['name']} - {citilink_ram['price']} руб.")
            print("\nАнализ:")
            print(analysis)
            print("\nРезультат сохранен в файл ram_comparison_result.json")
        else:
            print(f"Ошибка: Некорректный формат ответа от GigaChat")
    except Exception as e:
        print(f"Ошибка при запросе к GigaChat: {e}")


def main():
    """Основная функция для сравнения цен на оперативную память"""
    parser = argparse.ArgumentParser(description='Сравнение цен на оперативную память с использованием GigaChat')
    parser.add_argument('--mode', choices=['auto', 'interactive', 'compare_all'], default='interactive',
                        help='Режим работы: auto - автоматическое сравнение похожих моделей, interactive - интерактивный выбор моделей, compare_all - сравнение всех данных')

    args = parser.parse_args()

    if args.mode == 'auto':
        auto_mode()
    elif args.mode == 'compare_all':
        compare_all_ram_mode()
    else:
        interactive_mode()


if __name__ == "__main__":
    main()

