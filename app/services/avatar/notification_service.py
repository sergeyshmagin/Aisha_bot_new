"""
Сервис уведомлений о готовности аватаров
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
import redis.asyncio as redis

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import get_logger
from app.core.resources import RedisConfig
from app.database.models import Avatar, User
from app.services.user import UserService

logger = get_logger(__name__)class AvatarNotificationService:
    """Сервис для отправки уведомлений о готовности аватаров"""
    
    # Минимальный интервал между уведомлениями (в секундах)
    _min_notification_interval = 30
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)
        
        # Конфигурация Redis для кэша уведомлений
        self._redis_config = {
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "db": settings.REDIS_DB,
            "password": settings.REDIS_PASSWORD,
            "ssl": settings.REDIS_SSL,
            "socket_timeout": 5.0,
            "socket_connect_timeout": 5.0,
            "decode_responses": True,
            "encoding": "utf-8"
        }
    
    async def send_completion_notification(self, avatar: Avatar) -> bool:
        """
        Отправляет уведомление пользователю о завершении обучения аватара
        
        Args:
            avatar: Аватар, обучение которого завершено
            
        Returns:
            bool: True если уведомление отправлено успешно
        """
        try:
            # Проверяем, не отправляли ли уже уведомление недавно
            if await self._is_notification_recently_sent(avatar.id):
                logger.info(f"[NOTIFICATION] Уведомление для аватара {avatar.id} уже отправлено недавно, пропускаем")
                return True  # Считаем успешным, чтобы не логировать как ошибку
            
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
                
                # Записываем в Redis время отправки уведомления
                await self._mark_notification_sent(avatar.id)
                
                logger.info(f"[NOTIFICATION] ✅ Уведомление отправлено пользователю {user.telegram_id}")
                return True
                
            finally:
                await bot.session.close()
                
        except Exception as e:
            logger.exception(f"[NOTIFICATION] ❌ Ошибка отправки уведомления для аватара {avatar.id}: {e}")
            return False
    
    async def _is_notification_recently_sent(self, avatar_id: UUID) -> bool:
        """
        Проверяет, было ли недавно отправлено уведомление для аватара через Redis
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            bool: True если уведомление было отправлено недавно
        """
        redis_client = None
        try:
            redis_client = redis.Redis(**self._redis_config)
            
            # Формируем ключ для Redis
            cache_key = f"{RedisConfig.KEY_PREFIXES['avatar_cache']}notification:{avatar_id}"
            
            # Проверяем существование ключа в Redis
            exists = await redis_client.exists(cache_key)
            
            if exists:
                logger.debug(f"[NOTIFICATION] Найдена запись в Redis для аватара {avatar_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"[NOTIFICATION] Ошибка проверки Redis кэша для аватара {avatar_id}: {e}")
            # В случае ошибки Redis возвращаем False, чтобы не блокировать уведомления
            return False
            
        finally:
            if redis_client:
                await redis_client.close()
    
    async def _mark_notification_sent(self, avatar_id: UUID) -> None:
        """
        Отмечает в Redis, что уведомление для аватара было отправлено
        
        Args:
            avatar_id: ID аватара
        """
        redis_client = None
        try:
            redis_client = redis.Redis(**self._redis_config)
            
            # Формируем ключ для Redis
            cache_key = f"{RedisConfig.KEY_PREFIXES['avatar_cache']}notification:{avatar_id}"
            
            # Записываем в Redis с TTL равным интервалу защиты
            await redis_client.setex(
                cache_key,
                self._min_notification_interval,
                datetime.utcnow().isoformat()
            )
            
            logger.debug(f"[NOTIFICATION] Записана отметка в Redis для аватара {avatar_id} (TTL: {self._min_notification_interval}s)")
            
        except Exception as e:
            logger.warning(f"[NOTIFICATION] Ошибка записи в Redis кэш для аватара {avatar_id}: {e}")
            # В случае ошибки Redis не прерываем процесс
            
        finally:
            if redis_client:
                await redis_client.close()
    
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
