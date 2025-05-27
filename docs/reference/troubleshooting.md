# 🚨 Справочник по решению проблем

**Обновлено:** 15.01.2025  
**Статус:** ✅ Актуальный справочник  
**Версия:** v2.0

## 📋 Обзор

Справочник содержит решения типичных проблем, с которыми можно столкнуться при работе с Aisha v2. Включает диагностику, исправления и профилактические меры.

## 🔧 Общие проблемы

### 1. Бот не отвечает на сообщения

#### Симптомы
- Сообщения боту не получают ответа
- Команды не обрабатываются
- Статус бота показывает "offline"

#### Диагностика
```bash
# Проверка статуса сервиса
sudo systemctl status aisha-bot

# Проверка логов
sudo journalctl -u aisha-bot -n 50

# Проверка токена
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

#### Решения
1. **Неверный токен:**
   ```bash
   # Проверьте TELEGRAM_BOT_TOKEN в .env
   grep TELEGRAM_BOT_TOKEN /opt/aisha_v2/.env
   ```

2. **Сервис не запущен:**
   ```bash
   sudo systemctl start aisha-bot
   sudo systemctl enable aisha-bot
   ```

3. **Ошибки в коде:**
   ```bash
   # Проверка синтаксиса
   cd /opt/aisha_v2
   source venv/bin/activate
   python -m py_compile app/main.py
   ```

### 2. Ошибки базы данных

#### Симптомы
- "Connection refused" ошибки
- Таблицы не найдены
- Миграции не применяются

#### Диагностика
```bash
# Проверка подключения к PostgreSQL
psql -h localhost -U aisha_user -d aisha_v2 -c "SELECT version();"

# Проверка статуса миграций
cd /opt/aisha_v2
source venv/bin/activate
alembic current
alembic history
```

#### Решения
1. **PostgreSQL не запущен:**
   ```bash
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

2. **Неверные учетные данные:**
   ```bash
   # Проверьте настройки в .env
   grep DATABASE_ /opt/aisha_v2/.env
   ```

3. **Миграции не применены:**
   ```bash
   cd /opt/aisha_v2
   source venv/bin/activate
   alembic upgrade head
   ```

### 3. Проблемы с FAL AI

#### Симптомы
- Обучение аватаров не запускается
- Webhook не приходят
- Ошибки аутентификации

#### Диагностика
```bash
# Проверка API ключа
curl -H "Authorization: Key YOUR_FAL_API_KEY" https://fal.run/fal-ai/fast-sdxl

# Проверка webhook endpoint
curl -X POST https://yourdomain.com:8443/api/v1/avatar/status_update \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

#### Решения
1. **Неверный API ключ:**
   ```bash
   # Проверьте FAL_API_KEY в .env
   grep FAL_API_KEY /opt/aisha_v2/.env
   ```

2. **Webhook недоступен:**
   ```bash
   # Проверьте API сервер
   sudo systemctl status aisha-api-server
   curl https://localhost:8443/health
   ```

3. **Тестовый режим включен:**
   ```bash
   # Для продакшна установите false
   FAL_TRAINING_TEST_MODE=false
   ```

## 🎭 Проблемы с аватарами

### 1. Пустая галерея аватаров

#### Проблема
Пользователи видят пустую галерею даже при наличии аватаров в базе данных.

#### Причины
- Ошибки в запросах к базе данных
- Проблемы с фильтрацией по статусу
- Неправильная обработка исключений

#### Решение
```python
# Исправленный запрос в avatar_service.py
async def get_user_avatars(self, user_id: UUID) -> List[Avatar]:
    try:
        query = select(Avatar).where(
            Avatar.user_id == user_id,
            Avatar.status.in_([AvatarStatus.COMPLETED, AvatarStatus.TRAINING])
        ).order_by(Avatar.created_at.desc())
        
        result = await self.db.execute(query)
        avatars = result.scalars().all()
        
        logger.info(f"Найдено {len(avatars)} аватаров для пользователя {user_id}")
        return list(avatars)
        
    except Exception as e:
        logger.exception(f"Ошибка получения аватаров: {e}")
        return []
```

### 2. Ошибка finetune_id не найден

#### Проблема
При генерации изображений возникает ошибка "finetune_id not found".

#### Причины
- Обучение не завершено
- Неправильное сохранение finetune_id
- Проблемы с webhook обработкой

#### Решение
```python
# Проверка и исправление finetune_id
async def fix_missing_finetune_ids():
    avatars = await db.execute(
        select(Avatar).where(
            Avatar.status == AvatarStatus.COMPLETED,
            Avatar.finetune_id.is_(None)
        )
    )
    
    for avatar in avatars.scalars():
        # Попытка восстановить из логов или повторное обучение
        logger.warning(f"Аватар {avatar.id} без finetune_id")
```

### 3. Проблемы с загрузкой фотографий

#### Симптомы
- Фотографии не загружаются в MinIO
- Ошибки валидации
- Дублирование фотографий

#### Решения
1. **MinIO недоступен:**
   ```bash
   sudo systemctl status minio
   mc admin info local
   ```

2. **Неправильные права доступа:**
   ```bash
   mc policy set public local/aisha-v2-avatars
   ```

3. **Проблемы с валидацией:**
   ```python
   # Улучшенная валидация в photo_upload_service.py
   async def validate_photo(self, file_data: bytes) -> bool:
       try:
           # Проверка формата
           image = Image.open(io.BytesIO(file_data))
           if image.format not in ['JPEG', 'PNG', 'WEBP']:
               return False
           
           # Проверка размера
           if len(file_data) > 20 * 1024 * 1024:  # 20MB
               return False
           
           return True
       except Exception:
           return False
   ```

## 🔄 Проблемы с генерацией изображений

### 1. Медленная генерация

#### Симптомы
- Генерация занимает более 2 минут
- Таймауты запросов
- Пользователи жалуются на ожидание

#### Решения
1. **Оптимизация параметров:**
   ```python
   # Быстрые настройки для FLUX1.1 Ultra
   FAST_GENERATION_PARAMS = {
       "num_inference_steps": 20,  # Вместо 35
       "guidance_scale": 3.0,      # Вместо 3.5
       "finetune_strength": 1.0    # Вместо 1.1
   }
   ```

2. **Использование кэширования:**
   ```python
   # Кэширование популярных промптов
   @lru_cache(maxsize=100)
   async def generate_cached_image(prompt_hash: str, finetune_id: str):
       # Генерация с кэшированием
       pass
   ```

### 2. Ошибки безопасности контента

#### Проблема
FAL AI блокирует генерацию из-за safety checker.

#### Решение
```python
# Настройка safety checker
GENERATION_PARAMS = {
    "enable_safety_checker": True,
    "safety_tolerance": "2",  # Более мягкие ограничения
}

# Предварительная фильтрация промптов
def sanitize_prompt(prompt: str) -> str:
    # Удаление потенциально проблемных слов
    blocked_words = ["nude", "naked", "explicit"]
    for word in blocked_words:
        prompt = prompt.replace(word, "")
    return prompt.strip()
```

## 📡 Проблемы с API сервером

### 1. SSL сертификаты

#### Симптомы
- Webhook не работают
- Ошибки SSL handshake
- Браузер показывает "небезопасное соединение"

#### Решения
1. **Обновление сертификатов:**
   ```bash
   sudo certbot renew
   sudo systemctl restart aisha-api-server
   ```

2. **Проверка конфигурации:**
   ```bash
   openssl s_client -connect yourdomain.com:8443
   ```

3. **Исправление путей к сертификатам:**
   ```python
   # В api_server/run_api_server.py
   SSL_CERT_PATH = "/etc/letsencrypt/live/yourdomain.com/fullchain.pem"
   SSL_KEY_PATH = "/etc/letsencrypt/live/yourdomain.com/privkey.pem"
   ```

### 2. Webhook не обрабатываются

#### Симптомы
- FAL AI отправляет webhook, но статус не обновляется
- Логи показывают 404 или 500 ошибки

#### Решения
1. **Проверка маршрутов:**
   ```python
   # Правильный маршрут в api_server
   @app.post("/api/v1/avatar/status_update")
   async def fal_webhook(request: Request):
       # Обработка webhook
       pass
   ```

2. **Логирование webhook:**
   ```python
   @app.post("/api/v1/avatar/status_update")
   async def fal_webhook(request: Request):
       data = await request.json()
       logger.info(f"Получен webhook: {data}")
       # Дальнейшая обработка
   ```

## 🗄️ Проблемы с хранилищем

### 1. MinIO недоступен

#### Симптомы
- Ошибки загрузки файлов
- "Connection refused" к MinIO
- Фотографии не сохраняются

#### Решения
1. **Перезапуск сервиса:**
   ```bash
   sudo systemctl restart minio
   sudo systemctl status minio
   ```

2. **Проверка конфигурации:**
   ```bash
   cat /etc/default/minio
   mc admin info local
   ```

3. **Создание недостающих buckets:**
   ```bash
   mc mb local/aisha-v2-avatars
   mc mb local/aisha-v2-transcripts
   mc policy set public local/aisha-v2-avatars
   ```

### 2. Redis проблемы

#### Симптомы
- Медленная работа приложения
- Ошибки кэширования
- Сессии не сохраняются

#### Решения
1. **Очистка Redis:**
   ```bash
   redis-cli FLUSHALL
   ```

2. **Проверка памяти:**
   ```bash
   redis-cli INFO memory
   ```

3. **Настройка политики вытеснения:**
   ```bash
   redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

## 🔍 Диагностические команды

### Быстрая диагностика системы
```bash
#!/bin/bash
# health_check.sh

echo "=== Проверка сервисов ==="
systemctl is-active aisha-bot
systemctl is-active aisha-api-server
systemctl is-active postgresql
systemctl is-active redis
systemctl is-active minio

echo "=== Проверка портов ==="
netstat -tlnp | grep -E "(8000|8443|5432|6379|9000)"

echo "=== Проверка дискового пространства ==="
df -h

echo "=== Проверка памяти ==="
free -h

echo "=== Последние ошибки ==="
journalctl -u aisha-bot --since "1 hour ago" | grep ERROR
```

### Проверка конфигурации
```bash
#!/bin/bash
# config_check.sh

echo "=== Проверка переменных окружения ==="
cd /opt/aisha_v2
source venv/bin/activate

python -c "
import os
from app.core.config import settings

required_vars = [
    'TELEGRAM_BOT_TOKEN',
    'DATABASE_HOST',
    'FAL_API_KEY',
    'OPENAI_API_KEY'
]

for var in required_vars:
    value = getattr(settings, var, None)
    if value:
        print(f'✅ {var}: установлен')
    else:
        print(f'❌ {var}: НЕ УСТАНОВЛЕН')
"
```

## 📞 Получение помощи

### Логи для анализа
При обращении за помощью приложите:

1. **Логи сервисов:**
   ```bash
   journalctl -u aisha-bot --since "1 hour ago" > bot_logs.txt
   journalctl -u aisha-api-server --since "1 hour ago" > api_logs.txt
   ```

2. **Логи приложения:**
   ```bash
   tail -n 100 /var/log/aisha_v2/app.log > app_logs.txt
   ```

3. **Конфигурация (без секретов):**
   ```bash
   grep -v -E "(TOKEN|KEY|PASSWORD)" /opt/aisha_v2/.env > config_safe.txt
   ```

### Контакты поддержки
- **Документация:** `/opt/aisha_v2/docs/`
- **Логи:** `/var/log/aisha_v2/`
- **Конфигурация:** `/opt/aisha_v2/.env`

---

**💡 Совет:** Всегда делайте резервные копии перед внесением изменений! 