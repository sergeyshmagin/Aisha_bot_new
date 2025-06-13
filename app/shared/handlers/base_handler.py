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
        show_error: bool = True,
        auto_register: bool = True
    ) -> Optional[User]:
        """
        Получает пользователя из callback query с автоматической регистрацией
        
        Args:
            callback: Callback query от пользователя
            show_error: Показывать ли ошибку пользователю
            auto_register: Автоматически регистрировать пользователя если не найден
            
        Returns:
            User объект или None если не найден
        """
        try:
            user_telegram_id = callback.from_user.id
            
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                
                if not user and auto_register:
                    # Автоматически регистрируем пользователя
                    telegram_user_data = {
                        "id": callback.from_user.id,
                        "first_name": callback.from_user.first_name,
                        "last_name": callback.from_user.last_name,
                        "username": callback.from_user.username,
                        "language_code": callback.from_user.language_code,
                        "is_premium": getattr(callback.from_user, 'is_premium', False),
                        "is_bot": callback.from_user.is_bot,
                    }
                    
                    user = await user_service.register_user(telegram_user_data)
                    if user:
                        logger.info(f"Автоматически зарегистрирован пользователь: {user.telegram_id}")
                    else:
                        logger.error(f"Не удалось зарегистрировать пользователя {callback.from_user.id}")
                
                if not user and show_error:
                    await callback.answer("❌ Произошла ошибка. Попробуйте команду /start", show_alert=True)
                    
                return user
                
        except Exception as e:
            logger.exception(f"Ошибка получения пользователя: {e}")
            if show_error:
                await callback.answer("❌ Произошла ошибка", show_alert=True)
            return None
    
    async def get_user_from_message(
        self, 
        message: Message, 
        show_error: bool = True,
        auto_register: bool = True
    ) -> Optional[User]:
        """
        Получает пользователя из message с автоматической регистрацией
        
        Args:
            message: Message от пользователя
            show_error: Показывать ли ошибку пользователю
            auto_register: Автоматически регистрировать пользователя если не найден
            
        Returns:
            User объект или None если не найден
        """
        try:
            user_telegram_id = message.from_user.id
            
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                
                if not user and auto_register:
                    # Автоматически регистрируем пользователя
                    telegram_user_data = {
                        "id": message.from_user.id,
                        "first_name": message.from_user.first_name,
                        "last_name": message.from_user.last_name,
                        "username": message.from_user.username,
                        "language_code": message.from_user.language_code,
                        "is_premium": getattr(message.from_user, 'is_premium', False),
                        "is_bot": message.from_user.is_bot,
                    }
                    
                    user = await user_service.register_user(telegram_user_data)
                    if user:
                        logger.info(f"Автоматически зарегистрирован пользователь: {user.telegram_id}")
                    else:
                        logger.error(f"Не удалось зарегистрировать пользователя {message.from_user.id}")
                
                if not user and show_error:
                    await message.reply("❌ Произошла ошибка. Попробуйте команду /start")
                    
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
            logger.info(f"[BaseHandler] get_avatar_by_id called: avatar_id={avatar_id}, user_id={user_id}")
            logger.info(f"[BaseHandler] Types: avatar_id={type(avatar_id)}, user_id={type(user_id)}")
            
            async with get_avatar_service() as avatar_service:
                avatar = await avatar_service.get_avatar(avatar_id)
                logger.info(f"[BaseHandler] Avatar from service: {avatar}")
                
                if not avatar:
                    logger.warning(f"[BaseHandler] Avatar {avatar_id} not found in database")
                    if show_error:
                        error_msg = "❌ Аватар не найден"
                        if callback:
                            await callback.answer(error_msg, show_alert=True)
                        elif message:
                            await message.reply(error_msg)
                    return None
                
                logger.info(f"[BaseHandler] Avatar found: id={avatar.id}, user_id={avatar.user_id}, name={avatar.name}")
                logger.info(f"[BaseHandler] Avatar user_id type: {type(avatar.user_id)}")
                
                # Проверяем принадлежность пользователю
                if user_id:
                    logger.info(f"[BaseHandler] Checking ownership: avatar.user_id={avatar.user_id} vs user_id={user_id}")
                    
                    # Приводим user_id к UUID если это строка
                    user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
                    logger.info(f"[BaseHandler] Converted user_id to UUID: {user_uuid}, type: {type(user_uuid)}")
                    logger.info(f"[BaseHandler] Ownership check result: {avatar.user_id == user_uuid}")
                    
                    if avatar.user_id != user_uuid:
                        logger.error(f"[BaseHandler] OWNERSHIP FAILED: avatar belongs to {avatar.user_id}, but checking for {user_uuid}")
                        if show_error:
                            error_msg = "❌ Аватар не принадлежит вам"
                            if callback:
                                await callback.answer(error_msg, show_alert=True)
                            elif message:
                                await message.reply(error_msg)
                        return None
                
                # Проверяем что аватар не STYLE (LEGACY)
                from app.database.models import AvatarTrainingType
                if avatar.training_type == AvatarTrainingType.STYLE:
                    logger.warning(f"[BaseHandler] STYLE аватар {avatar_id} больше не поддерживается (LEGACY)")
                    if show_error:
                        error_msg = "❌ Этот аватар больше не поддерживается. Пожалуйста, создайте новый портретный аватар."
                        if callback:
                            await callback.answer(error_msg, show_alert=True)
                        elif message:
                            await message.reply(error_msg)
                    return None
                
                logger.info(f"[BaseHandler] Ownership check passed, returning avatar")
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
                # Получаем основной аватар
                main_avatar = await avatar_service.get_main_avatar(user_id)
                
                if not main_avatar:
                    error_msg = "🎭 Для этого действия нужен аватар!\n\n✨ Создайте свой первый аватар и откройте все возможности бота!"
                    if show_error:
                        if callback:
                            await callback.answer(error_msg, show_alert=True)
                        else:
                            await message.reply(error_msg)
                    return None
                
                # Проверяем что аватар не STYLE (LEGACY)
                from app.database.models import AvatarTrainingType
                if main_avatar.training_type == AvatarTrainingType.STYLE:
                    if show_error:
                        error_msg = "❌ Ваш основной аватар больше не поддерживается. Пожалуйста, создайте новый портретный аватар."
                        if callback:
                            await callback.answer(error_msg, show_alert=True)
                        elif message:
                            await message.reply(error_msg)
                    return None
                
                # Проверяем статус если требуется
                if check_completed and main_avatar.status != "completed":
                    if show_error:
                        error_msg = "❌ Ваш аватар еще не готов. Дождитесь завершения обучения!"
                        if callback:
                            await callback.answer(error_msg, show_alert=True)
                        elif message:
                            await message.reply(error_msg)
                    return None
                
                return main_avatar
                
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
    
    async def safe_edit_message(
        self,
        callback: CallbackQuery,
        text: str,
        reply_markup = None,
        parse_mode: str = "HTML"
    ) -> None:
        """
        Безопасное редактирование сообщения с fallback на новое сообщение
        
        Args:
            callback: Callback query
            text: Новый текст сообщения
            reply_markup: Клавиатура
            parse_mode: Режим парсинга
        """
        try:
            await callback.message.edit_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except Exception as edit_error:
            # Если не удается отредактировать (например, сообщение без текста), удаляем и отправляем новое
            logger.warning(f"Не удалось отредактировать сообщение: {edit_error}")
            try:
                await callback.message.delete()
            except Exception as delete_error:
                logger.warning(f"Не удалось удалить сообщение: {delete_error}")
            
            try:
                # Используем bot для отправки сообщения в чат
                # Получаем bot из callback
                bot = callback.bot
                
                await bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            except Exception as send_error:
                logger.error(f"Не удалось отправить новое сообщение: {send_error}")
                await callback.answer("❌ Произошла ошибка", show_alert=True)