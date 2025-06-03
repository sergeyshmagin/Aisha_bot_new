# Руководство по развертыванию Aisha v2

**Версия:** v2.0  
**Дата:** 23.05.2025  
**Статус:** FAL AI интеграция готова к продакшену

## 📋 Обзор архитектуры

### Компоненты системы
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   Backend API   │    │   FAL AI API    │
│   (aiogram 3.x) │◄──►│   (FastAPI)     │◄──►│   (External)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     MinIO       │    │   Webhook       │
│   (Database)    │    │   (Storage)     │    │   Endpoint      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Технологический стек
- **Bot Framework:** aiogram 3.x (async)
- **Database:** PostgreSQL + SQLAlchemy async
- **File Storage:** MinIO S3-compatible
- **AI Services:** OpenAI API, FAL AI
- **Runtime:** Python 3.11+
- **Orchestration:** Docker + Docker Compose

## 🛠️ Предварительные требования

### Системные требования
- **OS:** Linux (Ubuntu 22.04+ рекомендуется)
- **RAM:** Минимум 4GB, рекомендуется 8GB
- **Storage:** Минимум 50GB свободного места
- **Network:** Публичный IP для webhook
- **Docker:** 24.0+ с Docker Compose v2

### Внешние сервисы
1. **Telegram Bot Token** - от @BotFather
2. **OpenAI API Key** - для транскрибации и обработки текста
3. **FAL AI API Key** - для обучения аватаров
4. **Domain + SSL** - для webhook endpoint

## 🔧 Переменные окружения

### Создание .env файла
```bash
# Скопируйте пример и отредактируйте
cp .env.example .env
```

### Обязательные переменные

#### Telegram Configuration
```bash
TELEGRAM_BOT_TOKEN=1234567890:AAABBBCCCDDDEEEFFFGGGHHHIIIJJJKKK
BOT_USERNAME=your_bot_username
```

#### Database Configuration
```bash
DATABASE_URL=postgresql+asyncpg://aisha_user:strong_password@localhost:5432/aisha_v2
POSTGRES_USER=aisha_user
POSTGRES_PASSWORD=strong_password
POSTGRES_DB=aisha_v2
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

#### MinIO Configuration
```bash
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin_password
MINIO_SECURE=false
MINIO_BUCKET_AVATARS=aisha-v2-avatars
MINIO_BUCKET_TRANSCRIPTS=aisha-v2-transcripts
```

#### OpenAI Configuration
```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-3.5-turbo
```

#### FAL AI Configuration ⭐
```bash
# API ключ (обязательно)
FAL_API_KEY=your_fal_api_key_here

# Режим работы (критично!)
FAL_TRAINING_TEST_MODE=false  # true для разработки, false для продакшена

# Webhook URL (обязательно для продакшена)
FAL_WEBHOOK_URL=https://yourdomain.com/webhook/fal/status

# Настройки обучения
FAL_DEFAULT_MODE=character
FAL_DEFAULT_ITERATIONS=500
FAL_DEFAULT_PRIORITY=quality
FAL_TRIGGER_WORD=TOK
FAL_LORA_RANK=32
FAL_FINETUNE_TYPE=full
```

#### Production Settings
```bash
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# SSL и безопасность
SSL_CERT_PATH=/etc/ssl/certs/your_domain.pem
SSL_KEY_PATH=/etc/ssl/private/your_domain.key
```

## 🚀 Пошаговое развертывание

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose v2
sudo apt install docker-compose-plugin -y

# Перезагрузка для применения изменений группы
sudo reboot
```

### 2. Загрузка проекта

```bash
# Клонирование репозитория
git clone https://github.com/your-org/aisha-bot-v2.git
cd aisha-bot-v2

# Создание структуры каталогов
mkdir -p data/postgresql data/minio logs storage
sudo chown -R 1001:1001 data/
```

### 3. Конфигурация

```bash
# Создание файла переменных окружения
cp .env.example .env
nano .env  # Настройте все переменные согласно разделу выше

# Проверка конфигурации
./scripts/validate_config.sh
```

### 4. Настройка базы данных

```bash
# Запуск PostgreSQL
docker compose up -d postgresql

# Ожидание готовности БД
sleep 30

# Выполнение миграций
docker compose run --rm aisha-bot alembic upgrade head

# Проверка подключения
docker compose exec postgresql psql -U aisha_user -d aisha_v2 -c "SELECT version();"
```

### 5. Настройка MinIO

```bash
# Запуск MinIO
docker compose up -d minio

# Создание buckets
docker compose run --rm aisha-bot python scripts/setup_minio.py

# Проверка buckets
docker compose exec minio mc ls minio/
```

### 6. Настройка SSL и домена

```bash
# Установка Certbot для Let's Encrypt
sudo apt install certbot -y

# Получение SSL сертификата
sudo certbot certonly --standalone -d yourdomain.com

# Настройка автообновления
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### 7. Запуск приложения

```bash
# Запуск всех сервисов
docker compose up -d

# Проверка статуса
docker compose ps

# Проверка логов
docker compose logs -f aisha-bot
```

### 8. Настройка webhook

```bash
# Настройка Telegram webhook
curl -F "url=https://yourdomain.com/webhook/telegram" \
     https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook

# Проверка webhook
curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo
```

## 🔒 Безопасность

### Настройка файрвола
```bash
# Базовые правила
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Секреты и ключи
```bash
# Создание секретов Docker
echo "your_fal_api_key" | docker secret create fal_api_key -
echo "your_openai_key" | docker secret create openai_api_key -

# Обновление docker-compose для использования секретов
# (см. docker-compose.prod.yml)
```

### Мониторинг безопасности
- Регулярное обновление Docker images
- Мониторинг логов на подозрительную активность
- Ротация API ключей каждые 3 месяца

## 📊 Мониторинг и логирование

### Структурированные логи
```bash
# Просмотр логов в реальном времени
docker compose logs -f aisha-bot

# Логи по сервисам
docker compose logs postgresql
docker compose logs minio
docker compose logs nginx
```

### Мониторинг здоровья
```bash
# Health checks endpoint
curl https://yourdomain.com/health

# Мониторинг ресурсов
docker stats

# Мониторинг дискового пространства
df -h
du -sh data/
```

### Алерты и уведомления
```bash
# Настройка мониторинга через cron
cat > /etc/cron.d/aisha-monitoring << 'EOF'
*/5 * * * * root /opt/aisha/scripts/health_check.sh
0 */4 * * * root /opt/aisha/scripts/cleanup_logs.sh
EOF
```

## 🧪 Тестирование после развертывания

### 1. Базовые проверки
```bash
# Проверка API здоровья
curl https://yourdomain.com/health

# Тест подключения к базе данных
docker compose exec aisha-bot python scripts/test_db.py

# Тест MinIO подключения
docker compose exec aisha-bot python scripts/test_minio.py
```

### 2. Функциональное тестирование

#### Тест транскрибации
1. Отправьте аудиофайл боту
2. Проверьте корректность транскрибации
3. Убедитесь в сохранении в MinIO

#### Тест создания аватара
1. Создайте новый аватар через бота
2. Загрузите 10-20 фотографий
3. Запустите обучение
4. Проверьте webhook уведомления

### 3. FAL AI интеграция
```bash
# Тест FAL AI в продакшен режиме
docker compose exec aisha-bot python scripts/test_fal_production.py

# Проверка webhook endpoint
curl -X POST https://yourdomain.com/webhook/fal/status \
     -H "Content-Type: application/json" \
     -d '{"finetune_id":"test","status":"completed","progress":100}'
```

## 🔄 Обслуживание и резервные копии

### Резервное копирование

#### Ежедневные резервные копии БД
```bash
cat > /etc/cron.d/aisha-backup << 'EOF'
0 2 * * * root /opt/aisha/scripts/backup_database.sh
0 3 * * * root /opt/aisha/scripts/backup_minio.sh
EOF
```

#### Скрипт резервного копирования
```bash
#!/bin/bash
# backup_database.sh
DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec -T postgresql pg_dump -U aisha_user aisha_v2 | \
    gzip > /opt/backups/aisha_db_$DATE.sql.gz
find /opt/backups -name "aisha_db_*.sql.gz" -mtime +7 -delete
```

### Обновления системы
```bash
# Обновление образов Docker
docker compose pull
docker compose up -d --force-recreate

# Применение миграций БД
docker compose run --rm aisha-bot alembic upgrade head

# Перезапуск с новой конфигурацией
docker compose restart
```

## ⚡ Оптимизация производительности

### Настройка PostgreSQL
```sql
-- В postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
```

### Настройка MinIO
```bash
# Увеличение пулов соединений
export MINIO_API_REQUESTS_MAX=10000
export MINIO_API_REQUESTS_DEADLINE=10s
```

### Кэширование
- Redis для кэширования частых запросов
- CDN для статических файлов
- Connection pooling для БД

## 🚨 Устранение неполадок

### Общие проблемы

#### FAL AI webhook не работает
```bash
# Проверка настроек webhook
curl -H "Authorization: Key YOUR_FAL_API_KEY" \
     https://fal.run/webhooks

# Проверка доступности endpoint
curl -I https://yourdomain.com/webhook/fal/status

# Логи webhook обработки
docker compose logs -f aisha-bot | grep "FAL WEBHOOK"
```

#### Telegram webhook недоступен
```bash
# Проверка статуса
curl https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo

# Удаление и повторная установка webhook
curl https://api.telegram.org/bot$BOT_TOKEN/deleteWebhook
curl -F "url=https://yourdomain.com/webhook/telegram" \
     https://api.telegram.org/bot$BOT_TOKEN/setWebhook
```

#### Проблемы с MinIO
```bash
# Проверка доступности buckets
docker compose exec minio mc ls minio/

# Создание отсутствующих buckets
docker compose exec minio mc mb minio/aisha-v2-avatars
docker compose exec minio mc mb minio/aisha-v2-transcripts
```

### Диагностические команды
```bash
# Проверка всех сервисов
docker compose ps

# Проверка использования ресурсов
docker stats --no-stream

# Проверка логов ошибок
docker compose logs | grep -i error

# Проверка сетевых подключений
docker compose exec aisha-bot netstat -tlnp
```

## 📈 Масштабирование

### Горизонтальное масштабирование
- Запуск нескольких экземпляров бота
- Load balancer для распределения нагрузки
- Разделение обработки по типам запросов

### Вертикальное масштабирование
- Увеличение ресурсов контейнеров
- Оптимизация пулов соединений
- Настройка memory limits

---

## ✅ Чек-лист развертывания

### Перед запуском
- [ ] Все переменные окружения настроены
- [ ] SSL сертификаты получены
- [ ] Домен корректно настроен
- [ ] FAL_TRAINING_TEST_MODE=false для продакшена
- [ ] Резервные копии настроены

### После запуска
- [ ] Все сервисы запущены (docker compose ps)
- [ ] Telegram webhook настроен
- [ ] FAL AI webhook endpoint доступен
- [ ] Базовые тесты пройдены
- [ ] Мониторинг работает
- [ ] Логи пишутся корректно

### Финальная проверка
- [ ] Создание аватара работает end-to-end
- [ ] Транскрибация аудио работает
- [ ] Webhook от FAL AI обрабатываются
- [ ] Уведомления пользователям приходят
- [ ] Производительность в норме

**🚀 Поздравляем! Aisha v2 с FAL AI интеграцией успешно развернута!** 