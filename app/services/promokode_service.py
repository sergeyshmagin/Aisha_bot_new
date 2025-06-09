"""
Сервис для работы с промокодами
"""
from typing import Optional, Tuple, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone

from app.core.logger import get_logger
from app.database.repositories.promokode import PromokodeRepository, PromokodeUsageRepository
from app.database.models.promokode import PromokodeType
from app.services.base import BaseService

logger = get_logger(__name__)


class PromokodeService(BaseService):
    """Сервис для работы с промокодами"""
    
    def __init__(self, session):
        super().__init__(session)
        self.promokode_repo = PromokodeRepository(session)
        self.usage_repo = PromokodeUsageRepository(session)
    
    async def validate_promokode(self, code: str, user_id: UUID) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Валидирует промокод для пользователя
        
        Returns:
            Tuple[bool, str, dict]: (валиден, сообщение_об_ошибке, данные_промокода)
        """
        try:
            # Проверяем возможность использования
            can_use, error_msg = await self.promokode_repo.can_user_use_promokode(code, user_id)
            
            if not can_use:
                return False, error_msg, None
            
            # Получаем промокод
            promokode = await self.promokode_repo.get_by_code(code)
            if not promokode:
                return False, "Промокод не найден", None
            
            # Формируем данные промокода
            promokode_data = {
                "id": promokode.id,
                "code": promokode.code,
                "type": promokode.type,
                "balance_amount": promokode.balance_amount,
                "bonus_amount": promokode.bonus_amount,
                "discount_percent": promokode.discount_percent,
                "description": promokode.description
            }
            
            return True, None, promokode_data
            
        except Exception as e:
            logger.exception(f"Ошибка валидации промокода {code}: {e}")
            return False, "Ошибка проверки промокода", None
    
    async def apply_promokode(
        self, 
        code: str, 
        user_id: UUID,
        package_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Применяет промокод
        
        Args:
            code: Код промокода
            user_id: ID пользователя
            package_info: Информация о пакете (для бонусных промокодов)
            
        Returns:
            Tuple[bool, str, dict]: (успех, сообщение, результат_применения)
        """
        try:
            # Валидируем промокод
            is_valid, error_msg, promokode_data = await self.validate_promokode(code, user_id)
            if not is_valid:
                return False, error_msg, None
            
            promokode = await self.promokode_repo.get_by_code(code)
            if not promokode:
                return False, "Промокод не найден", None
            
            # Рассчитываем бонусы в зависимости от типа
            amount_to_add = 0.0
            bonus_to_add = 0.0
            result_info = {}
            
            if promokode.type == PromokodeType.BALANCE:
                # Прямое пополнение баланса
                amount_to_add = promokode.balance_amount or 0.0
                result_info = {
                    "type": "balance",
                    "amount": amount_to_add,
                    "message": f"Баланс пополнен на {amount_to_add} монет"
                }
                
            elif promokode.type == PromokodeType.BONUS and package_info:
                # Бонус при пополнении
                base_amount = package_info.get("coins", 0)
                bonus_to_add = promokode.bonus_amount or 0.0
                amount_to_add = base_amount  # Основная сумма пакета
                
                result_info = {
                    "type": "bonus",
                    "base_amount": base_amount,
                    "bonus_amount": bonus_to_add,
                    "total_amount": base_amount + bonus_to_add,
                    "message": f"Получен бонус {bonus_to_add} монет при пополнении"
                }
                
            elif promokode.type == PromokodeType.DISCOUNT and package_info:
                # Скидка на пакет
                base_amount = package_info.get("coins", 0)
                discount_percent = promokode.discount_percent or 0.0
                discount_amount = base_amount * (discount_percent / 100)
                amount_to_add = base_amount + discount_amount
                
                result_info = {
                    "type": "discount",
                    "base_amount": base_amount,
                    "discount_percent": discount_percent,
                    "discount_amount": discount_amount,
                    "total_amount": amount_to_add,
                    "message": f"Применена скидка {discount_percent}% (+{discount_amount} монет)"
                }
            
            # Используем промокод
            success, error = await self.promokode_repo.use_promokode(
                code=code,
                user_id=user_id,
                amount_added=amount_to_add,
                bonus_added=bonus_to_add,
                package_used=package_info.get("package_name") if package_info else None
            )
            
            if not success:
                return False, error, None
            
            result_info.update({
                "promokode_code": code,
                "total_coins_added": amount_to_add + bonus_to_add
            })
            
            return True, "Промокод успешно применен", result_info
            
        except Exception as e:
            logger.exception(f"Ошибка применения промокода {code}: {e}")
            return False, "Ошибка применения промокода", None
    
    async def get_user_promokode_history(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Получить историю использования промокодов пользователем"""
        try:
            usages = await self.usage_repo.get_user_usages(user_id)
            
            history = []
            for usage in usages:
                history.append({
                    "code": usage.promokode.code,
                    "type": usage.promokode.type,
                    "amount_added": usage.amount_added or 0,
                    "bonus_added": usage.bonus_added or 0,
                    "package_used": usage.package_used,
                    "used_at": usage.used_at,
                    "description": usage.promokode.description
                })
            
            return history
            
        except Exception as e:
            logger.exception(f"Ошибка получения истории промокодов для пользователя {user_id}: {e}")
            return []
    
    async def create_promokode(
        self,
        code: str,
        promokode_type: PromokodeType,
        balance_amount: Optional[float] = None,
        bonus_amount: Optional[float] = None,
        discount_percent: Optional[float] = None,
        max_uses: Optional[int] = None,
        max_uses_per_user: Optional[int] = 1,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Создает новый промокод
        
        Returns:
            Tuple[bool, str]: (успех, сообщение_об_ошибке)
        """
        try:
            # Проверяем, что промокод не существует
            existing = await self.promokode_repo.get_by_code(code)
            if existing:
                return False, "Промокод с таким кодом уже существует"
            
            await self.promokode_repo.create_promokode(
                code=code,
                promokode_type=promokode_type,
                balance_amount=balance_amount,
                bonus_amount=bonus_amount,
                discount_percent=discount_percent,
                max_uses=max_uses,
                max_uses_per_user=max_uses_per_user,
                valid_from=valid_from,
                valid_until=valid_until,
                description=description,
                created_by=created_by
            )
            
            logger.info(f"Создан промокод {code} типа {promokode_type}")
            return True, None
            
        except Exception as e:
            logger.exception(f"Ошибка создания промокода {code}: {e}")
            return False, f"Ошибка создания промокода: {str(e)}"
    
    async def deactivate_promokode(self, code: str) -> Tuple[bool, Optional[str]]:
        """
        Деактивирует промокод
        
        Returns:
            Tuple[bool, str]: (успех, сообщение_об_ошибке)
        """
        try:
            success = await self.promokode_repo.deactivate_promokode(code)
            if success:
                logger.info(f"Промокод {code} деактивирован")
                return True, None
            else:
                return False, "Промокод не найден"
                
        except Exception as e:
            logger.exception(f"Ошибка деактивации промокода {code}: {e}")
            return False, f"Ошибка деактивации: {str(e)}"
    
    async def get_promokode_stats(self, code: str) -> Optional[Dict[str, Any]]:
        """Получить статистику использования промокода"""
        try:
            promokode = await self.promokode_repo.get_by_code(code)
            if not promokode:
                return None
            
            stats = await self.usage_repo.get_promokode_usage_stats(promokode.id)
            
            return {
                "code": promokode.code,
                "type": promokode.type,
                "is_active": promokode.is_active,
                "max_uses": promokode.max_uses,
                "current_uses": promokode.current_uses,
                "max_uses_per_user": promokode.max_uses_per_user,
                "valid_from": promokode.valid_from,
                "valid_until": promokode.valid_until,
                "description": promokode.description,
                "stats": stats
            }
            
        except Exception as e:
            logger.exception(f"Ошибка получения статистики промокода {code}: {e}")
            return None 