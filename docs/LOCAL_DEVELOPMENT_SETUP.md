# 🏠 Настройка локальной разработки

**Дата создания:** 26.05.2025  
**Статус:** API развернут на aibots.kz (192.168.0.10)  
**Цель:** Продолжение разработки с локальным ботом и удаленным API

## 🎯 Архитектура разработки

```
┌─────────────────────────────────────────┐
│        Локальная разработка             │
│         Windows/WSL + Python            │
├─────────────────────────────────────────┤
│  🤖 Telegram Bot (localhost)           │ ← Локальная разработка
│     ├── Polling mode                    │   Port: -
│     ├── SQLAlchemy async               │   Env: development
│     └── FAL AI integration             │   Path: /c/dev/Aisha_bot_new/
├─────────────────────────────────────────┤
│  📡 External API (aibots.kz:8443)      │ ← Webhook endpoint
│     ├── FAL AI webhooks                │   SSL: ✅ Configured
│     └── Status callbacks               │   Health: ✅ Working
└─────────────────────────────────────────┘
              ↓ Network ↓
┌─────────────────────────────────────────┐
│           Remote Services               │
├─────────────────────────────────────────┤
│  🗄️ PostgreSQL (удаленный)             │ ← Production DB
│  🔴 Redis (удаленный)                  │ ← Production Cache  
│  📦 MinIO (удаленный)                  │ ← Production Storage
│  📡 API Server (aibots.kz:8443)        │ ← Production Webhook
└─────────────────────────────────────────┘
```

## ⚙️ Конфигурация разработки

### 1. Переменные окружения (.env)

```env
# Режим разработки
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Telegram Bot (локальный, polling mode)
TELEGRAM_TOKEN=your_test_bot_token
TELEGRAM_WEBHOOK_URL=  # Пустое = polling mode
TELEGRAM_ADMIN_IDS=your_telegram_id

# PostgreSQL (удаленный production)
DATABASE_URL=postgresql+asyncpg://user:password@remote_host:5432/aisha_bot_prod

# Redis (удаленный production) 
REDIS_HOST=remote_redis_host
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# MinIO (удаленный production)
MINIO_ENDPOINT=remote_minio_host:9000
MINIO_ACCESS_KEY=your_minio_key
MINIO_SECRET_KEY=your_minio_secret
MINIO_SECURE=true

# FAL AI (удаленный webhook)
FAL_API_KEY=your_fal_api_key
FAL_WEBHOOK_URL=https://aibots.kz:8443/api/v1/avatar/status_update
FAL_WEBHOOK_SECRET=your_webhook_secret

# Разработка
AVATAR_TEST_MODE=true
OPENAI_API_KEY=your_openai_key
```

### 2. Запуск локального бота

```bash
# Активация виртуального окружения
cd /c/dev/Aisha_bot_new
source .venv/bin/activate  # или .venv\Scripts\activate на Windows

# Установка зависимостей
pip install -r requirements.txt

# Запуск бота в режиме polling
python -m app.main
```

### 3. Тестирование FAL AI интеграции

```bash
# Тест подключения к удаленному API
curl https://aibots.kz:8443/health

# Тест webhook endpoint
curl -X POST https://aibots.kz:8443/api/v1/avatar/status_update \
  -H "Content-Type: application/json" \
  -d '{"test": "development"}'
```

## 🧪 Тестирование

### Запуск тестов
```bash
# Unit тесты
pytest tests/unit/ -v

# Интеграционные тесты (с удаленными сервисами)
pytest tests/integration/ -v --slow

# Тесты FAL AI (с реальным API)
pytest tests/integration/test_fal_ai.py -v -k "not real_api" 

# Полное покрытие
pytest --cov=app --cov-report=html
```

### Тестовые данные
```python
# Создание тестового аватара
async def create_test_avatar():
    avatar = await avatar_service.create_avatar(
        user_id=TEST_USER_ID,
        name="Test Avatar",
        training_type=AvatarTrainingType.PORTRAIT
    )
    return avatar
```

## 🔄 Workflow разработки

### Этапы разработки
1. **Локальная разработка** - изменения в коде
2. **Локальное тестирование** - unit + integration тесты
3. **Commit & Push** - сохранение изменений
4. **Деплой на сервер** - обновление production

### Git workflow
```bash
# Создание feature branch
git checkout -b feature/avatar-ui-improvements

# Разработка и тестирование
# ... code changes ...
pytest tests/ -v

# Commit и push
git add .
git commit -m "feat: улучшения UI выбора типа обучения аватара"
git push origin feature/avatar-ui-improvements

# Merge в main после ревью
git checkout main
git merge feature/avatar-ui-improvements
```

### Синхронизация с сервером
```bash
# Скрипт для деплоя изменений
./scripts/deploy_to_production.sh

# Или ручной способ
rsync -av --exclude='.git' --exclude='__pycache__' \
  ./ user@aibots.kz:/opt/aisha-backend/
```

## 📋 Текущие задачи разработки

### Приоритет: HIGH (на этой неделе)

#### 1. Завершение FAL AI UI интеграции
- 🔄 **Training type selection UI**
  - Файл: `app/handlers/avatar/training_type_selection.py`
  - Использовать поле `training_type` из модели Avatar
  - Интегрировать клавиатуры из `keyboards/avatar.py`

- 🔄 **Обновление AvatarTrainingService**
  - Файл: `app/services/avatar/fal_training_service.py`
  - Использовать все 18 FAL AI полей
  - Интеграция с webhook `https://aibots.kz:8443/api/v1/avatar/status_update`

#### 2. Тестирование интеграции
- 🔄 **Интеграционные тесты FAL AI**
  - Файл: `tests/integration/test_fal_ai_integration.py`
  - Тесты с реальным webhook endpoint
  - Проверка сохранения данных в production БД

### Приоритет: MEDIUM (следующая неделя)

#### 3. Улучшения UX
- 📊 **Мониторинг прогресса обучения**
- 🔍 **Расширенное логирование**
- 📱 **Оптимизация мобильного интерфейса**

## 🔧 Полезные команды

### Проверка состояния services
```bash
# Локальный бот
ps aux | grep python | grep run.py

# Удаленный API 
curl https://aibots.kz:8443/health
curl https://aibots.kz:8443/api/v1/webhook/status
```

### Логи разработки
```bash
# Локальные логи
tail -f logs/aisha_bot.log

# Удаленные логи API
ssh user@aibots.kz "tail -f /opt/aisha-backend/api_server/logs/webhook.log"
```

### База данных
```bash
# Подключение к production DB для отладки
psql $DATABASE_URL -c "SELECT id, name, status, training_type FROM avatars ORDER BY created_at DESC LIMIT 5;"

# Миграции (если нужны)
alembic upgrade head
alembic current
```

## 🚨 Важные замечания

### Безопасность
- ⚠️ **Не используйте production токены для тестов**
- ⚠️ **Всегда тестируйте в AVATAR_TEST_MODE=true**
- ⚠️ **Не пушьте .env файлы в git**

### Производительность
- 💡 **Используйте async/await везде**
- 💡 **Кэшируйте тяжелые запросы в Redis**
- 💡 **Оптимизируйте DB запросы с joinedload**

### Отладка
- 🔍 **Включите DEBUG=true для детального логирования**
- 🔍 **Используйте `pytest --pdb` для интерактивной отладки**
- 🔍 **Проверяйте webhook на aibots.kz при проблемах с FAL AI**

## 📚 Следующие шаги

1. **Настроить локальное окружение** по этому гайду
2. **Завершить FAL AI UI интеграцию** (handlers + services)
3. **Протестировать с production данными** 
4. **Подготовить к финальному релизу**

---

**Контакты для поддержки:**
- API Endpoint: https://aibots.kz:8443
- Health Check: https://aibots.kz:8443/health
- Webhook Status: https://aibots.kz:8443/api/v1/webhook/status 