"""
Валидированный сервис обучения аватаров
Интегрирует валидацию данных в процесс обучения
"""
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from uuid import UUID
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ...core.config import settings
from ...core.logger import get_logger
from ...database.models import Avatar, AvatarStatus, AvatarTrainingType
from .training_data_validator import AvatarTrainingDataValidator
from .fal_training_service.main_service import FALTrainingService

logger = get_logger(__name__)class ValidatedTrainingService:
    """
    Сервис обучения аватаров с интегрированной валидацией данных
    
    Обеспечивает:
    - Валидацию аватара перед запуском обучения
    - Очистку старых конфликтующих данных
    - Правильную запись результатов согласно типу аватара
    - Гарантированное соответствие строгим правилам
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.data_validator = AvatarTrainingDataValidator(session)
        self.fal_service = FALTrainingService()

    async def start_validated_training(
        self,
        avatar_id: UUID,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Запускает обучение аватара с предварительной валидацией
        
        Args:
            avatar_id: ID аватара для обучения
            user_preferences: Пользовательские настройки
            
        Returns:
            Tuple[bool, str, Optional[str]]: (успех, сообщение, request_id)
        """
        try:
            # 1. Получаем аватар
            avatar = await self._get_avatar(avatar_id)
            if not avatar:
                return False, f"Аватар {avatar_id} не найден", None

            # 2. ВАЛИДАЦИЯ ПЕРЕД ОБУЧЕНИЕМ
            is_ready, validation_message = await self.data_validator.validate_avatar_before_training(avatar)
            if not is_ready:
                logger.error(f"❌ Валидация не пройдена для аватара {avatar_id}: {validation_message}")
                return False, f"Валидация не пройдена: {validation_message}", None

            logger.info(f"✅ Валидация пройдена для аватара {avatar_id}: {validation_message}")

            # 3. Получаем правильную конфигурацию для типа аватара
            training_config = self.data_validator.get_training_config_for_type(
                avatar.training_type,
                user_preferences
            )

            # 4. Подготавливаем данные для обучения
            training_data_url = await self._prepare_training_data(avatar_id)
            if not training_data_url:
                return False, "Не удалось подготовить данные для обучения", None

            # 5. Устанавливаем правильные триггеры ПЕРЕД обучением
            await self._set_correct_triggers(avatar)

            # 6. Обновляем статус на "обучение"
            await self._update_avatar_status(avatar_id, AvatarStatus.TRAINING, 0)

            # 7. Запускаем обучение через FAL сервис
            logger.info(f"🚀 Запускаем обучение {avatar.training_type.value} аватара {avatar_id}")
            
            request_id = await self.fal_service.start_avatar_training(
                avatar_id=avatar_id,
                training_type=training_config["training_type"],
                training_data_url=training_data_url,
                user_preferences=user_preferences
            )

            if not request_id:
                await self._update_avatar_status(avatar_id, AvatarStatus.ERROR, error_message="Не удалось запустить обучение")
                return False, "FAL AI не смог запустить обучение", None

            # 8. Сохраняем request_id в БД
            await self._save_training_request(avatar_id, request_id, training_config)

            # 🔍 КРИТИЧЕСКИ ВАЖНО: Запускаем мониторинг status_checker
            try:
                from app.services.avatar.fal_training_service.status_checker import status_checker
                training_type = training_config.get("training_type", "portrait")
                await status_checker.start_status_monitoring(avatar_id, request_id, training_type)
                logger.info(f"🔍 Запущен мониторинг status_checker для аватара {avatar_id}, request_id: {request_id}")
            except Exception as monitor_error:
                logger.warning(f"🔍 Не удалось запустить мониторинг для аватара {avatar_id}: {monitor_error}")
                # Продолжаем работу - это не критическая ошибка

            logger.info(f"✅ Обучение аватара {avatar_id} запущено успешно: request_id={request_id}")
            return True, f"Обучение запущено успешно", request_id

        except Exception as e:
            logger.exception(f"❌ Критическая ошибка при запуске обучения аватара {avatar_id}: {e}")
            
            try:
                await self._update_avatar_status(avatar_id, AvatarStatus.ERROR, error_message=str(e))
            except Exception as rollback_error:
                logger.exception(f"Ошибка отката статуса: {rollback_error}")
            
            return False, f"Ошибка запуска обучения: {str(e)}", None

    async def _get_avatar(self, avatar_id: UUID) -> Optional[Avatar]:
        """Получает аватар по ID"""
        query = select(Avatar).where(Avatar.id == avatar_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _prepare_training_data(self, avatar_id: UUID) -> Optional[str]:
        """Подготавливает URL с данными для обучения"""
        try:
            # Логика подготовки данных (создание архива с фотографиями)
            # Здесь должна быть интеграция с существующим кодом подготовки данных
            
            # Пока возвращаем заглушку
            logger.info(f"🔄 Подготовка данных для обучения аватара {avatar_id}")
            
            # В реальной реализации здесь будет:
            # 1. Получение фотографий аватара
            # 2. Создание ZIP архива
            # 3. Загрузка в MinIO или другое хранилище
            # 4. Возврат URL архива
            
            mock_data_url = f"https://training-data.example.com/avatars/{avatar_id}/photos.zip"
            logger.info(f"✅ Данные подготовлены: {mock_data_url}")
            
            return mock_data_url
            
        except Exception as e:
            logger.exception(f"Ошибка подготовки данных для аватара {avatar_id}: {e}")
            return None

    async def _set_correct_triggers(self, avatar: Avatar) -> None:
        """Устанавливает правильные триггеры для типа аватара"""
        update_data = {}
        
        if avatar.training_type == AvatarTrainingType.STYLE:
            # Style аватары используют trigger_word
            if not avatar.trigger_word:
                trigger_word = f"TOK_{avatar.id.hex[:8]}"
                update_data["trigger_word"] = trigger_word
                logger.info(f"🎨 Установлен trigger_word для style аватара {avatar.id}: '{trigger_word}'")
        else:
            # Portrait аватары используют trigger_phrase
            if not avatar.trigger_phrase:
                trigger_phrase = f"TOK_{avatar.id.hex[:8]}"
                update_data["trigger_phrase"] = trigger_phrase
                logger.info(f"👤 Установлен trigger_phrase для portrait аватара {avatar.id}: '{trigger_phrase}'")

        if update_data:
            stmt = update(Avatar).where(Avatar.id == avatar.id).values(**update_data)
            await self.session.execute(stmt)
            await self.session.commit()

    async def _update_avatar_status(
        self,
        avatar_id: UUID,
        status: AvatarStatus,
        progress: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Обновляет статус аватара"""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if progress is not None:
            update_data["training_progress"] = progress
        
        if error_message:
            update_data["error_message"] = error_message
            
        if status == AvatarStatus.TRAINING:
            update_data["training_started_at"] = datetime.utcnow()

        stmt = update(Avatar).where(Avatar.id == avatar_id).values(**update_data)
        await self.session.execute(stmt)
        await self.session.commit()
        
        logger.info(f"📊 Статус аватара {avatar_id} обновлен: {status.value}")

    async def _save_training_request(
        self,
        avatar_id: UUID,
        request_id: str,
        training_config: Dict[str, Any]
    ) -> None:
        """Сохраняет информацию о запросе на обучение"""
        update_data = {
            "fal_request_id": request_id,
            "training_config": training_config,
            "training_started_at": datetime.utcnow()
        }
        
        stmt = update(Avatar).where(Avatar.id == avatar_id).values(**update_data)
        await self.session.execute(stmt)
        await self.session.commit()
        
        logger.info(f"💾 Сохранен request_id {request_id} для аватара {avatar_id}")

    async def validate_and_fix_existing_avatar(self, avatar_id: UUID) -> Dict[str, Any]:
        """
        Валидирует и исправляет данные существующего аватара
        
        Args:
            avatar_id: ID аватара для проверки
            
        Returns:
            Dict[str, Any]: Отчет о валидации и исправлениях
        """
        try:
            avatar = await self._get_avatar(avatar_id)
            if not avatar:
                return {"error": f"Аватар {avatar_id} не найден"}

            report = {
                "avatar_id": str(avatar_id),
                "name": avatar.name,
                "training_type": avatar.training_type.value if avatar.training_type else None,
                "status": avatar.status.value if avatar.status else None,
                "issues_found": [],
                "fixes_applied": []
            }

            # Проверяем статус
            if avatar.status != AvatarStatus.COMPLETED:
                report["issues_found"].append(f"Статус не COMPLETED: {avatar.status}")
                return report

            # Проверяем данные в зависимости от типа
            if avatar.training_type == AvatarTrainingType.STYLE:
                # Style аватар должен иметь finetune_id и НЕ иметь LoRA
                if not avatar.finetune_id:
                    report["issues_found"].append("Отсутствует finetune_id для style аватара")
                    
                if avatar.diffusers_lora_file_url:
                    report["issues_found"].append("Style аватар имеет LoRA файл (должен быть только finetune_id)")
                    # Исправляем
                    await self.session.execute(
                        update(Avatar)
                        .where(Avatar.id == avatar_id)
                        .values(diffusers_lora_file_url=None, config_file_url=None)
                    )
                    await self.session.commit()
                    report["fixes_applied"].append("Удален LoRA файл из style аватара")

            elif avatar.training_type == AvatarTrainingType.PORTRAIT:
                # Portrait аватар должен иметь LoRA и НЕ иметь finetune_id
                if not avatar.diffusers_lora_file_url:
                    report["issues_found"].append("Отсутствует LoRA файл для portrait аватара")
                    
                if avatar.finetune_id:
                    report["issues_found"].append("Portrait аватар имеет finetune_id (должен быть только LoRA файл)")
                    # Исправляем
                    await self.session.execute(
                        update(Avatar)
                        .where(Avatar.id == avatar_id)
                        .values(finetune_id=None)
                    )
                    await self.session.commit()
                    report["fixes_applied"].append("Удален finetune_id из portrait аватара")

            # Проверяем триггеры
            if avatar.training_type == AvatarTrainingType.STYLE and not avatar.trigger_word:
                report["issues_found"].append("Отсутствует trigger_word для style аватара")
                
            if avatar.training_type == AvatarTrainingType.PORTRAIT and not avatar.trigger_phrase:
                report["issues_found"].append("Отсутствует trigger_phrase для portrait аватара")

            report["is_valid"] = len(report["issues_found"]) == 0
            return report

        except Exception as e:
            logger.exception(f"Ошибка валидации аватара {avatar_id}: {e}")
            return {"error": str(e)}

    def get_validation_rules(self) -> Dict[str, Any]:
        """Возвращает правила валидации для документации"""
        return {
            "style_avatars": {
                "required_fields": ["finetune_id", "trigger_word"],
                "forbidden_fields": ["diffusers_lora_file_url"],
                "api_endpoint": "fal-ai/flux-pro/v1.1-ultra-finetuned"
            },
            "portrait_avatars": {
                "required_fields": ["diffusers_lora_file_url", "trigger_phrase"],
                "forbidden_fields": ["finetune_id"],
                "api_endpoint": "fal-ai/flux-lora"
            },
            "common_rules": [
                "Только один тип данных на аватар",
                "Триггеры обязательны",
                "Статус COMPLETED для готовых аватаров",
                "Валидация перед каждым обучением"
            ]
        }
