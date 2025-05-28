# 🔧 РЕШЕНИЕ ПРОБЛЕМЫ WEBHOOK FAL AI

**Дата:** 2025-01-27  
**Проблема:** Аватар успешно обучился, но webhook не пришел на API  
**Статус:** 🔍 Диагностика и исправление

## 📊 НАЙДЕННЫЕ ПРОБЛЕМЫ

### 1. ❌ Недоступность внешнего API endpoint
```bash
# Ошибка при тестировании
❌ 404, message='Attempt to decode JSON with unexpected mimetype: application/octet-stream'
URL: https://aibots.kz:8443/api/v1/avatar/test_webhook
```

**Причина:** Nginx не проксирует запросы к API серверу

### 2. ⚠️ Возможный тестовый режим
**Проверка:** Бот может работать в `AVATAR_TEST_MODE=true`  
**Проблема:** В тестовом режиме webhook'и не отправляются в FAL AI

### 3. 🔧 Неправильная интеграция API сервера
**Проблема:** API сервер использовал заглушки вместо реальной БД

## ✅ ВЫПОЛНЕННЫЕ ИСПРАВЛЕНИЯ

### 1. 🔗 Исправлен API роутер webhook'а
**Файл:** `api_server/app/routers/fal_webhook.py`

**Изменения:**
- ✅ Добавлена интеграция с основной БД проекта
- ✅ Подключены реальные сервисы (`AvatarTrainingService`, `UserService`)
- ✅ Добавлена отправка уведомлений в Telegram
- ✅ Исправлена обработка фоновых задач

### 2. 🚨 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Передача webhook_url в FAL AI
**Файл:** `app/services/avatar/fal_training_service.py`

**Проблема:** В методе `_train_general_model` webhook_url добавлялся в config, но не передавался как отдельный параметр в `fal_client.submit()`, из-за чего в FAL AI input был `null`.

**Исправление:**
```python
# Было (НЕПРАВИЛЬНО):
result = await self.fal_client.submit(
    "fal-ai/flux-pro-trainer",
    arguments=config  # webhook_url терялся!
)

# Стало (ПРАВИЛЬНО):
result = await self.fal_client.submit(
    "fal-ai/flux-pro-trainer", 
    arguments=config,
    webhook_url=webhook_url  # ✅ Передается отдельно!
)
```

**Результат:** Теперь FAL AI получает корректный webhook_url и будет отправлять уведомления о завершении обучения.

### 3. 🧪 НАСТРОЙКА БЫСТРОГО ТЕСТИРОВАНИЯ
**Файлы:** `app/core/config.py`, `test_training_settings.py`, `restore_training_config.py`

**Изменения для тестирования:**
- ✅ Установлены минимальные значения обучения (1 шаг/итерация)
- ✅ Создан скрипт проверки настроек (`test_training_settings.py`)
- ✅ Создан скрипт восстановления (`restore_training_config.py`)

**Временные настройки:**
```python
FAL_PORTRAIT_STEPS = 1          # было: 1000
FAL_PRO_ITERATIONS = 1          # было: 500
FAL_PRESET_BALANCED = {
    "portrait": {"steps": 1},    # было: 1000
    "general": {"iterations": 1} # было: 500
}
```

**Результат:** Обучение займет 1-2 минуты вместо 15-30 минут, что позволит быстро протестировать webhook.

```python
# Было (заглушка)
async def get_db_session():
    return None

# Стало (реальная БД)
async def get_db_session() -> AsyncSession:
    async for session in get_async_session():
        return session
```

### 4. 🧪 Созданы диагностические скрипты

#### `test_webhook_config.py` - Полная диагностика конфигурации
```bash
python test_webhook_config.py
```

#### `test_training_settings.py` - Проверка настроек обучения
```bash
python test_training_settings.py
```

#### `restore_training_config.py` - Восстановление оригинальных настроек
```bash
python restore_training_config.py
```

#### `test_local_webhook.py` - Тестирование локального API
```bash
python test_local_webhook.py
```

#### `check_training_requests.py` - Проверка активных обучений
```bash
python check_training_requests.py
```

#### `check_webhook_url.py` - Проверка конфигурации
```bash
python check_webhook_url.py
```

#### `test_webhook_simulation.py` - Симуляция webhook'а
```bash
python test_webhook_simulation.py
```

### 5. 🔧 Исправлены критичные ошибки кода
- ✅ **КРИТИЧНО:** Исправлена передача webhook_url в FAL AI (input больше не null)
- ✅ **ТЕСТИРОВАНИЕ:** Настроены минимальные значения обучения (1 шаг/итерация)
- ✅ Добавлен отсутствующий импорт `uuid` в `app/core/redis.py`
- ✅ Удален legacy файл `app/shared/utils/backend.py.LEGACY`
- ✅ Очищены неиспользуемые импорты в `app/api_server.py` и `app/main.py`

## 🔍 ДИАГНОСТИКА ПРОБЛЕМЫ

### Шаг 1: Проверьте конфигурацию и настройки тестирования
```bash
cd /opt/aisha-backend
python test_webhook_config.py
python test_training_settings.py
```

**Ожидаемый результат:**
```
✅ Бот работает в продакшн режиме
✅ FAL_API_KEY установлен
🔗 WEBHOOK URL: https://aibots.kz:8443/api/v1/avatar/status_update
✅ ГОТОВО К БЫСТРОМУ ТЕСТИРОВАНИЮ!
   Обучение займет минимальное время
   Webhook должен прийти через 1-2 минуты
```

### Шаг 2: Проверьте локальный API
```bash
python test_local_webhook.py
```

**Ожидаемый результат:**
```
✅ Статус: 200
📦 Данные: {"status": "ok", "message": "Webhook API работает"}
```

### Шаг 3: Проверьте активные обучения
```bash
python check_training_requests.py
```

### Шаг 4: Протестируйте webhook
```bash
python test_webhook_simulation.py
# Введите реальный request_id из шага 3
```

## 🚨 ВОЗМОЖНЫЕ ПРИЧИНЫ ПРОБЛЕМЫ

### 1. 🔴 Тестовый режим включен
```bash
# Проверьте переменную окружения
echo $AVATAR_TEST_MODE

# Если true - отключите для продакшена
export AVATAR_TEST_MODE=false
# Или в .env файле: AVATAR_TEST_MODE=false
```

### 2. 🔴 Nginx не проксирует API
**Проблема:** Запросы к `https://aibots.kz:8443/api/v1/avatar/*` не доходят до API сервера

**Решение:** Проверьте конфигурацию Nginx:
```nginx
location /api/v1/avatar/ {
    proxy_pass http://localhost:8000/api/v1/avatar/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 3. 🔴 API сервер не запущен
```bash
# Проверьте статус
sudo systemctl status aisha-api.service

# Перезапустите если нужно
sudo systemctl restart aisha-api.service
```

### 4. 🔴 FAL AI не отправляет webhook'и
**Возможные причины:**
- Неправильный webhook_url при запуске обучения
- FAL AI не может достучаться до вашего сервера
- Обучение запущено без webhook_url

## 🎯 ПЛАН ДЕЙСТВИЙ

### Немедленно:
1. **Запустите диагностику:** `python check_webhook_url.py`
2. **Проверьте тестовый режим:** Убедитесь что `AVATAR_TEST_MODE=false`
3. **Протестируйте локальный API:** `python test_local_webhook.py`

### Если локальный API работает:
1. **Проверьте Nginx конфигурацию**
2. **Протестируйте внешний доступ:** `curl https://aibots.kz:8443/api/v1/avatar/test_webhook`
3. **Проверьте логи Nginx:** `sudo tail -f /var/log/nginx/error.log`

### Если внешний API работает:
1. **Найдите активные обучения:** `python check_training_requests.py`
2. **Симулируйте webhook:** `python test_webhook_simulation.py`
3. **Проверьте логи API:** `sudo journalctl -u aisha-api.service -f`

## 📱 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

После исправления проблемы:
1. ✅ Webhook'и от FAL AI будут приходить на API сервер
2. ✅ API сервер будет обрабатывать их через основную БД
3. ✅ Пользователи будут получать уведомления в Telegram о готовности аватара
4. ✅ Статус аватара будет обновляться на "COMPLETED"

## ⚠️ ВАЖНО: ВОССТАНОВЛЕНИЕ НАСТРОЕК

**После успешного тестирования webhook обязательно восстановите оригинальные настройки:**

```bash
python restore_training_config.py
```

**Иначе все последующие обучения будут некачественными (1 шаг вместо 1000)!**

## 🔧 МОНИТОРИНГ

### Логи для отслеживания:
```bash
# API сервер
sudo journalctl -u aisha-api.service -f

# Основной бот
sudo journalctl -u aisha-bot.service -f

# Nginx
sudo tail -f /var/log/nginx/access.log | grep avatar
```

### Ключевые сообщения:
```
[WEBHOOK] Получен webhook от FAL AI
[WEBHOOK BACKGROUND] Webhook обработан успешно
[NOTIFICATION] Уведомление отправлено пользователю
```

---
**Автор:** AI Assistant  
**Следующая проверка:** После применения исправлений 