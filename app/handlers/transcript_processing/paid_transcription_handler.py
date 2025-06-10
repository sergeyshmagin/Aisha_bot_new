"""
Обработчик платной транскрипции аудио
"""
from typing import Optional, Dict, Any
from uuid import UUID

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.handlers.state import TranscribeStates

from app.core.logger import get_logger
from app.core.di import get_user_service
from app.core.database import get_session
from app.core.exceptions.audio_exceptions import InsufficientBalanceError, AudioProcessingError
from app.services.transcription_service import PaidTranscriptionService
from app.services.promokode_service import PromokodeService
from app.shared.handlers.base_handler import BaseHandler
from app.shared.decorators.auth_decorators import require_user

logger = get_logger(__name__)
router = Router()


class PaidTranscriptionHandler(BaseHandler):
    """Обработчик платной транскрибации"""
    
    def __init__(self):
        super().__init__()
    
    async def show_transcription_quote(
        self, 
        message: Message, 
        audio_data: bytes, 
        file_info: Dict[str, Any],
        user_id: UUID,
        state: FSMContext = None
    ) -> None:
        """
        Показывает расценки на транскрибацию и предлагает подтвердить платеж
        
        Args:
            message: Сообщение с аудио
            audio_data: Данные аудио файла
            file_info: Информация о файле
            user_id: ID пользователя
        """
        try:
            async with get_session() as session:
                transcription_service = PaidTranscriptionService(session)
                
                # Получаем расценки
                quote = await transcription_service.get_transcription_quote(audio_data)
                balance_estimate = await transcription_service.check_balance_and_estimate(user_id, audio_data)
                
                # Форматируем информацию
                duration_str = f"{quote['duration_minutes']:.1f} мин"
                if quote['duration_seconds'] < 60:
                    duration_str = f"{quote['duration_seconds']:.0f} сек"
                
                size_mb = quote['file_size_mb']
                
                text = f"""💰 <b>Платная транскрибация</b>

📎 <b>Файл:</b> {file_info.get('file_name', 'аудио')}
⏱️ <b>Длительность:</b> {duration_str}
📦 <b>Размер:</b> {size_mb:.1f} МБ
🔊 <b>Качество:</b> {quote['quality_info']['sample_rate']} Hz, {quote['quality_info']['bitrate']} kbps

💵 <b>Стоимость:</b> {quote['cost']:.0f} монет
📊 <b>Тариф:</b> {quote['cost_per_minute']:.0f} монет/мин
📝 <b>~Слов:</b> {quote['estimate_words']}

💰 <b>Ваш баланс:</b> {balance_estimate['current_balance']:.0f} монет"""
                
                # Определяем доступность услуги
                if balance_estimate['can_afford']:
                    text += f"\n✅ <b>Достаточно средств</b>\n💳 К списанию: {quote['cost']:.0f} монет"
                    
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=f"💳 Оплатить {quote['cost']:.0f} монет",
                                callback_data=f"pay_transcription_{hash(str(audio_data[:100]))}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="🎁 Ввести промокод",
                                callback_data=f"enter_promo_{hash(str(audio_data[:100]))}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="❌ Отмена",
                                callback_data="transcription_cancel"
                            )
                        ]
                    ])
                else:
                    shortage = balance_estimate['required_balance']
                    text += f"\n❌ <b>Недостаточно средств</b>\n💸 Нехватает: {shortage:.0f} монет"
                    
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=f"💳 Пополнить баланс",
                                callback_data="profile_topup_balance"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="🎁 Ввести промокод",
                                callback_data=f"enter_promo_{hash(str(audio_data[:100]))}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="❌ Отмена",
                                callback_data="transcription_cancel"
                            )
                        ]
                    ])
                
                # Сохраняем данные аудио во временном хранилище
                await self._store_audio_data(message.from_user.id, audio_data, file_info, quote)
                
                # Устанавливаем состояние ожидания подтверждения оплаты
                if state:
                    await state.set_state(TranscribeStates.waiting_payment_confirmation)
                else:
                    # Fallback: создаем контекст FSM вручную
                    from aiogram.fsm.context import FSMContext
                    from app.core.di import get_state_storage
                    
                    storage = get_state_storage()
                    manual_state = FSMContext(
                        storage=storage,
                        key=storage.make_key(
                            bot_id=message.bot.id,
                            chat_id=message.chat.id,
                            user_id=message.from_user.id
                        )
                    )
                    await manual_state.set_state(TranscribeStates.waiting_payment_confirmation)
                
                await message.answer(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                
        except Exception as e:
            logger.exception(f"Ошибка показа расценок транскрибации: {e}")
            await message.answer(
                "❌ Произошла ошибка при расчете стоимости транскрибации. "
                "Попробуйте позже или обратитесь в поддержку."
            )
    
    async def process_paid_transcription(
        self,
        callback: CallbackQuery,
        user_id: UUID
    ) -> None:
        """
        Обрабатывает платную транскрибацию после подтверждения оплаты
        
        Args:
            callback: Callback с подтверждением оплаты
            user_id: ID пользователя
        """
        try:
            # ВАЖНО: Отвечаем на callback сразу, до длительной операции
            await callback.answer()
            
            # Извлекаем сохраненные данные аудио
            audio_data, file_info, quote = await self._retrieve_audio_data(callback.from_user.id)
            
            if not audio_data:
                await callback.message.edit_text(
                    "❌ Данные аудио не найдены. Попробуйте снова.",
                    reply_markup=None
                )
                return
            
            # Обновляем сообщение о начале транскрибации
            await callback.message.edit_text(
                f"""🎵 <b>Обрабатываю аудио...</b>

💳 Списываю {quote['cost']:.0f} монет...
🔄 Запускаю транскрибацию...

⏳ Это может занять до {int(quote['duration_minutes']) + 1} минут""",
                parse_mode="HTML"
            )
            
            async with get_session() as session:
                transcription_service = PaidTranscriptionService(session)
                
                # Выполняем платную транскрибацию
                result = await transcription_service.transcribe_with_payment(
                    user_id=user_id,
                    audio_data=audio_data,
                    language="ru",
                    metadata={
                        "source": file_info.get("source_type", "audio"),
                        "file_name": file_info.get("file_name", "audio"),
                        "file_size": file_info.get("file_size", 0),
                        "file_id": file_info.get("file_id"),
                        "processing_type": "paid_transcription"
                    }
                )
                
                if result["success"]:
                    # Успешная транскрибация
                    payment_info = result["payment_info"]
                    transcript_id = result.get("transcript_id")  # Получаем ID сохраненного транскрипта
                    
                    # Создаем краткое превью текста
                    text_preview = result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"]
                    
                    # Объединяем информацию о результате с описанием файла
                    combined_caption = f"""✅ <b>Транскрибация завершена!</b>

💳 <b>Списано:</b> {payment_info['cost']:.0f} монет
💰 <b>Баланс:</b> {payment_info['new_balance']:.0f} монет
⏱️ <b>Длительность:</b> {payment_info['duration']:.0f} сек

📝 <b>Превью:</b>
{text_preview}

📎 <b>Полный текст транскрипции</b>
🔧 <b>Выберите действие для обработки:</b>"""
                    
                    # Отправляем файл с объединенным текстом и меню
                    from aiogram.types import BufferedInputFile
                    from app.keyboards.transcript import get_transcript_actions_keyboard
                    
                    file_name = file_info.get("file_name", "transcript")
                    if not file_name.endswith(".txt"):
                        file_name = file_name.rsplit(".", 1)[0] + ".txt"
                    
                    input_file = BufferedInputFile(
                        result["text"].encode('utf-8'),
                        filename=file_name
                    )
                    
                    # Определяем клавиатуру и caption
                    if transcript_id:
                        keyboard = get_transcript_actions_keyboard(transcript_id)
                    else:
                        keyboard = None
                        # Если нет transcript_id, убираем строку про выбор действия
                        combined_caption = combined_caption.replace(
                            "\n🔧 <b>Выберите действие для обработки:</b>", ""
                        )
                    
                    # Удаляем сообщение с расценками и отправляем файл с полной информацией
                    await callback.message.delete()
                    await callback.message.answer_document(
                        document=input_file,
                        caption=combined_caption,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                    
                else:
                    await callback.message.edit_text(
                        "❌ Произошла ошибка при транскрибации. "
                        "Средства возвращены на ваш баланс."
                    )
            
            # Очищаем временные данные
            await self._clear_audio_data(callback.from_user.id)
            
        except InsufficientBalanceError as e:
            await callback.message.edit_text(
                f"❌ <b>Недостаточно средств</b>\n\n{str(e)}\n\n"
                "Пополните баланс или используйте промокод.",
                parse_mode="HTML"
            )
            
        except AudioProcessingError as e:
            await callback.message.edit_text(
                f"❌ <b>Ошибка обработки аудио</b>\n\n{str(e)}",
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.exception(f"Ошибка платной транскрибации: {e}")
            await callback.message.edit_text(
                "❌ Произошла внутренняя ошибка. Попробуйте позже."
            )
    
    async def handle_promo_code_entry(self, callback: CallbackQuery, state: FSMContext) -> None:
        """
        Обрабатывает ввод промокода
        
        Args:
            callback: Callback кнопки промокода
            state: Состояние FSM
        """
        try:
            await callback.message.edit_text(
                "🎁 <b>Введите промокод</b>\n\n"
                "Отправьте промокод следующим сообщением:",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="❌ Отмена",
                            callback_data="transcription_cancel"
                        )
                    ]
                ])
            )
            
            await state.set_state(TranscribeStates.waiting_promo_code)
            await state.update_data({"callback_data": callback.data})
            
        except Exception as e:
            logger.exception(f"Ошибка обработки ввода промокода: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def apply_promo_code(
        self, 
        message: Message, 
        state: FSMContext, 
        user_id: UUID
    ) -> None:
        """
        Применяет промокод
        
        Args:
            message: Сообщение с промокодом
            state: Состояние FSM
            user_id: ID пользователя
        """
        try:
            promo_code = message.text.strip().upper()
            
            async with get_session() as session:
                promo_service = PromokodeService(session)
                
                # Валидируем и применяем промокод
                is_valid, error_msg, result = await promo_service.apply_promokode(
                    code=promo_code,
                    user_id=user_id
                )
                
                if is_valid:
                    coins_added = result.get("total_coins_added", 0)
                    success_text = f"""🎉 <b>Промокод применен!</b>

🎁 <b>Промокод:</b> {promo_code}
💰 <b>Получено:</b> {coins_added} монет
📝 <b>Описание:</b> {result.get('message', 'Промокод применен')}

✅ Теперь вы можете продолжить транскрибацию!"""
                    
                    await message.answer(
                        success_text,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="🔄 Обновить расценки",
                                    callback_data="refresh_transcription_quote"
                                )
                            ]
                        ])
                    )
                    
                else:
                    await message.answer(
                        f"❌ <b>Ошибка промокода</b>\n\n{error_msg}",
                        parse_mode="HTML"
                    )
            
            await state.clear()
            
        except Exception as e:
            logger.exception(f"Ошибка применения промокода: {e}")
            await message.answer("❌ Произошла ошибка при применении промокода")
            await state.clear()
    
    async def _store_audio_data(
        self, 
        user_id: int, 
        audio_data: bytes, 
        file_info: Dict[str, Any], 
        quote: Dict[str, Any]
    ) -> None:
        """
        Сохраняет данные аудио в Redis для production
        """
        try:
            from app.services.redis_storage import AudioDataRedisStorage
            storage = AudioDataRedisStorage()
            
            success = await storage.store_audio_data(
                user_id=user_id,
                audio_data=audio_data,
                file_info=file_info,
                quote=quote,
                ttl_seconds=3600  # 1 час
            )
            
            if not success:
                logger.warning(f"Не удалось сохранить аудио данные в Redis для пользователя {user_id}")
                
        except Exception as e:
            logger.exception(f"Ошибка сохранения аудио данных: {e}")
            # Fallback к временному хранению в памяти для development
            if not hasattr(self, '_temp_storage'):
                self._temp_storage = {}
            
            self._temp_storage[user_id] = {
                'audio_data': audio_data,
                'file_info': file_info,
                'quote': quote
            }
            logger.info(f"Использовано fallback хранение в памяти для пользователя {user_id}")
    
    async def _retrieve_audio_data(self, user_id: int) -> tuple:
        """
        Извлекает данные аудио из Redis или fallback хранилища
        """
        try:
            from app.services.redis_storage import AudioDataRedisStorage
            storage = AudioDataRedisStorage()
            
            audio_data, file_info, quote = await storage.retrieve_audio_data(user_id)
            
            if audio_data is not None:
                return audio_data, file_info, quote
            
        except Exception as e:
            logger.exception(f"Ошибка извлечения из Redis: {e}")
        
        # Fallback к временному хранению в памяти
        if hasattr(self, '_temp_storage'):
            data = self._temp_storage.get(user_id)
            if data:
                return data['audio_data'], data['file_info'], data['quote']
        
        return None, None, None
    
    async def _clear_audio_data(self, user_id: int) -> None:
        """
        Очищает данные аудио из Redis и fallback хранилища
        """
        try:
            from app.services.redis_storage import AudioDataRedisStorage
            storage = AudioDataRedisStorage()
            await storage.clear_audio_data(user_id)
            
        except Exception as e:
            logger.exception(f"Ошибка очистки Redis: {e}")
        
        # Очистка fallback хранилища
        if hasattr(self, '_temp_storage') and user_id in self._temp_storage:
            del self._temp_storage[user_id]


# Регистрируем обработчики callback
@router.callback_query(F.data.startswith("pay_transcription_"))
@require_user()
async def handle_pay_transcription(callback: CallbackQuery, user=None):
    """Обработчик оплаты транскрибации"""
    handler = PaidTranscriptionHandler()
    await handler.process_paid_transcription(callback, user.id)


@router.callback_query(F.data.startswith("enter_promo_"))
async def handle_enter_promo(callback: CallbackQuery, state: FSMContext):
    """Обработчик ввода промокода"""
    await callback.message.edit_text(
        "🎁 <b>Введите промокод</b>\n\n"
        "Отправьте промокод следующим сообщением:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="transcription_cancel"
                )
            ]
        ])
    )
    
    await state.set_state(TranscribeStates.waiting_promo_code)
    await callback.answer()


@router.callback_query(F.data == "transcription_cancel")
async def handle_transcription_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена транскрибации"""
    # Очищаем временные данные аудио
    try:
        handler = PaidTranscriptionHandler()
        await handler._clear_audio_data(callback.from_user.id)
    except Exception as e:
        logger.exception(f"Ошибка очистки данных при отмене: {e}")
    
    # Показываем главное меню
    from app.handlers.main_menu import show_main_menu
    await show_main_menu(callback, state)
    
    await state.clear()
    await callback.answer("Транскрибация отменена")


@router.callback_query(F.data == "refresh_transcription_quote")
async def handle_refresh_quote(callback: CallbackQuery):
    """Обновление расценок после применения промокода"""
    await callback.message.edit_text(
        "🔄 Обновите расценки, отправив аудиофайл заново",
        reply_markup=None
    )
    await callback.answer() 