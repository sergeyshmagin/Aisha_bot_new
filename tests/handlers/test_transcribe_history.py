import pytest
from unittest.mock import AsyncMock, patch
import frontend_bot.handlers.transcribe_history as transcribe_history


@pytest.mark.asyncio
@patch(
    "frontend_bot.handlers.transcribe_history.service_get_user_history",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_history.bot.send_message",
    new_callable=AsyncMock,
)
@patch("frontend_bot.handlers.transcribe_history.history_keyboard")
async def test_show_history_success(
    mock_keyboard,
    mock_send_message: AsyncMock,
    mock_get_history: AsyncMock,
    fake_user_id: int,
):
    """
    Проверяет успешную отправку истории, если у пользователя есть обработанные файлы.
    """
    mock_get_history.return_value = [
        {
            "file": "file1.txt",
            "type": "txt",
            "result": "summary",
            "date": "2024-07-01",
        },
        {
            "file": "file2.docx",
            "type": "word",
            "result": "protocol",
            "date": "2024-07-02",
        },
    ]
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
        },
    )()
    await transcribe_history.show_history(message)
    mock_send_message.assert_called()
    args, kwargs = mock_send_message.call_args
    assert "Последние файлы" in args[1], "❌ Сообщение истории не содержит заголовка."
    assert (
        "file1.txt" in args[1] and "file2.docx" in args[1]
    ), "❌ В истории не отображаются имена файлов."


@pytest.mark.asyncio
@patch(
    "frontend_bot.handlers.transcribe_history.service_get_user_history",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_history.bot.send_message",
    new_callable=AsyncMock,
)
@patch("frontend_bot.handlers.transcribe_history.history_keyboard")
async def test_show_history_empty(
    mock_keyboard,
    mock_send_message: AsyncMock,
    mock_get_history: AsyncMock,
    fake_user_id: int,
):
    """
    Проверяет корректное сообщение, если у пользователя нет обработанных файлов.
    """
    mock_get_history.return_value = []
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
        },
    )()
    await transcribe_history.show_history(message)
    mock_send_message.assert_called()
    args, kwargs = mock_send_message.call_args
    assert (
        "нет обработанных файлов" in args[1].lower()
    ), "❌ При пустой истории не отправлено ожидаемое сообщение."
