"""
Основной сервис управления обучением аватаров
Рефакторинг app/services/avatar/training_service.py (618 строк → модули)
Объединяет TrainingManager, WebhookHandler, ProgressTracker, AvatarValidator
"""
from typing import Dict, List, Optional, Any
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base import BaseService
from app.database.models import AvatarStatus
from .training_manager import TrainingManager
from .webhook_handler import WebhookHandler
from .progress_tracker import ProgressTracker
from .avatar_validator import AvatarValidator

logger = logging.getLogger(__name__)class AvatarTrainingService(BaseService):
    """
    Основной сервис для управления обучением аватаров с интеграцией FAL AI.
    
    Объединяет модули:
    - TrainingManager: запуск и отмена обучения
    - WebhookHandler: обработка webhook от FAL AI
    - ProgressTracker: отслеживание прогресса
    - AvatarValidator: валидация аватаров и фото
    
    Основные функции:
    - Запуск обучения аватаров
    - Мониторинг прогресса
    - Обработка webhook от FAL AI
    - Управление состояниями обучения
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.session = session
        
        # Инициализируем модули
        self.training_manager = TrainingManager(session)
        self.webhook_handler = WebhookHandler(session)
        self.progress_tracker = ProgressTracker(session)
        self.validator = AvatarValidator(session)
        
        logger.info("Инициализирован AvatarTrainingService с модулями")

    # Делегирование к TrainingManager
    async def start_training(
        self, 
        avatar_id: UUID, 
        custom_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Запускает обучение аватара
        
        Args:
            avatar_id: ID аватара для обучения
            custom_config: Пользовательская конфигурация обучения
            
        Returns:
            bool: True если обучение запущено успешно
            
        Raises:
            ValueError: При ошибках валидации
            RuntimeError: При критических ошибках
        """
        return await self.training_manager.start_training(avatar_id, custom_config)

    async def cancel_training(self, avatar_id: UUID) -> bool:
        """
        Отменяет обучение аватара
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            bool: True если отмена прошла успешно
        """
        return await self.training_manager.cancel_training(avatar_id)

    # Делегирование к WebhookHandler
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Обрабатывает webhook от FAL AI
        
        Args:
            webhook_data: Данные webhook от FAL AI
            
        Returns:
            bool: True если webhook обработан успешно
        """
        return await self.webhook_handler.handle_webhook(webhook_data)

    # Делегирование к ProgressTracker
    async def get_training_progress(self, avatar_id: UUID) -> Dict[str, Any]:
        """
        Получает прогресс обучения аватара
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            Dict[str, Any]: Информация о прогрессе обучения
        """
        return await self.progress_tracker.get_training_progress(avatar_id)

    async def get_training_statistics(self, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Получает статистику обучения аватаров
        
        Args:
            user_id: ID пользователя (если None, то общая статистика)
            
        Returns:
            Dict[str, Any]: Статистика обучения
        """
        return await self.progress_tracker.get_training_statistics(user_id)

    # Делегирование к AvatarValidator
    async def validate_training_readiness(self, avatar_id: UUID) -> bool:
        """
        Проверяет готовность аватара к обучению
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            bool: True если аватар готов к обучению
        """
        return await self.validator.validate_training_readiness(avatar_id)

    # Вспомогательные методы для поиска
    async def find_avatar_by_finetune_id(self, finetune_id: str) -> Optional[UUID]:
        """
        Находит аватар по finetune_id
        
        Args:
            finetune_id: ID обучения FAL AI
            
        Returns:
            Optional[UUID]: ID аватара или None
        """
        return await self.progress_tracker.find_avatar_by_finetune_id(finetune_id)

    async def find_avatar_by_request_id(self, request_id: str) -> Optional["Avatar"]:
        """
        Находит аватар по fal_request_id
        
        Args:
            request_id: Request ID от FAL AI
            
        Returns:
            Optional[Avatar]: Аватар или None
        """
        return await self.progress_tracker.find_avatar_by_request_id(request_id)

    # Методы для получения компонентов (для расширенного использования)
    def get_training_manager(self) -> TrainingManager:
        """Возвращает менеджер обучения"""
        return self.training_manager

    def get_webhook_handler(self) -> WebhookHandler:
        """Возвращает обработчик webhook"""
        return self.webhook_handler

    def get_progress_tracker(self) -> ProgressTracker:
        """Возвращает трекер прогресса"""
        return self.progress_tracker

    def get_validator(self) -> AvatarValidator:
        """Возвращает валидатор"""
        return self.validator

    # Методы для совместимости с оригинальным API
    async def _get_avatar_for_training(self, avatar_id: UUID):
        """Совместимость с оригинальным API"""
        return await self.validator.get_avatar_for_training(avatar_id)

    async def _get_avatar_photo_urls(self, avatar_id: UUID) -> List[str]:
        """Совместимость с оригинальным API"""
        return await self.validator.get_avatar_photo_urls(avatar_id)

    async def _find_avatar_by_finetune_id(self, finetune_id: str) -> Optional[UUID]:
        """Совместимость с оригинальным API"""
        return await self.progress_tracker.find_avatar_by_finetune_id(finetune_id)

    async def _find_avatar_by_request_id(self, request_id: str):
        """Совместимость с оригинальным API"""
        return await self.progress_tracker.find_avatar_by_request_id(request_id)

    async def _cleanup_training_photos(self, avatar_id: UUID) -> None:
        """Совместимость с оригинальным API"""
        return await self.training_manager.cleanup_training_photos(avatar_id)

    # ИСПРАВЛЕНИЕ: Добавляем недостающие методы для совместимости
    async def _save_training_info(
        self, 
        avatar_id: UUID, 
        finetune_id: str, 
        custom_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Сохраняет информацию об обучении (делегирует к TrainingManager)
        
        Args:
            avatar_id: ID аватара
            finetune_id: ID обучения FAL AI
            custom_config: Пользовательская конфигурация
        """
        return await self.training_manager._save_training_info(avatar_id, finetune_id, custom_config)

    async def _update_avatar_status(
        self,
        avatar_id: UUID,
        status: AvatarStatus,
        progress: Optional[int] = None,
        **kwargs
    ) -> None:
        """
        Обновляет статус аватара (делегирует к TrainingManager)
        
        Args:
            avatar_id: ID аватара
            status: Новый статус
            progress: Прогресс обучения (0-100)
            **kwargs: Дополнительные параметры для обновления
        """
        return await self.training_manager._update_avatar_status(avatar_id, status, progress, **kwargs)
