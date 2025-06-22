#!/bin/bash
set -e

echo "🚀 Starting nginx with SSL support..."

# Запускаем SSL загрузчик
echo "📋 Loading SSL certificates from environment variables..."
/usr/local/bin/ssl_loader.sh

# Проверяем есть ли SSL сертификаты
if [ -f "/var/run/ssl-loaded" ]; then
    echo "✅ SSL certificates loaded successfully, starting nginx with HTTPS support"
    echo "🔒 HTTPS will be available on port 443"
    echo "🔄 HTTP traffic on port 80 will redirect to HTTPS"
    
    # Запускаем nginx с SSL конфигурацией
    exec nginx -g 'daemon off;'
else
    echo "⚠️  SSL certificates not found, starting nginx in HTTP-only mode"
    echo "🌐 Only HTTP will be available on port 80"
    
    # Создаем HTTP-only конфигурацию
    cat > /etc/nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    
    # Основные настройки
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;
    
    # Gzip сжатие
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Upstream для веб-приложения
    upstream web_backend {
        server web:5000;
        keepalive 32;
    }
    
    # HTTP-only сервер
    server {
        listen 80 default_server;
        server_name pcconf.ru www.pcconf.ru;
        
        # SSL статус
        location /ssl-status {
            return 200 "SSL not configured - running on HTTP only\nTo enable SSL, set SSL_CERTIFICATE and SSL_PRIVATE_KEY environment variables";
            add_header Content-Type text/plain;
        }
        
        # Основное проксирование
        location / {
            proxy_pass http://web_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto http;
            
            # Таймауты
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
        
        # Статические файлы
        location /static/ {
            proxy_pass http://web_backend;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # API эндпоинты
        location /api/ {
            proxy_pass http://web_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto http;
            
            # Увеличенные таймауты для API
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
    }
}
EOF
    
    # Запускаем nginx
    exec nginx -g 'daemon off;'
fi 