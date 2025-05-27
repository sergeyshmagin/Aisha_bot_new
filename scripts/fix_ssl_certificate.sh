#!/bin/bash

# Скрипт для диагностики и исправления SSL сертификата
# Использование: sudo ./fix_ssl_certificate.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен запускаться с правами root (sudo)"
   exit 1
fi

log "🔍 Диагностика SSL сертификата для aibots.kz:8443"

# Пути к сертификатам
SSL_DIR="/opt/aisha-backend/ssl"
CERT_FILE="$SSL_DIR/aibots_kz.crt"
KEY_FILE="$SSL_DIR/aibots.kz.key"
CA_BUNDLE_FILE="$SSL_DIR/aibots_kz.ca-bundle"

echo
log "📁 Проверка наличия файлов сертификатов..."

# Проверка существования файлов
if [[ -f "$CERT_FILE" ]]; then
    log "✅ Сертификат найден: $CERT_FILE"
else
    error "❌ Сертификат не найден: $CERT_FILE"
    SSL_MISSING=true
fi

if [[ -f "$KEY_FILE" ]]; then
    log "✅ Ключ найден: $KEY_FILE"
else
    error "❌ Ключ не найден: $KEY_FILE"
    SSL_MISSING=true
fi

if [[ -f "$CA_BUNDLE_FILE" ]]; then
    log "✅ CA Bundle найден: $CA_BUNDLE_FILE"
    HAS_CA_BUNDLE=true
else
    warn "⚠️ CA Bundle не найден: $CA_BUNDLE_FILE"
    HAS_CA_BUNDLE=false
fi

if [[ "$SSL_MISSING" == "true" ]]; then
    error "Сертификаты отсутствуют! Необходимо их установить."
    echo
    log "Для получения SSL сертификата:"
    echo "1. Используйте Let's Encrypt: certbot --nginx -d aibots.kz"
    echo "2. Или скопируйте существующие сертификаты в $SSL_DIR/"
    echo "3. Убедитесь что файлы называются:"
    echo "   - aibots_kz.crt (сертификат)"
    echo "   - aibots.kz.key (приватный ключ)"
    echo "   - aibots_kz.ca-bundle (цепочка сертификатов, опционально)"
    exit 1
fi

echo
log "🔍 Анализ SSL сертификата..."

# Проверка сертификата
debug "Информация о сертификате:"
openssl x509 -in "$CERT_FILE" -text -noout | head -20

echo
log "📅 Сроки действия сертификата:"
openssl x509 -in "$CERT_FILE" -noout -dates

echo
log "🌐 Домены в сертификате:"
openssl x509 -in "$CERT_FILE" -noout -text | grep -A1 "Subject Alternative Name" || echo "SAN не найден"

echo
log "🔐 Проверка соответствия ключа и сертификата..."
CERT_HASH=$(openssl x509 -noout -modulus -in "$CERT_FILE" | openssl md5)
KEY_HASH=$(openssl rsa -noout -modulus -in "$KEY_FILE" | openssl md5)

if [[ "$CERT_HASH" == "$KEY_HASH" ]]; then
    log "✅ Ключ и сертификат соответствуют друг другу"
else
    error "❌ Ключ и сертификат НЕ соответствуют!"
    exit 1
fi

echo
log "🌍 Тестирование SSL соединения..."

# Тест локального SSL
debug "Тестирование локального SSL соединения..."
if echo | openssl s_client -connect localhost:8443 -servername aibots.kz 2>/dev/null | grep -q "Verify return code: 0"; then
    log "✅ Локальное SSL соединение успешно"
else
    warn "⚠️ Проблемы с локальным SSL соединением"
fi

# Проверка nginx конфигурации SSL
echo
log "📝 Проверка конфигурации nginx..."
if nginx -t; then
    log "✅ Конфигурация nginx корректна"
else
    error "❌ Ошибки в конфигурации nginx"
    exit 1
fi

# Исправления для типичных проблем
echo
log "🔧 Применение исправлений..."

# 1. Права доступа к файлам
log "Установка правильных прав доступа..."
chown -R aisha:aisha "$SSL_DIR"
chmod 644 "$CERT_FILE"
chmod 600 "$KEY_FILE"
if [[ "$HAS_CA_BUNDLE" == "true" ]]; then
    chmod 644 "$CA_BUNDLE_FILE"
fi

# 2. Обновление конфигурации nginx с CA bundle (если есть)
if [[ "$HAS_CA_BUNDLE" == "true" ]]; then
    log "Обновление nginx для использования CA bundle..."
    
    # Создаем полный сертификат (cert + ca-bundle)
    cat "$CERT_FILE" "$CA_BUNDLE_FILE" > "$SSL_DIR/aibots_kz_full.crt"
    chown aisha:aisha "$SSL_DIR/aibots_kz_full.crt"
    chmod 644 "$SSL_DIR/aibots_kz_full.crt"
    
    # Обновляем nginx конфигурацию
    sed -i "s|ssl_certificate.*aibots_kz.crt|ssl_certificate $SSL_DIR/aibots_kz_full.crt|g" /etc/nginx/sites-available/aisha-webhook
    log "✅ Nginx настроен для использования полного сертификата"
fi

# 3. Перезагрузка nginx
log "Перезагрузка nginx..."
systemctl reload nginx

echo
log "🧪 Финальное тестирование..."

# Тест через curl с подробным выводом
log "Тестирование HTTPS соединения..."

# Локальный тест
if curl -s -f -k https://localhost:8443/health > /dev/null; then
    log "✅ Локальный HTTPS работает (с игнорированием SSL)"
else
    error "❌ Локальный HTTPS не работает"
fi

# Тест с проверкой SSL
if curl -s -f https://aibots.kz:8443/health > /dev/null; then
    log "🎉 ✅ HTTPS с проверкой SSL работает!"
    SSL_WORKING=true
else
    warn "⚠️ HTTPS с проверкой SSL не работает"
    SSL_WORKING=false
fi

# Тест без проверки SSL (как это делает FAL AI)
if curl -s -f -k https://aibots.kz:8443/health > /dev/null; then
    log "✅ HTTPS без проверки SSL работает (достаточно для FAL AI)"
    FAL_WORKING=true
else
    error "❌ HTTPS не работает совсем"
    FAL_WORKING=false
fi

echo
log "📊 Итоговый отчет:"

if [[ "$SSL_WORKING" == "true" ]]; then
    log "🎉 ✅ SSL полностью исправен - webhook готов к работе!"
elif [[ "$FAL_WORKING" == "true" ]]; then
    warn "⚠️ SSL работает частично - FAL AI сможет подключиться, но браузеры могут показывать предупреждения"
    echo
    log "Возможные причины:"
    echo "1. Самоподписанный сертификат"
    echo "2. Неполная цепочка сертификатов"
    echo "3. Неправильная настройка домена"
    echo
    log "Для полного исправления:"
    echo "1. Получите сертификат от доверенного CA (Let's Encrypt)"
    echo "2. Убедитесь что aibots.kz указывает на этот сервер"
    echo "3. Добавьте полную цепочку сертификатов"
else
    error "❌ SSL не работает - необходимо исправление"
fi

echo
log "🔗 Полезные команды для дальнейшей диагностики:"
echo "- Тест SSL: openssl s_client -connect aibots.kz:8443 -servername aibots.kz"
echo "- Проверка сертификата: openssl x509 -in $CERT_FILE -text -noout"
echo "- Логи nginx: tail -f /var/log/nginx/error.log"
echo "- Статус nginx: systemctl status nginx"

if [[ "$FAL_WORKING" == "true" ]]; then
    echo
    log "🎯 Рекомендация: FAL AI webhook должен работать даже с текущими настройками SSL!"
    log "Протестируйте webhook: curl -k -X POST https://aibots.kz:8443/api/v1/avatar/status_update -H 'Content-Type: application/json' -d '{\"test\": true}'"
fi 