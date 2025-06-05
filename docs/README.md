# 🤖 Aisha v2 - AI Telegram Bot

**Версия:** v2.0  
**Статус:** ✅ Готов к продакшн использованию  
**Обновлено:** 04.06.2025

## 📋 Описание проекта

Aisha v2 - это продвинутый Telegram-бот с возможностями создания персонализированных AI аватаров и генерации изображений. Интегрирован с FAL AI для обучения моделей и генерации высококачественных изображений.

### 🎯 Ключевые возможности

- **🎭 Система аватаров** - создание персонализированных AI моделей
- **🎨 Генерация изображений** - создание изображений с обученными аватарами  
- **📸 Фото-промпты** - анализ изображений через GPT-4 Vision
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
python3.11 -m venv .venv
source .venv/bin/activate

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
python scripts/testing/test_app_health.py

# Проверка состояния аватаров
python scripts/testing/check_avatars.py
```

## 📚 Документация

### 🏗️ Архитектура и разработка
- **[architecture.md](architecture.md)** - Архитектура системы
- **[TASK.md](TASK.md)** - Текущие задачи и планы
- **[PLANNING.md](PLANNING.md)** - Долгосрочное планирование
- **[best_practices.md](best_practices.md)** - Лучшие практики разработки

### 🚀 Развертывание
- **[setup/DEPLOYMENT.md](setup/DEPLOYMENT.md)** - Полное руководство по развертыванию
- **[setup/DOCKER_SETUP.md](setup/DOCKER_SETUP.md)** - Настройка Docker

### 🔧 Разработка
- **[development/FIXES.md](development/FIXES.md)** - Общие исправления и решения
- **[development/AVATAR_SYSTEM_FIXES.md](development/AVATAR_SYSTEM_FIXES.md)** - Исправления системы аватаров
- **[development/PERFORMANCE.md](development/PERFORMANCE.md)** - Оптимизация производительности

### ✨ Функциональность
- **[features/PHOTO_PROMPT_FEATURE.md](features/PHOTO_PROMPT_FEATURE.md)** - Генерация промптов по фото
- **[features/PHOTO_ANALYSIS_IMPROVEMENTS.md](features/PHOTO_ANALYSIS_IMPROVEMENTS.md)** - Улучшения анализа фото

### 📚 Справочная информация
- **[reference/fal_knowlege_base/](reference/fal_knowlege_base/)** - База знаний FAL AI
- **[reference/troubleshooting.md](reference/troubleshooting.md)** - Устранение неполадок

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

### Фото-промпты (GPT-4 Vision)
- **📸 Анализ изображений** - автоматическое создание промптов
- **🎬 Кинематографические описания** - профессиональные промпты
- **📐 Выбор соотношений сторон** - 1:1, 3:4, 4:3, 9:16, 16:9
- **⚡ Быстрая генерация** - от анализа до результата за минуты

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

# MinIO
MINIO_ENDPOINT=192.168.0.4:9000
MINIO_BUCKET_AVATARS=avatars
MINIO_BUCKET_NAME=aisha

# Режимы
DEBUG=false
FAL_TRAINING_TEST_MODE=false
```

## 🔧 Основные команды

### Разработка
```bash
# Запуск в режиме разработки
source .venv/bin/activate
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

### Скрипты проверки
```bash
# Проверка здоровья всех компонентов
python scripts/testing/test_app_health.py

# Проверка состояния аватаров
python scripts/testing/check_avatars.py

# Проверка завершенных аватаров
python scripts/testing/check_completed_avatars.py

# Проверка базы данных
python scripts/maintenance/check_db_status.py
```

### Ключевые метрики
- **Время отклика UI:** 257-404ms
- **Готовые аватары:** SERGEY-PORTRAIT-1000 (PORTRAIT) ✅
- **MinIO файлы:** 814 объектов в bucket `avatars`
- **Статус обучения:** Полный pipeline работает ✅

## 🔄 Последние обновления (04.06.2025)

### ✅ Исправления системы аватаров:
- **Кнопка генерации** - исправлена ошибка "Аватар не найден"
- **FAL AI клиент** - исправлен вызов методов
- **MinIO bucket** - переключение на правильный bucket `avatars`
- **Загрузка архивов** - исправлена передача файлов в FAL AI
- **UX улучшения** - кнопка "Продолжить" для draft аватаров

### ✅ Готовность к продакшену:
- **Обучение аватаров** - полный pipeline работает без ошибок
- **Генерация изображений** - функциональна с готовыми аватарами
- **Фото-промпты** - полный цикл от анализа до генерации
- **Телеграм бот** - стабилен и готов к использованию

**Система полностью готова к продакшену!** 🚀

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
aisha-backend/
├── app/                    # Основное приложение
│   ├── handlers/          # Обработчики Telegram
│   ├── services/          # Бизнес-логика
│   ├── database/          # Модели и миграции
│   └── core/              # Конфигурация и DI
├── docs/                  # Документация
├── scripts/               # Утилиты и скрипты
├── tests/                 # Тесты
└── archive/               # Архивные файлы
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