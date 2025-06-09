"""
Обработчик промо-кодов для транскрипции
"""
from uuid import UUID

from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.core.logger import get_logger
from app.core.di import get_user_service
from app.core.database import get_session
from app.services.promokode_service import PromokodeService
from app.shared.decorators.auth_decorators import require_user

logger = get_logger(__name__)
router = Router()


from app.handlers.state import TranscribeStates

@router.message(F.text, TranscribeStates.waiting_promo_code)
@require_user()
async def handle_promo_code_message(message: Message, state: FSMContext, user=None):
    """
    Обрабатывает сообщение с промо-кодом
    
    Args:
        message: Сообщение с промо-кодом
        state: Состояние FSM
        user: Пользователь (из декоратора)
    """
    try:
        promo_code = message.text.strip().upper()
        
        # Удаляем сообщение пользователя с промо-кодом для безопасности
        try:
            await message.delete()
        except Exception:
            pass  # Игнорируем ошибки удаления
        
        async with get_session() as session:
            promo_service = PromokodeService(session)
            
            # Валидируем и применяем промокод
            is_valid, error_msg, result = await promo_service.apply_promokode(
                code=promo_code,
                user_id=user.id
            )
            
            if is_valid:
                coins_added = result.get("total_coins_added", 0)
                success_text = f"""🎉 <b>Промокод применен!</b>

🎁 <b>Промокод:</b> <code>{promo_code}</code>
💰 <b>Получено:</b> {coins_added} монет
📝 <b>Описание:</b> {result.get('message', 'Промокод применен')}

✅ Теперь вы можете продолжить транскрибацию!
Отправьте аудиофайл заново для обновления расценок."""
                
                await message.answer(
                    success_text,
                    parse_mode="HTML"
                )
                
                logger.info(f"Промокод {promo_code} успешно применен пользователем {user.id}: +{coins_added} монет")
                
            else:
                await message.answer(
                    f"❌ <b>Ошибка промокода</b>\n\n{error_msg}",
                    parse_mode="HTML"
                )
                
                logger.info(f"Неудачная попытка применения промокода {promo_code} пользователем {user.id}: {error_msg}")
        
        await state.clear()
        
    except Exception as e:
        logger.exception(f"Ошибка обработки промо-кода: {e}")
        await message.answer("❌ Произошла ошибка при применении промокода")
        await state.clear() 