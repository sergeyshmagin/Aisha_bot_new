#!/bin/bash

# Скрипт настройки nginx для Aisha Bot API сервера
# Использование: sudo ./setup_nginx.sh

set -e  # Остановка при ошибках

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен запускаться с правами root (sudo)"
fi

# Проверка наличия nginx
if ! command -v nginx &> /dev/null; then
    error "nginx не установлен. Установите nginx сначала: apt update && apt install nginx"
fi

# Проверка существования файла конфигурации
if [[ ! -f "nginx_aisha_webhook.conf" ]]; then
    error "Файл nginx_aisha_webhook.conf не найден в текущей директории"
fi

log "Настройка nginx для Aisha Bot API сервера..."

# 1. Создание директорий для логов
log "Создание директорий для логов..."
mkdir -p /var/log/aisha
chown www-data:www-data /var/log/aisha
chmod 755 /var/log/aisha

# 2. Проверка SSL сертификатов
SSL_CERT_PATH="/opt/aisha-backend/ssl/aibots_kz.crt"
SSL_KEY_PATH="/opt/aisha-backend/ssl/aibots.kz.key"

if [[ ! -f "$SSL_CERT_PATH" ]]; then
    warn "SSL сертификат не найден: $SSL_CERT_PATH"
    warn "Убедитесь, что SSL сертификаты загружены в /opt/aisha-backend/ssl/"
    warn "Конфигурация будет установлена, но nginx не запустится без сертификатов"
fi

if [[ ! -f "$SSL_KEY_PATH" ]]; then
    warn "SSL ключ не найден: $SSL_KEY_PATH"
fi

# 3. Установка конфигурации nginx
log "Копирование конфигурации nginx..."
cp nginx_aisha_webhook.conf /etc/nginx/sites-available/aisha-webhook

# 4. Создание символической ссылки
log "Активация конфигурации..."
ln -sf /etc/nginx/sites-available/aisha-webhook /etc/nginx/sites-enabled/aisha-webhook

# 5. Отключение дефолтного сайта (если активен)
if [[ -L /etc/nginx/sites-enabled/default ]]; then
    log "Отключение дефолтного сайта nginx..."
    rm /etc/nginx/sites-enabled/default
fi

# 6. Проверка синтаксиса конфигурации
log "Проверка синтаксиса конфигурации nginx..."
if nginx -t; then
    log "Синтаксис конфигурации nginx корректен"
else
    error "Ошибка в конфигурации nginx! Проверьте настройки"
fi

# 7. Проверка что API сервер запущен
log "Проверка API сервера..."
if systemctl is-active --quiet aisha-api; then
    log "API сервер aisha-api запущен"
else
    warn "API сервер aisha-api не запущен. Запустите его: sudo systemctl start aisha-api"
fi

# 8. Проверка доступности порта 8000
if netstat -ln | grep :8000 > /dev/null; then
    log "API сервер слушает на порту 8000"
else
    warn "API сервер не слушает на порту 8000. Проверьте настройки"
fi

# 9. Перезагрузка nginx
log "Перезагрузка nginx..."
if systemctl reload nginx; then
    log "nginx успешно перезагружен"
else
    error "Ошибка при перезагрузке nginx"
fi

# 10. Проверка статуса nginx
log "Проверка статуса nginx..."
if systemctl is-active --quiet nginx; then
    log "nginx запущен и работает"
else
    error "nginx не запущен!"
fi

# 11. Тестирование конфигурации
log "Тестирование локального подключения к API..."
sleep 2

if curl -s -f http://localhost:8000/health > /dev/null; then
    log "✅ API сервер отвечает на локальные запросы"
else
    warn "⚠️ API сервер не отвечает на локальные запросы"
fi

log "🎉 Настройка nginx завершена!"
echo
log "Следующие шаги:"
echo "1. Убедитесь, что SSL сертификаты находятся в /opt/aisha-backend/ssl/"
echo "2. Проверьте работу: curl https://aibots.kz:8443/health"
echo "3. Проверьте логи: tail -f /var/log/aisha/nginx_access.log"
echo "4. Настройте firewall для порта 8443"
echo
log "Полезные команды:"
echo "- Статус nginx: sudo systemctl status nginx"
echo "- Перезагрузка nginx: sudo systemctl reload nginx"
echo "- Проверка конфигурации: sudo nginx -t"
echo "- Логи nginx: sudo tail -f /var/log/nginx/error.log"
echo "- Логи webhook: sudo tail -f /var/log/aisha/webhook_access.log" 