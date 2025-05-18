"""
Интеграционные тесты для PostgreSQL.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Base, User, UserState, UserBalance
from frontend_bot.repositories.user_repository import UserRepository
from frontend_bot.repositories.state_repository import StateRepository
from frontend_bot.repositories.balance_repository import BalanceRepository

class TestPostgresIntegration:
    """Базовый класс для интеграционных тестов PostgreSQL."""
    
    @pytest.fixture
    async def user_repository(self, test_session: AsyncSession) -> UserRepository:
        """Создает репозиторий пользователей."""
        return UserRepository(test_session)
    
    @pytest.fixture
    async def state_repository(self, test_session: AsyncSession) -> StateRepository:
        """Создает репозиторий состояний."""
        return StateRepository(test_session)
    
    @pytest.fixture
    async def balance_repository(self, test_session: AsyncSession) -> BalanceRepository:
        """Создает репозиторий балансов."""
        return BalanceRepository(test_session)
    
    @pytest.fixture
    async def test_user(self, user_repository: UserRepository) -> User:
        """Создает тестового пользователя."""
        user = User(
            telegram_id=123456789,
            username="test_user"
        )
        return await user_repository.create(user)
    
    @pytest.fixture
    async def test_state(self, state_repository: StateRepository, test_user: User) -> UserState:
        """Создает тестовое состояние."""
        state = UserState(
            user_id=test_user.id,
            state_data={"test": "data"}
        )
        return await state_repository.create(state)
    
    @pytest.fixture
    async def test_balance(self, balance_repository: BalanceRepository, test_user: User) -> UserBalance:
        """Создает тестовый баланс."""
        balance = UserBalance(
            user_id=test_user.id,
            coins=100.0
        )
        return await balance_repository.create(balance)
    
    async def test_user_creation(self, user_repository: UserRepository):
        """Тест создания пользователя."""
        user = User(
            telegram_id=987654321,
            username="new_user"
        )
        created_user = await user_repository.create(user)
        
        assert created_user.id is not None
        assert created_user.telegram_id == 987654321
        assert created_user.username == "new_user"
        
        # Проверяем, что пользователь действительно сохранен в БД
        retrieved_user = await user_repository.get_by_telegram_id(987654321)
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
    
    async def test_state_management(self, state_repository: StateRepository, test_user: User):
        """Тест управления состоянием."""
        # Создаем новое состояние
        new_state = UserState(
            user_id=test_user.id,
            state_data={"action": "test"}
        )
        created_state = await state_repository.create(new_state)
        
        assert created_state.id is not None
        assert created_state.user_id == test_user.id
        assert created_state.state_data == {"action": "test"}
        
        # Обновляем состояние
        updated_data = {"action": "updated"}
        updated_state = await state_repository.update_state(test_user.id, updated_data)
        
        assert updated_state.state_data == updated_data
        
        # Получаем состояние
        retrieved_state = await state_repository.get_state(test_user.id)
        assert retrieved_state is not None
        assert retrieved_state.state_data == updated_data
    
    async def test_balance_operations(self, balance_repository: BalanceRepository, test_user: User):
        """Тест операций с балансом."""
        # Создаем начальный баланс
        initial_balance = UserBalance(
            user_id=test_user.id,
            coins=100.0
        )
        created_balance = await balance_repository.create(initial_balance)
        
        assert created_balance.id is not None
        assert created_balance.coins == 100.0
        
        # Пополняем баланс
        updated_balance = await balance_repository.add_coins(test_user.id, 50.0)
        assert updated_balance.coins == 150.0
        
        # Списываем средства
        final_balance = await balance_repository.deduct_coins(test_user.id, 30.0)
        assert final_balance.coins == 120.0
        
        # Проверяем, что нельзя списать больше, чем есть
        with pytest.raises(ValueError):
            await balance_repository.deduct_coins(test_user.id, 200.0) 