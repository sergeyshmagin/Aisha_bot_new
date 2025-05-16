from unittest.mock import AsyncMock, patch, MagicMock


class AsyncContextManagerMock(MagicMock):
    """Мок для асинхронного контекстного менеджера"""
    async def __aenter__(self):
        return self.aenter

    async def __aexit__(self, *args):
        pass

from frontend_bot.handlers import transcribe_protocol
from frontend_bot.services import transcript_cache


@patch(
    "frontend_bot.handlers.general.bot.send_message",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.general.bot.send_chat_action",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.general.bot.send_document",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.services.gpt_assistant.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
async def test_mom_success(
    mock_gpt,
    mock_send_document,
    mock_send_chat_action,
    mock_send_message,
    fake_user_id: int,
    fake_txt_file: str,
    mock_aiofiles_open,
):
    """
    Проверяет успешную отправку MoM как .txt-файла с корректным именем,
    содержимым и caption.
    """
    await transcript_cache.set(fake_user_id, fake_txt_file)
    mock_aiofiles_open.set_content(fake_txt_file, "Test transcript content")
    mock_gpt.return_value = "MoM для теста"
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
    assert mock_send_document.called, (
        "❌ send_document не был вызван. "
        "Проверьте, что хендлер send_mom корректно вызывает отправку файла."
    )
    args, kwargs = mock_send_document.call_args
    filename, fileobj = args[1]
    assert filename.startswith("mom_") and filename.endswith(".txt"), (
        f"❌ Имя файла некорректно: {filename}. "
        "Проверьте генерацию имени файла."
    )
    fileobj.seek(0)
    content = fileobj.read().decode()
    assert content, (
        "❌ Содержимое файла пустое. Проверьте, что файл отправлен."
    )
    assert kwargs["caption"].startswith("📝 MoM (Minutes of Meeting)"), (
        f"❌ Caption некорректен: {kwargs['caption']}. "
        "Проверьте caption для MoM."
    )


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
async def test_send_mom_no_file(
    mock_async_exists: AsyncMock,
    mock_send_message: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_document: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
    mock_aiofiles_open,
):
    """
    Проверяет, что если файла транскрипта нет, бот отправляет корректное
    сообщение об ошибке.
    """
    await transcript_cache.set(fake_user_id, fake_txt_file)
    mock_aiofiles_open.set_content(fake_txt_file, "")
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
    mock_send_message.assert_called()


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
async def test_send_mom_gpt_error(
    mock_gpt: AsyncMock,
    mock_async_exists: AsyncMock,
    mock_send_message: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_document: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
    mock_aiofiles_open,
):
    """
    Проверяет, что при ошибке GPT бот отправляет корректное сообщение об ошибке.
    """
    await transcript_cache.set(fake_user_id, fake_txt_file)
    mock_aiofiles_open.set_content(fake_txt_file, "Test transcript content")
    mock_async_exists.return_value = True
    mock_gpt.side_effect = Exception("GPT error")

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
    mock_send_message.assert_called()


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
async def test_send_mom_empty_transcript(
    mock_gpt: AsyncMock,
    mock_async_exists: AsyncMock,
    mock_send_message: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_document: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
    mock_aiofiles_open,
):
    """
    Проверяет обработку случая, когда транскрипт пустой (файл есть, но пустой) для MoM.
    Ожидается user-friendly сообщение об ошибке.
    """
    await transcript_cache.set(fake_user_id, fake_txt_file)
    mock_aiofiles_open.set_content(fake_txt_file, "")
    mock_async_exists.return_value = True

    class AsyncFile:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def read(self):
            return ""

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
    mock_send_message.assert_called()


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
async def test_send_mom_empty_gpt(
    mock_gpt: AsyncMock,
    mock_async_exists: AsyncMock,
    mock_send_message: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_document: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
    mock_aiofiles_open,
):
    """
    Проверяет обработку случая, когда GPT возвращает пустую строку для MoM.
    Ожидается user-friendly сообщение об ошибке.
    """
    await transcript_cache.set(fake_user_id, fake_txt_file)
    mock_aiofiles_open.set_content(fake_txt_file, "Test transcript content")
    mock_async_exists.return_value = True

    class AsyncFile:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def read(self):
            return "Test transcript content"

    mock_aiofiles_open.return_value = AsyncFile()
    mock_gpt.return_value = ""
    
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
    mock_send_message.assert_called()
