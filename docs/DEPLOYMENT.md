# 🚀 Развертывание Aisha Bot в продакшн

**Статус:** ✅ ПРОТЕСТИРОВАНО В ПРОДАКШНЕ  
**Дата:** 2025-06-09  
**Кластер:** 192.168.0.10 (РАБОТАЕТ)

## 🎯 Архитектура продакшн кластера

### Схема развертывания
```
📡 Nginx Load Balancer (443/80)
     ├── 🌐 Webhook API Cluster  
     │   ├── aisha-webhook-api-1:8001  (FAL AI webhooks)
     │   └── aisha-webhook-api-2:8001  (Load balanced)
     │
     └── 🤖 Bot Processing Cluster
         ├── aisha-bot-polling-1      (Active - получает сообщения)
         ├── aisha-bot-polling-2      (Standby - автоматический failover)
         └── aisha-worker-1           (Background task processing)

🗄️ External Services (существующие)
├── PostgreSQL (aisha_db)
├── Redis (кэширование + очереди)
└── MinIO (файловое хранилище)
```

### Масштабирование и отказоустойчивость

**✅ Преимущества текущей архитектуры:**
- **Polling Active/Standby**: один активный бот, второй на подхвате
- **Worker Pool**: горизонтальное масштабирование обработки
- **Load Balanced API**: webhook'и FAL AI распределяются между экземплярами  
- **Health Monitoring**: автоматическая проверка состояния
- **Zero Downtime**: возможность обновлений без остановки

## 🔧 Финальный деплой

### Быстрый старт (рекомендуется)

```bash
# 1. Установите токен бота
export TELEGRAM_BOT_TOKEN=8063965284:AAHbvpOdnfTopf14xxTLdsXiMEl4sjqEVXU

# 2. Запустите финальный скрипт
./scripts/production/deploy-production-final.sh
```

**Скрипт автоматически выполнит:**
1. ✅ Проверку валидности Telegram токена
2. 🔨 Сборку исправленных Docker образов  
3. 📤 Отправку на локальный регистр (localhost:5000)
4. 🚀 Развертывание на сервере с правильными переменными
5. 🏥 Проверку здоровья всех сервисов

### Ручной деплой (для отладки)

```bash
# 1. Сборка образов
docker build -f docker/Dockerfile.webhook -t localhost:5000/aisha-webhook:latest .
docker build -f docker/Dockerfile.bot -t localhost:5000/aisha-bot:latest .

# 2. Отправка в регистр
docker push localhost:5000/aisha-webhook:latest
docker push localhost:5000/aisha-bot:latest

# 3. Развертывание на сервере
ssh aisha@192.168.0.10 "
    cd /opt/aisha-backend
    export TELEGRAM_BOT_TOKEN='your_token'
    docker-compose -f docker-compose.webhook.prod.yml down
    docker-compose -f docker-compose.bot.registry.yml down
    docker-compose -f docker-compose.webhook.prod.yml up -d
    docker-compose -f docker-compose.bot.registry.yml up -d
"
```

## 📊 Мониторинг

### Скрипт мониторинга

```bash
# Полная проверка системы
./scripts/monitoring/monitor-production.sh

# Быстрая проверка (контейнеры + сводка)
./scripts/monitoring/monitor-production.sh quick

# Проверка конкретных компонентов
./scripts/monitoring/monitor-production.sh logs      # Логи сервисов
./scripts/monitoring/monitor-production.sh health    # Health checks
./scripts/monitoring/monitor-production.sh system    # Ресурсы сервера
./scripts/monitoring/monitor-production.sh telegram  # Telegram API
```

### Ключевые метрики

**Контейнеры (ожидаемое состояние):**
```
aisha-webhook-api-1    Up X hours (healthy)    8001/tcp
aisha-webhook-api-2    Up X hours (healthy)    8001/tcp  
aisha-bot-polling-1    Up X hours (healthy)    
aisha-bot-polling-2    Up X hours (healthy)    # standby
aisha-worker-1         Up X hours (healthy)
aisha-nginx-prod       Up X hours (healthy)    80/tcp, 443/tcp
```

**Системные ресурсы:**
- RAM: ~1.6GB / 31GB (5% использования)
- Диск: ~13GB / 28GB (46% использования)  
- CPU Load: < 1.0 (нормальная нагрузка)

## 🐛 Устранение неполадок

### Известные проблемы и решения

#### 1. "Token is invalid!" ❌→✅
**Проблема:** Бот не мог получить токен из переменных окружения
```bash
# Решение: добавлены обе переменные в docker-compose
- TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
- TELEGRAM_TOKEN=${TELEGRAM_BOT_TOKEN}  # Для совместимости
```

#### 2. Webhook API перезапуски ❌→✅
**Проблема:** uvicorn падал с ошибкой "unrecognized arguments: --worker-class"
```dockerfile
# Было (неправильно):
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--worker-class", "uvicorn.workers.UvicornWorker"]

# Стало (правильно):
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

#### 3. PermissionError на /app/storage ❌→✅
**Проблема:** Права доступа на директории storage
```dockerfile
# Решение в Dockerfile:
RUN mkdir -p /app/storage && chmod 755 /app/storage
```

#### 4. Telegram Conflict Error ❌→✅
**Проблема:** "terminated by other getUpdates request"
```yaml
# Решение: standby режим для второго бота
aisha-bot-polling-2:
  command: ["polling_standby"]  # Задержка 10 сек, не конфликтует
```

#### 5. ImportError в handlers ❌→✅
**Проблема:** `cannot import name 'MainMenuHandler'`
```python
# Было:
from app.handlers.main_menu import MainMenuHandler

# Стало:
from app.handlers.main_menu import show_main_menu
```

### Частые команды диагностики

```bash
# Проверить логи конкретного контейнера
ssh aisha@192.168.0.10 "docker logs aisha-bot-polling-1 --tail 20"

# Перезапустить проблемный сервис
ssh aisha@192.168.0.10 "docker restart aisha-webhook-api-1"

# Проверить переменные окружения
ssh aisha@192.168.0.10 "docker exec aisha-bot-polling-1 env | grep TELEGRAM"

# Очистить старые контейнеры
ssh aisha@192.168.0.10 "docker system prune -f"
```

## 🔄 Обновления

### Обновление кода (zero downtime)

```bash
# 1. Соберите новые образы локально
docker build -f docker/Dockerfile.webhook -t localhost:5000/aisha-webhook:latest .
docker build -f docker/Dockerfile.bot -t localhost:5000/aisha-bot:latest .

# 2. Отправьте в регистр
docker push localhost:5000/aisha-webhook:latest
docker push localhost:5000/aisha-bot:latest

# 3. Обновите на сервере
ssh aisha@192.168.0.10 "
    cd /opt/aisha-backend
    export TELEGRAM_BOT_TOKEN='${TELEGRAM_BOT_TOKEN}'
    
    # Обновляем webhook API (rolling update)
    docker-compose -f docker-compose.webhook.prod.yml pull
    docker-compose -f docker-compose.webhook.prod.yml up -d
    
    # Обновляем bot кластер (standby сначала)
    docker-compose -f docker-compose.bot.registry.yml pull  
    docker stop aisha-bot-polling-2
    docker-compose -f docker-compose.bot.registry.yml up -d aisha-bot-polling-2
    sleep 30
    docker stop aisha-bot-polling-1
    docker-compose -f docker-compose.bot.registry.yml up -d aisha-bot-polling-1
"
```

### Масштабирование

**Добавить worker'ов:**
```yaml
# В docker-compose.bot.registry.yml
aisha-worker-2:
  <<: *worker-template
  container_name: aisha-worker-2
  environment:
    - INSTANCE_ID=worker-2

aisha-worker-3:
  <<: *worker-template  
  container_name: aisha-worker-3
  environment:
    - INSTANCE_ID=worker-3
```

**Добавить webhook API:**
```yaml
# В docker-compose.webhook.prod.yml
aisha-webhook-api-3:
  <<: *api-template
  container_name: aisha-webhook-api-3
  ports:
    - "8003:8001"
```

## 📋 Чек-лист деплоя

### Предварительные проверки
- [ ] ✅ Токен бота валидный (`curl https://api.telegram.org/bot{TOKEN}/getMe`)
- [ ] ✅ SSH доступ к серверу (`ssh aisha@192.168.0.10`)
- [ ] ✅ Docker регистр работает (`curl localhost:5000/v2/_catalog`)
- [ ] ✅ Внешние сервисы доступны (PostgreSQL, Redis, MinIO)

### Процесс деплоя
- [ ] ✅ Образы собраны с исправлениями
- [ ] ✅ Образы отправлены в регистр
- [ ] ✅ Webhook API развернут и здоров
- [ ] ✅ Bot кластер развернут (active + standby)
- [ ] ✅ Nginx перенаправляет трафик
- [ ] ✅ Health checks прошли успешно

### Финальная проверка
- [ ] ✅ Бот отвечает на сообщения
- [ ] ✅ Webhook'и FAL AI работают  
- [ ] ✅ Standby бот готов к переключению
- [ ] ✅ Мониторинг показывает нормальные метрики
- [ ] ✅ Нет ошибок в логах

## 🎯 Результат

**✅ УСПЕШНО РАЗВЕРНУТ ПРОДАКШН КЛАСТЕР:**

- 🌐 **Webhook API**: 2 экземпляра с load balancing
- 🤖 **Bot кластер**: Active/Standby + background workers  
- 📊 **Мониторинг**: автоматические health checks
- 🔄 **Масштабирование**: готов к горизонтальному росту
- 🛡️ **Отказоустойчивость**: failover между экземплярами

**Сервер:** `aisha@192.168.0.10`  
**Статус:** 🟢 РАБОТАЕТ СТАБИЛЬНО  
**Uptime:** Webhook API 3+ часа, Bot cluster 1+ час 