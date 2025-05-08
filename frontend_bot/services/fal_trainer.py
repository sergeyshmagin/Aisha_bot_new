import os
import tempfile
import zipfile
from typing import List, Optional

import fal_client
from frontend_bot.config import (
    FAL_MODE, FAL_ITERATIONS, FAL_PRIORITY, FAL_CAPTIONING,
    FAL_TRIGGER_WORD, FAL_LORA_RANK, FAL_FINETUNE_TYPE,
    FAL_WEBHOOK_URL
)
from frontend_bot.utils.logger import get_logger

logger = get_logger('fal_trainer')


async def train_avatar(
    user_id: int,
    avatar_id: str,
    name: str,
    gender: str,
    photo_paths: List[str],
    finetune_comment: Optional[str] = None,
    mode: str = None,
    iterations: int = None,
    priority: str = None,
    captioning: bool = None,
    trigger_word: str = None,
    lora_rank: int = None,
    finetune_type: str = None,
    webhook_url: Optional[str] = None
) -> Optional[str]:
    """
    Архивирует фото, загружает на fal.ai и запускает обучение аватара.
    Возвращает finetune_id или None при ошибке.
    """
    # Используем значения из config, если не переданы явно
    mode = mode or FAL_MODE
    iterations = iterations or FAL_ITERATIONS
    priority = priority or FAL_PRIORITY
    captioning = FAL_CAPTIONING if captioning is None else captioning
    trigger_word = trigger_word or FAL_TRIGGER_WORD
    lora_rank = lora_rank or FAL_LORA_RANK
    finetune_type = finetune_type or FAL_FINETUNE_TYPE
    webhook_url = webhook_url or FAL_WEBHOOK_URL
    try:
        logger.info(
            f"[FAL_TRAINER] Старт обучения: user_id={user_id}, "
            f"avatar_id={avatar_id}, name={name}, gender={gender}, "
            f"photos={len(photo_paths)}, mode={mode}, "
            f"iterations={iterations}, priority={priority}, "
            f"captioning={captioning}, trigger_word={trigger_word}, "
            f"lora_rank={lora_rank}, finetune_type={finetune_type}, "
            f"webhook_url={webhook_url}"
        )
        # 1. Архивируем фото во временный zip
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, f"avatar_{avatar_id}.zip")
            try:
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for p in photo_paths:
                        zipf.write(p, arcname=os.path.basename(p))
                logger.info(
                    f"[FAL_TRAINER] Фото заархивированы: {zip_path}"
                )
            except Exception as e:
                logger.error(
                    f"[FAL_TRAINER] Ошибка архивации фото: {e}"
                )
                return None
            # 2. Загружаем архив на fal.ai
            try:
                data_url = await fal_client.upload_file_async(zip_path)
                logger.info(
                    f"[FAL_TRAINER] Архив загружен, data_url={data_url}"
                )
            except Exception as e:
                logger.error(
                    f"[FAL_TRAINER] Ошибка загрузки архива на fal.ai: {e}"
                )
                return None
            # 3. Формируем параметры
            arguments = {
                "data_url": data_url,
                "mode": mode,
                "finetune_comment": finetune_comment or f"user_{user_id}_avatar_{avatar_id}",
                "iterations": iterations,
                "priority": priority,
                "captioning": captioning,
                "trigger_word": trigger_word,
                "lora_rank": lora_rank,
                "finetune_type": finetune_type
            }
            logger.info(
                f"[FAL_TRAINER] Аргументы для submit: {arguments}"
            )
            # 4. Запускаем обучение
            try:
                handler = await fal_client.submit_async(
                    "fal-ai/flux-pro-trainer",
                    arguments=arguments,
                    webhook_url=webhook_url
                )
                result = await handler.get()
                finetune_id = result.get("finetune_id")
                logger.info(
                    f"[FAL_TRAINER] Обучение запущено, "
                    f"finetune_id={finetune_id}"
                )
                return finetune_id
            except Exception as e:
                logger.error(
                    f"[FAL_TRAINER] Ошибка запуска обучения на fal.ai: "
                    f"{e}"
                )
                return None
    except Exception as e:
        logger.critical(
            f"[FAL_TRAINER] Критическая ошибка в train_avatar: "
            f"{e}", exc_info=True
        )
        return None 