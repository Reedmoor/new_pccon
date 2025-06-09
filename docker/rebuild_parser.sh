#!/bin/bash

# Скрипт для пересборки и тестирования DNS парсера в Docker

echo "=== Rebuilding DNS Parser Container ==="

# Остановка и удаление старого контейнера
echo "Stopping existing parser container..."
docker-compose stop pccon_parser
docker-compose rm -f pccon_parser

# Удаление старого образа
echo "Removing old parser image..."
docker rmi $(docker images -q new_pccon_pccon_parser) 2>/dev/null || true

# Пересборка контейнера
echo "Rebuilding parser container..."
docker-compose build pccon_parser

# Запуск контейнера
echo "Starting parser container..."
docker-compose up -d pccon_parser

# Ожидание запуска
echo "Waiting for container to start..."
sleep 10

# Проверка статуса
echo "Checking container status..."
docker-compose ps pccon_parser

# Проверка логов
echo "=== Container logs ==="
docker logs pccon_parser --tail 20

# Тестирование настройки
echo "=== Testing parser setup ==="
docker exec pccon_parser python /app/parsers/dns/test_docker_setup.py

# Проверка Chrome
echo "=== Checking Chrome installation ==="
docker exec pccon_parser google-chrome --version
docker exec pccon_parser chromedriver --version

# Проверка Python пакетов
echo "=== Checking Python packages ==="
docker exec pccon_parser pip list | grep -E "(selenium|undetected|scrapy|beautifulsoup4)"

echo "=== Rebuild complete! ==="
echo ""
echo "To test the parser manually:"
echo "docker exec -it pccon_parser bash"
echo "cd /app/parsers/dns"
echo "python main.py videokarty 2" 