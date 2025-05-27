"""
Галерея аватаров - просмотр, редактирование и удаление аватаров
Реализация на основе archive/aisha_v1/frontend_bot/handlers/avatar/gallery.py
"""
import asyncio
import io
from typing import Optional, List
from uuid import UUID

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, BufferedInputFile
from aiogram.fsm.context import FSMContext

from app.core.di import get_user_service, get_avatar_service
from app.services.storage import StorageService
from app.core.logger import get_logger
from app.handlers.state import AvatarStates
from app.database.models import AvatarGender, AvatarStatus, AvatarTrainingType

logger = get_logger(__name__)
router = Router()

# Кэш галереи для отслеживания текущих позиций
gallery_cache = {}


def get_avatar_card_keyboard(avatar_idx: int, total_avatars: int, avatar_id: str, is_main: bool = False, avatar_status = None) -> InlineKeyboardMarkup:
    """Создает клавиатуру для карточки аватара"""
    
    buttons = []
    
    # Навигация (если больше одного аватара)
    if total_avatars > 1:
        nav_buttons = []
        if avatar_idx > 0:
            nav_buttons.append(
                InlineKeyboardButton(text="⬅️", callback_data=f"avatar_card_prev:{avatar_idx}")
            )
        
        nav_buttons.append(
            InlineKeyboardButton(text=f"{avatar_idx + 1}/{total_avatars}", callback_data="noop")
        )
        
        if avatar_idx < total_avatars - 1:
            nav_buttons.append(
                InlineKeyboardButton(text="➡️", callback_data=f"avatar_card_next:{avatar_idx}")
            )
        
        buttons.append(nav_buttons)
    
    # Действия с аватаром
    action_buttons = []
    
    # Кнопка "Сделать основным" только если не основной
    if not is_main:
        action_buttons.append(
            InlineKeyboardButton(text="⭐ Основной", callback_data=f"avatar_set_main:{avatar_id}")
        )
    else:
        action_buttons.append(
            InlineKeyboardButton(text="⭐ Основной", callback_data="noop")
        )
    
    # ИСПРАВЛЕНИЕ: Кнопка "Фото" только для черновиков и загрузки фото
    # После отправки на обучение пользователю не нужно пересматривать фото
    if avatar_status in [AvatarStatus.DRAFT, AvatarStatus.PHOTOS_UPLOADING]:
        action_buttons.append(
            InlineKeyboardButton(text="📸 Фото", callback_data=f"avatar_view_photos:{avatar_id}")
        )
    
    # Удаление
    action_buttons.append(
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"avatar_delete:{avatar_id}")
    )
    
    buttons.append(action_buttons)
    
    # Возврат в меню
    buttons.append([
        InlineKeyboardButton(text="◀️ В меню аватаров", callback_data="avatar_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_avatar_photo_gallery_keyboard(photo_idx: int, total_photos: int, avatar_id: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру для галереи фотографий аватара"""
    
    buttons = []
    
    # Навигация по фото
    if total_photos > 1:
        nav_buttons = []
        if photo_idx > 0:
            nav_buttons.append(
                InlineKeyboardButton(text="⬅️", callback_data=f"avatar_photo_prev:{avatar_id}:{photo_idx}")
            )
        
        nav_buttons.append(
            InlineKeyboardButton(text=f"{photo_idx + 1}/{total_photos}", callback_data="noop")
        )
        
        if photo_idx < total_photos - 1:
            nav_buttons.append(
                InlineKeyboardButton(text="➡️", callback_data=f"avatar_photo_next:{avatar_id}:{photo_idx}")
            )
        
        buttons.append(nav_buttons)
    
    # Возврат к карточке аватара
    buttons.append([
        InlineKeyboardButton(text="◀️ К аватару", callback_data=f"avatar_view_card:{avatar_id}")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def send_avatar_card(
    callback: CallbackQuery, 
    user_id: UUID, 
    avatars: List, 
    avatar_idx: int = 0
) -> None:
    """Отправляет карточку аватара"""
    
    if not avatars or avatar_idx >= len(avatars):
        await callback.message.edit_text(
            "❌ Аватар не найден",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="◀️ В меню", callback_data="avatar_menu")
            ]])
        )
        return
    
    avatar = avatars[avatar_idx]
    
    # Формируем информацию об аватаре
    name = avatar.name or "Без имени"
    
    # ИСПРАВЛЕНИЕ 2: Правильное отображение пола (исправлена логика)
    gender_str = "👨 Мужской" if avatar.gender == AvatarGender.MALE else "👩 Женский"
    
    # ИСПРАВЛЕНИЕ 3: Читаемые статусы вместо enum значений
    status_map = {
        AvatarStatus.DRAFT: "📝 Черновик",
        AvatarStatus.PHOTOS_UPLOADING: "📤 Загрузка фото",
        AvatarStatus.READY_FOR_TRAINING: "⏳ Готов к обучению", 
        AvatarStatus.TRAINING: "🔄 Обучается",
        AvatarStatus.COMPLETED: "✅ Готов",
        AvatarStatus.ERROR: "❌ Ошибка",
        AvatarStatus.CANCELLED: "⏹️ Отменен"
    }
    status_str = status_map.get(avatar.status, str(avatar.status))
    
    # Правильное отображение типа обучения
    type_map = {
        AvatarTrainingType.PORTRAIT: "🎭 Портретный",
        AvatarTrainingType.STYLE: "🎨 Художественный"
    }
    type_str = type_map.get(avatar.training_type, str(avatar.training_type))
    
    # Дата создания
    created_str = avatar.created_at.strftime("%d.%m.%Y %H:%M") if avatar.created_at else "—"
    
    # Количество фотографий
    photos_count = len(avatar.photos) if avatar.photos else 0
    
    main_str = "⭐ Основной аватар" if avatar.is_main else ""
    
    text = f"""
🎭 **{name}**

{main_str}

📋 **Информация:**
• 🚻 Пол: {gender_str}
• 🎯 Тип: {type_str}
• 📊 Статус: {status_str}
• 📸 Фотографий: {photos_count}
• 📅 Создан: {created_str}

({avatar_idx + 1} из {len(avatars)})
"""
    
    keyboard = get_avatar_card_keyboard(
        avatar_idx, 
        len(avatars), 
        str(avatar.id), 
        avatar.is_main,
        avatar.status
    )
    
    # Если у аватара есть превью фото, показываем его
    if avatar.photos and len(avatar.photos) > 0:
        try:
            storage = StorageService()
            first_photo = avatar.photos[0]
            photo_data = await storage.download_file("avatars", first_photo.minio_key)
            
            if photo_data:
                # Используем BufferedInputFile для работы с байтами
                photo_file = BufferedInputFile(photo_data, filename="preview.jpg")
                
                # Проверяем тип текущего сообщения
                if callback.message.photo:
                    # Если сообщение уже содержит фото, используем edit_media
                    await callback.message.edit_media(
                        media=InputMediaPhoto(media=photo_file, caption=text, parse_mode="Markdown"),
                        reply_markup=keyboard
                    )
                else:
                    # Если сообщение текстовое, удаляем его и отправляем новое с фото
                    try:
                        await callback.message.delete()
                    except Exception:
                        pass  # Игнорируем ошибки удаления
                    
                    await callback.message.answer_photo(
                        photo=photo_file,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                return
        except Exception as e:
            logger.warning(f"Не удалось загрузить превью для аватара {avatar.id}: {e}")
    
    # Если превью нет, показываем только текст
    if callback.message.photo:
        # Если текущее сообщение с фото, а превью нет - удаляем и отправляем текст
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        await callback.message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        # Если текущее сообщение текстовое - просто редактируем
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


@router.callback_query(F.data == "avatar_gallery")
async def show_avatar_gallery(callback: CallbackQuery, state: FSMContext):
    """Показывает галерею аватаров пользователя"""
    try:
        user_telegram_id = callback.from_user.id
        
        # Получаем пользователя
        user_id = None
        async with get_user_service() as user_service:
            user = await user_service.get_user_by_telegram_id(user_telegram_id)
            if not user:
                await callback.message.edit_text("❌ Пользователь не найден")
                return
            
            # Сохраняем user_id перед закрытием сессии
            user_id = user.id
        
        # Получаем аватары пользователя
        async with get_avatar_service() as avatar_service:
            avatars = await avatar_service.get_user_avatars_with_photos(user_id)
        
        if not avatars:
            # Если аватаров нет
            text = """
🎭 **Мои аватары**

🔍 У вас пока нет созданных аватаров

🆕 Создайте свой первый аватар чтобы:
• 🎨 Генерировать уникальные изображения
• 🎭 Создавать персональные портреты
• ✨ Экспериментировать со стилями

👆 Нажмите "Создать аватар" чтобы начать!
"""
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🆕 Создать аватар", callback_data="avatar_create")],
                [InlineKeyboardButton(text="◀️ Главное меню", callback_data="avatar_menu")]
            ])
            
            # Проверяем тип сообщения и выбираем правильный метод
            if callback.message.photo:
                # Если сообщение содержит фото, удаляем его и отправляем текстовое
                try:
                    await callback.message.delete()
                except Exception:
                    pass  # Игнорируем ошибки удаления
                
                await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                # Если сообщение текстовое, просто редактируем
                await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
            return
        
        # Сохраняем список аватаров в кэш
        gallery_cache[user_telegram_id] = {
            "avatars": avatars,
            "current_idx": 0
        }
        
        # Показываем первый аватар
        await send_avatar_card(callback, user.id, avatars, 0)
        
        logger.info(f"Пользователь {user_telegram_id} открыл галерею аватаров ({len(avatars)} шт.)")
        
    except Exception as e:
        logger.exception(f"Ошибка при показе галереи аватаров: {e}")
        await callback.answer("❌ Произошла ошибка при загрузке галереи", show_alert=True)


@router.callback_query(F.data.startswith("avatar_card_prev:"))
async def handle_avatar_card_prev(callback: CallbackQuery, state: FSMContext):
    """Переход к предыдущему аватару"""
    try:
        user_telegram_id = callback.from_user.id
        current_idx = int(callback.data.split(":")[1])
        
        cache_data = gallery_cache.get(user_telegram_id)
        if not cache_data:
            await callback.answer("❌ Данные галереи утеряны", show_alert=True)
            return
        
        avatars = cache_data["avatars"]
        new_idx = (current_idx - 1) % len(avatars)  # Циклический переход
        
        # Обновляем кэш
        gallery_cache[user_telegram_id]["current_idx"] = new_idx
        
        # Показываем новый аватар
        async with get_user_service() as user_service:
            user = await user_service.get_user_by_telegram_id(user_telegram_id)
            await send_avatar_card(callback, user.id, avatars, new_idx)
        
        await callback.answer()
        
    except Exception as e:
        logger.exception(f"Ошибка при переходе к предыдущему аватару: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("avatar_card_next:"))
async def handle_avatar_card_next(callback: CallbackQuery, state: FSMContext):
    """Переход к следующему аватару"""
    try:
        user_telegram_id = callback.from_user.id
        current_idx = int(callback.data.split(":")[1])
        
        cache_data = gallery_cache.get(user_telegram_id)
        if not cache_data:
            await callback.answer("❌ Данные галереи утеряны", show_alert=True)
            return
        
        avatars = cache_data["avatars"]
        new_idx = (current_idx + 1) % len(avatars)  # Циклический переход
        
        # Обновляем кэш
        gallery_cache[user_telegram_id]["current_idx"] = new_idx
        
        # Показываем новый аватар
        async with get_user_service() as user_service:
            user = await user_service.get_user_by_telegram_id(user_telegram_id)
            await send_avatar_card(callback, user.id, avatars, new_idx)
        
        await callback.answer()
        
    except Exception as e:
        logger.exception(f"Ошибка при переходе к следующему аватару: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("avatar_set_main:"))
async def handle_set_main_avatar(callback: CallbackQuery, state: FSMContext):
    """Устанавливает аватар как основной"""
    try:
        user_telegram_id = callback.from_user.id
        avatar_id = UUID(callback.data.split(":")[1])
        
        # Получаем пользователя
        user_id = None
        async with get_user_service() as user_service:
            user = await user_service.get_user_by_telegram_id(user_telegram_id)
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return
            
            # Сохраняем user_id перед закрытием сессии
            user_id = user.id
        
        # Устанавливаем основной аватар
        async with get_avatar_service() as avatar_service:
            success = await avatar_service.set_main_avatar(user.id, avatar_id)
            
            if success:
                # Обновляем кэш
                cache_data = gallery_cache.get(user_telegram_id)
                if cache_data:
                    # Перезагружаем аватары с обновленными данными
                    avatars = await avatar_service.get_user_avatars_with_photos(user.id)
                    cache_data["avatars"] = avatars
                    
                    # Находим индекс установленного аватара
                    current_idx = 0
                    for i, avatar in enumerate(avatars):
                        if avatar.id == avatar_id:
                            current_idx = i
                            break
                    
                    cache_data["current_idx"] = current_idx
                    
                    # Обновляем карточку
                    await send_avatar_card(callback, user.id, avatars, current_idx)
                
                await callback.answer("⭐ Аватар установлен как основной!")
            else:
                await callback.answer("❌ Не удалось установить аватар как основной", show_alert=True)
        
    except Exception as e:
        logger.exception(f"Ошибка при установке основного аватара: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("avatar_delete:"))
async def handle_delete_avatar(callback: CallbackQuery, state: FSMContext):
    """Удаляет аватар"""
    try:
        user_telegram_id = callback.from_user.id
        avatar_id = UUID(callback.data.split(":")[1])
        
        # Получаем пользователя
        user_id = None
        async with get_user_service() as user_service:
            user = await user_service.get_user_by_telegram_id(user_telegram_id)
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return
            
            # Сохраняем user_id перед закрытием сессии
            user_id = user.id
        
        # Удаляем аватар
        async with get_avatar_service() as avatar_service:
            success = await avatar_service.delete_avatar_completely(avatar_id)
            
            if success:
                # Обновляем галерею
                avatars = await avatar_service.get_user_avatars_with_photos(user.id)
                
                if avatars:
                    # Если остались аватары, показываем первый
                    gallery_cache[user_telegram_id] = {
                        "avatars": avatars,
                        "current_idx": 0
                    }
                    await send_avatar_card(callback, user.id, avatars, 0)
                else:
                    # Если аватаров не осталось, показываем красивую заглушку
                    text = """
🎭 **Мои аватары**

🔍 У вас больше нет аватаров

🆕 Создайте новый аватар чтобы:
• 🎨 Генерировать уникальные изображения
• 🎭 Создавать персональные портреты
• ✨ Экспериментировать со стилями

👆 Нажмите "Создать аватар" чтобы начать!
"""
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🆕 Создать аватар", callback_data="avatar_create")],
                        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="avatar_menu")]
                    ])
                    
                    # Проверяем тип сообщения и выбираем правильный метод
                    if callback.message.photo:
                        # Если сообщение содержит фото, удаляем его и отправляем текстовое
                        try:
                            await callback.message.delete()
                        except Exception:
                            pass  # Игнорируем ошибки удаления
                        
                        await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
                    else:
                        # Если сообщение текстовое, просто редактируем
                        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
                
                await callback.answer("🗑️ Аватар удален")
            else:
                await callback.answer("❌ Не удалось удалить аватар", show_alert=True)
        
    except Exception as e:
        logger.exception(f"Ошибка при удалении аватара: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("avatar_view_photos:"))
async def handle_view_avatar_photos(callback: CallbackQuery, state: FSMContext):
    """Показывает фотографии аватара"""
    try:
        avatar_id = UUID(callback.data.split(":")[1])
        
        # Получаем аватар с фотографиями
        async with get_avatar_service() as avatar_service:
            avatar = await avatar_service.get_avatar(avatar_id)
            
            if not avatar or not avatar.photos:
                await callback.answer("📸 У аватара нет фотографий", show_alert=True)
                return
        
        # Сохраняем в кэш для навигации
        user_telegram_id = callback.from_user.id
        gallery_cache[f"{user_telegram_id}_photos_{avatar_id}"] = {
            "avatar": avatar,
            "current_photo_idx": 0
        }
        
        # Показываем первое фото
        await show_avatar_photo(callback, avatar, 0)
        
    except Exception as e:
        logger.exception(f"Ошибка при просмотре фотографий аватара: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


async def show_avatar_photo(callback: CallbackQuery, avatar, photo_idx: int):
    """Показывает конкретное фото аватара"""
    try:
        if not avatar.photos or photo_idx >= len(avatar.photos):
            await callback.answer("📸 Фото не найдено", show_alert=True)
            return
        
        photo = avatar.photos[photo_idx]
        
        # Загружаем фото
        storage = StorageService()
        photo_data = await storage.download_file("avatars", photo.minio_key)
        
        if not photo_data:
            await callback.answer("❌ Не удалось загрузить фото", show_alert=True)
            return
        
        # Информация о фото
        text = f"""
🎭 **{avatar.name or 'Без имени'}**

📸 Фото {photo_idx + 1} из {len(avatar.photos)}

📅 Загружено: {photo.created_at.strftime("%d.%m.%Y %H:%M") if photo.created_at else "—"}
"""
        
        keyboard = get_avatar_photo_gallery_keyboard(
            photo_idx, 
            len(avatar.photos), 
            str(avatar.id)
        )
        
        # ИСПРАВЛЕНИЕ: Используем BufferedInputFile для корректной передачи байтов
        photo_file = BufferedInputFile(photo_data, filename=f"photo_{photo_idx + 1}.jpg")
        await callback.message.edit_media(
            media=InputMediaPhoto(media=photo_file, caption=text, parse_mode="Markdown"),
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.exception(f"Ошибка при показе фото аватара: {e}")
        await callback.answer("❌ Произошла ошибка при загрузке фото", show_alert=True)


@router.callback_query(F.data.startswith("avatar_photo_prev:"))
@router.callback_query(F.data.startswith("avatar_photo_next:"))
async def handle_photo_navigation(callback: CallbackQuery, state: FSMContext):
    """Навигация по фотографиям аватара"""
    try:
        parts = callback.data.split(":")
        direction = parts[0].split("_")[-1]  # "prev" или "next"
        avatar_id = UUID(parts[1])
        current_idx = int(parts[2])
        
        user_telegram_id = callback.from_user.id
        cache_key = f"{user_telegram_id}_photos_{avatar_id}"
        cache_data = gallery_cache.get(cache_key)
        
        if not cache_data:
            await callback.answer("❌ Данные фотогалереи утеряны", show_alert=True)
            return
        
        avatar = cache_data["avatar"]
        
        if direction == "prev":
            new_idx = (current_idx - 1) % len(avatar.photos)
        else:  # "next"
            new_idx = (current_idx + 1) % len(avatar.photos)
        
        # Обновляем кэш
        cache_data["current_photo_idx"] = new_idx
        
        # Показываем новое фото
        await show_avatar_photo(callback, avatar, new_idx)
        
        await callback.answer()
        
    except Exception as e:
        logger.exception(f"Ошибка при навигации по фотографиям: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("avatar_view_card:"))
async def handle_view_avatar_card(callback: CallbackQuery, state: FSMContext):
    """Возврат к карточке аватара из фотогалереи"""
    try:
        avatar_id = UUID(callback.data.split(":")[1])
        user_telegram_id = callback.from_user.id
        
        # Очищаем кэш фотогалереи
        cache_key = f"{user_telegram_id}_photos_{avatar_id}"
        if cache_key in gallery_cache:
            del gallery_cache[cache_key]
        
        # Получаем данные основной галереи
        cache_data = gallery_cache.get(user_telegram_id)
        if not cache_data:
            # Если кэша нет, показываем галерею заново
            await show_avatar_gallery(callback, state)
            return
        
        avatars = cache_data["avatars"]
        
        # Находим индекс аватара
        avatar_idx = 0
        for i, avatar in enumerate(avatars):
            if avatar.id == avatar_id:
                avatar_idx = i
                break
        
        # Обновляем кэш и показываем карточку
        cache_data["current_idx"] = avatar_idx
        
        async with get_user_service() as user_service:
            user = await user_service.get_user_by_telegram_id(user_telegram_id)
            user_id = user.id
            
        await send_avatar_card(callback, user_id, avatars, avatar_idx)
        
        await callback.answer()
        
    except Exception as e:
        logger.exception(f"Ошибка при возврате к карточке аватара: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    """Обработка пустых callback'ов (для неактивных кнопок)"""
    await callback.answer() 