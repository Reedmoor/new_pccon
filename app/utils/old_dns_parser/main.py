try:
    from . import productDetailsParser, linksParser
    from .session_utils import start_dns_session
except ImportError:
    import productDetailsParser, linksParser
    from session_utils import start_dns_session
import sys


def main(category_name=None, limit_per_category=5):
    """
    Основная функция для запуска парсера DNS.
    Каждый запуск пишет товары только в data/dns/dns_{category}_{timestamp}.json
    """
    session_file = start_dns_session(category_name=category_name)

    product_urls = linksParser.main(
        product_callback=None,
        limit_per_category=limit_per_category,
        category_name=category_name,
    )

    productDetailsParser.main()

    print(f"DNS session file: {session_file}")
    return product_urls, session_file


if __name__ == "__main__":
    category = None
    if len(sys.argv) > 1:
        category = sys.argv[1]

    limit = 5
    if len(sys.argv) > 2:
        try:
            limit = int(sys.argv[2])
        except ValueError:
            pass

    main(category_name=category, limit_per_category=limit)
