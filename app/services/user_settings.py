"""
Сервис для управления настройками пользователей
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.logger import get_logger
from app.core.database import get_session
from app.database.models.user_settings import UserSettings

logger = get_logger(__name__)class UserSettingsService:
    """Сервис для управления настройками пользователей"""
    
    async def get_user_settings(self, user_id: UUID) -> Optional[UserSettings]:
        """Получает настройки пользователя, создает если не существуют"""
        try:
            async with get_session() as session:
                stmt = select(UserSettings).where(UserSettings.user_id == user_id)
                result = await session.execute(stmt)
                settings = result.scalar_one_or_none()
                
                if not settings:
                    # Создаем настройки по умолчанию
                    settings = await self.create_default_settings(user_id)
                    logger.info(f"Созданы настройки по умолчанию для пользователя {user_id}")
                
                return settings
                
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка получения настроек пользователя {user_id}: {e}")
            return None
    
    async def create_default_settings(self, user_id: UUID) -> Optional[UserSettings]:
        """Создает настройки по умолчанию для пользователя"""
        try:
            async with get_session() as session:
                default_values = UserSettings.get_default_settings()
                
                settings = UserSettings(
                    user_id=user_id,
                    **default_values
                )
                
                session.add(settings)
                await session.commit()
                await session.refresh(settings)
                
                logger.info(f"Настройки по умолчанию созданы для пользователя {user_id}")
                return settings
                
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка создания настроек для пользователя {user_id}: {e}")
            return None
    
    async def update_user_settings(
        self, 
        user_id: UUID, 
        **updates
    ) -> Optional[UserSettings]:
        """Обновляет настройки пользователя"""
        try:
            async with get_session() as session:
                stmt = select(UserSettings).where(UserSettings.user_id == user_id)
                result = await session.execute(stmt)
                settings = result.scalar_one_or_none()
                
                if not settings:
                    # Создаем настройки если не существуют
                    settings = UserSettings(user_id=user_id, **UserSettings.get_default_settings())
                    session.add(settings)
                
                # Обновляем поля
                for key, value in updates.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
                
                await session.commit()
                await session.refresh(settings)
                
                logger.info(f"Настройки обновлены для пользователя {user_id}: {updates}")
                return settings
                
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка обновления настроек пользователя {user_id}: {e}")
            return None
    
    async def get_default_aspect_ratio(self, user_id: UUID) -> str:
        """Получает размер по умолчанию для пользователя"""
        settings = await self.get_user_settings(user_id)
        return settings.default_aspect_ratio if settings else "1:1"
    
    async def set_default_aspect_ratio(self, user_id: UUID, aspect_ratio: str) -> bool:
        """Устанавливает размер по умолчанию для пользователя"""
        # Проверяем что размер валиден
        valid_ratios = UserSettings.get_aspect_ratio_options()
        if aspect_ratio not in valid_ratios:
            logger.error(f"Недопустимое соотношение сторон: {aspect_ratio}")
            return False
        
        settings = await self.update_user_settings(
            user_id, 
            default_aspect_ratio=aspect_ratio
        )
        
        return settings is not None
    
    async def is_quick_mode_enabled(self, user_id: UUID) -> bool:
        """Проверяет включен ли быстрый режим для пользователя"""
        settings = await self.get_user_settings(user_id)
        return settings.quick_generation_mode if settings else False
    
    async def set_quick_mode(self, user_id: UUID, enabled: bool) -> bool:
        """Включает/выключает быстрый режим для пользователя"""
        settings = await self.update_user_settings(
            user_id, 
            quick_generation_mode=enabled
        )
        
        return settings is not None
    
    async def is_auto_enhance_enabled(self, user_id: UUID) -> bool:
        """Проверяет включено ли автоулучшение промптов"""
        settings = await self.get_user_settings(user_id)
        return settings.auto_enhance_prompts if settings else True
    
    async def set_auto_enhance(self, user_id: UUID, enabled: bool) -> bool:
        """Включает/выключает автоулучшение промптов"""
        settings = await self.update_user_settings(
            user_id, 
            auto_enhance_prompts=enabled
        )
        
        return settings is not None
    
    async def get_language_preference(self, user_id: UUID) -> str:
        """Получает предпочитаемый язык пользователя"""
        settings = await self.get_user_settings(user_id)
        return settings.language_preference if settings else "ru"
    
    async def set_language_preference(self, user_id: UUID, language: str) -> bool:
        """Устанавливает предпочитаемый язык пользователя"""
        if language not in ["ru", "en"]:
            logger.error(f"Недопустимый язык: {language}")
            return False
        
        settings = await self.update_user_settings(
            user_id, 
            language_preference=language
        )
        
        return settings is not None
    
    async def should_show_technical_details(self, user_id: UUID) -> bool:
        """Проверяет нужно ли показывать технические детали"""
        settings = await self.get_user_settings(user_id)
        return settings.show_technical_details if settings else False
    
    async def set_show_technical_details(self, user_id: UUID, enabled: bool) -> bool:
        """Включает/выключает показ технических деталей"""
        settings = await self.update_user_settings(
            user_id, 
            show_technical_details=enabled
        )
        
        return settings is not None
    
    async def delete_user_settings(self, user_id: UUID) -> bool:
        """Удаляет настройки пользователя"""
        try:
            async with get_session() as session:
                stmt = select(UserSettings).where(UserSettings.user_id == user_id)
                result = await session.execute(stmt)
                settings = result.scalar_one_or_none()
                
                if settings:
                    await session.delete(settings)
                    await session.commit()
                    logger.info(f"Настройки удалены для пользователя {user_id}")
                    return True
                
                return False
                
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка удаления настроек пользователя {user_id}: {e}")
            return False
