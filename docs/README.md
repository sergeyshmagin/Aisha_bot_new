# 🤖 Aisha v2 - AI Telegram Bot

**Версия:** v2.0  
**Статус:** ✅ Готов к продакшн использованию  
**Обновлено:** 15.01.2025

## 📋 Описание проекта

Aisha v2 - это продвинутый Telegram-бот с возможностями создания персонализированных AI аватаров и генерации изображений. Интегрирован с FAL AI для обучения моделей и генерации высококачественных изображений.

### 🎯 Ключевые возможности

- **🎭 Система аватаров** - создание персонализированных AI моделей
- **🎨 Генерация изображений** - создание изображений с обученными аватарами  
- **⚡ FAL AI интеграция** - автоматический выбор оптимальной модели
- **🔄 Асинхронная архитектура** - высокая производительность
- **📊 Мониторинг** - полное логирование и метрики
- **🔐 Безопасность** - валидация контента и защита данных

### 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   API Server    │    │   PostgreSQL    │
│   (Port 8000)   │◄──►│   (Port 8443)   │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
         │     MinIO       │    │     Redis       │    │    FAL AI       │
         │  File Storage   │    │    Cache        │    │   External API  │
         └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Быстрый старт

### Предварительные требования
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- MinIO
- FAL AI API ключ
- Telegram Bot Token

### Установка
```bash
# Клонирование репозитория
git clone https://github.com/your-repo/aisha_v2.git
cd aisha_v2

# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка окружения
cp .env.example .env
# Отредактируйте .env с вашими настройками

# Применение миграций
alembic upgrade head

# Запуск бота
python -m app.main
```

### Быстрая проверка
```bash
# Проверка здоровья системы
curl http://localhost:8000/health

# Проверка API сервера
curl https://localhost:8443/health
```

## 📚 Документация

### 🏗️ Архитектура и разработка
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - архитектура системы и структура кода
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - настройка окружения и лучшие практики

### 🚀 Развертывание
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - полное руководство по развертыванию в продакшн

### 📋 Текущий статус
- **[CURRENT_STATUS.md](CURRENT_STATUS.md)** - текущие задачи и планы развития

### 📖 Руководства
- **[guides/avatar_system.md](guides/avatar_system.md)** - система аватаров
- **[guides/fal_ai_integration.md](guides/fal_ai_integration.md)** - интеграция с FAL AI
- **[guides/image_generation.md](guides/image_generation.md)** - генерация изображений

### 📚 Справочники
- **[reference/troubleshooting.md](reference/troubleshooting.md)** - решение проблем
- **[reference/api_reference.md](reference/api_reference.md)** - API справочник
- **[reference/changelog.md](reference/changelog.md)** - история изменений

## 🎭 Система аватаров

### Типы обучения

#### 🎭 Портретный (Рекомендуемый)
- **Технология:** FLUX LoRA Portrait Trainer
- **Время:** 3-15 минут
- **Оптимизирован для:** Фотографии людей
- **Преимущества:** Быстрое обучение, высокое качество лиц

#### 🎨 Художественный
- **Технология:** FLUX Pro Trainer  
- **Время:** 5-30 минут
- **Оптимизирован для:** Универсальный контент
- **Преимущества:** Поддержка любых стилей и объектов

### Workflow создания
```
Главное меню → Создать аватар → Выбор типа → Загрузка фото → Обучение → Готово
```

## 🎨 Генерация изображений

### FLUX1.1 Ultra возможности
- **Разрешение:** До 2K (2048x2048)
- **Скорость:** 10x быстрее предыдущих версий
- **Качество:** Профессиональный фотореализм
- **Время генерации:** 10-30 секунд

### Планируемая галерея (v2.1)
- 🎭 Популярные стили и шаблоны
- 📱 Удобный пользовательский интерфейс
- 💾 Персональная галерея изображений
- 🔄 Генерация вариаций

## ⚙️ Конфигурация

### Основные переменные окружения
```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# База данных
DATABASE_HOST=localhost
DATABASE_NAME=aisha_v2
DATABASE_USER=aisha_user
DATABASE_PASSWORD=secure_password

# FAL AI
FAL_API_KEY=your_fal_api_key
FAL_WEBHOOK_URL=https://yourdomain.com:8443/api/v1/avatar/status_update

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Режимы
DEBUG=false
FAL_TRAINING_TEST_MODE=false
```

## 🔧 Основные команды

### Разработка
```bash
# Запуск в режиме разработки
python -m app.main

# Запуск тестов
pytest

# Применение миграций
alembic upgrade head

# Создание новой миграции
alembic revision --autogenerate -m "description"
```

### Продакшн
```bash
# Проверка статуса сервисов
sudo systemctl status aisha-bot aisha-api-server postgresql redis minio

# Просмотр логов
sudo journalctl -u aisha-bot -f
tail -f /var/log/aisha_v2/app.log

# Перезапуск сервисов
sudo systemctl restart aisha-bot
sudo systemctl restart aisha-api-server
```

## 📊 Мониторинг

### Health Check Endpoints
- **Основной бот:** `http://localhost:8000/health`
- **API сервер:** `https://localhost:8443/health`
- **Webhook статус:** `https://localhost:8443/api/v1/webhook/status`

### Ключевые метрики
- Время обучения аватаров
- Скорость генерации изображений
- Использование API квот
- Активность пользователей

## 🚨 Решение проблем

### Частые проблемы
1. **Бот не отвечает** → Проверьте токен и статус сервиса
2. **Ошибки FAL AI** → Проверьте API ключ и webhook URL
3. **Проблемы с БД** → Проверьте подключение и миграции

### Диагностика
```bash
# Быстрая проверка системы
systemctl is-active aisha-bot aisha-api-server postgresql redis minio

# Проверка конфигурации
grep -E "(TOKEN|KEY)" .env | wc -l  # Должно быть > 0

# Логи ошибок
journalctl -u aisha-bot --since "1 hour ago" | grep ERROR
```

## 🔄 Обновление

### Обновление кода
```bash
cd /opt/aisha_v2
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart aisha-bot aisha-api-server
```

### Резервное копирование
```bash
# База данных
pg_dump aisha_v2 > backup_$(date +%Y%m%d).sql

# Конфигурация
cp .env backup_env_$(date +%Y%m%d)
```

## 📈 Статистика проекта

### Текущее состояние
- ✅ **Система аватаров** - готова к использованию
- ✅ **FAL AI интеграция** - полностью функциональна
- ✅ **API сервер** - развернут в продакшн
- 🔄 **Галерея изображений** - в разработке (v2.1)

### Технические характеристики
- **Языки:** Python 3.11, SQL
- **Фреймворки:** aiogram, FastAPI, SQLAlchemy
- **База данных:** PostgreSQL 15
- **Кэширование:** Redis 7
- **Хранилище:** MinIO
- **AI сервисы:** FAL AI, OpenAI

## 🤝 Участие в разработке

### Структура проекта
```
aisha_v2/
├── app/                    # Основное приложение
│   ├── handlers/          # Обработчики Telegram
│   ├── services/          # Бизнес-логика
│   ├── database/          # Модели и миграции
│   └── core/              # Конфигурация
├── api_server/            # API сервер для webhook
├── docs/                  # Документация
└── tests/                 # Тесты
```

### Принципы разработки
- **PEP8** - стиль кода
- **Async/await** - асинхронное программирование
- **Type hints** - типизация
- **Pytest** - тестирование
- **Alembic** - миграции БД

## 📞 Поддержка

### Контакты
- **Документация:** `/docs/`
- **Логи:** `/var/log/aisha_v2/`
- **Конфигурация:** `.env`

### Полезные ссылки
- [FAL AI Documentation](https://fal.ai/docs)
- [aiogram Documentation](https://docs.aiogram.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**🎉 Добро пожаловать в Aisha v2! Создавайте удивительные AI аватары и генерируйте потрясающие изображения!** 