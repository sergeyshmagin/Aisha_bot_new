"""
Сервис для работы с пользователями
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import re

from app.database.models import User
from app.database.repositories import BalanceRepository, StateRepository, UserRepository
from app.services.base import BaseService


class UserService(BaseService):
    """
    Сервис для работы с пользователями
    """

    def _setup_repositories(self):
        """Инициализация репозиториев"""
        self.user_repo = UserRepository(self.session)
        self.state_repo = StateRepository(self.session)
        self.balance_repo = BalanceRepository(self.session)

    async def register_user(self, telegram_data: Dict) -> User:
        """
        Регистрация нового пользователя или обновление существующего
        """
        import logging
        
        # Получаем telegram_id из данных
        if "id" in telegram_data:
            telegram_id = str(telegram_data["id"])  # Преобразуем в строку
        elif "telegram_id" in telegram_data:
            telegram_id = str(telegram_data["telegram_id"])  # Преобразуем в строку
        else:
            # Если нет ни id, ни telegram_id, возвращаем None
            logging.error(f"Невозможно зарегистрировать пользователя без telegram_id: {telegram_data}")
            return None
            
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        
        # Получаем часовой пояс из сообщения пользователя, если он есть
        timezone = None
        if "location" in telegram_data and "user_location" in telegram_data["location"]:
            # Если в данных есть информация о местоположении пользователя
            timezone = self._get_timezone_from_location(telegram_data["location"]["user_location"])
        
        user_data = {
            "telegram_id": telegram_id,  # Уже преобразовано в строку
            "first_name": telegram_data.get("first_name", "Пользователь"),
            "last_name": telegram_data.get("last_name"),
            "username": telegram_data.get("username"),
            "language_code": telegram_data.get("language_code", "ru"),
            "is_premium": telegram_data.get("is_premium", False),
            "is_bot": telegram_data.get("is_bot", False),  # Добавляем поле is_bot
            "is_blocked": telegram_data.get("is_blocked", False),  # Добавляем поле is_blocked
        }
        
        # Добавляем часовой пояс, только если он был определен
        if timezone:
            user_data["timezone"] = timezone

        if user:
            return await self.user_repo.update(user.id, user_data)
        
        try:
            user = await self.user_repo.create(user_data)
            await self.balance_repo.create({"user_id": user.id, "coins": 0.0})
            return user
        except Exception as e:
            logging.error(f"Ошибка при создании пользователя: {e}")
            return None

    async def get_user(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        return await self.user_repo.get(user_id)

    async def get_user_by_telegram_id(self, telegram_id) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        # Преобразуем telegram_id в строку, так как в базе данных он хранится как VARCHAR
        telegram_id_str = str(telegram_id)
        return await self.user_repo.get_by_telegram_id(telegram_id_str)
    
    def _get_timezone_from_location(self, location: Dict) -> Optional[str]:
        """Получить часовой пояс из местоположения пользователя"""
        # Здесь можно реализовать более сложную логику определения часового пояса
        # на основе координат пользователя, но для простоты используем UTC+5
        return "UTC+5"
    
    async def get_user_timezone(self, user_id: int) -> str:
        """Получить часовой пояс пользователя"""
        user = await self.get_user_by_telegram_id(user_id)
        if user and user.timezone:
            return user.timezone
        return "UTC+5"  # Значение по умолчанию
    
    async def update_user_timezone(self, user_id: int, timezone: str) -> User:
        """Обновить часовой пояс пользователя"""
        user = await self.get_user_by_telegram_id(user_id)
        if user:
            return await self.user_repo.update(user.id, {"timezone": timezone})
        return None
    
    async def format_date_with_user_timezone(self, user_id: int, date: datetime, format_str: str = "%d.%m.%Y %H:%M") -> str:
        """Форматировать дату с учетом часового пояса пользователя"""
        from app.utils.timezone import TimezoneUtils
        
        timezone = await self.get_user_timezone(user_id)
        return TimezoneUtils.format_date_with_timezone(date, timezone, format_str)

    async def set_user_state(self, telegram_id, state_data: Dict) -> None:
        """Установить состояние пользователя"""
        # Преобразуем telegram_id в строку для работы с базой данных
        telegram_id_str = str(telegram_id)
        
        # Сначала получаем пользователя по telegram_id
        user = await self.get_user_by_telegram_id(telegram_id_str)
        if not user:
            # Если пользователь не найден, создаем его
            # Создаем минимальные данные для регистрации
            user_data = {
                "telegram_id": telegram_id_str,
                "first_name": "Пользователь",
                "language_code": "ru",
                "is_bot": False,  # Добавляем поле is_bot
                "is_blocked": False  # Добавляем поле is_blocked
            }
            try:
                user = await self.register_user(user_data)
                if not user:
                    # Если не удалось создать пользователя, выходим
                    return
            except Exception as e:
                # В случае ошибки при создании пользователя, выходим
                import logging
                logging.error(f"Ошибка при создании пользователя: {e}")
                return
        
        # Используем UUID пользователя для установки состояния
        await self.state_repo.set_state(user.id, state_data)

    async def get_user_state(self, telegram_id) -> Optional[Dict]:
        """Получить состояние пользователя"""
        # Преобразуем telegram_id в строку для работы с базой данных
        telegram_id_str = str(telegram_id)
        
        # Сначала получаем пользователя по telegram_id
        user = await self.get_user_by_telegram_id(telegram_id_str)
        if not user:
            return None
        
        # Используем UUID пользователя для получения состояния
        state = await self.state_repo.get_user_state(user.id)
        return state.state_data if state else None

    async def clear_user_state(self, telegram_id) -> None:
        """Очистить состояние пользователя"""
        # Преобразуем telegram_id в строку для работы с базой данных
        telegram_id_str = str(telegram_id)
        
        # Сначала получаем пользователя по telegram_id
        user = await self.get_user_by_telegram_id(telegram_id_str)
        if user:
            # Используем UUID пользователя для очистки состояния
            await self.state_repo.clear_state(user.id)

    async def get_user_balance(self, user_id: int) -> float:
        """Получить баланс пользователя"""
        balance = await self.balance_repo.get_user_balance(user_id)
        return balance.coins if balance else 0.0

    async def add_coins(self, user_id: int, amount: float) -> float:
        """Добавить монеты пользователю"""
        balance = await self.balance_repo.add_coins(user_id, amount)
        return balance.coins

    async def remove_coins(self, user_id: int, amount: float) -> Optional[float]:
        """Снять монеты с баланса пользователя"""
        balance = await self.balance_repo.remove_coins(user_id, amount)
        return balance.coins if balance else None

    async def has_enough_coins(self, user_id: int, amount: float) -> bool:
        """Проверить, достаточно ли монет у пользователя"""
        return await self.balance_repo.has_enough_coins(user_id, amount)
