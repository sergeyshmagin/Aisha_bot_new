"""
Тесты для сервиса настроек.
"""

import pytest
from datetime import datetime
from uuid import UUID

from frontend_bot.services.settings_service import SettingsService
from database.models import UserSettings

@pytest.fixture
def settings_service(session):
    """Создает экземпляр сервиса настроек."""
    return SettingsService(session)

@pytest.fixture
def test_settings_data():
    """Создает тестовые данные настроек."""
    return {
        "language": "ru",
        "theme": "dark",
        "notifications": True,
        "sound_enabled": True,
        "auto_translate": False,
        "settings_data": {
            "key1": "value1",
            "key2": "value2"
        }
    }

@pytest.mark.asyncio
async def test_create_settings(settings_service, test_user_data, test_settings_data):
    """Тест создания настроек."""
    # Создаем пользователя
    user = await settings_service.create_user(**test_user_data)
    assert user.id == test_user_data["id"]
    
    # Создаем настройки
    settings = await settings_service.create_settings(
        user_id=user.id,
        **test_settings_data
    )
    
    assert isinstance(settings.id, UUID)
    assert settings.user_id == user.id
    assert settings.language == test_settings_data["language"]
    assert settings.theme == test_settings_data["theme"]
    assert settings.notifications == test_settings_data["notifications"]
    assert settings.sound_enabled == test_settings_data["sound_enabled"]
    assert settings.auto_translate == test_settings_data["auto_translate"]
    assert settings.settings_data == test_settings_data["settings_data"]
    assert isinstance(settings.created_at, datetime)
    assert isinstance(settings.updated_at, datetime)

@pytest.mark.asyncio
async def test_get_settings(settings_service, test_user_data, test_settings_data):
    """Тест получения настроек."""
    # Создаем пользователя
    user = await settings_service.create_user(**test_user_data)
    
    # Создаем настройки
    settings = await settings_service.create_settings(
        user_id=user.id,
        **test_settings_data
    )
    
    # Получаем настройки
    retrieved_settings = await settings_service.get_settings(user.id)
    assert retrieved_settings.id == settings.id
    assert retrieved_settings.user_id == user.id
    assert retrieved_settings.language == test_settings_data["language"]
    assert retrieved_settings.theme == test_settings_data["theme"]
    assert retrieved_settings.notifications == test_settings_data["notifications"]
    assert retrieved_settings.sound_enabled == test_settings_data["sound_enabled"]
    assert retrieved_settings.auto_translate == test_settings_data["auto_translate"]
    assert retrieved_settings.settings_data == test_settings_data["settings_data"]

@pytest.mark.asyncio
async def test_update_settings(settings_service, test_user_data, test_settings_data):
    """Тест обновления настроек."""
    # Создаем пользователя
    user = await settings_service.create_user(**test_user_data)
    
    # Создаем настройки
    settings = await settings_service.create_settings(
        user_id=user.id,
        **test_settings_data
    )
    
    # Обновляем настройки
    updated_data = {
        "language": "en",
        "theme": "light",
        "notifications": False,
        "sound_enabled": False,
        "auto_translate": True,
        "settings_data": {
            "key3": "value3",
            "key4": "value4"
        }
    }
    
    updated_settings = await settings_service.update_settings(
        user.id,
        **updated_data
    )
    
    assert updated_settings.id == settings.id
    assert updated_settings.user_id == user.id
    assert updated_settings.language == updated_data["language"]
    assert updated_settings.theme == updated_data["theme"]
    assert updated_settings.notifications == updated_data["notifications"]
    assert updated_settings.sound_enabled == updated_data["sound_enabled"]
    assert updated_settings.auto_translate == updated_data["auto_translate"]
    assert updated_settings.settings_data == updated_data["settings_data"]
    assert updated_settings.updated_at > settings.updated_at

@pytest.mark.asyncio
async def test_delete_settings(settings_service, test_user_data, test_settings_data):
    """Тест удаления настроек."""
    # Создаем пользователя
    user = await settings_service.create_user(**test_user_data)
    
    # Создаем настройки
    settings = await settings_service.create_settings(
        user_id=user.id,
        **test_settings_data
    )
    
    # Удаляем настройки
    await settings_service.delete_settings(user.id)
    
    # Проверяем, что настройки удалены
    retrieved_settings = await settings_service.get_settings(user.id)
    assert retrieved_settings is None

@pytest.mark.asyncio
async def test_get_settings_by_language(settings_service, test_user_data, test_settings_data):
    """Тест получения настроек по языку."""
    # Создаем пользователей
    user1 = await settings_service.create_user(**test_user_data)
    user2 = await settings_service.create_user(**{**test_user_data, "id": UUID(int=2)})
    
    # Создаем настройки с разными языками
    await settings_service.create_settings(
        user_id=user1.id,
        **test_settings_data
    )
    await settings_service.create_settings(
        user_id=user2.id,
        **{**test_settings_data, "language": "en"}
    )
    
    # Получаем настройки по языку
    ru_settings = await settings_service.get_settings_by_language("ru")
    assert len(ru_settings) == 1
    assert ru_settings[0].language == "ru"
    
    en_settings = await settings_service.get_settings_by_language("en")
    assert len(en_settings) == 1
    assert en_settings[0].language == "en"

@pytest.mark.asyncio
async def test_get_settings_by_theme(settings_service, test_user_data, test_settings_data):
    """Тест получения настроек по теме."""
    # Создаем пользователей
    user1 = await settings_service.create_user(**test_user_data)
    user2 = await settings_service.create_user(**{**test_user_data, "id": UUID(int=2)})
    
    # Создаем настройки с разными темами
    await settings_service.create_settings(
        user_id=user1.id,
        **test_settings_data
    )
    await settings_service.create_settings(
        user_id=user2.id,
        **{**test_settings_data, "theme": "light"}
    )
    
    # Получаем настройки по теме
    dark_settings = await settings_service.get_settings_by_theme("dark")
    assert len(dark_settings) == 1
    assert dark_settings[0].theme == "dark"
    
    light_settings = await settings_service.get_settings_by_theme("light")
    assert len(light_settings) == 1
    assert light_settings[0].theme == "light" 