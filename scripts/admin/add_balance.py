#!/usr/bin/env python3
"""
Улучшенный скрипт для управления балансом пользователей
Использование: 
  python scripts/admin/add_balance.py <telegram_id> <amount> [reason]  # Прямое пополнение
  python scripts/admin/add_balance.py --list                          # Показать всех пользователей
  python scripts/admin/add_balance.py --interactive                   # Интерактивный режим
  python scripts/admin/add_balance.py --stats                         # Статистика пользователей
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Добавляем путь к корню проекта
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.database import get_session
from app.services.balance_service import BalanceService
from app.core.di import get_user_service_with_session
from app.core.logger import get_logger
from app.database.models.models import User
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

logger = get_logger(__name__)

class BalanceAdminTool:
    """Улучшенный инструмент администратора для управления балансом"""
    
    def __init__(self):
        self.session = None
        self.user_service = None
        self.balance_service = None
    
    async def __aenter__(self):
        self.session = get_session()
        await self.session.__aenter__()
        self.user_service = get_user_service_with_session(self.session)
        self.balance_service = BalanceService(self.session)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)

    async def get_all_users_with_balance(self) -> List[Dict[str, Any]]:
        """Получает всех пользователей с их балансами"""
        try:
            # Получаем всех пользователей
            query = select(User).options(selectinload(User.balance))
            result = await self.session.execute(query)
            users = result.scalars().all()
            
            users_data = []
            for user in users:
                try:
                    balance = await self.balance_service.get_balance(user.id)
                    users_data.append({
                        'id': user.id,
                        'telegram_id': user.telegram_id,
                        'first_name': user.first_name or 'Без имени',
                        'last_name': user.last_name or '',
                        'username': user.username,
                        'balance': balance,
                        'created_at': user.created_at,
                        'language_code': user.language_code or 'ru'
                    })
                except Exception as e:
                    logger.warning(f"Ошибка получения баланса для пользователя {user.id}: {e}")
                    users_data.append({
                        'id': user.id,
                        'telegram_id': user.telegram_id,
                        'first_name': user.first_name or 'Без имени',
                        'last_name': user.last_name or '',
                        'username': user.username,
                        'balance': 0.0,
                        'created_at': user.created_at,
                        'language_code': user.language_code or 'ru'
                    })
            
            # Сортируем по дате регистрации (новые сначала)
            users_data.sort(key=lambda x: x['created_at'], reverse=True)
            return users_data
            
        except Exception as e:
            logger.exception(f"Ошибка получения пользователей: {e}")
            return []

    async def show_users_list(self):
        """Показывает список всех пользователей с балансами"""
        print("📋 Получение списка пользователей...")
        users = await self.get_all_users_with_balance()
        
        if not users:
            print("❌ Пользователи не найдены")
            return
        
        print(f"\n👥 Всего пользователей: {len(users)}")
        print("=" * 100)
        print(f"{'№':<3} {'Telegram ID':<12} {'Имя':<20} {'Username':<15} {'Баланс':<10} {'Дата регистрации':<20}")
        print("=" * 100)
        
        for i, user in enumerate(users, 1):
            full_name = f"{user['first_name']} {user['last_name']}".strip()
            username = f"@{user['username']}" if user['username'] else "—"
            balance = f"{user['balance']:.0f}"
            reg_date = user['created_at'].strftime('%d.%m.%Y %H:%M') if user['created_at'] else "—"
            
            print(f"{i:<3} {user['telegram_id']:<12} {full_name[:20]:<20} {username[:15]:<15} {balance:<10} {reg_date:<20}")
        
        print("=" * 100)
        print(f"\n💡 Для копирования ID просто выделите нужный Telegram ID из списка выше")

    async def show_user_stats(self):
        """Показывает статистику пользователей"""
        print("📊 Получение статистики пользователей...")
        users = await self.get_all_users_with_balance()
        
        if not users:
            print("❌ Пользователи не найдены")
            return
        
        total_users = len(users)
        users_with_balance = len([u for u in users if u['balance'] > 0])
        users_without_balance = total_users - users_with_balance
        total_balance = sum(u['balance'] for u in users)
        avg_balance = total_balance / total_users if total_users > 0 else 0
        
        # Топ пользователей по балансу
        top_users = sorted(users, key=lambda x: x['balance'], reverse=True)[:5]
        
        print(f"\n📊 Статистика пользователей:")
        print("=" * 50)
        print(f"👥 Всего пользователей: {total_users}")
        print(f"💰 Пользователей с балансом: {users_with_balance}")
        print(f"🆓 Пользователей без баланса: {users_without_balance}")
        print(f"💎 Общий баланс всех пользователей: {total_balance:.0f} монет")
        print(f"📈 Средний баланс: {avg_balance:.0f} монет")
        print("=" * 50)
        
        if top_users:
            print("\n🏆 Топ-5 пользователей по балансу:")
            print("-" * 60)
            for i, user in enumerate(top_users[:5], 1):
                full_name = f"{user['first_name']} {user['last_name']}".strip()
                username = f"@{user['username']}" if user['username'] else ""
                print(f"{i}. {full_name} {username} — {user['balance']:.0f} монет")
            print("-" * 60)

    async def interactive_mode(self):
        """Интерактивный режим пополнения баланса"""
        print("🎯 Интерактивный режим пополнения баланса")
        print("=" * 50)
        
        # Показываем список пользователей
        users = await self.get_all_users_with_balance()
        if not users:
            print("❌ Пользователи не найдены")
            return
        
        print(f"\n👥 Доступные пользователи ({len(users)}):")
        print("-" * 80)
        for i, user in enumerate(users, 1):
            full_name = f"{user['first_name']} {user['last_name']}".strip()
            username = f"@{user['username']}" if user['username'] else ""
            balance_str = f"{user['balance']:.0f} монет"
            print(f"{i:2}. {full_name:<25} {username:<15} (ID: {user['telegram_id']}, баланс: {balance_str})")
        
        print("-" * 80)
        
        try:
            # Выбор пользователя
            choice = input("\n🔢 Введите номер пользователя (или 'q' для выхода): ").strip()
            if choice.lower() == 'q':
                print("👋 Выход из интерактивного режима")
                return
            
            user_index = int(choice) - 1
            if user_index < 0 or user_index >= len(users):
                print("❌ Неверный номер пользователя")
                return
            
            selected_user = users[user_index]
            full_name = f"{selected_user['first_name']} {selected_user['last_name']}".strip()
            
            print(f"\n✅ Выбран пользователь: {full_name}")
            print(f"   Telegram ID: {selected_user['telegram_id']}")
            print(f"   Текущий баланс: {selected_user['balance']:.0f} монет")
            
            # Ввод суммы
            amount_str = input("\n💰 Введите сумму для пополнения: ").strip()
            amount = float(amount_str)
            
            if amount <= 0:
                print("❌ Сумма должна быть положительной")
                return
            
            # Ввод причины
            reason = input("📝 Введите причину пополнения (Enter для стандартной): ").strip()
            if not reason:
                reason = "Ручное пополнение администратором"
            
            # Подтверждение
            print(f"\n📋 Подтверждение операции:")
            print(f"   👤 Пользователь: {full_name}")
            print(f"   💰 Сумма: +{amount:.0f} монет")
            print(f"   📝 Причина: {reason}")
            print(f"   💎 Новый баланс: {selected_user['balance'] + amount:.0f} монет")
            
            confirm = input("\n❓ Подтвердить операцию? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ Операция отменена")
                return
            
            # Выполнение пополнения
            success = await self.add_balance_to_user(
                int(selected_user['telegram_id']), 
                amount, 
                reason
            )
            
            if success:
                print("✅ Баланс успешно пополнен!")
            else:
                print("❌ Ошибка при пополнении баланса")
                
        except ValueError:
            print("❌ Неверный формат числа")
        except KeyboardInterrupt:
            print("\n👋 Операция прервана пользователем")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

    async def add_balance_to_user(self, telegram_id: int, amount: float, reason: str = "Ручное пополнение") -> bool:
        """Добавляет баланс пользователю"""
        try:
            # Получаем пользователя
            user = await self.user_service.get_user_by_telegram_id(telegram_id)
            
            if not user:
                print(f"❌ Пользователь с Telegram ID {telegram_id} не найден")
                return False
            
            # Получаем текущий баланс
            current_balance = await self.balance_service.get_balance(user.id)
            
            # Пополняем баланс
            result = await self.balance_service.add_balance(
                user_id=user.id,
                amount=amount,
                description=reason
            )
            
            if result["success"]:
                new_balance = await self.balance_service.get_balance(user.id)
                full_name = f"{user.first_name} {user.last_name or ''}".strip()
                username = f"@{user.username}" if user.username else "без_username"
                
                print(f"✅ Баланс пользователя {full_name} ({username}) пополнен")
                print(f"💰 Было: {current_balance:.0f} монет")
                print(f"📈 Добавлено: +{amount:.0f} монет")
                print(f"💎 Стало: {new_balance:.0f} монет")
                print(f"📝 Причина: {reason}")
                
                await self.session.commit()
                return True
            else:
                print(f"❌ Ошибка пополнения баланса: {result.get('message', 'Неизвестная ошибка')}")
                return False
                
        except Exception as e:
            logger.exception(f"Ошибка пополнения баланса: {e}")
            print(f"❌ Ошибка: {e}")
            return False

async def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("❌ Использование:")
        print("  python scripts/admin/add_balance.py <telegram_id> <amount> [reason]  # Прямое пополнение")
        print("  python scripts/admin/add_balance.py --list                          # Показать всех пользователей")
        print("  python scripts/admin/add_balance.py --interactive                   # Интерактивный режим")
        print("  python scripts/admin/add_balance.py --stats                         # Статистика пользователей")
        print("")
        print("Примеры:")
        print("  python scripts/admin/add_balance.py 174171680 250")
        print("  python scripts/admin/add_balance.py 174171680 500 'Пополнение пакетом 500 монет'")
        print("  python scripts/admin/add_balance.py --list")
        print("  python scripts/admin/add_balance.py --interactive")
        print("  python scripts/admin/add_balance.py --stats")
        return
    
    try:
        async with BalanceAdminTool() as tool:
            # Обработка специальных команд
            if sys.argv[1] == "--list":
                await tool.show_users_list()
                return
            elif sys.argv[1] == "--interactive":
                await tool.interactive_mode()
                return
            elif sys.argv[1] == "--stats":
                await tool.show_user_stats()
                return
            
            # Обычное пополнение баланса
            if len(sys.argv) < 3:
                print("❌ Для прямого пополнения укажите telegram_id и сумму")
                return
            
            telegram_id = int(sys.argv[1])
            amount = float(sys.argv[2])
            reason = sys.argv[3] if len(sys.argv) > 3 else "Ручное пополнение администратором"
            
            print(f"🔄 Пополнение баланса пользователя...")
            print(f"👤 Telegram ID: {telegram_id}")
            print(f"💰 Сумма: {amount:.0f} монет")
            print(f"📝 Причина: {reason}")
            print("")
            
            success = await tool.add_balance_to_user(telegram_id, amount, reason)
            
            if success:
                print("✅ Операция выполнена успешно!")
            else:
                print("❌ Операция не выполнена")
                sys.exit(1)
                
    except ValueError as e:
        print(f"❌ Неверный формат аргументов: {e}")
        print("Telegram ID и сумма должны быть числами")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Операция прервана пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 