# 🎓 Руководство по обучению Aisha Bot

## 🚀 Готовность к обучению

✅ **Все системы готовы к обучению!**

### Предварительные проверки (на сервере)

```bash
# 1. Проверка статуса сервисов
sudo systemctl status aisha-bot.service
sudo systemctl status aisha-api.service

# 2. Проверка логов
sudo journalctl -u aisha-bot.service -n 20
sudo journalctl -u aisha-api.service -n 20

# 3. Тест webhook API
python scripts/test_webhook.py

# 4. Проверка БД
python -c "from app.database.connection import get_db_session; print('DB OK')"
```

## 🎯 Процесс обучения

### 1. Мониторинг во время обучения

```bash
# Следить за логами в реальном времени
sudo journalctl -u aisha-bot.service -f

# Проверка использования ресурсов
htop
df -h
free -h
```

### 2. Ключевые метрики для отслеживания

- **Память:** Следите за использованием RAM
- **Диск:** Проверяйте свободное место в `/opt/aisha-backend/storage/`
- **Сеть:** Мониторьте подключения к Telegram API
- **База данных:** Отслеживайте рост таблиц с диалогами

### 3. Webhook для FAL AI

**URL для настройки в FAL AI:**
```
https://aishabot.aibots.kz:8443/api/v1/avatar/status_update
```

**Тестирование webhook:**
```bash
curl -k -X POST https://aishabot.aibots.kz:8443/api/v1/avatar/status_update \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test_123",
    "status": "completed",
    "result": {
      "video_url": "https://example.com/video.mp4"
    }
  }'
```

## 🔧 Настройки для обучения

### Переменные окружения (в .env)

```bash
# Основные настройки
TELEGRAM_BOT_TOKEN=your_token_here
DATABASE_URL=postgresql://user:pass@localhost/aisha_db

# Настройки для обучения
LEARNING_MODE=true
MAX_CONTEXT_LENGTH=4000
RESPONSE_TEMPERATURE=0.7

# FAL AI настройки
FAL_API_KEY=your_fal_key_here
WEBHOOK_URL=https://aishabot.aibots.kz:8443/api/v1/avatar/status_update
```

### Рекомендуемые лимиты

- **Максимум сообщений в час:** 1000
- **Размер контекста:** 4000 токенов
- **Timeout для ответов:** 30 секунд
- **Размер файлов:** до 20MB

## 📊 Мониторинг обучения

### Логи для анализа

```bash
# Ошибки и предупреждения
sudo journalctl -u aisha-bot.service -p err -n 50

# Статистика сообщений
grep "Processing message" /var/log/aisha-bot.log | wc -l

# Время ответов
grep "Response time" /var/log/aisha-bot.log | tail -20
```

### Базовые метрики

1. **Количество диалогов в день**
2. **Среднее время ответа**
3. **Процент успешных ответов**
4. **Использование различных функций (аудио, изображения, аватары)**

## 🚨 Аварийные процедуры

### При высокой нагрузке

```bash
# Перезапуск сервисов
sudo systemctl restart aisha-bot.service
sudo systemctl restart aisha-api.service

# Очистка временных файлов
sudo find /opt/aisha-backend/storage/temp -type f -mtime +1 -delete

# Проверка места на диске
df -h /opt/aisha-backend/
```

### При ошибках БД

```bash
# Проверка подключения
sudo -u postgres psql -c "SELECT version();"

# Бэкап БД
sudo -u postgres pg_dump aisha_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Проверка размера БД
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('aisha_db'));"
```

## 📈 Оптимизация производительности

### Настройки PostgreSQL

```sql
-- Увеличение shared_buffers для лучшей производительности
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
SELECT pg_reload_conf();
```

### Настройки Python

```bash
# Увеличение лимитов для asyncio
export PYTHONUNBUFFERED=1
export PYTHONASYNCIODEBUG=0
```

## 🎉 Готово к обучению!

Все системы настроены и готовы к интенсивному обучению. Следите за метриками и логами для обеспечения стабильной работы.

### Контакты поддержки

- **Логи:** `sudo journalctl -u aisha-bot.service -f`
- **Статус:** `sudo systemctl status aisha-*`
- **Тесты:** `python scripts/test_webhook.py`

---

**🚀 Удачного обучения Aisha Bot!** 