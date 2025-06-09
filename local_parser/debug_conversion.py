#!/usr/bin/env python3
"""
Скрипт для отладки конвертации товара в UnifiedProduct
"""

import json
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.utils.standardization.standardize import standardize_characteristics, convert_to_unified_product
    from app.models.models import UnifiedProduct
    from app import create_app, db
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    sys.exit(1)

def debug_conversion():
    """Отладка полного процесса конвертации"""
    print("🔍 ОТЛАДКА КОНВЕРТАЦИИ ТОВАРА")
    print("=" * 60)
    
    # Читаем товар из JSON
    json_file = "../data/local_parser_data_20250607_151208.json"
    target_product = None
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        # Ищем ARDOR GAMING Rare M
        for product in products:
            name = product.get('name') or ''
            if 'ARDOR GAMING Rare M' in name:
                target_product = product
                print(f"✅ Найден товар: {name}")
                break
        
        if not target_product:
            print("❌ Товар ARDOR GAMING Rare M не найден!")
            return
            
    except Exception as e:
        print(f"❌ Ошибка чтения JSON: {e}")
        return
    
    print(f"\n🔧 ЭТАП 1: СТАНДАРТИЗАЦИЯ")
    print("-" * 40)
    
    try:
        # Стандартизация
        std_product = standardize_characteristics(target_product, 'dns')
        print(f"✅ Стандартизация успешна")
        print(f"   Название: {std_product.get('product_name')}")
        print(f"   Тип: {std_product.get('product_type')}")
        print(f"   Vendor: {std_product.get('vendor', 'НЕ УСТАНОВЛЕН')}")
        print(f"   URL: {std_product.get('product_url')}")
        print(f"   Характеристики: {len(std_product.get('characteristics', {}))}")
        
    except Exception as e:
        print(f"❌ Ошибка стандартизации: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"\n🔧 ЭТАП 2: КОНВЕРТАЦИЯ В UnifiedProduct")
    print("-" * 40)
    
    try:
        # Устанавливаем vendor если не установлен
        if not std_product.get('vendor'):
            std_product['vendor'] = 'dns'
            print(f"🔧 Установлен vendor: dns")
        
        # Конвертация в UnifiedProduct
        unified_product = convert_to_unified_product(std_product)
        print(f"✅ Конвертация в UnifiedProduct успешна")
        print(f"   Тип объекта: {type(unified_product)}")
        print(f"   product_name: {unified_product.product_name}")
        print(f"   product_type: {unified_product.product_type}")
        print(f"   vendor: {unified_product.vendor}")
        print(f"   price_discounted: {unified_product.price_discounted}")
        print(f"   price_original: {unified_product.price_original}")
        print(f"   product_url: {unified_product.product_url}")
        print(f"   characteristics: {type(unified_product.characteristics)} (length: {len(unified_product.characteristics) if unified_product.characteristics else 0})")
        print(f"   images: {type(unified_product.images)} (length: {len(unified_product.images) if unified_product.images else 0})")
        print(f"   category: {type(unified_product.category)} (length: {len(unified_product.category) if unified_product.category else 0})")
        
    except Exception as e:
        print(f"❌ Ошибка конвертации в UnifiedProduct: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"\n🔧 ЭТАП 3: ПРОВЕРКА ПОЛЕЙ БД")
    print("-" * 40)
    
    # Проверяем соответствие полей модели
    required_fields = {
        'product_name': unified_product.product_name,
        'vendor': unified_product.vendor,
        'product_url': unified_product.product_url,
        'characteristics': unified_product.characteristics,
        'product_type': unified_product.product_type,
    }
    
    for field_name, field_value in required_fields.items():
        if field_value is None or field_value == "":
            print(f"❌ {field_name}: ПУСТОЕ ({field_value})")
        else:
            print(f"✅ {field_name}: OK ({type(field_value)}, length: {len(str(field_value))})")
    
    print(f"\n🔧 ЭТАП 4: ПРОБНОЕ СОХРАНЕНИЕ В БД")
    print("-" * 40)
    
    try:
        # Создаем приложение и тестируем сохранение
        app = create_app()
        with app.app_context():
            
            # Проверяем существование товара
            existing = db.session.query(UnifiedProduct).filter(
                UnifiedProduct.product_name == unified_product.product_name,
                UnifiedProduct.vendor == unified_product.vendor
            ).first()
            
            if existing:
                print(f"⚠️ Товар уже существует в БД с ID: {existing.id}")
                print(f"   Существующий тип: {existing.product_type}")
                print(f"   Новый тип: {unified_product.product_type}")
                
                # Проверяем различия
                if existing.product_type != unified_product.product_type:
                    print(f"❗ РАЗЛИЧИЕ В ТИПЕ ТОВАРА!")
                
                return
            
            # Пробуем добавить новый товар
            print(f"💾 Попытка сохранения нового товара...")
            db.session.add(unified_product)
            db.session.flush()  # Проверяем валидацию без коммита
            
            print(f"✅ Валидация прошла успешно! ID будет: {unified_product.id}")
            
            # НЕ коммитим, просто проверяем
            db.session.rollback()
            print(f"🔄 Rollback выполнен (тест)")
            
    except Exception as e:
        print(f"❌ Ошибка при пробном сохранении: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            db.session.rollback()
        except:
            pass

if __name__ == "__main__":
    debug_conversion() 