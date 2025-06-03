"""
Обработчик загрузки и валидации фотографий
Выделен из app/handlers/avatar/photo_upload.py для соблюдения правила ≤500 строк
"""
import asyncio
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from uuid import UUID
from typing import List, Optional, Tuple
import logging

from app.core.di import get_user_service, get_avatar_service
from app.services.avatar.photo_service import PhotoUploadService
from app.database.models import AvatarPhoto
from .models import PhotoUploadConfig

logger = logging.getLogger(__name__)

# Кэш для блокировки загрузок
user_upload_locks = {}

class UploadHandler:
    """Обработчик загрузки и валидации фотографий"""
    
    def __init__(self):
        self.config = PhotoUploadConfig()
    
    async def handle_photo_upload(self, message: Message, state: FSMContext, bot: Bot) -> Tuple[bool, Optional[str], int]:
        """
        Обработка загрузки фотографий с валидацией
        
        Returns:
            tuple: (success, error_message, photos_count)
        """
        try:
            user_id = message.from_user.id
            
            # Получаем данные из состояния
            data = await state.get_data()
            avatar_id_str = data.get("avatar_id")
            
            if not avatar_id_str:
                return False, "Аватар не найден. Начните создание заново.", 0
            
            avatar_id = UUID(avatar_id_str)
            
            # Получаем пользователя
            user_db_id = await self._get_user_db_id(user_id)
            if not user_db_id:
                return False, "Пользователь не найден", 0
            
            # Проверяем лимиты
            photos_count = await self._check_photo_limits(avatar_id)
            if photos_count >= self.config.MAX_PHOTOS:
                return False, f"Достигнут лимит {self.config.MAX_PHOTOS} фотографий", photos_count
            
            # Защита от спама загрузок
            if user_id not in user_upload_locks:
                user_upload_locks[user_id] = asyncio.Lock()
            
            async with user_upload_locks[user_id]:
                # Показываем индикатор загрузки
                loading_msg = await message.answer("📤 Обрабатываю фотографию...")
                
                try:
                    # Скачиваем и обрабатываем фото
                    photo_bytes = await self._download_photo(bot, message)
                    
                    # Загружаем через PhotoUploadService
                    uploaded_photo = await self._upload_photo_to_service(
                        avatar_id, user_db_id, photo_bytes, message.photo[-1].file_id
                    )
                    
                    # Удаляем сообщение загрузки
                    await loading_msg.delete()
                    
                    # Удаляем исходное фото пользователя
                    await self._delete_original_photo(bot, message)
                    
                    # Получаем обновленное количество фото
                    _, photos_count = await self._get_avatar_photos(avatar_id)
                    
                    logger.info(f"Загружено фото {uploaded_photo.id} для аватара {avatar_id}, всего: {photos_count}")
                    return True, None, photos_count
                    
                except Exception as upload_error:
                    await loading_msg.delete()
                    # Показываем фото с ошибкой валидации
                    await self._handle_upload_error_with_photo(bot, message, upload_error, photo_bytes)
                    return False, str(upload_error), photos_count
                    
        except Exception as e:
            logger.exception(f"Критическая ошибка при загрузке фото: {e}")
            return False, "Произошла критическая ошибка. Попробуйте позже.", 0

    async def _get_user_db_id(self, user_id: int) -> Optional[UUID]:
        """Получает ID пользователя из БД"""
        try:
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_id)
                return user.id if user else None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None

    async def _check_photo_limits(self, avatar_id: UUID) -> int:
        """Проверяет лимиты фотографий и возвращает текущее количество"""
        try:
            async with get_avatar_service() as avatar_service:
                photos, total = await avatar_service.get_avatar_photos(avatar_id)
                return total
        except Exception as e:
            logger.error(f"Ошибка проверки лимитов: {e}")
            return 0

    async def _download_photo(self, bot: Bot, message: Message) -> bytes:
        """Скачивает фото из Telegram"""
        photo = message.photo[-1]  # Самое большое разрешение
        file_info = await bot.get_file(photo.file_id)
        file_data = await bot.download_file(file_info.file_path)
        return file_data.read()

    async def _upload_photo_to_service(self, avatar_id: UUID, user_id: UUID, photo_bytes: bytes, file_id: str):
        """Загружает фото через PhotoUploadService"""
        async with get_avatar_service() as avatar_service:
            session = avatar_service.session
            photo_service = PhotoUploadService(session)
            return await photo_service.upload_photo(
                avatar_id=avatar_id,
                user_id=user_id,
                photo_data=photo_bytes,
                filename=f"telegram_photo_{file_id}.jpg"
            )

    async def _get_avatar_photos(self, avatar_id: UUID) -> Tuple[List[AvatarPhoto], int]:
        """Получает фотографии аватара"""
        async with get_avatar_service() as avatar_service:
            return await avatar_service.get_avatar_photos(avatar_id)

    async def _delete_original_photo(self, bot: Bot, message: Message):
        """Удаляет исходное фото пользователя из чата"""
        try:
            await bot.delete_message(message.chat.id, message.message_id)
            logger.debug(f"Удалено исходное фото пользователя: {message.message_id}")
        except Exception as e:
            logger.warning(f"Не удалось удалить исходное фото: {e}")

    async def _handle_upload_error_with_photo(self, bot: Bot, message: Message, error: Exception, photo_bytes: bytes):
        """Обрабатывает ошибки загрузки фото с показом самого фото"""
        try:
            # Удаляем исходное фото пользователя
            await self._delete_original_photo(bot, message)
            
            # Определяем текст ошибки
            error_text = self._format_error_message(str(error))
            
            # Создаем клавиатуру с кнопкой "Понятно"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💡 Понятно", callback_data="delete_error_photo")]
            ])
            
            # Создаем caption с ошибкой и советами
            caption = f"""❌ Фото не принято: {error_text}

📸 Совет: Используйте четкие фото без фильтров, хорошего разрешения и качества.

💡 Рекомендации:
• Размер от {self.config.MIN_RESOLUTION}×{self.config.MIN_RESOLUTION} пикселей
• Формат JPG или PNG
• Без размытия и фильтров
• Хорошее освещение"""
            
            # Отправляем фото с ошибкой и кнопкой
            photo_input = BufferedInputFile(photo_bytes, filename="rejected_photo.jpg")
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=photo_input,
                caption=caption,
                reply_markup=keyboard
            )
            
            logger.warning(f"Показано фото с ошибкой валидации: {error}")
            
        except Exception as e:
            logger.exception(f"Ошибка при показе фото с ошибкой: {e}")
            # Fallback на обычное текстовое сообщение
            await message.answer(f"❌ Ошибка загрузки\n\n{str(error)}")

    def _format_error_message(self, error_msg: str) -> str:
        """Форматирует сообщение об ошибке для пользователя"""
        error_msg_lower = error_msg.lower()
        
        if "не прошло валидацию" in error_msg_lower:
            if "размер" in error_msg_lower:
                return f"Разрешение слишком маленькое (минимум {self.config.MIN_RESOLUTION}×{self.config.MIN_RESOLUTION} пикселей)"
            elif "дубликат" in error_msg_lower or "уже загружено" in error_msg_lower:
                return "Это фото уже было загружено ранее"
            elif "формат" in error_msg_lower:
                return "Неподдерживаемый формат (используйте JPG или PNG)"
            elif "размер файла" in error_msg_lower:
                return f"Файл слишком большой (максимум {self.config.MAX_FILE_SIZE // (1024*1024)}MB)"
            else:
                return error_msg.replace("Фото не прошло валидацию: ", "")
        elif "превышен лимит" in error_msg_lower:
            return f"Достигнут лимит {self.config.MAX_PHOTOS} фотографий"
        else:
            return "Неизвестная ошибка загрузки" 