"""
Основной сервис для работы с Google Imagen 4 API
"""
import asyncio
import time
from typing import Optional, Dict, Any
import logging

try:
    import fal_client
except ImportError:
    fal_client = None
    
from app.core.logger import get_logger
from app.core.config import settings
from .models import (
    Imagen4Request, 
    Imagen4Response, 
    Imagen4GenerationResult, 
    Imagen4GenerationStatus,
    Imagen4Config,
    Imagen4Image
)

logger = get_logger(__name__)


class Imagen4Service:
    """Сервис для работы с Google Imagen 4 API через FAL"""
    
    def __init__(self):
        self.config = self._load_config()
        self._setup_fal_environment()
        self._validate_dependencies()
    
    def _load_config(self) -> Imagen4Config:
        """Загружает конфигурацию из настроек приложения"""
        return Imagen4Config(
            api_key=settings.effective_fal_api_key,
            enabled=getattr(settings, 'IMAGEN4_ENABLED', True),
            default_aspect_ratio=getattr(settings, 'IMAGEN4_DEFAULT_ASPECT_RATIO', '1:1'),
            max_images=getattr(settings, 'IMAGEN4_MAX_IMAGES', 4),
            generation_cost=settings.IMAGEN4_GENERATION_COST,
            timeout_seconds=getattr(settings, 'IMAGEN4_TIMEOUT', 300)
        )
    
    def _setup_fal_environment(self):
        """Настраивает переменные окружения для FAL клиента"""
        import os
        
        # Устанавливаем FAL_KEY для совместимости с fal_client, если она не установлена
        if not os.getenv('FAL_KEY') and self.config.api_key:
            os.environ['FAL_KEY'] = self.config.api_key
            logger.debug(f"FAL_KEY установлен для совместимости с fal_client")
    
    def _validate_dependencies(self):
        """Проверяет доступность необходимых зависимостей"""
        if not fal_client:
            logger.error("fal_client не установлен. Установите: pip install fal-client")
            raise ImportError("fal_client package is required for Imagen 4")
        
        if not self.config.api_key:
            logger.error("FAL_API_KEY не настроен в переменных окружения")
            raise ValueError("FAL_API_KEY environment variable is required")
    
    def is_available(self) -> bool:
        """Проверяет доступность сервиса"""
        return (
            self.config.enabled and 
            bool(self.config.api_key) and 
            fal_client is not None
        )
    
    def _check_content_safety(self, prompt: str) -> bool:
        """
        Простая предварительная проверка контента
        
        Args:
            prompt: Текст промпта
            
        Returns:
            True если контент безопасен, False иначе
        """
        # Список проблематичных слов/фраз
        unsafe_keywords = [
            "синдром дауна", "down syndrome", "ментальная отсталость",
            "умственная отсталость", "дебил", "идиот", "кретин",
            "насилие", "violence", "убийство", "murder", "кровь", "blood",
            "порно", "porn", "секс", "sex", "голый", "nude", "naked",
            "наркотики", "drugs", "марихуана", "cocaine", "героин"
        ]
        
        prompt_lower = prompt.lower()
        
        for keyword in unsafe_keywords:
            if keyword in prompt_lower:
                return False
        
        return True

    async def generate_image(self, request: Imagen4Request) -> Imagen4GenerationResult:
        """
        Генерирует изображение через Imagen 4 API
        
        Args:
            request: Запрос на генерацию
            
        Returns:
            Результат генерации с информацией о статусе
        """
        if not self.is_available():
            return Imagen4GenerationResult(
                status=Imagen4GenerationStatus.FAILED,
                error_message="Imagen 4 service is not available"
            )
        
        # Предварительная проверка контента
        if not self._check_content_safety(request.prompt):
            return Imagen4GenerationResult(
                status=Imagen4GenerationStatus.FAILED,
                error_message="Контент может быть заблокирован системой безопасности. Измените формулировку запроса."
            )
        
        start_time = time.time()
        
        try:
            logger.info(f"[Imagen4] Начинаю генерацию: '{request.prompt[:50]}...'")
            
            # Подготавливаем аргументы для API
            api_args = {
                "prompt": request.prompt,
                "aspect_ratio": request.aspect_ratio.value,
                "num_images": request.num_images
            }
            
            # Добавляем негативный промпт если есть
            if request.negative_prompt:
                api_args["negative_prompt"] = request.negative_prompt
            
            # Добавляем seed если указан
            if request.seed is not None:
                api_args["seed"] = request.seed
            
            # Отправляем запрос в Imagen 4
            result = await self._call_fal_api(api_args)
            
            generation_time = time.time() - start_time
            
            # Парсим ответ
            response = self._parse_fal_response(result)
            
            logger.info(f"[Imagen4] Генерация завершена за {generation_time:.2f}s, получено {len(response.images)} изображений")
            
            return Imagen4GenerationResult(
                status=Imagen4GenerationStatus.COMPLETED,
                response=response,
                generation_time=generation_time,
                cost_credits=self.config.generation_cost
            )
            
        except Exception as e:
            generation_time = time.time() - start_time
            error_msg = f"Ошибка генерации Imagen 4: {str(e)}"
            logger.exception(error_msg)
            
            return Imagen4GenerationResult(
                status=Imagen4GenerationStatus.FAILED,
                error_message=error_msg,
                generation_time=generation_time
            )
    
    async def _call_fal_api(self, api_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Вызывает FAL API для Imagen 4
        
        Args:
            api_args: Аргументы для API
            
        Returns:
            Ответ от API
        """
        try:
            # Используем асинхронный клиент FAL
            handler = await fal_client.submit_async(
                self.config.api_endpoint,
                arguments=api_args
            )
            
            # Ждем результат с таймаутом
            result = await asyncio.wait_for(
                handler.get(),
                timeout=self.config.timeout_seconds
            )
            
            return result
            
        except asyncio.TimeoutError:
            raise Exception(f"Таймаут генерации ({self.config.timeout_seconds}s)")
        except Exception as e:
            error_msg = str(e)
            # Улучшаем сообщение для ошибок безопасности
            if "filtered by safety checks" in error_msg.lower():
                raise Exception("Контент заблокирован системой безопасности. Измените формулировку запроса.")
            elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                raise Exception("Превышен лимит API. Попробуйте позже.")
            elif "invalid" in error_msg.lower() and "key" in error_msg.lower():
                raise Exception("Неверный API ключ. Обратитесь к администратору.")
            else:
                raise Exception(f"Ошибка вызова FAL API: {error_msg}")
    
    def _parse_fal_response(self, fal_result: Dict[str, Any]) -> Imagen4Response:
        """
        Парсит ответ от FAL API в наш формат
        
        Args:
            fal_result: Результат от FAL API
            
        Returns:
            Структурированный ответ
        """
        try:
            images = []
            
            # Парсим изображения
            if "images" in fal_result and isinstance(fal_result["images"], list):
                for img_data in fal_result["images"]:
                    if isinstance(img_data, dict) and "url" in img_data:
                        image = Imagen4Image(
                            url=img_data["url"],
                            content_type=img_data.get("content_type"),
                            file_name=img_data.get("file_name"),
                            file_size=img_data.get("file_size")
                        )
                        images.append(image)
            
            if not images:
                raise ValueError("Не найдены изображения в ответе API")
            
            return Imagen4Response(
                images=images,
                seed=fal_result.get("seed")
            )
            
        except Exception as e:
            raise Exception(f"Ошибка парсинга ответа FAL API: {str(e)}")
    
    def estimate_cost(self, num_images: int = 1) -> float:
        """
        Оценивает стоимость генерации в кредитах
        
        Args:
            num_images: Количество изображений
            
        Returns:
            Стоимость в кредитах
        """
        return self.config.generation_cost * num_images
    
    def get_config(self) -> Imagen4Config:
        """Возвращает текущую конфигурацию"""
        return self.config


# Глобальный экземпляр сервиса
imagen4_service = Imagen4Service() 