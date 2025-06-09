# Скрипт для пересборки и тестирования DNS парсера в Docker (Windows PowerShell)

Write-Host "=== Rebuilding DNS Parser Container ===" -ForegroundColor Green

# Остановка и удаление старого контейнера
Write-Host "Stopping existing parser container..." -ForegroundColor Yellow
docker-compose stop pccon_parser
docker-compose rm -f pccon_parser

# Удаление старого образа
Write-Host "Removing old parser image..." -ForegroundColor Yellow
$oldImage = docker images -q new_pccon_pccon_parser
if ($oldImage) {
    docker rmi $oldImage
}

# Пересборка контейнера
Write-Host "Rebuilding parser container..." -ForegroundColor Yellow
docker-compose build pccon_parser

# Запуск контейнера
Write-Host "Starting parser container..." -ForegroundColor Yellow
docker-compose up -d pccon_parser

# Ожидание запуска
Write-Host "Waiting for container to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Проверка статуса
Write-Host "Checking container status..." -ForegroundColor Yellow
docker-compose ps pccon_parser

# Проверка логов
Write-Host "=== Container logs ===" -ForegroundColor Cyan
docker logs pccon_parser --tail 20

# Тестирование настройки
Write-Host "=== Testing parser setup ===" -ForegroundColor Cyan
docker exec pccon_parser python /app/parsers/dns/test_docker_setup.py

# Проверка Chrome
Write-Host "=== Checking Chrome installation ===" -ForegroundColor Cyan
docker exec pccon_parser google-chrome --version
docker exec pccon_parser chromedriver --version

# Проверка Python пакетов
Write-Host "=== Checking Python packages ===" -ForegroundColor Cyan
docker exec pccon_parser pip list | Select-String -Pattern "(selenium|undetected|scrapy|beautifulsoup4)"

# Тестирование улучшенных селекторов
Write-Host "=== Testing improved selectors ===" -ForegroundColor Cyan
Write-Host "Running comprehensive selector tests..." -ForegroundColor Yellow
docker exec pccon_parser python /app/parsers/dns/test_improved_selectors.py

# Быстрый тест парсинга одного товара
Write-Host "=== Quick single product test ===" -ForegroundColor Cyan
Write-Host "Testing single product parsing..." -ForegroundColor Yellow
docker exec pccon_parser python /app/parsers/dns/test_parse_single.py

Write-Host "=== Rebuild complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "To test the parser manually:" -ForegroundColor Yellow
Write-Host "docker exec -it pccon_parser bash" -ForegroundColor White
Write-Host "cd /app/parsers/dns" -ForegroundColor White
Write-Host "python main.py videokarty 2" -ForegroundColor White
Write-Host ""
Write-Host "To test improved selectors:" -ForegroundColor Yellow
Write-Host "docker exec pccon_parser python /app/parsers/dns/test_improved_selectors.py" -ForegroundColor White 