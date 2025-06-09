# Архитектура проекта Aisha v2

**Обновлено:** 09.06.2025  
**Статус:** ✅ СТАБИЛЬНАЯ ПРОДАКШН АРХИТЕКТУРА  
**Версия БД:** 5088361401fe (Alembic)  
**Продакшн кластер:** 🚀 РАЗВЕРНУТ И РАБОТАЕТ

## 🏗️ Обзор архитектуры

Проект основан на принципах **Clean Architecture** с четким разделением слоев ответственности. Архитектура полностью асинхронная и использует современные практики разработки.

### Ключевые принципы

1. **Модульность** - каждый компонент имеет четкую область ответственности
2. **Асинхронность** - все I/O операции неблокирующие
3. **Dependency Injection** - управление зависимостями через DI контейнер
4. **Чистые интерфейсы** - без legacy конфликтов и зависимостей
5. **Типизация** - полная поддержка type hints

## 📂 Структура проекта

```
aisha_v2/
├── alembic/                    # Миграции базы данных
│   ├── versions/               # Файлы миграций
│   ├── env.py                  # Конфигурация Alembic
│   └── alembic.ini             # Настройки Alembic
├── app/                        # Основное приложение
│   ├── core/                   # Ядро системы
│   │   ├── config.py           # Конфигурация
│   │   ├── constants.py        # Константы
│   │   ├── di.py               # Dependency Injection
│   │   ├── exceptions.py       # Кастомные исключения
│   │   └── logger.py           # Логирование
│   ├── database/               # Слой данных
│   │   ├── models/             # SQLAlchemy модели
│   │   │   ├── __init__.py     # Экспорты моделей
│   │   │   ├── base.py         # Базовая модель
│   │   │   ├── user.py         # Модель пользователя
│   │   │   ├── avatar.py       # Модель аватара (42 поля + FAL AI)
│   │   │   └── transcript.py   # Модель транскрипта
│   │   └── repositories/       # Паттерн Repository
│   │       ├── base.py         # Базовый репозиторий
│   │       ├── user.py         # Репозиторий пользователей
│   │       ├── avatar.py       # Репозиторий аватаров
│   │       └── transcript.py   # Репозиторий транскриптов
│   ├── handlers/               # Обработчики команд бота (МОДУЛЬНАЯ СТРУКТУРА)
│   │   ├── __init__.py         # Главный роутер
│   │   ├── main_menu.py        # Главное меню
│   │   ├── fallback.py         # Fallback обработчики
│   │   ├── avatar/             # Модуль аватаров
│   │   │   ├── __init__.py     # Роутер аватаров
│   │   │   ├── main.py         # AvatarMainHandler
│   │   │   ├── create.py       # Создание аватаров
│   │   │   └── training_type_selection.py  # Выбор типа обучения
│   │   ├── gallery/            # Модуль галереи
│   │   │   └── __init__.py     # Обработчики галереи
│   │   └── transcript/         # Модуль транскрипции
│   │       ├── main.py         # Основные обработчики
│   │       └── processing.py   # Обработка файлов
│   ├── keyboards/              # Клавиатуры Telegram
│   │   ├── main.py             # Главное меню
│   │   ├── avatar.py           # Клавиатуры аватаров
│   │   ├── gallery.py          # Клавиатуры галереи
│   │   └── transcript.py       # Клавиатуры транскрипции
│   ├── services/               # Бизнес-логика
│   │   ├── user.py             # Сервис пользователей
│   │   ├── avatar/             # Сервисы аватаров
│   │   │   ├── avatar_service.py        # Основной сервис
│   │   │   ├── photo_upload_service.py  # Загрузка фото
│   │   │   └── fal_training_service.py  # FAL AI обучение
│   │   ├── transcript/         # Сервисы транскрипции
│   │   │   ├── transcript_service.py    # Основной сервис
│   │   │   ├── audio_processing.py      # Обработка аудио
│   │   │   └── text_processing.py       # Обработка текста
│   │   ├── fal/                # FAL AI интеграция
│   │   │   ├── fal_client.py           # FAL AI клиент
│   │   │   └── webhook_handler.py      # Webhook обработка
│   │   └── storage/            # Файловое хранилище
│   │       └── minio_service.py        # MinIO интеграция
│   ├── texts/                  # Тексты UI
│   │   ├── avatar.py           # Тексты аватаров
│   │   ├── transcript.py       # Тексты транскрипции
│   │   └── common.py           # Общие тексты
│   └── utils/                  # Утилиты
│       ├── file_utils.py       # Работа с файлами
│       ├── validation.py       # Валидация
│       └── helpers.py          # Вспомогательные функции
├── docs/                       # Документация
├── scripts/                    # Инструменты разработки
│   ├── check_migration_sync.py         # Диагностика Alembic
│   ├── reset_migrations.py             # Очистка миграций
│   ├── diagnose_alembic_env.py         # Диагностика окружения
│   ├── force_apply_migration.py        # Принудительное применение
│   └── migration_diagnosis_report.py   # Отчеты миграций
├── storage/                    # Локальное хранилище
└── tests/                      # Тестирование
    ├── test_database_schema.py         # Валидация схемы БД (9 тестов)
    ├── conftest.py                     # Конфигурация pytest
    └── pytest.ini                     # Настройки asyncio
```

## 🔄 Слои архитектуры

### 1. Presentation Layer (Слой представления)
**Компоненты:** `handlers/`, `keyboards/`, `texts/`

**Ответственность:**
- Обработка команд пользователей
- Формирование ответов и клавиатур
- Управление состояниями (FSM)
- Валидация входных данных

**Новая модульная структура handlers:**
```python
# Чистая архитектура без legacy конфликтов
from app.handlers.avatar import avatar_main_handler
await avatar_main_handler.show_avatar_menu(callback, state)
```

### 2. Business Logic Layer (Слой бизнес-логики)
**Компоненты:** `services/`

**Ответственность:**
- Реализация бизнес-правил
- Координация между компонентами
- Внешние интеграции (FAL AI, OpenAI)
- Обработка файлов и медиа

**Ключевые сервисы:**
- `AvatarService` - управление аватарами
- `FALTrainingService` - обучение через FAL AI
- `TranscriptService` - обработка транскриптов

### 3. Data Access Layer (Слой доступа к данным)
**Компоненты:** `database/repositories/`

**Ответственность:**
- Абстракция над базой данных
- CRUD операции
- Оптимизация запросов
- Управление транзакциями

### 4. Infrastructure Layer (Инфраструктурный слой)
**Компоненты:** `core/`, `utils/`, внешние сервисы

**Ответственность:**
- Конфигурация приложения
- Логирование и мониторинг
- Интеграция с внешними сервисами
- Утилиты и вспомогательные функции

## 🗄️ Модель данных

### Avatar Model (Enhanced with FAL AI)
**42 поля всего, включая 18 FAL AI полей:**

```python
class Avatar(Base):
    # Основные поля (24 поля)
    id: int
    user_id: int
    name: str
    gender: AvatarGender
    status: AvatarStatus
    created_at: datetime
    updated_at: datetime
    # ... другие базовые поля
    
    # FAL AI поля (18 полей)
    training_type: Optional[AvatarTrainingType]    # portrait, style, object
    fal_request_id: Optional[str]                 # ID в FAL AI
    learning_rate: Optional[float]                # Скорость обучения
    trigger_phrase: Optional[str]                 # Ключевая фраза
    steps: Optional[int]                          # Шаги обучения
    multiresolution_training: Optional[bool]      # Мультиразрешение
    subject_crop: Optional[bool]                  # Кроп субъекта
    create_masks: Optional[bool]                  # Создание масок
    captioning: Optional[bool]                    # Автоподписи
    finetune_type: Optional[FALFinetuneType]      # lora, dreambooth
    finetune_comment: Optional[str]               # Комментарий
    diffusers_lora_file_url: Optional[str]        # URL LoRA файла
    config_file_url: Optional[str]                # URL конфига
    training_logs: Optional[str]                  # Логи обучения
    training_error: Optional[str]                 # Ошибки
    webhook_url: Optional[str]                    # URL webhook
    last_status_check: Optional[datetime]         # Последняя проверка
    fal_response_data: Optional[dict]             # Полный ответ FAL AI
```

### Enum Types (NEW)
```python
class AvatarTrainingType(str, Enum):
    PORTRAIT = "portrait"  # Портретное обучение
    STYLE = "style"        # Художественное обучение  
    OBJECT = "object"      # Обучение объектов

class FALFinetuneType(str, Enum):
    LORA = "lora"          # LoRA fine-tuning
    DREAMBOOTH = "dreambooth"  # DreamBooth

class FALPriority(str, Enum):
    NORMAL = "normal"      # Обычный приоритет
    HIGH = "high"          # Высокий приоритет
```

### Database Indexes (NEW)
```sql
-- Оптимизация для FAL AI запросов
CREATE INDEX ix_avatars_fal_request_id ON avatars(fal_request_id);
CREATE INDEX ix_avatars_training_type ON avatars(training_type);
```

## 🔧 Dependency Injection

### DI Container
```python
# app/core/di.py
class DIContainer:
    async def get_user_service() -> UserService:
        """Получить сервис пользователей"""
        
    async def get_avatar_service() -> AvatarService:
        """Получить сервис аватаров"""
        
    async def get_fal_training_service() -> FALTrainingService:
        """Получить сервис FAL AI обучения"""
```

### Использование в handlers
```python
# Современный подход без legacy зависимостей
async def show_avatar_menu(self, callback: CallbackQuery, state: FSMContext):
    async with get_user_service() as user_service:
        user = await user_service.get_user_by_telegram_id(callback.from_user.id)
    
    async with get_avatar_service() as avatar_service:
        avatars = await avatar_service.get_user_avatars(user.id)
```

## 🎯 Конфигурация

### Environment Variables
```python
# Базовые настройки
TELEGRAM_TOKEN: str
DATABASE_URL: str
REDIS_URL: str

# FAL AI интеграция
FAL_API_KEY: str
FAL_TRAINING_TEST_MODE: bool = True
FAL_WEBHOOK_URL: Optional[str]
FAL_DEFAULT_MODE: str = "character"

# MinIO хранилище
MINIO_ENDPOINT: str
MINIO_ACCESS_KEY: str
MINIO_SECRET_KEY: str
MINIO_BUCKET_AVATARS: str = "aisha-v2-avatars"

# Лимиты
AVATAR_MIN_PHOTOS: int = 10
AVATAR_MAX_PHOTOS: int = 20
PHOTO_MAX_SIZE: int = 20971520  # 20MB
```

## 🛠️ Технологический стек

### 🗄️ PostgreSQL - Основная база данных
**Версия:** 13+  
**Роль:** Хранение всех структурированных данных

**Конфигурация:**
- **Асинхронные подключения** через `asyncpg`
- **Connection pooling** для оптимизации
- **Миграции** через Alembic
- **Типизированные enum** с `native_enum=False` для совместимости

**Основные таблицы:**
- `users` - пользователи Telegram
- `avatars` - AI-аватары (42 поля включая FAL AI)
- `avatar_photos` - фотографии для обучения
- `image_generations` - сгенерированные изображения
- `user_balances` - баланс пользователей

**Индексы:**
```sql
-- Быстрый поиск аватаров
CREATE INDEX ix_avatars_user_id ON avatars(user_id);
CREATE INDEX ix_avatars_fal_request_id ON avatars(fal_request_id);
CREATE INDEX ix_avatars_status ON avatars(status);

-- Оптимизация поиска фотографий
CREATE INDEX ix_avatar_photos_avatar_id ON avatar_photos(avatar_id);
CREATE INDEX ix_avatar_photos_upload_order ON avatar_photos(upload_order);
```

### 🔄 Redis - Кэширование и состояния
**Версия:** 6+  
**Роль:** Кэширование и управление состояниями

**Использование:**
- **FSM состояния** пользователей (aiogram)
- **Кэш галереи фотографий** (TTL: 10 минут)
- **Сессии пользователей** и временные данные
- **Очереди задач** для фоновой обработки

**Конфигурация Redis:**
```python
# TTL для разных типов данных
GALLERY_CACHE_TTL = 600        # 10 минут
USER_SESSION_TTL = 3600        # 1 час
TEMP_DATA_TTL = 300           # 5 минут

# Ключи Redis
photo_gallery_cache:{user_id}  # Кэш галереи фотографий
user_session:{user_id}         # Сессия пользователя
temp_upload:{file_hash}        # Временная загрузка
```

**Очистка кэша:**
```python
# Автоматическая очистка при изменениях
await cache_service.delete(f"avatar_meta:{avatar_id}")
await cache_service.delete(f"user_avatars:{user_id}")
```

### 📁 MinIO - Объектное хранилище
**Версия:** Latest  
**Роль:** Хранение файлов (фотографии, результаты генерации)

**Bucket структура:**
```
aisha-v2-avatars/
├── avatars/
│   └── {user_id}/
│       └── {avatar_id}/
│           ├── photo_1.jpeg
│           ├── photo_2.jpeg
│           └── ...
├── generations/
│   └── {user_id}/
│       └── {generation_id}/
│           ├── result_1.png
│           ├── result_2.png
│           └── ...
└── temp/
    └── {upload_id}/
        └── temp_file.jpeg
```

**Конфигурация MinIO:**
```python
# Настройки хранилища
MINIO_ENDPOINT: str = "192.168.0.4:9000"
MINIO_ACCESS_KEY: str = "minioadmin"
MINIO_SECRET_KEY: str = "minioadmin"
MINIO_BUCKET_AVATARS: str = "aisha-v2-avatars"

# Лимиты файлов
PHOTO_MAX_SIZE: int = 20971520  # 20MB
ALLOWED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']
MIN_RESOLUTION = (512, 512)
MAX_RESOLUTION = (4096, 4096)
```

**Операции с файлами:**
```python
# Загрузка фото
storage = StorageService()
minio_key = await storage.upload_file(
    bucket="avatars",
    object_name=f"avatars/{user_id}/{avatar_id}/photo_{order}.jpeg",
    file_data=photo_bytes,
    content_type="image/jpeg"
)

# Скачивание
file_data = await storage.download_file("avatars", minio_key)
```

**Безопасность и управление:**
- **Версионирование** файлов через timestamp
- **Автоочистка** временных файлов (TTL: 1 час)
- **Проверка типов файлов** и размеров
- **Уникальные пути** для избежания конфликтов

## 📊 Миграции и версионирование

### Alembic Configuration
- **Текущая версия:** `5088361401fe`
- **Статус:** ✅ Все миграции применены
- **Синхронизация:** 0 критических проблем

### Диагностические инструменты
1. **`check_migration_sync.py`** - проверка синхронизации
2. **`reset_migrations.py`** - очистка и восстановление
3. **`force_apply_migration.py`** - принудительное применение
4. **`diagnose_alembic_env.py`** - диагностика окружения
5. **`migration_diagnosis_report.py`** - отчеты

## 🧪 Тестирование

### Test Infrastructure  
```python
# pytest.ini - конфигурация asyncio
[tool:pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### Database Schema Tests (9 tests)
```python
# tests/test_database_schema.py
def test_avatar_fal_fields_count():
    """Проверяет количество FAL AI полей (18)"""
    
def test_avatar_enum_types():
    """Проверяет enum типы FAL AI"""
    
def test_avatar_indexes():
    """Проверяет индексы для FAL AI полей"""
```

## 🔄 Workflow разработки

### 1. Создание новой функциональности
```python
# 1. Создать/обновить модель данных
class NewModel(Base):
    pass

# 2. Создать миграцию
alembic revision --autogenerate -m "Add new model"

# 3. Применить миграцию  
alembic upgrade head

# 4. Создать repository
class NewRepository(BaseRepository[NewModel]):
    pass

# 5. Создать service
class NewService:
    def __init__(self, repo: NewRepository):
        self.repo = repo

# 6. Создать handlers
@router.callback_query(F.data == "new_action")
async def handle_new_action(callback: CallbackQuery):
    pass

# 7. Написать тесты
def test_new_functionality():
    pass
```

### 2. Обновление существующей функциональности
```python
# 1. Диагностика (если нужно)
python scripts/check_migration_sync.py

# 2. Обновление
# ... внесение изменений

# 3. Тестирование
pytest tests/

# 4. Миграция (если нужно)
alembic upgrade head
```

## 🚀 Производительность

### Оптимизации базы данных
- **Индексы на FAL AI поля** - быстрый поиск по fal_request_id и training_type
- **select_related/joinedload** - оптимизация N+1 запросов  
- **Асинхронные запросы** - все операции БД неблокирующие

### Кэширование
- **Redis** - кэширование состояний пользователей
- **Буферизация фото** - групповая загрузка в MinIO
- **Мемоизация** - кэширование результатов сервисов

### Асинхронность
- **aiogram 3.x** - полностью асинхронный Telegram bot
- **SQLAlchemy async** - неблокирующие операции БД
- **httpx** - асинхронные HTTP запросы к FAL AI
- **aiofiles** - неблокирующая работа с файлами

## 🔒 Безопасность

### Управление секретами
- Все API ключи через переменные окружения
- Валидация входных данных в handlers
- Ограничения размера файлов и форматов
- Изоляция пользовательских данных

### Валидация
```python
# Валидация загружаемых фото
max_size = settings.PHOTO_MAX_SIZE  # 20MB
allowed_formats = ['.jpg', '.jpeg', '.png']
min_resolution = (512, 512)
```

## 📈 Мониторинг и логирование

### Структурированное логирование
```python
# app/core/logger.py
logger.info(
    "Avatar created",
    extra={
        "user_id": user.id,
        "avatar_id": avatar.id,
        "training_type": avatar.training_type,
        "photos_count": len(photos)
    }
)
```

### Метрики
- Время выполнения операций
- Количество ошибок по типам
- Использование ресурсов
- Статистика FAL AI запросов

## 🎯 Архитектурные решения

### 1. Модульная структура handlers
**Проблема:** Конфликты импортов между `avatar.py` и `avatar/`
**Решение:** Полная модуляризация в директории `handlers/avatar/`

### 2. FAL AI интеграция  
**Проблема:** 18 дополнительных полей в модели Avatar
**Решение:** Расширение модели с сохранением обратной совместимости

### 3. Миграции Alembic
**Проблема:** Autogenerate создавал пустые миграции
**Решение:** Создание диагностических инструментов и force migration

### 4. Legacy код
**Проблема:** Устаревшие зависимости замедляли разработку  
**Решение:** Полное удаление legacy с заменой на современные решения

## 🏆 Преимущества архитектуры

### ✅ Достигнутые цели
1. **Модульность** - четкое разделение ответственности
2. **Масштабируемость** - легко добавлять новые компоненты
3. **Тестируемость** - 9 тестов БД, возможность расширения
4. **Поддерживаемость** - чистый код без legacy зависимостей
5. **Производительность** - асинхронность + оптимизация БД

### ✅ Техническое качество
- **Типизация** - полная поддержка type hints
- **Dependency Injection** - управляемые зависимости
- **Clean Architecture** - четкие границы слоев
- **Modern Stack** - современные библиотеки и практики

**Архитектура готова для дальнейшего развития и масштабирования.**

## 🔧 Критические исправления

### ✅ Исправление удаления аватаров (04.06.2025)
**Проблема:** `TelegramBadRequest: there is no text in the message to edit`
**Файл:** `app/handlers/avatar/gallery/avatar_actions.py`

**Корневая причина:**
- Попытка редактировать текст сообщения с фото через `edit_text`
- Telegram API не позволяет такие операции

**Решение:**
```python
# Проверка типа сообщения и правильная обработка
if callback.message.photo:
    # Удаляем сообщение с фото + отправляем новое текстовое
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=keyboard)
else:
    # Обычное редактирование текстового сообщения
    await callback.message.edit_text(text, reply_markup=keyboard)
```

**Результат:**
- ✅ Устранена ошибка TelegramBadRequest
- ✅ Плавное удаление аватаров из галереи
- ✅ Многоуровневая обработка ошибок Markdown
- ✅ Информативное подтверждение с количеством удаляемых фото

### ✅ Исправление точного удаления фото (04.06.2025)  
**Проблема:** Удалялись неправильные фотографии
**Решение:** Использование photo_id вместо позиции + двойная верификация

### ✅ Исправление навигации "К загрузке" (04.06.2025)
**Проблема:** `TypeError: UUID(None)` при потере состояния
**Решение:** Fallback на кэш галереи + graceful degradation

### ✅ Исправление enum совместимости (04.06.2025)
**Проблема:** Конфликт uppercase/lowercase enum значений
**Решение:** Миграция PostgreSQL enum + данных на uppercase

### ✅ Новая кнопка "Продолжить" для черновиков (04.06.2025)
**Функция:** Замена кнопки "📸 Фото" на "🔄 Продолжить" для лучшего UX
**Файлы:** `app/handlers/avatar/gallery/keyboards.py`, `app/handlers/avatar/gallery/main_handler.py`

**Изменения:**
- Заменена кнопка "📸 Фото" → "🔄 Продолжить" для черновиков
- Добавлен обработчик `handle_continue_avatar_creation()`
- Восстановление контекста аватара из БД для продолжения создания
- Безопасная валидация принадлежности и статуса аватара

**Результат:**
- ✅ Более понятный UX для продолжения создания аватаров
- ✅ Корректное восстановление контекста из базы данных
- ✅ Безопасность и валидация всех параметров
- ✅ Совместимость с существующей логикой загрузки

## 📚 Связанная документация

- `docs/development/AVATAR_DELETE_PHOTO_MESSAGE_FIX.md` - Детали исправления удаления
- `docs/development/BACK_TO_UPLOAD_FIX.md` - Исправление навигации  
- `docs/development/PHOTO_DELETE_ACCURACY_FIX.md` - Точное удаление фото
- `docs/development/ENUM_ISSUES_RESOLVED.md` - Enum совместимость
- `docs/development/AVATAR_CONTINUE_BUTTON_FEATURE.md` - Новая кнопка "Продолжить"
- `docs/DOCUMENTATION_CLEANUP_REPORT.md` - Очистка документации

## 🆕 Восстановление inline меню транскрипции (07.06.2025)

### ✅ Проблема
После внедрения платных транскриптов пропали inline кнопки для обработки результатов:
- 📝 Краткое содержание
- ✅ Список задач  
- 📊 Протокол

### ✅ Решение
**Восстановлена интеграция с существующим AI форматированием:**

#### 1. Обновлен `PaidTranscriptionHandler`
```python
# Добавлена интеграция с клавиатурами после успешной транскрипции
from app.keyboards.transcript import get_transcript_actions_keyboard

if transcript_id:
    keyboard = get_transcript_actions_keyboard(transcript_id)
    caption = "📄 Полный текст транскрипции\n\n🔧 Выберите действие для обработки:"
```

#### 2. Обновлен `PaidTranscriptionService`
```python
# Добавлен возврат transcript_id для создания кнопок
return {
    "success": True,
    "transcript_id": saved_transcript.get("id") if saved_transcript else None,
    "text": transcription_result.text,
    # ...
}
```

#### 3. Архитектура inline обработки
```
User sends audio (>1 min) → PaidTranscriptionHandler
                          ↓
Shows quote + payment → User pays → Transcription  
                    ↓
Result with inline buttons → User clicks action
                          ↓
TranscriptProcessingHandler → AIFormatter
                          ↓
OpenAI processing → New formatted transcript saved
```

### ✅ Компоненты системы

#### Обработчики callback'ов
- `transcript_summary_{id}` → Краткое содержание через OpenAI
- `transcript_todo_{id}` → Список задач через OpenAI  
- `transcript_protocol_{id}` → Протокол встречи через OpenAI

#### Используемые сервисы
- `TextProcessingService` - AI форматирование через OpenAI
- `TranscriptService` - сохранение результатов
- `UserService` - проверка прав доступа

#### Интеграция
- ✅ **Клавиатуры** - готовые в `keyboards/transcript.py`
- ✅ **Обработчики** - регистрация в `main_handler.py`
- ✅ **AI форматирование** - работает через `ai_formatter.py`
- ✅ **Сохранение результатов** - каждый результат как отдельный транскрипт

### ✅ Результат
- ✅ **Восстановлена функциональность** из архивной версии
- ✅ **Интегрировано с платной системой** - кнопки появляются после оплаты
- ✅ **AI обработка через OpenAI** - высокое качество форматирования
- ✅ **Все результаты сохраняются** - доступны в истории пользователя

**Пользователи снова могут обрабатывать транскрипты через удобное inline меню!** 🎉 