#!/bin/bash

# Скрипт для настройки продакшн сервера Ubuntu 24 
# Запускать на целевом сервере 192.168.0.10

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Проверяем что мы на Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
    log_error "Скрипт предназначен для Ubuntu"
    exit 1
fi

log_info "Настройка продакшн сервера для Aisha Backend..."

# 1. Обновление системы
log_info "Обновление системы..."
sudo apt update && sudo apt upgrade -y
log_success "Система обновлена"

# 2. Установка базовых пакетов
log_info "Установка базовых пакетов..."
sudo apt install -y \
    curl \
    wget \
    git \
    htop \
    ufw \
    fail2ban \
    logrotate \
    unzip \
    ca-certificates \
    gnupg \
    lsb-release
log_success "Базовые пакеты установлены"

# 3. Установка Docker
log_info "Установка Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 4. Установка Docker Compose
log_info "Установка Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 5. Создание структуры директорий
log_info "Создание структуры директорий..."
sudo mkdir -p /opt/aisha-backend/{logs/nginx,ssl_certificate}
sudo mkdir -p /opt/backups/aisha

# Устанавливаем права
sudo chown -R $USER:$USER /opt/aisha-backend
sudo chown -R $USER:$USER /opt/backups/aisha

log_success "Структура директорий создана"

# 6. Настройка firewall
log_info "Настройка firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Разрешаем необходимые порты
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 8443/tcp comment 'HTTPS Aisha'
sudo ufw allow from 192.168.0.0/24 comment 'Local network'

# Включаем firewall
sudo ufw --force enable

log_success "Firewall настроен"

# 7. Настройка fail2ban
log_info "Настройка fail2ban..."
sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200
EOF

sudo systemctl enable fail2ban
sudo systemctl restart fail2ban

log_success "fail2ban настроен"

# 8. Настройка logrotate для Docker
log_info "Настройка logrotate..."
sudo tee /etc/logrotate.d/aisha-docker << 'EOF'
/opt/aisha-backend/logs/*/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    create 644 root root
}

/var/lib/docker/containers/*/*-json.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    maxsize 100M
}
EOF

log_success "logrotate настроен"

# 9. Настройка мониторинга диска
log_info "Настройка мониторинга диска..."
sudo tee /usr/local/bin/disk-monitor.sh << 'EOF'
#!/bin/bash
THRESHOLD=85
USAGE=$(df /opt | tail -1 | awk '{print $5}' | sed 's/%//')

if [ $USAGE -gt $THRESHOLD ]; then
    echo "ВНИМАНИЕ: Диск заполнен на ${USAGE}%" | wall
    logger "Disk usage warning: ${USAGE}%"
fi
EOF

sudo chmod +x /usr/local/bin/disk-monitor.sh

# Добавляем в cron
(crontab -l 2>/dev/null; echo "*/15 * * * * /usr/local/bin/disk-monitor.sh") | crontab -

log_success "Мониторинг диска настроен"

# 10. Настройка Docker daemon
log_info "Настройка Docker daemon..."
sudo tee /etc/docker/daemon.json << 'EOF'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "insecure-registries": ["192.168.0.3:5000"],
    "metrics-addr": "127.0.0.1:9323",
    "experimental": false
}
EOF

sudo systemctl restart docker

log_success "Docker daemon настроен"

# 11. Создание пользователя для деплоя
log_info "Настройка пользователя для деплоя..."
if ! id "deploy" &>/dev/null; then
    sudo useradd -m -s /bin/bash deploy
    sudo usermod -aG docker deploy
    
    # Настройка sudo без пароля для deploy скриптов
    sudo tee /etc/sudoers.d/aisha-deploy << 'EOF'
deploy ALL=(ALL) NOPASSWD: /opt/aisha-backend/scripts/deploy-nginx.sh
deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart aisha-nginx
deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl status aisha-nginx
deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop aisha-nginx
deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl start aisha-nginx
EOF
    
    log_success "Пользователь deploy создан"
else
    log_warning "Пользователь deploy уже существует"
fi

# 12. Создание SSH ключей для deploy
log_info "Генерация SSH ключей для автоматизации..."
if [ ! -f ~/.ssh/id_rsa ]; then
    ssh-keygen -t rsa -b 4096 -C "aisha-prod-deploy" -f ~/.ssh/id_rsa -N ""
    log_success "SSH ключи созданы"
    
    echo "Добавьте следующий публичный ключ на dev сервер:"
    echo "$(cat ~/.ssh/id_rsa.pub)"
else
    log_warning "SSH ключи уже существуют"
fi

# 13. Настройка системных лимитов
log_info "Настройка системных лимитов..."
sudo tee -a /etc/security/limits.conf << 'EOF'
# Aisha Backend limits
* soft nofile 65536
* hard nofile 65536
* soft nproc 4096
* hard nproc 4096
EOF

log_success "Системные лимиты настроены"

# 14. Создание базовых скриптов мониторинга
log_info "Создание скриптов мониторинга..."
mkdir -p ~/scripts

# Скрипт проверки здоровья системы
tee ~/scripts/health-check.sh << 'EOF'
#!/bin/bash
echo "=== Проверка здоровья системы ==="
echo "Время: $(date)"
echo "Uptime: $(uptime)"
echo "Использование диска:"
df -h /opt
echo "Использование памяти:"
free -h
echo "Статус Docker:"
systemctl is-active docker
echo "Запущенные контейнеры:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo "Статус nginx:"
systemctl is-active aisha-nginx 2>/dev/null || echo "Не настроен"
EOF

chmod +x ~/scripts/health-check.sh

log_success "Скрипты мониторинга созданы"

# 15. Настройка NTP синхронизации
log_info "Настройка синхронизации времени..."
sudo apt install -y ntp
sudo systemctl enable ntp
sudo systemctl start ntp

log_success "Синхронизация времени настроена"

# Финальная информация
log_success "Настройка продакшн сервера завершена!"

echo -e "\n${GREEN}=== Информация о сервере ===${NC}"
echo "Hostname: $(hostname)"
echo "IP: $(hostname -I | awk '{print $1}')"
echo "Docker версия: $(docker --version)"
echo "Docker Compose версия: $(docker-compose --version)"
echo "Доступные порты: 22, 80, 8443"

echo -e "\n${BLUE}=== Следующие шаги ===${NC}"
echo "1. Скопируйте публичный SSH ключ на dev сервер"
echo "2. Клонируйте репозиторий в /opt/aisha-backend"
echo "3. Скопируйте SSL сертификаты"
echo "4. Создайте файл .env.docker.prod"
echo "5. Запустите развертывание nginx"

echo -e "\n${YELLOW}=== Требуется перезагрузка ===${NC}"
echo "Для применения всех изменений перезагрузите сервер:"
echo "sudo reboot" 