#!/usr/bin/env python3
"""
Скрипт для пополнения баланса пользователя в базе данных
"""
import asyncio
import sys
from uuid import UUID
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Добавляем путь к проекту
sys.path.append('.')

from app.core.database import get_session
from app.database.models import User, UserBalance
from app.core.logger import get_logger
from app.core.config import settings
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = get_logger(__name__)


async def find_user_by_telegram_id(session: AsyncSession, telegram_id: str) -> Optional[User]:
    """Найти пользователя по Telegram ID"""
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def find_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    """Найти пользователя по username"""
    # Убираем @ если есть
    clean_username = username.replace('@', '').strip()
    stmt = select(User).where(User.username == clean_username)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_balance(session: AsyncSession, user_id: UUID) -> Optional[UserBalance]:
    """Получить баланс пользователя"""
    stmt = select(UserBalance).where(UserBalance.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_user_balance(session: AsyncSession, user_id: UUID, initial_amount: float = 0.0) -> UserBalance:
    """Создать баланс для пользователя"""
    balance = UserBalance(user_id=user_id, coins=initial_amount)
    session.add(balance)
    await session.commit()
    await session.refresh(balance)
    return balance


async def add_balance(session: AsyncSession, user_id: UUID, amount: float) -> UserBalance:
    """Пополнить баланс пользователя"""
    # Получаем текущий баланс
    balance = await get_user_balance(session, user_id)
    
    if balance is None:
        # Создаем баланс если его нет
        logger.info(f"Создаем новый баланс для пользователя {user_id}")
        balance = await create_user_balance(session, user_id, amount)
    else:
        # Пополняем существующий баланс
        old_amount = balance.coins
        balance.coins += amount
        await session.commit()
        await session.refresh(balance)
        logger.info(f"Баланс обновлен: {old_amount} + {amount} = {balance.coins}")
    
    return balance


async def send_balance_notification(telegram_id: str, added_amount: float, current_balance: float):
    """Отправляет уведомление о пополнении баланса с кнопкой для всплывающего окна"""
    try:
        bot = Bot(token=settings.TELEGRAM_TOKEN)
        
        # Формируем краткое сообщение
        message = (
            f"💰 **Баланс пополнен!**\n\n"
            f"➕ Добавлено: {added_amount} кредитов\n"
            f"💎 Текущий баланс: {current_balance} кредитов"
        )
        
        # Создаем inline-кнопку для показа детальной информации
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✨ Подробности",
                    callback_data=f"balance_details_{added_amount}_{current_balance}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧑‍🎨 Создать аватар",
                    callback_data="create_avatar"
                )
            ]
        ])
        
        # Отправляем сообщение с кнопками
        await bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode="Markdown",
            reply_markup=keyboard,
            disable_notification=False,  # Включаем звук уведомления
            disable_web_page_preview=True
        )
        
        logger.info(f"✅ Уведомление о пополнении с кнопками отправлено пользователю {telegram_id}")
        
        # Закрываем сессию бота
        await bot.session.close()
        
    except Exception as e:
        logger.exception(f"❌ Ошибка отправки уведомления пользователю {telegram_id}: {e}")
        print(f"⚠️ Не удалось отправить уведомление в Telegram: {e}")


async def send_simple_balance_notification(telegram_id: str, added_amount: float, current_balance: float):
    """Отправляет простое всплывающее уведомление (как в справке)"""
    try:
        bot = Bot(token=settings.TELEGRAM_TOKEN)
        
        # Формируем сообщение в стиле справки аватаров (краткое и информативное)
        message = (
            f"💰 Баланс пополнен на {added_amount} кредитов\n\n"
            f"💎 Текущий баланс: {current_balance} кредитов\n\n"
            f"✨ Теперь вы можете создавать аватары!"
        )
        
        # Отправляем как обычное сообщение, но с выделением
        await bot.send_message(
            chat_id=telegram_id,
            text=f"🔔 **УВЕДОМЛЕНИЕ**\n\n{message}",
            parse_mode="Markdown",
            disable_notification=False
        )
        
        logger.info(f"✅ Простое уведомление о пополнении отправлено пользователю {telegram_id}")
        
        # Закрываем сессию бота
        await bot.session.close()
        
    except Exception as e:
        logger.exception(f"❌ Ошибка отправки простого уведомления пользователю {telegram_id}: {e}")
        print(f"⚠️ Не удалось отправить уведомление в Telegram: {e}")


async def show_user_info(user: User, balance: Optional[UserBalance]):
    """Показать информацию о пользователе"""
    print(f"\n👤 Информация о пользователе:")
    print(f"   ID: {user.id}")
    print(f"   Telegram ID: {user.telegram_id}")
    print(f"   Имя: {user.first_name} {user.last_name or ''}")
    print(f"   Username: @{user.username or 'не указан'}")
    print(f"   Язык: {user.language_code}")
    print(f"   Premium: {'Да' if user.is_premium else 'Нет'}")
    print(f"   Создан: {user.created_at}")
    
    if balance:
        print(f"\n💰 Текущий баланс: {balance.coins} кредитов")
        print(f"   Обновлен: {balance.updated_at}")
    else:
        print(f"\n💰 Баланс: не создан")


async def main():
    """Основная функция"""
    print("💰 Скрипт пополнения баланса пользователя")
    print("=" * 50)
    
    # Получаем параметры
    if len(sys.argv) < 3:
        print("Использование:")
        print("  python add_balance.py <telegram_id_или_username> <сумма> [тип_уведомления]")
        print("")
        print("Примеры:")
        print("  python add_balance.py 123456789 150.0")
        print("  python add_balance.py @ivan_petrov 100 simple")
        print("  python add_balance.py ivan_petrov 50.5 buttons")
        print("")
        print("Типы уведомлений:")
        print("  simple  - простое уведомление (по умолчанию)")
        print("  buttons - уведомление с кнопками")
        return
    
    user_identifier = sys.argv[1]
    try:
        amount = float(sys.argv[2])
    except ValueError:
        print("❌ Ошибка: сумма должна быть числом")
        return
    
    # Получаем тип уведомления (опционально)
    notification_type = "simple"  # по умолчанию
    if len(sys.argv) > 3:
        notification_type = sys.argv[3].lower()
        if notification_type not in ["simple", "buttons"]:
            print("❌ Ошибка: неизвестный тип уведомления. Используйте 'simple' или 'buttons'")
            return
    
    if amount <= 0:
        print("❌ Ошибка: сумма должна быть положительной")
        return
    
    print(f"🔍 Поиск пользователя: {user_identifier}")
    print(f"💵 Сумма пополнения: {amount} кредитов")
    print(f"📱 Тип уведомления: {notification_type}")
    
    # Подключаемся к базе данных
    try:
        async with get_session() as session:
            # Ищем пользователя
            user = None
            
            # Сначала пробуем найти по telegram_id (если это число)
            if user_identifier.isdigit():
                user = await find_user_by_telegram_id(session, user_identifier)
                if user:
                    print(f"✅ Пользователь найден по Telegram ID: {user_identifier}")
            
            # Если не найден, пробуем по username
            if user is None:
                user = await find_user_by_username(session, user_identifier)
                if user:
                    print(f"✅ Пользователь найден по username: {user_identifier}")
            
            if user is None:
                print(f"❌ Пользователь не найден: {user_identifier}")
                print("💡 Проверьте правильность Telegram ID или username")
                return
            
            # Получаем текущий баланс
            current_balance = await get_user_balance(session, user.id)
            
            # Показываем информацию до пополнения
            await show_user_info(user, current_balance)
            
            # Подтверждение
            print(f"\n❓ Пополнить баланс на {amount} кредитов?")
            confirm = input("Введите 'да' для подтверждения: ").lower().strip()
            
            if confirm not in ['да', 'yes', 'y']:
                print("❌ Операция отменена")
                return
            
            # Пополняем баланс
            print(f"\n💰 Пополняем баланс...")
            updated_balance = await add_balance(session, user.id, amount)
            
            print(f"✅ Баланс успешно пополнен!")
            print(f"   Новый баланс: {updated_balance.coins} кредитов")
            print(f"   Пополнено на: +{amount} кредитов")
            
            # Отправляем уведомление в Telegram
            print(f"\n📱 Отправляем уведомление в Telegram ({notification_type})...")
            
            if notification_type == "buttons":
                await send_balance_notification(
                    telegram_id=user.telegram_id,
                    added_amount=amount,
                    current_balance=updated_balance.coins
                )
            else:  # simple
                await send_simple_balance_notification(
                    telegram_id=user.telegram_id,
                    added_amount=amount,
                    current_balance=updated_balance.coins
                )
            
    except Exception as e:
        logger.exception(f"Ошибка при пополнении баланса: {e}")
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 