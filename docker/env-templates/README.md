# Environment Configuration для Docker

Эта папка содержит шаблоны для настройки переменных окружения в Docker контейнерах.

## 📁 Структура файлов

- `dev.env.template` - шаблон для development окружения (с реальными API ключами)
- `prod.env.template` - шаблон для production окружения

## 🚀 Быстрая настройка

### 1. Скопируйте шаблоны в корень проекта:

```bash
# Для development
cp docker/env-templates/dev.env.template .env.docker.dev

# Для production  
cp docker/env-templates/prod.env.template .env.docker.prod
```

### 2. Обновите необходимые значения:

#### В .env.docker.prod обновите:

```bash
# Security keys для production (ОБЯЗАТЕЛЬНО!)
JWT_SECRET_KEY=your_production_jwt_secret_key_here
PASSWORD_SALT=your_production_salt_here
TELEGRAM_WEBHOOK_SECRET=your_production_webhook_secret_here
FAL_WEBHOOK_SECRET=your_production_fal_webhook_secret_here

# SSL сертификаты
SSL_CERT_PATH=/etc/nginx/ssl/aibots_kz.crt
SSL_KEY_PATH=/etc/nginx/ssl/aibots.kz.key
```

**Важно**: Dev шаблон уже содержит рабочие API ключи для разработки!

## 🗄️ Внешние сервисы

В текущих шаблонах уже настроено подключение к существующим сервисам:

- **PostgreSQL**: `192.168.0.4:5432` (база: `aisha`, пользователь: `aisha_user`)
- **Redis**: `192.168.0.3:6379` (с паролем `wd7QuwAbG0wtyoOOw3Sm`)
- **MinIO**: `192.168.0.4:9000` (access: `minioadmin`)

## ⚡ Запуск после настройки

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d

# Проверка здоровья внешних сервисов
./scripts/health-check.sh
```

## 🔧 Настройки API и режимы работы

### Development:
- `API_DEBUG=true` - включена отладка
- `API_RELOAD=true` - автоперезагрузка
- `FAL_TRAINING_TEST_MODE=true` - тестовый режим обучения
- `AVATAR_TEST_MODE=true` - тестовый режим аватаров
- `LOG_LEVEL=DEBUG` - детальные логи

### Production:
- `API_DEBUG=false` - отладка отключена
- `SSL_ENABLED=true` - включен SSL
- `FAL_TRAINING_TEST_MODE=false` - продакшн режим
- `LOG_LEVEL=INFO` - оптимальные логи

## 📊 Настройки производительности

### Development vs Production:

| Параметр | Development | Production |
|----------|-------------|------------|
| DB Pool Size | 5 | 10 |
| DB Max Overflow | 10 | 20 |
| Redis Pool Size | 10 | 20 |
| Redis Pool Timeout | 5s | 10s |
| Session Timeout | 3600s | 7200s |
| API Rate Limit | 60/min | 120/min |
| Log Level | DEBUG | INFO |

## 🤖 API ключи и интеграции

Шаблоны уже содержат рабочие ключи:

- **OpenAI API**: Готов к использованию
- **FAL AI**: Настроен для создания аватаров  
- **Assistant ID**: Подключен к OpenAI ассистенту
- **Telegram Bot**: Готов к работе

## 🔒 Безопасность

- ❌ НЕ коммитьте .env файлы с production секретами
- ✅ Обновите JWT_SECRET_KEY для production
- ✅ Установите strong TELEGRAM_WEBHOOK_SECRET
- ✅ Настройте SSL сертификаты

## 🐛 Troubleshooting

### Проблемы с подключением к внешним сервисам:

```bash
# Проверьте доступность сервисов
./scripts/health-check.sh

# Проверьте логи контейнеров
docker-compose logs -f aisha-bot
docker-compose logs -f aisha-api
```

### Проблемы с Redis аутентификацией:

Убедитесь, что в Redis URL присутствует пароль:
```
redis://:wd7QuwAbG0wtyoOOw3Sm@192.168.0.3:6379/0
```

### Сброс настроек:

```bash
# Удалить и пересоздать .env файлы
rm .env.docker.dev .env.docker.prod
cp docker/env-templates/dev.env.template .env.docker.dev
cp docker/env-templates/prod.env.template .env.docker.prod
```

## 🚢 Быстрый старт

```bash
# 1. Скопировать шаблоны
cp docker/env-templates/dev.env.template .env.docker.dev

# 2. Проверить внешние сервисы  
./scripts/health-check.sh

# 3. Запустить development
docker-compose up -d

# 4. Проверить логи
docker-compose logs -f
``` 