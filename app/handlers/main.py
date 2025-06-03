"""
Основные обработчики бота
"""
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("debug_avatars"))
async def debug_avatars_command(message: Message):
    """Диагностическая команда для проверки статуса аватаров"""
    await _debug_avatars_logic(message)

@router.message(Command("debug_avatar"))
async def debug_avatar_command(message: Message):
    """Альтернативная диагностическая команда (без 's')"""
    await _debug_avatars_logic(message)

async def _debug_avatars_logic(message: Message):
    """Общая логика диагностики аватаров"""
    try:
        from app.core.di import get_user_service, get_avatar_service
        
        user_telegram_id = str(message.from_user.id)
        
        async with get_user_service() as user_service:
            user = await user_service.get_user_by_telegram_id(user_telegram_id)
            if not user:
                await message.reply("❌ Пользователь не найден в базе данных")
                return
        
        async with get_avatar_service() as avatar_service:
            avatars = await avatar_service.get_user_avatars(user.id)
            
            if not avatars:
                await message.reply("📭 У вас нет аватаров")
                return
            
            debug_text = f"🔍 **Диагностика аватаров** (User ID: `{str(user.id)[:8]}...`)\n\n"
            
            for i, avatar in enumerate(avatars, 1):
                # Определяем готовность к генерации
                ready_for_generation = avatar.status.value == "completed"
                has_training_data = bool(avatar.diffusers_lora_file_url or avatar.finetune_id)
                
                status_icon = {
                    "draft": "📝",
                    "uploading": "📤", 
                    "ready": "⏳",
                    "training": "🔄",
                    "completed": "✅",
                    "error": "❌",
                    "cancelled": "⏹️"
                }.get(avatar.status.value, "❓")
                
                debug_text += f"**{i}. {avatar.name}** {status_icon}\n"
                debug_text += f"   • Статус: `{avatar.status.value}`\n"
                debug_text += f"   • Тип: `{avatar.training_type.value}`\n"
                debug_text += f"   • Готов к генерации: {'✅' if ready_for_generation else '❌'}\n"
                debug_text += f"   • Имеет обученную модель: {'✅' if has_training_data else '❌'}\n"
                
                if avatar.diffusers_lora_file_url:
                    debug_text += f"   • LoRA файл: ✅\n"
                if avatar.finetune_id:
                    debug_text += f"   • Finetune ID: `{avatar.finetune_id}`\n"
                if avatar.fal_request_id:
                    debug_text += f"   • Request ID: `{avatar.fal_request_id[:8]}...`\n"
                
                debug_text += f"   • Прогресс: {avatar.training_progress}%\n"
                debug_text += f"   • Основной: {'✅' if avatar.is_main else '❌'}\n"
                debug_text += f"   • Создан: {avatar.created_at.strftime('%d.%m %H:%M') if avatar.created_at else 'N/A'}\n\n"
            
            # Рекомендации
            ready_avatars = [a for a in avatars if a.status.value == "completed"]
            if ready_avatars:
                debug_text += f"🎯 **Готово к генерации:** {len(ready_avatars)} из {len(avatars)}\n"
                debug_text += f"💡 Используйте команду /generate для создания изображений"
            else:
                debug_text += "⚠️ **Нет аватаров готовых к генерации**\n"
                debug_text += "💡 Создайте аватар или дождитесь завершения обучения"
            
            await message.reply(debug_text, parse_mode="Markdown")
            
    except Exception as e:
        logger.exception(f"Ошибка команды debug_avatars: {e}")
        await message.reply(f"❌ Ошибка диагностики: {str(e)}") 