# 🛠️ Workflow разработки Aisha Bot

**Цель:** Организация правильного процесса разработки для стабильного деплоя в продакшн

## 🎯 Принципы разработки

### ✅ Что мы имеем сейчас (PRODUCTION READY)
- 🚀 **Рабочий продакшн кластер** на `aisha@192.168.0.10`
- 🔧 **Исправленные критические ошибки** (токены, Dockerfile, entrypoint)
- 📊 **Мониторинг** через `./scripts/monitoring/monitor-production.sh`
- 🚀 **Деплой скрипт** `./scripts/production/deploy-production-final.sh`

### ⚠️ Текущие проблемы
1. **Standby бот конфликтует** с основным (делает polling одновременно)
2. **Неясно работает ли транскрибация** после исправлений
3. **Нет dev/staging окружения** для тестирования изменений

## 🏗️ Правильная архитектура разработки

### 📊 Среды разработки

```
🏠 LOCAL DEVELOPMENT
├── Полная локальная среда
├── Тестирование новых функций  
├── Unit/Integration тесты
└── Быстрая итерация

🧪 STAGING (PLANNING)
├── Копия продакшн окружения
├── Тестирование деплоя
├── E2E тестирование
└── Проверка миграций

🚀 PRODUCTION (CURRENT)
├── Стабильная версия ✅
├── Мониторинг ✅
├── Резервное копирование
└── Zero-downtime updates
```

### 🔄 Git Workflow

```bash
# Ветки
main              # Стабильная продакшн версия
develop           # Развитие функций
feature/*         # Новые функции
hotfix/*          # Критические исправления
release/*         # Подготовка релизов
```

## 🚀 Процесс деплоя

### 1. 🧪 Разработка функций

```bash
# 1. Создание feature ветки
git checkout develop
git pull origin develop
git checkout -b feature/fix-transcription

# 2. Разработка и тестирование локально
python -m pytest tests/
python main.py  # Локальный запуск

# 3. Коммит изменений
git add .
git commit -m "🎤 Исправление транскрибации аудио"
git push origin feature/fix-transcription
```

### 2. 🔄 Code Review и слияние

```bash
# Создание Pull Request в develop
# После review - слияние в develop

git checkout develop  
git pull origin develop
git merge feature/fix-transcription
```

### 3. 🚀 Деплой в продакшн

```bash
# 1. Слияние в main
git checkout main
git merge develop
git tag v2.1.0
git push origin main --tags

# 2. Деплой на продакшн
export TELEGRAM_BOT_TOKEN=your_token
./scripts/production/deploy-production-final.sh

# 3. Проверка деплоя
./scripts/monitoring/monitor-production.sh
```

## 🔧 Диагностика и исправления

### Проверка логов транскрибации

```bash
# 1. Полный мониторинг
./scripts/monitoring/monitor-production.sh

# 2. Поиск ошибок транскрибации
ssh aisha@192.168.0.10 "docker logs aisha-bot-polling-1 | grep -E '(transcript|audio|ERROR)'"

# 3. Проверка worker'ов
ssh aisha@192.168.0.10 "docker logs aisha-worker-1 --tail 20"

# 4. Проверка Redis очередей
ssh aisha@192.168.0.10 "docker exec redis-prod redis-cli LLEN transcript_queue"
```

### Исправление standby бота

```bash
# Временное решение: остановить standby бот
ssh aisha@192.168.0.10 "docker stop aisha-bot-polling-2"

# Долгосрочное решение: реализовать true standby режим
# 1. Мониторинг основного бота
# 2. Автоматический failover при падении
# 3. Health check система
```

### Тестирование транскрибации

```bash
# 1. Отправить голосовое сообщение боту в Telegram
# 2. Проверить обработку в логах
ssh aisha@192.168.0.10 "docker logs aisha-bot-polling-1 --follow"

# 3. Проверить файлы в MinIO
# 4. Проверить записи в PostgreSQL
```

## 📋 Чек-лист релиза

### Перед деплоем
- [ ] ✅ Все тесты проходят локально
- [ ] ✅ Code review выполнен
- [ ] ✅ Документация обновлена
- [ ] ✅ Миграции БД протестированы
- [ ] ✅ Переменные окружения актуальны

### Процесс деплоя
- [ ] ✅ Резервная копия БД создана
- [ ] ✅ Деплой скрипт запущен успешно
- [ ] ✅ Все контейнеры healthy
- [ ] ✅ Основные функции работают
- [ ] ✅ Мониторинг показывает норму

### После деплоя
- [ ] ✅ Функционал протестирован вручную
- [ ] ✅ Логи не показывают критических ошибок
- [ ] ✅ Производительность в норме
- [ ] ✅ Rollback план готов

## 🛠️ Инструменты разработки

### Локальная разработка
```bash
# Запуск тестов
python -m pytest tests/ -v

# Проверка типов
mypy app/

# Форматирование кода  
black app/
isort app/

# Запуск бота локально
python main.py
```

### Продакшн мониторинг
```bash
# Быстрая проверка
./scripts/monitoring/monitor-production.sh quick

# Детальный мониторинг
./scripts/monitoring/monitor-production.sh full

# Проверка конкретного компонента
./scripts/monitoring/monitor-production.sh logs
./scripts/monitoring/monitor-production.sh health
./scripts/monitoring/monitor-production.sh system
```

## 🚨 Аварийные процедуры

### Rollback деплоя
```bash
# 1. Откат к предыдущей версии образов
ssh aisha@192.168.0.10 "
    docker tag localhost:5000/aisha-bot:previous localhost:5000/aisha-bot:latest
    docker-compose -f docker-compose.bot.registry.yml restart
"

# 2. Откат миграций БД (если нужно)
alembic downgrade -1
```

### Экстренное восстановление
```bash
# 1. Перезапуск всех сервисов
ssh aisha@192.168.0.10 "
    docker-compose -f docker-compose.webhook.prod.yml restart
    docker-compose -f docker-compose.bot.registry.yml restart
"

# 2. Очистка проблемных контейнеров
ssh aisha@192.168.0.10 "docker system prune -f"
```

## 📊 Результат

**✅ Организованный workflow:**
- 🏠 **Локальная разработка** с тестированием
- 🔄 **Git flow** с code review
- 🚀 **Автоматизированный деплой** через скрипты
- 📊 **Мониторинг** и диагностика
- 🚨 **Процедуры восстановления**

**🎯 Следующие шаги:**
1. Исправить standby бота (true failover)
2. Протестировать транскрибацию
3. Настроить staging окружение  
4. Добавить автоматические тесты 