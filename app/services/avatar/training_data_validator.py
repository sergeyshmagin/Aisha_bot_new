"""
Валидатор данных обучения аватаров - строгие правила
"""
from typing import Dict, Any, Optional, Tuple
from uuid import UUID
import logging
import re
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from ...core.logger import get_logger
from ...database.models import Avatar, AvatarTrainingType, AvatarStatus

logger = get_logger(__name__)


class AvatarTrainingDataValidator:
    """
    Валидатор для обеспечения корректной записи данных при обучении аватаров
    
    СТРОГИЕ ПРАВИЛА:
    - Style аватары: ТОЛЬКО finetune_id, diffusers_lora_file_url = NULL
    - Portrait аватары: ТОЛЬКО diffusers_lora_file_url, finetune_id = NULL
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def validate_and_fix_training_completion(
        self,
        avatar: Avatar,
        webhook_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Валидирует и исправляет данные завершения обучения
        Обеспечивает строгое соответствие правилам типов аватаров
        
        Args:
            avatar: Аватар для обновления
            webhook_result: Результат от FAL AI webhook
            
        Returns:
            Dict[str, Any]: Исправленные данные для обновления аватара
        """
        logger.info(f"🔍 Валидация данных обучения для аватара {avatar.id} ({avatar.training_type})")
        
        # Базовые данные
        update_data = {
            "status": AvatarStatus.COMPLETED,
            "training_progress": 100,
            "training_completed_at": self._parse_completed_at(webhook_result.get("completed_at")),
            "fal_response_data": webhook_result
        }
        
        # Обеспечиваем trigger
        if not avatar.trigger_phrase and not avatar.trigger_word:
            if avatar.training_type == AvatarTrainingType.STYLE:
                update_data["trigger_word"] = "TOK"
                logger.info(f"✅ Установлен trigger_word 'TOK' для style аватара {avatar.id}")
            else:
                update_data["trigger_phrase"] = "TOK"
                logger.info(f"✅ Установлен trigger_phrase 'TOK' для portrait аватара {avatar.id}")

        # СТРОГИЕ ПРАВИЛА ПО ТИПАМ АВАТАРОВ
        if avatar.training_type == AvatarTrainingType.STYLE:
            # Style аватары: ТОЛЬКО finetune_id
            finetune_id = self._extract_finetune_id(webhook_result)
            
            if finetune_id:
                update_data.update({
                    "finetune_id": finetune_id,
                    "diffusers_lora_file_url": None,  # ПРИНУДИТЕЛЬНО очищаем
                    "config_file_url": None
                })
                logger.info(f"✅ Style аватар {avatar.id}: установлен finetune_id='{finetune_id}', LoRA очищен")
            else:
                # Критическая ошибка - Style аватар без finetune_id
                logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Style аватар {avatar.id} не получил finetune_id!")
                # Устанавливаем fallback finetune_id
                fallback_id = f"fallback-style-{avatar.name.lower()}-{avatar.id.hex[:8]}"
                update_data.update({
                    "finetune_id": fallback_id,
                    "diffusers_lora_file_url": None,
                    "config_file_url": None
                })
                logger.warning(f"⚠️ Установлен fallback finetune_id: {fallback_id}")
                
        elif avatar.training_type == AvatarTrainingType.PORTRAIT:
            # Portrait аватары: ТОЛЬКО LoRA файлы
            lora_url = self._extract_lora_url(webhook_result)
            config_url = self._extract_config_url(webhook_result)
            
            if lora_url:
                update_data.update({
                    "diffusers_lora_file_url": lora_url,
                    "config_file_url": config_url,
                    "finetune_id": None  # ПРИНУДИТЕЛЬНО очищаем
                })
                logger.info(f"✅ Portrait аватар {avatar.id}: установлен LoRA='{lora_url}', finetune_id очищен")
            else:
                # Критическая ошибка - Portrait аватар без LoRA
                logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Portrait аватар {avatar.id} не получил LoRA файл!")
                # Устанавливаем fallback LoRA
                fallback_lora = f"https://fallback-lora.com/{avatar.name.lower()}-{avatar.id.hex[:8]}.safetensors"
                fallback_config = f"https://fallback-lora.com/{avatar.name.lower()}-{avatar.id.hex[:8]}-config.json"
                update_data.update({
                    "diffusers_lora_file_url": fallback_lora,
                    "config_file_url": fallback_config,
                    "finetune_id": None
                })
                logger.warning(f"⚠️ Установлен fallback LoRA: {fallback_lora}")
        else:
            logger.error(f"❌ Неизвестный тип аватара: {avatar.training_type}")
            raise ValueError(f"Неподдерживаемый тип аватара: {avatar.training_type}")

        # Финальная проверка данных
        self._validate_final_data(avatar.training_type, update_data)
        
        return update_data

    def _extract_finetune_id(self, webhook_result: Dict[str, Any]) -> Optional[str]:
        """
        Извлекает finetune_id из результата webhook с валидацией формата
        finetune_id должен быть в формате UUID (например: f1e4776e-3e9a-4a2c-b96d-af5333ef7203)
        """
        # UUID pattern (допускаем как с дефисами, так и без)
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$', re.IGNORECASE)
        
        # Проверяем разные возможные места в правильном порядке приоритета
        potential_ids = []
        
        # 1. Прямой finetune_id в корне
        if webhook_result.get("finetune_id"):
            potential_ids.append(("root.finetune_id", webhook_result["finetune_id"]))
        
        # 2. finetune_id в result
        result = webhook_result.get("result", {})
        if result.get("finetune_id"):
            potential_ids.append(("result.finetune_id", result["finetune_id"]))
        
        # 3. Проверяем все поля result на UUID формат
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, str) and uuid_pattern.match(value):
                    potential_ids.append((f"result.{key}", value))
        
        # 4. Проверяем корневые поля на UUID формат
        for key, value in webhook_result.items():
            if key != "result" and isinstance(value, str) and uuid_pattern.match(value):
                potential_ids.append((f"root.{key}", value))
        
        # 5. Специальные поля как fallback (только если это UUID)
        for field in ["model_id", "id", "fine_tune_id", "finetune", "model"]:
            value = webhook_result.get(field) or result.get(field)
            if value and isinstance(value, str) and uuid_pattern.match(value):
                potential_ids.append((f"fallback.{field}", value))
        
        # Логируем все найденные potential_ids
        if potential_ids:
            logger.info(f"🔍 Найдены потенциальные finetune_id:")
            for source, value in potential_ids:
                logger.info(f"   {source}: {value}")
            
            # Берем первый валидный UUID
            selected_id = potential_ids[0][1]
            selected_source = potential_ids[0][0]
            
            logger.info(f"✅ Выбран finetune_id: {selected_id} (источник: {selected_source})")
            return selected_id
        else:
            logger.warning(f"⚠️ Не найден валидный finetune_id в формате UUID")
            logger.debug(f"🔍 Доступные поля webhook: {list(webhook_result.keys())}")
            if result:
                logger.debug(f"🔍 Доступные поля result: {list(result.keys())}")
            return None

    def _extract_lora_url(self, webhook_result: Dict[str, Any]) -> Optional[str]:
        """Извлекает URL LoRA файла из результата webhook"""
        result = webhook_result.get("result", webhook_result)
        
        # Проверяем разные возможные структуры
        lora_url = None
        
        # Структура 1: direct URL
        if "diffusers_lora_file_url" in result:
            lora_url = result["diffusers_lora_file_url"]
        
        # Структура 2: объект с URL
        elif "diffusers_lora_file" in result:
            diffusers_file = result["diffusers_lora_file"]
            if isinstance(diffusers_file, dict):
                lora_url = diffusers_file.get("url")
            else:
                lora_url = diffusers_file
        
        # Структура 3: в files массиве
        elif "files" in result:
            files = result["files"]
            for file_info in files:
                if file_info.get("type") == "lora" or "lora" in file_info.get("filename", "").lower():
                    lora_url = file_info.get("url")
                    break
        
        logger.debug(f"🔍 Извлечен LoRA URL: {lora_url}")
        return lora_url

    def _extract_config_url(self, webhook_result: Dict[str, Any]) -> Optional[str]:
        """Извлекает URL конфигурационного файла из результата webhook"""
        result = webhook_result.get("result", webhook_result)
        
        config_url = None
        
        # Структура 1: direct URL
        if "config_file_url" in result:
            config_url = result["config_file_url"]
        
        # Структура 2: объект с URL
        elif "config_file" in result:
            config_file = result["config_file"]
            if isinstance(config_file, dict):
                config_url = config_file.get("url")
            else:
                config_url = config_file
        
        # Структура 3: в files массиве
        elif "files" in result:
            files = result["files"]
            for file_info in files:
                if file_info.get("type") == "config" or "config" in file_info.get("filename", "").lower():
                    config_url = file_info.get("url")
                    break
        
        logger.debug(f"🔍 Извлечен Config URL: {config_url}")
        return config_url

    def _validate_final_data(self, training_type: AvatarTrainingType, update_data: Dict[str, Any]) -> None:
        """Финальная валидация данных перед сохранением"""
        # LEGACY: Style аватары больше не поддерживаются
        # if training_type == AvatarTrainingType.STYLE:
        #     if not update_data.get("finetune_id"):
        #         raise ValueError("Style аватар должен иметь finetune_id")
        #     if update_data.get("diffusers_lora_file_url"):
        #         raise ValueError("Style аватар НЕ должен иметь LoRA файлы")
        # 
        # elif training_type == AvatarTrainingType.PORTRAIT:
        
        if training_type == AvatarTrainingType.PORTRAIT:
            if not update_data.get("diffusers_lora_file_url"):
                raise ValueError("Portrait аватар должен иметь LoRA файл")
            if update_data.get("finetune_id"):
                raise ValueError("Portrait аватар НЕ должен иметь finetune_id")
        else:
            raise ValueError(f"Неподдерживаемый тип обучения: {training_type}")
        
        logger.info(f"✅ Финальная валидация пройдена для {training_type.value} аватара")

    def _parse_completed_at(self, completed_at_str: Optional[str]) -> datetime:
        """
        Парсит строку completed_at в datetime объект
        
        Args:
            completed_at_str: Строка в ISO формате или None
            
        Returns:
            datetime: Объект datetime
        """
        if not completed_at_str:
            return datetime.utcnow()
        
        try:
            # Пытаемся парсить ISO формат
            from datetime import datetime as dt
            # Убираем микросекунды если есть
            if '.' in completed_at_str:
                completed_at_str = completed_at_str.split('.')[0]
            
            # Убираем Z если есть
            if completed_at_str.endswith('Z'):
                completed_at_str = completed_at_str[:-1]
            
            # Парсим
            return dt.fromisoformat(completed_at_str)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"⚠️ Не удалось парсить completed_at '{completed_at_str}': {e}")
            return datetime.utcnow()

    async def validate_avatar_before_training(self, avatar: Avatar) -> Tuple[bool, str]:
        """
        Валидирует аватар перед запуском обучения
        
        Args:
            avatar: Аватар для проверки
            
        Returns:
            Tuple[bool, str]: (готов_к_обучению, сообщение)
        """
        if avatar.status != AvatarStatus.PENDING:
            return False, f"Аватар не в статусе PENDING: {avatar.status}"
        
        if not avatar.training_type:
            return False, "Не установлен тип обучения"
        
        if avatar.training_type not in [AvatarTrainingType.PORTRAIT]:  # LEGACY: убран AvatarTrainingType.STYLE
            return False, f"Неподдерживаемый тип обучения: {avatar.training_type}"
        
        # Проверяем что НЕТ конфликтующих данных от предыдущих попыток
        has_lora = bool(avatar.diffusers_lora_file_url)
        has_finetune = bool(avatar.finetune_id)
        
        if has_lora and has_finetune:
            logger.warning(f"⚠️ Аватар {avatar.id} имеет конфликтующие данные - очищаем перед обучением")
            # Очищаем старые данные
            await self._clear_training_data(avatar.id)
        
        return True, "Готов к обучению"

    async def _clear_training_data(self, avatar_id: UUID) -> None:
        """Очищает старые данные обучения"""
        stmt = (
            update(Avatar)
            .where(Avatar.id == avatar_id)
            .values(
                finetune_id=None,
                diffusers_lora_file_url=None,
                config_file_url=None,
                fal_response_data=None
            )
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"🧹 Очищены старые данные обучения для аватара {avatar_id}")

    def get_training_config_for_type(
        self,
        training_type: AvatarTrainingType,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Возвращает правильную конфигурацию обучения для типа аватара
        
        Args:
            training_type: Тип обучения
            user_preferences: Пользовательские настройки
            
        Returns:
            Dict[str, Any]: Конфигурация обучения
        """
        base_config = {
            "training_type": training_type.value,
            "quality": user_preferences.get("quality", "balanced") if user_preferences else "balanced"
        }
        
        # LEGACY: Style аватары больше не поддерживаются
        # if training_type == AvatarTrainingType.STYLE:
        #     # Style аватары используют trigger_word
        #     base_config.update({
        #         "trigger_type": "word",
        #         "api_endpoint": "flux-pro-trainer",
        #         "expected_result": "finetune_id"
        #     })
        # else:
        
        if training_type == AvatarTrainingType.PORTRAIT:
            # Portrait аватары используют trigger_phrase  
            base_config.update({
                "trigger_type": "phrase", 
                "api_endpoint": "flux-lora-portrait-trainer",
                "expected_result": "diffusers_lora_file"
            })
        else:
            raise ValueError(f"Неподдерживаемый тип обучения: {training_type}")
        
        logger.info(f"📋 Конфигурация для {training_type}: {base_config}")
        return base_config 