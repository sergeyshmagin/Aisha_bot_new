"""
Платный сервис транскрибации с поддержкой определения длительности через ffmpeg
"""
from typing import Optional, Dict, Any, Tuple
from uuid import UUID

from app.core.logger import get_logger
from app.core.config import settings
from app.core.exceptions.audio_exceptions import AudioProcessingError, InsufficientBalanceError
from app.services.base import BaseService
from app.services.audio_processing.duration_service import AudioDurationService
from app.services.balance_service import BalanceService
from app.services.audio_processing.factory import get_audio_service
from app.services.transcript import TranscriptService

logger = get_logger(__name__)


class PaidTranscriptionService(BaseService):
    """Платный сервис транскрибации с проверкой баланса"""
    
    def __init__(self, session):
        super().__init__(session)
        self.duration_service = AudioDurationService()
        self.balance_service = BalanceService(session)
        self.audio_service = get_audio_service()
        self.transcript_service = TranscriptService(session)
    
    async def calculate_cost(self, audio_data: bytes) -> Tuple[float, float]:
        """
        Рассчитывает стоимость транскрибации
        
        Args:
            audio_data: Аудио данные
            
        Returns:
            Tuple[float, float]: (длительность_в_секундах, стоимость_в_монетах)
        """
        try:
            # Определяем длительность через ffmpeg
            duration_seconds = await self.duration_service.get_audio_duration(audio_data)
            
            # Рассчитываем стоимость
            cost = self.duration_service.calculate_transcription_cost(
                duration_seconds, 
                settings.TRANSCRIPTION_COST_PER_MINUTE
            )
            
            logger.info(f"Рассчитана стоимость транскрибации: {duration_seconds:.2f}с = {cost} монет")
            return duration_seconds, cost
            
        except Exception as e:
            logger.exception(f"Ошибка расчета стоимости: {e}")
            raise AudioProcessingError(f"Ошибка расчета стоимости: {str(e)}")
    
    async def check_balance_and_estimate(self, user_id: UUID, audio_data: bytes) -> Dict[str, Any]:
        """
        Проверяет баланс и оценивает стоимость транскрибации
        
        Args:
            user_id: ID пользователя
            audio_data: Аудио данные
            
        Returns:
            Dict: Информация о стоимости и доступности услуги
        """
        try:
            # Рассчитываем стоимость
            duration, cost = await self.calculate_cost(audio_data)
            
            # Получаем баланс пользователя
            balance = await self.balance_service.get_balance(user_id)
            
            # Проверяем достаточность средств
            can_afford = balance >= cost
            
            # Получаем дополнительную информацию об аудио
            audio_info = await self.duration_service.get_audio_info(audio_data)
            
            return {
                "duration_seconds": duration,
                "duration_minutes": duration / 60.0,
                "cost": cost,
                "current_balance": balance,
                "can_afford": can_afford,
                "required_balance": cost - balance if not can_afford else 0,
                "audio_info": audio_info,
                "cost_per_minute": settings.TRANSCRIPTION_COST_PER_MINUTE
            }
            
        except Exception as e:
            logger.exception(f"Ошибка проверки баланса: {e}")
            raise AudioProcessingError(f"Ошибка проверки баланса: {str(e)}")
    
    async def transcribe_with_payment(
        self, 
        user_id: UUID, 
        audio_data: bytes,
        language: str = "ru",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Выполняет платную транскрибацию с списанием средств
        
        Args:
            user_id: ID пользователя
            audio_data: Аудио данные
            language: Язык транскрибации
            metadata: Дополнительные метаданные
            
        Returns:
            Dict: Результат транскрибации с информацией о платеже
        """
        try:
            # Проверяем баланс и рассчитываем стоимость
            estimate = await self.check_balance_and_estimate(user_id, audio_data)
            
            if not estimate["can_afford"]:
                raise InsufficientBalanceError(
                    f"Недостаточно средств для транскрибации. "
                    f"Требуется: {estimate['cost']} монет, "
                    f"доступно: {estimate['current_balance']} монет"
                )
            
            # Списываем средства
            payment_result = await self.balance_service.charge_balance(
                user_id=user_id,
                amount=estimate["cost"],
                description=f"Транскрибация аудио ({estimate['duration_minutes']:.1f} мин)"
            )
            
            if not payment_result["success"]:
                raise AudioProcessingError(f"Ошибка списания средств: {payment_result['error']}")
            
            try:
                # Выполняем транскрибацию
                transcription_result = await self.audio_service.process_audio(
                    audio_data=audio_data,
                    language=language,
                    save_original=True,
                    normalize=True,
                    remove_silence=True
                )
                
                if not transcription_result.success:
                    # Если транскрибация не удалась, возвращаем деньги
                    await self.balance_service.add_balance(
                        user_id=user_id,
                        amount=estimate["cost"],
                        description=f"Возврат за неудачную транскрибацию"
                    )
                    raise AudioProcessingError(f"Ошибка транскрибации: {transcription_result.error}")
                
                # Сохраняем транскрипт
                transcript_metadata = {
                    **(metadata or {}),
                    "duration_seconds": estimate["duration_seconds"],
                    "duration_minutes": estimate["duration_minutes"],
                    "cost_paid": estimate["cost"],
                    "cost_per_minute": settings.TRANSCRIPTION_COST_PER_MINUTE,
                    "audio_format": estimate["audio_info"]["format"],
                    "audio_bitrate": estimate["audio_info"]["bitrate"],
                    "audio_sample_rate": estimate["audio_info"]["sample_rate"],
                    "processing_type": "paid_transcription",
                    "payment_id": payment_result.get("transaction_id")
                }
                
                saved_transcript = await self.transcript_service.save_transcript(
                    user_id=user_id,
                    audio_data=audio_data,
                    transcript_data=transcription_result.text.encode('utf-8'),
                    metadata=transcript_metadata
                )
                
                logger.info(f"Успешная платная транскрибация для пользователя {user_id}: {estimate['cost']} монет")
                
                return {
                    "success": True,
                    "transcript": saved_transcript,
                    "transcript_id": saved_transcript.get("id") if saved_transcript else None,
                    "text": transcription_result.text,
                    "payment_info": {
                        "cost": estimate["cost"],
                        "duration": estimate["duration_seconds"],
                        "new_balance": payment_result.get("new_balance", 0),
                        "transaction_id": payment_result.get("transaction_id")
                    },
                    "audio_info": estimate["audio_info"]
                }
                
            except Exception as transcribe_error:
                # При ошибке транскрибации возвращаем деньги
                try:
                    await self.balance_service.add_balance(
                        user_id=user_id,
                        amount=estimate["cost"],
                        description="Возврат за неудачную транскрибацию"
                    )
                    logger.info(f"Возвращены средства пользователю {user_id}: {estimate['cost']} монет")
                except Exception as refund_error:
                    logger.error(f"Ошибка возврата средств: {refund_error}")
                
                raise transcribe_error
                
        except Exception as e:
            logger.exception(f"Ошибка платной транскрибации: {e}")
            if isinstance(e, (InsufficientBalanceError, AudioProcessingError)):
                raise
            raise AudioProcessingError(f"Ошибка платной транскрибации: {str(e)}")
    
    async def get_transcription_quote(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Получает расценки на транскрибацию без списания средств
        
        Args:
            audio_data: Аудио данные
            
        Returns:
            Dict: Информация о стоимости и длительности
        """
        try:
            duration, cost = await self.calculate_cost(audio_data)
            audio_info = await self.duration_service.get_audio_info(audio_data)
            
            # Округляем минуты в большую сторону для отображения
            full_minutes = int(duration / 60.0) if duration % 60 == 0 else int(duration / 60.0) + 1
            
            return {
                "duration_seconds": duration,
                "duration_minutes": duration / 60.0,
                "billing_minutes": full_minutes,
                "cost": cost,
                "cost_per_minute": settings.TRANSCRIPTION_COST_PER_MINUTE,
                "audio_format": audio_info["format"],
                "file_size_mb": len(audio_data) / (1024 * 1024),
                "estimate_words": int(duration * 2.5),  # Примерно 2.5 слова в секунду
                "quality_info": {
                    "sample_rate": audio_info["sample_rate"],
                    "bitrate": audio_info["bitrate"],
                    "channels": audio_info["channels"]
                }
            }
            
        except Exception as e:
            logger.exception(f"Ошибка получения расценок: {e}")
            raise AudioProcessingError(f"Ошибка получения расценок: {str(e)}")
    
    async def is_service_available(self) -> bool:
        """
        Проверяет доступность сервиса транскрибации
        
        Returns:
            bool: True если сервис доступен
        """
        try:
            # Проверяем доступность ffmpeg
            ffmpeg_available = await self.duration_service.is_ffmpeg_available()
            
            # Проверяем наличие OpenAI API ключа
            openai_available = bool(settings.OPENAI_API_KEY)
            
            if not ffmpeg_available:
                logger.warning("FFmpeg недоступен")
                
            if not openai_available:
                logger.warning("OpenAI API ключ не настроен")
            
            return ffmpeg_available and openai_available
            
        except Exception as e:
            logger.exception(f"Ошибка проверки доступности сервиса: {e}")
            return False 