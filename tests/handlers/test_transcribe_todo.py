from unittest.mock import AsyncMock, patch
from frontend_bot.handlers import transcribe_protocol
from frontend_bot.services import user_transcripts_store


@patch(
    "frontend_bot.handlers.transcribe_protocol.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.bot.send_document",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.bot.send_chat_action",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.bot.send_message",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.async_exists",
    new_callable=AsyncMock,
)
async def test_send_todo_success(
    mock_async_exists: AsyncMock,
    mock_send_message: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_document: AsyncMock,
    mock_gpt: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
    mock_aiofiles_open,
):
    """
    Проверяет успешную отправку ToDo как .txt-файла с корректным именем,
    содержимым и caption.
    """
    await user_transcripts_store.set(fake_user_id, fake_txt_file)
    mock_async_exists.return_value = True
    mock_gpt.return_value = "ToDo для теста"

    class AsyncFile:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def read(self):
            return "not empty"

    with patch("aiofiles.open", return_value=AsyncFile()):
        message = type(
            "Msg",
            (),
            {
                "from_user": type("U", (), {"id": fake_user_id})(),
                "chat": type("C", (), {"id": 1})(),
                "text": "Сформировать ToDo",
            },
        )()
        await transcribe_protocol.send_todo_checklist(message)
    assert mock_send_document.called, "send_document не был вызван"
    args, kwargs = mock_send_document.call_args
    filename, fileobj = args[1]
    fileobj.seek(0)
    content = fileobj.read().decode()
    assert content, "Файл пустой"


@patch(
    "frontend_bot.handlers.transcribe_protocol.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.bot.send_document",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.bot.send_chat_action",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.bot.send_message",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.async_exists",
    new_callable=AsyncMock,
)
async def test_send_todo_no_file(
    mock_async_exists: AsyncMock,
    mock_send_message: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_document: AsyncMock,
    mock_gpt: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
    mock_aiofiles_open,
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
            "text": "Сформировать ToDo",
        },
    )()
    await transcribe_protocol.send_todo_checklist(message)
    mock_send_message.assert_called()


@patch(
    "frontend_bot.handlers.transcribe_protocol.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.bot.send_document",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.bot.send_chat_action",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.bot.send_message",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.async_exists",
    new_callable=AsyncMock,
)
async def test_send_todo_gpt_error(
    mock_async_exists: AsyncMock,
    mock_send_message: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_document: AsyncMock,
    mock_gpt: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
    mock_aiofiles_open,
):
    """
    Проверяет, что при ошибке GPT бот отправляет корректное сообщение об ошибке.
    """
    await user_transcripts_store.set(fake_user_id, fake_txt_file)
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
            "text": "Сформировать ToDo",
        },
    )()
    await transcribe_protocol.send_todo_checklist(message)
    mock_send_message.assert_called()


@patch(
    "frontend_bot.handlers.transcribe_protocol.bot.send_message",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.bot.send_chat_action",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.bot.send_document",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.async_exists",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
async def test_send_todo_empty_transcript(
    mock_async_exists: AsyncMock,
    mock_send_message: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_document: AsyncMock,
    mock_gpt: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
    mock_aiofiles_open,
):
    """
    Проверяет обработку случая, когда транскрипт пустой (файл есть, но пустой)
    для ToDo. Ожидается user-friendly сообщение об ошибке.
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
    mock_gpt.return_value = ""
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
            "text": "Сформировать ToDo",
        },
    )()
    await transcribe_protocol.send_todo_checklist(message)
    mock_send_message.assert_called()


@patch(
    "frontend_bot.handlers.transcribe_protocol.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.bot.send_document",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.bot.send_chat_action",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.bot.send_message",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.async_exists",
    new_callable=AsyncMock,
)
async def test_send_todo_empty_gpt(
    mock_async_exists: AsyncMock,
    mock_send_message: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_document: AsyncMock,
    mock_gpt: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
    mock_aiofiles_open,
):
    """
    Проверяет обработку случая, когда GPT возвращает пустую строку для ToDo.
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
    mock_gpt.return_value = ""
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
            "text": "Сформировать ToDo",
        },
    )()
    await transcribe_protocol.send_todo_checklist(message)
    mock_send_message.assert_called()
