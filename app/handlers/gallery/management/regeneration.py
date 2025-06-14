"""
Управление повторной генерацией изображений
Воссоздание изображений с теми же параметрами
"""
from uuid import UUID

from aiogram.types import CallbackQuery

from app.shared.handlers.base_handler import BaseHandler
from app.core.logger import get_logger
from app.database.models import ImageGeneration, GenerationStatus

logger = get_logger(__name__)


class RegenerationManager(BaseHandler):
    """Менеджер повторной генерации изображений"""
    
    async def regenerate_image(self, callback: CallbackQuery):
        """Повторная генерация изображения с теми же параметрами"""
        
        try:
            # Извлекаем generation_id из callback_data
            generation_id = callback.data.split(":")[1]
            
            # Получаем пользователя
            user = await self.get_user_from_callback(callback, show_error=False)
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return
            
            # Получаем оригинальное изображение
            original_generation = await self._get_generation(UUID(generation_id), user.id)
            if not original_generation:
                await callback.answer("❌ Изображение не найдено", show_alert=True)
                return
            
            # Показываем сообщение о начале генерации
            await callback.answer("🔄 Запущена повторная генерация...")
            
            # Запускаем генерацию
            await self._start_regeneration(callback, original_generation, user.id)
            
        except Exception as e:
            logger.exception(f"Ошибка повторной генерации: {e}")
            await callback.answer("❌ Ошибка запуска генерации", show_alert=True)
    
    async def _get_generation(self, generation_id: UUID, user_id: UUID):
        """Получает оригинальное изображение из БД"""
        
        from app.core.database import get_session
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        async with get_session() as session:
            stmt = (
                select(ImageGeneration)
                .options(selectinload(ImageGeneration.avatar))
                .where(
                    ImageGeneration.id == generation_id,
                    ImageGeneration.user_id == user_id
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def _start_regeneration(self, callback: CallbackQuery, original_generation, user_id: UUID):
        """Запускает процесс повторной генерации с автоматическим мониторингом"""
        
        try:
            # Проверяем баланс пользователя
            from app.core.constants import GENERATION_COST
            if not await self.check_user_balance_for_regeneration(user_id, GENERATION_COST):
                await callback.answer("❌ Недостаточно средств для генерации", show_alert=True)
                return
            
            # Подготавливаем параметры для новой генерации
            generation_params = {
                'prompt': original_generation.final_prompt or original_generation.original_prompt,
                'avatar_id': original_generation.avatar_id,
                'aspect_ratio': getattr(original_generation, 'aspect_ratio', '1:1'),
                'num_images': 1,  # Генерируем одно изображение
                'model': getattr(original_generation, 'model', 'flux-pro'),
                'lora_weights': getattr(original_generation, 'lora_weights', None)
            }
            
            logger.info(f"🔄 Запуск повторной генерации: промпт='{generation_params['prompt'][:50]}...', аватар={original_generation.avatar_id}")
            
            # Получаем аватар для проверки его готовности
            from app.core.di import get_avatar_service
            async with get_avatar_service() as avatar_service:
                avatar = await avatar_service.get_avatar(original_generation.avatar_id)
                if not avatar or avatar.status != "completed":
                    await callback.answer("❌ Аватар не готов к генерации", show_alert=True)
                    return
            
            # Обновляем сообщение на процесс генерации
            from app.shared.utils.telegram_utils import format_prompt_for_display
            initial_message = f"""🔄 <b>Повторная генерация запущена</b>

🎭 <b>Аватар:</b> {original_generation.avatar.name if original_generation.avatar else 'Без названия'}
📝 <b>Промпт:</b> {format_prompt_for_display(generation_params['prompt'], 80)}
📐 <b>Размер:</b> {generation_params['aspect_ratio']}

⏳ <b>Статус:</b> Запуск генерации...
🔄 <b>Прогресс:</b> 0%

💡 <i>Обычно занимает 30-60 секунд</i>"""
            
            # Правильная обработка сообщений с изображениями
            try:
                if callback.message.photo:
                    # Если это сообщение с фото - удаляем и отправляем новое
                    await callback.message.delete()
                    status_message = await callback.message.answer(
                        text=initial_message,
                        parse_mode="HTML"
                    )
                else:
                    # Если это текстовое сообщение - редактируем
                    await callback.message.edit_text(
                        text=initial_message,
                        parse_mode="HTML"
                    )
                    status_message = callback.message
            except Exception as msg_error:
                logger.warning(f"Ошибка обновления сообщения: {msg_error}")
                # Fallback: всегда отправляем новое
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                    
                status_message = await callback.message.answer(
                    text=initial_message,
                    parse_mode="HTML"
                )
            
            # Запускаем генерацию через сервис
            from app.services.generation.generation_service import ImageGenerationService
            generation_service = ImageGenerationService()
            
            new_generation = await generation_service.generate_custom(
                user_id=user_id,
                avatar_id=original_generation.avatar_id,
                custom_prompt=generation_params['prompt'],
                aspect_ratio=generation_params['aspect_ratio'],
                num_images=1
            )
            
            if not new_generation:
                await status_message.edit_text(
                    "❌ <b>Не удалось запустить генерацию</b>\n\n💡 <i>Попробуйте позже</i>",
                    parse_mode="HTML"
                )
                return
            
            # Списываем баланс после успешного создания генерации
            try:
                from app.core.di import get_user_service
                async with get_user_service() as user_service:
                    new_balance = await user_service.remove_coins(user_id, GENERATION_COST)
                    if new_balance is not None:
                        logger.info(f"Списано {GENERATION_COST} монет за повторную генерацию. Новый баланс: {new_balance}")
                    else:
                        logger.warning(f"Не удалось списать баланс за повторную генерацию для пользователя {user_id}")
            except Exception as balance_error:
                logger.exception(f"Ошибка списания баланса: {balance_error}")
                # Генерация уже запущена, поэтому продолжаем
            
            logger.info(f"✅ Повторная генерация создана: {new_generation.id}")
            
            # Запускаем автоматический мониторинг генерации
            await self._monitor_regeneration_progress(
                status_message, 
                new_generation, 
                generation_params['prompt'], 
                original_generation.avatar.name if original_generation.avatar else 'Без названия'
            )
            
        except Exception as e:
            logger.exception(f"Ошибка запуска повторной генерации: {e}")
            
            # Fallback сообщение об ошибке
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Вернуться в галерею", callback_data="gallery_main")
            ]])
            
            try:
                await callback.message.edit_text(
                    text="❌ <b>Ошибка повторной генерации</b>\n\n💡 <i>Попробуйте позже или создайте новое изображение</i>",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            except Exception:
                await callback.message.answer(
                    text="❌ <b>Ошибка повторной генерации</b>\n\n💡 <i>Попробуйте позже или создайте новое изображение</i>",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
    
    async def check_user_balance_for_regeneration(self, user_id: UUID, cost: int) -> bool:
        """Проверяет баланс пользователя для повторной генерации"""
        try:
            from app.core.di import get_user_service
            
            async with get_user_service() as user_service:
                # Получаем текущий баланс пользователя
                current_balance = await user_service.get_user_balance(user_id)
                
                # Проверяем достаточность средств
                has_sufficient_balance = current_balance >= cost
                
                logger.info(f"Проверка баланса пользователя {user_id}: баланс={current_balance}, стоимость={cost}, достаточно={has_sufficient_balance}")
                
                return has_sufficient_balance
                
        except Exception as e:
            logger.exception(f"Ошибка проверки баланса: {e}")
            # В случае ошибки НЕ разрешаем генерацию для безопасности
            return False
    
    async def _monitor_regeneration_progress(self, message, generation, prompt: str, avatar_name: str):
        """Мониторинг прогресса повторной генерации"""
        import asyncio
        from app.shared.utils.telegram_utils import format_prompt_for_display
        
        try:
            max_attempts = 60  # Максимум 3 минуты ожидания
            attempt = 0
            
            while attempt < max_attempts:
                attempt += 1
                
                # Получаем актуальный статус из БД
                updated_generation = await self._get_generation(generation.id, generation.user_id)
                
                if not updated_generation:
                    break
                
                # Обновляем сообщение в зависимости от статуса
                if updated_generation.status == GenerationStatus.COMPLETED:
                    # Генерация завершена успешно
                    await self._show_regeneration_result(message, updated_generation, prompt, avatar_name)
                    return
                    
                elif updated_generation.status == GenerationStatus.FAILED:
                    # Генерация провалилась
                    await self._show_regeneration_error(message, "Генерация завершилась с ошибкой")
                    return
                    
                elif updated_generation.status == GenerationStatus.CANCELLED:
                    # Генерация отменена
                    await self._show_regeneration_error(message, "Генерация была отменена")
                    return
                
                # Обновляем прогресс каждые 3 секунды
                if attempt % 3 == 0:
                    progress = min(90, attempt * 2)  # Эмуляция прогресса до 90%
                    
                    status_text = f"""🔄 <b>Повторная генерация в процессе</b>

🎭 <b>Аватар:</b> {avatar_name}
📝 <b>Промпт:</b> {format_prompt_for_display(prompt, 80)}

⏳ <b>Статус:</b> Генерируется...
🔄 <b>Прогресс:</b> {progress}%

💡 <i>Осталось примерно {max_attempts - attempt} секунд</i>"""
                    
                    try:
                        await message.edit_text(status_text, parse_mode="HTML")
                    except Exception:
                        pass  # Игнорируем ошибки редактирования
                
                await asyncio.sleep(1)  # Ждем 1 секунду перед следующей проверкой
            
            # Таймаут - показываем ошибку
            await self._show_regeneration_error(message, "Превышено время ожидания генерации")
            
        except Exception as e:
            logger.exception(f"Ошибка мониторинга повторной генерации: {e}")
            await self._show_regeneration_error(message, "Ошибка мониторинга генерации")
    
    async def _show_regeneration_result(self, message, generation, prompt: str, avatar_name: str):
        """Показывает результат завершенной повторной генерации"""
        try:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            from aiogram.types import BufferedInputFile
            from app.shared.utils.telegram_utils import format_prompt_for_display
            import aiohttp
            
            # Загружаем изображение
            if generation.result_urls and len(generation.result_urls) > 0:
                image_url = generation.result_urls[0]  # Берем первое изображение
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            
                            # Создаем клавиатуру для результата
                            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                                [
                                    InlineKeyboardButton(text="🔄 Повторить еще раз", callback_data=f"gallery_regenerate:{generation.id}"),
                                    InlineKeyboardButton(text="🖼️ В галерею", callback_data="gallery_main")
                                ],
                                [
                                    InlineKeyboardButton(text="🎨 Новая генерация", callback_data="generation_menu"),
                                    InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
                                ]
                            ])
                            
                            caption = f"""✅ <b>Повторная генерация завершена!</b>

🎭 <b>Аватар:</b> {avatar_name}
📝 <b>Промпт:</b> {format_prompt_for_display(prompt, 100)}
🆔 <b>ID:</b> {str(generation.id)[:8]}...

🎉 <b>Изображение готово!</b>"""
                            
                            # Удаляем старое сообщение и отправляем новое с фото
                            try:
                                await message.delete()
                            except Exception:
                                pass
                            
                            await message.answer_photo(
                                photo=BufferedInputFile(image_data, filename=f"regeneration_{generation.id}.jpg"),
                                caption=caption,
                                reply_markup=keyboard,
                                parse_mode="HTML"
                            )
                            
                            logger.info(f"✅ Результат повторной генерации показан: {generation.id}")
                            return
            
            # Fallback без изображения
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🖼️ В галерею", callback_data="gallery_main")]
            ])
            
            await message.edit_text(
                f"✅ <b>Повторная генерация завершена!</b>\n\n🖼️ Результат доступен в галерее",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.exception(f"Ошибка показа результата повторной генерации: {e}")
            await self._show_regeneration_error(message, "Ошибка отображения результата")
    
    async def _show_regeneration_error(self, message, error_text: str):
        """Показывает ошибку повторной генерации"""
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="generation_menu"),
                InlineKeyboardButton(text="🖼️ В галерею", callback_data="gallery_main")
            ],
            [
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
            ]
        ])
        
        try:
            await message.edit_text(
                f"❌ <b>Ошибка генерации</b>\n\n💭 {error_text}\n\n💡 <i>Попробуйте еще раз или обратитесь в поддержку</i>",
                reply_markup=keyboard,
                parse_mode="HTML"
            ) 
        except Exception as e:
            logger.exception(f"Ошибка показа ошибки повторной генерации: {e}") 