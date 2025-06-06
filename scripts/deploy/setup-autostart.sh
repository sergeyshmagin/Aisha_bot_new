#!/bin/bash

# ============================================================================
# ⚡ AUTOSTART SETUP SCRIPT
# ============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}⚡ Настройка автозапуска сервисов...${NC}"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# 🗄️ НАСТРОЙКА АВТОЗАПУСКА DOCKER REGISTRY (192.168.0.4)
# ============================================================================

log_info "Настройка автозапуска Docker Registry..."

ssh aisha@192.168.0.4 << 'EOF'
    # Создание systemd сервиса для Registry
    sudo tee /etc/systemd/system/docker-registry.service > /dev/null << 'SERVICE'
[Unit]
Description=Docker Registry Server
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStartPre=-/usr/bin/docker stop registry-server
ExecStartPre=-/usr/bin/docker rm registry-server
ExecStart=/usr/bin/docker run -d \
    --name registry-server \
    --restart=always \
    -p 5000:5000 \
    -v /home/aisha/docker-registry:/var/lib/registry \
    registry:2
ExecStop=/usr/bin/docker stop registry-server
ExecStopPost=/usr/bin/docker rm registry-server

[Install]
WantedBy=multi-user.target
SERVICE
    
    # Включение и запуск сервиса
    sudo systemctl daemon-reload
    sudo systemctl enable docker-registry.service
    sudo systemctl start docker-registry.service
    
    echo "✅ Docker Registry автозапуск настроен"
    sudo systemctl status docker-registry.service --no-pager
EOF

# ============================================================================
# 🗄️ НАСТРОЙКА АВТОЗАПУСКА POSTGRESQL + MINIO (192.168.0.4)
# ============================================================================

log_info "Настройка автозапуска PostgreSQL и MinIO..."

ssh aisha@192.168.0.4 << 'EOF'
    # Создание docker-compose файла для инфраструктуры
    cat > ~/infrastructure-compose.yml << 'COMPOSE'
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: postgres-main
    restart: always
    environment:
      POSTGRES_DB: aisha
      POSTGRES_USER: aisha
      POSTGRES_PASSWORD: securePwd2024
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aisha"]
      interval: 30s
      timeout: 10s
      retries: 5

  minio:
    image: minio/minio:latest
    container_name: minio-main
    restart: always
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin123
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

volumes:
  postgres_data:
  minio_data:
COMPOSE
    
    # Создание systemd сервиса для инфраструктуры
    sudo tee /etc/systemd/system/infrastructure.service > /dev/null << 'SERVICE'
[Unit]
Description=Infrastructure Services (PostgreSQL + MinIO)
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/aisha
ExecStart=/usr/bin/docker-compose -f infrastructure-compose.yml up -d
ExecStop=/usr/bin/docker-compose -f infrastructure-compose.yml down

[Install]
WantedBy=multi-user.target
SERVICE
    
    # Включение и запуск сервиса
    sudo systemctl daemon-reload
    sudo systemctl enable infrastructure.service
    sudo systemctl start infrastructure.service
    
    echo "✅ Infrastructure автозапуск настроен"
    sudo systemctl status infrastructure.service --no-pager
EOF

# ============================================================================
# 🤖 НАСТРОЙКА АВТОЗАПУСКА WEBHOOK API (192.168.0.10)
# ============================================================================

log_info "Настройка автозапуска Webhook API..."

ssh aisha@192.168.0.10 << 'EOF'
    # Создание systemd сервиса для Webhook API
    sudo tee /etc/systemd/system/webhook-api.service > /dev/null << 'SERVICE'
[Unit]
Description=Webhook API Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/aisha
ExecStart=/usr/bin/docker-compose -f docker-compose.webhook.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.webhook.prod.yml down
ExecReload=/usr/bin/docker-compose -f docker-compose.webhook.prod.yml restart

[Install]
WantedBy=multi-user.target
SERVICE
    
    # Включение и запуск сервиса
    sudo systemctl daemon-reload
    sudo systemctl enable webhook-api.service
    sudo systemctl start webhook-api.service
    
    echo "✅ Webhook API автозапуск настроен"
    sudo systemctl status webhook-api.service --no-pager
EOF

# ============================================================================
# ✅ ПРОВЕРКА СТАТУСА ВСЕХ СЕРВИСОВ
# ============================================================================

log_info "Проверка статуса всех сервисов..."

echo ""
echo "🔍 Статус сервисов на 192.168.0.4:"
ssh aisha@192.168.0.4 << 'EOF'
    echo "Docker Registry:"
    sudo systemctl is-active docker-registry.service
    echo "Infrastructure:"
    sudo systemctl is-active infrastructure.service
    echo "Контейнеры:"
    sudo docker ps --format "table {{.Names}}\t{{.Status}}"
EOF

echo ""
echo "🔍 Статус сервисов на 192.168.0.10:"
ssh aisha@192.168.0.10 << 'EOF'
    echo "Webhook API:"
    sudo systemctl is-active webhook-api.service
    echo "Контейнеры:"
    sudo docker ps --format "table {{.Names}}\t{{.Status}}"
EOF

echo ""
echo -e "${GREEN}🎉 Автозапуск настроен для всех сервисов!${NC}"
echo ""
echo "📊 Управление сервисами:"
echo "  Registry:       systemctl {start|stop|restart|status} docker-registry.service"
echo "  Infrastructure: systemctl {start|stop|restart|status} infrastructure.service"  
echo "  Webhook API:    systemctl {start|stop|restart|status} webhook-api.service"
echo ""
echo "🔧 Полезные команды:"
echo "  sudo systemctl list-units --type=service | grep -E '(docker-registry|infrastructure|webhook-api)'"
echo "  journalctl -u docker-registry.service -f"
echo "  journalctl -u infrastructure.service -f"
echo "  journalctl -u webhook-api.service -f" 