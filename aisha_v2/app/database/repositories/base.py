"""
Базовый класс репозитория
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aisha_v2.app.core.types import Repository
from aisha_v2.app.database.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Repository[ModelType], Generic[ModelType]):
    """
    Базовый класс репозитория с основными CRUD операциями
    """

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def get(self, id: Any) -> Optional[ModelType]:
        """Получить запись по ID"""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[ModelType]:
        """Получить все записи"""
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, data: Dict[str, Any]) -> ModelType:
        """Создать новую запись"""
        obj = self.model(**data)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[ModelType]:
        """Обновить запись"""
        obj = await self.get(id)
        if obj:
            for key, value in data.items():
                setattr(obj, key, value)
            await self.session.flush()
            await self.session.refresh(obj)
        return obj

    async def delete(self, id: Any) -> bool:
        """Удалить запись"""
        obj = await self.get(id)
        if obj:
            await self.session.delete(obj)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: Any) -> bool:
        """Проверить существование записи"""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.first() is not None
