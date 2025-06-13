"""
Репозитории для работы с промокодами
"""
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload

from app.database.models import Promokode, PromokodeUsage, PromokodeType
from app.database.repositories.base import BaseRepository


class PromokodeRepository(BaseRepository[Promokode]):
    """Репозиторий для работы с промокодами"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Promokode)

    async def get_by_code(self, code: str) -> Optional[Promokode]:
        """Получить промокод по коду"""
        stmt = select(self.model).where(
            and_(
                self.model.code == code.upper(),
                self.model.is_active == True
            )
        ).options(selectinload(self.model.usages))
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_valid_promokode(self, code: str) -> Optional[Promokode]:
        """Получить валидный промокод"""
        promokode = await self.get_by_code(code)
        if promokode and promokode.is_valid():
            return promokode
        return None

    async def can_user_use_promokode(self, code: str, user_id: UUID) -> tuple[bool, Optional[str]]:
        """
        Проверяет, может ли пользователь использовать промокод
        
        Returns:
            tuple[bool, str]: (можно_использовать, причина_отказа)
        """
        promokode = await self.get_by_code(code)
        
        if not promokode:
            return False, "Промокод не найден"
            
        if not promokode.is_active:
            return False, "Промокод неактивен"
            
        if not promokode.is_valid():
            return False, "Промокод недействителен или истек"
            
        if not promokode.can_be_used_by_user(user_id):
            return False, "Вы уже использовали этот промокод максимальное количество раз"
            
        return True, None

    async def use_promokode(
        self, 
        code: str, 
        user_id: UUID,
        amount_added: Optional[float] = None,
        bonus_added: Optional[float] = None,
        package_used: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Использует промокод
        
        Returns:
            tuple[bool, str]: (успех, сообщение_об_ошибке)
        """
        # Проверяем возможность использования
        can_use, error_msg = await self.can_user_use_promokode(code, user_id)
        if not can_use:
            return False, error_msg
            
        # Получаем промокод
        promokode = await self.get_by_code(code)
        if not promokode:
            return False, "Промокод не найден"
        
        try:
            # Создаем запись использования
            usage = PromokodeUsage(
                promokode_id=promokode.id,
                user_id=user_id,
                amount_added=amount_added,
                bonus_added=bonus_added,
                package_used=package_used,
                used_at=datetime.now(timezone.utc)
            )
            
            self.session.add(usage)
            
            # Увеличиваем счетчик использований
            promokode.current_uses += 1
            
            await self.session.commit()
            await self.session.refresh(promokode)
            
            return True, None
            
        except Exception as e:
            await self.session.rollback()
            return False, f"Ошибка использования промокода: {str(e)}"

    async def get_user_promokode_usages(self, user_id: UUID, code: str) -> int:
        """Получить количество использований промокода пользователем"""
        stmt = select(func.count(PromokodeUsage.id)).select_from(
            PromokodeUsage.__table__.join(Promokode.__table__)
        ).where(
            and_(
                PromokodeUsage.user_id == user_id,
                Promokode.code == code.upper()
            )
        )
        
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_active_promokodes(self) -> List[Promokode]:
        """Получить все активные промокоды"""
        stmt = select(self.model).where(
            and_(
                self.model.is_active == True,
                self.model.valid_until >= datetime.now(timezone.utc)
            )
        ).order_by(self.model.created_at.desc())
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_promokodes_by_type(self, promokode_type: PromokodeType) -> List[Promokode]:
        """Получить промокоды по типу"""
        stmt = select(self.model).where(
            and_(
                self.model.type == promokode_type,
                self.model.is_active == True
            )
        ).order_by(self.model.created_at.desc())
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_promokode(
        self,
        code: str,
        promokode_type: PromokodeType,
        balance_amount: Optional[float] = None,
        bonus_amount: Optional[float] = None,
        discount_percent: Optional[float] = None,
        max_uses: Optional[int] = None,
        max_uses_per_user: Optional[int] = None,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Promokode:
        """Создать новый промокод"""
        
        promokode_data = {
            "code": code.upper(),
            "type": promokode_type,
            "balance_amount": balance_amount,
            "bonus_amount": bonus_amount,
            "discount_percent": discount_percent,
            "max_uses": max_uses,
            "max_uses_per_user": max_uses_per_user,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "description": description,
            "created_by": created_by,
            "is_active": True
        }
        
        return await self.create(promokode_data)

    async def deactivate_promokode(self, code: str) -> bool:
        """Деактивировать промокод"""
        promokode = await self.get_by_code(code)
        if promokode:
            await self.update(promokode.id, {"is_active": False})
            return True
        return False


class PromokodeUsageRepository(BaseRepository[PromokodeUsage]):
    """Репозиторий для работы с использованиями промокодов"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, PromokodeUsage)

    async def get_user_usages(self, user_id: UUID) -> List[PromokodeUsage]:
        """Получить все использования промокодов пользователем"""
        stmt = select(self.model).where(
            self.model.user_id == user_id
        ).options(
            selectinload(self.model.promokode)
        ).order_by(self.model.used_at.desc())
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_promokode_usage_stats(self, promokode_id: UUID) -> dict:
        """Получить статистику использования промокода"""
        stmt = select(
            func.count(self.model.id).label("total_uses"),
            func.count(func.distinct(self.model.user_id)).label("unique_users"),
            func.sum(self.model.amount_added).label("total_amount"),
            func.sum(self.model.bonus_added).label("total_bonus")
        ).where(self.model.promokode_id == promokode_id)
        
        result = await self.session.execute(stmt)
        row = result.first()
        
        return {
            "total_uses": row.total_uses or 0,
            "unique_users": row.unique_users or 0,
            "total_amount": float(row.total_amount or 0),
            "total_bonus": float(row.total_bonus or 0)
        } 