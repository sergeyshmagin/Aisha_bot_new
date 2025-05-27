# 🚀 Включение продакшн обучения аватаров

## 📍 Текущее состояние

**Конфигурация:** `app/core/config.py`
```python
AVATAR_TEST_MODE: bool = Field(True, env="AVATAR_TEST_MODE")  # ← СЕЙЧАС ВКЛЮЧЕН ТЕСТ
```

## 🔧 Включение продакшена

### 1. Изменить конфигурацию

**Способ 1: Через переменную окружения (рекомендуется)**
```bash
# В .env файле на сервере
AVATAR_TEST_MODE=false
```

**Способ 2: Прямо в коде (для постоянного изменения)**
```python
# app/core/config.py
AVATAR_TEST_MODE: bool = Field(False, env="AVATAR_TEST_MODE")  # ← ПРОДАКШН
```

### 2. Перезапустить сервисы

```bash
# На сервере
sudo systemctl restart aisha-bot.service
sudo systemctl restart aisha-api.service
```

### 3. Проверить применение настроек

```bash
# Проверить логи запуска
sudo journalctl -u aisha-bot.service -n 20 | grep -i avatar
```

## 📊 Мониторинг обучения

### 🔍 Ключевые логи для отслеживания

#### 1. Запуск обучения
```bash
# Поиск запусков обучения
sudo journalctl -u aisha-bot.service -f | grep -E "(Запуск обучения|start.*training|FAL.*training)"

# Ожидаемые логи:
# ✅ ПРОДАКШН: "🎯 Запуск обучения аватара abc123 с типом: portrait"
# ✅ ПРОДАКШН: "💰 ПРОДАКШН: Списано 150 кредитов с баланса пользователя"
# ❌ ТЕСТ: "🧪 ТЕСТ РЕЖИМ: Пропускаем отправку на обучение"
```

#### 2. Статус FAL AI запросов
```bash
# Отслеживание реальных запросов к FAL AI
sudo journalctl -u aisha-bot.service -f | grep -E "(FAL.*request|fal.*training|request_id)"

# Ожидаемые логи:
# ✅ ПРОДАКШН: "FAL AI запрос отправлен: request_id=req_abc123"
# ✅ ПРОДАКШН: "FAL training started with ID: req_abc123"
# ❌ ТЕСТ: "🧪 Сгенерирован тестовый request_id: test_abc123"
```

#### 3. Webhook получение
```bash
# Отслеживание webhook от FAL AI
sudo journalctl -u aisha-api.service -f | grep -E "(webhook|status_update|avatar.*completed)"

# Ожидаемые логи:
# ✅ ПРОДАКШН: "Получен webhook от FAL AI: request_id=req_abc123, status=completed"
# ✅ ПРОДАКШН: "Аватар abc123 обучение завершено, модель сохранена"
# ❌ ТЕСТ: "🧪 Тестовый webhook отправлен: 200"
```

#### 4. Обновление статуса аватара
```bash
# Отслеживание обновлений в БД
sudo journalctl -u aisha-bot.service -f | grep -E "(avatar.*status|AvatarStatus|COMPLETED)"

# Ожидаемые логи:
# ✅ "Аватар abc123 статус изменен: TRAINING → COMPLETED"
# ✅ "Модель аватара сохранена: https://fal.ai/files/model.safetensors"
```

### 🎯 Команды для мониторинга

#### Общий мониторинг
```bash
# Все логи аватаров в реальном времени
sudo journalctl -u aisha-bot.service -u aisha-api.service -f | grep -i avatar

# Только ошибки
sudo journalctl -u aisha-bot.service -u aisha-api.service -p err -f

# Статистика за последний час
sudo journalctl -u aisha-bot.service --since "1 hour ago" | grep -c "Запуск обучения"
```

#### Проверка конкретного аватара
```bash
# Поиск по ID аватара
sudo journalctl -u aisha-bot.service -u aisha-api.service | grep "abc123"

# Поиск по request_id
sudo journalctl -u aisha-api.service | grep "req_abc123"
```

#### Проверка webhook API
```bash
# Статус API сервиса
curl -k https://aishabot.aibots.kz:8443/health

# Тест webhook endpoint
curl -k -X POST https://aishabot.aibots.kz:8443/api/v1/avatar/status_update \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test", "status": "completed"}'
```

## 🚨 Индикаторы проблем

### ❌ Признаки что тест режим все еще включен
```bash
# Поиск тестовых логов (не должно быть в продакшене!)
sudo journalctl -u aisha-bot.service -n 100 | grep "🧪"

# Если видите:
# "🧪 ТЕСТ РЕЖИМ: Пропускаем отправку"
# "🧪 Имитация обучения"
# "🧪 Тестовый webhook"
# → AVATAR_TEST_MODE все еще True!
```

### ❌ Проблемы с FAL AI
```bash
# Поиск ошибок FAL AI
sudo journalctl -u aisha-bot.service -p err | grep -i fal

# Типичные ошибки:
# "FAL API key not found" → проверить FAL_API_KEY
# "Insufficient credits" → пополнить баланс FAL AI
# "Request timeout" → проверить сеть
```

### ❌ Проблемы с webhook
```bash
# Проверка недоставленных webhook
sudo journalctl -u aisha-api.service -p err | grep webhook

# Проверка доступности API
sudo lsof -i :8443
sudo systemctl status aisha-api.service
```

## 📈 Метрики успеха

### ✅ Признаки корректной работы продакшена

1. **Запуск обучения:**
   - Логи содержат "🎯 Запуск обучения аватара"
   - НЕТ логов с "🧪 ТЕСТ РЕЖИМ"
   - Списание кредитов: "💰 ПРОДАКШН: Списано X кредитов"

2. **FAL AI интеграция:**
   - Реальные request_id (не начинаются с "test_")
   - Логи "FAL AI запрос отправлен"
   - Получение webhook с реальными данными

3. **Завершение обучения:**
   - Webhook с status="completed"
   - Сохранение реальной модели (.safetensors)
   - Уведомление пользователя о готовности

### 📊 Время обучения в продакшене

| Тип обучения | Ожидаемое время | Лог завершения |
|--------------|-----------------|----------------|
| Портретный (Fast) | 3-5 минут | "Portrait training completed" |
| Портретный (Balanced) | 5-15 минут | "Portrait training completed" |
| Портретный (Quality) | 15-30 минут | "Portrait training completed" |
| Художественный | 10-45 минут | "Style training completed" |

## 🔧 Troubleshooting

### Если обучение не запускается
```bash
# 1. Проверить режим
grep -r "AVATAR_TEST_MODE" /opt/aisha-backend/.env

# 2. Проверить FAL API ключ
grep -r "FAL_API_KEY" /opt/aisha-backend/.env

# 3. Перезапустить сервисы
sudo systemctl restart aisha-bot.service
sudo systemctl restart aisha-api.service

# 4. Проверить логи запуска
sudo journalctl -u aisha-bot.service -n 50
```

### Если webhook не приходят
```bash
# 1. Проверить API сервис
sudo systemctl status aisha-api.service
curl -k https://aishabot.aibots.kz:8443/health

# 2. Проверить webhook URL в FAL AI
echo $FAL_WEBHOOK_URL

# 3. Проверить файрвол
sudo ufw status
sudo lsof -i :8443
```

## 🎯 Готовность к продакшену

### Чек-лист перед включением:
- [ ] `AVATAR_TEST_MODE=false` в .env
- [ ] `FAL_API_KEY` настроен и валиден
- [ ] Webhook API работает (порт 8443)
- [ ] Достаточно кредитов на FAL AI
- [ ] Мониторинг логов настроен
- [ ] Тестовое обучение прошло успешно

---

**🚀 После включения продакшена все обучения будут реальными и платными!** 