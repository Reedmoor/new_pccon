"""Импорт товаров парсеров в UnifiedProduct."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

try:
    from app import create_app, db
    from app.utils.standardization.import_helpers import (
        collect_citilink_category_dirs,
        collect_from_json_files,
        convert_to_unified_product,
        dedupe_std_products,
        detect_product_type,
        discover_import_paths,
        ensure_compatibility_characteristics,
        ensure_import_identity,
        infer_vendor,
        persist_std_products,
        prepare_std_product,
        print_type_stats,
        resolve_product_type,
        standardize_characteristics,
        upsert_unified_product,
    )
except ImportError:
    print("Error importing app modules. Run from project root.")
    sys.exit(1)

# Обратная совместимость для comparison.py и др.
__all__ = ["detect_product_type", "resolve_product_type", "import_products", "import_products_from_data", "import_latest_citilink_dump", "import_latest_dns_dump"]


def import_products_from_data(products_data, source="local_parser"):
    """Импорт списка товаров (API). Upsert по product_url."""
    app = create_app()
    with app.app_context():
        print(f"Импорт {len(products_data)} товаров из {source}")
        added_count = updated_count = error_count = 0
        results = []

        for idx, product in enumerate(products_data):
            try:
                if not isinstance(product, dict):
                    raise ValueError("Product must be an object")
                vendor = infer_vendor(product, source)
                product_type = resolve_product_type(product)
                std = standardize_characteristics(product, vendor)
                std["vendor"] = vendor
                if product_type and product_type != "other":
                    std["product_type"] = product_type
                ensure_compatibility_characteristics(std)
                ensure_import_identity(std, product, vendor)
                unified = convert_to_unified_product(std)
                action, _ = upsert_unified_product(unified)
                db.session.commit()
                if action == "added":
                    added_count += 1
                else:
                    updated_count += 1
                results.append({
                    "name": product.get("name", "Unknown"),
                    "type": product_type,
                    "vendor": vendor,
                    "status": action,
                })
                if idx % 50 == 0 and idx > 0:
                    print(f"  обработано {idx} (+{added_count} / ~{updated_count})")
            except Exception as e:
                error_count += 1
                db.session.rollback()
                results.append({"name": product.get("name", "Unknown"), "status": "error", "error": str(e)})
                print(f"Ошибка товара {idx + 1}: {e}")

        print(f"Готово: +{added_count}, обновлено {updated_count}, ошибок {error_count}")
        print_type_stats()
        return {
            "success": error_count < len(products_data),
            "added_count": added_count,
            "updated_count": updated_count,
            "error_count": error_count,
            "results": results,
        }


def import_latest_dns_dump(project_root=None):
    """Импорт последнего дампа DNS в БД."""
    from app.utils.standardization.import_helpers import find_latest_dns_dump, load_products_from_json

    dump_path = find_latest_dns_dump(project_root)
    if not dump_path:
        return import_products()

    products = load_products_from_json(dump_path)
    if not products:
        return {
            "success": False,
            "error": "DNS dump is empty",
            "added_count": 0,
            "updated_count": 0,
            "error_count": 0,
        }

    print(f"Импорт последнего дампа DNS: {dump_path} ({len(products)} товаров)")
    return import_products_from_data(products, source="dns")


def import_latest_citilink_dump(project_root=None):
    """Импорт последнего дампа Citilink (data/citilink/citilink_*.json) в БД."""
    from app.utils.standardization.import_helpers import find_latest_citilink_dump, load_products_from_json

    dump_path = find_latest_citilink_dump(project_root)
    if not dump_path:
        return import_products()

    products = load_products_from_json(dump_path)
    if not products:
        return {
            "success": False,
            "error": "Citilink dump is empty",
            "added_count": 0,
            "updated_count": 0,
            "error_count": 0,
        }

    print(f"Импорт последнего дампа Citilink: {dump_path} ({len(products)} товаров)")
    return import_products_from_data(products, source="citilink")


def import_products():
    """Полный импорт из JSON-файлов парсеров на диске."""
    app = create_app()
    with app.app_context():
        all_products = []
        patterns, citilink_roots = discover_import_paths()

        print("Сбор товаров из файлов...")
        for pattern, vendor, strict, require_name in patterns:
            print(f"[{vendor}] {pattern}")
            all_products.extend(
                collect_from_json_files(pattern, vendor, strict=strict, require_name=require_name)
            )

        if citilink_roots:
            print("[citilink] каталоги по категориям")
            all_products.extend(collect_citilink_category_dirs(citilink_roots))

        print(f"Всего перед дедупликацией: {len(all_products)}")
        unique, removed = dedupe_std_products(all_products)
        print(f"После дедупликации: {len(unique)} (удалено дублей: {removed})")

        stats = persist_std_products(unique, log_every=100)
        print(f"Готово: +{stats['added_count']}, обновлено {stats['updated_count']}, ошибок {stats['error_count']}")
        print_type_stats()
        return stats


if __name__ == "__main__":
    import_products()
