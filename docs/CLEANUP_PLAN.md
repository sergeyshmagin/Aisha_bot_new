# 🧹 ПЛАН ОЧИСТКИ СИСТЕМЫ AISHA BACKEND

## 📅 Дата: 2024-12-11
## 🎯 Цель: Очистка устаревших файлов, скриптов и образов для чистого продакшн деплоя

---

## 📋 1. ИНВЕНТАРИЗАЦИЯ API_SERVER

### ✅ **АКТУАЛЬНЫЕ ФАЙЛЫ:**
- `webhook_main.py` - основной webhook сервер (496 строк) **KEEP**
- `Dockerfile.webhook` - Docker образ для webhook API **KEEP**
- `requirements.txt` - зависимости Python **KEEP**
- `README.md` - документация API сервера **KEEP**
- `env.example` - пример конфигурации **KEEP**
- `ssl/` - SSL сертификаты **KEEP**

### ❌ **LEGACY ФАЙЛЫ (переименованы):**
- `main_LEGACY.py` - устаревший основной файл **DELETE**
- `test_main_LEGACY.py` - простой тест **DELETE**
- `run_api_server_LEGACY.py` - устаревший запускатель **DELETE**
- `app_LEGACY/` - дублирующая структура **DELETE**
- `legacy_main.py` - уже помеченный legacy **DELETE**

---

## 📋 2. ИНВЕНТАРИЗАЦИЯ СКРИПТОВ

### ✅ **КРИТИЧЕСКИ ВАЖНЫЕ СКРИПТЫ:**
- `scripts/test_webhook_system.py` - система тестирования **KEEP**
- `scripts/deploy/webhook-remote-deploy.sh` - удаленный деплой **KEEP**
- `scripts/production/manage-webhook.sh` - управление webhook **KEEP**
- `scripts/production/safe-cleanup.sh` - безопасная очистка **KEEP**

### ⚠️ **УСТАРЕВШИЕ СКРИПТЫ (к анализу):**
- `scripts/deploy-local.sh` - локальный деплой **ANALYZE**
- `scripts/local-dev-setup.sh` - локальная разработка **ANALYZE**
- `scripts/quick-dev.sh` - быстрая разработка **ANALYZE**
- `scripts/production/deploy_production_minimal.sh` - большой скрипт **ANALYZE**
- `scripts/production/fix-telegram-webhook.sh` - фикс telegram **ANALYZE**
- `scripts/production/deploy-transcription-fix.sh` - фикс транскрипции **ANALYZE**

### ❌ **ДУБЛИРУЮЩИЕ СКРИПТЫ:**
- `scripts/setup-registry.sh` + `scripts/deploy/setup-registry.sh` **MERGE**
- Множественные деплой скрипты **CONSOLIDATE**

---

## 📋 3. ИНВЕНТАРИЗАЦИЯ ДОКУМЕНТАЦИИ

### ✅ **АКТУАЛЬНАЯ ДОКУМЕНТАЦИЯ:**
- `docs/WEBHOOK_DEPLOYMENT.md` - деплой webhook **KEEP**
- `docs/architecture.md` - архитектура проекта **KEEP**
- `docs/best_practices.md` - лучшие практики **KEEP**
- `docs/TASK.md` - текущие задачи **KEEP**
- `docs/STATUS_CURRENT.md` - текущий статус **UPDATE**

### ⚠️ **К ОБНОВЛЕНИЮ:**
- `docs/PLANNING.md` - планирование **UPDATE**
- `docs/DEPLOYMENT.md` - общий деплой **UPDATE**
- `docs/README.md` - главная документация **UPDATE**

### ❌ **УСТАРЕВШИЕ:**
- `docs/GALLERY_FIXES.md` - фиксы галереи **DELETE**
- `docs/PAYMENT_SYSTEM.md` - платежная система **ANALYZE**

---

## 🧹 4. ПЛАН ОЧИСТКИ DOCKER REGISTRY

### 📦 **Текущие образы для анализа:**
```bash
# Получить список всех образов в registry
curl -X GET http://192.168.0.4:5000/v2/_catalog

# Получить теги для каждого образа
curl -X GET http://192.168.0.4:5000/v2/{image}/tags/list
```

### 🎯 **Стратегия очистки:**
1. **Оставить последние 3 версии** каждого образа
2. **Удалить все тестовые** образы (содержащие test, temp, debug)
3. **Оставить production образы** (webhook-api:final, nginx-webhook:latest)

---

## 🗂️ 5. ПЛАН ОЧИСТКИ ПРОДАКШН СЕРВЕРА

### 📊 **Анализ текущего состояния:**
```bash
# Проверить использование диска
ssh aisha@192.168.0.10 "df -h"

# Проверить запущенные контейнеры
ssh aisha@192.168.0.10 "docker ps -a"

# Проверить образы
ssh aisha@192.168.0.10 "docker images"

# Проверить volumes
ssh aisha@192.168.0.10 "docker volume ls"
```

### 🧹 **Действия очистки:**
1. **Остановить неиспользуемые контейнеры**
2. **Удалить старые образы** (кроме текущих)
3. **Очистить неиспользуемые volumes**
4. **Очистить Docker build cache**

---

## 🚀 6. ПЛАН ЧИСТОГО ДЕПЛОЯ

### 🎯 **Цель:** Развернуть только webhook API + nginx

### 📝 **Шаги:**
1. **Остановить все сервисы**
2. **Очистить старые контейнеры и образы**
3. **Собрать новый webhook-api образ**
4. **Развернуть nginx + webhook API**
5. **Проверить работоспособность**
6. **Запустить полные тесты**

### 🔧 **Файлы для деплоя:**
- `docker-compose.webhook.prod.yml` - основная конфигурация
- `scripts/deploy/webhook-remote-deploy.sh` - скрипт деплоя
- `scripts/test_webhook_system.py` - тестирование

---

## ✅ 7. КРИТЕРИИ УСПЕХА

- [ ] Все legacy файлы удалены
- [ ] Остались только необходимые скрипты
- [ ] Docker registry очищен (< 5 GB)
- [ ] Продакшн сервер использует < 80% диска
- [ ] Webhook API работает стабильно
- [ ] Все тесты проходят успешно
- [ ] Документация актуализирована

---

## 📞 КОНТАКТЫ ДЛЯ ПОДДЕРЖКИ

- **Webhook endpoints:** http://192.168.0.10:8001, :8002
- **Registry:** 192.168.0.4:5000
- **Database:** 192.168.0.4:5432
- **Redis:** 192.168.0.3:6379 