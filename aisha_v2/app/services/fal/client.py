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
        self.test_mode = settings.FAL_TRAINING_TEST_MODE
        
        # Настраиваем FAL клиент
        if self.api_key:
            fal_client.api_key = self.api_key
        else:
            logger.warning("FAL_API_KEY не установлен, работа в тестовом режиме")

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
            training_config: Конфигурация обучения
            
        Returns:
            Optional[str]: finetune_id или None при ошибке
            
        Raises:
            RuntimeError: При критических ошибках
        """
        try:
            if self.test_mode:
                logger.info(f"[FAL TEST MODE] Симуляция обучения аватара {avatar_id}")
                # В тестовом режиме возвращаем мок finetune_id
                mock_finetune_id = f"test_finetune_{avatar_id}"
                await asyncio.sleep(0.1)  # Симуляция задержки
                return mock_finetune_id
            
            # Настройки по умолчанию
            config = {
                "mode": settings.FAL_DEFAULT_MODE,
                "iterations": settings.FAL_DEFAULT_ITERATIONS,
                "priority": settings.FAL_DEFAULT_PRIORITY,
                "captioning": True,
                "trigger_word": settings.FAL_TRIGGER_WORD,
                "lora_rank": settings.FAL_LORA_RANK,
                "finetune_type": settings.FAL_FINETUNE_TYPE,
                "webhook_url": settings.FAL_WEBHOOK_URL,
            }
            
            # Обновляем конфигурацию пользовательскими параметрами
            if training_config:
                config.update(training_config)
            
            logger.info(
                f"[FAL AI] Начало обучения аватара {avatar_id}: "
                f"user_id={user_id}, name='{name}', gender={gender}, "
                f"photos={len(photo_urls)}, config={config}"
            )
            
            # 1. Скачиваем фотографии из MinIO
            photo_paths = await self._download_photos_from_minio(photo_urls, avatar_id)
            
            if not photo_paths:
                raise RuntimeError("Не удалось скачать фотографии из MinIO")
            
            # 2. Создаем архив с фотографиями
            data_url = await self._create_and_upload_archive(photo_paths, avatar_id)
            
            if not data_url:
                raise RuntimeError("Не удалось создать архив с фотографиями")
            
            # 3. Запускаем обучение на FAL AI
            finetune_id = await self._submit_training(
                data_url=data_url,
                user_id=user_id,
                avatar_id=avatar_id,
                config=config
            )
            
            logger.info(f"[FAL AI] Обучение запущено успешно: finetune_id={finetune_id}")
            return finetune_id
            
        except Exception as e:
            logger.exception(f"[FAL AI] Критическая ошибка при обучении аватара {avatar_id}: {e}")
            raise RuntimeError(f"Ошибка обучения аватара: {str(e)}")
        
        finally:
            # Очищаем временные файлы
            await self._cleanup_temp_files()

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

    async def generate_image(
        self,
        finetune_id: str,
        prompt: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Генерирует изображение с обученной моделью
        
        Args:
            finetune_id: ID обученной модели
            prompt: Промпт для генерации
            config: Дополнительные параметры генерации
            
        Returns:
            Optional[str]: URL сгенерированного изображения
        """
        try:
            if self.test_mode:
                logger.info(f"[FAL TEST MODE] Симуляция генерации с моделью {finetune_id}")
                # Возвращаем тестовую ссылку
                return "https://example.com/test_generated_image.jpg"
            
            # TODO: Реализовать генерацию изображений
            logger.warning(f"[FAL AI] Генерация изображений пока не реализована")
            return None
            
        except Exception as e:
            logger.exception(f"[FAL AI] Ошибка генерации изображения: {e}")
            return None

    async def _download_photos_from_minio(
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
        photo_paths = []
        
        try:
            # Создаем временную директорию для аватара
            temp_dir = Path(settings.TEMP_DIR) / f"avatar_{avatar_id}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Импортируем StorageService здесь чтобы избежать циклических импортов
            from ..storage import StorageService
            storage = StorageService()
            
            for i, photo_url in enumerate(photo_urls):
                try:
                    # Извлекаем путь объекта из URL (предполагаем формат MinIO URL)
                    object_name = photo_url.split('/')[-1] if '/' in photo_url else photo_url
                    
                    # Скачиваем файл из MinIO
                    photo_data = await storage.download_file("avatars", object_name)
                    
                    if not photo_data:
                        logger.warning(f"[FAL AI] Не удалось скачать фото {object_name}")
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
                        logger.warning(f"[FAL AI] Ошибка обработки изображения {object_name}: {img_error}")
                        continue
                
                except Exception as e:
                    logger.warning(f"[FAL AI] Ошибка скачивания фото {photo_url}: {e}")
                    continue
            
            logger.info(f"[FAL AI] Скачано {len(photo_paths)} фотографий для аватара {avatar_id}")
            return photo_paths
            
        except Exception as e:
            logger.exception(f"[FAL AI] Ошибка скачивания фотографий: {e}")
            return []

    async def _create_and_upload_archive(
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
            Optional[str]: finetune_id
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
                # В тестовом режиме возвращаем мок ID
                return f"test_finetune_{avatar_id}_{user_id}"
            
            # Отправляем задачу на обучение
            handler = await fal_client.submit_async(
                "fal-ai/flux-pro-trainer",
                arguments=arguments,
                webhook_url=config.get("webhook_url")
            )
            
            # Получаем результат с finetune_id
            result = await handler.get()
            finetune_id = result.get("finetune_id")
            
            if not finetune_id:
                raise RuntimeError(f"FAL AI не вернул finetune_id: {result}")
            
            return finetune_id
            
        except Exception as e:
            logger.exception(f"[FAL AI] Ошибка отправки задачи на обучение: {e}")
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