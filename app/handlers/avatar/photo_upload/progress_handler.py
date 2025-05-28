"""
Обработчик прогресса и UI обновлений
Выделен из app/handlers/avatar/photo_upload.py для соблюдения правила ≤500 строк
"""
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from uuid import UUID
from typing import Dict, List, Optional
import logging

from app.core.di import get_avatar_service, get_user_service
from app.database.models import AvatarPhoto
from app.keyboards.photo_upload import get_photo_upload_keyboard, get_training_start_keyboard
from app.core.config import settings
from .models import PhotoUploadConfig

logger = logging.getLogger(__name__)

# Кэш для отслеживания сообщений прогресса
user_progress_messages = {}

class ProgressHandler:
    """Обработчик прогресса загрузки и UI обновлений"""
    
    def __init__(self):
        self.config = PhotoUploadConfig()
    
    async def show_upload_progress(self, message: Message, photos_count: int, avatar_id: UUID):
        """Показывает прогресс загрузки фотографий"""
        try:
            user_id = message.from_user.id
            
            # Формируем текст прогресса
            progress_text = self._get_progress_text(photos_count)
            
            # Создаем клавиатуру с действиями
            keyboard = get_photo_upload_keyboard(photos_count, self.config.MIN_PHOTOS, self.config.MAX_PHOTOS)
            
            # Отправляем или обновляем сообщение прогресса
            if user_id in user_progress_messages:
                try:
                    # Обновляем существующее сообщение
                    await user_progress_messages[user_id].edit_text(
                        text=progress_text,
                        reply_markup=keyboard
                    )
                except Exception:
                    # Если не удалось обновить, отправляем новое
                    progress_msg = await message.answer(progress_text, reply_markup=keyboard)
                    user_progress_messages[user_id] = progress_msg
            else:
                # Отправляем новое сообщение
                progress_msg = await message.answer(progress_text, reply_markup=keyboard)
                user_progress_messages[user_id] = progress_msg
            
            logger.debug(f"Показан прогресс загрузки: {photos_count}/{self.config.MAX_PHOTOS}")
            
        except Exception as e:
            logger.exception(f"Ошибка при показе прогресса: {e}")

    async def update_gallery_if_open(self, user_id: int, avatar_id: UUID, photos: List[AvatarPhoto]):
        """Обновляет галерею если она открыта у пользователя"""
        try:
            # Импортируем здесь чтобы избежать циклических импортов
            from .gallery_handler import user_gallery_cache
            
            if user_id in user_gallery_cache:
                cache = user_gallery_cache[user_id]
                if cache["avatar_id"] == avatar_id:
                    # Обновляем кэш с новыми фотографиями
                    cache["photos"] = photos
                    logger.debug(f"Обновлен кэш галереи для пользователя {user_id}")
                    
        except Exception as e:
            logger.warning(f"Ошибка при обновлении галереи: {e}")

    async def show_training_confirmation(self, callback: CallbackQuery, state: FSMContext):
        """Показывает экран подтверждения перед началом обучения"""
        try:
            user_id = callback.from_user.id
            
            # Получаем данные из состояния
            data = await state.get_data()
            avatar_id_str = data.get("avatar_id")
            avatar_name = data.get("avatar_name", "Аватар")
            gender = data.get("gender", "unknown")
            training_type = data.get("training_type", "portrait")
            
            if not avatar_id_str:
                await callback.answer("❌ Ошибка: аватар не найден", show_alert=True)
                return
            
            avatar_id = UUID(avatar_id_str)
            
            # Получаем количество фото
            async with get_avatar_service() as avatar_service:
                photos, photos_count = await avatar_service.get_avatar_photos(avatar_id)
            
            if photos_count < self.config.MIN_PHOTOS:
                await callback.answer(
                    f"❌ Недостаточно фотографий!\nМинимум: {self.config.MIN_PHOTOS}, загружено: {photos_count}",
                    show_alert=True
                )
                return
            
            # Получаем пользователя для проверки баланса
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_id)
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
                
                # Получаем баланс через сервис
                user_balance = await user_service.get_user_balance(user.id)
            
            # Определяем стоимость из конфигурации
            avatar_cost = settings.AVATAR_CREATION_COST
            
            # Проверяем тестовый режим
            is_test_mode = getattr(settings, 'AVATAR_TEST_MODE', False)
            
            # Формируем текст подтверждения
            gender_text = "👨 мужской" if gender == "male" else "👩 женский"
            type_text = "🖼️ Художественный" if training_type == "style" else "🎨 Портретный"
            
            text = f"""🦋 ПРОВЕРЬТЕ ДАННЫЕ АВАТАРА

👤 Имя: {avatar_name}
🚻 Пол: {gender_text}
🎨 Тип: {type_text}
📸 Загружено фото: {photos_count}

💎 Стоимость аватара: {avatar_cost}
💰 Ваш баланс: {user_balance}"""
            
            if is_test_mode:
                text += "\n\n🧪 ТЕСТОВЫЙ РЕЖИМ - обучение имитируется без реальных затрат"
            
            text += "\n\nЕсли всё верно, нажмите Создать аватар:"
            
            # Проверяем достаточность баланса
            if not is_test_mode and user_balance < avatar_cost:
                # Недостаточно средств
                text += f"\n\n❌ Недостаточно средств!\nНеобходимо: {avatar_cost - user_balance} кредитов"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="💳 Пополнить баланс",
                            callback_data="balance_top_up"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="◀️ К загрузке фото",
                            callback_data="back_to_upload"
                        )
                    ]
                ])
            else:
                # Достаточно средств или тестовый режим
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Создать аватар",
                            callback_data=f"start_training_{avatar_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="◀️ К загрузке фото",
                            callback_data="back_to_upload"
                        )
                    ]
                ])
            
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard
            )
            
            logger.info(f"Показан экран подтверждения обучения для пользователя {user_id}, аватар {avatar_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при показе подтверждения обучения: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    def _get_progress_text(self, photos_count: int) -> str:
        """Генерирует текст прогресса загрузки"""
        # Вычисляем прогресс в процентах
        progress_percent = min(100, (photos_count / self.config.MAX_PHOTOS) * 100)
        
        # Создаем прогресс-бар
        filled_blocks = int(progress_percent / 10)
        progress_bar = "█" * filled_blocks + "░" * (10 - filled_blocks)
        
        # Определяем статус
        if photos_count < self.config.MIN_PHOTOS:
            status = f"❌ Нужно еще {self.config.MIN_PHOTOS - photos_count} фото"
            status_emoji = "📤"
        elif photos_count < self.config.MAX_PHOTOS:
            status = "✅ Можно начать обучение или добавить еще фото"
            status_emoji = "🎯"
        else:
            status = "✅ Максимум достигнут! Готов к обучению"
            status_emoji = "🚀"
        
        return f"""{status_emoji} Прогресс загрузки

📊 {progress_bar} {progress_percent:.0f}%

📸 Загружено: {photos_count}/{self.config.MAX_PHOTOS} фото
📋 Минимум: {self.config.MIN_PHOTOS} фото

{status}

💡 Совет: Больше качественных фото = лучший результат!"""

    def _get_upload_intro_text(self, name: str, training_type: str, gender: str) -> str:
        """Генерирует введение для загрузки фото"""
        gender_emoji = "👨" if gender == "male" else "👩"
        
        if training_type == "portrait":
            tips = "• Портретные фото с хорошим освещением\n• Разные углы и выражения лица\n• Без головных уборов и очков"
        elif training_type == "style":
            tips = "• Фото в полный рост\n• Разная одежда и стили\n• Хорошее освещение"
        else:
            tips = "• Качественные фото с хорошим освещением\n• Разные позы и углы\n• Без фильтров и масок"
        
        return f"""📸 Загрузка фотографий

{gender_emoji} Аватар: {name}
🎯 Тип: {training_type.title()}

📋 Рекомендации:
{tips}

📊 Требования:
• Минимум: {self.config.MIN_PHOTOS} фото
• Рекомендуется: {self.config.MAX_PHOTOS} фото
• Формат: JPG, PNG (до {self.config.MAX_FILE_SIZE // (1024*1024)}MB)
• Размер: минимум {self.config.MIN_RESOLUTION}×{self.config.MIN_RESOLUTION} пикселей

💡 Совет: Чем больше качественных фото, тем лучше результат!

📤 Начните отправлять фотографии:"""

    def clear_progress_cache(self, user_id: int):
        """Очищает кэш прогресса для пользователя"""
        if user_id in user_progress_messages:
            del user_progress_messages[user_id] 