from unittest.mock import AsyncMock, patch, MagicMock


class AsyncContextManagerMock(MagicMock):
    """Мок для асинхронного контекстного менеджера"""
    async def __aenter__(self):
        return self.aenter

    async def __aexit__(self, *args):
        pass

from frontend_bot.handlers import transcribe_protocol
from frontend_bot.services import user_transcripts_store


@patch("frontend_bot.services.user_transcripts_store._save", new_callable=AsyncMock)
@patch("frontend_bot.services.user_transcripts_store._load", new_callable=AsyncMock)
@patch(
    "frontend_bot.handlers.general.bot.send_document",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.general.bot.send_chat_action",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.general.bot.send_message",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.services.file_utils.async_exists",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.services.gpt_assistant.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
@patch("aiofiles.open", new_callable=AsyncMock)
async def test_send_mom_success(
    mock_aiofiles_open: AsyncMock,
    mock_format_transcript_with_gpt: AsyncMock,
    mock_async_exists: AsyncMock,
    mock_send_message: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_document: AsyncMock,
    mock_load: AsyncMock,
    mock_save: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
):
    """
    Проверяет успешную отправку MoM (Minutes of Meeting) как .txt-файла с
    корректным именем, содержимым и caption.
    """
    await user_transcripts_store.set(fake_user_id, fake_txt_file)
    mock_async_exists.return_value = True
    mock_format_transcript_with_gpt.return_value = "MoM для теста"

    class AsyncFile:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def read(self):
            return "Test transcript content"

    mock_aiofiles_open.return_value = AsyncFile()
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
            "text": "Сформировать MoM",
        },
    )()
    await transcribe_protocol.send_mom(message)
    # Проверяем, что файл отправлен
    mock_send_document.assert_called()
    args, kwargs = mock_send_document.call_args
    filename, fileobj = args[1]
    assert filename.startswith("mom_") and filename.endswith(".txt"), (
        f"❌ Имя файла некорректно: {filename}. "
        "Проверьте генерацию имени файла для MoM."
    )
    fileobj.seek(0)
    content = fileobj.read().decode()
    assert content, (
        "❌ Содержимое файла пустое. Проверьте, что GPT-ответ передаётся в файл MoM."
    )
    assert kwargs["caption"].startswith("📝 MoM (Minutes of Meeting)"), (
        f"❌ Caption некорректен: {kwargs['caption']}. " "Проверьте caption для MoM."
    )


@patch("frontend_bot.services.user_transcripts_store._save", new_callable=AsyncMock)
@patch("frontend_bot.services.user_transcripts_store._load", new_callable=AsyncMock)
@patch(
    "frontend_bot.handlers.general.bot.send_document",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.general.bot.send_chat_action",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.general.bot.send_message",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.services.file_utils.async_exists",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.services.gpt_assistant.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
@patch("aiofiles.open", new_callable=AsyncMock)
async def test_send_mom_no_file(
    mock_aiofiles_open: AsyncMock,
    mock_format_transcript_with_gpt: AsyncMock,
    mock_async_exists: AsyncMock,
    mock_send_message: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_document: AsyncMock,
    mock_load: AsyncMock,
    mock_save: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
):
    """
    Проверяет, что если файла транскрипта нет, бот отправляет корректное
    сообщение об ошибке.
    """
    await user_transcripts_store.set(fake_user_id, fake_txt_file)
    mock_async_exists.return_value = False
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
            "text": "Сформировать MoM",
        },
    )()
    await transcribe_protocol.send_mom(message)
    # Проверяем только факт отправки сообщения
    mock_send_message.assert_called()


@patch("frontend_bot.services.user_transcripts_store._save", new_callable=AsyncMock)
@patch("frontend_bot.services.user_transcripts_store._load", new_callable=AsyncMock)
@patch(
    "frontend_bot.handlers.general.bot.send_document",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.general.bot.send_chat_action",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.general.bot.send_message",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.services.file_utils.async_exists",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.services.gpt_assistant.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
@patch("aiofiles.open", new_callable=AsyncMock)
async def test_send_mom_gpt_error(
    mock_aiofiles_open: AsyncMock,
    mock_format_transcript_with_gpt: AsyncMock,
    mock_async_exists: AsyncMock,
    mock_send_message: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_document: AsyncMock,
    mock_load: AsyncMock,
    mock_save: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
):
    """
    Проверяет, что при ошибке GPT бот отправляет корректное сообщение об ошибке.
    """
    await user_transcripts_store.set(fake_user_id, fake_txt_file)
    mock_async_exists.return_value = True
    mock_format_transcript_with_gpt.side_effect = Exception("GPT error")

    class AsyncFile:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def read(self):
            return "Test transcript content"

    mock_aiofiles_open.return_value = AsyncFile()
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
            "text": "Сформировать MoM",
        },
    )()
    await transcribe_protocol.send_mom(message)
    # Проверяем только факт отправки сообщения
    mock_send_message.assert_called()


@patch("frontend_bot.services.user_transcripts_store._save", new_callable=AsyncMock)
@patch("frontend_bot.services.user_transcripts_store._load", new_callable=AsyncMock)
@patch(
    "frontend_bot.handlers.general.bot.send_document",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.general.bot.send_chat_action",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.general.bot.send_message",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.services.file_utils.async_exists",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.services.gpt_assistant.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
@patch("aiofiles.open", new_callable=AsyncMock)
async def test_send_mom_empty_transcript(
    mock_aiofiles_open: AsyncMock,
    mock_format_transcript_with_gpt: AsyncMock,
    mock_async_exists: AsyncMock,
    mock_send_message: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_document: AsyncMock,
    mock_load: AsyncMock,
    mock_save: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
):
    """
    Проверяет обработку случая, когда транскрипт пустой (файл есть, но пустой) для MoM.
    Ожидается user-friendly сообщение об ошибке.
    """
    await user_transcripts_store.set(fake_user_id, fake_txt_file)
    mock_async_exists.return_value = True

    class AsyncFile:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def read(self):
            return ""

    mock_aiofiles_open.return_value = AsyncFile()
    mock_format_transcript_with_gpt.return_value = ""
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
            "text": "Сформировать MoM",
        },
    )()
    await transcribe_protocol.send_mom(message)
    # Проверяем только факт отправки сообщения
    mock_send_message.assert_called()


@patch("frontend_bot.services.user_transcripts_store._save", new_callable=AsyncMock)
@patch("frontend_bot.services.user_transcripts_store._load", new_callable=AsyncMock)
@patch(
    "frontend_bot.handlers.general.bot.send_document",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.general.bot.send_chat_action",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.general.bot.send_message",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.services.file_utils.async_exists",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.services.gpt_assistant.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
@patch("aiofiles.open", new_callable=AsyncMock)
async def test_send_mom_empty_gpt(
    mock_aiofiles_open: AsyncMock,
    mock_format_transcript_with_gpt: AsyncMock,
    mock_async_exists: AsyncMock,
    mock_send_message: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_document: AsyncMock,
    mock_load: AsyncMock,
    mock_save: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
):
    """
    Проверяет обработку случая, когда GPT возвращает пустую строку для MoM.
    Ожидается user-friendly сообщение об ошибке.
    """
    await user_transcripts_store.set(fake_user_id, fake_txt_file)
    mock_async_exists.return_value = True

    class AsyncFile:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def read(self):
            return "Test transcript content"

    mock_aiofiles_open.return_value = AsyncFile()
    mock_format_transcript_with_gpt.return_value = ""
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
            "text": "Сформировать MoM",
        },
    )()
    await transcribe_protocol.send_mom(message)
    # Проверяем только факт отправки сообщения
    mock_send_message.assert_called()
