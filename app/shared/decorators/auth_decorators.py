"""
Декораторы для автоматической проверки пользователя и аватара
Устраняют дублирование кода проверок
"""
import functools
from typing import Callable, Optional
from uuid import UUID

from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.core.di import get_user_service, get_avatar_service
from app.core.logger import get_logger

logger = get_logger(__name__)


def require_user(show_error: bool = True):
    """
    Декоратор для автоматической проверки и получения пользователя
    
    Args:
        show_error: Показывать ли ошибку пользователю
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Ищем callback или message в аргументах
            callback = None
            message = None
            
            for arg in args:
                if isinstance(arg, CallbackQuery):
                    callback = arg
                    break
                elif isinstance(arg, Message):
                    message = arg
                    break
            
            if not callback and not message:
                raise ValueError("Декоратор require_user требует CallbackQuery или Message в аргументах")
            
            # Получаем пользователя
            user_telegram_id = (callback or message).from_user.id
            
            try:
                async with get_user_service() as user_service:
                    user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                    
                    if not user:
                        if show_error:
                            error_msg = "❌ Пользователь не найден"
                            if callback:
                                await callback.answer(error_msg, show_alert=True)
                            else:
                                await message.reply(error_msg)
                        return
                    
                    # Добавляем пользователя в kwargs
                    kwargs['user'] = user
                    return await func(*args, **kwargs)
                    
            except Exception as e:
                logger.exception(f"Ошибка в декораторе require_user: {e}")
                if show_error:
                    error_msg = "❌ Произошла ошибка"
                    if callback:
                        await callback.answer(error_msg, show_alert=True)
                    else:
                        await message.reply(error_msg)
                return
        
        return wrapper
    return decorator


def require_avatar(
    avatar_id_param: str = "avatar_id",
    check_ownership: bool = True,
    check_completed: bool = False,
    show_error: bool = True
):
    """
    Декоратор для автоматической проверки и получения аватара
    
    Args:
        avatar_id_param: Имя параметра с ID аватара
        check_ownership: Проверять ли принадлежность пользователю
        check_completed: Проверять ли что аватар завершен
        show_error: Показывать ли ошибку пользователю
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Ищем callback или message в аргументах
            callback = None
            message = None
            
            for arg in args:
                if isinstance(arg, CallbackQuery):
                    callback = arg
                    break
                elif isinstance(arg, Message):
                    message = arg
                    break
            
            if not callback and not message:
                raise ValueError("Декоратор require_avatar требует CallbackQuery или Message в аргументах")
            
            # Получаем avatar_id
            avatar_id = kwargs.get(avatar_id_param)
            if not avatar_id:
                raise ValueError(f"Параметр {avatar_id_param} не найден в kwargs")
            
            if isinstance(avatar_id, str):
                avatar_id = UUID(avatar_id)
            
            try:
                async with get_avatar_service() as avatar_service:
                    avatar = await avatar_service.get_avatar(avatar_id)
                    
                    if not avatar:
                        if show_error:
                            error_msg = "❌ Аватар не найден"
                            if callback:
                                await callback.answer(error_msg, show_alert=True)
                            else:
                                await message.reply(error_msg)
                        return
                    
                    # Проверяем принадлежность если требуется
                    if check_ownership:
                        user = kwargs.get('user')
                        if user and avatar.user_id != user.id:
                            if show_error:
                                error_msg = "❌ Аватар не принадлежит вам"
                                if callback:
                                    await callback.answer(error_msg, show_alert=True)
                                else:
                                    await message.reply(error_msg)
                            return
                    
                    # Проверяем статус если требуется
                    if check_completed and avatar.status != "completed":
                        if show_error:
                            error_msg = "❌ Аватар еще не готов"
                            if callback:
                                await callback.answer(error_msg, show_alert=True)
                            else:
                                await message.reply(error_msg)
                        return
                    
                    # Добавляем аватар в kwargs
                    kwargs['avatar'] = avatar
                    return await func(*args, **kwargs)
                    
            except Exception as e:
                logger.exception(f"Ошибка в декораторе require_avatar: {e}")
                if show_error:
                    error_msg = "❌ Произошла ошибка"
                    if callback:
                        await callback.answer(error_msg, show_alert=True)
                    else:
                        await message.reply(error_msg)
                return
        
        return wrapper
    return decorator


def require_main_avatar(
    check_completed: bool = False,
    show_error: bool = True
):
    """
    Декоратор для автоматической проверки и получения основного аватара
    
    Args:
        check_completed: Проверять ли что аватар завершен
        show_error: Показывать ли ошибку пользователю
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Ищем callback или message в аргументах
            callback = None
            message = None
            
            for arg in args:
                if isinstance(arg, CallbackQuery):
                    callback = arg
                    break
                elif isinstance(arg, Message):
                    message = arg
                    break
            
            if not callback and not message:
                raise ValueError("Декоратор require_main_avatar требует CallbackQuery или Message в аргументах")
            
            # Получаем пользователя
            user = kwargs.get('user')
            if not user:
                raise ValueError("Декоратор require_main_avatar требует пользователя в kwargs (используйте @require_user)")
            
            try:
                async with get_avatar_service() as avatar_service:
                    avatar = await avatar_service.get_main_avatar(user.id)
                    
                    if not avatar:
                        if show_error:
                            error_msg = "❌ У вас нет основного аватара. Создайте аватар сначала!"
                            if callback:
                                await callback.answer(error_msg, show_alert=True)
                            else:
                                await message.reply(error_msg)
                        return
                    
                    # Проверяем статус если требуется
                    if check_completed and avatar.status != "completed":
                        if show_error:
                            error_msg = "❌ Ваш аватар еще не готов. Дождитесь завершения обучения!"
                            if callback:
                                await callback.answer(error_msg, show_alert=True)
                            else:
                                await message.reply(error_msg)
                        return
                    
                    # Добавляем аватар в kwargs
                    kwargs['main_avatar'] = avatar
                    return await func(*args, **kwargs)
                    
            except Exception as e:
                logger.exception(f"Ошибка в декораторе require_main_avatar: {e}")
                if show_error:
                    error_msg = "❌ Произошла ошибка"
                    if callback:
                        await callback.answer(error_msg, show_alert=True)
                    else:
                        await message.reply(error_msg)
                return
        
        return wrapper
    return decorator


def require_balance(
    amount: float,
    show_error: bool = True
):
    """
    Декоратор для проверки достаточности баланса
    
    Args:
        amount: Требуемая сумма
        show_error: Показывать ли ошибку пользователю
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Ищем callback или message в аргументах
            callback = None
            message = None
            
            for arg in args:
                if isinstance(arg, CallbackQuery):
                    callback = arg
                    break
                elif isinstance(arg, Message):
                    message = arg
                    break
            
            if not callback and not message:
                raise ValueError("Декоратор require_balance требует CallbackQuery или Message в аргументах")
            
            # Получаем пользователя
            user = kwargs.get('user')
            if not user:
                raise ValueError("Декоратор require_balance требует пользователя в kwargs (используйте @require_user)")
            
            try:
                async with get_user_service() as user_service:
                    balance = await user_service.get_user_balance(user.id)
                    
                    if balance < amount:
                        if show_error:
                            error_msg = f"❌ Недостаточно средств. Требуется: {amount:.0f}, у вас: {balance:.0f}"
                            if callback:
                                await callback.answer(error_msg, show_alert=True)
                            else:
                                await message.reply(error_msg)
                        return
                    
                    # Добавляем баланс в kwargs
                    kwargs['user_balance'] = balance
                    return await func(*args, **kwargs)
                    
            except Exception as e:
                logger.exception(f"Ошибка в декораторе require_balance: {e}")
                if show_error:
                    error_msg = "❌ Произошла ошибка при проверке баланса"
                    if callback:
                        await callback.answer(error_msg, show_alert=True)
                    else:
                        await message.reply(error_msg)
                return
        
        return wrapper
    return decorator 