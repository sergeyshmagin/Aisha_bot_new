from aiogram import Router
from aiogram.types import CallbackQuery

fallback_router = Router()

@fallback_router.callback_query()
async def unknown_callback(call: CallbackQuery):
    """Универсальный обработчик для неизвестных/устаревших callback-запросов."""
    await call.answer("Действие не поддерживается или устарело.", show_alert=True) 