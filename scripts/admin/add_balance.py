#!/usr/bin/env python3
"""
Скрипт для ручного пополнения баланса пользователя
Использование: 
  python scripts/admin/add_balance.py <telegram_id> <amount> [reason]
  python scripts/admin/add_balance.py --list  # Показать список пользователей
  python scripts/admin/add_balance.py --interactive  # Интерактивный режим
"""
import sys
import asyncio
from pathlib import Path
from typing import List, Optional

# Добавляем путь к корню проекта
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.database import get_session
from app.services.balance_service import BalanceService
from app.core.di import get_user_service_with_session
from app.database.models import User, UserBalance
from app.core.logger import get_logger
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

logger = get_logger(__name__)

async def get_all_users() -> List[User]:
    """
    Получает список всех зарегистрированных пользователей
    
    Returns:
        Список объектов User
    """
    try:
        async with get_session() as session:
            # Получаем всех пользователей с их балансом, отсортированных по дате регистрации
            stmt = (
                select(User)
                .options(selectinload(User.balance))
                .where(User.is_bot == False)  # Исключаем ботов
                .order_by(User.created_at.desc())
            )
            result = await session.execute(stmt)
            users = result.scalars().all()
            return list(users)
    except Exception as e:
        logger.exception(f"Ошибка получения списка пользователей: {e}")
        return []

async def show_users_list():
    """Показывает список всех зарегистрированных пользователей"""
    print("🔄 Загружаем список пользователей...")
    users = await get_all_users()
    
    if not users:
        print("❌ Пользователи не найдены")
        return
    
    print(f"\n📋 Найдено пользователей: {len(users)}")
    print("=" * 80)
    
    for i, user in enumerate(users, 1):
        # Получаем баланс
        balance = 0.0
        if user.balance:
            balance = user.balance.coins
        
        username_str = f"@{user.username}" if user.username else "без username"
        full_name = f"{user.first_name}"
        if user.last_name:
            full_name += f" {user.last_name}"
        
        # Форматируем дату регистрации
        reg_date = user.created_at.strftime("%d.%m.%Y")
        
        print(f"{i:3d}. 🆔 {user.telegram_id:<12} | 👤 {full_name:<25} | {username_str:<20} | 💰 {balance:>7.0f} | 📅 {reg_date}")
    
    print("=" * 80)
    print("\n💡 Для пополнения баланса скопируйте Telegram ID и используйте:")
    print("   python scripts/admin/add_balance.py <telegram_id> <amount> [reason]")
    print("\n📋 Пример:")
    if users:
        example_user = users[0]
        print(f"   python scripts/admin/add_balance.py {example_user.telegram_id} 500 'Пополнение баланса'")

async def interactive_mode():
    """Интерактивный режим выбора пользователя и пополнения баланса"""
    print("🔄 Загружаем список пользователей...")
    users = await get_all_users()
    
    if not users:
        print("❌ Пользователи не найдены")
        return
    
    while True:
        print(f"\n📋 Список пользователей (всего: {len(users)})")
        print("=" * 80)
        
        # Показываем первые 20 пользователей
        display_users = users[:20]
        for i, user in enumerate(display_users, 1):
            balance = 0.0
            if user.balance:
                balance = user.balance.coins
            
            username_str = f"@{user.username}" if user.username else "без username"
            full_name = f"{user.first_name}"
            if user.last_name:
                full_name += f" {user.last_name}"
            
            print(f"{i:2d}. 🆔 {user.telegram_id:<12} | 👤 {full_name:<25} | {username_str:<20} | 💰 {balance:>7.0f}")
        
        if len(users) > 20:
            print(f"... и еще {len(users) - 20} пользователей")
        
        print("=" * 80)
        
        try:
            choice = input("\n🔢 Введите номер пользователя (1-20) или 'q' для выхода: ").strip()
            
            if choice.lower() == 'q':
                print("👋 Выход из программы")
                break
            
            user_index = int(choice) - 1
            if user_index < 0 or user_index >= len(display_users):
                print("❌ Неверный номер пользователя")
                continue
            
            selected_user = display_users[user_index]
            
            print(f"\n✅ Выбран пользователь:")
            print(f"🆔 Telegram ID: {selected_user.telegram_id}")
            print(f"👤 Имя: {selected_user.first_name} {selected_user.last_name or ''}")
            print(f"📧 Username: @{selected_user.username}" if selected_user.username else "📧 Username: отсутствует")
            
            # Получаем текущий баланс
            async with get_session() as session:
                balance_service = BalanceService(session)
                current_balance = await balance_service.get_balance(selected_user.id)
                print(f"💰 Текущий баланс: {current_balance:.0f} монет")
            
            # Запрашиваем сумму пополнения
            amount_str = input("\n💸 Введите сумму для пополнения: ").strip()
            if not amount_str:
                print("❌ Сумма не указана")
                continue
            
            try:
                amount = float(amount_str)
                if amount <= 0:
                    print("❌ Сумма должна быть больше 0")
                    continue
            except ValueError:
                print("❌ Неверный формат суммы")
                continue
            
            # Запрашиваем причину
            reason = input("📝 Введите причину пополнения (или Enter для стандартной): ").strip()
            if not reason:
                reason = "Ручное пополнение администратором"
            
            # Подтверждение
            print(f"\n🔍 Подтвердите операцию:")
            print(f"👤 Пользователь: {selected_user.first_name} (@{selected_user.username or 'без_username'})")
            print(f"💰 Сумма: +{amount:.0f} монет")
            print(f"📝 Причина: {reason}")
            
            confirm = input("\n✅ Выполнить пополнение? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes', 'да', 'д']:
                print("❌ Операция отменена")
                continue
            
            # Выполняем пополнение
            success = await add_balance_to_user(selected_user.telegram_id, amount, reason)
            
            if success:
                print("\n🎉 Операция выполнена успешно!")
                
                # Спрашиваем, хочет ли пользователь продолжить
                continue_choice = input("\n🔄 Пополнить баланс другому пользователю? (y/N): ").strip().lower()
                if continue_choice not in ['y', 'yes', 'да', 'д']:
                    break
            else:
                print("\n❌ Операция не выполнена")
                
        except (ValueError, KeyboardInterrupt):
            print("\n👋 Выход из программы")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")

async def add_balance_to_user(telegram_id: int, amount: float, reason: str = "Ручное пополнение"):
    """
    Добавляет баланс пользователю
    
    Args:
        telegram_id: Telegram ID пользователя
        amount: Сумма для пополнения
        reason: Причина пополнения
    """
    try:
        async with get_session() as session:
            # Получаем пользователя
            user_service = get_user_service_with_session(session)
            user = await user_service.get_user_by_telegram_id(telegram_id)
            
            if not user:
                print(f"❌ Пользователь с Telegram ID {telegram_id} не найден")
                return False
            
            # Получаем текущий баланс
            balance_service = BalanceService(session)
            current_balance = await balance_service.get_balance(user.id)
            
            # Пополняем баланс
            result = await balance_service.add_balance(
                user_id=user.id,
                amount=amount,
                description=reason
            )
            
            if result["success"]:
                new_balance = await balance_service.get_balance(user.id)
                print(f"✅ Баланс пользователя {user.first_name} (@{user.username or 'без_username'}) пополнен")
                print(f"💰 Было: {current_balance:.0f} монет")
                print(f"📈 Добавлено: +{amount:.0f} монет")
                print(f"💎 Стало: {new_balance:.0f} монет")
                print(f"📝 Причина: {reason}")
                
                await session.commit()
                return True
            else:
                print(f"❌ Ошибка пополнения баланса")
                return False
                
    except Exception as e:
        logger.exception(f"Ошибка пополнения баланса: {e}")
        print(f"❌ Ошибка: {e}")
        return False

async def show_user_stats():
    """Показывает статистику по пользователям"""
    try:
        async with get_session() as session:
            # Получаем общую статистику
            total_users_stmt = select(func.count(User.id)).where(User.is_bot == False)
            total_users_result = await session.execute(total_users_stmt)
            total_users = total_users_result.scalar()
            
            # Получаем пользователей с балансом больше 0
            users_with_balance_stmt = (
                select(func.count(User.id))
                .join(User.balance)
                .where(User.is_bot == False)
                .where(User.balance.has(UserBalance.coins > 0))
            )
            users_with_balance_result = await session.execute(users_with_balance_stmt)
            users_with_balance = users_with_balance_result.scalar()
            
            print(f"\n📊 Статистика пользователей:")
            print(f"👥 Всего пользователей: {total_users}")
            print(f"💰 С положительным балансом: {users_with_balance}")
            print(f"💸 Без баланса: {total_users - users_with_balance}")
            
    except Exception as e:
        logger.exception(f"Ошибка получения статистики: {e}")
        print(f"❌ Ошибка получения статистики: {e}")

async def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("❌ Использование:")
        print("  python scripts/admin/add_balance.py <telegram_id> <amount> [reason]")
        print("  python scripts/admin/add_balance.py --list  # Показать список пользователей")
        print("  python scripts/admin/add_balance.py --interactive  # Интерактивный режим")
        print("  python scripts/admin/add_balance.py --stats  # Показать статистику")
        print("")
        print("Примеры:")
        print("  python scripts/admin/add_balance.py 174171680 250")
        print("  python scripts/admin/add_balance.py 174171680 500 'Пополнение пакетом 500 монет'")
        print("  python scripts/admin/add_balance.py --list")
        print("  python scripts/admin/add_balance.py --interactive")
        return
    
    # Обработка специальных команд
    if sys.argv[1] == "--list":
        await show_users_list()
        return
    
    if sys.argv[1] == "--interactive":
        await interactive_mode()
        return
    
    if sys.argv[1] == "--stats":
        await show_user_stats()
        return
    
    # Обычный режим пополнения баланса
    if len(sys.argv) < 3:
        print("❌ Для пополнения баланса укажите Telegram ID и сумму")
        print("Использование: python scripts/admin/add_balance.py <telegram_id> <amount> [reason]")
        return
    
    try:
        telegram_id = int(sys.argv[1])
        amount = float(sys.argv[2])
        reason = sys.argv[3] if len(sys.argv) > 3 else "Ручное пополнение администратором"
        
        print(f"🔄 Пополнение баланса пользователя...")
        print(f"👤 Telegram ID: {telegram_id}")
        print(f"💰 Сумма: {amount:.0f} монет")
        print(f"📝 Причина: {reason}")
        print("")
        
        success = await add_balance_to_user(telegram_id, amount, reason)
        
        if success:
            print("✅ Операция выполнена успешно!")
        else:
            print("❌ Операция не выполнена")
            sys.exit(1)
            
    except ValueError as e:
        print(f"❌ Неверный формат аргументов: {e}")
        print("Telegram ID и сумма должны быть числами")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 