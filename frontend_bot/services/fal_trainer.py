import logging
import os
import tempfile
import zipfile
from typing import List, Optional

import fal_client

logger = logging.getLogger(__name__)


async def train_avatar(
    user_id: int,
    avatar_id: str,
    name: str,
    gender: str,
    photo_paths: List[str],
    finetune_comment: Optional[str] = None,
    mode: str = "character",
    iterations: int = 300,
    priority: str = "quality",
    captioning: bool = True,
    trigger_word: str = "TOK",
    lora_rank: int = 32,
    finetune_type: str = "full",
    webhook_url: Optional[str] = None
) -> str:
    """
    Архивирует фото, загружает на fal.ai и запускает обучение аватара.
    Возвращает finetune_id.
    """
    logger.info(
        f"[FAL_TRAINER] Старт обучения: user_id={user_id}, "
        f"avatar_id={avatar_id}, name={name}, gender={gender}, "
        f"photos={len(photo_paths)}"
    )
    # 1. Архивируем фото во временный zip
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, f"avatar_{avatar_id}.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for p in photo_paths:
                zipf.write(p, arcname=os.path.basename(p))
        logger.info(
            f"[FAL_TRAINER] Фото заархивированы: {zip_path}"
        )
        # 2. Загружаем архив на fal.ai
        data_url = await fal_client.upload_file_async(zip_path)
        logger.info(
            f"[FAL_TRAINER] Архив загружен, data_url={data_url}"
        )
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
        handler = await fal_client.submit_async(
            "fal-ai/flux-pro-trainer",
            arguments=arguments,
            webhook_url=webhook_url
        )
        result = await handler.get()
        finetune_id = result.get("finetune_id")
        logger.info(
            f"[FAL_TRAINER] Обучение запущено, finetune_id={finetune_id}"
        )
        return finetune_id 