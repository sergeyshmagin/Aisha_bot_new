# Устранение неисправностей AISHA Backend

## 🚨 Типичные проблемы и решения

### 🖼️ Проблемы с галереей

#### Пустая галерея Imagen4
**Симптомы:**
- Генерация Imagen4 работает
- Изображения не отображаются в галерее
- Фильтр показывает 0 изображений

**Решение:**
```bash
# Проверяем конфигурацию MinIO
python scripts/debug/check_imagen4_config.py

# Проверяем сохранение в правильный bucket
grep -r "MINIO_BUCKET" app/services/generation/

# Очищаем тестовые данные если есть
python scripts/debug/cleanup_test_imagen4.py
```

**Корневая причина:** Неправильный bucket или тестовые URL

#### Фильтры сбрасываются при навигации
**Симптомы:**
- Устанавливаем фильтр
- Переключаемся между изображениями
- Фильтр исчезает

**Решение:**
```bash
# Проверяем Redis подключение
redis-cli -h 192.168.0.3 ping

# Проверяем кэширование состояний
python -c "from app.handlers.gallery.states import gallery_state_manager; print('OK')"
```

**Корневая причина:** Отсутствие Redis или проблемы с GalleryStateManager

#### Кнопка "Назад" не работает
**Симптомы:**
- Нажимаем "Назад" в галерее
- Ничего не происходит или ошибка

**Решение:**
```bash
# Проверяем callback handlers
grep -r "gallery_all" app/handlers/gallery/

# Проверяем состояния FSM
python -c "from app.handlers.gallery.states import GalleryStates; print('OK')"
```

### 🎨 Проблемы с генерацией

#### Imagen4 зависает в PENDING
**Симптомы:**
- Создаем изображение
- Статус остается PENDING долго
- Изображение не появляется

**Решение:**
```bash
# Проверяем FAL AI токен
echo $FAL_KEY

# Проверяем статус через API
python -c "
import os
print('FAL_KEY:', os.getenv('FAL_KEY', 'NOT_SET')[:10] + '...')
"

# Очищаем зависшие генерации
python -c "
from app.core.database import get_session
from app.database.models import ImageGeneration, GenerationStatus
# (код для очистки PENDING записей)
"
```

#### Тестовые URL вместо реальных
**Симптомы:**
- Изображения генерируются
- URL содержат "example.com"
- Изображения не отображаются

**Решение:**
```bash
# Проверяем URL в базе
python -c "
from app.core.database import get_session
from app.database.models import ImageGeneration
# SELECT result_urls FROM image_generation WHERE result_urls LIKE '%example%'
"

# Исправляем если найдены
# Скрипт для замены тестовых URL создан и выполнен ранее
```

### 🗄️ Проблемы с хранилищем

#### MinIO недоступен
**Симптомы:**
- Ошибки подключения к MinIO
- Изображения не сохраняются

**Решение:**
```bash
# Проверяем доступность MinIO
curl http://192.168.0.4:9000/health/live

# Проверяем конфигурацию
python -c "
from app.core.config import settings
print('MinIO endpoint:', settings.MINIO_ENDPOINT)
print('MinIO bucket:', getattr(settings, 'MINIO_BUCKET', 'NOT_SET'))
"

# Создаем bucket если не существует
mc alias set local http://192.168.0.4:9000 minioadmin minioadmin
mc mb local/imagen4
mc mb local/photos
```

#### Redis недоступен
**Симптомы:**
- Состояния не сохраняются
- Фильтры сбрасываются

**Решение:**
```bash
# Проверяем Redis
redis-cli -h 192.168.0.3 ping

# Проверяем подключение из приложения
python -c "
from app.services.cache_service import cache_service
import asyncio
asyncio.run(cache_service.ping())
"
```

### 👤 Проблемы с пользователями

#### Баланс не списывается
**Симптомы:**
- Генерация проходит
- Баланс остается прежним

**Решение:**
```bash
# Проверяем сервис баланса
python -c "
from app.services.balance_service import BalanceService
print('Balance service OK')
"

# Проверяем транзакции
python scripts/admin/add_balance.py --stats
```

#### Пользователь не найден
**Симптомы:**
- Ошибка при обращении к боту
- "User not found" в логах

**Решение:**
```bash
# Проверяем пользователей
python scripts/admin/add_balance.py --list

# Создаем пользователя если нужно
python -c "
from app.services.user_service import UserService
# (код для создания пользователя)
"
```

### 🔧 Системные проблемы

#### Import errors
**Симптомы:**
- Ошибки импорта модулей
- "cannot import name" в логах

**Решение:**
```bash
# Проверяем виртуальное окружение
which python
pip list | grep -E "(aiogram|sqlalchemy|redis)"

# Переустанавливаем зависимости
pip install -r requirements.txt
```

#### Circular imports
**Симптомы:**
- ImportError: cannot import name
- Проблемы при запуске

**Решение:**
1. Используйте ленивые импорты в функциях
2. Реорганизуйте структуру модулей
3. Используйте dependency injection

### 📊 Диагностические команды

#### Проверка всех сервисов
```bash
# База данных
python -c "from app.core.database import get_session; print('DB OK')"

# Redis
redis-cli -h 192.168.0.3 ping

# MinIO
curl -I http://192.168.0.4:9000/health/live

# FAL AI
python -c "import os; print('FAL_KEY set:', bool(os.getenv('FAL_KEY')))"
```

#### Проверка конкретного пользователя
```bash
# Данные пользователя
python scripts/admin/add_balance.py --list | grep "174171680"

# Изображения пользователя
python -c "
from app.core.database import get_session
from app.database.models import ImageGeneration, User
# SELECT count(*) FROM image_generation WHERE user_id = ...
"
```

#### Очистка кэшей
```bash
# Redis кэш
redis-cli -h 192.168.0.3 FLUSHALL

# Python кэш
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
```

## 🆘 Экстренные ситуации

### Полная перезагрузка
```bash
# Остановка всех сервисов
pkill -f "python -m app.main"

# Очистка кэшей
redis-cli -h 192.168.0.3 FLUSHALL

# Перезапуск
python -m app.main
```

### Восстановление из бэкапа
```bash
# БД (если есть бэкап)
pg_restore -h 192.168.0.4 -U aisha -d aisha_db backup.sql

# MinIO (если есть бэкап)
mc cp --recursive backup/ local/imagen4/
```

### Откат к предыдущей версии
```bash
# Git откат
git log --oneline -10
git reset --hard <commit_hash>

# Docker откат
docker pull registry:5000/aisha-backend:previous
docker-compose up -d
```

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте логи**: `tail -f logs/app.log`
2. **Проверьте статус сервисов**: команды выше
3. **Проверьте конфигурацию**: переменные окружения
4. **Создайте issue**: с подробным описанием и логами 