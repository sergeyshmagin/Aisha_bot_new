# 🎭 Руководство по системе аватаров

**Обновлено:** 15.01.2025  
**Статус:** ✅ Система готова к использованию  
**Версия:** v2.0 с FAL AI интеграцией

## 📋 Обзор системы

Система аватаров Aisha v2 позволяет пользователям создавать персонализированные AI модели для генерации изображений. Поддерживает два типа обучения с автоматическим выбором оптимальной технологии.

### 🎯 Ключевые возможности
- **Два типа обучения:** Портретный и Художественный
- **Автоматический выбор API:** FAL AI Portrait Trainer / Pro Trainer
- **Валидация фотографий:** Проверка качества и содержимого
- **Прогресс в реальном времени:** Webhook уведомления
- **Тестовый режим:** Безопасная разработка без затрат

## 🏗️ Архитектура системы

### Компоненты системы
```
app/
├── handlers/avatar/              # Обработчики UI
│   ├── main.py                  # Главное меню аватаров
│   ├── create.py                # Создание аватара
│   ├── training_type_selection.py # Выбор типа обучения
│   └── photo_upload.py          # Загрузка фотографий
├── services/avatar/             # Бизнес-логика
│   ├── avatar_service.py        # Управление аватарами
│   ├── photo_upload_service.py  # Загрузка и валидация
│   └── fal_training_service.py  # Обучение через FAL AI
├── database/models/             # Модели данных
│   └── avatar.py               # Avatar, AvatarPhoto
└── keyboards/                   # Пользовательский интерфейс
    └── avatar.py               # Клавиатуры аватаров
```

### Модели данных

#### Avatar (Основная модель)
```python
class Avatar(Base):
    # Идентификация
    id: UUID (PK)
    user_id: UUID (FK)
    
    # Основные данные
    name: str                     # Имя аватара
    gender: AvatarGender         # male, female, other
    training_type: AvatarTrainingType  # portrait, style
    
    # Статус и прогресс
    status: AvatarStatus         # draft, training, completed, error
    training_progress: int       # 0-100%
    
    # FAL AI интеграция
    finetune_id: str            # ID обучения в FAL
    fal_mode: str               # "portrait" или "style"
    
    # Временные метки
    created_at: DateTime
    updated_at: DateTime
```

#### AvatarPhoto (Фотографии)
```python
class AvatarPhoto(Base):
    # Идентификация
    id: UUID (PK)
    avatar_id: UUID (FK)
    
    # Файл
    minio_key: str              # Путь в MinIO
    file_hash: str              # MD5 для дедупликации
    file_size: int
    
    # Валидация
    validation_status: PhotoValidationStatus
    has_face: bool
    quality_score: float
    
    # Метаданные
    width: int
    height: int
    created_at: DateTime
```

## 🎨 Типы обучения

### 🎭 Портретный тип (Рекомендуемый)
**Технология:** Flux LoRA Portrait Trainer  
**Оптимизирован для:** Фотографии людей

**Преимущества:**
- ⚡ Быстрое обучение (3-15 минут)
- 🎯 Специализация на лицах
- 🔍 Автоматическая обрезка портретов
- 🎭 Создание масок лица
- ⭐ Превосходное качество для портретов

**Идеально для:**
- Селфи и фотографии людей
- Портретная съемка
- Профессиональные фото
- Личные аватары

### 🎨 Художественный тип
**Технология:** Flux Pro Trainer  
**Оптимизирован для:** Универсальный контент

**Преимущества:**
- 🌐 Поддержка любых стилей и объектов
- 🔧 Гибкие настройки обучения
- 📝 Автоматическое создание описаний
- 🎛️ Различные режимы качества
- 🔄 Максимальная универсальность

**Идеально для:**
- Художественные стили
- Предметы и объекты
- Архитектура и интерьеры
- Абстрактные концепции

## 🔄 Workflow создания аватара

### Этап 1: Выбор типа обучения
```
Главное меню → Создать аватар → Выбор типа обучения
├── 🎭 Портретный (рекомендуется)
├── 🎨 Художественный
└── 📊 Сравнить типы
```

### Этап 2: Настройка аватара
```
Выбор типа → Выбор пола → Ввод имени → Переход к загрузке
```

### Этап 3: Загрузка фотографий
```
Загрузка фото → Валидация → Накопление (10-20 шт) → Готовность к обучению
```

### Этап 4: Обучение
```
Запуск обучения → FAL AI обработка → Webhook уведомления → Завершение
```

## ⚙️ Настройка и конфигурация

### Переменные окружения
```env
# FAL AI API
FAL_API_KEY=your_fal_api_key_here
FAL_WEBHOOK_URL=https://yourdomain.com/api/avatar/status_update

# Тестовый режим (отключает реальные запросы)
FAL_TRAINING_TEST_MODE=true

# Настройки webhook симуляции
FAL_ENABLE_WEBHOOK_SIMULATION=true
FAL_MOCK_TRAINING_DURATION=30

# Лимиты
AVATAR_MIN_PHOTOS=10
AVATAR_MAX_PHOTOS=20
PHOTO_MAX_SIZE=20971520  # 20MB
```

### Пресеты качества
```python
# Быстрое обучение (3-5 минут)
FAL_PRESET_FAST = {
    "portrait": {"steps": 500, "learning_rate": 0.0003},
    "general": {"iterations": 200, "priority": "speed"}
}

# Сбалансированное (5-15 минут)
FAL_PRESET_BALANCED = {
    "portrait": {"steps": 1000, "learning_rate": 0.0002},
    "general": {"iterations": 500, "priority": "quality"}
}

# Качественное (15-30 минут)
FAL_PRESET_QUALITY = {
    "portrait": {"steps": 2500, "learning_rate": 0.0001},
    "general": {"iterations": 1000, "priority": "quality"}
}
```

## 🧪 Тестовый режим

### Настройка тестового режима
При `FAL_TRAINING_TEST_MODE=true`:
- ❌ Реальные запросы к FAL AI **не отправляются**
- ✅ Имитация обучения с настраиваемой длительностью
- ✅ Симуляция webhook для тестирования UX
- ✅ Полное тестирование без затрат

### Логи тестового режима
```
🧪 ТЕСТ РЕЖИМ: Пропускаем отправку на обучение для аватара abc123
🧪 Сгенерирован тестовый request_id: test_abc123_def456
🧪 Имитация обучения portrait, завершение через 30 секунд
🧪 Тестовый webhook отправлен: 200
```

## 📡 Webhook система

### Endpoint конфигурация
```
POST /api/avatar/status_update?training_type={portrait|style}
```

### Обработка статусов
1. **in_progress** → обновление прогресса
2. **completed** → сохранение модели + уведомление пользователя
3. **failed** → обработка ошибки + уведомление

### Формат webhook
```json
{
    "request_id": "req_123456789",
    "status": "completed",
    "progress": 100,
    "training_type": "portrait",
    "result": {
        "diffusers_lora_file": {
            "url": "https://fal.ai/files/model.safetensors",
            "file_name": "avatar_model.safetensors"
        }
    }
}
```

## 🔧 Основные сервисы

### AvatarService
**Файл:** `app/services/avatar/avatar_service.py`

**Ключевые методы:**
```python
async def create_avatar(user_id, name, gender, training_type)
async def get_user_avatars(user_id)
async def update_training_progress(avatar_id, progress)
async def complete_avatar_training(avatar_id, model_url)
```

### PhotoUploadService
**Файл:** `app/services/avatar/photo_upload_service.py`

**Возможности:**
- Валидация формата и размера
- Проверка наличия лиц (для портретного типа)
- Дедупликация по хешу
- Загрузка в MinIO

### FALTrainingService
**Файл:** `app/services/avatar/fal_training_service.py`

**Автоматический выбор API:**
```python
if training_type == "portrait":
    # Flux LoRA Portrait Trainer
    result = await self.portrait_trainer.train_avatar_async(...)
else:
    # Flux Pro Trainer
    result = await self.adapter.train_avatar(...)
```

## 🎹 Пользовательский интерфейс

### Главное меню аватаров
```
🎭 Меню аватаров

Ваши аватары: 3
┌─────────────────────┐
│ 🆕 Создать аватар   │
│ 📁 Мои аватары (3)  │
│ ℹ️ Помощь           │
│ ◀️ Главное меню     │
└─────────────────────┘
```

### Выбор типа обучения
```
🎓 Выберите тип обучения

┌─────────────────────┐
│ 🎭 Портретный       │
│   (рекомендуемый)   │
│                     │
│ 🎨 Художественный   │
│   (универсальный)   │
│                     │
│ 📊 Сравнить типы    │
│ ◀️ Назад            │
└─────────────────────┘
```

### Процесс обучения
```
🤖 Обучение аватара

📊 Прогресс: 65%
⚡ Статус: В процессе...

⏱️ Продолжаем обучение...

┌─────────────────────┐
│ ⏸️ Отменить         │
└─────────────────────┘
```

## 📊 Мониторинг и отладка

### Health check
```bash
curl http://localhost:8000/health
```

### Проверка статуса обучения
```python
from app.services.avatar.fal_training_service import FALTrainingService

service = FALTrainingService()
status = await service.check_training_status(request_id, training_type)
```

### Логирование
```python
logger.info(f"🎭 Создан аватар {avatar_id} пользователем {user_id}")
logger.info(f"📸 Загружено {photo_count} фотографий для аватара {avatar_id}")
logger.info(f"🚀 Запущено обучение аватара {avatar_id} типа {training_type}")
```

## 🚨 Решение проблем

### Webhook не приходят
- Проверьте `FAL_WEBHOOK_URL` в настройках
- Убедитесь что API сервер запущен
- Проверьте доступность URL извне

### Ошибки FAL API
- Проверьте `FAL_API_KEY`
- Убедитесь в наличии кредитов на FAL AI
- Включите тестовый режим: `FAL_TRAINING_TEST_MODE=true`

### Уведомления не приходят
- Проверьте `TELEGRAM_TOKEN`
- Убедитесь в правах бота
- Проверьте логи API сервера

## 📈 Производительность

### Время обучения по типам

| Тип | Пресет | Время | Качество |
|-----|--------|-------|----------|
| Портретный | Fast | 3-5 мин | ⭐⭐⭐ |
| Портретный | Balanced | 5-15 мин | ⭐⭐⭐⭐ |
| Портретный | Quality | 15-30 мин | ⭐⭐⭐⭐⭐ |
| Художественный | Fast | 5-10 мин | ⭐⭐⭐ |
| Художественный | Balanced | 10-20 мин | ⭐⭐⭐⭐ |
| Художественный | Quality | 20-45 мин | ⭐⭐⭐⭐⭐ |

### Рекомендации
- **Портретные аватары:** для селфи и фотографий людей
- **Художественные аватары:** для стилей, объектов, архитектуры
- **Тестовый режим:** всегда тестируйте перед продакшн

---

**🎉 Система аватаров готова к использованию пользователями!** 