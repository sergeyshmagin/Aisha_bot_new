# 📚 Индекс документации Aisha Bot v2

## 🚀 Быстрый доступ

### 📖 Основные документы
- **[README.md](README.md)** - Главная документация проекта
- **[architecture.md](architecture.md)** - Техническая архитектура системы
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Руководство по развертыванию
- **[best_practices.md](best_practices.md)** - Стандарты разработки

### 🔧 Настройка и развертывание
- **[setup/DOCKER_SETUP.md](setup/DOCKER_SETUP.md)** - Настройка Docker окружения
- **[setup/DEPLOYMENT.md](setup/DEPLOYMENT.md)** - Детальное руководство по развертыванию
- **[WEBHOOK_DEPLOYMENT.md](WEBHOOK_DEPLOYMENT.md)** - Развертывание webhook сервера

### 🛠️ Разработка
- **[development/PERFORMANCE.md](development/PERFORMANCE.md)** - Оптимизация производительности
- **[development/AVATAR_SYSTEM_FIXES.md](development/AVATAR_SYSTEM_FIXES.md)** - Исправления системы аватаров
- **[development/FIXES.md](development/FIXES.md)** - Общие исправления

### 📊 Справочная информация
- **[reference/troubleshooting.md](reference/troubleshooting.md)** - Решение проблем
- **[reference/fal_knowlege_base/](reference/fal_knowlege_base/)** - База знаний FAL AI
- **[reference/async_and_safety.md](reference/async_and_safety.md)** - Асинхронность и безопасность

### 📋 Последние обновления
- **[EYE_QUALITY_IMPROVEMENTS.md](EYE_QUALITY_IMPROVEMENTS.md)** - Улучшения качества глаз
- **[USER_FRIENDLY_MESSAGES.md](USER_FRIENDLY_MESSAGES.md)** - Дружелюбные сообщения
- **[BUTTON_HANDLERS_FIX.md](BUTTON_HANDLERS_FIX.md)** - Исправления обработчиков кнопок
- **[WELCOME_MESSAGE_UPDATE.md](WELCOME_MESSAGE_UPDATE.md)** - Обновление приветственного сообщения

### 🏗️ Архитектурная документация
- **[DOCKER_ARCHITECTURE.md](DOCKER_ARCHITECTURE.md)** - Docker архитектура
- **[DEPLOYMENT_SUCCESS.md](DEPLOYMENT_SUCCESS.md)** - Успешное развертывание

## 🎯 По функциональности

### 🎭 AI-Аватары
- Создание персональных моделей через FAL AI
- Портретные и художественные стили
- Автоматическое обучение на фотографиях
- Галерея аватаров с управлением

### 🖼️ Генерация изображений
- Создание фото с аватаром по описанию
- Кинематографические промпты с автоулучшением
- Анализ изображений через GPT-4 Vision
- Специальные улучшения качества глаз

### 🔊 Транскрибация аудио
- OpenAI Whisper для преобразования речи в текст
- Smart chunking для длинных аудиофайлов
- Персональная галерея результатов

### 💰 Система балансов
- Кредитная система для оплаты AI-услуг
- Гибкие тарифы для разных операций
- История транзакций и управление

## 🛠️ Технические детали

### Стек технологий
- **Backend**: Python 3.12, aiogram 3.4.1, FastAPI, SQLAlchemy 2.0
- **AI/ML**: FAL AI, OpenAI GPT-4 Vision, OpenAI Whisper
- **Infrastructure**: PostgreSQL, Redis, MinIO, Docker

### Архитектура
- Микросервисная архитектура
- Асинхронная обработка
- Webhook интеграции
- Файловое хранилище S3-совместимое

## 🚀 Быстрые команды

```bash
# Запуск DEV бота
./scripts/run_dev_bot.sh

# Проверка здоровья системы
python scripts/testing/test_app_health.py

# Проверка аватаров
python scripts/testing/check_avatars.py

# Миграции БД
alembic upgrade head

# Docker команды
docker-compose -f docker-compose.bot.dev.yml up -d --build
docker-compose -f docker-compose.bot.dev.yml logs -f aisha-bot-dev
```

## 📊 Мониторинг

### Health Checks
- ✅ Telegram API подключение
- ✅ PostgreSQL доступность  
- ✅ Redis состояние
- ✅ MinIO подключение
- ✅ FAL AI валидность ключа

### Полезные скрипты
- `scripts/testing/test_app_health.py` - Проверка системы
- `scripts/testing/check_avatars.py` - Статус аватаров
- `scripts/testing/start_ready_training.py` - Запуск обучения
- `scripts/run_dev_bot.sh` - Запуск DEV бота

## 🆘 Поддержка

### Частые проблемы
1. **Конфликт токенов** → Используйте `./scripts/run_dev_bot.sh`
2. **Ошибки обучения** → Проверьте FAL_API_KEY и webhook URL
3. **Проблемы с БД** → Убедитесь в доступности PostgreSQL

### Получение помощи
1. Проверьте логи: `docker-compose logs -f`
2. Запустите health check: `python scripts/testing/test_app_health.py`
3. Изучите соответствующую документацию

---

**Индекс актуализирован:** Июнь 2025 | **Версия:** 2.0 