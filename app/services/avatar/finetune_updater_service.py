"""
Сервис для автоматического обновления finetune_id аватаров
Может использоваться status_checker, webhook или вручную
"""
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ...core.logger import get_logger
from ...database.models import Avatar, AvatarStatus, AvatarTrainingType

logger = get_logger(__name__)


class FinetuneUpdaterService:
    """
    Сервис для автоматического обновления finetune_id аватаров
    
    Может быть использован для:
    - Обновления устаревших finetune_id
    - Исправления некорректных форматов
    - Массового обновления при изменениях в FAL AI
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        # Регулярное выражение для проверки UUID формата
        self.uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$', 
            re.IGNORECASE
        )

    async def update_finetune_id_by_name(
        self, 
        avatar_name: str, 
        new_finetune_id: str,
        reason: str = "Manual update",
        updated_by: str = "finetune_updater_service"
    ) -> bool:
        """
        Обновляет finetune_id аватара по имени
        
        Args:
            avatar_name: Имя аватара
            new_finetune_id: Новый finetune_id
            reason: Причина обновления
            updated_by: Источник обновления
            
        Returns:
            bool: Успешность обновления
        """
        logger.info(f"🔄 Обновление finetune_id для аватара '{avatar_name}'")
        
        # Валидируем новый finetune_id
        if not self._is_valid_uuid(new_finetune_id):
            logger.error(f"❌ Новый finetune_id '{new_finetune_id}' не в формате UUID")
            return False
        
        # Ищем аватар
        query = select(Avatar).where(Avatar.name == avatar_name)
        result = await self.session.execute(query)
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            logger.error(f"❌ Аватар '{avatar_name}' не найден")
            return False
        
        # Проверяем тип аватара
        if avatar.training_type != AvatarTrainingType.STYLE:
            logger.error(f"❌ Аватар '{avatar_name}' не является Style типом: {avatar.training_type}")
            return False
        
        old_finetune_id = avatar.finetune_id
        
        # Проверяем что finetune_id действительно изменился
        if old_finetune_id == new_finetune_id:
            logger.info(f"ℹ️ finetune_id аватара '{avatar_name}' уже корректный")
            return True
        
        logger.info(f"🔄 Старый finetune_id: {old_finetune_id}")
        logger.info(f"🔄 Новый finetune_id: {new_finetune_id}")
        
        # Выполняем обновление
        success = await self._perform_update(
            avatar=avatar,
            new_finetune_id=new_finetune_id,
            reason=reason,
            updated_by=updated_by
        )
        
        if success:
            logger.info(f"✅ finetune_id аватара '{avatar_name}' успешно обновлен")
        
        return success

    async def update_finetune_id_by_id(
        self, 
        avatar_id: UUID, 
        new_finetune_id: str,
        reason: str = "Manual update",
        updated_by: str = "finetune_updater_service"
    ) -> bool:
        """
        Обновляет finetune_id аватара по ID
        
        Args:
            avatar_id: ID аватара
            new_finetune_id: Новый finetune_id
            reason: Причина обновления
            updated_by: Источник обновления
            
        Returns:
            bool: Успешность обновления
        """
        logger.info(f"🔄 Обновление finetune_id для аватара {avatar_id}")
        
        # Валидируем новый finetune_id
        if not self._is_valid_uuid(new_finetune_id):
            logger.error(f"❌ Новый finetune_id '{new_finetune_id}' не в формате UUID")
            return False
        
        # Получаем аватар
        avatar = await self.session.get(Avatar, avatar_id)
        
        if not avatar:
            logger.error(f"❌ Аватар {avatar_id} не найден")
            return False
        
        # Проверяем тип аватара
        if avatar.training_type != AvatarTrainingType.STYLE:
            logger.error(f"❌ Аватар {avatar_id} не является Style типом: {avatar.training_type}")
            return False
        
        old_finetune_id = avatar.finetune_id
        
        # Проверяем что finetune_id действительно изменился
        if old_finetune_id == new_finetune_id:
            logger.info(f"ℹ️ finetune_id аватара {avatar_id} уже корректный")
            return True
        
        logger.info(f"🔄 Старый finetune_id: {old_finetune_id}")
        logger.info(f"🔄 Новый finetune_id: {new_finetune_id}")
        
        # Выполняем обновление
        success = await self._perform_update(
            avatar=avatar,
            new_finetune_id=new_finetune_id,
            reason=reason,
            updated_by=updated_by
        )
        
        if success:
            logger.info(f"✅ finetune_id аватара {avatar_id} успешно обновлен")
        
        return success

    async def bulk_update_invalid_finetune_ids(
        self, 
        finetune_id_mapping: Dict[str, str],
        reason: str = "Bulk update of invalid finetune_ids",
        updated_by: str = "bulk_finetune_updater"
    ) -> Dict[str, Any]:
        """
        Массовое обновление некорректных finetune_id
        
        Args:
            finetune_id_mapping: Словарь {старый_finetune_id: новый_finetune_id}
            reason: Причина обновления
            updated_by: Источник обновления
            
        Returns:
            Dict[str, Any]: Результат операции
        """
        logger.info(f"🔄 Массовое обновление {len(finetune_id_mapping)} finetune_id")
        
        results = {
            "total_requested": len(finetune_id_mapping),
            "updated": 0,
            "errors": [],
            "skipped": []
        }
        
        for old_finetune_id, new_finetune_id in finetune_id_mapping.items():
            try:
                # Валидируем новый finetune_id
                if not self._is_valid_uuid(new_finetune_id):
                    error_msg = f"Новый finetune_id '{new_finetune_id}' не в формате UUID"
                    logger.error(f"❌ {error_msg}")
                    results["errors"].append({"old_id": old_finetune_id, "error": error_msg})
                    continue
                
                # Ищем аватар по старому finetune_id
                query = select(Avatar).where(Avatar.finetune_id == old_finetune_id)
                result = await self.session.execute(query)
                avatar = result.scalar_one_or_none()
                
                if not avatar:
                    skip_msg = f"Аватар с finetune_id '{old_finetune_id}' не найден"
                    logger.warning(f"⚠️ {skip_msg}")
                    results["skipped"].append({"old_id": old_finetune_id, "reason": skip_msg})
                    continue
                
                # Проверяем тип аватара
                if avatar.training_type != AvatarTrainingType.STYLE:
                    skip_msg = f"Аватар {avatar.name} не является Style типом"
                    logger.warning(f"⚠️ {skip_msg}")
                    results["skipped"].append({"old_id": old_finetune_id, "reason": skip_msg})
                    continue
                
                # Выполняем обновление
                success = await self._perform_update(
                    avatar=avatar,
                    new_finetune_id=new_finetune_id,
                    reason=f"{reason} (bulk operation)",
                    updated_by=updated_by
                )
                
                if success:
                    results["updated"] += 1
                    logger.info(f"✅ Обновлен аватар {avatar.name}: {old_finetune_id} -> {new_finetune_id}")
                else:
                    results["errors"].append({
                        "old_id": old_finetune_id, 
                        "error": "Ошибка выполнения обновления"
                    })
                
            except Exception as e:
                error_msg = f"Исключение при обновлении {old_finetune_id}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                results["errors"].append({"old_id": old_finetune_id, "error": error_msg})
        
        logger.info(f"📊 Результат массового обновления:")
        logger.info(f"   Запрошено: {results['total_requested']}")
        logger.info(f"   Обновлено: {results['updated']}")
        logger.info(f"   Пропущено: {len(results['skipped'])}")
        logger.info(f"   Ошибок: {len(results['errors'])}")
        
        return results

    async def find_avatars_with_invalid_finetune_ids(self) -> List[Dict[str, Any]]:
        """
        Находит аватары с некорректными finetune_id (не в формате UUID)
        
        Returns:
            List[Dict[str, Any]]: Список аватаров с проблемными finetune_id
        """
        logger.info("🔍 Поиск аватаров с некорректными finetune_id")
        
        # Получаем все Style аватары с finetune_id
        query = select(Avatar).where(
            Avatar.training_type == AvatarTrainingType.STYLE,
            Avatar.finetune_id.isnot(None)
        )
        result = await self.session.execute(query)
        avatars = result.scalars().all()
        
        invalid_avatars = []
        
        for avatar in avatars:
            if not self._is_valid_uuid(avatar.finetune_id):
                invalid_avatars.append({
                    "id": str(avatar.id),
                    "name": avatar.name,
                    "finetune_id": avatar.finetune_id,
                    "status": avatar.status.value,
                    "created_at": avatar.created_at.isoformat() if avatar.created_at else None
                })
        
        logger.info(f"🔍 Найдено {len(invalid_avatars)} аватаров с некорректными finetune_id")
        
        return invalid_avatars

    async def _perform_update(
        self, 
        avatar: Avatar, 
        new_finetune_id: str,
        reason: str,
        updated_by: str
    ) -> bool:
        """
        Выполняет обновление finetune_id аватара с соблюдением правил валидации
        
        Args:
            avatar: Аватар для обновления
            new_finetune_id: Новый finetune_id
            reason: Причина обновления
            updated_by: Источник обновления
            
        Returns:
            bool: Успешность обновления
        """
        try:
            old_finetune_id = avatar.finetune_id
            
            # Подготавливаем данные для обновления (соблюдаем правила валидации)
            update_data = {
                "finetune_id": new_finetune_id,
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Для Style аватаров ПРИНУДИТЕЛЬНО очищаем LoRA данные
            if avatar.training_type == AvatarTrainingType.STYLE:
                update_data.update({
                    "diffusers_lora_file_url": None,
                    "config_file_url": None
                })
                
                # Обеспечиваем trigger_word
                if not avatar.trigger_word:
                    update_data["trigger_word"] = "TOK"
            
            # Добавляем информацию об обновлении в avatar_data
            avatar_data = avatar.avatar_data or {}
            avatar_data["finetune_update_history"] = avatar_data.get("finetune_update_history", [])
            avatar_data["finetune_update_history"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "old_finetune_id": old_finetune_id,
                "new_finetune_id": new_finetune_id,
                "reason": reason,
                "updated_by": updated_by,
                "cleared_lora": bool(avatar.diffusers_lora_file_url),
                "added_trigger_word": not bool(avatar.trigger_word)
            })
            update_data["avatar_data"] = avatar_data
            
            # Выполняем обновление
            stmt = update(Avatar).where(Avatar.id == avatar.id).values(**update_data)
            await self.session.execute(stmt)
            await self.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления аватара {avatar.id}: {e}")
            await self.session.rollback()
            return False

    def _is_valid_uuid(self, value: str) -> bool:
        """
        Проверяет что строка является валидным UUID
        
        Args:
            value: Строка для проверки
            
        Returns:
            bool: True если строка является UUID
        """
        if not isinstance(value, str):
            return False
        
        return bool(self.uuid_pattern.match(value))

    async def get_update_history(self, avatar_id: UUID) -> List[Dict[str, Any]]:
        """
        Получает историю обновлений finetune_id для аватара
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            List[Dict[str, Any]]: История обновлений
        """
        avatar = await self.session.get(Avatar, avatar_id)
        
        if not avatar or not avatar.avatar_data:
            return []
        
        return avatar.avatar_data.get("finetune_update_history", []) 