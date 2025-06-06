# Стратегии развертывания в продакшене

## Обзор

Документ описывает различные стратегии развертывания Docker контейнеров на продакшн сервере `192.168.0.10` (Ubuntu 24).

## Архитектура

- **Dev/Staging**: 192.168.0.3 (текущий сервер)
- **Production**: 192.168.0.10 (Ubuntu 24)
- **Сеть**: Локальная сеть 192.168.0.0/24

## Стратегии развертывания

### 1. Git + Docker Build (Рекомендуемая для начала)

**Преимущества:**
- Простота настройки
- Версионирование через Git
- Воспроизводимость сборки

**Недостатки:**
- Время сборки на продакшене
- Зависимость от интернета

#### Настройка

1. **На продакшн сервере:**
```bash
# Клонирование репозитория
git clone <repository_url> /opt/aisha-backend
cd /opt/aisha-backend

# Установка зависимостей
sudo apt update
sudo apt install -y docker.io docker-compose git
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

2. **Скрипт развертывания:**
```bash
#!/bin/bash
# scripts/deploy-production.sh

set -euo pipefail

PROD_SERVER="192.168.0.10"
DEPLOY_USER="aisha"
PROJECT_PATH="/opt/aisha-backend"

deploy_to_production() {
    echo "Развертывание на продакшн сервер $PROD_SERVER..."
    
    ssh $DEPLOY_USER@$PROD_SERVER << 'EOF'
        cd /opt/aisha-backend
        git pull origin main
        chmod +x scripts/*.sh docker/nginx/healthcheck.sh
        sudo ./scripts/deploy-nginx.sh
EOF
}

deploy_to_production
```

### 2. Docker Registry (Для масштабирования)

**Преимущества:**
- Быстрое развертывание
- Единый источник образов
- Версионирование образов

**Недостатки:**
- Требует настройки registry

#### Настройка Private Registry

1. **На Dev сервере (192.168.0.3):**
```bash
# Запуск локального registry
docker run -d -p 5000:5000 --name registry registry:2

# Или через docker-compose
cat > docker-compose.registry.yml << 'EOF'
version: '3.8'
services:
  registry:
    image: registry:2
    ports:
      - "5000:5000"
    volumes:
      - registry_data:/var/lib/registry
    restart: unless-stopped

volumes:
  registry_data:
EOF

docker-compose -f docker-compose.registry.yml up -d
```

2. **Скрипт сборки и push:**
```bash
#!/bin/bash
# scripts/build-and-push.sh

REGISTRY="192.168.0.3:5000"
IMAGE_NAME="aisha-nginx"
VERSION=$(git rev-parse --short HEAD)

# Сборка образа
docker build -t $REGISTRY/$IMAGE_NAME:$VERSION docker/nginx/
docker build -t $REGISTRY/$IMAGE_NAME:latest docker/nginx/

# Push в registry
docker push $REGISTRY/$IMAGE_NAME:$VERSION
docker push $REGISTRY/$IMAGE_NAME:latest

echo "Образ $REGISTRY/$IMAGE_NAME:$VERSION опубликован"
```

3. **На продакшн сервере:**
```bash
# Настройка insecure registry
echo '{"insecure-registries": ["192.168.0.3:5000"]}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker

# Pull и запуск
docker pull 192.168.0.3:5000/aisha-nginx:latest
```

### 3. Docker Save/Load (Для ограниченной сети)

**Преимущества:**
- Работает без интернета
- Полный контроль над образами

**Недостатки:**
- Ручная передача файлов
- Размер образов

#### Процедура

1. **На Dev сервере:**
```bash
# Сборка образа
docker-compose -f docker-compose.prod.yml build nginx

# Сохранение в файл
docker save aisha-backend_nginx:latest | gzip > nginx-image.tar.gz

# Передача на продакшн
scp nginx-image.tar.gz aisha@192.168.0.10:/tmp/
```

2. **На продакшн сервере:**
```bash
# Загрузка образа
gunzip -c /tmp/nginx-image.tar.gz | docker load

# Запуск
docker-compose -f docker-compose.prod.yml up -d nginx
```

### 4. CI/CD Pipeline (Продвинутая стратегия)

Использование GitLab CI/Jenkins/GitHub Actions для автоматизации.

#### Пример GitLab CI (.gitlab-ci.yml):
```yaml
stages:
  - build
  - deploy

variables:
  DOCKER_REGISTRY: "192.168.0.3:5000"
  IMAGE_NAME: "aisha-nginx"

build_nginx:
  stage: build
  script:
    - docker build -t $DOCKER_REGISTRY/$IMAGE_NAME:$CI_COMMIT_SHA docker/nginx/
    - docker push $DOCKER_REGISTRY/$IMAGE_NAME:$CI_COMMIT_SHA
    - docker tag $DOCKER_REGISTRY/$IMAGE_NAME:$CI_COMMIT_SHA $DOCKER_REGISTRY/$IMAGE_NAME:latest
    - docker push $DOCKER_REGISTRY/$IMAGE_NAME:latest

deploy_production:
  stage: deploy
  script:
    - ssh aisha@192.168.0.10 "cd /opt/aisha-backend && ./scripts/deploy-from-registry.sh $CI_COMMIT_SHA"
  only:
    - main
```

## Подготовка продакшн сервера

### 1. Базовая настройка

```bash
#!/bin/bash
# scripts/setup-production-server.sh

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Создание структуры директорий
sudo mkdir -p /opt/aisha-backend
sudo chown $USER:$USER /opt/aisha-backend

# Настройка firewall
sudo ufw allow 80
sudo ufw allow 8443
sudo ufw allow 22
sudo ufw --force enable

# Настройка логротate
sudo tee /etc/logrotate.d/aisha-docker << 'EOF'
/opt/aisha-backend/logs/*/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
```

### 2. SSL сертификаты

```bash
# Копирование сертификатов
scp ssl_certificate/* aisha@192.168.0.10:/opt/aisha-backend/ssl_certificate/

# Или настройка Let's Encrypt
ssh aisha@192.168.0.10 << 'EOF'
sudo apt install -y certbot
sudo certbot certonly --standalone -d aibots.kz
sudo cp /etc/letsencrypt/live/aibots.kz/fullchain.pem /opt/aisha-backend/ssl_certificate/aibots_kz_full.crt
sudo cp /etc/letsencrypt/live/aibots.kz/privkey.pem /opt/aisha-backend/ssl_certificate/aibots.kz.key
sudo chown aisha:aisha /opt/aisha-backend/ssl_certificate/*
EOF
```

### 3. Переменные окружения

```bash
# Создание .env.docker.prod на продакшене
scp .env.docker.prod aisha@192.168.0.10:/opt/aisha-backend/

# Или создание через SSH
ssh aisha@192.168.0.10 << 'EOF'
cat > /opt/aisha-backend/.env.docker.prod << 'ENVEOF'
# Продакшн переменные
DATABASE_HOST=192.168.0.10
REDIS_HOST=192.168.0.3
MINIO_ENDPOINT=192.168.0.3:9000
ENVIRONMENT=production
DEBUG=false
# ... остальные переменные
ENVEOF
EOF
```

## Процедуры развертывания

### Blue-Green Deployment

Стратегия для zero-downtime deployment:

```bash
#!/bin/bash
# scripts/blue-green-deploy.sh

BLUE_COMPOSE="docker-compose.blue.yml"
GREEN_COMPOSE="docker-compose.green.yml"
CURRENT_COLOR=$(docker ps --format "table {{.Names}}" | grep nginx | head -1 | cut -d'-' -f3)

if [ "$CURRENT_COLOR" = "blue" ]; then
    NEW_COLOR="green"
    NEW_COMPOSE=$GREEN_COMPOSE
    OLD_COMPOSE=$BLUE_COMPOSE
else
    NEW_COLOR="blue"
    NEW_COMPOSE=$BLUE_COMPOSE
    OLD_COMPOSE=$GREEN_COMPOSE
fi

echo "Развертывание $NEW_COLOR окружения..."

# Запуск нового окружения
docker-compose -f $NEW_COMPOSE up -d nginx

# Проверка здоровья
sleep 10
if curl -f http://localhost:8080/health; then
    echo "Переключение трафика на $NEW_COLOR..."
    
    # Обновление nginx upstream или load balancer
    # Здесь логика переключения трафика
    
    # Остановка старого окружения
    docker-compose -f $OLD_COMPOSE down
    echo "Развертывание завершено!"
else
    echo "Health check не прошел, откат..."
    docker-compose -f $NEW_COMPOSE down
    exit 1
fi
```

### Rolling Update

Для обновления с минимальным downtime:

```bash
#!/bin/bash
# scripts/rolling-update.sh

# Обновление образа
docker-compose -f docker-compose.prod.yml pull nginx

# Пересоздание контейнера
docker-compose -f docker-compose.prod.yml up -d --no-deps nginx

# Проверка
sleep 5
./scripts/nginx-management.sh health
```

### Hotfix Deployment

Для экстренных исправлений:

```bash
#!/bin/bash
# scripts/hotfix-deploy.sh

HOTFIX_BRANCH=${1:-hotfix}

echo "Развертывание hotfix из ветки $HOTFIX_BRANCH..."

# Переключение на hotfix ветку
git fetch origin
git checkout $HOTFIX_BRANCH
git pull origin $HOTFIX_BRANCH

# Быстрая пересборка и развертывание
docker-compose -f docker-compose.prod.yml build --no-cache nginx
docker-compose -f docker-compose.prod.yml up -d nginx

# Проверка
./scripts/nginx-management.sh health

echo "Hotfix развернут!"
```

## Мониторинг развертывания

### Health Checks

```bash
#!/bin/bash
# scripts/deployment-health-check.sh

PROD_SERVER="192.168.0.10"

echo "Проверка здоровья на $PROD_SERVER..."

ssh aisha@$PROD_SERVER << 'EOF'
cd /opt/aisha-backend

# Проверка контейнеров
echo "=== Статус контейнеров ==="
docker-compose -f docker-compose.prod.yml ps

# Проверка логов
echo "=== Последние логи nginx ==="
docker-compose -f docker-compose.prod.yml logs --tail=10 nginx

# Health checks
echo "=== Health Checks ==="
./scripts/nginx-management.sh health

# Проверка ресурсов
echo "=== Использование ресурсов ==="
./scripts/nginx-management.sh metrics
EOF
```

### Rollback Process

```bash
#!/bin/bash
# scripts/rollback.sh

ROLLBACK_VERSION=${1:-HEAD~1}

echo "Откат к версии $ROLLBACK_VERSION..."

# Откат кода
git checkout $ROLLBACK_VERSION

# Пересборка и развертывание
docker-compose -f docker-compose.prod.yml build nginx
docker-compose -f docker-compose.prod.yml up -d nginx

# Проверка
./scripts/nginx-management.sh health

echo "Откат завершен!"
```

## Backup и Restore

### Backup Process

```bash
#!/bin/bash
# scripts/backup-production.sh

BACKUP_DIR="/opt/backups/aisha-$(date +%Y%m%d_%H%M%S)"
PROD_SERVER="192.168.0.10"

ssh aisha@$PROD_SERVER << EOF
mkdir -p $BACKUP_DIR

# Backup контейнеров
docker save \$(docker images --format "{{.Repository}}:{{.Tag}}" | grep aisha) | gzip > $BACKUP_DIR/images.tar.gz

# Backup конфигурации
cp -r /opt/aisha-backend/docker $BACKUP_DIR/
cp -r /opt/aisha-backend/ssl_certificate $BACKUP_DIR/
cp /opt/aisha-backend/.env.docker.prod $BACKUP_DIR/

# Backup логов
tar -czf $BACKUP_DIR/logs.tar.gz /opt/aisha-backend/logs/

echo "Backup создан в $BACKUP_DIR"
EOF
```

### Restore Process

```bash
#!/bin/bash
# scripts/restore-production.sh

BACKUP_DIR=${1:-/opt/backups/latest}
PROD_SERVER="192.168.0.10"

ssh aisha@$PROD_SERVER << EOF
cd $BACKUP_DIR

# Восстановление образов
gunzip -c images.tar.gz | docker load

# Восстановление конфигурации
cp -r docker/* /opt/aisha-backend/docker/
cp -r ssl_certificate/* /opt/aisha-backend/ssl_certificate/
cp .env.docker.prod /opt/aisha-backend/

# Перезапуск сервисов
cd /opt/aisha-backend
docker-compose -f docker-compose.prod.yml up -d

echo "Восстановление завершено"
EOF
```

## Рекомендации по безопасности

### 1. SSH ключи
```bash
# Настройка SSH ключей для автоматизации
ssh-keygen -t rsa -b 4096 -C "deploy@aisha-backend"
ssh-copy-id aisha@192.168.0.10
```

### 2. Docker секреты
```bash
# Использование Docker secrets
echo "sensitive_data" | docker secret create my_secret -
```

### 3. Ограничение доступа
```bash
# Настройка sudo для пользователя deploy
echo "aisha ALL=(ALL) NOPASSWD: /opt/aisha-backend/scripts/deploy-nginx.sh" | sudo tee /etc/sudoers.d/aisha-deploy
```

## Выбор стратегии

### Для начала (рекомендуется):
**Git + Docker Build** - простота и надежность

### Для развития:
**Docker Registry** - скорость и масштабируемость

### Для enterprise:
**CI/CD Pipeline** - полная автоматизация

## Чек-лист развертывания

- [ ] Продакшн сервер настроен
- [ ] SSL сертификаты скопированы
- [ ] Переменные окружения настроены
- [ ] Docker и Docker Compose установлены
- [ ] Сеть и firewall настроены
- [ ] Backup процедуры протестированы
- [ ] Мониторинг настроен
- [ ] Rollback процедуры протестированы 