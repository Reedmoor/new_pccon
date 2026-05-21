import argparse
import glob
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

SOURCE_GROUPS = {
    'citilink_current': 'data/citilink/citilink_*.json',
    'citilink_backups': 'data/parser_backups/*/citilink/data',
    'dns_backups': 'data/parser_backups/*/dns/product_data.json',
    'dns_current': 'data/dns/dns_*.json',
    'local_parser': 'data/local_parser_data_*.json',
}


def load_json_count(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            if data and all(isinstance(item, list) for item in data):
                return sum(len(item) for item in data), None
            if len(data) == 1 and isinstance(data[0], list):
                return len(data[0]), None
            return len(data), None
        if isinstance(data, dict):
            for key in ('products', 'data', 'items'):
                if key in data and isinstance(data[key], list):
                    return len(data[key]), None
            return 1, None
        return 1, None
    except Exception as exc:
        return 0, str(exc)


def count_citilink_primary(data_root):
    counts = {}
    if not os.path.isdir(data_root):
        return counts

    for category in sorted(os.listdir(data_root)):
        category_path = os.path.join(data_root, category)
        if not os.path.isdir(category_path):
            continue
        products_file = os.path.join(category_path, 'Товары.json')
        if os.path.exists(products_file):
            count, error = load_json_count(products_file)
            counts[products_file] = {'count': count, 'error': error}
    return counts


def count_citilink_backups(pattern):
    counts = {}
    for data_root in sorted(glob.glob(pattern)):
        if not os.path.isdir(data_root):
            continue
        root_name = os.path.relpath(data_root, ROOT)
        counts[root_name] = {
            'files': count_citilink_primary(data_root),
        }
    return counts


def count_simple_files(pattern):
    counts = {}
    for file_path in sorted(glob.glob(pattern)):
        count, error = load_json_count(file_path)
        counts[file_path] = {'count': count, 'error': error}
    return counts


def print_group(name, data):
    print(f"\n=== {name} ===")
    if not data:
        print("  (не найдено)")
        return
    total = 0
    total_errors = 0
    for key, value in data.items():
        if isinstance(value, dict) and 'files' in value:
            print(f"{key}:")
            for subpath, subvalue in value['files'].items():
                error = subvalue['error']
                if error:
                    total_errors += 1
                    print(f"  {subpath}: ошибка загрузки ({error})")
                else:
                    total += subvalue['count']
                    print(f"  {subpath}: {subvalue['count']}")
        else:
            error = value['error']
            if error:
                total_errors += 1
                print(f"{key}: ошибка загрузки ({error})")
            else:
                total += value['count']
                print(f"{key}: {value['count']}")
    print(f"  Итог: {total} товаров{', ошибок: ' + str(total_errors) if total_errors else ''}")
    return total


def count_db_products():
    try:
        from app import create_app
        from app.models.models import UnifiedProduct
    except Exception as exc:
        print(f"Не удалось импортировать приложение или модель: {exc}")
        return None

    app = create_app()
    with app.app_context():
        return UnifiedProduct.query.count()


def main():
    parser = argparse.ArgumentParser(description='Count products in initial JSON files and compare with DB')
    parser.add_argument('--no-backups', action='store_true', help='Не считать Citilink бэкапы')
    parser.add_argument('--no-db', action='store_true', help='Не считать количество продуктов в базе данных')
    args = parser.parse_args()

    current_citilink = count_simple_files(SOURCE_GROUPS['citilink_current'])
    citilink_current_total = print_group('Citilink (текущие данные)', current_citilink) or 0

    citilink_backups = {}
    citilink_backups_total = 0
    if not args.no_backups:
        citilink_backups = count_citilink_backups(SOURCE_GROUPS['citilink_backups'])
        citilink_backups_total = print_group('Citilink (бэкапы)', citilink_backups) or 0

    dns_backups = count_simple_files(SOURCE_GROUPS['dns_backups'])
    dns_backups_total = print_group('DNS (бэкапы)', dns_backups) or 0

    dns_current = count_simple_files(SOURCE_GROUPS['dns_current'])
    dns_current_total = print_group('DNS (текущие данные)', dns_current) or 0

    local_parser = count_simple_files(SOURCE_GROUPS['local_parser'])
    local_parser_total = print_group('Local parser файлы', local_parser) or 0

    total_raw = citilink_current_total + citilink_backups_total + dns_backups_total + dns_current_total + local_parser_total
    print(f"\n=== Общее количество исходных JSON-товаров: {total_raw} ===")
    print(f"Citilink total: {citilink_current_total + citilink_backups_total}")
    print(f"DNS total: {dns_backups_total + dns_current_total}")
    print(f"Local parser total: {local_parser_total}")

    db_count = None
    if not args.no_db:
        db_count = count_db_products()
        if db_count is not None:
            print(f"Всего продуктов в БД UnifiedProduct: {db_count}")
            estimated_left = max(total_raw - db_count, 0)
            print(f"Оценочно осталось импортировать: {estimated_left} (примерно)")
        else:
            print("База данных не посчитана")

    if db_count is None:
        print("Запустите с --no-db, чтобы пропустить попытку подключения к базе данных.")


if __name__ == '__main__':
    main()
