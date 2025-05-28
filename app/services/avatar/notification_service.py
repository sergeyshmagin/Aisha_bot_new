"""
Сервис уведомлений о готовности аватаров
"""
from typing import Optional
from uuid import UUID

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import get_logger
from app.database.models import Avatar, User
from app.services.user import UserService

logger = get_logger(__name__)


class AvatarNotificationService:
    """Сервис для отправки уведомлений о готовности аватаров"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)
    
    async def send_completion_notification(self, avatar: Avatar) -> bool:
        """
        Отправляет уведомление пользователю о завершении обучения аватара
        
        Args:
            avatar: Аватар, обучение которого завершено
            
        Returns:
            bool: True если уведомление отправлено успешно
        """
        try:
            # Получаем пользователя
            user = await self.user_service.get_user_by_id(avatar.user_id)
            
            if not user or not user.telegram_id:
                logger.warning(f"[NOTIFICATION] Пользователь не найден для аватара {avatar.id}")
                return False
            
            logger.info(f"[NOTIFICATION] Отправляем уведомление о готовности аватара {avatar.name} пользователю {user.telegram_id}")
            
            # Отправляем уведомление через Telegram
            bot = Bot(token=settings.TELEGRAM_TOKEN)
            
            try:
                # Формируем сообщение
                training_type = avatar.training_type.value if avatar.training_type else "style"
                
                if training_type == "portrait":
                    emoji = "🎭"
                    type_name = "Портретный"
                else:
                    emoji = "🎨"
                    type_name = "Художественный"
                
                message = (
                    f"🎉 **Ваш аватар готов!**\n\n"
                    f"{emoji} **{avatar.name}** ({type_name} стиль)\n"
                    f"✅ Обучение завершено успешно\n\n"
                    f"Теперь вы можете использовать аватар для генерации изображений!\n\n"
                    f"Перейдите в меню → Аватары для использования."
                )
                
                # Создаем кнопки для перехода в меню аватаров
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="🎭 Мои аватары",
                        callback_data="avatar_gallery"
                    )],
                    [InlineKeyboardButton(
                        text="🎨 Создать изображение",
                        callback_data=f"avatar_generate:{avatar.id}"
                    )]
                ])
                
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=message,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                
                logger.info(f"[NOTIFICATION] ✅ Уведомление отправлено пользователю {user.telegram_id}")
                return True
                
            finally:
                await bot.session.close()
                
        except Exception as e:
            logger.exception(f"[NOTIFICATION] ❌ Ошибка отправки уведомления для аватара {avatar.id}: {e}")
            return False
    
    async def send_completion_notification_by_id(self, avatar_id: UUID) -> bool:
        """
        Отправляет уведомление о завершении обучения по ID аватара
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            bool: True если уведомление отправлено успешно
        """
        try:
            from sqlalchemy import select
            
            # Получаем аватар из БД
            query = select(Avatar).where(Avatar.id == avatar_id)
            result = await self.session.execute(query)
            avatar = result.scalar_one_or_none()
            
            if not avatar:
                logger.warning(f"[NOTIFICATION] Аватар {avatar_id} не найден")
                return False
            
            return await self.send_completion_notification(avatar)
            
        except Exception as e:
            logger.exception(f"[NOTIFICATION] ❌ Ошибка получения аватара {avatar_id}: {e}")
            return False 