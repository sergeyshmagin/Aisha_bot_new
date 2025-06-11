# Развёртывание Webhook Сервисов

## Обзор

Webhook сервисы отвечают за приём уведомлений от FAL AI о статусе обучения аватаров. Архитектура включает:

- **2 экземпляра Webhook API** (load balancing)
- **Nginx Load Balancer** (распределение нагрузки)
- **Docker Registry** на 192.168.0.4:5000 (хранение образов)

## Архитектура

```
                    ┌─────────────────┐
                    │   Nginx LB      │
                    │   (80/443)      │
                    └─────────┬───────┘
                              │
                    ┌─────────┴───────┐
                    │                 │
            ┌───────▼──────┐  ┌──────▼──────┐
            │ Webhook API  │  │ Webhook API │
            │ Instance #1  │  │ Instance #2 │
            │   (8001)     │  │   (8002)    │
            └──────────────┘  └─────────────┘
                    │                 │
                    └─────────┬───────┘
                              │
                    ┌─────────▼───────┐
                    │   Database      │
                    │ PostgreSQL      │
                    │ (192.168.0.4)   │
                    └─────────────────┘
```

## Предварительные требования

### 1. Зависимости

- **Docker** и **Docker Compose**
- **curl** для проверки health endpoints
- Доступ к Docker Registry на **192.168.0.4:5000**

### 2. Файлы конфигурации

Убедитесь что у вас есть файл `prod.env` в корне проекта:

```bash
# Database
DATABASE_URL=postgresql://aisha_user:aisha_pass_2024@192.168.0.4:5432/aisha_db

# Redis
REDIS_URL=redis://192.168.0.3:6379/0

# MinIO
MINIO_ENDPOINT=192.168.0.4:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=aisha-files
MINIO_SECURE=false

# FAL AI
FAL_API_KEY=your_fal_api_key_here
FAL_WEBHOOK_SECRET=your_webhook_secret_here

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## Развёртывание

### Полное развёртывание

Для первого развёртывания или полного пересоздания сервисов:

```bash
./scripts/deploy/webhook-complete.sh
```

Этот скрипт:
1. ✅ Собирает образы `webhook-api` и `nginx-webhook`
2. ✅ Пушит их в реестр 192.168.0.4:5000  
3. ✅ Создаёт Docker сеть `aisha_webhook_cluster`
4. ✅ Останавливает старые контейнеры
5. ✅ Запускает новые контейнеры
6. ✅ Проверяет работоспособность сервисов

### Быстрое обновление образов

Для обновления кода без пересоздания сервисов:

```bash
./scripts/deploy/update-webhook-images.sh
```

Этот скрипт:
1. ✅ Собирает новые образы
2. ✅ Пушит в реестр
3. ✅ Перезапускает контейнеры с новыми образами

## Управление сервисами

### Просмотр статуса
```bash
docker-compose -f docker-compose.webhook.prod.yml --env-file prod.env ps
```

### Просмотр логов
```bash
# Все сервисы
docker-compose -f docker-compose.webhook.prod.yml --env-file prod.env logs -f

# Только webhook API
docker-compose -f docker-compose.webhook.prod.yml --env-file prod.env logs -f aisha-webhook-api-1

# Только nginx  
docker-compose -f docker-compose.webhook.prod.yml --env-file prod.env logs -f aisha-nginx-webhook
```

### Перезапуск сервисов
```bash
# Все сервисы
docker-compose -f docker-compose.webhook.prod.yml --env-file prod.env restart

# Конкретный сервис
docker-compose -f docker-compose.webhook.prod.yml --env-file prod.env restart aisha-webhook-api-1
```

### Остановка сервисов
```bash
docker-compose -f docker-compose.webhook.prod.yml --env-file prod.env down
```

## Проверка работоспособности

### Health Check Endpoints

```bash
# Через nginx load balancer
curl -f http://localhost/health

# Прямое подключение к API инстансам
curl -f http://localhost:8001/health  # API #1
curl -f http://localhost:8002/health  # API #2
```

### Тестирование webhook endpoint

```bash
# FAL AI webhook URL (через nginx)
curl -X POST http://localhost/api/v1/avatar/status_update \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "request_id": "test-123"}'
```

## Мониторинг

### Проверка Docker Registry

```bash
# Список образов в реестре
curl -s http://192.168.0.4:5000/v2/_catalog

# Теги webhook-api
curl -s http://192.168.0.4:5000/v2/webhook-api/tags/list

# Теги nginx-webhook  
curl -s http://192.168.0.4:5000/v2/nginx-webhook/tags/list
```

### Мониторинг контейнеров

```bash
# Статистика использования ресурсов
docker stats aisha-webhook-api-1 aisha-webhook-api-2 aisha-nginx-webhook

# Детальная информация о контейнере
docker inspect aisha-webhook-api-1
```

## Устранение неполадок

### Проблема: Контейнеры не запускаются

1. **Проверьте логи:**
   ```bash
   docker-compose -f docker-compose.webhook.prod.yml --env-file prod.env logs
   ```

2. **Проверьте переменные окружения:**
   ```bash
   # Убедитесь что prod.env содержит все необходимые переменные
   cat prod.env
   ```

3. **Проверьте сеть:**
   ```bash
   docker network ls | grep aisha_webhook_cluster
   ```

### Проблема: Health checks не проходят

1. **Проверьте порты:**
   ```bash
   netstat -tlnp | grep -E "(8001|8002|80|443)"
   ```

2. **Проверьте подключение к базе данных:**
   ```bash
   # Из контейнера webhook
   docker exec -it aisha-webhook-api-1 curl http://localhost:8000/health
   ```

### Проблема: Образы не находятся в реестре

1. **Проверьте доступность реестра:**
   ```bash
   curl -s http://192.168.0.4:5000/v2/_catalog
   ```

2. **Пересоберите и запушьте образы:**
   ```bash
   ./scripts/deploy/update-webhook-images.sh
   ```

## Конфигурация FAL AI

После успешного развёртывания настройте webhook URL в FAL AI:

**Webhook URL:** `https://aibots.kz:8443/api/v1/avatar/status_update`

Этот URL должен быть настроен в настройках FAL AI проекта для получения уведомлений о статусе обучения аватаров.

## Безопасность

1. **Webhook Secret:** Используйте надёжный секрет в `FAL_WEBHOOK_SECRET`
2. **HTTPS:** В продакшене обязательно используйте HTTPS
3. **Firewall:** Ограничьте доступ к портам 8001, 8002 только от nginx
4. **Логи:** Регулярно просматривайте логи на предмет подозрительной активности

## Обновления

Для обновления компонентов:

1. **Обновление кода приложения:** `./scripts/deploy/update-webhook-images.sh`
2. **Обновление конфигурации nginx:** Отредактируйте `docker/nginx/nginx.conf` и перезапустите
3. **Обновление переменных окружения:** Отредактируйте `prod.env` и перезапустите сервисы

## Бэкап и восстановление

### Экспорт образов

```bash
# Экспорт образов для бэкапа
docker save 192.168.0.4:5000/webhook-api:latest > webhook-api-backup.tar
docker save 192.168.0.4:5000/nginx-webhook:latest > nginx-webhook-backup.tar
```

### Импорт образов

```bash
# Восстановление из бэкапа
docker load < webhook-api-backup.tar
docker load < nginx-webhook-backup.tar
``` 