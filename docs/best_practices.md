# Лучшие практики

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
# Главное меню
def get_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🤖 Бизнес-ассистент", callback_data="business_menu")],
        [InlineKeyboardButton("🖼 Галерея", callback_data="business_gallery")],
        [InlineKeyboardButton("🧑‍🎨 Аватары", callback_data="business_avatar")],
        [InlineKeyboardButton("❓ Помощь", callback_data="main_help")]
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
@router.callback_query(F.data == "business_menu")
async def show_business_menu(call: CallbackQuery):
    await call.answer("🔄 Переход...", show_alert=False)
    await call.message.edit_text(
        "🤖 Бизнес-ассистент",
        reply_markup=get_business_menu()
    ) 

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