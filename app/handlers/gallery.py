"""
Обработчики галереи
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.keyboards.gallery import get_gallery_menu
from app.keyboards.main import get_main_menu
from app.core.di import get_user_service
from app.services.storage import StorageService
from app.core.logger import get_logger

logger = get_logger(__name__)
router = Router()

class GalleryStates(StatesGroup):
    """Состояния для галереи"""
    waiting_for_image = State()
    waiting_for_folder = State()
    processing = State()

@router.callback_query(F.data == "gallery_my_images")
async def show_my_images(call: CallbackQuery):
    """
    Показывает изображения пользователя
    """
    try:
        async with get_user_service() as user_service:
            user = await user_service.get_user_by_telegram_id(call.from_user.id)
            if not user:
                await call.answer("❌ Пользователь не найден", show_alert=True)
                return

            async with StorageService() as storage:
                images = await storage.get_user_images(user.id)
                
                if not images:
                    await call.answer("📭 У вас пока нет изображений", show_alert=True)
                    return

                # TODO: Реализовать пагинацию изображений
                await call.message.edit_text(
                    "🖼 Ваши изображения\n\n"
                    "Выберите изображение для просмотра:",
                    reply_markup=get_gallery_menu()
                )

    except Exception as e:
        logger.exception("Ошибка при получении изображений")
        await call.answer("❌ Ошибка при получении изображений", show_alert=True)

@router.callback_query(F.data == "gallery_upload")
async def upload_image(call: CallbackQuery, state: FSMContext):
    """
    Начинает процесс загрузки изображения
    """
    await call.answer("📤 Отправьте изображение для загрузки...", show_alert=False)
    await state.set_state(GalleryStates.waiting_for_image)
    await call.message.edit_text(
        "📤 Отправьте изображение для загрузки\n\n"
        "Поддерживаемые форматы: JPG, PNG, WEBP\n"
        "Максимальный размер: 10MB",
        reply_markup=get_gallery_menu()
    )

@router.callback_query(F.data == "gallery_search")
async def search_images(call: CallbackQuery):
    """
    Показывает поиск изображений
    """
    await call.answer("🔍 Поиск изображений", show_alert=False)
    await call.message.edit_text(
        "🔍 Поиск изображений\n\n"
        "Введите поисковый запрос:",
        reply_markup=get_gallery_menu()
    )

@router.callback_query(F.data == "gallery_folders")
async def show_folders(call: CallbackQuery):
    """
    Показывает папки пользователя
    """
    try:
        async with get_user_service() as user_service:
            user = await user_service.get_user_by_telegram_id(call.from_user.id)
            if not user:
                await call.answer("❌ Пользователь не найден", show_alert=True)
                return

            async with StorageService() as storage:
                folders = await storage.get_user_folders(user.id)
                
                if not folders:
                    await call.answer("📁 У вас пока нет папок", show_alert=True)
                    return

                # TODO: Реализовать отображение папок
                await call.message.edit_text(
                    "📁 Ваши папки\n\n"
                    "Выберите папку для просмотра:",
                    reply_markup=get_gallery_menu()
                )

    except Exception as e:
        logger.exception("Ошибка при получении папок")
        await call.answer("❌ Ошибка при получении папок", show_alert=True)

@router.message(GalleryStates.waiting_for_image)
async def handle_image(message: Message, state: FSMContext):
    """
    Обрабатывает полученное изображение
    """
    try:
        if not message.photo:
            await message.answer(
                "❌ Пожалуйста, отправьте изображение",
                reply_markup=get_gallery_menu()
            )
            return

        await state.set_state(GalleryStates.processing)
        await message.answer("⏳ Загружаю изображение...")

        async with StorageService() as storage:
            # TODO: Реализовать загрузку изображения
            result = await storage.upload_image(
                user_id=message.from_user.id,
                image=message.photo[-1]
            )

        await state.clear()
        await message.answer(
            "✅ Изображение загружено!\n\n"
            f"ID: {result.id}\n"
            f"Размер: {result.size}",
            reply_markup=get_gallery_menu()
        )

    except Exception as e:
        logger.exception("Ошибка при загрузке изображения")
        await state.clear()
        await message.answer(
            "❌ Произошла ошибка при загрузке изображения",
            reply_markup=get_gallery_menu()
        ) 