"""
Обработчик карточек аватаров
Выделен из app/handlers/avatar/gallery.py для соблюдения правила ≤500 строк
"""
from typing import List, Optional
from uuid import UUID
import logging

from aiogram.types import CallbackQuery, InputMediaPhoto, BufferedInputFile
from aiogram.fsm.context import FSMContext

from app.core.di import get_user_service, get_avatar_service
from app.services.storage import StorageService
from app.database.models import AvatarGender, AvatarStatus, AvatarTrainingType
from .keyboards import GalleryKeyboards
from .models import gallery_cache

logger = logging.getLogger(__name__)

class AvatarCardsHandler:
    """Обработчик карточек аватаров и навигации"""
    
    def __init__(self):
        self.keyboards = GalleryKeyboards()
    
    async def send_avatar_card(
        self, 
        callback: CallbackQuery, 
        user_id: UUID, 
        avatars: List, 
        avatar_idx: int = 0
    ) -> None:
        """Отправляет карточку аватара"""
        
        if not avatars or avatar_idx >= len(avatars):
            await callback.message.edit_text(
                "❌ Аватар не найден",
                reply_markup=self.keyboards.get_empty_gallery_keyboard()
            )
            return
        
        avatar = avatars[avatar_idx]
        
        # Формируем информацию об аватаре
        text = self._format_avatar_card_text(avatar, avatar_idx, len(avatars))
        
        keyboard = self.keyboards.get_avatar_card_keyboard(
            avatar_idx, 
            len(avatars), 
            str(avatar.id), 
            avatar.is_main,
            avatar.status
        )
        
        # Если у аватара есть превью фото, показываем его
        if avatar.photos and len(avatar.photos) > 0:
            try:
                photo_data = await self._load_avatar_preview(avatar)
                if photo_data:
                    await self._send_card_with_photo(callback, text, keyboard, photo_data)
                    return
            except Exception as e:
                logger.warning(f"Не удалось загрузить превью для аватара {avatar.id}: {e}")
        
        # Если превью нет, показываем только текст
        await self._send_card_text_only(callback, text, keyboard)

    async def handle_avatar_card_navigation(self, callback: CallbackQuery, direction: str):
        """Обрабатывает навигацию по карточкам аватаров"""
        try:
            user_telegram_id = callback.from_user.id
            current_idx = int(callback.data.split(":")[1])
            
            cache_data = await gallery_cache.get_avatars(user_telegram_id)
            if not cache_data:
                await callback.answer("❌ Данные галереи утеряны", show_alert=True)
                return
            
            total_avatars = cache_data["total_count"]
            
            if direction == "prev":
                new_idx = (current_idx - 1) % total_avatars  # Циклический переход
            else:  # "next"
                new_idx = (current_idx + 1) % total_avatars  # Циклический переход
            
            # Обновляем кэш
            await gallery_cache.update_current_idx(user_telegram_id, new_idx)
            
            # Получаем актуальные аватары из БД (кэш содержит только ID)
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                
            async with get_avatar_service() as avatar_service:
                avatars = await avatar_service.get_user_avatars_with_photos(user.id)
                
            await self.send_avatar_card(callback, user.id, avatars, new_idx)
            
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"Ошибка при навигации по аватарам: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    def _format_avatar_card_text(self, avatar, avatar_idx: int, total_avatars: int) -> str:
        """Форматирует текст карточки аватара"""
        name = avatar.name or "Без имени"
        
        # Правильное отображение пола
        gender_str = "👨 Мужской" if avatar.gender == AvatarGender.MALE else "👩 Женский"
        
        # Читаемые статусы
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
        
        return f"""🎭 **{name}**

{main_str}

📋 **Информация:**
• 🚻 Пол: {gender_str}
• 🎯 Тип: {type_str}
• 📊 Статус: {status_str}
• 📸 Фотографий: {photos_count}
• 📅 Создан: {created_str}

({avatar_idx + 1} из {total_avatars})"""

    async def _load_avatar_preview(self, avatar) -> Optional[bytes]:
        """Загружает превью аватара из MinIO"""
        try:
            storage = StorageService()
            first_photo = avatar.photos[0]
            return await storage.download_file("avatars", first_photo.minio_key)
        except Exception as e:
            logger.warning(f"Ошибка загрузки превью аватара: {e}")
            return None

    async def _send_card_with_photo(self, callback: CallbackQuery, text: str, keyboard, photo_data: bytes):
        """Отправляет карточку с фото"""
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

    async def _send_card_text_only(self, callback: CallbackQuery, text: str, keyboard):
        """Отправляет карточку только с текстом"""
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