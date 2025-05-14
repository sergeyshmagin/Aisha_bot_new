from unittest.mock import AsyncMock, patch
import frontend_bot.handlers.transcribe_history as transcribe_history
from frontend_bot.services import user_transcripts_store


@patch("frontend_bot.handlers.transcribe_history.history_keyboard")
@patch(
    "frontend_bot.handlers.transcribe_history.bot.send_message",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_history.async_remove",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_history.async_exists",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_history.service_remove_last_history_entry",
    new_callable=AsyncMock,
)
async def test_delete_my_file_success(
    mock_remove_history: AsyncMock,
    mock_async_exists: AsyncMock,
    mock_async_remove: AsyncMock,
    mock_send_message: AsyncMock,
    mock_keyboard,
    fake_user_id: int,
    fake_txt_file: str,
):
    """
    Проверяет успешное удаление файла: файл есть, все сервисы вызываются, сообщение корректно.
    """
    await user_transcripts_store.set(fake_user_id, fake_txt_file)
    mock_async_exists.return_value = True
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
            "text": "🗑 Удалить мой файл",
        },
    )()
    await transcribe_history.delete_my_file(message)
    mock_async_remove.assert_awaited_once_with(fake_txt_file)
    mock_remove_history.assert_awaited_once_with(
        str(fake_user_id)
    )
    mock_send_message.assert_awaited()
    args, kwargs = mock_send_message.call_args
    assert (
        "Ваш последний файл удалён." in args[1]
    ), "❌ При успешном удалении не отправлено ожидаемое сообщение."
    if hasattr(user_transcripts_store, 'all'):
        all_store = await user_transcripts_store.all()
        assert fake_user_id not in all_store


@patch("frontend_bot.handlers.transcribe_history.history_keyboard")
@patch(
    "frontend_bot.handlers.transcribe_history.bot.send_message",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_history.async_remove",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_history.async_exists",
    new_callable=AsyncMock,
)
@patch(
    "frontend_bot.handlers.transcribe_history.service_remove_last_history_entry",
    new_callable=AsyncMock,
)
async def test_delete_my_file_no_file(
    mock_remove_history: AsyncMock,
    mock_async_exists: AsyncMock,
    mock_async_remove: AsyncMock,
    mock_send_message: AsyncMock,
    mock_keyboard,
    fake_user_id: int,
):
    """
    Проверяет корректное сообщение, если файла для удаления нет.
    """
    # user_transcripts пустой
    mock_async_exists.return_value = False
    message = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": fake_user_id})(),
            "chat": type("C", (), {"id": 1})(),
            "text": "🗑 Удалить мой файл",
        },
    )()
    await transcribe_history.delete_my_file(message)
    mock_send_message.assert_awaited()
    args, kwargs = mock_send_message.call_args
    assert (
        "Нет файла для удаления." in args[1]
    ), "❌ При отсутствии файла не отправлено ожидаемое сообщение."
    if hasattr(user_transcripts_store, 'all'):
        all_store = await user_transcripts_store.all()
        assert fake_user_id not in all_store
