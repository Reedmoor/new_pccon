#!/bin/bash

# SSL Loader - Загрузка SSL сертификатов из переменных окружения
# Автор: SSL Security Script
# Версия: 1.0

set -e

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${BLUE}[SSL-LOADER]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[SSL-LOADER WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[SSL-LOADER ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SSL-LOADER SUCCESS]${NC} $1"
}

# Директория для SSL сертификатов
SSL_DIR="/etc/ssl/certs"
SSL_KEY_DIR="/etc/ssl/private"

# Создаем директории если не существуют
mkdir -p ${SSL_DIR}
mkdir -p ${SSL_KEY_DIR}

log "Starting SSL certificate loader..."

# Проверяем наличие переменных окружения
if [ -z "$SSL_CERTIFICATE" ] && [ -z "$SSL_PRIVATE_KEY" ]; then
    warn "No SSL environment variables found. Skipping SSL configuration."
    warn "Set SSL_CERTIFICATE and SSL_PRIVATE_KEY environment variables to enable SSL."
    exit 0
fi

# Загрузка SSL сертификата
if [ -n "$SSL_CERTIFICATE" ]; then
    log "Loading SSL certificate from environment variable..."
    
    # Записываем сертификат в файл
    echo "$SSL_CERTIFICATE" > ${SSL_DIR}/pcconf.ru.crt
    
    # Устанавливаем правильные права доступа
    chmod 644 ${SSL_DIR}/pcconf.ru.crt
    chown root:root ${SSL_DIR}/pcconf.ru.crt
    
    success "SSL certificate loaded successfully"
else
    error "SSL_CERTIFICATE environment variable is required but not set"
    exit 1
fi

# Загрузка приватного ключа
if [ -n "$SSL_PRIVATE_KEY" ]; then
    log "Loading SSL private key from environment variable..."
    
    # Записываем ключ в файл
    echo "$SSL_PRIVATE_KEY" > ${SSL_KEY_DIR}/pcconf.ru.key
    
    # Устанавливаем правильные права доступа (только root может читать)
    chmod 600 ${SSL_KEY_DIR}/pcconf.ru.key
    chown root:root ${SSL_KEY_DIR}/pcconf.ru.key
    
    success "SSL private key loaded successfully"
else
    error "SSL_PRIVATE_KEY environment variable is required but not set"
    exit 1
fi

# Загрузка цепочки сертификатов (опционально)
if [ -n "$SSL_CERTIFICATE_CHAIN" ]; then
    log "Loading SSL certificate chain from environment variable..."
    
    echo "$SSL_CERTIFICATE_CHAIN" > ${SSL_DIR}/pcconf.ru.chain.crt
    chmod 644 ${SSL_DIR}/pcconf.ru.chain.crt
    chown root:root ${SSL_DIR}/pcconf.ru.chain.crt
    
    success "SSL certificate chain loaded successfully"
fi

# Загрузка DH параметров (опционально)
if [ -n "$SSL_DH_PARAMS" ]; then
    log "Loading SSL DH parameters from environment variable..."
    
    echo "$SSL_DH_PARAMS" > ${SSL_DIR}/dhparam.pem
    chmod 644 ${SSL_DIR}/dhparam.pem
    chown root:root ${SSL_DIR}/dhparam.pem
    
    success "SSL DH parameters loaded successfully"
fi

# Проверяем валидность сертификата и ключа
log "Validating SSL certificate and key..."

if openssl x509 -in ${SSL_DIR}/pcconf.ru.crt -text -noout > /dev/null 2>&1; then
    success "SSL certificate is valid"
else
    error "SSL certificate is invalid"
    exit 1
fi

if openssl rsa -in ${SSL_KEY_DIR}/pcconf.ru.key -check -noout > /dev/null 2>&1; then
    success "SSL private key is valid"
else
    error "SSL private key is invalid"
    exit 1
fi

# Проверяем соответствие сертификата и ключа
CERT_HASH=$(openssl x509 -noout -modulus -in ${SSL_DIR}/pcconf.ru.crt | openssl md5)
KEY_HASH=$(openssl rsa -noout -modulus -in ${SSL_KEY_DIR}/pcconf.ru.key | openssl md5)

if [ "$CERT_HASH" = "$KEY_HASH" ]; then
    success "SSL certificate and private key match"
else
    error "SSL certificate and private key do not match"
    exit 1
fi

# Создаем флаг успешной загрузки
touch /var/run/ssl-loaded

success "SSL certificates loaded and validated successfully!"
success "Files created:"
success "  - Certificate: ${SSL_DIR}/pcconf.ru.crt"
success "  - Private Key: ${SSL_KEY_DIR}/pcconf.ru.key"
[ -f "${SSL_DIR}/pcconf.ru.chain.crt" ] && success "  - Certificate Chain: ${SSL_DIR}/pcconf.ru.chain.crt"
[ -f "${SSL_DIR}/dhparam.pem" ] && success "  - DH Parameters: ${SSL_DIR}/dhparam.pem"

log "SSL loader completed successfully" 