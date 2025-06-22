FROM nginx:alpine

# Устанавливаем openssl для работы с сертификатами
RUN apk add --no-cache openssl bash

# Копируем SSL загрузчик
COPY docker/ssl_loader.sh /usr/local/bin/ssl_loader.sh
RUN chmod +x /usr/local/bin/ssl_loader.sh

# Копируем nginx конфигурацию
COPY docker/nginx.conf /etc/nginx/nginx.conf

# Создаем директории для SSL
RUN mkdir -p /etc/ssl/certs /etc/ssl/private

# Создаем entrypoint скрипт
COPY docker/nginx-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Экспонируем порты
EXPOSE 80 443

# Запускаем через наш стартовый скрипт
ENTRYPOINT ["/docker-entrypoint.sh"] 