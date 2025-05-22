"""
Базовый класс для обработчиков
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from aiogram import Router
from aiogram.fsm.storage.base import BaseStorage
from aisha_v2.app.core.di import get_state_storage
from aisha_v2.app.core.database import get_session

logger = logging.getLogger(__name__)

class BaseHandler:
    """
    Базовый класс для всех обработчиков
    """
    def __init__(self):
        self.router = Router()
        self.state_storage: BaseStorage = get_state_storage()

    async def register_handlers(self):
        """
        Регистрация обработчиков
        Должен быть переопределен в дочерних классах
        """
        raise NotImplementedError

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator:
        """
        Получение сессии для работы с БД
        """
        async with get_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
