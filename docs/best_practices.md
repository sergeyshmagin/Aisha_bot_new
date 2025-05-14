# Best Practices (Лучшие практики)

## 1. Централизация шаблонов, клавиатур и прогресс-баров

- Все шаблоны сообщений, caption, ошибки — только в `frontend_bot/texts/`.
- Все генераторы клавиатур (inline/reply) — только в `frontend_bot/keyboards/`.
- Все прогресс-бары и shared-утилиты — только в `frontend_bot/shared/`.
- Не допускается дублирование шаблонов и клавиатур в хендлерах или сервисах.

**Пример:**
```python
# texts/common.py
ERROR_NO_PHOTOS = "Нет фото для отображения. Пожалуйста, загрузите хотя бы одно фото."

def get_gallery_caption(idx: int, total: int) -> str:
    ...

# keyboards/common.py
def get_gallery_keyboard(idx: int, total: int) -> InlineKeyboardMarkup:
    ...
```

## 2. Асинхронность

- Все операции с файлами — только через `aiofiles` и асинхронные аналоги.
- Внешние процессы (ffmpeg, docx) — только через `asyncio.create_subprocess_exec`.
- Не использовать `open()`, `os.remove()`, `os.path.exists()` напрямую в async-коде.
- **Если появляется новая sync-функция, обязательно проверять, чтобы её не вызывали с await.**

**Пример:**
```python
import aiofiles
async with aiofiles.open(path, "rb") as f:
    data = await f.read()
```

## 3. Docstring и аннотации типов

- Все публичные функции и классы должны иметь docstring с кратким описанием назначения, параметров и возвращаемого значения.
- Использовать аннотации типов для всех параметров и возвращаемых значений.

**Пример:**
```python
def get_gallery_caption(idx: int, total: int) -> str:
    """
    Генерирует caption для галереи фото.
    :param idx: Индекс текущего фото.
    :param total: Общее количество фото.
    :return: Строка caption.
    """
    ...
```

## 4. Расширение shared-модулей

- При добавлении нового шаблона/клавиатуры/утилиты — добавлять только в соответствующий shared-модуль.
- Не создавать локальные копии или дублирующие функции.

**Пример добавления шаблона:**
```python
# texts/common.py
NEW_FEATURE_TEXT = "Текст для новой фичи..."
```

**Пример добавления клавиатуры:**
```python
# keyboards/common.py
def new_feature_keyboard() -> InlineKeyboardMarkup:
    ...
```

## 5. Приоритеты рефакторинга (Code Review v2)

### Критичные нарушения
```python
# services/transcribe.py (line 45)
with open(temp_file, 'rb') as f:  # Нарушение: синхронное чтение

# handlers/avatar.py (line 31)
os.remove(temp_path)  # Нарушение: синхронное удаление
```

### План исправлений
1. **Унификация файловых операций**  
Создать `shared/file_operations.py` с async-менеджером:
```python
class AsyncFileManager:
    @staticmethod
    async def safe_remove(path: Path) -> None:
        try:
            await aiofiles.os.remove(str(path))
        except FileNotFoundError:
            logger.warning(f"File {path} not found")
```

2. **Тестирование асинхронности**  
Добавить интеграционные тесты:
```python
async def test_async_remove():
    test_file = Path("test.tmp")
    test_file.touch()
    await AsyncFileManager.safe_remove(test_file)
    assert not await aiofiles.os.path.exists(test_file)
```

## 6. Этапы рефакторинга (из Code Review v2)
| Этап           | Срок   | Связь с практиками      |
|----------------|--------|-------------------------|
| Рефакторинг IO | 1 нед  | §2.1, §5.1              |
| Тесты безопасности | 3 дня | §3.1, §5.2          |

## 7. Примеры использования

- Примеры запуска, настройки и расширения — в `README.md` и `docs/quickstart.md`.
- Примеры добавления новых shared-компонентов — в этом файле.

## Best practices: тестирование и покрытие

- Покрывать все публичные сервисные функции и edge-cases (пустой файл, пустой ответ GPT, отсутствие файла, исключения).
- Для каждого перехода FSM и возврата в меню — отдельный тест.
- Все ошибки должны быть снабжены user-friendly сообщением (assert с пояснением).
- Использовать только async-compatible моки и фикстуры (AsyncMock, patch).
- Все фикстуры (user_transcripts, fake_user_id, fake_txt_file) — в conftest.py.
- Пример структуры теста:

```python
@pytest.mark.asyncio
@patch("frontend_bot.handlers.transcribe_protocol.bot.send_message", new_callable=AsyncMock)
async def test_some_case(mock_send_message, fake_user_id):
    ...
    assert "ожидаемый текст" in args[1], (
        "❌ User-friendly сообщение об ошибке"
    )
```
- Не дублировать тесты между файлами, каждый блок — свой файл.
- Для моков Telebot и GPT — только async-совместимые моки.
- Состояние очищается через autouse-фикстуру.

## 8. Smoke-тесты для протоколов (MoM, summary, todo, Word)

- В smoke-тестах для протоколов проверять только факт отправки файла (или сообщения об ошибке) и что файл не пустой.
- Не завязываться на конкретный текст в файле или сообщении — это делает тесты устойчивыми к изменению шаблонов и GPT-ответов.
- Для моков файловых операций использовать только async-compatible моки (AsyncMock, patch, собственные async-контекстные менеджеры).
- Если требуется мокать aiofiles.open, делать это только внутри области теста, чтобы не ломать работу других сервисов.

**Пример:**
```python
from unittest.mock import patch
class AsyncFile:
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc, tb): pass
    async def read(self): return "not empty"
with patch("aiofiles.open", return_value=AsyncFile()):
    await my_async_func()
```

## Тестирование переходов между меню

### Общие принципы

1. Каждый тест должен быть независимым
   - Использовать фикстуры для создания чистого состояния
   - Очищать состояние после каждого теста
   - Не полагаться на результаты других тестов

2. Моки и фикстуры
   ```python
   @pytest.fixture
   async def clean_state():
       # Очищаем состояние перед каждым тестом
       await clear_all_states()
       yield
       # Очищаем после теста
       await clear_all_states()
   
   @pytest.fixture
   def mock_bot():
       with patch('frontend_bot.bot.bot') as mock:
           yield mock
   ```

3. Структура тестов переходов
   ```python
   @pytest.mark.asyncio
   async def test_main_menu_to_ai_photographer(clean_state, mock_bot):
       # Arrange
       user_id = 123456789
       message = create_message(user_id, "🧑‍🎨 ИИ фотограф")
   
       # Act
       await handle_main_menu(message)
   
       # Assert
       mock_bot.send_message.assert_called_once()
       args = mock_bot.send_message.call_args[0]
       assert args[0] == user_id  # chat_id
       assert "Выберите действие" in args[1]  # message text
       # Проверяем клавиатуру
       keyboard = mock_bot.send_message.call_args[1]['reply_markup']
       assert "📷 Создать аватар" in str(keyboard)
       # Проверяем состояние
       state = await get_state(user_id)
       assert state == "ai_photographer"
   ```

### Чек-лист для тестов переходов

1. Подготовка
   - [ ] Очистка состояния
   - [ ] Создание тестовых данных
   - [ ] Настройка моков

2. Проверка перехода
   - [ ] Корректность нового состояния
   - [ ] Правильность отправленного сообщения
   - [ ] Наличие всех кнопок в клавиатуре
   - [ ] Очистка старого состояния

3. Проверка данных
   - [ ] Сохранение необходимых данных
   - [ ] Очистка ненужных данных
   - [ ] Корректность метаданных

### Примеры тестов для основных переходов

```python
# tests/handlers/test_menu_transitions.py

import pytest
from unittest.mock import patch, AsyncMock
from frontend_bot.handlers.start import handle_start
from frontend_bot.services.state_manager import get_state, clear_all_states

@pytest.fixture
def create_message():
    def _create_message(user_id, text):
        message = AsyncMock()
        message.from_user.id = user_id
        message.chat.id = user_id
        message.text = text
        return message
    return _create_message

@pytest.mark.asyncio
async def test_start_to_main_menu(clean_state, mock_bot, create_message):
    # Arrange
    user_id = 123456789
    message = create_message(user_id, "/start")

    # Act
    await handle_start(message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    assert "Добро пожаловать" in args[1]
    keyboard = mock_bot.send_message.call_args[1]['reply_markup']
    assert "🧑‍🎨 ИИ фотограф" in str(keyboard)
    state = await get_state(user_id)
    assert state == "main_menu"
```

### Тестирование обработки ошибок

1. Проверка некорректных переходов
   ```python
   @pytest.mark.asyncio
   async def test_invalid_state_transition(clean_state, mock_bot, create_message):
       # Arrange
       user_id = 123456789
       await set_state(user_id, "invalid_state")
       message = create_message(user_id, "🧑‍🎨 ИИ фотограф")

       # Act
       await handle_main_menu(message)

       # Assert
       mock_bot.send_message.assert_called_once_with(
           user_id,
           "Что-то пошло не так. Возвращаемся в главное меню...",
           reply_markup=main_menu_keyboard()
       )
       state = await get_state(user_id)
       assert state == "main_menu"
   ```

2. Проверка таймаутов и очистки состояния
   ```python
   @pytest.mark.asyncio
   async def test_state_timeout(clean_state, mock_bot, create_message):
       # Arrange
       user_id = 123456789
       await set_state(user_id, "avatar_photo_upload", timeout=0)
       message = create_message(user_id, "Любой текст")

       # Act
       await handle_message(message)

       # Assert
       mock_bot.send_message.assert_called_once_with(
           user_id,
           "Время сессии истекло. Начните сначала.",
           reply_markup=main_menu_keyboard()
       )
       state = await get_state(user_id)
       assert state == "main_menu"
   ```

### Документирование тестов

1. Каждый тест должен иметь документацию:
   ```python
   @pytest.mark.asyncio
   async def test_avatar_creation_flow(clean_state, mock_bot, create_message):
       """
       Тест полного flow создания аватара:
       1. Переход к загрузке фото
       2. Загрузка фото
       3. Выбор пола
       4. Ввод имени
       5. Подтверждение
       
       Проверяет:
       - Корректность переходов между состояниями
       - Сохранение данных между шагами
       - Финальное сохранение аватара
       """
   ```

2. Обновлять документацию при изменении тестов
3. Указывать причины пропуска тестов (skip/xfail) 