"""Печатает путь к последнему DNS-дампу для bat-скриптов."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DNS_UTILS = ROOT / "app" / "utils" / "old_dns_parser"
sys.path.insert(0, str(DNS_UTILS))

from session_utils import find_latest_dns_dump  # noqa: E402

if __name__ == "__main__":
    path = find_latest_dns_dump(ROOT)
    if not path:
        sys.exit(1)
    print(path)
