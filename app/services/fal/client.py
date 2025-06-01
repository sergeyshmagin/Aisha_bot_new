"""
FAL AI клиент для обучения моделей аватаров
"""
import asyncio
import io
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID

import fal_client
from PIL import Image

from ...core.config import settings
from ...core.logger import get_logger

logger = get_logger(__name__)


class FalAIClient:
    """
    Клиент для работы с FAL AI API.
    
    Основные функции:
    - Обучение персональных моделей (finetune)
    - Мониторинг прогресса обучения
    - Генерация изображений с обученными моделями
    - Управление файлами и архивами
    """

    def __init__(self):
        self.logger = logger
        self.api_key = settings.FAL_API_KEY
        self.test_mode = settings.AVATAR_TEST_MODE
        
        # Настраиваем FAL клиент
        if self.api_key:
            fal_client.api_key = self.api_key
        else:
            logger.debug("FAL_API_KEY не установлен, работа в тестовом режиме")

    async def train_avatar(
        self,
        user_id: UUID,
        avatar_id: UUID,
        name: str,
        gender: str,
        photo_urls: List[str],
        training_config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Запускает обучение аватара на FAL AI
        
        Args:
            user_id: ID пользователя
            avatar_id: ID аватара
            name: Имя аватара
            gender: Пол аватара
            photo_urls: Список URL фотографий в MinIO
            training_config: Конфигурация обучения (включая training_type)
            
        Returns:
            Optional[str]: request_id или None при ошибке
            
        Raises:
            RuntimeError: При критических ошибках
        """
        try:
            if self.test_mode:
                logger.info(f"[FAL TEST MODE] Симуляция обучения аватара {avatar_id}")
                # В тестовом режиме возвращаем мок request_id
                mock_request_id = f"test_request_{avatar_id}"
                await asyncio.sleep(0.1)  # Симуляция задержки
                return mock_request_id
            
            # Получаем тип обучения из конфигурации
            training_type = training_config.get("training_type", "style") if training_config else "style"
            
            logger.info(
                f"[FAL AI] Начало обучения аватара {avatar_id}: "
                f"user_id={user_id}, name='{name}', gender={gender}, "
                f"photos={len(photo_urls)}, training_type={training_type}"
            )
            
            # 1. Скачиваем фотографии и создаем архив
            data_url = await self._download_and_create_archive(photo_urls, avatar_id)
            
            if not data_url:
                raise RuntimeError("Не удалось скачать фотографии для создания архива")
            
            # 2. Запускаем обучение в зависимости от типа
            if training_type == "portrait":
                # Портретное обучение через flux-lora-portrait-trainer
                request_id = await self._train_portrait_avatar(
                    data_url=data_url,
                    user_id=user_id,
                    avatar_id=avatar_id,
                    config=training_config or {}
                )
            else:
                # Художественное обучение через flux-pro-trainer
                request_id = await self._train_style_avatar(
                    data_url=data_url,
                    user_id=user_id,
                    avatar_id=avatar_id,
                    config=training_config or {}
                )
            
            logger.info(f"[FAL AI] Обучение запущено успешно: request_id={request_id}")
            return request_id
            
        except Exception as e:
            logger.exception(f"[FAL AI] Критическая ошибка при обучении аватара {avatar_id}: {e}")
            raise RuntimeError(f"Ошибка обучения аватара: {str(e)}")
        
        finally:
            # Очищаем временные файлы
            await self._cleanup_temp_files()

    async def _train_portrait_avatar(
        self,
        data_url: str,
        user_id: UUID,
        avatar_id: UUID,
        config: Dict[str, Any]
    ) -> Optional[str]:
        """
        Запускает портретное обучение через flux-lora-portrait-trainer
        
        Args:
            data_url: URL архива с фотографиями
            user_id: ID пользователя
            avatar_id: ID аватара
            config: Конфигурация обучения
            
        Returns:
            Optional[str]: request_id
        """
        try:
            # Получаем настройки портретного обучения
            trigger_phrase = config.get("trigger_phrase", f"PERSON_{avatar_id.hex[:8]}")
            steps = config.get("steps", settings.FAL_PORTRAIT_STEPS)
            learning_rate = config.get("learning_rate", settings.FAL_PORTRAIT_LEARNING_RATE)
            multiresolution_training = config.get("multiresolution_training", settings.FAL_PORTRAIT_MULTIRESOLUTION)
            subject_crop = config.get("subject_crop", settings.FAL_PORTRAIT_SUBJECT_CROP)
            create_masks = config.get("create_masks", settings.FAL_PORTRAIT_CREATE_MASKS)
            webhook_url = config.get("webhook_url", settings.FAL_WEBHOOK_URL)
            
            logger.info(f"[FAL AI] Портретное обучение аватара {avatar_id}: trigger='{trigger_phrase}', steps={steps}")
            
            # Запускаем портретное обучение
            request_id = await self.train_portrait_model(
                images_data_url=data_url,
                trigger_phrase=trigger_phrase,
                steps=steps,
                learning_rate=learning_rate,
                multiresolution_training=multiresolution_training,
                subject_crop=subject_crop,
                create_masks=create_masks,
                webhook_url=webhook_url
            )
            
            return request_id
            
        except Exception as e:
            logger.exception(f"[FAL AI] Ошибка портретного обучения аватара {avatar_id}: {e}")
            return None

    async def _train_style_avatar(
        self,
        data_url: str,
        user_id: UUID,
        avatar_id: UUID,
        config: Dict[str, Any]
    ) -> Optional[str]:
        """
        Запускает художественное обучение через flux-pro-trainer
        
        Args:
            data_url: URL архива с фотографиями
            user_id: ID пользователя
            avatar_id: ID аватара
            config: Конфигурация обучения
            
        Returns:
            Optional[str]: request_id
        """
        try:
            # Настройки по умолчанию для художественного обучения
            style_config = {
                "mode": config.get("mode", settings.FAL_DEFAULT_MODE),
                "iterations": config.get("iterations", settings.FAL_DEFAULT_ITERATIONS),
                "priority": config.get("priority", settings.FAL_DEFAULT_PRIORITY),
                "captioning": config.get("captioning", True),
                "trigger_word": config.get("trigger_word", f"TOK_{avatar_id.hex[:8]}"),
                "lora_rank": config.get("lora_rank", settings.FAL_LORA_RANK),
                "finetune_type": config.get("finetune_type", settings.FAL_FINETUNE_TYPE),
                "webhook_url": config.get("webhook_url", settings.FAL_WEBHOOK_URL),
            }
            
            logger.info(f"[FAL AI] Художественное обучение аватара {avatar_id}: trigger='{style_config['trigger_word']}'")
            
            # Запускаем художественное обучение через существующий метод
            request_id = await self._submit_training(
                data_url=data_url,
                user_id=user_id,
                avatar_id=avatar_id,
                config=style_config
            )
            
            return request_id
            
        except Exception as e:
            logger.exception(f"[FAL AI] Ошибка художественного обучения аватара {avatar_id}: {e}")
            return None

    async def get_training_status(self, finetune_id: str) -> Dict[str, Any]:
        """
        Получает статус обучения модели
        
        Args:
            finetune_id: ID обучения FAL AI
            
        Returns:
            Dict[str, Any]: Статус обучения
        """
        try:
            if self.test_mode:
                # В тестовом режиме возвращаем мок статус
                return {
                    "status": "completed",
                    "progress": 100,
                    "created_at": "2025-05-23T16:00:00Z",
                    "updated_at": "2025-05-23T16:30:00Z",
                    "completed_at": "2025-05-23T16:30:00Z",
                    "message": "Training completed successfully (test mode)"
                }
            
            # TODO: Реализовать получение статуса через FAL API
            # В FAL AI пока нет прямого API для получения статуса
            # Статус приходит через webhook
            
            logger.warning(f"[FAL AI] Получение статуса {finetune_id} пока не реализовано")
            return {
                "status": "unknown",
                "message": "Status checking not implemented yet"
            }
            
        except Exception as e:
            logger.exception(f"[FAL AI] Ошибка получения статуса {finetune_id}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    # LEGACY: Устаревший метод, используйте FALGenerationService
    # async def generate_image(
    #     self,
    #     finetune_id: str,
    #     prompt: str,
    #     config: Optional[Dict[str, Any]] = None
    # ) -> Optional[str]:
    #     """
    #     DEPRECATED: Используйте FALGenerationService вместо этого метода
    #     
    #     Args:
    #         finetune_id: ID обученной модели
    #         prompt: Промпт для генерации
    #         config: Дополнительные параметры генерации
    #         
    #     Returns:
    #         Optional[str]: URL сгенерированного изображения
    #     """
    #     logger.warning(
    #         "[FAL AI] Метод generate_image устарел. "
    #         "Используйте FALGenerationService.generate_avatar_image()"
    #     )
    #     
    #     try:
    #         if self.test_mode:
    #             logger.info(f"[FAL TEST MODE] Симуляция генерации с моделью {finetune_id}")
    #             # Возвращаем тестовую ссылку
    #             return "https://example.com/test_generated_image.jpg"
    #         
    #         # Простая реализация для обратной совместимости
    #         # В продакшене используйте FALGenerationService
    #         logger.warning(f"[FAL AI] Генерация изображений через старый API")
    #         return None
    #         
    #     except Exception as e:
    #         logger.exception(f"[FAL AI] Ошибка генерации изображения: {e}")
    #         return None

    async def _download_and_create_archive(
        self, 
        photo_urls: List[str], 
        avatar_id: UUID
    ) -> Optional[str]:
        """
        Скачивает фотографии из MinIO и создает архив для FAL AI
        
        Args:
            photo_urls: Список URL фотографий в MinIO
            avatar_id: ID аватара
            
        Returns:
            Optional[str]: URL загруженного архива
        """
        import tempfile
        import zipfile
        
        with tempfile.TemporaryDirectory(prefix=f"avatar_{avatar_id}_") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            photo_paths = []
            
            try:
                # Импортируем StorageService здесь чтобы избежать циклических импортов
                from ..storage import StorageService
                storage = StorageService()
                
                # Скачиваем фотографии
                for i, minio_key in enumerate(photo_urls):
                    try:
                        # minio_key содержит полный путь, например: avatars/user_id/avatar_id/photo_1.jpeg
                        # Используем весь путь как object_name, bucket всегда "avatars"
                        bucket_name = "avatars"
                        object_name = minio_key
                        
                        # Скачиваем файл из MinIO
                        photo_data = await storage.download_file(bucket_name, object_name)
                        
                        if not photo_data:
                            logger.warning(f"[FAL AI] Не удалось скачать фото {bucket_name}/{object_name}")
                            continue
                        
                        # Сохраняем файл во временную директорию
                        photo_path = temp_dir / f"photo_{i+1:02d}.jpg"
                        
                        # Проверяем и конвертируем изображение
                        try:
                            # Открываем изображение для валидации
                            with Image.open(io.BytesIO(photo_data)) as img:
                                # Конвертируем в RGB если нужно
                                if img.mode != 'RGB':
                                    img = img.convert('RGB')
                                
                                # Сохраняем в JPEG
                                img.save(photo_path, 'JPEG', quality=95)
                                photo_paths.append(photo_path)
                                
                                logger.debug(f"[FAL AI] Сохранено фото: {photo_path}")
                        
                        except Exception as img_error:
                            logger.warning(f"[FAL AI] Ошибка обработки изображения {bucket_name}/{object_name}: {img_error}")
                            continue
                    
                    except Exception as e:
                        logger.warning(f"[FAL AI] Ошибка скачивания фото {minio_key}: {e}")
                        continue
                
                if not photo_paths:
                    logger.error(f"[FAL AI] Не удалось скачать ни одной фотографии для аватара {avatar_id}")
                    return None
                
                logger.info(f"[FAL AI] Скачано {len(photo_paths)} фотографий для аватара {avatar_id}")
                
                # Создаем ZIP архив
                zip_path = temp_dir / f"avatar_{avatar_id}.zip"
                
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for photo_path in photo_paths:
                        if photo_path.exists():
                            # Используем только имя файла в архиве
                            arcname = photo_path.name
                            zipf.write(photo_path, arcname=arcname)
                
                logger.info(f"[FAL AI] Создан архив: {zip_path} ({len(photo_paths)} фото)")
                
                if self.test_mode:
                    # В тестовом режиме возвращаем мок URL
                    return f"https://fal.ai/test/archive_{avatar_id}.zip"
                
                # Загружаем архив на FAL AI
                data_url = await fal_client.upload_file_async(str(zip_path))
                
                logger.info(f"[FAL AI] Архив загружен: {data_url}")
                return data_url
                
            except Exception as e:
                logger.exception(f"[FAL AI] Ошибка создания архива: {e}")
                return None

    async def download_photos_from_minio(
        self, 
        photo_urls: List[str], 
        avatar_id: UUID
    ) -> List[Path]:
        """
        Скачивает фотографии из MinIO во временную директорию
        
        Args:
            photo_urls: Список URL фотографий в MinIO
            avatar_id: ID аватара для создания временной директории
            
        Returns:
            List[Path]: Пути к скачанным файлам
        """
        import tempfile
        
        with tempfile.TemporaryDirectory(prefix=f"avatar_{avatar_id}_") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            photo_paths = []
            
            try:
                # Импортируем StorageService здесь чтобы избежать циклических импортов
                from ..storage import StorageService
                storage = StorageService()
                
                for i, minio_key in enumerate(photo_urls):
                    try:
                        # minio_key содержит полный путь, например: avatars/user_id/avatar_id/photo_1.jpeg
                        # Используем весь путь как object_name, bucket всегда "avatars"
                        bucket_name = "avatars"
                        object_name = minio_key
                        
                        # Скачиваем файл из MinIO
                        photo_data = await storage.download_file(bucket_name, object_name)
                        
                        if not photo_data:
                            logger.warning(f"[FAL AI] Не удалось скачать фото {bucket_name}/{object_name}")
                            continue
                        
                        # Сохраняем файл во временную директорию
                        photo_path = temp_dir / f"photo_{i+1:02d}.jpg"
                        
                        # Проверяем и конвертируем изображение
                        try:
                            # Открываем изображение для валидации
                            with Image.open(io.BytesIO(photo_data)) as img:
                                # Конвертируем в RGB если нужно
                                if img.mode != 'RGB':
                                    img = img.convert('RGB')
                                
                                # Сохраняем в JPEG
                                img.save(photo_path, 'JPEG', quality=95)
                                photo_paths.append(photo_path)
                                
                                logger.debug(f"[FAL AI] Сохранено фото: {photo_path}")
                        
                        except Exception as img_error:
                            logger.warning(f"[FAL AI] Ошибка обработки изображения {bucket_name}/{object_name}: {img_error}")
                            continue
                    
                    except Exception as e:
                        logger.warning(f"[FAL AI] Ошибка скачивания фото {minio_key}: {e}")
                        continue
                
                logger.info(f"[FAL AI] Скачано {len(photo_paths)} фотографий для аватара {avatar_id}")
                return photo_paths
                
            except Exception as e:
                logger.exception(f"[FAL AI] Ошибка скачивания фотографий: {e}")
                return []

    async def create_and_upload_archive(
        self, 
        photo_paths: List[Path], 
        avatar_id: UUID
    ) -> Optional[str]:
        """
        Создает ZIP архив с фотографиями и загружает на FAL AI
        
        Args:
            photo_paths: Пути к фотографиям
            avatar_id: ID аватара
            
        Returns:
            Optional[str]: URL загруженного архива
        """
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = Path(tmpdir) / f"avatar_{avatar_id}.zip"
                
                # Создаем ZIP архив
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for photo_path in photo_paths:
                        if photo_path.exists():
                            # Используем только имя файла в архиве
                            arcname = photo_path.name
                            zipf.write(photo_path, arcname=arcname)
                
                logger.info(f"[FAL AI] Создан архив: {zip_path} ({len(photo_paths)} фото)")
                
                if self.test_mode:
                    # В тестовом режиме возвращаем мок URL
                    return f"https://fal.ai/test/archive_{avatar_id}.zip"
                
                # Загружаем архив на FAL AI
                data_url = await fal_client.upload_file_async(str(zip_path))
                
                logger.info(f"[FAL AI] Архив загружен: {data_url}")
                return data_url
                
        except Exception as e:
            logger.exception(f"[FAL AI] Ошибка создания/загрузки архива: {e}")
            return None

    async def _submit_training(
        self,
        data_url: str,
        user_id: UUID,
        avatar_id: UUID,
        config: Dict[str, Any]
    ) -> Optional[str]:
        """
        Отправляет задачу на обучение в FAL AI
        
        Args:
            data_url: URL архива с фотографиями
            user_id: ID пользователя
            avatar_id: ID аватара
            config: Конфигурация обучения
            
        Returns:
            Optional[str]: request_id (НЕ finetune_id!)
        """
        try:
            # Формируем аргументы для FAL AI
            arguments = {
                "data_url": data_url,
                "mode": config["mode"],
                "finetune_comment": f"user_{user_id}_avatar_{avatar_id}",
                "iterations": config["iterations"],
                "priority": config["priority"],
                "captioning": config["captioning"],
                "trigger_word": config["trigger_word"],
                "lora_rank": config["lora_rank"],
                "finetune_type": config["finetune_type"],
            }
            
            logger.info(f"[FAL AI] Отправка задачи на обучение: {arguments}")
            
            if self.test_mode:
                # В тестовом режиме возвращаем мок request_id
                return f"test_request_{avatar_id}_{user_id}"
            
            # Отправляем задачу на обучение (НЕ ЖДЕМ РЕЗУЛЬТАТ!)
            handler = await fal_client.submit_async(
                "fal-ai/flux-pro-trainer",
                arguments=arguments,
                webhook_url=config.get("webhook_url")
            )
            
            # ИСПРАВЛЕНИЕ: Возвращаем request_id сразу, не ждем завершения
            request_id = handler.request_id
            
            logger.info(f"[FAL AI] Задача отправлена, request_id: {request_id}")
            return request_id
            
        except Exception as e:
            logger.exception(f"[FAL AI] Ошибка отправки задачи на обучение: {e}")
            return None

    async def train_portrait_model(
        self,
        images_data_url: str,
        trigger_phrase: Optional[str] = None,
        steps: int = 1000,
        learning_rate: float = 0.0002,
        multiresolution_training: bool = True,
        subject_crop: bool = True,
        create_masks: bool = False,
        webhook_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Обучение портретной модели через FAL AI flux-lora-portrait-trainer
        
        Args:
            images_data_url: URL архива с изображениями
            trigger_phrase: Триггерная фраза (если None, будет использоваться trigger_word)
            steps: Количество шагов обучения (по умолчанию 1000)
            learning_rate: Скорость обучения (по умолчанию 0.0002)
            multiresolution_training: Мультиразрешающее обучение
            subject_crop: Автообрезка субъекта
            create_masks: Создание масок
            webhook_url: URL для webhook уведомлений
            
        Returns:
            Optional[str]: request_id или None при ошибке
        """
        try:
            if self.test_mode:
                logger.info(f"[FAL TEST MODE] Симуляция портретного обучения")
                await asyncio.sleep(0.1)
                return f"test_portrait_request_{int(asyncio.get_event_loop().time())}"
            
            # Формируем аргументы согласно FAL AI API
            arguments = {
                "images_data_url": images_data_url,
                "learning_rate": learning_rate,
                "steps": steps,
                "multiresolution_training": multiresolution_training,
                "subject_crop": subject_crop,
                "create_masks": create_masks
            }
            
            # Добавляем trigger_phrase если указан
            if trigger_phrase:
                arguments["trigger_phrase"] = trigger_phrase
            
            logger.info(f"[FAL AI] Запуск портретного обучения: {arguments}")
            
            # Отправляем задачу на обучение
            handler = await fal_client.submit_async(
                "fal-ai/flux-lora-portrait-trainer",
                arguments=arguments,
                webhook_url=webhook_url
            )
            
            request_id = handler.request_id
            logger.info(f"[FAL AI] Портретное обучение запущено, request_id: {request_id}")
            return request_id
            
        except Exception as e:
            logger.exception(f"[FAL AI] Ошибка запуска портретного обучения: {e}")
            return None

    async def _cleanup_temp_files(self):
        """Очищает временные файлы"""
        try:
            temp_dir = Path(settings.TEMP_DIR)
            if temp_dir.exists():
                # Удаляем только файлы аватаров старше 1 часа
                import time
                current_time = time.time()
                
                for avatar_dir in temp_dir.glob("avatar_*"):
                    if avatar_dir.is_dir():
                        # Проверяем время создания
                        if current_time - avatar_dir.stat().st_ctime > 3600:  # 1 час
                            import shutil
                            shutil.rmtree(avatar_dir, ignore_errors=True)
                            logger.debug(f"[FAL AI] Удалена временная директория: {avatar_dir}")
                            
        except Exception as e:
            logger.warning(f"[FAL AI] Ошибка очистки временных файлов: {e}")

    def is_available(self) -> bool:
        """
        Проверяет доступность FAL AI сервиса
        
        Returns:
            bool: True если сервис доступен
        """
        if self.test_mode:
            return True
            
        return bool(self.api_key)

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Возвращает сводку текущей конфигурации
        
        Returns:
            Dict[str, Any]: Конфигурация клиента
        """
        return {
            "test_mode": self.test_mode,
            "api_key_set": bool(self.api_key),
            "webhook_url": settings.FAL_WEBHOOK_URL,
            "default_mode": settings.FAL_DEFAULT_MODE,
            "default_iterations": settings.FAL_DEFAULT_ITERATIONS,
            "default_priority": settings.FAL_DEFAULT_PRIORITY,
            "trigger_word": settings.FAL_TRIGGER_WORD,
            "lora_rank": settings.FAL_LORA_RANK,
        } 