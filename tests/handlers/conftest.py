import pytest
from frontend_bot.services import user_transcripts_store
from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock, MagicMock, patch


@pytest.fixture(autouse=True)
async def clear_user_transcripts() -> AsyncGenerator[None, None]:
    """Очищает user_transcripts до и после каждого теста."""
    await user_transcripts_store.clear()
    yield
    await user_transcripts_store.clear()


@pytest.fixture
def fake_user_id() -> int:
    """Фикстура для поддельного user_id."""
    return 123456


@pytest.fixture
def fake_txt_file(tmp_path) -> str:
    """Создаёт временный .txt-файл для теста транскрипта."""
    file_path = tmp_path / "test_transcript.txt"
    file_path.write_text("Test transcript content")
    return str(file_path)


class AsyncFileMock:
    def __init__(self, content="", mode="r"):
        self._content = content
        self._written = b"" if "b" in mode else ""
        self._mode = mode

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def read(self):
        if "b" in self._mode:
            return self._content.encode() if isinstance(self._content, str) else self._content
        return self._content.decode() if isinstance(self._content, bytes) else self._content

    async def write(self, data):
        if "b" in self._mode:
            self._written += data if isinstance(data, bytes) else data.encode()
        else:
            self._written += data if isinstance(data, str) else data.decode()


@pytest.fixture
def mock_aiofiles_open(monkeypatch):
    """
    Позволяет задавать содержимое для мокнутого файла через параметр content.
    Пример использования:
        mock_aiofiles_open.set_content(
            "test.txt",
            "some text"
        )
    """
    file_contents = {}

    def set_content(file, content):
        file_contents[str(file)] = content

    def _open(file, mode="r", *args, **kwargs):
        content = file_contents.get(str(file), b"" if "b" in mode else "")
        return AsyncFileMock(content=content, mode=mode)

    monkeypatch.setattr("aiofiles.open", _open)
    _open.set_content = set_content
    return _open


@pytest.fixture
def mock_send_message():
    return AsyncMock()


@pytest.fixture
def mock_send_chat_action():
    return AsyncMock()


@pytest.fixture
def mock_send_document():
    return AsyncMock()


@pytest.fixture
def mock_gpt():
    return AsyncMock()


@pytest.fixture
def mock_generate_word():
    return AsyncMock()


@pytest.fixture
def mock_open():
    return MagicMock()


@pytest.fixture
def mock_async_remove():
    return AsyncMock()


@pytest.fixture
def mock_add_history():
    return AsyncMock()


@pytest.fixture
def mock_remove_history():
    return AsyncMock()


@pytest.fixture
def mock_async_exists():
    return AsyncMock()


@pytest.fixture
def mock_get_history():
    return AsyncMock()


@pytest.fixture
def mock_keyboard():
    return Mock()


@pytest.fixture(autouse=True, scope="session")
def patch_telebot_methods():
    """Мокает методы бота, чтобы не было реальных запросов к Telegram API."""
    with patch(
        "frontend_bot.handlers.transcribe_protocol.bot.send_message",
        new_callable=AsyncMock,
    ), patch(
        "frontend_bot.handlers.transcribe_protocol.bot.send_chat_action",
        new_callable=AsyncMock,
    ), patch(
        "frontend_bot.handlers.transcribe_protocol.bot.send_document",
        new_callable=AsyncMock,
    ):
        yield


@pytest.fixture(autouse=True)
def set_user_transcripts_json(mock_aiofiles_open):
    """
    Всегда задаёт '{}' для user_transcripts.json, чтобы избежать ошибок декодирования JSON.
    """
    mock_aiofiles_open.set_content("storage/user_transcripts.json", "{}")
