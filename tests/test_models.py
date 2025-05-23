"""
Тесты для моделей базы данных
"""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User, UserBalance, UserState, Avatar, AvatarPhoto


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """Тест создания пользователя"""
    # Arrange
    user_data = {
        "telegram_id": 123456789,
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "language_code": "ru",
        "is_premium": False
    }
    
    # Act
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Assert
    assert user.id is not None
    assert user.telegram_id == user_data["telegram_id"]
    assert user.first_name == user_data["first_name"]
    assert user.last_name == user_data["last_name"]
    assert user.username == user_data["username"]
    assert user.language_code == user_data["language_code"]
    assert user.is_premium == user_data["is_premium"]


@pytest.mark.asyncio
async def test_create_user_with_balance(db_session: AsyncSession):
    """Тест создания пользователя с балансом"""
    # Arrange
    user = User(
        telegram_id=123456789,
        first_name="Test",
        language_code="ru"
    )
    balance = UserBalance(coins=100.0)
    user.balance = balance
    
    # Act
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Assert
    assert user.balance is not None
    assert user.balance.coins == 100.0
    assert user.balance.user_id == user.id


@pytest.mark.asyncio
async def test_create_user_with_state(db_session: AsyncSession):
    """Тест создания пользователя с состоянием"""
    # Arrange
    user = User(
        telegram_id=123456789,
        first_name="Test",
        language_code="ru"
    )
    state = UserState(state_data={"current_step": "select_gender"})
    user.state = state
    
    # Act
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Assert
    assert user.state is not None
    assert user.state.state_data == {"current_step": "select_gender"}
    assert user.state.user_id == user.id


@pytest.mark.asyncio
async def test_create_avatar_with_photos(db_session: AsyncSession):
    """Тест создания аватара с фотографиями"""
    # Arrange
    user = User(
        telegram_id=123456789,
        first_name="Test",
        language_code="ru"
    )
    avatar = Avatar(
        name="Test Avatar",
        gender="male",
        status="draft",
        is_draft=True,
        avatar_data={"style": "anime"}
    )
    photo1 = AvatarPhoto(minio_key="test/photo1.jpg", order=1)
    photo2 = AvatarPhoto(minio_key="test/photo2.jpg", order=2)
    
    avatar.photos = [photo1, photo2]
    user.avatars = [avatar]
    
    # Act
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Assert
    assert len(user.avatars) == 1
    assert len(user.avatars[0].photos) == 2
    assert user.avatars[0].photos[0].minio_key == "test/photo1.jpg"
    assert user.avatars[0].photos[1].minio_key == "test/photo2.jpg"


@pytest.mark.asyncio
async def test_cascade_delete_user(db_session: AsyncSession):
    """Тест каскадного удаления пользователя"""
    # Arrange
    user = User(
        telegram_id=123456789,
        first_name="Test",
        language_code="ru"
    )
    balance = UserBalance(coins=100.0)
    state = UserState(state_data={"step": "test"})
    avatar = Avatar(
        name="Test Avatar",
        status="draft",
        is_draft=True
    )
    photo = AvatarPhoto(minio_key="test/photo.jpg", order=1)
    
    avatar.photos = [photo]
    user.avatars = [avatar]
    user.balance = balance
    user.state = state
    
    db_session.add(user)
    await db_session.commit()
    
    # Act
    await db_session.delete(user)
    await db_session.commit()
    
    # Assert
    result = await db_session.execute(select(User).where(User.telegram_id == 123456789))
    deleted_user = result.scalar_one_or_none()
    assert deleted_user is None
    
    result = await db_session.execute(select(UserBalance).where(UserBalance.user_id == user.id))
    deleted_balance = result.scalar_one_or_none()
    assert deleted_balance is None
    
    result = await db_session.execute(select(UserState).where(UserState.user_id == user.id))
    deleted_state = result.scalar_one_or_none()
    assert deleted_state is None
    
    result = await db_session.execute(select(Avatar).where(Avatar.user_id == user.id))
    deleted_avatar = result.scalar_one_or_none()
    assert deleted_avatar is None
    
    result = await db_session.execute(select(AvatarPhoto).where(AvatarPhoto.avatar_id == avatar.id))
    deleted_photo = result.scalar_one_or_none()
    assert deleted_photo is None
