"""
LEGACY: бизнес-ассистент (устаревший код, не использовать, не импортировать)
Весь код закомментирован для предотвращения случайного использования.
"""
# --- LEGACY: файл переименован в business.py.LEGACY, не использовать ---
# from aiogram import Router, F
# from aiogram.types import Message, CallbackQuery
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import State, StatesGroup
# from aisha_v2.app.keyboards.business import get_business_menu
# from aisha_v2.app.keyboards.main import get_main_menu
# from aisha_v2.app.core.di import get_user_service
# from aisha_v2.app.services.audio.service import AudioProcessingService
# from aisha_v2.app.services.text_processing import TextProcessingService
# from aisha_v2.app.core.logger import get_logger
# ...
# Весь остальной код файла закомментирован как LEGACY

"""
Обработчики бизнес-ассистента
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aisha_v2.app.keyboards.business import get_business_menu
from aisha_v2.app.keyboards.main import get_main_menu
from aisha_v2.app.core.di import get_user_service
# from aisha_v2.app.services.audio.service import AudioProcessingService  # LEGACY: удалено
from aisha_v2.app.services.text_processing import TextProcessingService
from aisha_v2.app.core.logger import get_logger

logger = get_logger(__name__)
router = Router()

class BusinessStates(StatesGroup):
    """Состояния для бизнес-ассистента"""
    waiting_for_audio = State()
    waiting_for_text = State()
    processing = State()

@router.callback_query(F.data == "business_audio")
async def process_audio(call: CallbackQuery, state: FSMContext):
    """
    Обработчик для работы с аудио
    """
    await call.answer("🎤 Отправьте аудио для обработки...", show_alert=False)
    await state.set_state(BusinessStates.waiting_for_audio)
    new_text = (
        "🎤 Отправьте аудио для обработки\n\n"
        "Поддерживаемые форматы: MP3, WAV, OGG\n"
        "Максимальный размер: 50MB"
    )
    # Редактируем только если текст отличается
    if call.message.text != new_text:
        await call.message.edit_text(
            new_text,
            reply_markup=get_business_menu()
        )

@router.callback_query(F.data == "business_text")
async def process_text(call: CallbackQuery, state: FSMContext):
    """
    Обработчик для работы с текстом
    """
    await call.answer("📝 Отправьте текст для обработки...", show_alert=False)
    await state.set_state(BusinessStates.waiting_for_text)
    await call.message.edit_text(
        "📝 Отправьте текст для обработки\n\n"
        "Поддерживаемые языки: русский, английский\n"
        "Максимальная длина: 4000 символов",
        reply_markup=get_business_menu()
    )

@router.message(BusinessStates.waiting_for_audio)
async def handle_audio(message: Message, state: FSMContext):
    """
    Обрабатывает полученное аудио
    """
    try:
        if not message.audio and not message.voice:
            await message.answer(
                "❌ Пожалуйста, отправьте аудио или голосовое сообщение",
                reply_markup=get_business_menu()
            )
            return

        await state.set_state(BusinessStates.processing)
        await message.answer("⏳ Обрабатываю аудио...")

        # audio_service = AudioProcessingService()
        # result = await audio_service.process_audio(message.audio or message.voice, message.from_user.id, message.bot)
        pass

        await state.clear()
        # --- LEGACY: отправка технических деталей результата пользователю ---
        # await message.answer(
        #     "✅ Аудио обработано!\n\n"
        #     f"Результат: {result}",
        #     reply_markup=get_business_menu()
        # )
        # --- END LEGACY ---
        # Используйте TranscriptProcessingHandler для корректного UX

    except Exception as e:
        logger.exception("Ошибка при обработке аудио")
        await state.clear()
        await message.answer(
            "❌ Произошла ошибка при обработке аудио",
            reply_markup=get_business_menu()
        )

@router.message(BusinessStates.waiting_for_text)
async def handle_text(message: Message, state: FSMContext):
    """
    Обрабатывает полученный текст
    """
    try:
        if not message.text:
            await message.answer(
                "❌ Пожалуйста, отправьте текст",
                reply_markup=get_business_menu()
            )
            return

        await state.set_state(BusinessStates.processing)
        await message.answer("⏳ Обрабатываю текст...")

        async with TextProcessingService() as text_service:
            # TODO: Реализовать обработку текста
            # result = await text_service.process_text(message.text)
            pass

        await state.clear()
        await message.answer(
            "✅ Текст обработан!\n\n"
            f"Результат: {result}",
            reply_markup=get_business_menu()
        )

    except Exception as e:
        logger.exception("Ошибка при обработке текста")
        await state.clear()
        await message.answer(
            "❌ Произошла ошибка при обработке текста",
            reply_markup=get_business_menu()
        ) 