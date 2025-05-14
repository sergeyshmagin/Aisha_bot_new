# Асинхронность и безопасность

## Почему важна асинхронность?

- Асинхронные операции позволяют обрабатывать десятки и сотни запросов одновременно без блокировки event loop.
- Синхронные вызовы (open, os.remove, os.path.exists, time.sleep) блокируют event loop и приводят к деградации производительности.
- Для highload-сценариев (массовая обработка фото, аудио, транскрипций) асинхронность — обязательное требование.

## Как правильно работать с файлами и процессами

- Используйте только `aiofiles` для чтения/записи файлов.
- Для запуска внешних процессов (ffmpeg, docx) используйте `asyncio.create_subprocess_exec`.
- Не используйте sync-функции внутри async-кода.

**Пример (правильно):**
```python
import aiofiles
async with aiofiles.open(path, "rb") as f:
    data = await f.read()
```

**Пример (неправильно):**
```python
with open(path, "rb") as f:  # Блокирует event loop!
    data = f.read()
```

## Безопасность и конкурентный доступ

- Для конкурентного доступа к общим данным используйте asyncio.Lock или переходите на Redis.
- Не храните важные данные только в памяти — используйте файловое или внешнее хранилище.
- Все ошибки логируйте через logger.exception, пользователю отправляйте информативные сообщения.

## Проверка на sync-операции

- Перед коммитом обязательно проверяйте, что нет sync-операций с файлами.
- В ревью обращайте внимание на работу с файлами и процессами.

## Переход на Redis

- Для production-окружения рекомендуется заменить глобальные словари для сессий и буферов на Redis.
- Это обеспечит масштабируемость и устойчивость к сбоям.

## Async и безопасность в тестах

- Все тесты используют pytest-asyncio, все хендлеры и сервисы тестируются как async def.
- Для моков Telebot, GPT и файлов — только async-compatible моки (AsyncMock, patch).
- Состояние (user_transcripts) очищается через autouse-фикстуру в conftest.py.
- Проверять, что event-loop не остаётся с pending-tasks (pytest-asyncio strict mode).
- Не использовать sync-функции (open, os.path, shutil) в async-коде.
- Для файловых операций — только aiofiles.
- Для внешних процессов — только через asyncio.create_subprocess_exec.
- Все тесты должны быть изолированы: не влияют друг на друга, не используют глобальное состояние без фикстур.
- Пример фикстуры для очистки состояния:

```python
@pytest.fixture(autouse=True)
def clear_user_transcripts():
    user_transcripts.clear()
    yield
    user_transcripts.clear()
```

## Паттерн мока aiofiles.open в асинхронных тестах

- Для моков файловых операций используйте только async-compatible моки (AsyncMock, patch, собственные async-контекстные менеджеры).
- Если требуется мокать aiofiles.open, делайте это только внутри области теста (with patch(...)), чтобы не ломать работу других сервисов (например, user_transcripts_store).
- Пример async-контекстного менеджера для мока:

```python
from unittest.mock import patch
class AsyncFile:
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc, tb): pass
    async def read(self): return "not empty"
with patch("aiofiles.open", return_value=AsyncFile()):
    await my_async_func()
```
