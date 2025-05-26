# 📋 Краткая сводка: Продакшн развертывание (только Bot + API)

## 🖥️ Системные требования для 5000+ пользователей

> **Примечание**: PostgreSQL, Redis и MinIO развернуты на отдельных серверах

### Минимум (до 2000 пользователей):
- **CPU**: 2 cores (4 threads)
- **RAM**: 4 GB
- **SSD**: 50 GB
- **Network**: 1 Gbps

### Рекомендуемо (до 5000+ пользователей):
- **CPU**: 4 cores (8 threads) 
- **RAM**: 8 GB
- **SSD**: 100 GB (NVMe)
- **Network**: 1 Gbps+

### Распределение ресурсов:
```
🤖 Telegram Bot:    1.5-3 GB RAM, 100-200% CPU
📡 API Server:      0.5-1 GB RAM, 25-50% CPU  
🔄 System/Other:    1-2 GB RAM, 25-50% CPU
Total:              3-6 GB RAM, 150-300% CPU
```

## ⚡ Быстрый запуск

### 1. Автоматическая установка
```bash
# Скачайте и запустите скрипт развертывания
sudo bash scripts/deploy_production_minimal.sh
```

### 2. Ручная настройка конфигурации
```bash
# Основная конфигурация
sudo nano /opt/aisha_bot/.env

# API сервер
sudo nano /opt/aisha_bot/api_server/.env
```

### 3. Копирование проекта и SSL
```bash
# Код проекта
sudo cp -r . /opt/aisha_bot/
sudo chown -R aisha:aisha /opt/aisha_bot/

# SSL сертификаты
sudo cp ssl_certificate/* /opt/aisha_bot/api_server/ssl/
sudo chmod 600 /opt/aisha_bot/api_server/ssl/*.key
```

### 4. Установка зависимостей
```bash
sudo -u aisha bash
cd /opt/aisha_bot
source venv/bin/activate
pip install -r requirements.txt
cd api_server && pip install -r requirements.txt
```

### 5. Миграции БД (на внешнем сервере)
```bash
# Если нужно выполнить миграции с этого сервера
alembic upgrade head
```

### 6. Запуск сервисов
```bash
sudo systemctl start aisha-bot aisha-api
sudo systemctl status aisha-bot aisha-api
```

## 🔧 Архитектура продакшн

```
┌─────────────────────────────────────────┐
│         Application Server              │
│            Ubuntu 24.04                 │
├─────────────────────────────────────────┤
│  🤖 Telegram Bot                       │ ← systemd: aisha-bot.service
│     ├── Aiogram 3.3                    │   RAM: 1.5-3 GB
│     ├── SQLAlchemy async               │   CPU: 100-200%
│     └── FAL AI integration             │
├─────────────────────────────────────────┤
│  📡 API Server (HTTPS:8443)            │ ← systemd: aisha-api.service  
│     ├── FastAPI + uvicorn              │   RAM: 0.5-1 GB
│     ├── SSL certificates               │   CPU: 25-50%
│     └── Webhook processing             │
└─────────────────────────────────────────┘
              ↓ Network ↓
┌─────────────────────────────────────────┐
│           External Services             │
├─────────────────────────────────────────┤
│  🗄️ PostgreSQL Server                  │ ← Уже развернут
│     ├── Database: aisha_bot_prod        │
│     └── Async connections              │
├─────────────────────────────────────────┤
│  🔴 Redis Server                       │ ← Уже развернут
│     ├── Cache & Sessions               │
│     └── Background tasks               │
├─────────────────────────────────────────┤
│  📦 MinIO Server                       │ ← Уже развернут
│     ├── User uploads                   │
│     └── Generated images               │
└─────────────────────────────────────────┘
```

## 🚀 Процессы в продакшн

### Основные сервисы:
1. **aisha-bot.service** - Основной Telegram бот
2. **aisha-api.service** - API сервер для webhook

### Внешние зависимости:
- **PostgreSQL** - База данных (внешний сервер)
- **Redis** - Кэш и сессии (внешний сервер)  
- **MinIO** - Хранение файлов (внешний сервер)

### Мониторинг:
- **Health check** (каждые 5 минут) - автоперезапуск
- **Local backup** (только логи и конфиг) 
- **Log rotation** (ежедневно) - сжатие старых логов
- **Disk monitoring** - предупреждения при >85%

## 📊 Производительность

### Ожидаемая нагрузка на 5000 пользователей:
- **Сообщений в день**: ~50,000
- **Concurrent пользователей**: ~200-500
- **External DB connections**: ~20-50 активных
- **API requests**: ~1000/час (обучение аватаров)
- **Local storage growth**: ~100-500 MB/месяц (только логи)

### Ресурсы по компонентам (только приложения):
```
Telegram Bot:    1.5-3 GB RAM, 100-200% CPU
API Server:      0.5-1 GB RAM, 25-50% CPU  
System/Other:    1-2 GB RAM, 25-50% CPU
Total:           3-6 GB RAM, 150-300% CPU
```

## 🔐 Безопасность

### Firewall (UFW):
- **SSH**: 22/tcp (только ваш IP)
- **HTTP/HTTPS**: 80/tcp, 443/tcp
- **API Server**: 8443/tcp (только FAL AI IPs)

### Outbound connections:
- **PostgreSQL Server**: 5432/tcp (ваши DB серверы)
- **Redis Server**: 6379/tcp (ваш Redis сервер)
- **MinIO Server**: 9000/tcp (ваш MinIO сервер)

### SSL/TLS:
- **Domain**: aibots.kz
- **Certificate**: Valid SSL for webhook
- **Ciphers**: Strong encryption only
- **HSTS**: Enabled

### App Security:
- **User isolation**: Dedicated 'aisha' user
- **File permissions**: Restricted access
- **Environment vars**: Secure token storage
- **Process limits**: Memory/CPU quotas

## 📈 Масштабирование

### При росте нагрузки:
1. **Вертикальное** - больше CPU/RAM для app сервера
2. **Горизонтальное** - несколько app серверов + load balancer
3. **External services** - масштабирование PostgreSQL/Redis/MinIO отдельно

### Сигналы для масштабирования:
- CPU > 70% длительно (меньше запас т.к. нет БД)
- RAM > 85% 
- Response time > 2s
- Error rate > 1%
- External connection timeouts

## 🚨 Критичные точки

### Обязательно проверить:
- [ ] **SSL сертификаты** корректны
- [ ] **TELEGRAM_TOKEN** настроен
- [ ] **FAL_API_KEY** настроен  
- [ ] **PostgreSQL connection** работает
- [ ] **Redis connection** работает
- [ ] **MinIO connection** работает
- [ ] **Firewall** настроен (включая outbound)
- [ ] **Health monitoring** активен
- [ ] **Log rotation** настроен

### Частые проблемы:
1. **SSL expired** → Обновить сертификаты
2. **External DB timeout** → Проверить сетевое подключение
3. **Redis connection lost** → Проверить Redis сервер
4. **MinIO access denied** → Проверить credentials
5. **High memory** → Перезапустить app сервисы

## 📞 Команды для мониторинга

```bash
# Статус сервисов
sudo systemctl status aisha-bot aisha-api

# Логи в реальном времени
sudo journalctl -fu aisha-bot
sudo journalctl -fu aisha-api

# Ресурсы системы
htop
iotop
df -h

# Проверка внешних подключений
telnet your-postgres-server 5432
telnet your-redis-server 6379
telnet your-minio-server 9000

# Health checks
curl https://aibots.kz:8443/health
tail -f /var/log/aisha-health.log

# Test external connections
redis-cli -h your-redis-server ping
psql -h your-postgres-server -U aisha -d aisha_bot_prod -c "SELECT 1;"
```

## 💰 Ориентировочная стоимость

### Application Server (месяц):
- **Минимум**: $20-40 (2 cores, 4GB RAM, 50GB SSD)
- **Рекомендуемо**: $40-80 (4 cores, 8GB RAM, 100GB SSD)

### Дополнительные расходы:
- **SSL сертификат**: $50-100/год (или бесплатный Let's Encrypt)
- **Domain**: $10-20/год
- **Backup storage**: $5/месяц (только логи и конфиг)
- **Monitoring**: $0-30/месяц (опционально)

### Внешние сервисы (уже развернуты):
- PostgreSQL Server
- Redis Server  
- MinIO Server

### Итого для App Server: $30-100/месяц

## 🔄 Пример конфигурации

### DATABASE_URL
```env
DATABASE_URL=postgresql+asyncpg://username:password@your-postgres-server:5432/aisha_bot_prod
```

### REDIS_URL
```env
REDIS_URL=redis://your-redis-server:6379/0
```

### MinIO настройки
```env
MINIO_ENDPOINT=your-minio-server:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET=aisha-bot-storage
``` 