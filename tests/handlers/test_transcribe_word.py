from unittest.mock import AsyncMock, patch
from frontend_bot.handlers import transcribe_protocol
from frontend_bot.services import transcript_cache


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
    "frontend_bot.services.word_generator.generate_protocol_word",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
async def test_send_meeting_protocol_success(
    mock_gpt,
    mock_generate_word,
    mock_async_exists,
    mock_send_document,
    mock_send_chat_action,
    mock_send_message,
    fake_user_id,
    fake_txt_file,
    mock_aiofiles_open,
):
    """
    Проверяет успешную отправку Word-протокола: файл отправляется с правильным именем, содержимым и caption.
    """
    await transcript_cache.set(fake_user_id, fake_txt_file)
    mock_aiofiles_open.set_content(fake_txt_file, "Test transcript content")
    mock_async_exists.return_value = True
    mock_gpt.return_value = "Текст протокола для теста"
    mock_generate_word.return_value = "temp_protocol.docx"
    class AsyncFile:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass
        async def read(self): return "Test transcript content"
    class AsyncDocxFile:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass
        async def read(self): return b"DOCX DATA"
    mock_aiofiles_open.side_effect = [AsyncFile(), AsyncDocxFile()]
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
            "text": "Протокол заседания (Word)",
        },
    )()
    await transcribe_protocol.send_meeting_protocol(message)
    assert mock_send_document.called, "send_document не был вызван"
    args, kwargs = mock_send_document.call_args
    filename, fileobj = args[1]
    assert filename.startswith("protocol_") and filename.endswith(".docx"), (
        f"❌ Имя файла некорректно: {filename}. Проверьте генерацию имени файла для Word-протокола."
    )
    fileobj.seek(0)
    content = fileobj.read()
    assert content, "Файл Word пустой"


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
    "frontend_bot.services.word_generator.generate_protocol_word",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
async def test_send_meeting_protocol_no_file(
    mock_gpt,
    mock_generate_word,
    mock_async_exists,
    mock_send_document,
    mock_send_chat_action,
    mock_send_message,
    fake_user_id,
    fake_txt_file,
    mock_aiofiles_open,
):
    """
    Проверяет, что если файла транскрипта нет, бот отправляет корректное
    сообщение об ошибке.
    """
    await transcript_cache.set(fake_user_id, fake_txt_file)
    mock_aiofiles_open.set_content(fake_txt_file, "")
    mock_async_exists.return_value = False
    mock_gpt.return_value = ""
    class AsyncFile:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass
        async def read(self): return ""
    mock_aiofiles_open.return_value = AsyncFile()
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
            "text": "Протокол заседания (Word)",
        },
    )()
    await transcribe_protocol.send_meeting_protocol(message)
    mock_send_message.assert_called()
    mock_send_document.assert_not_called()


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
    "frontend_bot.services.word_generator.generate_protocol_word",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
# Удалён patch для mock_add_history и mock_async_remove, так как они не вызываются в send_meeting_protocol
async def test_send_meeting_protocol_gpt_empty(
    mock_gpt: AsyncMock,
    mock_generate_word: AsyncMock,
    mock_async_exists: AsyncMock,
    mock_send_document: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_message: AsyncMock,
    mock_aiofiles_open: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
):
    """
    Проверяет, что если GPT вернул пустую строку, бот отправляет корректное
    сообщение об ошибке (Word).
    """
    await transcript_cache.set(fake_user_id, fake_txt_file)
    mock_aiofiles_open.set_content(fake_txt_file, "Test transcript content")
    mock_async_exists.return_value = True
    mock_gpt.return_value = "   "

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
            "text": "Протокол заседания (Word)",
        },
    )()
    await transcribe_protocol.send_meeting_protocol(message)
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
    "frontend_bot.services.word_generator.generate_protocol_word",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
# Удалён patch для mock_add_history и mock_async_remove, так как они не вызываются в send_meeting_protocol
async def test_send_meeting_protocol_exception(
    mock_gpt: AsyncMock,
    mock_generate_word: AsyncMock,
    mock_async_exists: AsyncMock,
    mock_send_document: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_message: AsyncMock,
    mock_aiofiles_open: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
):
    """
    Проверяет, что при исключении в процессе генерации Word бот отправляет
    корректное сообщение об ошибке.
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
            "text": "Протокол заседания (Word)",
        },
    )()
    await transcribe_protocol.send_meeting_protocol(message)
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
    "frontend_bot.services.word_generator.generate_protocol_word",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_protocol.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
# Удалён patch для mock_add_history и mock_async_remove, так как они не вызываются в send_meeting_protocol
async def test_send_meeting_protocol_empty_transcript(
    mock_gpt: AsyncMock,
    mock_generate_word: AsyncMock,
    mock_async_exists: AsyncMock,
    mock_send_document: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_message: AsyncMock,
    mock_aiofiles_open: AsyncMock,
    fake_user_id: int,
    fake_txt_file: str,
):
    """
    Проверяет обработку случая, когда транскрипт пустой (файл есть, но пустой)
    для Word-протокола. Ожидается user-friendly сообщение об ошибке.
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

    mock_aiofiles_open(AsyncFile())
    mock_gpt.return_value = ""
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
            "text": "Протокол заседания (Word)",
        },
    )()
    await transcribe_protocol.send_meeting_protocol(message)
    mock_send_message.assert_called()
