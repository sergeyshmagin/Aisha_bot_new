"""
Базовый сервис приложения
"""
from sqlalchemy.ext.asyncio import AsyncSession

from aisha_v2.app.core.types import Service


class BaseService(Service):
    """
    Базовый сервис приложения
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self._setup_repositories()

    def _setup_repositories(self):
        """
        Инициализация репозиториев.
        Должна быть переопределена в дочерних классах.
        """
        pass
