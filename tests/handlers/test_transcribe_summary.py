"""
Тесты для функций генерации сводок и полных транскриптов.
"""

from unittest.mock import AsyncMock, Mock, patch
from frontend_bot.handlers import transcribe_protocol
from frontend_bot.services import user_transcripts_store


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
async def test_full_official_transcript_success(
    mock_gpt,
    mock_send_document,
    mock_send_chat_action,
    mock_send_message,
    fake_user_id: int,
    fake_txt_file: str,
    mock_aiofiles_open,
):
    """
    Проверяет успешную отправку полного официального транскрипта как .txt-файла
    с корректным именем, содержимым и caption.
    """
    await user_transcripts_store.set(fake_user_id, fake_txt_file)
    mock_aiofiles_open.set_content(fake_txt_file, "Test transcript content")
    mock_gpt.return_value = "Полный транскрипт для теста"
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
            "text": "Полный официальный транскрипт",
        },
    )()
    await transcribe_protocol.send_full_official_transcript(message)
    args, kwargs = mock_send_document.call_args
    filename, fileobj = args[1]
    assert filename.startswith("full_transcript_") and filename.endswith(".txt"), (
        f"❌ Имя файла некорректно: {filename}. "
        "Проверьте генерацию имени файла."
    )
    fileobj.seek(0)
    content = fileobj.read().decode()
    assert content, (
        "❌ Содержимое файла пустое. Проверьте, что файл отправлен."
    )
    assert kwargs["caption"].startswith("📝 Полный официальный транскрипт"), (
        f"❌ Caption некорректен: {kwargs['caption']}. "
        "Проверьте caption для полного транскрипта."
    )


@patch(
    "frontend_bot.services.gpt_assistant.format_transcript_with_gpt",
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
    "frontend_bot.handlers.general.bot.send_document",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.services.file_utils.async_exists",
    new_callable=AsyncMock,
)
async def test_short_summary_success(
    mock_async_exists,
    mock_send_document,
    mock_send_message,
    mock_send_chat_action,
    mock_gpt,
    fake_user_id: int,
    fake_txt_file: str,
    mock_aiofiles_open,
):
    """
    Проверяет успешную отправку сводки как .txt-файла с корректным именем,
    содержимым и caption.
    """
    await user_transcripts_store.set(fake_user_id, fake_txt_file)
    mock_aiofiles_open.set_content(fake_txt_file, "Test transcript content")
    mock_async_exists.return_value = True
    mock_gpt.return_value = "Сводка для теста"
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
            "text": "Сводка на 1 страницу",
        },
    )()
    await transcribe_protocol.send_short_summary(message)
    assert mock_send_document.called, (
        "❌ send_document не был вызван. "
        "Проверьте, что хендлер send_short_summary корректно вызывает отправку файла."
    )
    args, kwargs = mock_send_document.call_args
    filename, fileobj = args[1]
    assert filename.startswith("summary_") and filename.endswith(".txt"), (
        f"❌ Имя файла некорректно: {filename}. "
        "Проверьте генерацию имени файла."
    )
    fileobj.seek(0)
    content = fileobj.read().decode()
    assert content, (
        "❌ Содержимое файла пустое. Проверьте, что файл отправлен."
    )
    assert kwargs["caption"].startswith("📝 Сводка на 1 страницу"), (
        f"❌ Caption некорректен: {kwargs['caption']}. "
        "Проверьте caption для summary."
    )


@patch(
    "frontend_bot.services.gpt_assistant.format_transcript_with_gpt",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.services.file_utils.async_exists",
    new_callable=AsyncMock,
)
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
async def test_short_summary_empty_transcript(
    mock_send_document: AsyncMock,
    mock_send_chat_action: AsyncMock,
    mock_send_message: AsyncMock,
    mock_async_exists: AsyncMock,
    mock_gpt,
    fake_user_id: int,
    fake_txt_file: str,
    mock_aiofiles_open,
):
    """
    Проверяет обработку случая, когда транскрипт пустой (файл есть, но пустой)
    для сводки. Ожидается user-friendly сообщение об ошибке.
    """
    mock_aiofiles_open.set_content(fake_txt_file, "")
    await user_transcripts_store.set(fake_user_id, fake_txt_file)
    mock_async_exists.return_value = True
    mock_gpt.return_value = ""
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
            "text": "Сводка на 1 страницу",
        },
    )()
    await transcribe_protocol.send_short_summary(message)
    mock_send_message.assert_called()
    args, kwargs = mock_send_message.call_args
    assert (
        "что-то пошло не так" in args[1].lower()
        or "gpt вернул пустой" in args[1].lower()
    ), "❌ При пустом транскрипте не отправлено ожидаемое сообщение об ошибке."


import pytest
@pytest.mark.asyncio
async def test_audio_transcript_persistence(fake_user_id, fake_txt_file):
    """
    Проверяет, что после set/get user_transcripts_store возвращает путь к транскрипту.
    """
    from frontend_bot.services import user_transcripts_store
    await user_transcripts_store.set(fake_user_id, fake_txt_file)
    result = await user_transcripts_store.get(fake_user_id)
    assert result == fake_txt_file, f"❌ user_transcripts_store.get вернул {result}, ожидалось {fake_txt_file}"
