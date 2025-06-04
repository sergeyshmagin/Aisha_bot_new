"""
Мониторинг и управление процессом генерации изображений
"""
import asyncio
from uuid import UUID

from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext

from app.shared.handlers.base_handler import BaseHandler
from app.core.logger import get_logger
from app.services.generation.generation_service import ImageGenerationService, GENERATION_COST
from app.services.user_settings import UserSettingsService
from app.database.models.generation import GenerationStatus
from .keyboards import build_generation_result_keyboard

logger = get_logger(__name__)


class GenerationMonitor(BaseHandler):
    """Мониторинг и управление процессом генерации"""
    
    def __init__(self):
        self.generation_service = ImageGenerationService()
        self.user_settings_service = UserSettingsService()
    
    async def start_generation(
        self, 
        message: Message, 
        state: FSMContext, 
        aspect_ratio: str,
        is_photo_analysis: bool = False
    ):
        """Запускает процесс генерации изображения"""
        
        try:
            # Получаем данные из состояния
            data = await state.get_data()
            avatar_id = UUID(data.get("avatar_id"))
            user_id = UUID(data.get("user_id"))
            custom_prompt = data.get("custom_prompt")
            avatar_name = data.get("avatar_name")
            
            # Получаем пользователя
            user = await self.get_user_from_message(message, show_error=False)
            if not user or str(user.id) != str(user_id):
                await message.reply("❌ Ошибка авторизации")
                await self.safe_clear_state(state)
                return
            
            # Получаем аватар
            avatar = await self.get_avatar_by_id(
                avatar_id, 
                user_id=user.id,
                message=message,
                show_error=False
            )
            if not avatar:
                await self.safe_clear_state(state)
                return
            
            # Проверяем статус аватара
            if avatar.status != "completed":
                await message.reply("❌ Аватар еще не готов к генерации!")
                await self.safe_clear_state(state)
                return
            
            # Проверяем баланс
            if not await self.check_user_balance(
                user, 
                GENERATION_COST, 
                message=message
            ):
                await self.safe_clear_state(state)
                return
            
            # Показываем сообщение о начале генерации
            generation_message = await message.reply(
                f"""🎨 <b>Запускаю генерацию...</b>

🎭 <b>Аватар:</b> {avatar_name}
📝 <b>Промпт:</b> {custom_prompt[:60]}{'...' if len(custom_prompt) > 60 else ''}
📐 <b>Формат:</b> {aspect_ratio}
⚡ <b>Модель:</b> FLUX 1.1 Ultra

⏳ <b>Процесс:</b>
• 💰 Списание баланса...
• 🚀 Отправка в очередь...
• 🎨 Генерация изображения...

💡 Обычно занимает 30-60 секунд""",
                parse_mode="HTML"
            )
            
            # Запускаем генерацию
            generation = await self.generation_service.generate_custom(
                user_id=user.id,
                avatar_id=avatar_id,
                custom_prompt=custom_prompt,
                aspect_ratio=aspect_ratio
            )
            
            if not generation:
                await generation_message.edit_text(
                    "❌ Не удалось запустить генерацию. Попробуйте еще раз.",
                    parse_mode="HTML"
                )
                await self.safe_clear_state(state)
                return
            
            # Очищаем состояние
            await self.safe_clear_state(state)
            
            # Обновляем сообщение
            await generation_message.edit_text(
                f"""✅ <b>Генерация запущена!</b>

🎭 <b>Аватар:</b> {avatar_name}
📝 <b>Промпт:</b> {custom_prompt[:60]}{'...' if len(custom_prompt) > 60 else ''}
📐 <b>Формат:</b> {aspect_ratio}
🆔 <b>ID:</b> {str(generation.id)[:8]}...

⏳ <b>Статус:</b> В очереди
🔄 <b>Мониторинг:</b> Автоматический

💡 Результат появится здесь автоматически""",
                parse_mode="HTML"
            )
            
            # Запускаем мониторинг
            await self.monitor_generation_status(
                generation_message, 
                generation, 
                custom_prompt, 
                avatar_name
            )
            
        except Exception as e:
            logger.exception(f"Ошибка запуска генерации: {e}")
            await message.reply("❌ Произошла ошибка при запуске генерации")
            await self.safe_clear_state(state)
    
    async def start_generation_from_callback(
        self, 
        callback: CallbackQuery, 
        state: FSMContext, 
        aspect_ratio: str
    ):
        """Запускает генерацию из callback (для кнопок)"""
        
        try:
            # Получаем данные из состояния
            data = await state.get_data()
            avatar_id = UUID(data.get("avatar_id"))
            user_id = UUID(data.get("user_id"))
            custom_prompt = data.get("custom_prompt")
            avatar_name = data.get("avatar_name")
            
            # Получаем пользователя
            user = await self.get_user_from_callback(callback, show_error=False)
            if not user or str(user.id) != str(user_id):
                await callback.answer("❌ Ошибка авторизации", show_alert=True)
                await self.safe_clear_state(state)
                return
            
            # Получаем аватар
            avatar = await self.get_avatar_by_id(
                avatar_id, 
                user_id=user.id,
                callback=callback,
                show_error=False
            )
            if not avatar:
                await self.safe_clear_state(state)
                return
            
            # Проверяем статус аватара
            if avatar.status != "completed":
                await callback.answer("❌ Аватар еще не готов к генерации!", show_alert=True)
                await self.safe_clear_state(state)
                return
            
            # Проверяем баланс
            if not await self.check_user_balance(
                user, 
                GENERATION_COST, 
                callback=callback
            ):
                await self.safe_clear_state(state)
                return
            
            # Обновляем сообщение о начале генерации
            await callback.message.edit_text(
                f"""🎨 <b>Запускаю генерацию...</b>

🎭 <b>Аватар:</b> {avatar_name}
📝 <b>Промпт:</b> {custom_prompt[:60]}{'...' if len(custom_prompt) > 60 else ''}
📐 <b>Формат:</b> {aspect_ratio}
⚡ <b>Модель:</b> FLUX 1.1 Ultra

⏳ <b>Процесс:</b>
• 💰 Списание баланса...
• 🚀 Отправка в очередь...
• 🎨 Генерация изображения...

💡 Обычно занимает 30-60 секунд""",
                parse_mode="HTML"
            )
            
            # Запускаем генерацию
            generation = await self.generation_service.generate_custom(
                user_id=user.id,
                avatar_id=avatar_id,
                custom_prompt=custom_prompt,
                aspect_ratio=aspect_ratio
            )
            
            if not generation:
                await callback.message.edit_text(
                    "❌ Не удалось запустить генерацию. Попробуйте еще раз.",
                    parse_mode="HTML"
                )
                await self.safe_clear_state(state)
                return
            
            # Очищаем состояние
            await self.safe_clear_state(state)
            
            # Обновляем сообщение
            await callback.message.edit_text(
                f"""✅ <b>Генерация запущена!</b>

🎭 <b>Аватар:</b> {avatar_name}
📝 <b>Промпт:</b> {custom_prompt[:60]}{'...' if len(custom_prompt) > 60 else ''}
📐 <b>Формат:</b> {aspect_ratio}
🆔 <b>ID:</b> {str(generation.id)[:8]}...

⏳ <b>Статус:</b> В очереди
🔄 <b>Мониторинг:</b> Автоматический

💡 Результат появится здесь автоматически""",
                parse_mode="HTML"
            )
            
            # Запускаем мониторинг
            await self.monitor_generation_status(
                callback.message, 
                generation, 
                custom_prompt, 
                avatar_name
            )
            
        except Exception as e:
            logger.exception(f"Ошибка запуска генерации из callback: {e}")
            await callback.answer("❌ Произошла ошибка при запуске генерации", show_alert=True)
            await self.safe_clear_state(state)
    
    async def monitor_generation_status(self, message, generation, original_prompt: str, avatar_name: str):
        """Мониторит статус генерации и показывает результат автоматически"""
        
        max_attempts = 120  # 2 минуты максимум (по 1 секунде)
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Получаем актуальный статус
                current_generation = await self.generation_service.get_generation_by_id(generation.id)
                
                if not current_generation:
                    await message.edit_text(
                        "❌ Ошибка: генерация не найдена",
                        parse_mode="HTML"
                    )
                    return
                
                if current_generation.status == GenerationStatus.COMPLETED:
                    # Генерация завершена - показываем результат
                    await self.show_final_result(message, current_generation, original_prompt, avatar_name)
                    return
                    
                elif current_generation.status == GenerationStatus.FAILED:
                    # Генерация провалилась - показываем ошибку
                    await self.show_final_error(message, current_generation)
                    return
                
                # Генерация еще идет - ждем секунду
                await asyncio.sleep(1)
                attempt += 1
                
            except Exception as e:
                logger.exception(f"Ошибка мониторинга генерации: {e}")
                await asyncio.sleep(1)
                attempt += 1
        
        # Таймаут - показываем сообщение
        await message.edit_text(
            f"""⏰ <b>Генерация занимает больше времени чем обычно</b>

📝 <b>Промпт:</b> {original_prompt[:60]}{'...' if len(original_prompt) > 60 else ''}
🎭 <b>Аватар:</b> {avatar_name}

💡 Проверьте результат через несколько минут в галерее""",
            parse_mode="HTML"
        )

    async def show_final_result(self, message, generation, original_prompt: str, avatar_name: str):
        """Показывает финальный результат генерации"""
        
        try:
            if not generation.result_urls or len(generation.result_urls) == 0:
                await message.edit_text(
                    "❌ Результат генерации недоступен",
                    parse_mode="HTML"
                )
                return
            
            duration = (generation.completed_at - generation.created_at).total_seconds() if generation.completed_at else 0
            
            text = f"""✨ <b>Изображение готово!</b>

📝 <b>Промпт:</b> {original_prompt[:60]}{'...' if len(original_prompt) > 60 else ''}
🎭 <b>Аватар:</b> {avatar_name}
⚡ <b>Качество:</b> Максимальный фотореализм
⏱️ <b>Время:</b> {duration:.1f}с

🎉 Ваше изображение создано!"""

            keyboard = build_generation_result_keyboard(generation.id)
            
            # Отправляем изображение
            result_url = generation.result_urls[0]
            
            try:
                # Попытка 1: Отправить через URL
                await message.reply_photo(
                    photo=result_url,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                
                # Удаляем сообщение о генерации только при успешной отправке
                await message.delete()
                
            except Exception as telegram_error:
                logger.warning(f"Ошибка отправки изображения по URL: {telegram_error}")
                
                try:
                    # Попытка 2: Скачать изображение и отправить как файл
                    import aiohttp
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(result_url) as response:
                            if response.status == 200:
                                image_data = await response.read()
                                
                                # Определяем расширение файла
                                content_type = response.headers.get('content-type', 'image/jpeg')
                                extension = '.jpg' if 'jpeg' in content_type else '.png' if 'png' in content_type else '.jpg'
                                
                                photo_input = BufferedInputFile(
                                    image_data, 
                                    filename=f"generated_image_{generation.id}{extension}"
                                )
                                
                                await message.reply_photo(
                                    photo=photo_input,
                                    caption=text,
                                    reply_markup=keyboard,
                                    parse_mode="HTML"
                                )
                                
                                # Удаляем сообщение о генерации
                                await message.delete()
                                
                                logger.info(f"Изображение успешно отправлено как файл для генерации {generation.id}")
                                
                            else:
                                raise Exception(f"HTTP {response.status} при скачивании изображения")
                                
                except Exception as download_error:
                    logger.exception(f"Ошибка скачивания и отправки изображения: {download_error}")
                    
                    # Попытка 3: Показать результат без изображения
                    await message.edit_text(
                        text + "\n\n❌ <b>Изображение временно недоступно</b>\n💡 Попробуйте открыть галерею через несколько минут",
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
            
        except Exception as e:
            logger.exception(f"Критическая ошибка показа финального результата: {e}")
            await message.edit_text(
                "❌ Ошибка при отображении результата. Попробуйте открыть галерею.",
                parse_mode="HTML"
            )

    async def show_final_error(self, message, generation):
        """Показывает финальную ошибку генерации"""
        
        error_message = generation.error_message or "Произошла неизвестная ошибка"
        
        text = f"""❌ <b>Ошибка генерации</b>

🚫 <b>Причина:</b> {error_message[:100]}{'...' if len(error_message) > 100 else ''}

💰 <b>Ваш баланс восстановлен</b>

💡 <b>Что делать:</b>
• Попробуйте еще раз
• Измените промпт  
• Обратитесь в поддержку"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Попробовать снова",
                    callback_data="generation_menu"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="main_menu"
                )
            ]
        ])
        
        await message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    async def show_full_prompt(self, callback: CallbackQuery):
        """Показывает полный промпт генерации"""
        
        try:
            # Извлекаем generation_id из callback_data (show_prompt:{generation_id})
            data_parts = callback.data.split(":")
            generation_id = UUID(data_parts[1])
            
            # Получаем генерацию
            generation = await self.generation_service.get_generation_by_id(generation_id)
            if not generation:
                await callback.answer("❌ Генерация не найдена", show_alert=True)
                return
            
            # Проверяем принадлежность пользователю
            user = await self.get_user_from_callback(callback)
            if not user or generation.user_id != user.id:
                await callback.answer("❌ Генерация не принадлежит вам", show_alert=True)
                return
            
            # Показываем полный промпт
            text = f"""📝 <b>Полный промпт генерации</b>

🆔 <b>ID:</b> {str(generation.id)[:8]}...
📅 <b>Дата:</b> {generation.created_at.strftime('%d.%m.%Y %H:%M')}

<b>Промпт:</b>
<code>{generation.final_prompt}</code>

📐 <b>Формат:</b> {generation.aspect_ratio}
⚡ <b>Модель:</b> FLUX 1.1 Ultra"""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="noop"
                    )
                ]
            ])
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.exception(f"Ошибка показа полного промпта: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True) 