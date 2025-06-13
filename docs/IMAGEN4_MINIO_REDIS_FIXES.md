# Исправления Imagen4, MinIO и Redis

## Обзор изменений

Данный документ описывает исправления, внесенные для решения проблем с:
1. Ошибками в обработчиках Imagen4
2. Структурой директорий MinIO для Imagen4
3. Подключением к Redis и устаревшими методами

## 🔧 Исправленные проблемы

### 1. Ошибка в handle_imagen4_menu()

**Проблема:**
```
TypeError: handle_imagen4_menu() got an unexpected keyword argument 'user'
```

**Решение:**
- Убран дублирующий декоратор `@require_user()` из роутов
- Декоратор остался только в методах класса `Imagen4Handler`

**Файлы:**
- `app/handlers/imagen4/imagen4_handler.py`

### 2. Отдельная директория для Imagen4 в MinIO

**Проблема:**
- Imagen4 изображения сохранялись в общую папку `generated`
- Отсутствовала отдельная конфигурация для Imagen4

**Решение:**
- Добавлен отдельный bucket `imagen4` в конфигурацию MinIO
- Обновлена логика `ImageStorage` для выбора bucket по типу генерации
- Добавлены настройки в `app/core/config.py` и `app/core/resources.py`

**Конфигурация:**
```python
# MinIO buckets
MINIO_BUCKETS = {
    "avatars": "avatars",
    "imagen4": "imagen4",  # Новый bucket для Imagen4
    "generated": "generated"
}

# Folders
FOLDERS = {
    "imagen4": "imagen4/",  # Отдельная папка
}
```

**Файлы:**
- `app/core/config.py`
- `app/core/resources.py`
- `app/services/generation/storage/image_storage.py`

### 3. Исправление Redis подключений

**Проблема:**
```
DeprecationWarning: Call to deprecated close. (Use aclose() instead)
```

**Решение:**
- Заменен устаревший метод `close()` на `aclose()` во всех Redis клиентах
- Обновлены все сервисы, использующие Redis

**Файлы:**
- `app/core/redis.py`
- `app/services/avatar/redis_service.py`
- `app/services/avatar/notification_service.py`
- `app/core/redis_session.py`
- `scripts/maintenance/check_redis.py`

## 📁 Структура хранения Imagen4

### Bucket структура:
```
imagen4/
├── 2025/
│   ├── 06/
│   │   ├── 13/
│   │   │   ├── {generation_id}_1.jpg
│   │   │   ├── {generation_id}_2.jpg
│   │   │   └── ...
│   │   └── ...
│   └── ...
└── ...
```

### Логика выбора bucket:
```python
if generation.generation_type == "imagen4":
    bucket = "imagen4"  # Отдельный bucket для Imagen4
else:
    bucket = "generated"  # Общий bucket для остальных типов
```

## 🔄 Обновленная логика сохранения

### ImageStorage.save_images_to_minio():
1. **Определение bucket** по типу генерации
2. **Скачивание** изображений с FAL AI
3. **Сохранение** в соответствующий MinIO bucket
4. **Генерация** presigned URLs для доступа
5. **Fallback** к FAL URLs при ошибках MinIO

### Удаление изображений:
- Автоматическое определение bucket из URL
- Fallback поиск в нескольких bucket'ах
- Безопасное удаление с логированием

## 🧪 Тестирование

### Redis подключение:
```bash
cd /opt/aisha-backend
source .venv/bin/activate
python scripts/maintenance/check_redis.py
```

**Результат:**
```
✅ Redis подключение успешно
✅ Операции чтения/записи работают
✅ Нет предупреждений о deprecated методах
```

### Запуск бота:
```bash
cd /opt/aisha-backend
source .venv/bin/activate
python -m app.main
```

**Результат:**
```
✅ Бот запускается без ошибок
✅ Обработчики Imagen4 регистрируются корректно
✅ Redis подключение стабильно
```

## 📊 Производительность

### Redis кеширование:
- **Генерации Imagen4**: `imagen4:generation:{id}` (TTL: 1 час)
- **Пользовательские списки**: `imagen4:user_generations:{user_id}` (TTL: 24 часа)
- **Фильтрованные галереи**: `gallery:filtered:{user_id}:{filter_hash}` (TTL: 5 минут)

### MinIO хранение:
- **Imagen4**: Отдельный bucket для изоляции
- **Presigned URLs**: 24 часа для доступа
- **Автоматическая структура**: По дате создания

## 🔐 Безопасность

### Redis:
- Пароль: `wd7QuwAbG0wtyoOOw3Sm`
- Хост: `192.168.0.3:6379`
- SSL: отключен для локальной сети

### MinIO:
- Endpoint: `192.168.0.4:9000`
- Access Key: `minioadmin`
- Secret Key: `74rSbw9asQ1uMzcFeM5G`
- SSL: отключен для локальной сети

## 🚀 Развертывание

### Переменные окружения:
```bash
# Redis
REDIS_HOST=192.168.0.3
REDIS_PORT=6379
REDIS_PASSWORD=wd7QuwAbG0wtyoOOw3Sm

# MinIO
MINIO_ENDPOINT=192.168.0.4:9000
MINIO_BUCKET_IMAGEN4=imagen4
```

### Docker конфигурация:
- Все настройки уже добавлены в `docker-compose` файлы
- Поддержка как dev, так и prod окружений

## 📝 Заключение

Все исправления внесены и протестированы:

✅ **Imagen4 обработчики** работают без ошибок  
✅ **MinIO структура** оптимизирована для Imagen4  
✅ **Redis подключения** обновлены до актуальных методов  
✅ **Кеширование** работает стабильно  
✅ **Производительность** улучшена  

Система готова к продуктивному использованию. 