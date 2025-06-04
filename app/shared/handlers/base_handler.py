"""
Базовый класс для обработчиков с общими методами
Устраняет дублирование кода согласно принципу DRY
"""
from typing import Optional, Union
from uuid import UUID

from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.core.di import get_user_service, get_avatar_service
from app.core.logger import get_logger
from app.database.models import User, Avatar

logger = get_logger(__name__)


class BaseHandler:
    """Базовый класс для всех обработчиков с общими методами"""
    
    async def get_user_from_callback(
        self, 
        callback: CallbackQuery, 
        show_error: bool = True
    ) -> Optional[User]:
        """
        Получает пользователя из callback query
        
        Args:
            callback: Callback query от пользователя
            show_error: Показывать ли ошибку пользователю
            
        Returns:
            User объект или None если не найден
        """
        try:
            user_telegram_id = callback.from_user.id
            
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                
                if not user and show_error:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    
                return user
                
        except Exception as e:
            logger.exception(f"Ошибка получения пользователя: {e}")
            if show_error:
                await callback.answer("❌ Произошла ошибка", show_alert=True)
            return None
    
    async def get_user_from_message(
        self, 
        message: Message, 
        show_error: bool = True
    ) -> Optional[User]:
        """
        Получает пользователя из message
        
        Args:
            message: Message от пользователя
            show_error: Показывать ли ошибку пользователю
            
        Returns:
            User объект или None если не найден
        """
        try:
            user_telegram_id = message.from_user.id
            
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                
                if not user and show_error:
                    await message.reply("❌ Пользователь не найден")
                    
                return user
                
        except Exception as e:
            logger.exception(f"Ошибка получения пользователя: {e}")
            if show_error:
                await message.reply("❌ Произошла ошибка")
            return None
    
    async def get_avatar_by_id(
        self, 
        avatar_id: UUID, 
        user_id: Optional[UUID] = None,
        callback: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
        show_error: bool = True
    ) -> Optional[Avatar]:
        """
        Получает аватар по ID с проверкой принадлежности пользователю
        
        Args:
            avatar_id: ID аватара
            user_id: ID пользователя для проверки принадлежности
            callback: Callback для отправки ошибки
            message: Message для отправки ошибки
            show_error: Показывать ли ошибку пользователю
            
        Returns:
            Avatar объект или None если не найден
        """
        try:
            async with get_avatar_service() as avatar_service:
                avatar = await avatar_service.get_avatar(avatar_id)
                
                if not avatar:
                    if show_error:
                        error_msg = "❌ Аватар не найден"
                        if callback:
                            await callback.answer(error_msg, show_alert=True)
                        elif message:
                            await message.reply(error_msg)
                    return None
                
                # Проверяем принадлежность пользователю
                if user_id and avatar.user_id != user_id:
                    if show_error:
                        error_msg = "❌ Аватар не принадлежит вам"
                        if callback:
                            await callback.answer(error_msg, show_alert=True)
                        elif message:
                            await message.reply(error_msg)
                    return None
                
                return avatar
                
        except Exception as e:
            logger.exception(f"Ошибка получения аватара {avatar_id}: {e}")
            if show_error:
                error_msg = "❌ Произошла ошибка"
                if callback:
                    await callback.answer(error_msg, show_alert=True)
                elif message:
                    await message.reply(error_msg)
            return None
    
    async def get_main_avatar(
        self, 
        user_id: UUID,
        callback: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
        show_error: bool = True,
        check_completed: bool = False
    ) -> Optional[Avatar]:
        """
        Получает основной аватар пользователя
        
        Args:
            user_id: ID пользователя
            callback: Callback для отправки ошибки
            message: Message для отправки ошибки
            show_error: Показывать ли ошибку пользователю
            check_completed: Проверять ли что аватар завершен
            
        Returns:
            Avatar объект или None если не найден
        """
        try:
            async with get_avatar_service() as avatar_service:
                avatar = await avatar_service.get_main_avatar(user_id)
                
                if not avatar:
                    if show_error:
                        error_msg = "❌ У вас нет основного аватара. Создайте аватар сначала!"
                        if callback:
                            await callback.answer(error_msg, show_alert=True)
                        elif message:
                            await message.reply(error_msg)
                    return None
                
                # Проверяем статус если требуется
                if check_completed and avatar.status != "completed":
                    if show_error:
                        error_msg = "❌ Ваш аватар еще не готов. Дождитесь завершения обучения!"
                        if callback:
                            await callback.answer(error_msg, show_alert=True)
                        elif message:
                            await message.reply(error_msg)
                    return None
                
                return avatar
                
        except Exception as e:
            logger.exception(f"Ошибка получения основного аватара для пользователя {user_id}: {e}")
            if show_error:
                error_msg = "❌ Произошла ошибка"
                if callback:
                    await callback.answer(error_msg, show_alert=True)
                elif message:
                    await message.reply(error_msg)
            return None
    
    async def check_user_balance(
        self, 
        user: User, 
        required_amount: float,
        callback: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
        show_error: bool = True
    ) -> bool:
        """
        Проверяет достаточность баланса пользователя
        
        Args:
            user: Пользователь
            required_amount: Требуемая сумма
            callback: Callback для отправки ошибки
            message: Message для отправки ошибки
            show_error: Показывать ли ошибку пользователю
            
        Returns:
            True если баланс достаточен, False иначе
        """
        try:
            async with get_user_service() as user_service:
                balance = await user_service.get_user_balance(user.id)
                
                if balance < required_amount:
                    if show_error:
                        error_msg = f"❌ Недостаточно средств. Требуется: {required_amount:.0f}, у вас: {balance:.0f}"
                        if callback:
                            await callback.answer(error_msg, show_alert=True)
                        elif message:
                            await message.reply(error_msg)
                    return False
                
                return True
                
        except Exception as e:
            logger.exception(f"Ошибка проверки баланса пользователя {user.id}: {e}")
            if show_error:
                error_msg = "❌ Произошла ошибка при проверке баланса"
                if callback:
                    await callback.answer(error_msg, show_alert=True)
                elif message:
                    await message.reply(error_msg)
            return False
    
    async def safe_clear_state(self, state: FSMContext) -> None:
        """Безопасно очищает состояние FSM"""
        try:
            await state.clear()
        except Exception as e:
            logger.warning(f"Ошибка очистки состояния: {e}") 