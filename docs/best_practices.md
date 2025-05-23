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

---

**См. также:**
- docs/architecture.md — архитектурные паттерны
- docs/async_and_safety.md — best practices по async Python 