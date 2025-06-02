"""
Базовые типы и интерфейсы
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

Model = TypeVar("Model")class Repository(Protocol[Model]):
    """Базовый интерфейс репозитория"""
    
    @abstractmethod
    async def get(self, id: Any) -> Optional[Model]:
        """Получить запись по ID"""
        pass
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Model:
        """Создать новую запись"""
        pass
    
    @abstractmethod
    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[Model]:
        """Обновить запись"""
        pass
    
    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Удалить запись"""
        passclass Service(ABC):
    """Базовый класс сервиса"""
    
    def __init__(self, session: AsyncSession):
        self.session = sessionclass Handler(ABC):
    """Базовый класс обработчика"""
    
    def __init__(self, services: "ServiceContainer"):
        self.services = servicesclass ServiceContainer:
    """Контейнер для всех сервисов"""
    
    def __init__(self):
        self.user_service: "UserService"
        self.avatar_service: "AvatarService"
