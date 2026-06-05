"""Общая логика импорта товаров в UnifiedProduct."""
import glob
import json
import os
import re
import traceback
from pathlib import Path

from app import db
from app.models.models import UnifiedProduct
from app.utils.standardization.standardize import (
    standardize_characteristics,
    convert_to_unified_product,
)

PRODUCT_TYPES = (
    "case", "processor", "graphics_card", "motherboard",
    "power_supply", "ram", "cooler", "hard_drive",
)

# Ключи формы сравнения (comparison) → product_type в БД
COMPARE_CATEGORY_TO_TYPE = {
    "gpu": "graphics_card",
    "cpu": "processor",
    "ram": "ram",
    "storage": "hard_drive",
    "motherboard": "motherboard",
    "psu": "power_supply",
    "cooler": "cooler",
    "case": "case",
}


def compare_category_to_product_type(category):
    return COMPARE_CATEGORY_TO_TYPE.get(category)


def filter_products_by_compare_category(products, category):
    """Оставляет только товары выбранной категории (та же логика, что при импорте)."""
    target = compare_category_to_product_type(category)
    if not target or not products:
        return []
    filtered = []
    for item in products:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        if resolve_product_type(item) == target:
            filtered.append(item)
    return filtered

_COMPAT_DEFAULTS = {
    "motherboard": {
        "socket": "", "form_factor": "", "memory_type": "", "memory_form_factor": "",
    },
    "processor": {
        "socket": "", "power_consumption": 0, "core_count": 0, "thread_count": 0,
    },
    "graphics_card": {"power_consumption": 0, "length": 0, "memory_size": 0},
    "ram": {"memory_type": "", "memory_size": 0, "memory_form_factor": ""},
    "power_supply": {"wattage": 0},
    "cooler": {"cooler_height": 0},
    "case": {"supported_form_factors": [], "max_gpu_length": 0, "max_cooler_height": 0},
    "hard_drive": {},
}

CATEGORY_MAPPING = {
    "Видеокарты": "graphics_card", "Процессоры": "processor",
    "Материнские платы": "motherboard", "Оперативная память": "ram",
    "Корпуса": "case", "Блоки питания": "power_supply", "Кулеры": "cooler",
    "Жесткие диски": "hard_drive", "SSD M.2": "hard_drive", "SSD SATA": "hard_drive",
    "videokarty": "graphics_card", "processory": "processor",
    "materinskie-platy": "motherboard", "moduli-pamyati": "ram",
    "korpusa": "case", "bloki-pitaniya": "power_supply",
    "sistemy-ohlazhdeniya-processora": "cooler",
    "zhestkie-diski": "hard_drive", "ssd-nakopiteli": "hard_drive",
    "ssd-m2": "hard_drive", "ssd-sata": "hard_drive",
}

_CATEGORY_KEYWORDS = (
    ("graphics_card", ("видеокарт", "gpu", "graphics")),
    ("processor", ("процессор", "cpu", "processor")),
    ("motherboard", ("материнск", "motherboard", "mainboard")),
    ("ram", ("оперативн", "память", "dimm", "модуль памяти")),
    ("case", ("корпус", "case", "chassis", "tower")),
    ("power_supply", ("блок", "питан", "psu", "power supply")),
    ("cooler", ("кулер", "охлажден", "cooler", "вентилятор")),
    ("hard_drive", ("ssd", "диск", "накопител", "hdd", "жесткий", "винчестер")),
)

_NAME_KEYWORDS = (
    ("graphics_card", ("видеокарта", "gpu", "graphics", "geforce", "radeon", "gtx", "rtx")),
    ("processor", ("процессор", "cpu", "processor", "intel core", "amd ryzen", "intel pentium", "amd fx")),
    ("motherboard", ("материнская плата", "motherboard", "mainboard", "мат. плата")),
    ("power_supply", ("блок питания", "power supply", "psu")),
    ("ram", ("оперативная память", "ram", "memory", "ddr4", "ddr5", "dimm")),
    ("cooler", ("кулер", "cooler", "охлаждение", "вентилятор")),
    ("hard_drive", ("ssd", "hdd", "накопитель", "диск", "жесткий")),
    ("case", ("корпус", "case", "tower", "chassis")),
)


def ensure_compatibility_characteristics(product_data):
    characteristics = product_data.setdefault("characteristics", {})
    defaults = _COMPAT_DEFAULTS.get(product_data.get("product_type", "other"), {})
    for field, default in defaults.items():
        characteristics.setdefault(field, default)


def detect_vendor_from_url(url):
    if not url:
        return "unknown"
    url_lower = url.lower()
    if "citilink.ru" in url_lower:
        return "citilink"
    if "dns-shop.ru" in url_lower:
        return "dns"
    return "unknown"


def infer_vendor(product, source="unknown"):
    vendor = detect_vendor_from_url(product.get("url", "") or product.get("product_url", ""))
    if vendor != "unknown":
        return vendor
    source_lower = str(source or "").lower()
    if "citilink" in source_lower or "citi" in source_lower:
        return "citilink"
    if "dns" in source_lower:
        return "dns"
    images = product.get("images")
    if product.get("slug") and isinstance(images, dict) and "citilink" in images:
        return "citilink"
    return "unknown"


def ensure_import_identity(std_product, raw_product, vendor):
    if (std_product.get("product_url") or "").strip():
        return
    product_id = std_product.get("id") or raw_product.get("id") or raw_product.get("article")
    product_name = std_product.get("product_name") or raw_product.get("name") or "unknown"
    product_type = std_product.get("product_type") or "other"
    if product_id:
        std_product["product_url"] = f"import://{vendor}/{product_type}/{product_id}"
    else:
        safe_name = re.sub(r"\s+", "-", product_name.strip().lower())[:180]
        std_product["product_url"] = f"import://{vendor}/{product_type}/{safe_name}"


def _normalize_categories(raw_categories):
    if isinstance(raw_categories, list):
        return raw_categories
    return [raw_categories] if raw_categories else []


def _map_category_label(label):
    if not label:
        return None
    text = str(label).strip()
    return CATEGORY_MAPPING.get(text) or CATEGORY_MAPPING.get(text.lower())


def _match_keywords(text, rules):
    lower = text.lower()
    for product_type, keywords in rules:
        if any(kw in lower for kw in keywords):
            return product_type
    return None


def detect_product_type(product_name, product_categories=None):
    if product_categories:
        for category in product_categories:
            cat_name = category.get("name", "") if isinstance(category, dict) else str(category)
            mapped = _map_category_label(cat_name)
            if mapped:
                return mapped
            matched = _match_keywords(cat_name, _CATEGORY_KEYWORDS)
            if matched:
                return matched
    name_lower = (product_name or "").lower()
    if not name_lower:
        return "other"
    if name_lower.endswith(" вт") or " вт " in name_lower:
        return "power_supply"
    return _match_keywords(name_lower, _NAME_KEYWORDS) or "other"


def resolve_product_type(product, folder_name=None, strict=False):
    explicit = product.get("product_type") or product.get("detected_product_type")
    if explicit:
        return explicit
    if folder_name:
        mapped = _map_category_label(folder_name)
        if mapped:
            return mapped
    category_field = product.get("category")
    if category_field and not isinstance(category_field, list):
        mapped = _map_category_label(category_field)
        if mapped:
            return mapped
    categories = _normalize_categories(product.get("categories") or product.get("category"))
    detected = detect_product_type(product.get("name", ""), categories)
    if detected != "other":
        return detected
    return None if strict else "other"


def load_products_from_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "products" in data:
        return data["products"]
    if isinstance(data, list):
        return data
    return [data] if data else []


def prepare_std_product(raw, vendor, *, folder_name=None, strict=False, source_label=None):
    """Стандартизирует один товар. strict=True и без типа → None."""
    if strict and not raw.get("name") and not folder_name:
        return None
    product_type = resolve_product_type(raw, folder_name=folder_name, strict=strict)
    if strict and not product_type:
        return None
    std = standardize_characteristics(raw, vendor)
    std["vendor"] = vendor
    std["product_type"] = product_type
    if source_label:
        std["source"] = source_label
    ensure_import_identity(std, raw, vendor)
    return std


def dedupe_std_products(products):
    seen = {}
    for product in products:
        key = product.get("product_url") or product.get("url", "")
        if not key:
            name_key = product.get("product_name") or product.get("name", "")
            key = f"__nourl__{name_key}" if name_key else ""
        if key:
            seen[key] = product
    unique = list(seen.values())
    return unique, len(products) - len(unique)


def upsert_unified_product(unified_product):
    existing = None
    product_url = (unified_product.product_url or "").strip()
    if product_url:
        existing = UnifiedProduct.query.filter_by(product_url=product_url).first()
    if not existing:
        existing = UnifiedProduct.query.filter_by(
            vendor=unified_product.vendor,
            product_type=unified_product.product_type,
            product_name=unified_product.product_name,
        ).first()
    if existing:
        existing.product_name = unified_product.product_name
        existing.price_discounted = unified_product.price_discounted
        existing.price_original = unified_product.price_original
        existing.rating = unified_product.rating
        existing.number_of_reviews = unified_product.number_of_reviews
        existing.images = unified_product.images
        existing.characteristics = unified_product.characteristics
        existing.availability = unified_product.availability
        existing.category = unified_product.category
        existing.product_type = unified_product.product_type
        existing.vendor = unified_product.vendor
        return "updated", existing
    db.session.add(unified_product)
    return "added", unified_product


def persist_std_products(std_products, *, log_every=100):
    added_count = updated_count = error_count = 0
    for idx, product_data in enumerate(std_products):
        try:
            ensure_compatibility_characteristics(product_data)
            unified = convert_to_unified_product(product_data)
            action, _ = upsert_unified_product(unified)
            db.session.commit()
            if action == "added":
                added_count += 1
            else:
                updated_count += 1
            if log_every and idx > 0 and idx % log_every == 0:
                print(f"  сохранено {idx} (добавлено: {added_count}, обновлено: {updated_count})")
        except Exception as e:
            error_count += 1
            print(f"Ошибка сохранения [{idx}] {product_data.get('product_name', '?')}: {e}")
            traceback.print_exc()
            db.session.rollback()
    db.session.commit()
    return {
        "added_count": added_count,
        "updated_count": updated_count,
        "error_count": error_count,
        "total_products": len(std_products),
        "success": error_count < len(std_products),
    }


def print_type_stats():
    print("\nСтатистика по типам продуктов:")
    for product_type in PRODUCT_TYPES:
        count = UnifiedProduct.query.filter_by(product_type=product_type).count()
        if count:
            print(f"  {product_type}: {count}")


def collect_from_json_files(pattern, vendor, *, strict=False, require_name=False):
    """Читает glob-файлы и возвращает список std_product."""
    collected = []
    paths = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    for path in paths:
        try:
            print(f"  {path}")
            products = load_products_from_json(path)
            print(f"    товаров: {len(products)}")
            for raw in products:
                if require_name and not raw.get("name"):
                    continue
                std = prepare_std_product(raw, vendor, strict=strict)
                if std:
                    collected.append(std)
        except Exception as e:
            print(f"    ошибка: {e}")
            traceback.print_exc()
    return collected


def collect_citilink_category_dirs(roots):
    collected = []
    for root in roots:
        if not os.path.isdir(root):
            continue
        print(f"  Citilink каталоги: {root}")
        for category_dir in os.listdir(root):
            category_path = os.path.join(root, category_dir)
            products_file = os.path.join(category_path, "Товары.json")
            if not os.path.isdir(category_path) or not os.path.isfile(products_file):
                continue
            product_type = resolve_product_type({}, folder_name=category_dir, strict=True)
            if not product_type:
                print(f"    пропуск неизвестной категории: {category_dir}")
                continue
            try:
                products = load_products_from_json(products_file)
                print(f"    {category_dir} ({product_type}): {len(products)}")
                for raw in products:
                    std = prepare_std_product(raw, "citilink", folder_name=category_dir)
                    if std:
                        collected.append(std)
            except Exception as e:
                print(f"    ошибка {products_file}: {e}")
                traceback.print_exc()
    return collected


def discover_import_paths(project_root=None):
    """Все пути/паттерны для полного импорта (порядок = приоритет при дедупе)."""
    root = Path(project_root or os.getcwd())
    patterns = []

    if os.environ.get("IMPORT_LOCAL_DNS_FILES", "1").strip() != "0":
        patterns.append((str(root / "data/local_parser_data_*.json"), "dns", True, True))

    patterns.extend([
        (str(root / "data/citilink/citilink_*.json"), "citilink", True, False),
        (str(root / "data/dns/dns_*.json"), "dns", False, False),
        (str(root / "data/parser_backups/*/dns/product_data.json"), "dns", False, False),
        (str(root / "app/utils/old_dns_parser/product_data.json"), "dns", False, False),
    ])

    citilink_roots = []
    primary = root / "app/utils/Citi_parser/data"
    if primary.is_dir():
        citilink_roots.append(str(primary))
    backup_glob = str(root / "data/parser_backups/*/citilink/data")
    citilink_roots.extend(sorted(glob.glob(backup_glob), key=os.path.getmtime, reverse=True))
    return patterns, citilink_roots
