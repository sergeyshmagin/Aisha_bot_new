# Лучшие практики

## 1. Структура проекта и организация кода

### 1.1 Модульная структура
- Каждый модуль в отдельной директории с `__init__.py`
- Сервисы в `services/`, обработчики в `handlers/`
- Утилиты в `utils/`, конфигурация в `core/`
- Модели данных в `models/`

### 1.2 Именование
- Классы: PascalCase (например, `TranscriptService`)
- Методы и переменные: snake_case (например, `process_audio`)
- Константы: UPPER_CASE (например, `MAX_RETRIES`)
- Приватные методы: с префиксом `_` (например, `_handle_audio`)

## 2. Асинхронное программирование

### 2.1 Основные принципы
- Используем `async/await` для всех I/O операций
- Избегаем блокирующих операций в асинхронном коде
- Используем контекстные менеджеры для ресурсов
- Правильно обрабатываем исключения в асинхронном коде

### 2.2 Примеры
```python
# Правильно
async def process_data():
    async with get_session() as session:
        result = await service.process(session)
        return result

# Неправильно
async def process_data():
    session = get_session()  # Блокирующий вызов
    result = service.process(session)  # Синхронный вызов
    return result
```

## 3. Обработка ошибок и логирование

### 3.1 Логирование
- Используем структурированное логирование
- Добавляем контекст к логам (префиксы, ID пользователя)
- Разные уровни для разных типов сообщений
- Логируем все исключения с полным стеком

```python
# Пример правильного логирования
logger.info(f"[AUDIO] Начало обработки для user_id={user_id}")
logger.error(f"[AUDIO] Ошибка обработки: {error}", exc_info=True)
```

### 3.2 Обработка ошибок
- Используем специфические исключения
- Обрабатываем все возможные ошибки
- Предоставляем понятные сообщения пользователю
- Логируем детали ошибок

```python
try:
    result = await process_data()
except ValidationError as e:
    logger.error(f"[VALIDATION] Ошибка валидации: {e}")
    await message.reply("❌ Ошибка в данных")
except DatabaseError as e:
    logger.error(f"[DB] Ошибка БД: {e}")
    await message.reply("❌ Ошибка базы данных")
except Exception as e:
    logger.exception(f"[UNKNOWN] Неизвестная ошибка: {e}")
    await message.reply("❌ Произошла ошибка")
```

## 4. Типизация и валидация данных

### 4.1 Pydantic модели
- Используем Pydantic для валидации данных
- Добавляем описания полей
- Используем Field для дополнительной валидации
- Документируем модели

```python
class TranscriptResult(BaseModel):
    """Модель результата транскрипта"""
    id: str = Field(..., description="Уникальный идентификатор")
    text: str = Field(..., min_length=1, description="Текст транскрипта")
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 4.2 Аннотации типов
- Используем аннотации для всех параметров
- Указываем возвращаемые значения
- Используем Optional для необязательных параметров
- Документируем типы

```python
async def process_audio(
    audio_data: bytes,
    user_id: int,
    options: Optional[Dict[str, Any]] = None
) -> AudioResult:
    """Обработка аудио"""
    pass
```

## 5. Работа с базой данных

### 5.1 Сессии и транзакции
- Используем асинхронные сессии
- Правильно управляем транзакциями
- Закрываем сессии после использования
- Обрабатываем ошибки БД

```python
async with get_session() as session:
    try:
        async with session.begin():
            result = await service.process(session)
            return result
    except SQLAlchemyError as e:
        logger.error(f"[DB] Ошибка: {e}")
        raise
```

### 5.2 Миграции
- Используем Alembic для миграций
- Версионируем миграции
- Тестируем миграции
- Делаем бэкап перед миграцией

### 5.3 Правильное наследование от BaseService ⚠️

**КРИТИЧЕСКИ ВАЖНО**: При создании сервисов, наследующихся от `BaseService`, обязательно передавайте `session` в конструктор базового класса.

#### ❌ НЕПРАВИЛЬНО:
```python
class MyService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__()  # ❌ ОШИБКА: missing session
        self.session = session
```

#### ✅ ПРАВИЛЬНО:
```python
class MyService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)  # ✅ Передаем session
        self.session = session
```

#### Правила для BaseService:
1. **Все сервисы, работающие с БД** - наследуются от `BaseService`
2. **Утилитарные классы** (клиенты API, помощники) - НЕ наследуются от `BaseService`
3. **Всегда передавайте session** в `super().__init__(session)`
4. **Тестируйте создание сервисов** в unit-тестах

#### Примеры классификации:
```python
# ✅ Наследуется от BaseService (работает с БД)
class UserService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

class AvatarService(BaseService): 
    def __init__(self, session: AsyncSession):
        super().__init__(session)

# ✅ НЕ наследуется от BaseService (утилитарный класс)
class FalAIClient:
    def __init__(self):
        self.logger = get_logger(__name__)

class EmailSender:
    def __init__(self):
        self.smtp_config = get_smtp_config()
```

#### Проверка в тестах:
```python
def test_service_creation():
    """Проверяет что сервис создается без ошибок"""
    session = Mock(spec=AsyncSession)
    
    # Это должно работать без ошибок
    service = MyService(session)
    assert service.session is session
```

#### Частые ошибки:
- `super().__init__()` без session → `TypeError: missing positional argument`
- Наследование от BaseService для API клиентов → Лишняя зависимость
- Забытое наследование для DB сервисов → Отсутствие базовой функциональности

## 6. Безопасность

### 6.1 Конфиденциальные данные
- Храним секреты в переменных окружения
- Не логируем чувствительные данные
- Используем безопасные соединения
- Валидируем входные данные

### 6.2 Аутентификация и авторизация
- Проверяем права доступа
- Используем токены
- Защищаем API endpoints
- Логируем попытки доступа

## 7. Тестирование

### 7.1 Unit-тесты
- Покрываем код тестами
- Используем фикстуры
- Мокаем внешние зависимости
- Тестируем граничные случаи

### 7.2 Интеграционные тесты
- Тестируем взаимодействие компонентов
- Проверяем работу с БД
- Тестируем API endpoints
- Проверяем обработку ошибок

## 8. Документация

### 8.1 Docstrings
- Документируем все публичные методы
- Описываем параметры и возвращаемые значения
- Добавляем примеры использования
- Обновляем документацию при изменениях

### 8.2 README и документация
- Поддерживаем актуальность README
- Документируем архитектуру
- Описываем процесс развертывания
- Добавляем примеры конфигурации

## 9. Оптимизация

### 9.1 Производительность
- Используем кэширование
- Оптимизируем запросы к БД
- Минимизируем сетевые запросы
- Используем пулы соединений

### 9.2 Ресурсы
- Освобождаем ресурсы
- Используем контекстные менеджеры
- Контролируем использование памяти
- Мониторим производительность

## 10. CI/CD

### 10.1 Автоматизация
- Настраиваем CI/CD пайплайны
- Автоматизируем тесты
- Проверяем качество кода
- Автоматизируем деплой

### 10.2 Мониторинг
- Настраиваем логирование
- Мониторим ошибки
- Отслеживаем метрики
- Настраиваем алерты

## UX/UI Паттерны

### Главное меню и навигация

1. **Inline-меню**
   - Используем только InlineKeyboardMarkup
   - Каждая кнопка на отдельной строке для лучшей читаемости
   - Эмодзи для визуального разделения
   - Callback data в формате "section_action"

2. **Регистрация пользователя**
   - При /start проверяем наличие пользователя
   - Создаем нового пользователя если не найден
   - Логируем создание пользователя
   - Обрабатываем ошибки с информативными сообщениями

3. **Переходы между меню**
   - Используем edit_message_text вместо новых сообщений
   - Всплывающие подсказки для подтверждений
   - Краткие уведомления о переходе
   - Возврат в главное меню через /start

4. **Обработка ошибок**
   - Логируем все исключения
   - Пользователю показываем понятные сообщения
   - Предлагаем действия при ошибках

### Примеры кода

```python
# Главное меню (актуальный пример)
def get_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🎤 Транскрибация", callback_data="transcribe_menu")],
        [InlineKeyboardButton("🖼 Галерея", callback_data="business_gallery")],
        [InlineKeyboardButton("🧑‍🎨 Аватары", callback_data="business_avatar")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ])

# Регистрация пользователя
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    try:
        async with get_user_service() as user_service:
            user = await user_service.get_user_by_telegram_id(message.from_user.id)
            if not user:
                user = await user_service.create_user(...)
                logger.info(f"Создан новый пользователь: {user.telegram_id}")
            await message.answer("👋 Добро пожаловать!", reply_markup=get_main_menu())
    except Exception as e:
        logger.exception("Ошибка при регистрации")
        await message.answer("❌ Произошла ошибка...")

# Переход между меню
# @router.callback_query(F.data == "business_menu")  # LEGACY
# async def show_business_menu(call: CallbackQuery):
#     await call.answer("🔄 Переход...", show_alert=False)
#     await call.message.edit_text(
#         "🤖 Бизнес-ассистент",
#         reply_markup=get_business_menu()
#     )

# Сценарий транскрибации
@router.callback_query(F.data == "transcribe_menu")
async def show_transcribe_menu(call: CallbackQuery, state: FSMContext):
    """
    Показывает меню транскрибации (обработка аудио и текста).
    """
    from aisha_v2.app.handlers.transcript_main import TranscriptMainHandler
    handler = TranscriptMainHandler()
    await handler._handle_transcribe_command(call.message, state)

# FSM состояния и обработка
class TranscribeStates(StatesGroup):
    menu = State()
    waiting_audio = State()
    waiting_text = State()
    processing = State()
    result = State()
    format_selection = State()
    error = State()

# Пример обработки аудио и .txt через TranscriptProcessingHandler см. в aisha_v2/app/handlers/transcript_processing.py

## Best practices: сервисы, интеграции и асинхронность

### 1. Вынесение headers и повторяющихся частей
- Все повторяющиеся headers для внешних API (OpenAI, Backend и др.) выносить в shared/utils/openai.py, shared/utils/backend.py и т.д.
- Использовать функции-утилиты для формирования headers:

```python
from aisha_v2.app.shared.utils.openai import get_openai_headers
headers = get_openai_headers(settings.OPENAI_API_KEY)

from aisha_v2.app.shared.utils.backend import get_backend_headers
headers = get_backend_headers(settings.BACKEND_API_KEY)
```

### 2. Асинхронная работа с MinIO
- Все операции с MinIO (загрузка, скачивание, удаление, presigned URL) — только через асинхронный StorageService.
- Прямое создание клиента Minio и sync-операции запрещены.

```python
async with StorageService() as storage:
    await storage.upload_file(bucket, file_path, user_id)
    url = await storage.generate_presigned_url(bucket, object_name, expires=3600)
```

### 3. Docstring и аннотации
- Все публичные методы сервисов и утилит должны иметь docstring и аннотации типов.
- Пример:

```python
def get_openai_headers(api_key: str) -> dict:
    """Формирует headers для OpenAI API"""
    ...
```

### 4. Промпты и шаблоны
- Все промпты для LLM и шаблоны сообщений выносить в отдельные модули (например, prompts/ или texts/).

### 5. Исключить sync-операции в async-коде
- Все файловые и сетевые операции — только асинхронные (aiofiles, httpx/aiohttp, StorageService).

## 11. Очистка от Legacy кода

### 11.1 Принципы очистки
- **Удаляем устаревшие файлы** - все файлы помеченные как Legacy
- **Обновляем импорты** - убираем ссылки на удаленные модули
- **Упрощаем архитектуру** - оставляем только актуальные обработчики
- **Документируем изменения** - фиксируем что удалено и почему

### 11.2 Удаленные компоненты
```
Удаленные файлы:
├── handlers/
│   ├── base.py                     # Базовый обработчик (LEGACY)
│   ├── business.py                 # Бизнес-ассистент (LEGACY)
│   ├── menu.py                     # Устаревшее меню (LEGACY)
│   ├── transcript_management.py    # Управление транскриптами (LEGACY)
│   ├── transcript_view.py          # Просмотр транскриптов (LEGACY)
│   └── audio.py                    # Аудио обработчик (LEGACY)
├── services/
│   └── audio/service.py.LEGACY     # Устаревший аудио сервис
├── keyboards/
│   └── business.py                 # Клавиатуры бизнес-ассистента (LEGACY)
```

### 11.3 Современная архитектура
```
Актуальные компоненты:
├── handlers/
│   ├── main.py                     # Главное меню (АКТУАЛЬНО)
│   ├── transcript_main.py          # История транскриптов (АКТУАЛЬНО)
│   └── transcript_processing.py    # Обработка аудио/текста (АКТУАЛЬНО)
├── services/
│   ├── transcript.py               # Управление транскриптами (АКТУАЛЬНО)
│   ├── audio_processing/           # Современная обработка аудио
│   ├── text_processing/            # Обработка текста
│   └── storage/                    # MinIO хранилище
```

### 11.4 Миграция с Legacy
```python
# Было (Legacy)
from aisha_v2.app.handlers.business import BusinessHandler  # Удалено
from aisha_v2.app.handlers.audio import AudioHandler       # Удалено

# Стало (Современно)
from aisha_v2.app.handlers.transcript_main import TranscriptMainHandler
from aisha_v2.app.handlers.transcript_processing import TranscriptProcessingHandler
```

## 12. Современная навигация

### 12.1 Иерархия меню
```
Главное меню приложения
    ↓ transcribe_menu
Меню транскрибации
    ↓ transcribe_history  
История транскриптов
    ↓ transcribe_open_{id}
Карточка транскрипта
```

### 12.2 Callback data конвенции
```python
# Основные действия
"transcribe_menu"           # Вход в меню транскрибации
"transcribe_audio"          # Обработка аудио
"transcribe_text"           # Обработка текста
"transcribe_history"        # История транскриптов

# Навигация
"transcribe_back_to_menu"   # Возврат в меню транскрибации
"back_to_main"              # Возврат в главное меню

# Действия с транскриптами
"transcribe_open_{id}"      # Открыть транскрипт
"transcript_format_{id}_{type}"  # Форматировать транскрипт
"transcribe_history_page_{page}" # Пагинация истории
```

### 12.3 Дружелюбные названия файлов
```python
def _format_friendly_filename(self, transcript_data: dict) -> str:
    """
    Примеры форматирования:
    
    Технические названия:
    "2025-05-21_10-01_file_362.txt" → "📝 Текст (569 сл.) • 23.05 04:32"
    
    Осмысленные названия:
    "Мой документ.txt" → "📝 Мой документ • 23.05 04:32"
    "presentation.mp3" → "🎵 presentation • 23.05 14:15"
    
    Длинные названия:
    "Очень длинное название документа.txt" → "📝 Очень длинное наз... • 23.05 10:30"
    """
```

## 13. Обработка ошибок и UX

### 13.1 Graceful degradation
```python
# Проблема редактирования сообщений с медиа
if call.message.text:
    try:
        await call.message.edit_text(new_text, reply_markup=keyboard)
    except Exception:
        # Fallback на новое сообщение
        await call.message.answer(new_text, reply_markup=keyboard)
else:
    # Сообщение содержит документ/медиа - отправляем новое
    await call.message.answer(new_text, reply_markup=keyboard)
```

### 13.2 Безопасная конвертация типов
```python
# Проблема несовпадения типов user_id
async def get_user_transcripts(self, user_id: Union[int, str, UUID], ...):
    # Поддерживаем разные типы для совместимости
    
# Безопасная конвертация SQLAlchemy объектов
transcript_dict = {
    "id": str(id_attr) if id_attr else None,
    "created_at": created_at_attr.isoformat() if created_at_attr else None,
    "metadata": metadata_attr or {}
}
```

### 13.3 Решение конфликтов импортов
```python
# Проблема: конфликт BaseModel между Aiogram и Pydantic
from aiogram.types import InlineKeyboardButton  # Явный импорт

# Детальное логирование для отладки
logger.info(f"[SEND_HISTORY] InlineKeyboardButton type: {type(InlineKeyboardButton)}")
logger.info(f"[SEND_HISTORY] Создана кнопка: {type(btn)}")
```

---

**Обновлено после удаления Legacy кода 2025-05-23**

**См. также:**
- `docs/architecture.md` - архитектурные паттерны
- `docs/async_and_safety.md` - best practices по async Python
- `docs/navigation_transcript.md` - архитектура навигации 

---

## 14. ✅ Developer Checklist

### 14.1 🚨 Критические правила (ОБЯЗАТЕЛЬНО!)

#### BaseService наследование
- [ ] ✅ **При наследовании от BaseService передавай session**: `super().__init__(session)`
- [ ] ❌ **НЕ используй**: `super().__init__()` без session
- [ ] 🔍 **Проверь тип класса**:
  - Работает с БД? → наследуется от `BaseService`
  - Утилитарный класс (API клиент)? → обычный класс

```python
# ✅ ПРАВИЛЬНО
class MyService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)  # ✅ session передан
        
# ❌ НЕПРАВИЛЬНО  
class MyService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__()  # ❌ TypeError: missing session
```

#### Async/Await 
- [ ] ✅ Все I/O операции через `async/await`
- [ ] ✅ Используй `async with get_session()` для БД
- [ ] ❌ НЕ используй sync функции в async коде

#### Обработка ошибок
- [ ] ✅ Логируй все исключения: `logger.exception()`
- [ ] ✅ Показывай понятные сообщения пользователю
- [ ] ✅ Используй try/except блоки

#### Структура кода
- [ ] ✅ Бизнес-логика → `services/`
- [ ] ✅ Хендлеры → `handlers/` (только маршрутизация)
- [ ] ✅ Тексты → `texts/`
- [ ] ✅ Клавиатуры → `keyboards/`

### 14.2 База данных 🗄️
- [ ] ✅ **Проверяй миграции**: `alembic history` и содержимое файлов
- [ ] ✅ **Не создавай пустые миграции**: всегда проверяй `upgrade()` и `downgrade()`
- [ ] ✅ **Тестируй на тестовой БД**: перед применением на продакшене
- [ ] ✅ **Применяй миграции**: `alembic upgrade head` после создания
- [ ] ❌ **НЕ изменяй модели без миграций**: сначала миграция, потом код

```python
# ✅ ПРАВИЛЬНО - проверка миграции
def upgrade() -> None:
    op.create_table('my_table', ...)  # Реальное содержимое

# ❌ НЕПРАВИЛЬНО - пустая миграция  
def upgrade() -> None:
    pass  # Ничего не делает!
```

### 14.3 🧪 Перед коммитом

#### Базовые проверки
- [ ] ✅ Код запускается без ошибок
- [ ] ✅ Все импорты работают
- [ ] ✅ Тесты проходят (если есть)
- [ ] ✅ Логи понятные и информативные

#### Проверка BaseService (если создавал новые сервисы)
```python
# Быстрый тест
from my_module import MyService
from unittest.mock import Mock
from sqlalchemy.ext.asyncio import AsyncSession

session = Mock(spec=AsyncSession)
service = MyService(session)  # Должно работать без ошибок
print("✅ Сервис создается корректно")
```

### 14.4 🔧 Частые ошибки и решения

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `BaseService.__init__() missing session` | Не передан session в super() | Измени на `super().__init__(session)` |
| `ValidationError: Instance is frozen` | Попытка изменить CallbackQuery.data | Используй прямой вызов методов |
| `ImportError: No module named` | Неправильные импорты | Проверь пути импортов |
| `Session is closed` | Сессия БД закрыта | Используй `async with get_session()` |
| `relation "table" does not exist` | Миграции не применены | Запусти `alembic upgrade head` |
| `DATABASE_URL not configured` | Неправильная конфигурация БД | Проверь .env и validator |

### 14.5 📋 Конфигурация и миграции
- [ ] ✅ **Создан .env файл** с реальными настройками
- [ ] ✅ **DATABASE_URL генерируется автоматически** через validator
- [ ] ✅ **Миграции применены**: `alembic upgrade head`
- [ ] ✅ **Проверена структура БД**: таблицы созданы
- [ ] ✅ **Настроены секреты**: TELEGRAM_TOKEN, API ключи

```python
# Проверка конфигурации
from aisha_v2.app.core.config import settings
print("DATABASE_URL:", settings.DATABASE_URL)
print("TELEGRAM_TOKEN установлен:", bool(settings.TELEGRAM_TOKEN))
```

### 14.6 💡 Советы по отладке

```python
# Логирование для отладки
logger.info(f"[DEBUG] User ID: {user_id}, type: {type(user_id)}")
logger.info(f"[DEBUG] Session: {session}, closed: {session.is_closed if hasattr(session, 'is_closed') else 'unknown'}")

# Проверка BaseService
if isinstance(service, BaseService):
    logger.info(f"[DEBUG] Service session: {service.session}")
```

---

**💡 Запомни**: Большинство ошибок связано с неправильным наследованием BaseService и неприменёнными миграциями. 

**🛠️ При любых проблемах**:
1. Проверь validator и DATABASE_URL
2. Проверь что миграции применены
3. Проверь наследование от BaseService
4. Проверь async/await в I/O операциях