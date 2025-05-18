import pytest
import uuid
from unittest.mock import MagicMock, patch
from frontend_bot.services.avatar_service import AvatarService
from database.models import UserAvatar
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from minio.error import S3Error
import asyncio
from uuid import UUID

@pytest.fixture
def minio_client():
    """Мок MinIO клиента."""
    client = MagicMock()
    client.bucket_exists.return_value = True
    return client

@pytest.fixture
def avatar_service(minio_client):
    return AvatarService(minio_client)

@pytest.fixture
def fake_user_id():
    return uuid.uuid4()

@pytest.fixture
def fake_avatar_id():
    return uuid.uuid4()

@pytest.fixture
def fake_original():
    return b"fake_image_data"

@pytest.fixture
def fake_processed():
    return b"fake_processed_data"

@pytest.fixture
def test_avatar_data():
    """Создает тестовые данные аватара."""
    return {
        "avatar_name": "test_avatar",
        "avatar_type": "image/png",
        "avatar_size": 1024,
        "avatar_path": "/path/to/test_avatar.png",
        "avatar_data": {
            "key1": "value1",
            "key2": "value2"
        }
    }

@pytest.mark.asyncio
async def test_save_and_get_avatar(avatar_service, async_session: AsyncSession, fake_user_id, fake_avatar_id, fake_original, fake_processed):
    """Тест сохранения и получения аватара."""
    # Сохраняем аватар
    avatar = await avatar_service.save_avatar(
        db=async_session,
        user_id=fake_user_id,
        avatar_id=fake_avatar_id,
        original=fake_original,
        processed=fake_processed,
        metadata={"name": "Test Avatar"},
        original_ext="png",
        processed_ext="webp"
    )
    assert avatar.user_id == fake_user_id
    assert avatar.avatar_data["name"] == "Test Avatar"
    # Получаем аватар
    loaded = await avatar_service.get_avatar(
        db=async_session,
        user_id=fake_user_id,
        avatar_id=fake_avatar_id
    )
    assert loaded is not None
    assert loaded.id == fake_avatar_id
    assert loaded.avatar_data["original_path"].endswith("original.png")

@pytest.mark.asyncio
async def test_list_user_avatars(avatar_service, async_session: AsyncSession, fake_user_id, fake_avatar_id, fake_original):
    """Тест получения списка аватаров пользователя."""
    # Сохраняем аватар
    await avatar_service.save_avatar(
        db=async_session,
        user_id=fake_user_id,
        avatar_id=fake_avatar_id,
        original=fake_original,
        metadata={"name": "Test Avatar"}
    )
    # Получаем список
    avatars = await avatar_service.list_user_avatars(
        db=async_session,
        user_id=fake_user_id
    )
    assert len(avatars) >= 1
    assert any(a.id == fake_avatar_id for a in avatars)

@pytest.mark.asyncio
async def test_delete_avatar(avatar_service, async_session: AsyncSession, fake_user_id, fake_avatar_id, fake_original):
    """Тест удаления аватара."""
    # Сохраняем аватар
    await avatar_service.save_avatar(
        db=async_session,
        user_id=fake_user_id,
        avatar_id=fake_avatar_id,
        original=fake_original,
        metadata={"name": "Test Avatar"}
    )
    # Удаляем аватар
    await avatar_service.delete_avatar(
        db=async_session,
        user_id=fake_user_id,
        avatar_id=fake_avatar_id
    )
    # Проверяем, что аватар удалён
    avatar = await avatar_service.get_avatar(
        db=async_session,
        user_id=fake_user_id,
        avatar_id=fake_avatar_id
    )
    assert avatar is None

@pytest.mark.asyncio
async def test_minio_error_handling(avatar_service, async_session: AsyncSession, fake_user_id, fake_avatar_id, fake_original):
    """Тест обработки ошибок MinIO."""
    # Симулируем ошибку MinIO
    avatar_service.minio.put_object.side_effect = S3Error("Test error")
    
    with pytest.raises(S3Error):
        await avatar_service.save_avatar(
            db=async_session,
            user_id=fake_user_id,
            avatar_id=fake_avatar_id,
            original=fake_original
        )

@pytest.mark.asyncio
async def test_metadata_validation(avatar_service, async_session: AsyncSession, fake_user_id, fake_avatar_id, fake_original):
    """Тест валидации метаданных аватара."""
    # Тест с некорректными метаданными
    invalid_metadata = {
        "name": 123,  # Должно быть строкой
        "size": "large",  # Должно быть числом
        "created_at": "invalid_date"  # Должно быть datetime
    }
    
    avatar = await avatar_service.save_avatar(
        db=async_session,
        user_id=fake_user_id,
        avatar_id=fake_avatar_id,
        original=fake_original,
        metadata=invalid_metadata
    )
    
    # Проверяем, что метаданные сохранены как есть (валидация на уровне БД)
    assert avatar.avatar_data == invalid_metadata

@pytest.mark.asyncio
async def test_image_formats(avatar_service, async_session: AsyncSession, fake_user_id, fake_avatar_id, fake_original):
    """Тест работы с разными форматами изображений."""
    formats = [
        ("png", "webp"),
        ("jpg", "webp"),
        ("jpeg", "webp"),
        ("gif", "webp")
    ]
    
    for orig_ext, proc_ext in formats:
        avatar = await avatar_service.save_avatar(
            db=async_session,
            user_id=fake_user_id,
            avatar_id=uuid.uuid4(),
            original=fake_original,
            processed=fake_original,  # Для теста используем те же данные
            original_ext=orig_ext,
            processed_ext=proc_ext
        )
        
        assert avatar.avatar_data["original_path"].endswith(f".{orig_ext}")
        assert avatar.avatar_data["processed_path"].endswith(f".{proc_ext}")

@pytest.mark.asyncio
async def test_concurrent_access(avatar_service, async_session: AsyncSession, fake_user_id, fake_original):
    """Тест конкурентного доступа к аватарам."""
    async def save_avatar(avatar_id):
        return await avatar_service.save_avatar(
            db=async_session,
            user_id=fake_user_id,
            avatar_id=avatar_id,
            original=fake_original
        )
    
    # Создаем несколько аватаров одновременно
    avatar_ids = [uuid.uuid4() for _ in range(5)]
    tasks = [save_avatar(avatar_id) for avatar_id in avatar_ids]
    avatars = await asyncio.gather(*tasks)
    
    # Проверяем, что все аватары созданы
    assert len(avatars) == len(avatar_ids)
    
    # Проверяем, что все аватары доступны
    for avatar in avatars:
        loaded = await avatar_service.get_avatar(
            db=async_session,
            user_id=fake_user_id,
            avatar_id=avatar.id
        )
        assert loaded is not None
        assert loaded.id == avatar.id 

@pytest.mark.asyncio
async def test_create_avatar(avatar_service, test_user_data, test_avatar_data):
    """Тест создания аватара."""
    # Создаем пользователя
    user = await avatar_service.create_user(**test_user_data)
    assert user.id == test_user_data["id"]
    
    # Создаем аватар
    avatar = await avatar_service.create_avatar(
        user_id=user.id,
        **test_avatar_data
    )
    
    assert isinstance(avatar.id, UUID)
    assert avatar.user_id == user.id
    assert avatar.avatar_name == test_avatar_data["avatar_name"]
    assert avatar.avatar_type == test_avatar_data["avatar_type"]
    assert avatar.avatar_size == test_avatar_data["avatar_size"]
    assert avatar.avatar_path == test_avatar_data["avatar_path"]
    assert avatar.avatar_data == test_avatar_data["avatar_data"]
    assert isinstance(avatar.created_at, datetime)
    assert isinstance(avatar.updated_at, datetime)

@pytest.mark.asyncio
async def test_get_avatar(avatar_service, test_user_data, test_avatar_data):
    """Тест получения аватара."""
    # Создаем пользователя
    user = await avatar_service.create_user(**test_user_data)
    
    # Создаем аватар
    avatar = await avatar_service.create_avatar(
        user_id=user.id,
        **test_avatar_data
    )
    
    # Получаем аватар
    retrieved_avatar = await avatar_service.get_avatar(avatar.id)
    assert retrieved_avatar.id == avatar.id
    assert retrieved_avatar.user_id == user.id
    assert retrieved_avatar.avatar_name == test_avatar_data["avatar_name"]
    assert retrieved_avatar.avatar_type == test_avatar_data["avatar_type"]
    assert retrieved_avatar.avatar_size == test_avatar_data["avatar_size"]
    assert retrieved_avatar.avatar_path == test_avatar_data["avatar_path"]
    assert retrieved_avatar.avatar_data == test_avatar_data["avatar_data"]

@pytest.mark.asyncio
async def test_update_avatar(avatar_service, test_user_data, test_avatar_data):
    """Тест обновления аватара."""
    # Создаем пользователя
    user = await avatar_service.create_user(**test_user_data)
    
    # Создаем аватар
    avatar = await avatar_service.create_avatar(
        user_id=user.id,
        **test_avatar_data
    )
    
    # Обновляем аватар
    updated_data = {
        "avatar_name": "updated_avatar",
        "avatar_type": "image/jpeg",
        "avatar_size": 2048,
        "avatar_path": "/path/to/updated_avatar.jpg",
        "avatar_data": {
            "key3": "value3",
            "key4": "value4"
        }
    }
    
    updated_avatar = await avatar_service.update_avatar(
        avatar.id,
        **updated_data
    )
    
    assert updated_avatar.id == avatar.id
    assert updated_avatar.user_id == user.id
    assert updated_avatar.avatar_name == updated_data["avatar_name"]
    assert updated_avatar.avatar_type == updated_data["avatar_type"]
    assert updated_avatar.avatar_size == updated_data["avatar_size"]
    assert updated_avatar.avatar_path == updated_data["avatar_path"]
    assert updated_avatar.avatar_data == updated_data["avatar_data"]
    assert updated_avatar.updated_at > avatar.updated_at

@pytest.mark.asyncio
async def test_delete_avatar(avatar_service, test_user_data, test_avatar_data):
    """Тест удаления аватара."""
    # Создаем пользователя
    user = await avatar_service.create_user(**test_user_data)
    
    # Создаем аватар
    avatar = await avatar_service.create_avatar(
        user_id=user.id,
        **test_avatar_data
    )
    
    # Удаляем аватар
    await avatar_service.delete_avatar(avatar.id)
    
    # Проверяем, что аватар удален
    retrieved_avatar = await avatar_service.get_avatar(avatar.id)
    assert retrieved_avatar is None

@pytest.mark.asyncio
async def test_get_user_avatars(avatar_service, test_user_data, test_avatar_data):
    """Тест получения аватаров пользователя."""
    # Создаем пользователя
    user = await avatar_service.create_user(**test_user_data)
    
    # Создаем аватары
    avatar1 = await avatar_service.create_avatar(
        user_id=user.id,
        **test_avatar_data
    )
    avatar2 = await avatar_service.create_avatar(
        user_id=user.id,
        **{**test_avatar_data, "avatar_name": "test_avatar2"}
    )
    
    # Получаем аватары пользователя
    user_avatars = await avatar_service.get_user_avatars(user.id)
    assert len(user_avatars) == 2
    assert all(isinstance(a.id, UUID) for a in user_avatars)
    assert all(a.user_id == user.id for a in user_avatars)
    assert {a.avatar_name for a in user_avatars} == {"test_avatar", "test_avatar2"}

@pytest.mark.asyncio
async def test_get_avatars_by_type(avatar_service, test_user_data, test_avatar_data):
    """Тест получения аватаров по типу."""
    # Создаем пользователя
    user = await avatar_service.create_user(**test_user_data)
    
    # Создаем аватары разных типов
    await avatar_service.create_avatar(
        user_id=user.id,
        **test_avatar_data
    )
    await avatar_service.create_avatar(
        user_id=user.id,
        **{**test_avatar_data, "avatar_name": "test_avatar2", "avatar_type": "image/jpeg"}
    )
    
    # Получаем аватары по типу
    png_avatars = await avatar_service.get_avatars_by_type("image/png")
    assert len(png_avatars) == 1
    assert png_avatars[0].avatar_type == "image/png"
    
    jpeg_avatars = await avatar_service.get_avatars_by_type("image/jpeg")
    assert len(jpeg_avatars) == 1
    assert jpeg_avatars[0].avatar_type == "image/jpeg"

@pytest.mark.asyncio
async def test_get_avatars_by_data(avatar_service, test_user_data, test_avatar_data):
    """Тест получения аватаров по данным."""
    # Создаем пользователя
    user = await avatar_service.create_user(**test_user_data)
    
    # Создаем аватары с разными данными
    await avatar_service.create_avatar(
        user_id=user.id,
        **test_avatar_data
    )
    await avatar_service.create_avatar(
        user_id=user.id,
        **{**test_avatar_data, "avatar_name": "test_avatar2", "avatar_data": {"key3": "value3"}}
    )
    
    # Получаем аватары по данным
    avatars_with_key1 = await avatar_service.get_avatars_by_data("key1", "value1")
    assert len(avatars_with_key1) == 1
    assert avatars_with_key1[0].avatar_data["key1"] == "value1"
    
    avatars_with_key3 = await avatar_service.get_avatars_by_data("key3", "value3")
    assert len(avatars_with_key3) == 1
    assert avatars_with_key3[0].avatar_data["key3"] == "value3" 