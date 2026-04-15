"""
Повтор запросов DNS как у браузера после прохождения Qrator.

Как снять данные из Chrome (или Edge):
1. F12 → вкладка «Сеть» / Network.
2. Обновите страницу товара (уже после зелёной проверки Qrator).
3. Клик по запросу документа (тип document, ваш URL товара) ИЛИ по XHR,
   который отдаёт JSON с товаром.
4. ПКМ → Копировать → «Copy as cURL» (bash) — можно вставить в блокнот
   и вытащить оттуда заголовок Cookie и User-Agent.

Вариант A — JSON-файл (удобно хранить вне репозитория):

    {
      "Cookie": "имя=значение; другое=значение; ...",
      "User-Agent": "то же, что в браузере"
    }

Дополнительно можно добавить любые заголовки:
    "Referer": "https://www.dns-shop.ru/",
    "Accept": "text/html,application/xhtml+xml,..."

Запуск:
    .venv\\Scripts\\python.exe app/utils/DNS_parsing/dns_replay_session.py \\
        --url https://www.dns-shop.ru/product/.../ \\
        --headers-file path/to/secret_headers.json \\
        --output page.html

Потом сырой HTML можно прогнать через extract_from_html из dns_parser_v2
или просто открыть в браузере.

Внутренние API: в Network включите фильтр «Fetch/XHR», откройте карточку товара.
Ищите ответы с JSON (имя часто содержит product, card, detail, goods).
URL и метод скопируйте «Copy as cURL» — те же Cookie обычно обязательны;
иногда нужны anti-CSRF заголовки из первого ответа HTML.

Ограничения: сессия протухает (минуты–часы–сутки), после логаута / смены IP
Qrator может снова попросить проверку — тогда обновляете Cookie в JSON.

Правовая сторона: только для своих тестов и с соблюдением правил сайта / оферты.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description="GET страницы DNS с заголовками из браузера")
    p.add_argument("--url", required=True, help="URL товара или XHR")
    p.add_argument(
        "--headers-file",
        required=True,
        help="JSON с полями Cookie, User-Agent и опционально другими заголовками",
    )
    p.add_argument("--output", default="", help="Куда сохранить тело ответа (UTF-8)")
    args = p.parse_args()

    path = Path(args.headers_file)
    if not path.is_file():
        print(f"Файл не найден: {path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(path.read_text(encoding="utf-8"))
    if "Cookie" not in data and "cookie" not in data:
        print("В JSON нужен ключ «Cookie» (строка как в DevTools)", file=sys.stderr)
        sys.exit(1)

    cookie = data.get("Cookie") or data.get("cookie", "")
    ua = data.get("User-Agent") or data.get("user-agent") or (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    headers = {
        "User-Agent": ua,
        "Cookie": cookie,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    for k, v in data.items():
        if k in ("Cookie", "cookie", "User-Agent", "user-agent"):
            continue
        if isinstance(v, str) and k:
            headers[k] = v

    try:
        from curl_cffi import requests as curl_requests
    except ImportError:
        print("Установите: pip install curl-cffi", file=sys.stderr)
        sys.exit(1)

    r = curl_requests.get(
        args.url,
        headers=headers,
        impersonate="chrome124",
        timeout=30,
        allow_redirects=True,
    )
    print(f"HTTP {r.status_code}, {len(r.text)} байт")

    if args.output:
        out = Path(args.output)
        out.write_text(r.text, encoding="utf-8")
        print(f"Сохранено: {out.resolve()}")

    if r.status_code != 200:
        sys.exit(2)


if __name__ == "__main__":
    main()
