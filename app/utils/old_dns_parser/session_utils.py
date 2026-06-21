"""Сессионные дампы DNS-парсера (один запуск = один файл)."""
import glob
import json
import os
from datetime import datetime
from pathlib import Path

SESSION_DIR_NAME = "data/dns"
LAST_SESSION_FILE = "last_session.txt"


def ensure_session_dir(base_dir=None):
    base = Path(base_dir or os.getcwd())
    session_dir = base / SESSION_DIR_NAME
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def start_dns_session(category_name=None, base_dir=None):
    """Создаёт пустой JSON-дамп для текущего запуска парсера."""
    base = Path(base_dir or os.getcwd())
    session_dir = ensure_session_dir(base)
    cat = (category_name or "all").strip() or "all"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_file = session_dir / f"dns_{cat}_{timestamp}.json"
    session_file.write_text("[]", encoding="utf-8")
    session_path = str(session_file.resolve())
    os.environ["DNS_SESSION_FILE"] = session_path
    (session_dir / LAST_SESSION_FILE).write_text(session_path, encoding="utf-8")
    return session_path


def get_active_session_file():
    path = os.environ.get("DNS_SESSION_FILE", "").strip()
    if path and os.path.isfile(path):
        return path
    return None


def find_latest_dns_dump(project_root=None):
    """Последний дамп dns_*.json или путь из last_session.txt."""
    root = Path(project_root or os.getcwd())
    candidates = []

    last_session = root / "app/utils/old_dns_parser/data/dns" / LAST_SESSION_FILE
    if last_session.is_file():
        try:
            path = last_session.read_text(encoding="utf-8").strip()
            if path and os.path.isfile(path):
                return path
        except OSError:
            pass

    patterns = [
        root / "app/utils/old_dns_parser/data/dns/dns_*.json",
        root / "data/dns/dns_*.json",
    ]
    for pattern in patterns:
        candidates.extend(glob.glob(str(pattern)))
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)
