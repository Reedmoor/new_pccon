#!/usr/bin/env python3
"""
Утилита для очистки временных файлов и остановки зависших процессов Citilink парсера
"""

import os
import sys
import logging
import glob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def remove_stop_flags():
    """Удаляет файлы-флаги остановки"""
    removed_count = 0
    
    # Ищем файлы флагов в текущей директории и поддиректориях
    flag_patterns = ['STOP_PARSER.flag', '**/STOP_PARSER.flag']
    
    for pattern in flag_patterns:
        for flag_file in glob.glob(pattern, recursive=True):
            try:
                os.remove(flag_file)
                logging.info(f"Удален файл-флаг: {flag_file}")
                removed_count += 1
            except Exception as e:
                logging.error(f"Ошибка при удалении {flag_file}: {e}")
    
    return removed_count

def cleanup_temp_files():
    """Очищает временные файлы парсера"""
    temp_patterns = [
        '*.tmp',
        '*.temp',
        '.parser_*',
        'parser_*.lock'
    ]
    
    removed_count = 0
    
    for pattern in temp_patterns:
        for temp_file in glob.glob(pattern):
            try:
                os.remove(temp_file)
                logging.info(f"Удален временный файл: {temp_file}")
                removed_count += 1
            except Exception as e:
                logging.error(f"Ошибка при удалении {temp_file}: {e}")
    
    return removed_count

def fix_incomplete_json_files():
    """Пытается исправить неполные JSON файлы"""
    json_files = ['Товары.json', 'Отзывы.json', 'Обзоры.json']
    fixed_count = 0
    
    for json_file in json_files:
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                # Проверяем, если файл не закрыт правильно
                if content and not content.endswith(']'):
                    if content.endswith(','):
                        # Удаляем последнюю запятую и добавляем закрывающую скобку
                        content = content.rstrip(',') + '\n]'
                    else:
                        # Просто добавляем закрывающую скобку
                        content += '\n]'
                    
                    # Создаем резервную копию
                    backup_file = f"{json_file}.backup"
                    os.rename(json_file, backup_file)
                    
                    # Записываем исправленный файл
                    with open(json_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    logging.info(f"Исправлен JSON файл: {json_file} (резервная копия: {backup_file})")
                    fixed_count += 1
                    
            except Exception as e:
                logging.error(f"Ошибка при исправлении {json_file}: {e}")
    
    return fixed_count

def show_parser_status():
    """Показывает статус файлов парсера"""
    logging.info("=== Статус файлов парсера ===")
    
    # Проверяем основные файлы
    files_to_check = [
        'Товары.json',
        'Отзывы.json', 
        'Обзоры.json',
        'parser.log',
        'STOP_PARSER.flag'
    ]
    
    for file_name in files_to_check:
        if os.path.exists(file_name):
            size = os.path.getsize(file_name)
            logging.info(f"✅ {file_name}: {size} байт")
        else:
            logging.info(f"❌ {file_name}: не найден")
    
    # Проверяем директории данных
    data_dirs = ['data']
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            subdirs = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
            logging.info(f"📁 {data_dir}/: {len(subdirs)} категорий ({', '.join(subdirs)})")
        else:
            logging.info(f"❌ {data_dir}/: не найдена")

def main():
    """Основная функция очистки"""
    logging.info("🧹 Запуск утилиты очистки Citilink парсера...")
    
    # Показываем текущий статус
    show_parser_status()
    
    total_cleaned = 0
    
    # 1. Удаляем файлы-флаги остановки
    logging.info("\n1. Удаление файлов-флагов остановки...")
    removed_flags = remove_stop_flags()
    total_cleaned += removed_flags
    
    if removed_flags > 0:
        logging.info(f"Удалено {removed_flags} файлов-флагов")
    else:
        logging.info("Файлы-флаги остановки не найдены")
    
    # 2. Очистка временных файлов
    logging.info("\n2. Очистка временных файлов...")
    removed_temp = cleanup_temp_files()
    total_cleaned += removed_temp
    
    if removed_temp > 0:
        logging.info(f"Удалено {removed_temp} временных файлов")
    else:
        logging.info("Временные файлы не найдены")
    
    # 3. Исправление неполных JSON файлов
    logging.info("\n3. Проверка и исправление JSON файлов...")
    fixed_json = fix_incomplete_json_files()
    
    if fixed_json > 0:
        logging.info(f"Исправлено {fixed_json} JSON файлов")
    else:
        logging.info("JSON файлы в порядке или не найдены")
    
    # Финальный статус
    logging.info(f"\n✅ Очистка завершена. Обработано {total_cleaned} файлов.")
    
    if total_cleaned > 0 or fixed_json > 0:
        logging.info("Парсер готов к новому запуску.")
    else:
        logging.info("Очистка не требовалась.")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logging.info("Очистка прервана пользователем")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Критическая ошибка при очистке: {e}")
        sys.exit(1) 