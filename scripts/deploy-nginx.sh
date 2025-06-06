#!/bin/bash

# Скрипт для развертывания nginx контейнера в продакшене
# Заменяет systemd nginx сервис на Docker контейнер

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверяем, что мы в правильной директории
if [[ ! -f "docker-compose.prod.yml" ]]; then
    log_error "Скрипт должен запускаться из корня проекта aisha-backend"
    exit 1
fi

# Проверяем права sudo
if [[ $EUID -ne 0 ]]; then
    log_error "Скрипт должен запускаться с правами sudo"
    exit 1
fi

log_info "Начинаем развертывание nginx в Docker контейнере..."

# 1. Останавливаем и отключаем systemd nginx сервис
log_info "Останавливаем systemd nginx сервис..."
if systemctl is-active --quiet nginx; then
    systemctl stop nginx
    log_success "nginx сервис остановлен"
else
    log_warning "nginx сервис уже остановлен"
fi

if systemctl is-enabled --quiet nginx; then
    systemctl disable nginx
    log_success "nginx сервис отключен из автозагрузки"
else
    log_warning "nginx сервис уже отключен"
fi

# 2. Создаем резервную копию конфигурации systemd nginx
if [[ -d "/etc/nginx" ]]; then
    log_info "Создаем резервную копию конфигурации nginx..."
    cp -r /etc/nginx /etc/nginx.backup.$(date +%Y%m%d_%H%M%S)
    log_success "Резервная копия создана"
fi

# 3. Проверяем наличие SSL сертификатов
if [[ ! -f "ssl_certificate/aibots_kz_full.crt" ]] || [[ ! -f "ssl_certificate/aibots.kz.key" ]]; then
    log_error "SSL сертификаты не найдены!"
    log_error "Убедитесь, что файлы ssl_certificate/aibots_kz_full.crt и ssl_certificate/aibots.kz.key существуют"
    log_error "Текущие файлы в ssl_certificate/:"
    ls -la ssl_certificate/ || true
    exit 1
fi

# 4. Создаем директории для логов
log_info "Создаем директории для логов..."
mkdir -p logs/nginx
chmod 755 logs/nginx
log_success "Директории созданы"

# 5. Проверяем файл окружения
if [[ ! -f ".env.docker.prod" ]]; then
    log_error "Файл .env.docker.prod не найден!"
    log_error "Создайте файл на основе env.docker.prod.template"
    exit 1
fi

# 6. Останавливаем старые контейнеры (если есть)
log_info "Останавливаем старые nginx контейнеры..."
docker-compose -f docker-compose.prod.yml stop nginx 2>/dev/null || true
docker-compose -f docker-compose.prod.yml rm -f nginx 2>/dev/null || true

# 7. Собираем новый образ nginx
log_info "Собираем новый образ nginx..."
docker-compose -f docker-compose.prod.yml build nginx
log_success "Образ nginx собран"

# 8. Запускаем nginx контейнер
log_info "Запускаем nginx контейнер..."
docker-compose -f docker-compose.prod.yml up -d nginx
log_success "nginx контейнер запущен"

# 9. Ждем инициализации и проверяем статус
log_info "Ждем инициализации nginx..."
sleep 10

if docker-compose -f docker-compose.prod.yml ps nginx | grep -q "Up"; then
    log_success "nginx контейнер успешно запущен"
else
    log_error "Ошибка запуска nginx контейнера"
    docker-compose -f docker-compose.prod.yml logs nginx
    exit 1
fi

# 10. Проверяем health check
log_info "Проверяем health check..."
for i in {1..10}; do
    if curl -s http://localhost/health > /dev/null; then
        log_success "Health check прошел успешно"
        break
    fi
    if [[ $i -eq 10 ]]; then
        log_error "Health check не прошел после 10 попыток"
        docker-compose -f docker-compose.prod.yml logs nginx
        exit 1
    fi
    sleep 3
done

# 11. Настраиваем автозапуск Docker при загрузке системы
log_info "Настраиваем автозапуск Docker..."
systemctl enable docker
log_success "Docker автозапуск настроен"

# 12. Создаем systemd сервис для управления контейнерами
cat > /etc/systemd/system/aisha-nginx.service << 'EOF'
[Unit]
Description=Aisha Bot Nginx Container
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/aisha-backend
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d nginx
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml stop nginx
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable aisha-nginx.service
log_success "Systemd сервис aisha-nginx создан и включен"

# 13. Финальные проверки
log_info "Выполняем финальные проверки..."
echo "Статус контейнера:"
docker-compose -f docker-compose.prod.yml ps nginx

echo -e "\nЛоги nginx:"
docker-compose -f docker-compose.prod.yml logs --tail=20 nginx

echo -e "\nПроверка HTTP:"
curl -I http://localhost/health

echo -e "\nПроверка HTTPS на порту 8443:"
curl -Ik https://localhost:8443/health || log_warning "HTTPS недоступен (возможно, не настроены сертификаты)"

log_success "Развертывание nginx завершено!"
log_info "Nginx теперь работает в Docker контейнере с автоперезапуском"
log_info "Управление: docker-compose -f docker-compose.prod.yml [start|stop|restart] nginx"
log_info "Или через systemd: systemctl [start|stop|restart] aisha-nginx" 