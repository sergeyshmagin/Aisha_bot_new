# --- LEGACY: устаревший обработчик меню, не использовать ---
# Вся логика перенесена в main_menu.py
# Файл сохранён для истории, не импортировать!

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aisha_v2.app.handlers.audio import AudioHandler

router = Router()

def setup_menu_handlers(audio_handler: AudioHandler):
    @router.message(F.text == "🎤 Аудио")
    async def menu_audio(message: Message, state: FSMContext):
        await audio_handler.handle_audio_start(message, state) 