# 🚀 Кластерное развертывание Aisha Bot v2.0

## 📋 Обзор архитектуры

Горизонтально масштабируемая архитектура Aisha Bot с использованием внешних сервисов:

### 🏗️ Компоненты кластера

- **Сервер приложений**: `192.168.0.10` (aibots.kz)
- **Redis сервер**: `192.168.0.3` (сессии aiogram + кеш)
- **Database/Storage сервер**: `192.168.0.4` (PostgreSQL + MinIO + Registry)

### 🐳 Контейнеры

1. **Nginx Load Balancer** - маршрутизация и SSL терминация
2. **Webhook API кластер** (2 экземпляра) - обработка webhooks FAL.ai
3. **Telegram Bot кластер** (2 экземпляра) - основной и резервный
4. **Background Worker** - фоновые задачи

## 🛠️ Предварительные требования

### Системные требования
- Docker 24.0+
- Docker Compose 2.0+
- 4GB RAM минимум (рекомендуется 8GB)
- 20GB свободного места на диске

### Внешние сервисы (должны быть запущены)
- **PostgreSQL** на `192.168.0.4:5432`
- **Redis** на `192.168.0.3:6379`
- **MinIO** на `192.168.0.4:9000`

### SSL сертификаты
Поместите в папку `ssl/`:
- `aibots_kz.crt` - основной сертификат
- `aibots_kz.key` - приватный ключ
- `aibots_kz.ca-bundle` - промежуточные сертификаты (опционально)

## 🔧 Настройка

### 1. Конфигурация переменных окружения

Скопируйте и настройте файл переменных:
```bash
cp cluster.env.example cluster.env
```

Обязательно заполните:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
FAL_API_KEY=your_fal_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Проверка подключения к внешним сервисам

```bash
# PostgreSQL
telnet 192.168.0.4 5432

# Redis
telnet 192.168.0.3 6379

# MinIO
telnet 192.168.0.4 9000
```

## 🚀 Развертывание

### Автоматическое развертывание

```bash
# Полное развертывание кластера
./deploy-cluster.sh
```

Скрипт автоматически:
1. ✅ Проверит предварительные условия
2. 🔐 Подготовит SSL сертификаты
3. 🏗️ Соберет Docker образы
4. 🌐 Проверит внешние сервисы
5. 🛑 Остановит старые контейнеры
6. 🚀 Развернет новый кластер
7. 🏥 Проверит здоровье сервисов

### Ручное развертывание

#### 1. Сборка образов
```bash
# Nginx
docker build -f docker/nginx/Dockerfile -t aisha-nginx:latest docker/nginx/

# Webhook API
docker build -f docker/Dockerfile.webhook --target production -t aisha-webhook:latest .

# Bot
docker build -f docker/Dockerfile.bot --target production -t aisha-bot:latest .
```

#### 2. Создание сетей
```bash
docker network create aisha_cluster --subnet=172.25.0.0/16
docker network create aisha_bot_cluster --subnet=172.26.0.0/16
```

#### 3. Развертывание API кластера
```bash
docker-compose -f docker-compose.prod.yml --env-file cluster.env up -d
```

#### 4. Развертывание Bot кластера
```bash
docker-compose -f docker-compose.bot.prod.yml --env-file cluster.env up -d
```

## 📊 Мониторинг

### Интерактивный мониторинг
```bash
./monitor-cluster.sh
```

### Быстрая проверка статуса
```bash
./monitor-cluster.sh status
```

### Просмотр логов
```bash
./monitor-cluster.sh logs
```

### Системные ресурсы
```bash
./monitor-cluster.sh resources
```

## 🔍 Диагностика

### Проверка контейнеров
```bash
docker ps --filter "label=com.aisha.service"
```

### Проверка логов отдельных сервисов
```bash
# Nginx
docker logs aisha-nginx-prod -f

# API
docker logs aisha-webhook-api-1 -f
docker logs aisha-webhook-api-2 -f

# Боты
docker logs aisha-bot-polling-1 -f
docker logs aisha-bot-polling-2 -f

# Worker
docker logs aisha-worker-1 -f
```

### Проверка сети
```bash
# Сети Docker
docker network ls --filter "name=aisha"

# Порты
netstat -tlnp | grep -E ':80|:8443'

# Тест API
curl -k https://localhost:8443/health
```

## 🛠️ Управление кластером

### Перезапуск отдельных сервисов

```bash
# Перезапуск nginx
docker restart aisha-nginx-prod

# Перезапуск API
docker restart aisha-webhook-api-1 aisha-webhook-api-2

# Перезапуск ботов
docker restart aisha-bot-polling-1 aisha-bot-polling-2
```

### Масштабирование

#### Добавление экземпляра webhook API
```bash
docker run -d \
  --name aisha-webhook-api-3 \
  --network aisha_cluster \
  --ip 172.25.0.22 \
  --env-file cluster.env \
  --label "com.aisha.service=webhook-api" \
  --label "com.aisha.instance=additional" \
  aisha-webhook:latest
```

#### Обновление nginx конфигурации
Добавьте новый upstream сервер в `docker/nginx/nginx.conf` и пересоберите:
```bash
docker build -f docker/nginx/Dockerfile -t aisha-nginx:latest docker/nginx/
docker restart aisha-nginx-prod
```

### Обновление кода

1. Остановите сервисы:
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.bot.prod.yml down
```

2. Пересоберите образы:
```bash
./deploy-cluster.sh
```

## 🏥 Health Checks

### Автоматические проверки

Все контейнеры имеют встроенные health checks:
- **Nginx**: проверка статуса каждые 15 секунд
- **API**: проверка `/health` каждые 30 секунд  
- **Боты**: проверка процесса каждые 60 секунд
- **Worker**: проверка процесса каждые 60 секунд

### Ручные проверки

```bash
# Общее здоровье
curl -k https://aibots.kz:8443/health

# Nginx статус
curl http://aibots.kz/nginx-health

# API статус
curl -k https://aibots.kz:8443/api/health

# Docker health
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## 🔐 Безопасность

### SSL/TLS
- Автоматическое перенаправление HTTP → HTTPS
- TLS 1.2+ only
- HSTS headers
- Secure cipher suites

### Сетевая изоляция
- Отдельные Docker сети для разных компонентов
- Ограничение доступа только к необходимым портам
- Внутренняя коммуникация через приватные IP

### Мониторинг безопасности
```bash
# Проверка открытых портов
nmap localhost

# Проверка SSL
openssl s_client -connect aibots.kz:8443 -verify_return_error

# Логи безопасности
docker logs aisha-nginx-prod | grep -E "(error|deny|403|404)"
```

## 🚨 Troubleshooting

### Распространенные проблемы

#### 1. Контейнеры не запускаются
```bash
# Проверка логов
docker logs <container_name>

# Проверка ресурсов
docker system df
df -h

# Очистка системы
docker system prune -f
```

#### 2. API не отвечает
```bash
# Проверка upstream
docker exec aisha-nginx-prod nginx -t

# Проверка сети
docker network inspect aisha_cluster

# Перезапуск API кластера
docker restart aisha-webhook-api-1 aisha-webhook-api-2
```

#### 3. Бот не получает сообщения
```bash
# Проверка токена
docker logs aisha-bot-polling-1 | grep -i token

# Проверка Redis сессий
docker exec -it aisha-bot-polling-1 redis-cli -h 192.168.0.3 ping

# Проверка webhook URL
curl -k https://aibots.kz:8443/api/v1/avatar/status_update
```

#### 4. Проблемы с SSL
```bash
# Проверка сертификатов
openssl x509 -in ssl/aibots_kz.crt -text -noout

# Проверка приватного ключа
openssl rsa -in ssl/aibots_kz.key -check

# Тест соответствия
openssl x509 -noout -modulus -in ssl/aibots_kz.crt | openssl md5
openssl rsa -noout -modulus -in ssl/aibots_kz.key | openssl md5
```

### Аварийное восстановление

#### Быстрый rollback
```bash
# Остановка текущего кластера
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.bot.prod.yml down

# Запуск предыдущей версии
docker-compose -f docker-compose.webhook.prod.yml up -d
```

#### Восстановление данных
```bash
# Проверка подключения к PostgreSQL
docker run --rm -it postgres:15 psql -h 192.168.0.4 -U aisha_user -d aisha

# Проверка MinIO
docker run --rm -it minio/mc mc ls minio-server/generated/
```

## 📈 Мониторинг производительности

### Метрики Docker
```bash
# Использование ресурсов
docker stats --no-stream

# Система Docker
docker system df

# События
docker events --filter container=aisha-nginx-prod
```

### Метрики приложения
```bash
# Логи производительности
docker logs aisha-webhook-api-1 | grep -E "(response_time|duration)"

# Мониторинг Redis
docker exec -it aisha-bot-polling-1 redis-cli -h 192.168.0.3 info stats
```

## 📞 Поддержка

При возникновении проблем:

1. Запустите полную диагностику: `./monitor-cluster.sh report > cluster-report.txt`
2. Соберите логи: `./monitor-cluster.sh logs > cluster-logs.txt`
3. Проверьте внешние сервисы
4. Обратитесь к команде разработки с отчетами

---

**Версия документа**: 2.0  
**Дата обновления**: 2025-01-06  
**Автор**: Aisha AI Development Team 