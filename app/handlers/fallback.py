from aiogram import Router, F
from aiogram.types import CallbackQuery

fallback_router = Router()

@fallback_router.callback_query(    F.data.startswith("business_") |     F.data.startswith("old_"))
async def fallback_callback(call: CallbackQuery):
    await call.answer("Это действие устарело. Пожалуйста, используйте новое меню.", show_alert=True) 