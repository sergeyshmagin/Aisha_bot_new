"""
Сервис для работы с балансом пользователя
"""
from typing import Optional, Dict, Any
from uuid import UUID

from app.core.logger import get_logger
from app.core.di import get_user_service
from app.services.base import BaseService

logger = get_logger(__name__)


class BalanceService(BaseService):
    """Сервис для работы с балансом пользователя"""
    
    def __init__(self, session):
        super().__init__(session)
    
    async def get_balance(self, user_id: UUID) -> float:
        """
        Получает текущий баланс пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            float: Текущий баланс в монетах
        """
        try:
            async with get_user_service() as user_service:
                balance = await user_service.get_user_balance(user_id)
                return float(balance) if balance is not None else 0.0
                
        except Exception as e:
            logger.exception(f"Ошибка получения баланса пользователя {user_id}: {e}")
            return 0.0
    
    async def charge_balance(
        self, 
        user_id: UUID, 
        amount: float, 
        description: str = "Списание"
    ) -> Dict[str, Any]:
        """
        Списывает средства с баланса пользователя
        
        Args:
            user_id: ID пользователя
            amount: Сумма к списанию
            description: Описание операции
            
        Returns:
            Dict: Результат операции
        """
        try:
            async with get_user_service() as user_service:
                # Проверяем текущий баланс
                current_balance = await user_service.get_user_balance(user_id)
                
                if current_balance < amount:
                    return {
                        "success": False,
                        "error": f"Недостаточно средств. Требуется: {amount}, доступно: {current_balance}",
                        "current_balance": current_balance,
                        "required_amount": amount
                    }
                
                # Списываем средства
                new_balance = await user_service.remove_coins(user_id, amount)
                
                if new_balance is None:
                    return {
                        "success": False,
                        "error": "Ошибка списания средств",
                        "current_balance": current_balance
                    }
                
                logger.info(f"Списано {amount} монет с баланса пользователя {user_id}. Новый баланс: {new_balance}")
                
                return {
                    "success": True,
                    "amount_charged": amount,
                    "new_balance": new_balance,
                    "description": description,
                    "transaction_id": f"charge_{user_id}_{int(amount * 100)}_{hash(description) % 10000}"
                }
                
        except Exception as e:
            logger.exception(f"Ошибка списания баланса пользователя {user_id}: {e}")
            return {
                "success": False,
                "error": f"Ошибка операции: {str(e)}"
            }
    
    async def add_balance(
        self, 
        user_id: UUID, 
        amount: float, 
        description: str = "Пополнение"
    ) -> Dict[str, Any]:
        """
        Добавляет средства на баланс пользователя
        
        Args:
            user_id: ID пользователя
            amount: Сумма к добавлению
            description: Описание операции
            
        Returns:
            Dict: Результат операции
        """
        try:
            async with get_user_service() as user_service:
                # Получаем текущий баланс
                current_balance = await user_service.get_user_balance(user_id)
                
                # Добавляем средства
                new_balance = await user_service.add_coins(user_id, amount)
                
                if new_balance is None:
                    return {
                        "success": False,
                        "error": "Ошибка добавления средств",
                        "current_balance": current_balance
                    }
                
                logger.info(f"Добавлено {amount} монет на баланс пользователя {user_id}. Новый баланс: {new_balance}")
                
                return {
                    "success": True,
                    "amount_added": amount,
                    "new_balance": new_balance,
                    "description": description,
                    "transaction_id": f"add_{user_id}_{int(amount * 100)}_{hash(description) % 10000}"
                }
                
        except Exception as e:
            logger.exception(f"Ошибка пополнения баланса пользователя {user_id}: {e}")
            return {
                "success": False,
                "error": f"Ошибка операции: {str(e)}"
            }
    
    async def can_afford(self, user_id: UUID, amount: float) -> bool:
        """
        Проверяет, может ли пользователь позволить себе операцию
        
        Args:
            user_id: ID пользователя
            amount: Требуемая сумма
            
        Returns:
            bool: True если может позволить
        """
        try:
            balance = await self.get_balance(user_id)
            return balance >= amount
            
        except Exception as e:
            logger.exception(f"Ошибка проверки доступности средств для пользователя {user_id}: {e}")
            return False 