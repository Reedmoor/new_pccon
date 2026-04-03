"""
DNS Parser v2 — многостратегийный парсер с замером скорости и антибот-защитой.

Три стратегии (от быстрой к надёжной):
  A) curl_cffi  — TLS-фингерпринт настоящего Chrome, без браузера. Самый быстрый.
  B) Playwright — асинхронный headless Chromium со stealth-патчами.
  C) Playwright + human — Playwright с имитацией поведения пользователя (скролл, паузы).

Запуск:
    python dns_parser_v2.py --url URL [--strategy A|B|C] [--limit N] [--output output.json]
    python dns_parser_v2.py --category materinskie-platy --limit 10

Авто-бенчмарк (запускает все стратегии на одном URL):
    python dns_parser_v2.py --bench --url URL
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

def detect_block(html: str) -> str | None:
    """
    Определяет тип блокировки по HTML-странице.
    Возвращает строку-описание или None если всё OK.
    """
    h = html[:5000].lower()
    if "cloudflare" in h and ("challenge" in h or "ray id" in h):
        return "Cloudflare challenge"
    if "captcha" in h or "recaptcha" in h:
        return "CAPTCHA"
    if "выберите ваш город" in h or "выбор города" in h or "modal-city" in h:
        return "Модалка выбора города"
    if "403 forbidden" in h or "<title>403" in h:
        return "403 Forbidden"
    if "доступ ограничен" in h or "access denied" in h:
        return "Access Denied"
    if len(html) < 2000:
        return f"Слишком короткий ответ ({len(html)} байт)"
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

    # JSON-LD — самый надёжный источник базовых данных
    ld_data = {}
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if data.get("@type") == "Product":
                ld_data = data
                break
        except (json.JSONDecodeError, AttributeError):
            continue

    name = (
        ld_data.get("name")
        or _safe_text(soup, "div", "product-card-top__name")
        # Запасные селекторы на случай редизайна DNS
        or _safe_text(soup, "h1", None)
        or (soup.title.text.strip() if soup.title else None)
    )
    if not name:
        log.warning(f"  ⚠ Имя товара не найдено в {url}")
        if debug:
            dump_debug_html(html, strategy, url)
        return None

    # Цены
    price_discounted = _clean_price(
        soup.select_one(".product-buy__price_active") or
        soup.select_one("[data-price]")
    )
    price_original = _clean_price(
        soup.select_one(".product-buy__prev")
    ) or price_discounted

    # Рейтинг из JSON-LD
    agg = ld_data.get("aggregateRating", {})
    rating = float(agg["ratingValue"]) if agg.get("ratingValue") else None
    reviews = int(agg["reviewCount"]) if agg.get("reviewCount") else None

    # Изображения — быстро из слайдера, без лайтбокса
    images = []
    for img in soup.select(".product-images-slider__img"):
        src = img.get("src") or img.get("data-src") or ""
        src = src.split("?")[0]
        if src and not src.endswith(".svg") and src not in images:
            images.append(src)
        if len(images) >= 5:
            break

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
#  БЕНЧМАРК
# ══════════════════════════════════════════════════════════════════════════════

async def benchmark(url: str, debug: bool = False):
    """Прогоняет все три стратегии на одном URL и выводит таблицу сравнения."""
    print(f"\n{'='*60}")
    print(f"  БЕНЧМАРК DNS парсера")
    print(f"  URL: {url}")
    if debug:
        print(f"  Режим: DEBUG (HTML блокированных страниц сохраняется)")
    print(f"{'='*60}\n")

    strategies = []
    try:
        strategies.append(StrategyA(debug=debug))
    except RuntimeError as e:
        log.warning(f"Стратегия A недоступна: {e}")

    strategies.append(StrategyB(concurrency=1, debug=debug))
    strategies.append(StrategyC(debug=debug))

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
    strategy_name: str = "B",
    limit: int = 10,
    concurrency: int = 3,
    output: str | None = None,
):
    """Запускает парсер выбранной стратегией."""
    strategy_map = {
        "A": StrategyA,
        "B": lambda: StrategyB(concurrency=concurrency),
        "C": StrategyC,
    }

    cls = strategy_map.get(strategy_name.upper())
    if not cls:
        raise ValueError(f"Неизвестная стратегия: {strategy_name}. Выберите A, B или C.")

    strategy = cls()
    log.info(f"Стратегия: {strategy.name}")

    t_start = time.perf_counter()
    products = []

    # ── Получаем список URL ──────────────────────────────────────────────────
    if not urls and category_slug:
        log.info(f"Сбор ссылок из категории: {category_slug}")
        if strategy_name.upper() == "A":
            from curl_cffi.requests import AsyncSession
            async with AsyncSession() as session:
                urls = await strategy.get_product_links(category_slug, limit, session)
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
    if strategy_name.upper() == "A":
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
  # Спарсить 5 товаров стратегией A (быстро):
  python dns_parser_v2.py --category materinskie-platy --limit 5 --strategy A

  # Спарсить конкретный URL стратегией B:
  python dns_parser_v2.py --url https://www.dns-shop.ru/product/... --strategy B

  # Сравнить все стратегии на одном URL:
  python dns_parser_v2.py --bench --url https://www.dns-shop.ru/product/...

Стратегии:
  A — curl_cffi: TLS-спуф Chrome, без JS, очень быстро (~1-3s/товар)
  B — Playwright headless + stealth-патчи (~3-6s/товар)
  C — Playwright + имитация человека, надёжнее, медленнее (~8-15s/товар)

Доступные категории:
""" + "\n".join(f"  {k}" for k in CATEGORIES)
    )

    parser.add_argument("--url", help="URL конкретного товара или списка (через запятую)")
    parser.add_argument("--category", help="Slug категории DNS (см. список выше)")
    parser.add_argument("--strategy", default="B", choices=["A", "B", "C"],
                        help="Стратегия парсинга (default: B)")
    parser.add_argument("--limit", type=int, default=10,
                        help="Максимум товаров (default: 10)")
    parser.add_argument("--concurrency", type=int, default=3,
                        help="Параллельных запросов (default: 3, только для A/B)")
    parser.add_argument("--output", help="Путь к выходному JSON-файлу")
    parser.add_argument("--bench", action="store_true",
                        help="Запустить бенчмарк всех стратегий на одном URL")
    parser.add_argument("--debug", action="store_true",
                        help="Сохранять HTML при блокировке/ошибке (для анализа)")

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
    ))


if __name__ == "__main__":
    main()
