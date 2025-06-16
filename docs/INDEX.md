# 📚 Индекс документации AISHA Backend

## 🚀 Быстрый старт

- **[README.md](README.md)** - Основная информация о проекте
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Инструкции по развертыванию
- **[architecture.md](architecture.md)** - Архитектура системы
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Решение проблем

## 📋 Основная документация

### 🏗️ Архитектура и дизайн
- **[architecture.md](architecture.md)** - Общая архитектура системы
- **[best_practices.md](best_practices.md)** - Лучшие практики разработки
- **[FEATURES.md](FEATURES.md)** - Описание всех функций системы

### 🚀 Развертывание и эксплуатация
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Полное руководство по развертыванию
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Устранение неисправностей

### 📊 Управление проектом
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Текущий статус разработки
- **[CHANGELOG.md](CHANGELOG.md)** - История изменений
- **[PROJECT_CLEANUP_ANALYSIS.md](PROJECT_CLEANUP_ANALYSIS.md)** - Анализ очистки проекта

## 🔧 Разработка

### 📝 Планирование
- **[PROJECT_CLEANUP_ANALYSIS.md](PROJECT_CLEANUP_ANALYSIS.md)** - План рефакторинга
- **[DOCUMENTATION_CLEANUP.md](DOCUMENTATION_CLEANUP.md)** - План консолидации документации

## 📁 Структура каталогов

### setup/
Инструкции по первоначальной настройке системы.

### development/
Документация для разработчиков, включая стандарты кодирования и рабочие процессы.

### reference/
Справочные материалы и технические спецификации.

### features/
Детальное описание функций и возможностей системы.

### fixes/
История исправлений ошибок и улучшений.

## 🎯 Функции системы (краткий обзор)

### 🤖 Telegram Bot
- Многоязычный интерфейс
- Персонализированные меню
- Балансная система

### 🎨 AI Генерация
- **Imagen4**: Высококачественная генерация изображений
- **Аватары**: Персонализированные модели пользователей

### 📸 Галерея
- Фильтрация по типу, дате, избранному
- Навигация с сохранением состояния
- Redis-кэширование для производительности

### 🗄️ Хранение данных
- **PostgreSQL**: Структурированные данные
- **Redis**: Кэширование и состояния
- **MinIO**: Объектное хранилище файлов

## 🛠️ Технические детали

### Стек технологий
- **Backend**: Python 3.12, aiogram, FastAPI, SQLAlchemy
- **AI/ML**: FAL AI (Imagen4, Avatar generation)
- **Infrastructure**: PostgreSQL, Redis, MinIO, Docker

### Развертывание
- Docker containerization
- Registry на 192.168.0.4
- Продакшн на 192.168.0.10
- Redis на 192.168.0.3
- MinIO и PostgreSQL на 192.168.0.4

## 🚀 Быстрые команды

```bash
# Запуск бота
python -m app.main

# Проверка состояния MinIO
python scripts/debug/check_imagen4_config.py

# Очистка тестовых данных
python scripts/debug/cleanup_test_imagen4.py

# Управление балансом пользователей
python scripts/admin/add_balance.py --list
python scripts/admin/add_balance.py --interactive

# Миграции БД
alembic upgrade head
```

## 📖 Как использовать эту документацию

1. **Новые разработчики**: Начните с [README.md](README.md) и [architecture.md](architecture.md)
2. **Администраторы**: Обратитесь к [DEPLOYMENT.md](DEPLOYMENT.md) и [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. **Продуктовая команда**: Изучите [FEATURES.md](FEATURES.md)
4. **При проблемах**: Используйте [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 🔍 Поиск информации

- **Функции системы**: [FEATURES.md](FEATURES.md)
- **История изменений**: [CHANGELOG.md](CHANGELOG.md) 
- **Проблемы и решения**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Текущий статус**: [PROJECT_STATUS.md](PROJECT_STATUS.md)
- **Лучшие практики**: [best_practices.md](best_practices.md)

## 🆘 Поддержка

### Частые проблемы
1. **Пустая галерея Imagen4** → См. [TROUBLESHOOTING.md](TROUBLESHOOTING.md#пустая-галерея-imagen4)
2. **Фильтры сбрасываются** → Проверьте Redis подключение
3. **Тестовые URL** → Используйте cleanup скрипты

### Получение помощи
1. Проверьте логи: `tail -f logs/app.log`
2. Запустите диагностику: см. [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Изучите соответствующую документацию

---

*Документация очищена и обновлена: 2025-01-24* 