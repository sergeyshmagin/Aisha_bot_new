#!/usr/bin/env python3
"""
Скрипт для ручного пополнения баланса пользователя
Использование: python scripts/admin/add_balance.py <telegram_id> <amount> [reason]
"""
import sys
import asyncio
from pathlib import Path

# Добавляем путь к корню проекта
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.database import get_session
from app.services.balance_service import BalanceService
from app.core.di import get_user_service_with_session
from app.core.logger import get_logger

logger = get_logger(__name__)

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

async def main():
    """Главная функция"""
    if len(sys.argv) < 3:
        print("❌ Использование: python scripts/admin/add_balance.py <telegram_id> <amount> [reason]")
        print("")
        print("Примеры:")
        print("  python scripts/admin/add_balance.py 174171680 250")
        print("  python scripts/admin/add_balance.py 174171680 500 'Пополнение пакетом 500 монет'")
        print("  python scripts/admin/add_balance.py 174171680 1000 'Промо-акция'")
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