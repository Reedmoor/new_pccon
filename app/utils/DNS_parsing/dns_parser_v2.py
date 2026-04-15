"""
DNS Parser v2 — многостратегийный парсер с замером скорости и антибот-защитой.

DNS защищён Qrator (ответ 401 + скрипт /__qrator/qauth_*.js). Без реального Chrome
это почти не обойти: A/B/C часто бесполезны. Рабочая стратегия — D (undetected-chromedriver).

  A) curl_cffi      — быстро, но Qrator блокирует (без куки после браузера).
  B) Playwright     — headless Chromium не проходит Qrator.
  C) Playwright+    — то же.
  D) uc Chrome      — undetected_chromedriver, как в productDetailsParser. Рекомендуется.

Запуск:
    python dns_parser_v2.py --url URL --strategy D --output out.json
    python dns_parser_v2.py --bench --url URL          # A,B,C + D

Видимый браузер (если headless не проходит):
    python dns_parser_v2.py --url ... --strategy D --headed
"""

import asyncio
import json
import logging
import os
import random
import re
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

# ─── логирование ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("dns_v2")

# ─── константы ────────────────────────────────────────────────────────────────
BASE_URL = "https://www.dns-shop.ru"
DEFAULT_CATEGORY_URL = BASE_URL + "/catalog/{slug}/?order=1&stock=2&p={page}"

# Популярные категории DNS (slug → product_type)
CATEGORIES = {
    "materinskie-platy-s-processorom":    "materinskie-platy",
    "materinskie-platy":                  "materinskie-platy",
    "processory":                         "processory",
    "videokarty":                         "videokarty",
    "moduli-operativnoj-pamyati":         "ram",
    "zhestkie-diski":                     "hard_drive",
    "ssd-nakopiteli":                     "hard_drive",
    "bloki-pitaniya":                     "power_supply",
    "kulery-dlya-processora":             "cooler",
    "korpusa-dlya-pk":                    "case",
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

# ─── вспомогательные функции парсинга ─────────────────────────────────────────

def _has_product_markup(html: str) -> bool:
    """
    Строгая проверка: нельзя искать просто подстроку \"Product\" — она есть в любом бандле.
    """
    if "product-card-top__name" in html:
        return True
    if "product-card-top__code" in html:
        return True
    if re.search(r'"@type"\s*:\s*"Product"', html):
        return True
    if re.search(r'"@type"\s*:\s*\[[^\]]*"Product"', html):
        return True
    if "catalog-product" in html and "product-buy__price" in html:
        return True
    if 'itemprop="name"' in html and ("product-card" in html or "product-buy" in html):
        return True
    return False


def _extract_jsonld_product(soup: BeautifulSoup) -> dict:
    """
    Достаёт объект Product из любого script[type=application/ld+json].
    Учитывает @graph, list @type, script без .string (у BS бывает пустой .string).
    """
    def _try_parse(raw: str) -> list[dict]:
        raw = (raw or "").strip()
        if not raw:
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []
        out = []

        def _is_product_type(t):
            if t == "Product":
                return True
            if isinstance(t, list):
                return any(_is_product_type(x) for x in t)
            if isinstance(t, str):
                tl = t.lower()
                return (
                    t == "Product"
                    or tl.endswith("/product")
                    or "schema.org/product" in tl
                )
            return False

        def _collect(obj: dict):
            if not isinstance(obj, dict):
                return
            if _is_product_type(obj.get("@type")):
                out.append(obj)
            for g in obj.get("@graph", []) if isinstance(obj.get("@graph"), list) else []:
                _collect(g)

        if isinstance(data, list):
            for item in data:
                _collect(item if isinstance(item, dict) else {})
        else:
            _collect(data)
        return out

    for script in soup.find_all("script"):
        typ = (script.get("type") or "").lower()
        if typ and "ld+json" not in typ:
            continue
        raw = script.string
        if not raw:
            raw = script.get_text() or ""
        if not raw and hasattr(script, "contents"):
            raw = "".join(str(c) for c in script.contents) if script.contents else ""
        objs = _try_parse(raw)
        for obj in objs:
            if obj.get("name") or obj.get("offers"):
                return obj
        if objs:
            return objs[0]
    return {}


def _schema_text(val):
    if val is None:
        return None
    if isinstance(val, str):
        s = val.strip()
        return s or None
    if isinstance(val, list) and val:
        return _schema_text(val[0])
    if isinstance(val, dict):
        return _schema_text(val.get("name") or val.get("@value") or val.get("text"))
    return None


def _price_from_offers(ld: dict):
    """Цена из schema.org offers → (discount, original)."""
    if not ld:
        return None, None
    offers = ld.get("offers")
    if isinstance(offers, list) and offers:
        offers = offers[0]
    if not isinstance(offers, dict):
        return None, None
    p = offers.get("price") or offers.get("lowPrice")
    if p is None:
        return None, None
    try:
        price = int(float(str(p).replace(",", ".").replace(" ", "")))
    except (ValueError, TypeError):
        return None, None
    return price, price


def _images_from_ld(ld: dict, existing: list) -> list:
    out = list(existing)
    img = ld.get("image") if ld else None
    if isinstance(img, str) and img.startswith("http"):
        if img not in out:
            out.append(img.split("?")[0])
    elif isinstance(img, list):
        for x in img[:8]:
            if isinstance(x, str) and x.startswith("http"):
                u = x.split("?")[0]
                if u not in out:
                    out.append(u)
            elif isinstance(x, dict):
                u = x.get("url") or x.get("@content")
                if isinstance(u, str) and u.startswith("http"):
                    u = u.split("?")[0]
                    if u not in out:
                        out.append(u)
    return out


def detect_block(html: str) -> str | None:
    """
    Определяет тип блокировки по HTML-странице.
    Внимание: «выбор города», modal-city часто встречаются в JS-бандле DNS —
    нельзя считать это блокировкой, если уже есть разметка товара.
    """
    h = html[:12000].lower()
    hl = html.lower()
    has_prod = _has_product_markup(html)

    # Qrator: только если нет карточки товара
    if "__qrator" in hl or "/__qrator/" in hl or "qauth_" in hl:
        if not has_prod:
            return "Qrator WAF — используйте --strategy D (undetected Chrome)"

    if "cloudflare" in h and ("challenge" in h or "ray id" in h):
        if not has_prod:
            return "Cloudflare challenge"
    if ("captcha" in h or "recaptcha" in h) and not has_prod:
        return "CAPTCHA"
    # Город: только без товара (иначе ложное срабатывание на строках в бандле)
    if not has_prod:
        if "city-select-popup_is-opened" in hl or "city-confirm_visible" in hl:
            return "Модалка выбора города"
        if "подтвердите город" in hl and "modal" in h:
            return "Модалка выбора города"
    if "403 forbidden" in h or "<title>403" in h:
        if not has_prod:
            return "403 Forbidden"
    if ("доступ ограничен" in h or "access denied" in h) and not has_prod:
        return "Access Denied"
    if len(html) < 2000 and not has_prod:
        return f"Короткий ответ ({len(html)} байт), вероятно челлендж/ошибка"
    return None


def dump_debug_html(html: str, strategy: str, url: str):
    """Сохраняет HTML для ручного анализа."""
    ts = datetime.now().strftime("%H%M%S")
    slug = re.sub(r"[^\w]", "_", url[-40:])
    fname = Path(f"dns_debug_{strategy}_{ts}_{slug}.html")
    fname.write_text(html, encoding="utf-8")
    log.warning(f"  ↳ HTML сохранён для отладки: {fname.resolve()}")
    return fname


def extract_from_html(html: str, url: str, debug: bool = False, strategy: str = "?") -> dict | None:
    """Извлекает данные товара из HTML-страницы."""
    # Проверяем блокировку ДО парсинга
    block_reason = detect_block(html)
    if block_reason:
        log.warning(f"  ⛔ Блокировка: {block_reason}")
        if debug:
            dump_debug_html(html, strategy, url)
        return None

    soup = BeautifulSoup(html, "lxml")

    ld_data = _extract_jsonld_product(soup)

    og_title = None
    og = soup.select_one('meta[property="og:title"]') or soup.select_one('meta[name="og:title"]')
    if og and og.get("content"):
        og_title = og["content"].strip()

    name = _schema_text(ld_data.get("name")) if ld_data else None
    if not name:
        for sel in (
            ".product-card-top__name",
            "[class*='product-card-top__name']",
            "[itemprop=name]",
            "h1.product-card-top__title",
            "h1",
        ):
            el = soup.select_one(sel)
            if el:
                t = el.get_text(strip=True)
                if t and len(t) > 2 and t.lower() not in ("dns", "каталог", "интернет-магазин"):
                    name = t
                    break
    if not name:
        name = og_title
    if not name and soup.title and soup.title.string:
        t = re.sub(r"\s*[—–|-]\s*DNS[-\s].*$", "", soup.title.string, flags=re.I).strip()
        if len(t) > 3:
            name = t
    if not name:
        log.warning(f"  ⚠ Имя товара не найдено в {url}")
        if debug:
            dump_debug_html(html, strategy, url)
        return None

    # Цены: DOM, затем JSON-LD
    price_discounted = _clean_price(
        soup.select_one(".product-buy__price_active") or
        soup.select_one("[data-price]")
    )
    price_original = _clean_price(
        soup.select_one(".product-buy__prev")
    ) or price_discounted
    if price_discounted is None and ld_data:
        pd, po = _price_from_offers(ld_data)
        price_discounted = pd
        price_original = po or pd

    # Рейтинг из JSON-LD
    agg = ld_data.get("aggregateRating", {}) if ld_data else {}
    if isinstance(agg, dict):
        rv = agg.get("ratingValue")
        rc = agg.get("reviewCount")
        rating = float(rv) if rv is not None else None
        try:
            reviews = int(rc) if rc is not None else None
        except (ValueError, TypeError):
            reviews = None
    else:
        rating, reviews = None, None

    # Изображения — слайдер + JSON-LD
    images = []
    for img in soup.select(".product-images-slider__img"):
        src = img.get("src") or img.get("data-src") or ""
        src = src.split("?")[0]
        if src and not src.endswith(".svg") and src not in images:
            images.append(src)
        if len(images) >= 5:
            break
    images = _images_from_ld(ld_data, images)

    # Характеристики
    characteristics = {}
    for group in soup.select(".product-characteristics__group"):
        title_el = group.select_one(".product-characteristics__group-title")
        group_name = title_el.text.strip() if title_el else "Общее"
        characteristics[group_name] = []
        for spec in group.select(".product-characteristics__spec"):
            key_el = spec.select_one(".product-characteristics__spec-title-content")
            val_el = spec.select_one(".product-characteristics__spec-value")
            if key_el and val_el:
                characteristics[group_name].append({
                    "title": " ".join(key_el.text.split()),
                    "value": " ".join(val_el.text.split()),
                })

    # Категории (хлебные крошки)
    categories = []
    for item in soup.select(".breadcrumb-list__item"):
        link = item.select_one("a.ui-link")
        if link:
            span = link.find("span")
            categories.append({
                "name": span.text.strip() if span else link.text.strip(),
                "url": BASE_URL + link.get("href", ""),
            })
    if len(categories) > 2:
        categories = categories[1:-1]

    return {
        "url": url,
        "name": name,
        "price_discounted": price_discounted,
        "price_original": price_original,
        "rating": rating,
        "number_of_reviews": reviews,
        "images": images,
        "characteristics": characteristics,
        "categories": categories,
        "parsed_at": datetime.now().isoformat(),
    }


def _safe_text(soup, tag, cls):
    el = soup.find(tag, class_=cls)
    return el.text.strip() if el else None


def _clean_price(el):
    if el is None:
        return None
    text = el.get("data-price") or el.text
    digits = re.sub(r"\D", "", text or "")
    return int(digits) if digits else None


def extract_product_links(html: str) -> list[str]:
    """Извлекает ссылки на товары со страницы каталога."""
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.select("a.catalog-product__name"):
        href = a.get("href", "")
        if href:
            links.append(BASE_URL + href if href.startswith("/") else href)
    # убираем дубли, сохраняем порядок
    return list(dict.fromkeys(links))


# ══════════════════════════════════════════════════════════════════════════════
#  СТРАТЕГИЯ A — curl_cffi (TLS-фингерпринт Chrome, без браузера)
# ══════════════════════════════════════════════════════════════════════════════

class StrategyA:
    """
    curl_cffi — TLS-фингерпринт Chrome без запуска браузера.
    DNS требует warm-up сессии: сначала идём на главную (получаем куки),
    потом на товар. Без JS — данные берём из JSON-LD в HTML.
    """
    name = "A: curl_cffi (TLS-spoof, no JS)"

    def __init__(self, debug: bool = False):
        self.debug = debug
        try:
            from curl_cffi.requests import AsyncSession
            self._AsyncSession = AsyncSession
        except ImportError:
            raise RuntimeError("curl_cffi не установлен: pip install curl-cffi")

    def _headers(self, referer: str = "https://www.dns-shop.ru/"):
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                      "image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": referer,
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
        }

    async def _warm_up(self, session):
        """Warm-up: заходим на главную страницу DNS чтобы получить куки."""
        try:
            await session.get(
                BASE_URL + "/",
                headers=self._headers(referer="https://www.google.com/"),
                impersonate="chrome124",
                timeout=10,
                allow_redirects=True,
            )
            # Устанавливаем куку города вручную
            session.cookies.set("selected-city", "moskva", domain=".dns-shop.ru")
            session.cookies.set("city_confirmed", "1", domain=".dns-shop.ru")
            await asyncio.sleep(random.uniform(0.5, 1.0))
        except Exception as e:
            log.warning(f"[A] warm-up: {e}")

    async def fetch(self, url: str, session, referer: str = BASE_URL + "/") -> str | None:
        try:
            resp = await session.get(
                url,
                headers=self._headers(referer=referer),
                timeout=15,
                impersonate="chrome124",
                allow_redirects=True,
            )
            log.debug(f"[A] {resp.status_code} {url}")
            if resp.status_code == 200:
                return resp.text
            log.warning(f"[A] HTTP {resp.status_code} для {url}")
            if self.debug:
                dump_debug_html(resp.text, "A", url)
            return None
        except Exception as e:
            log.error(f"[A] Ошибка запроса {url}: {e}")
            return None

    async def parse_product(self, url: str, session) -> dict | None:
        html = await self.fetch(url, session, referer=BASE_URL + "/catalog/")
        if not html:
            return None
        result = extract_from_html(html, url, debug=self.debug, strategy="A")
        return result

    async def get_product_links(self, category_slug: str, limit: int, session) -> list[str]:
        links = []
        page = 1
        while len(links) < limit:
            url = DEFAULT_CATEGORY_URL.format(slug=category_slug, page=page)
            html = await self.fetch(url, session, referer=BASE_URL + "/catalog/")
            if not html:
                break
            page_links = extract_product_links(html)
            if not page_links:
                break
            for l in page_links:
                if l not in links:
                    links.append(l)
            if len(page_links) < 12:
                break
            page += 1
            await asyncio.sleep(random.uniform(0.8, 1.5))
        return links[:limit]

    async def run(self, urls: list[str], concurrency: int = 3) -> list[dict]:
        from curl_cffi.requests import AsyncSession
        results = []
        sem = asyncio.Semaphore(concurrency)

        async def fetch_one(url, session):
            async with sem:
                await asyncio.sleep(random.uniform(0.5, 1.2))
                return await self.parse_product(url, session)

        async with AsyncSession() as session:
            await self._warm_up(session)
            tasks = [fetch_one(u, session) for u in urls]
            for coro in asyncio.as_completed(tasks):
                res = await coro
                if res:
                    results.append(res)
                    log.info(f"[A] ✓ {res['name'][:60]}")
        return results


# ══════════════════════════════════════════════════════════════════════════════
#  СТРАТЕГИЯ B — Playwright headless + stealth
# ══════════════════════════════════════════════════════════════════════════════

STEALTH_JS = """
// --- Playwright stealth patches ---
// 1. Убираем webdriver
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

// 2. Правдоподобные plugins
const makePlugin = (name, filename, desc) => ({name, filename, description: desc, length: 0});
Object.defineProperty(navigator, 'plugins', {get: () => [
    makePlugin('Chrome PDF Plugin','internal-pdf-viewer','Portable Document Format'),
    makePlugin('Chrome PDF Viewer','mhjfbmdgcfjbbpaeojofohoefgiehjai',''),
    makePlugin('Native Client','internal-nacl-plugin',''),
]});

// 3. Chrome runtime
window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}, app: {}};

// 4. Языки
Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU','ru','en-US','en']});

// 5. Platform
Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});

// 6. Hardware concurrency (реалистичное)
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});

// 7. Permission API — не отдаём denied сразу
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (params) =>
    (params.name === 'notifications')
        ? Promise.resolve({state: Notification.permission})
        : originalQuery(params);

// 8. Скрываем automation флаги
['__driver_evaluate','__webdriver_evaluate','__selenium','__driver_unwrapped',
 '__webdriver_unwrapped','__nightmare','callPhantom','_phantom'].forEach(k => {
    try { delete window[k]; } catch(e) {}
});
"""


class StrategyB:
    """
    Playwright headless + полные stealth-патчи + обработка модалки города DNS.
    Параллельные вкладки для скорости.
    """
    name = "B: Playwright headless + stealth"

    def __init__(self, concurrency: int = 3, debug: bool = False):
        self.concurrency = concurrency
        self.debug = debug

    async def _new_context(self, browser):
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            viewport={"width": random.choice([1280, 1366, 1440, 1920]),
                      "height": random.choice([720, 768, 900, 1080])},
            extra_http_headers={
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            # Отключаем WebRTC leak
            ignore_https_errors=True,
        )
        # Куки города — устанавливаем ДО перехода на страницу
        await context.add_cookies([
            {"name": "selected-city",   "value": "moskva",   "domain": ".dns-shop.ru", "path": "/"},
            {"name": "city_confirmed",  "value": "1",        "domain": ".dns-shop.ru", "path": "/"},
            {"name": "region_id",       "value": "Moscow",   "domain": ".dns-shop.ru", "path": "/"},
        ])
        await context.add_init_script(STEALTH_JS)
        return context

    async def _dismiss_city_modal(self, page):
        """Закрывает модалку выбора города, если она появилась."""
        selectors = [
            "button.modal-confirm-city__agree",
            "button.confirm-city-btn",
            ".city-select__confirm",
            "button:has-text('Да, верно')",
            "button:has-text('Подтвердить')",
            "a:has-text('Москва')",
        ]
        for sel in selectors:
            try:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    await asyncio.sleep(0.5)
                    log.debug(f"[B] Закрыта модалка города: {sel}")
                    return
            except Exception:
                continue

    async def fetch_page(self, url: str, browser, label: str = "B") -> str | None:
        context = await self._new_context(browser)
        page = await context.new_page()
        try:
            # Переходим и ждём загрузки сети
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            if resp and resp.status not in (200, 304):
                log.warning(f"[{label}] HTTP {resp.status} для {url}")

            # Закрываем модалку города
            await self._dismiss_city_modal(page)
            await asyncio.sleep(random.uniform(0.5, 1.0))

            # Ждём нужного элемента (несколько запасных вариантов)
            content_sel = (
                "h1, "
                ".product-card-top__name, "
                ".catalog-product__name, "
                "[class*='product-card-top']"
            )
            try:
                await page.wait_for_selector(content_sel, timeout=10000)
            except Exception:
                log.warning(f"[{label}] Контент-селектор не появился за 10s: {url}")

            html = await page.content()

            if self.debug:
                block = detect_block(html)
                if block:
                    log.warning(f"  ⛔ [{label}] {block}")
                    dump_debug_html(html, label, url)

            return html
        except Exception as e:
            log.error(f"[{label}] Ошибка загрузки {url}: {e}")
            return None
        finally:
            await page.close()
            await context.close()

    async def parse_product(self, url: str, browser) -> dict | None:
        html = await self.fetch_page(url, browser)
        if not html:
            return None
        return extract_from_html(html, url, debug=self.debug, strategy="B")

    async def get_product_links(self, category_slug: str, limit: int, browser) -> list[str]:
        links = []
        page_num = 1
        while len(links) < limit:
            url = DEFAULT_CATEGORY_URL.format(slug=category_slug, page=page_num)
            html = await self.fetch_page(url, browser)
            if not html:
                break
            page_links = extract_product_links(html)
            if not page_links:
                log.warning(f"[B] Нет ссылок на странице {page_num}: {url}")
                break
            for l in page_links:
                if l not in links:
                    links.append(l)
            log.info(f"[B] Страница {page_num}: +{len(page_links)} ссылок (итого {len(links)})")
            if len(page_links) < 12:
                break
            page_num += 1
            await asyncio.sleep(random.uniform(1.2, 2.5))
        return links[:limit]

    def _browser_args(self):
        return [
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-dev-shm-usage",
            "--lang=ru-RU",
            f"--window-size={random.choice([1280,1366,1440])},{random.choice([720,768,900])}",
        ]

    async def run(self, urls: list[str]) -> list[dict]:
        from playwright.async_api import async_playwright
        results = []
        sem = asyncio.Semaphore(self.concurrency)

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=self._browser_args(),
            )

            async def fetch_one(url):
                async with sem:
                    res = await self.parse_product(url, browser)
                    if res:
                        log.info(f"[B] ✓ {res['name'][:60]}")
                    return res

            tasks = [fetch_one(u) for u in urls]
            for coro in asyncio.as_completed(tasks):
                res = await coro
                if res:
                    results.append(res)

            await browser.close()
        return results


# ══════════════════════════════════════════════════════════════════════════════
#  СТРАТЕГИЯ C — Playwright + human behavior
# ══════════════════════════════════════════════════════════════════════════════

class StrategyC(StrategyB):
    """
    Playwright с имитацией поведения человека:
    прокрутка страницы, случайные паузы, движение мыши.
    Самый надёжный, но медленный. Запускать в 1-2 потока.
    """
    name = "C: Playwright + human behavior"

    def __init__(self, debug: bool = False):
        super().__init__(concurrency=2, debug=debug)

    async def _human_scroll(self, page):
        """Плавная прокрутка страницы, как у человека."""
        total_height = await page.evaluate("document.body.scrollHeight")
        current = 0
        step = random.randint(200, 400)
        while current < total_height * 0.8:
            current = min(current + step, total_height)
            await page.evaluate(f"window.scrollTo(0, {current})")
            await asyncio.sleep(random.uniform(0.05, 0.15))

    async def _human_mouse(self, page):
        """Случайное движение мыши."""
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 1200)
            y = random.randint(100, 600)
            await page.mouse.move(x, y, steps=random.randint(5, 15))
            await asyncio.sleep(random.uniform(0.05, 0.2))

    async def fetch_page(self, url: str, browser, label: str = "C") -> str | None:
        context = await self._new_context(browser)
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await self._dismiss_city_modal(page)
            await asyncio.sleep(random.uniform(1.0, 2.0))

            await self._human_mouse(page)
            await self._human_scroll(page)
            await asyncio.sleep(random.uniform(0.5, 1.0))

            content_sel = "h1, .product-card-top__name, .catalog-product__name"
            try:
                await page.wait_for_selector(content_sel, timeout=10000)
            except Exception:
                pass

            # Раскрываем все характеристики
            try:
                btn = await page.query_selector(".product-characteristics__expand")
                if btn:
                    await btn.scroll_into_view_if_needed()
                    await asyncio.sleep(0.3)
                    await btn.click()
                    await asyncio.sleep(0.8)
            except Exception:
                pass

            html = await page.content()
            if self.debug:
                block = detect_block(html)
                if block:
                    log.warning(f"  ⛔ [C] {block}")
                    dump_debug_html(html, "C", url)
            return html
        except Exception as e:
            log.error(f"[C] Ошибка загрузки {url}: {e}")
            return None
        finally:
            await page.close()
            await context.close()


# ══════════════════════════════════════════════════════════════════════════════
#  СТРАТЕГИЯ D — undetected_chromedriver (обход Qrator)
# ══════════════════════════════════════════════════════════════════════════════

def _uc_version_main():
    v = os.environ.get("DNS_UC_VERSION_MAIN", "").strip()
    if v.isdigit():
        return int(v)
    return None


def uc_fetch_page_sync(url: str, headless: bool = True, debug: bool = False) -> str | None:
    """
    Загрузка страницы через настоящий Chrome с патчами undetected_chromedriver.
    Qrator отдаёт 401 + JS; только такой браузер обычно проходит проверку.
    """
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    options = uc.ChromeOptions()
    options.add_argument("--lang=ru-RU")
    options.add_argument("--window-size=1366,768")
    options.add_argument("--disable-blink-features=AutomationControlled")
    if headless:
        options.add_argument("--headless=new")

    driver = None
    try:
        driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            version_main=_uc_version_main(),
        )
        driver.set_page_load_timeout(75)

        # Главная → сессия и Qrator; затем целевой URL
        driver.get(BASE_URL + "/")
        time.sleep(random.uniform(2.0, 3.5))
        try:
            driver.add_cookie(
                {"name": "selected-city", "value": "moskva",
                 "domain": ".dns-shop.ru", "path": "/"}
            )
            driver.add_cookie(
                {"name": "city_confirmed", "value": "1",
                 "domain": ".dns-shop.ru", "path": "/"}
            )
        except Exception:
            pass

        driver.get(url)

        def _ready(d):
            src = d.page_source or ""
            if len(src) < 10000:
                return False
            return _has_product_markup(src)

        WebDriverWait(driver, 90).until(_ready)

        # Докрутка и «Развернуть характеристики» — как в productDetailsParser
        try:
            driver.execute_script(
                "window.scrollTo(0, Math.min(1200, document.body.scrollHeight * 0.35));"
            )
            time.sleep(0.6)
            btn = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".product-characteristics__expand"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(1.0)
        except Exception:
            pass

        time.sleep(random.uniform(0.6, 1.2))
        html = driver.page_source
        return html
    except Exception as e:
        log.error(f"[D] Ошибка: {e}")
        if debug and driver:
            try:
                dump_debug_html(driver.page_source or "", "D_fail", url)
            except Exception:
                pass
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
            time.sleep(0.3)


class StrategyD:
    """undetected_chromedriver — единственная стратегия, которая обычно работает с Qrator."""

    name = "D: undetected_chromedriver (Qrator)"

    def __init__(self, headless: bool = True, debug: bool = False):
        self.headless = headless
        self.debug = debug

    async def parse_product(self, url: str) -> dict | None:
        html = await asyncio.to_thread(
            uc_fetch_page_sync, url, self.headless, self.debug
        )
        if not html:
            log.warning("[D] Браузер вернул пустой HTML")
            return None
        result = extract_from_html(html, url, debug=self.debug, strategy="D")
        if not result:
            br = detect_block(html)
            log.warning(
                "[D] Парсинг не удалился | block=%s | len=%s | has_markup=%s",
                br,
                len(html),
                _has_product_markup(html),
            )
            dump_debug_html(html, "D_fail", url)
        return result

    async def get_product_links(self, category_slug: str, limit: int) -> list[str]:
        links = []
        page_num = 1
        while len(links) < limit:
            page_url = DEFAULT_CATEGORY_URL.format(slug=category_slug, page=page_num)
            html = await asyncio.to_thread(
                uc_fetch_page_sync, page_url, self.headless, self.debug
            )
            if not html:
                break
            page_links = extract_product_links(html)
            if not page_links:
                log.warning(f"[D] Нет ссылок на стр. {page_num}")
                break
            for l in page_links:
                if l not in links:
                    links.append(l)
            log.info(f"[D] Стр. {page_num}: +{len(page_links)} (всего {len(links)})")
            if len(page_links) < 12:
                break
            page_num += 1
            await asyncio.sleep(random.uniform(2.0, 4.0))
        return links[:limit]

    async def run(self, urls: list[str]) -> list[dict]:
        results = []
        for u in urls:
            p = await self.parse_product(u)
            if p:
                results.append(p)
                log.info(f"[D] ✓ {p['name'][:60]}")
            await asyncio.sleep(random.uniform(1.0, 2.5))
        return results


# ══════════════════════════════════════════════════════════════════════════════
#  БЕНЧМАРК
# ══════════════════════════════════════════════════════════════════════════════

async def benchmark(url: str, debug: bool = False):
    """Прогоняет стратегии A–D на одном URL и выводит таблицу."""
    print(f"\n{'='*60}")
    print(f"  БЕНЧМАРК DNS парсера")
    print(f"  URL: {url}")
    print(f"  WAF: Qrator — A/B/C обычно падают; рабочая стратегия — D.")
    if debug:
        print(f"  Режим: DEBUG (HTML при ошибках сохраняется)")
    print(f"{'='*60}\n")

    strategies = []
    try:
        strategies.append(StrategyA(debug=debug))
    except RuntimeError as e:
        log.warning(f"Стратегия A недоступна: {e}")

    strategies.append(StrategyB(concurrency=1, debug=debug))
    strategies.append(StrategyC(debug=debug))
    strategies.append(StrategyD(headless=True, debug=debug))

    results = []
    for strategy in strategies:
        print(f"▶ Тестируем: {strategy.name}")
        t0 = time.perf_counter()
        product = None

        try:
            if isinstance(strategy, StrategyA):
                from curl_cffi.requests import AsyncSession
                async with AsyncSession() as session:
                    product = await strategy.parse_product(url, session)
            elif isinstance(strategy, StrategyD):
                product = await strategy.parse_product(url)
            else:
                from playwright.async_api import async_playwright
                async with async_playwright() as pw:
                    browser = await pw.chromium.launch(
                        headless=True,
                        args=["--no-sandbox",
                              "--disable-blink-features=AutomationControlled"],
                    )
                    product = await strategy.parse_product(url, browser)
                    await browser.close()
        except Exception as e:
            log.error(f"  Ошибка: {e}")

        elapsed = time.perf_counter() - t0
        success = product is not None
        name_found = product.get("name", "—")[:50] if product else "—"
        price = product.get("price_discounted", "—") if product else "—"
        images = len(product.get("images", [])) if product else 0
        chars_groups = len(product.get("characteristics", {})) if product else 0

        results.append({
            "strategy": strategy.name,
            "elapsed_s": round(elapsed, 2),
            "success": success,
            "name": name_found,
            "price": price,
            "images": images,
            "char_groups": chars_groups,
        })

        status = "✅" if success else "❌"
        print(f"  {status} Время: {elapsed:.2f}s | Товар: {name_found} | "
              f"Цена: {price} | Фото: {images} | Хар. групп: {chars_groups}\n")

    print(f"\n{'='*60}")
    print("  ИТОГ БЕНЧМАРКА")
    print(f"{'='*60}")
    print(f"{'Стратегия':<40} {'Время':>8} {'Успех':>6}")
    print("-" * 58)
    for r in results:
        ok = "✅" if r["success"] else "❌"
        print(f"{r['strategy']:<40} {r['elapsed_s']:>7.2f}s {ok:>6}")
    print(f"{'='*60}\n")
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  ОСНОВНОЙ ПОТОК
# ══════════════════════════════════════════════════════════════════════════════

async def run_parser(
    urls: list[str] | None = None,
    category_slug: str | None = None,
    strategy_name: str = "D",
    limit: int = 10,
    concurrency: int = 3,
    output: str | None = None,
    headed: bool = False,
):
    """Запускает парсер выбранной стратегией."""
    sn = strategy_name.upper()
    if sn == "A":
        strategy = StrategyA()
    elif sn == "B":
        strategy = StrategyB(concurrency=concurrency)
    elif sn == "C":
        strategy = StrategyC()
    elif sn == "D":
        strategy = StrategyD(headless=not headed, debug=False)
    else:
        raise ValueError("Выберите стратегию: A, B, C или D (рекомендуется D).")

    log.info(f"Стратегия: {strategy.name}")

    t_start = time.perf_counter()
    products = []

    # ── Получаем список URL ──────────────────────────────────────────────────
    if not urls and category_slug:
        log.info(f"Сбор ссылок из категории: {category_slug}")
        if sn == "A":
            from curl_cffi.requests import AsyncSession
            async with AsyncSession() as session:
                urls = await strategy.get_product_links(category_slug, limit, session)
        elif sn == "D":
            urls = await strategy.get_product_links(category_slug, limit)
        else:
            from playwright.async_api import async_playwright
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=True,
                    args=["--no-sandbox",
                          "--disable-blink-features=AutomationControlled"],
                )
                urls = await strategy.get_product_links(category_slug, limit, browser)
                await browser.close()
        log.info(f"Найдено {len(urls)} ссылок")

    if not urls:
        log.error("Нет URL для парсинга. Укажите --url или --category.")
        return []

    urls = list(dict.fromkeys(urls))[:limit]
    log.info(f"Парсим {len(urls)} товаров...")

    # ── Парсим товары ────────────────────────────────────────────────────────
    if sn == "A":
        products = await strategy.run(urls, concurrency=concurrency)
    else:
        products = await strategy.run(urls)

    elapsed = time.perf_counter() - t_start

    log.info(f"\n{'='*50}")
    log.info(f"Готово: {len(products)}/{len(urls)} товаров за {elapsed:.1f}s "
             f"({elapsed/max(len(urls),1):.1f}s/товар)")

    # ── Сохраняем ────────────────────────────────────────────────────────────
    if not output:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = category_slug or "manual"
        output = f"dns_parsed_{slug}_{ts}_{strategy_name}.json"

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "meta": {
                    "strategy": strategy.name,
                    "total": len(products),
                    "elapsed_s": round(elapsed, 2),
                    "per_item_s": round(elapsed / max(len(urls), 1), 2),
                    "parsed_at": datetime.now().isoformat(),
                    "category": category_slug,
                },
                "products": products,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    log.info(f"Результат сохранён: {output_path.resolve()}")
    return products


# ══════════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="DNS Parser v2 — многостратегийный парсер с антибот-защитой",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  # Рекомендуется (обход Qrator):
  python dns_parser_v2.py --url https://www.dns-shop.ru/product/... --strategy D

  # Если headless не проходит — окно браузера:
  python dns_parser_v2.py --url ... --strategy D --headed

  # Сравнить A,B,C,D (D обычно единственная ✅):
  python dns_parser_v2.py --bench --url https://www.dns-shop.ru/product/...

Стратегии:
  A — curl_cffi (Qrator обычно блокирует)
  B/C — Playwright (Qrator обычно блокирует headless)
  D — undetected_chromedriver (рабочий вариант для dns-shop.ru)

Доступные категории:
""" + "\n".join(f"  {k}" for k in CATEGORIES)
    )

    parser.add_argument("--url", help="URL конкретного товара или списка (через запятую)")
    parser.add_argument("--category", help="Slug категории DNS (см. список выше)")
    parser.add_argument("--strategy", default="D", choices=["A", "B", "C", "D"],
                        help="Стратегия (default: D — undetected Chrome, обход Qrator)")
    parser.add_argument("--limit", type=int, default=10,
                        help="Максимум товаров (default: 10)")
    parser.add_argument("--concurrency", type=int, default=3,
                        help="Параллельных запросов (default: 3, только для A/B)")
    parser.add_argument("--output", help="Путь к выходному JSON-файлу")
    parser.add_argument("--bench", action="store_true",
                        help="Запустить бенчмарк всех стратегий на одном URL")
    parser.add_argument("--debug", action="store_true",
                        help="Сохранять HTML при блокировке/ошибке (для анализа)")
    parser.add_argument("--headed", action="store_true",
                        help="Реальное окно Chrome (для стратегии D, если headless не проходит)")

    args = parser.parse_args()

    if args.bench:
        if not args.url:
            parser.error("--bench требует --url")
        asyncio.run(benchmark(args.url, debug=args.debug))
        return

    urls = None
    if args.url:
        urls = [u.strip() for u in args.url.split(",")]

    if not urls and not args.category:
        parser.print_help()
        print("\n⚠ Укажите --url или --category")
        sys.exit(1)

    asyncio.run(run_parser(
        urls=urls,
        category_slug=args.category,
        strategy_name=args.strategy,
        limit=args.limit,
        concurrency=args.concurrency,
        output=args.output,
        headed=args.headed,
    ))


if __name__ == "__main__":
    main()
