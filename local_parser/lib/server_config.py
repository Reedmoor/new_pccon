"""Единая конфигурация URL сервера для локального парсера и загрузки данных."""

import json
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent
_DEFAULT_URL = "https://pcconf.ru"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config() -> dict:
    server_json = _BASE / "config" / "server.json"
    if server_json.exists():
        data = _read_json(server_json)
        return {
            "server_url": data.get("server_url", _DEFAULT_URL),
            "upload_endpoint": data.get("upload_endpoint", "/api/upload-products"),
            "health_endpoint": data.get("health_endpoint", "/api/health"),
            "local_dev_url": data.get("local_dev_url", "http://127.0.0.1:5000"),
        }

    remote_json = _BASE / "config" / "remote_config.json"
    if remote_json.exists():
        data = _read_json(remote_json)
        return {
            "server_url": data.get("server_url")
            or data.get("remote_server", {}).get("url", _DEFAULT_URL),
            "upload_endpoint": data.get("endpoints", {}).get(
                "upload", "/api/upload-products"
            ),
            "health_endpoint": data.get("endpoints", {}).get("health", "/api/health"),
            "local_dev_url": "http://127.0.0.1:5000",
        }

    return {
        "server_url": _DEFAULT_URL,
        "upload_endpoint": "/api/upload-products",
        "health_endpoint": "/api/health",
        "local_dev_url": "http://127.0.0.1:5000",
    }


def get_server_url() -> str:
    return str(load_config()["server_url"]).rstrip("/")


def get_upload_endpoint() -> str:
    return load_config().get("upload_endpoint", "/api/upload-products")


def get_health_endpoint() -> str:
    return load_config().get("health_endpoint", "/api/health")


def get_local_dev_url() -> str:
    return str(load_config().get("local_dev_url", "http://127.0.0.1:5000")).rstrip("/")
