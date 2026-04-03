#!/usr/bin/env python3
"""
Скрипт для принудительной остановки Citilink парсера
"""

import os
import sys
import logging
import psutil
import signal
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_stop_flag():
    """Создает файл-флаг для остановки парсера"""
    try:
        with open('STOP_PARSER.flag', 'w') as f:
            f.write('STOP_REQUESTED')
        logging.info("🚩 Создан файл-флаг остановки парсера")
        return True
    except Exception as e:
        logging.error(f"Ошибка при создании файла-флага: {e}")
        return False

def find_parser_processes():
    """Находит процессы парсера"""
    parser_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                # Ищем процессы, которые запускают парсер
                if any(keyword in cmdline.lower() for keyword in ['main.py', 'citilink', 'parser']):
                    if 'Citi_parser' in cmdline or 'main.py' in cmdline:
                        parser_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return parser_processes

def stop_parser_processes(processes):
    """Останавливает процессы парсера"""
    stopped_count = 0
    
    for proc in processes:
        try:
            logging.info(f"Отправка сигнала SIGTERM процессу {proc.pid} ({proc.info['name']})")
            proc.send_signal(signal.SIGTERM)
            stopped_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logging.warning(f"Не удалось остановить процесс {proc.pid}: {e}")
    
    if stopped_count > 0:
        logging.info(f"Отправлен сигнал остановки {stopped_count} процессам")
        
        # Ждем немного и проверяем, завершились ли процессы
        time.sleep(3)
        
        # Принудительное завершение оставшихся процессов
        for proc in processes:
            try:
                if proc.is_running():
                    logging.warning(f"Принудительное завершение процесса {proc.pid}")
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    
    return stopped_count

def main():
    """Основная функция остановки парсера"""
    logging.info("🛑 Запуск процедуры остановки Citilink парсера...")
    
    # 1. Создаем файл-флаг остановки
    if not create_stop_flag():
        logging.error("Не удалось создать файл-флаг остановки")
        return 1
    
    # 2. Ищем процессы парсера
    parser_processes = find_parser_processes()
    
    if not parser_processes:
        logging.info("Активные процессы парсера не найдены")
        logging.info("Файл-флаг остановки создан. Парсер остановится при следующей проверке.")
        return 0
    
    logging.info(f"Найдено {len(parser_processes)} процессов парсера:")
    for proc in parser_processes:
        try:
            cmdline = ' '.join(proc.info['cmdline'])
            logging.info(f"  PID {proc.pid}: {cmdline}")
        except:
            logging.info(f"  PID {proc.pid}: <информация недоступна>")
    
    # 3. Останавливаем процессы
    stopped_count = stop_parser_processes(parser_processes)
    
    if stopped_count > 0:
        logging.info(f"✅ Отправлен сигнал остановки {stopped_count} процессам парсера")
    
    logging.info("🏁 Процедура остановки завершена")
    logging.info("Парсер должен остановиться в течение нескольких секунд")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logging.info("Остановка скрипта по Ctrl+C")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        sys.exit(1) 