"""
Менеджер баланса для генерации изображений
Проверка и списание средств пользователя
"""
from uuid import UUID

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class BalanceManager:
    """Менеджер баланса для генерации"""
    
    def __init__(self):
        pass
    
    def _get_user_service(self):
        """Получает UserService с сессией"""
        from app.core.di import get_user_service
        return get_user_service()
    
    def calculate_cost(self, num_images: int) -> float:
        """
        Рассчитывает стоимость генерации
        
        Args:
            num_images: Количество изображений
            
        Returns:
            float: Общая стоимость
        """
        return settings.IMAGE_GENERATION_COST * num_images
    
    async def check_and_charge_balance(self, user_id: UUID, cost: float) -> float:
        """
        Проверяет баланс и списывает средства
        
        Args:
            user_id: ID пользователя
            cost: Стоимость операции
            
        Returns:
            float: Остаток баланса после списания
            
        Raises:
            ValueError: Если недостаточно средств
        """
        async with self._get_user_service() as user_service:
            user_balance = await user_service.get_user_balance(user_id)
            if user_balance < cost:
                raise ValueError(
                    f"Недостаточно баланса. Требуется: {cost}, доступно: {user_balance}"
                )
            
            # Списываем баланс
            remaining_balance = await user_service.remove_coins(user_id, cost)
            if remaining_balance is None:
                raise ValueError("Ошибка списания баланса")
            
            logger.info(f"Списано {cost} единиц баланса. Остаток: {remaining_balance}")
            return remaining_balance
    
    async def refund_balance(self, user_id: UUID, cost: float):
        """
        Возвращает баланс при ошибке
        
        Args:
            user_id: ID пользователя
            cost: Сумма к возврату
        """
        try:
            async with self._get_user_service() as user_service:
                await user_service.add_coins(user_id, cost)
            
            logger.info(f"Возвращено {cost} единиц баланса пользователю {user_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка возврата баланса: {e}") 