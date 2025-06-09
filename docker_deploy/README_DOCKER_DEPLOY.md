# Развертывание PCConf через Docker на dockhost.ru

## Архитектура системы

Система разделена на следующие сервисы:
- **web** (порт 5000) - основное веб-приложение
- **parser** (порт 5001) - сервис парсинга сайтов DNS и Citilink
- **db** - PostgreSQL база данных
- **redis** - кэш и очереди задач
- **nginx** - reverse proxy (порты 80/443)

## Настройка на dockhost.ru

### 1. Подготовка Git репозитория

1. Создайте Git репозиторий (например, на GitHub)
2. Загрузите все файлы из папки `docker_deploy` в корень репозитория
3. Структура должна быть:
```
repository/
├── app/
├── migrations/
├── Dockerfile
├── Dockerfile.parser
├── docker-compose.yml
├── nginx.conf
├── requirements.txt
├── requirements-parser.txt
├── run.py
├── init.sql
└── create_admin.py
```

### 2. Настройка на dockhost.ru

1. Войдите на https://my.dockhost.ru/
2. Создайте новый проект:
   - **Имя**: new-pccon
   - **Адрес репозитория**: https://github.com/Reedmoor/new_pccon
   - **Ветка**: main
   - **Dockerfile**: Dockerfile (по умолчанию)
   - **Контекст**: . (по умолчанию)

### 3. Переменные окружения

В настройках проекта на dockhost.ru добавьте переменные:
```
SECRET_KEY=pcconf_production_secret_key_change_this_very_secure_12345
FLASK_ENV=production
DEBUG=False
DATABASE_URL=postgresql://pccon_user:12345@db:5432/pccon_db
REDIS_URL=redis://:12345@redis:6379
GIGACHAT_CREDENTIALS=MjZjYjAwNzUtZTllZS00YjkxLWJlOGEtYjk5N2FjMzA3ZjBmOjQ3ZTVmZmM4LTJiZGQtNDU1OC1iNDdkLTBiZmJmZDNmNWI4Ng==
PARSER_API_URL=http://parser:5001
MAIN_SERVER_URL=http://web:5000
```

### 4. Настройка домена

1. В настройках проекта укажите домен: `pcconf.ru`
2. Настройте DNS записи у регистратора домена:
   - A-запись: pcconf.ru → IP адрес от dockhost.ru
   - CNAME-запись: www.pcconf.ru → pcconf.ru

### 5. Развертывание

1. Нажмите кнопку "Deploy" в панели dockhost.ru
2. Дождитесь завершения сборки контейнеров
3. Система автоматически запустит все сервисы

## Структура сервисов

### Веб-приложение (web:5000)
- Основной сайт PCConf
- Пользовательский интерфейс
- API для управления конфигурациями

### Парсер (parser:5001)
- Отдельный сервис для парсинга DNS и Citilink
- Работает независимо от основного сайта
- Доступен через `/parser/` URL

### База данных (PostgreSQL)
- Хранение пользователей, конфигураций, продуктов
- Автоматическое создание схемы при первом запуске

### Redis
- Кэширование данных
- Очереди задач для парсера

### Nginx
- Reverse proxy для распределения запросов
- Балансировка нагрузки
- SSL терминация (при настройке сертификата)

## Первый запуск

После развертывания:

1. Перейдите на https://pcconf.ru
2. Создайте администратора через консоль:
   ```bash
   docker exec -it <web_container_id> python create_admin.py
   ```
3. Войдите с учетными данными администратора
4. Настройте каталог продуктов через админ-панель

## Мониторинг и логи

### Просмотр логов
```bash
# Логи веб-приложения
docker logs <web_container_id>

# Логи парсера
docker logs <parser_container_id>

# Логи всех сервисов
docker-compose logs -f
```

### Проверка состояния
- Веб-приложение: https://pcconf.ru
- Парсер: https://pcconf.ru/parser/health
- База данных: автоматические health checks

## Обновление

1. Внесите изменения в код
2. Сделайте commit и push в Git репозиторий
3. В панели dockhost.ru нажмите "Redeploy"
4. Система автоматически пересоберет и перезапустит контейнеры

## Масштабирование

### Увеличение ресурсов парсера
```yaml
# В docker-compose.yml
parser:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
```

### Добавление реплик
```yaml
# В docker-compose.yml
parser:
  deploy:
    replicas: 2
```

## Резервное копирование

### База данных
```bash
# Создание бэкапа
docker exec <db_container_id> pg_dump -U pccon_user pccon_db > backup.sql

# Восстановление
docker exec -i <db_container_id> psql -U pccon_user pccon_db < backup.sql
```

### Данные парсера
Данные парсера сохраняются в volume и автоматически сохраняются между перезапусками.

## Решение проблем

### Проблемы с парсером
1. Проверьте логи парсера: `docker logs <parser_container_id>`
2. Убедитесь, что Chromium установлен в контейнере
3. Проверьте доступность целевых сайтов

### Проблемы с базой данных
1. Проверьте состояние: `docker exec <db_container_id> pg_isready`
2. Проверьте подключение: переменные DATABASE_URL
3. Пересоздайте volume при необходимости

### Проблемы с производительностью
1. Увеличьте ресурсы контейнеров
2. Настройте кэширование Redis
3. Добавьте индексы в базу данных

## Безопасность

1. **Смените пароли** в production:
   - SECRET_KEY
   - Пароли базы данных
   - Пароль Redis

2. **Настройте SSL сертификат** через Let's Encrypt или загрузите свой

3. **Ограничьте доступ** к админ-панели по IP (если нужно)

## Контакты поддержки

При возникновении проблем:
1. Проверьте логи всех сервисов
2. Обратитесь к документации dockhost.ru
3. Создайте issue в Git репозитории проекта 