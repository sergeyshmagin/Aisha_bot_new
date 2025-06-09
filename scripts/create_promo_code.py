#!/usr/bin/env python3
"""
Скрипт для создания промо-кодов
"""
import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import get_session
from app.services.promokode_service import PromokodeService
from app.database.models.promokode import PromokodeType
from app.core.logger import get_logger

logger = get_logger(__name__)


async def create_promo_code(
    code: str,
    promo_type: str,
    balance_amount: float = None,
    bonus_amount: float = None,
    discount_percent: float = None,
    max_uses: int = None,
    max_uses_per_user: int = 1,
    valid_days: int = None,
    description: str = None
):
    """
    Создает промо-код
    
    Args:
        code: Код промокода
        promo_type: Тип промокода (balance, bonus, discount)
        balance_amount: Сумма пополнения баланса (для типа balance)
        bonus_amount: Размер бонуса (для типа bonus)
        discount_percent: Процент скидки (для типа discount)
        max_uses: Максимальное количество использований
        max_uses_per_user: Максимальное количество использований на пользователя
        valid_days: Количество дней действия (None = без ограничения)
        description: Описание промокода
    """
    try:
        # Определяем тип промокода
        if promo_type.lower() == "balance":
            promokode_type = PromokodeType.BALANCE
        elif promo_type.lower() == "bonus":
            promokode_type = PromokodeType.BONUS
        elif promo_type.lower() == "discount":
            promokode_type = PromokodeType.DISCOUNT
        else:
            print(f"❌ Неизвестный тип промокода: {promo_type}")
            return False
        
        # Рассчитываем дату окончания действия
        valid_until = None
        if valid_days:
            valid_until = datetime.now() + timedelta(days=valid_days)
        
        async with get_session() as session:
            promo_service = PromokodeService(session)
            
            success, error = await promo_service.create_promokode(
                code=code,
                promokode_type=promokode_type,
                balance_amount=balance_amount,
                bonus_amount=bonus_amount,
                discount_percent=discount_percent,
                max_uses=max_uses,
                max_uses_per_user=max_uses_per_user,
                valid_from=datetime.now(),
                valid_until=valid_until,
                description=description,
                created_by="admin_script"
            )
            
            if success:
                print(f"✅ Промокод '{code}' успешно создан!")
                print(f"   Тип: {promo_type}")
                if balance_amount:
                    print(f"   Пополнение баланса: {balance_amount} монет")
                if bonus_amount:
                    print(f"   Бонус: {bonus_amount} монет")
                if discount_percent:
                    print(f"   Скидка: {discount_percent}%")
                if max_uses:
                    print(f"   Максимальное количество использований: {max_uses}")
                print(f"   Использований на пользователя: {max_uses_per_user}")
                if valid_until:
                    print(f"   Действует до: {valid_until.strftime('%Y-%m-%d %H:%M:%S')}")
                if description:
                    print(f"   Описание: {description}")
                return True
            else:
                print(f"❌ Ошибка создания промокода: {error}")
                return False
                
    except Exception as e:
        logger.exception(f"Ошибка создания промокода: {e}")
        print(f"❌ Ошибка: {e}")
        return False


def print_usage():
    """Выводит справку по использованию"""
    print("""
💰 Скрипт создания промо-кодов

Использование:
  python scripts/create_promo_code.py <код> <тип> [параметры]

Типы промокодов:
  balance   - Прямое пополнение баланса
  bonus     - Бонус при пополнении
  discount  - Скидка на пакет

Параметры:
  --balance <сумма>        Сумма пополнения баланса (для типа balance)
  --bonus <сумма>          Размер бонуса (для типа bonus)
  --discount <процент>     Процент скидки (для типа discount)
  --max-uses <число>       Максимальное количество использований
  --max-per-user <число>   Максимальное количество использований на пользователя (по умолчанию: 1)
  --valid-days <дни>       Количество дней действия
  --description <текст>    Описание промокода

Примеры:
  # Промокод на 100 монет
  python scripts/create_promo_code.py WELCOME100 balance --balance 100 --description "Приветственный бонус"
  
  # Промокод на 50 монет бонуса при пополнении
  python scripts/create_promo_code.py BONUS50 bonus --bonus 50 --description "Бонус при пополнении"
  
  # Промокод на 20% скидку
  python scripts/create_promo_code.py DISCOUNT20 discount --discount 20 --max-uses 100 --description "Скидка 20%"
  
  # Промокод с ограниченным сроком действия
  python scripts/create_promo_code.py LIMITED balance --balance 50 --valid-days 7 --max-uses 50
""")


async def main():
    """Основная функция"""
    if len(sys.argv) < 3:
        print_usage()
        return
    
    code = sys.argv[1].upper()
    promo_type = sys.argv[2].lower()
    
    # Парсим аргументы
    args = sys.argv[3:]
    params = {}
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg == "--balance" and i + 1 < len(args):
            params["balance_amount"] = float(args[i + 1])
            i += 2
        elif arg == "--bonus" and i + 1 < len(args):
            params["bonus_amount"] = float(args[i + 1])
            i += 2
        elif arg == "--discount" and i + 1 < len(args):
            params["discount_percent"] = float(args[i + 1])
            i += 2
        elif arg == "--max-uses" and i + 1 < len(args):
            params["max_uses"] = int(args[i + 1])
            i += 2
        elif arg == "--max-per-user" and i + 1 < len(args):
            params["max_uses_per_user"] = int(args[i + 1])
            i += 2
        elif arg == "--valid-days" and i + 1 < len(args):
            params["valid_days"] = int(args[i + 1])
            i += 2
        elif arg == "--description" and i + 1 < len(args):
            params["description"] = args[i + 1]
            i += 2
        else:
            print(f"❌ Неизвестный аргумент: {arg}")
            print_usage()
            return
    
    # Проверяем обязательные параметры
    if promo_type == "balance" and "balance_amount" not in params:
        print("❌ Для типа 'balance' требуется параметр --balance")
        return
    
    if promo_type == "bonus" and "bonus_amount" not in params:
        print("❌ Для типа 'bonus' требуется параметр --bonus")
        return
    
    if promo_type == "discount" and "discount_percent" not in params:
        print("❌ Для типа 'discount' требуется параметр --discount")
        return
    
    print(f"🎁 Создание промокода '{code}' типа '{promo_type}'...")
    
    success = await create_promo_code(code, promo_type, **params)
    
    if success:
        print("\n🎉 Промокод готов к использованию!")
    else:
        print("\n❌ Не удалось создать промокод")


if __name__ == "__main__":
    asyncio.run(main()) 