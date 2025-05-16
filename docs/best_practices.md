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

## 2.1. Строгое правило по await

- **Все вызовы асинхронных функций (coroutine) должны сопровождаться await.**
- Запрещено вызывать async-функции без await — это приводит к ошибкам выполнения, предупреждениям RuntimeWarning и потере задач.
- При code review обязательно проверять, что все вызовы async-функций (например, is_audio_file_ffmpeg, aiofiles.open, convert_to_mp3 и др.) имеют await.
- Исключение: если coroutine передаётся как объект (например, в asyncio.create_task), но не вызывается напрямую.

**Пример (правильно):**
```python
is_audio = await is_audio_file_ffmpeg(temp_file)
```
**Пример (ошибка!):**
```python
is_audio = is_audio_file_ffmpeg(temp_file)  # ОШИБКА: нет await
```

**Чеклист для code review:**
- [ ] Нет вызовов async-функций без await
- [ ] Нет RuntimeWarning: coroutine was never awaited
- [ ] Все асинхронные операции (файлы, процессы, HTTP) вызываются с await

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

### Фикстуры для тестирования аватаров

```python
@pytest.fixture
def mock_bot():
    """Фикстура для мока бота."""
    with patch("frontend_bot.handlers.handlers.bot") as mock:
        mock.send_message = AsyncMock()
        mock.get_file = AsyncMock()
        mock.download_file = AsyncMock()
        yield mock

@pytest.fixture
def mock_avatar_workflow():
    """Фикстура для мока avatar_workflow."""
    with patch("frontend_bot.handlers.handlers.handle_photo_upload") as mock_upload, \
         patch("frontend_bot.handlers.handlers.handle_gender_selection") as mock_gender, \
         patch("frontend_bot.handlers.handlers.handle_name_input") as mock_name, \
         patch("frontend_bot.handlers.handlers.finalize_avatar") as mock_finalize, \
         patch("frontend_bot.handlers.handlers.load_avatar_fsm") as mock_load, \
         patch("frontend_bot.handlers.handlers.cleanup_state") as mock_cleanup:
        
        mock_upload.return_value = AsyncMock()
        mock_gender.return_value = AsyncMock()
        mock_name.return_value = AsyncMock()
        mock_finalize.return_value = AsyncMock()
        mock_load.return_value = {"photos": []}
        mock_cleanup.return_value = AsyncMock()
        
        yield {
            "upload": mock_upload,
            "gender": mock_gender,
            "name": mock_name,
            "finalize": mock_finalize,
            "load": mock_load,
            "cleanup": mock_cleanup,
        }
```

### Пример структуры теста для аватаров

```python
@pytest.mark.asyncio
async def test_handle_avatar_photo_success(mock_bot, mock_avatar_workflow, mock_state_manager):
    """Тест успешной загрузки фото."""
    message, photo_bytes = create_test_photo_message()
    mock_bot.download_file.return_value = photo_bytes
    
    await handle_avatar_photo(message)
    
    mock_avatar_workflow["upload"].assert_called_once()
    mock_bot.send_message.assert_called_once()
    assert "Фото успешно загружено" in mock_bot.send_message.call_args[0][1]
```

### Важные моменты при тестировании аватаров

1. Всегда проверять вызов cleanup_state при ошибках:
```python
@pytest.mark.asyncio
async def test_handle_avatar_photo_validation_error(mock_bot, mock_avatar_workflow, mock_state_manager):
    """Тест ошибки валидации фото."""
    message, photo_bytes = create_test_photo_message()
    mock_bot.download_file.return_value = photo_bytes
    mock_avatar_workflow["upload"].side_effect = PhotoValidationError("Test error")
    
    await handle_avatar_photo(message)
    
    mock_avatar_workflow["cleanup"].assert_called_once_with(123)
```

2. Проверять корректность переходов между состояниями:
```python
@pytest.mark.asyncio
async def test_handle_avatar_photo_next_success(mock_bot, mock_avatar_workflow, mock_state_manager):
    """Тест успешного перехода к следующему шагу."""
    message = next(create_test_text_message("Далее"))
    mock_avatar_workflow["load"].return_value = {"photos": ["photo"] * AVATAR_MIN_PHOTOS}
    
    await handle_avatar_photo_next(message)
    
    mock_bot.send_message.assert_called_once()
    assert "Выберите пол для аватара" in mock_bot.send_message.call_args[0][1]
    mock_state_manager["set"].assert_called_once_with(123, "avatar_gender")
```

3. Проверять валидацию входных данных:
```python
@pytest.mark.asyncio
async def test_handle_avatar_gender_validation_error(mock_bot, mock_avatar_workflow, mock_state_manager):
    """Тест ошибки валидации при выборе пола."""
    message = next(create_test_text_message("Неверный пол", "avatar_gender"))
    mock_avatar_workflow["gender"].side_effect = ValidationError("Test error")
    
    await handle_avatar_gender(message)
    
    mock_avatar_workflow["cleanup"].assert_called_once_with(123)
```

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
from frontend_bot.services.state_utils import get_state, clear_all_states

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

## Тестирование асинхронных функций и моков

### 1. Правила мокирования асинхронных функций

- Всегда использовать `AsyncMock` для мокирования асинхронных функций:
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_async_function():
    mock_func = AsyncMock(return_value="result")
    result = await mock_func()
    assert result == "result"
```

### 2. Проверка сигнатур функций

- Перед написанием теста всегда проверять сигнатуру тестируемой функции:
```python
# Правильно:
async def send_main_menu(bot: AsyncTeleBot, message: Message) -> None:
    ...

# В тесте:
await send_main_menu(mock_bot, message)  # Передаём все аргументы
```

### 3. Фикстуры для общих моков

- Выносить часто используемые моки в фикстуры:
```python
@pytest.fixture
def mock_bot():
    with patch('frontend_bot.bot.bot', new_callable=AsyncMock) as mock:
        yield mock

@pytest.fixture
def mock_message():
    return Message(
        message_id=1,
        date=datetime.now(),
        chat=Chat(id=123, type='private'),
        text='/start'
    )
```

### 4. Проверка вызовов асинхронных функций

- Использовать `assert_called_once_with()` для проверки аргументов:
```python
mock_bot.send_message.assert_called_once_with(
    chat_id=user_id,
    text="Ожидаемый текст",
    reply_markup=ANY
)
```

### 5. Обработка исключений

- Тестировать исключения через `pytest.raises`:
```python
with pytest.raises(ValueError, match="Ожидаемое сообщение об ошибке"):
    await function_that_raises()
```

### 6. Асинхронные контекстные менеджеры

- Для мокирования асинхронных контекстных менеджеров:
```python
class AsyncContextManagerMock:
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.mark.asyncio
async def test_async_context():
    with patch('aiofiles.open', return_value=AsyncContextManagerMock()):
        await async_function()
```

### 7. Проверка состояния

- После каждого теста проверять, что состояние очищено:
```python
@pytest.mark.asyncio
async def test_state_management(clean_state):
    # Arrange
    await set_state(user_id, "some_state")
    
    # Act
    await handle_something()
    
    # Assert
    assert await get_state(user_id) is None
```

### 8. Изоляция тестов

- Каждый тест должен быть полностью изолирован:
  - Свои моки
  - Своё состояние
  - Свои фикстуры
  - Не зависеть от порядка выполнения

### 9. Документирование тестов

- Каждый тест должен иметь понятное описание:
```python
@pytest.mark.asyncio
async def test_send_main_menu_returns_to_main_menu():
    """
    Проверяет, что функция send_main_menu:
    1. Отправляет сообщение с главным меню
    2. Устанавливает правильную клавиатуру
    3. Очищает предыдущее состояние
    """
    # ... код теста ...
```

### 10. Проверка асинхронных операций

- Всегда проверять, что асинхронные операции завершились:
```python
@pytest.mark.asyncio
async def test_async_operation():
    # Arrange
    mock_operation = AsyncMock()
    
    # Act
    await mock_operation()
    
    # Assert
    assert mock_operation.call_count == 1
    assert mock_operation.await_count == 1
```

## Централизованный bot и регистрация хендлеров

- Объект `bot` должен создаваться только в одном месте (например, в `frontend_bot/bot_instance.py`).
- Во всех хендлерах импортируйте bot только из этого файла:
  ```python
  from frontend_bot.bot_instance import bot
  ```
- Не создавайте bot локально в каждом модуле — это приведёт к тому, что хендлеры будут регистрироваться на разные экземпляры и не будут работать.
- Все хендлеры должны импортироваться в точке входа (например, в `main.py`), чтобы гарантировать их регистрацию.
- Запускать polling только на этом экземпляре bot.
- **Дублирование экземпляра бота (например, через bot.py) запрещено!**
- Файл `frontend_bot/bot.py` удалён и не должен использоваться для инициализации или запуска.
- Такой подход предотвращает циклические импорты и обеспечивает корректную маршрутизацию всех сообщений.

## Пример архитектуры запуска

- `frontend_bot/bot_instance.py` — только создание bot.
- `frontend_bot/main.py` — импорт bot, импорт всех хендлеров, запуск polling.
- Все хендлеры используют только импорт bot из bot_instance. 

## DRY для работы с транскриптами
- Все проверки наличия, чтения и ошибок транскрипта выносить в утилиту (например, `get_user_transcript_or_error` в `services/transcript_utils.py`).
- Не дублировать эти блоки в каждом хендлере — используйте общую функцию.
- Это упрощает сопровождение и снижает риск ошибок при изменениях. 

## 9. Отправка файлов и сообщений об ошибке

- Для отправки файлов и сообщений об ошибке используйте shared-утилиты (`send_document_with_caption`, `send_transcript_error` в `services/transcript_utils.py`).
- Не дублируйте вызовы bot.send_document и bot.send_message в каждом хендлере. 

## 1.1. Централизация промтов для GPT

- Все промты для GPT (транскрибация, резюме, MoM, ToDo, протоколы и др.) должны храниться только в отдельном модуле, например, `frontend_bot/GPT_Prompts/transcribe/prompts.py`.
- В хендлерах и сервисах запрещено дублировать или захардкоживать промты — только импортировать из централизованного файла.
- Это облегчает поддержку, локализацию и переиспользование промтов.

**Пример:**
```python
# frontend_bot/GPT_Prompts/transcribe/prompts.py
FULL_TRANSCRIPT_PROMPT = "..."

# frontend_bot/handlers/transcribe_protocol.py
from frontend_bot.GPT_Prompts.transcribe.prompts import FULL_TRANSCRIPT_PROMPT
```

## Документирование и правила ведения задач

- Все задачи, планы и чек-листы ведём только в корневом TASK.md.
- Архитектура и best practices — только в docs/architecture.md, docs/best_practices.md.
- Не допускается дублирование задач и регламентов в других файлах.
- Все новые правила и процессы — отдельный подраздел в best_practices.md.
- Любое изменение в архитектуре или процессах — фиксировать в соответствующем md-файле.
- В README.md — только краткое описание и ссылки на docs/. 

### Валидация фото (размер, формат, дубликаты)
- Всегда используйте только `validate_photo` из `frontend_bot/services/avatar_manager.py` для проверки фото.
- Не допускается дублирование логики валидации в других модулях.
- Все параметры (размер, формат, лимиты) — только из config.
- При добавлении новых хендлеров/сервисов — импортировать и вызывать только эту функцию. 

## Функциональный стиль вместо классов-сервисов

- Все сервисы реализуются как отдельные функции с явной передачей зависимостей (storage_dir и др.), без хранения состояния в классах.
- Исключение — state/caching-менеджеры, где оправдано хранение состояния (например, StateManager).
- Каждый сервис-файл должен содержать только функции, необходимые для бизнес-логики, без классов-обёрток.
- Все функции должны иметь аннотации типов и docstring.
- Для асинхронных операций использовать только async-совместимые библиотеки (aiofiles, AsyncFileManager и др.).
- Все значения (пути, лимиты, константы) — только через config.py или переменные окружения.
- Валидация и обработка ошибок — через отдельные функции, логирование через logger.exception.
- Тесты пишутся сразу для каждой функции (pytest, pytest-asyncio), каждый тест работает с чистым temp_dir.
- Для тестов не использовать глобальные/реальные директории — только временные каталоги через tmp_path/fixtures.
- Все переходы между состояниями FSM и возвраты в меню покрываются тестами (минимум ручными), кейсы описываются в best_practices.md.
- При рефакторинге классов-сервисов в функции:
    - Удалять класс, переносить методы в функции с явной передачей зависимостей.
    - Обновлять все импорты и вызовы в коде и тестах.
    - Проверять, что тесты проходят (pytest -v).
- Все архитектурные решения и best practices фиксируются в docs/. 

- При очистке истории пользователя (clear_user_history) обязательно вызывать и delete_user_transcripts(user_id, storage_dir), чтобы удалять все файлы пользователя из transcripts/{user_id}/ и все chunk-папки (chunks_*). Это предотвращает накопление мусора и утечку данных. 