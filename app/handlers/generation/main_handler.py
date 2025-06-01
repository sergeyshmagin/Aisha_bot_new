"""
Главный обработчик для системы генерации изображений
"""
from typing import List
from uuid import UUID

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.exceptions import TelegramBadRequest

from app.core.di import get_user_service, get_avatar_service
from app.core.logger import get_logger
from app.services.generation.style_service import StyleService
from app.services.generation.generation_service import ImageGenerationService, GENERATION_COST
from app.database.models.generation import StyleCategory, StyleTemplate, ImageGeneration, GenerationStatus
from app.database.models import AvatarStatus
from .states import GenerationStates

logger = get_logger(__name__)
router = Router()


class GenerationMainHandler:
    """Главный обработчик генерации изображений"""
    
    def __init__(self):
        self.style_service = StyleService()
        self.generation_service = ImageGenerationService()
    
    async def show_generation_menu(self, callback: CallbackQuery):
        """Показывает главное меню генерации"""
        
        user_telegram_id = callback.from_user.id
        
        try:
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
                
                # Получаем баланс пользователя
                user_balance = await user_service.get_user_balance(user.id)
            
            # Получаем основной аватар
            async with get_avatar_service() as avatar_service:
                main_avatar = await avatar_service.get_main_avatar(user.id)
                if not main_avatar:
                    await callback.answer("❌ У вас нет основного аватара. Создайте аватар сначала!", show_alert=True)
                    return
                
                # Проверяем статус аватара
                if main_avatar.status != AvatarStatus.COMPLETED:
                    await callback.answer("❌ Ваш аватар еще не готов. Дождитесь завершения обучения!", show_alert=True)
                    return
            
            # Получаем популярные категории (заглушка)
            popular_categories = []
            
            # Получаем избранные шаблоны (заглушка)
            favorites = []
            
            # Формируем текст
            avatar_type_text = "Портретный" if main_avatar.training_type.value == "portrait" else "Стилевой"
            
            text = f"""🎨 <b>Создание изображения</b>
👤 Основной аватар: {main_avatar.name} ({avatar_type_text})
💰 Баланс: {user_balance:.0f} единиц
💎 Стоимость: {GENERATION_COST:.0f} единиц за изображение

🔥 <b>Популярные стили</b>"""
            
            # Формируем клавиатуру
            keyboard = self._build_generation_menu_keyboard(
                popular_categories, 
                favorites, 
                main_avatar.id,
                user_balance
            )
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            logger.info(f"Показано меню генерации для пользователя {user_telegram_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка показа меню генерации: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    def _build_generation_menu_keyboard(
        self, 
        popular_categories: List[StyleCategory],
        favorites: List[StyleTemplate],
        avatar_id: UUID,
        user_balance: float
    ) -> InlineKeyboardMarkup:
        """Строит клавиатуру главного меню генерации"""
        
        buttons = []
        
        # Проверяем, достаточно ли баланса
        has_balance = user_balance >= GENERATION_COST
        
        if has_balance:
            # Свой промпт
            buttons.append([
                InlineKeyboardButton(
                    text="📝 Свой промпт",
                    callback_data=f"gen_custom:{avatar_id}"
                )
            ])
        else:
            # Недостаточно баланса
            buttons.append([
                InlineKeyboardButton(
                    text="💰 Пополнить баланс",
                    callback_data="balance_topup"
                )
            ])
        
        # Сменить аватар
        buttons.append([
            InlineKeyboardButton(
                text="🔄 Сменить аватар",
                callback_data="gen_change_avatar"
            )
        ])
        
        # Моя галерея
        buttons.append([
            InlineKeyboardButton(
                text="🖼️ Моя галерея",
                callback_data="my_gallery"
            )
        ])
        
        # Назад
        buttons.append([
            InlineKeyboardButton(
                text="🔙 Главное меню",
                callback_data="main_menu"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    async def show_custom_prompt_input(self, callback: CallbackQuery, state: FSMContext):
        """Показывает форму для ввода кастомного промпта"""
        
        try:
            # Извлекаем avatar_id из callback_data (gen_custom:{avatar_id})
            data_parts = callback.data.split(":")
            avatar_id = UUID(data_parts[1])
            
            user_telegram_id = callback.from_user.id
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Получаем аватар
            async with get_avatar_service() as avatar_service:
                avatar = await avatar_service.get_avatar(avatar_id)
                if not avatar or avatar.user_id != user.id:
                    await callback.answer("❌ Аватар не найден", show_alert=True)
                    return
                
                # Проверяем статус аватара
                if avatar.status != AvatarStatus.COMPLETED:
                    await callback.answer("❌ Аватар еще не готов к генерации!", show_alert=True)
                    return
            
            # Показываем форму для ввода промпта
            text = f"""📝 <b>Свой промпт</b>

🎭 <b>Аватар:</b> {avatar.name}
✨ <b>Тип:</b> {avatar.training_type.value.title()}

📋 <b>Введите описание изображения:</b>

🤖 <b>НОВАЯ Продвинутая обработка промптов:</b>
• 🌐 Автоматический перевод с русского на английский
• 🎯 Создание детальных профессиональных описаний
• 📸 Добавление технических фотографических терминов
• 🎨 Оптимизация композиции, освещения и качества
• ⚡ Специализация для типа аватара (портрет/стиль)

💡 <b>Примеры простых промптов (превратятся в детальные!):</b>
• "деловой мужчина в костюме" → детальный портрет со студийным освещением
• "Superman costume" → профессиональное описание с технической композицией
• "кофейня, очки" → полное описание сцены с параметрами камеры
• "космонавт в шлеме" → художественное описание с атмосферой

✍️ <b>Введите ЛЮБОЙ промпт (даже простой):</b>
Система сама создаст профессиональное описание как у фотографа!"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад к стилям",
                        callback_data="generation_menu"
                    )
                ]
            ])
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            # Сохраняем avatar_id в состоянии для дальнейшей обработки
            await state.update_data(avatar_id=str(avatar_id))
            await state.set_state(GenerationStates.waiting_for_custom_prompt)
            
            logger.info(f"Пользователь {user_telegram_id} начал ввод кастомного промпта для аватара {avatar_id}")
            
        except ValueError as e:
            await callback.answer("❌ Неверный формат данных", show_alert=True)
        except Exception as e:
            logger.exception(f"Ошибка показа формы кастомного промпта: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def process_custom_prompt(self, message: Message, state: FSMContext):
        """Обрабатывает введенный пользователем кастомный промпт"""
        
        try:
            # Получаем данные из состояния
            data = await state.get_data()
            avatar_id = data.get("avatar_id")
            
            if not avatar_id:
                await message.reply("❌ Ошибка: не найдены данные аватара. Попробуйте еще раз.")
                await state.clear()
                return
            
            custom_prompt = message.text
            user_telegram_id = message.from_user.id
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await message.reply("❌ Пользователь не найден")
                    await state.clear()
                    return
            
            # Получаем аватар ДО показа сообщения обработки
            async with get_avatar_service() as avatar_service:
                avatar = await avatar_service.get_avatar(UUID(avatar_id))
                if not avatar or avatar.user_id != user.id:
                    await message.reply("❌ Аватар не найден")
                    await state.clear()
                    return
                
                # Проверяем статус аватара
                if avatar.status != AvatarStatus.COMPLETED:
                    await message.reply("❌ Аватар еще не готов к генерации!")
                    await state.clear()
                    return
            
            # Показываем простое сообщение о генерации
            processing_message = await message.reply(
                f"""🎨 <b>Создаю изображение...</b>

📝 <b>Ваш промпт:</b> {custom_prompt[:60]}{'...' if len(custom_prompt) > 60 else ''}
🎭 <b>Аватар:</b> {avatar.name}
⚡ <b>Модель:</b> FLUX 1.1 Ultra (максимальный фотореализм)

⏳ <b>Генерация запущена...</b>
💡 Обычно занимает 30-60 секунд""",
                parse_mode="HTML"
            )
            
            # Запускаем генерацию
            generation = await self.generation_service.generate_custom(
                user_id=user.id,
                avatar_id=UUID(avatar_id),
                custom_prompt=custom_prompt,
                quality_preset="photorealistic_max",
                aspect_ratio="1:1",
                num_images=1
            )
            
            # Сразу запускаем мониторинг статуса
            await self._monitor_generation_status(processing_message, generation, custom_prompt, avatar.name)
            
            await state.clear()
            logger.info(f"Запущена кастомная генерация {generation.id} для пользователя {user_telegram_id}")
            
        except ValueError as e:
            # Ошибки валидации (недостаточно баланса и т.д.)
            await message.reply(f"❌ {str(e)}")
            await state.clear()
            
        except Exception as e:
            logger.exception(f"Ошибка обработки кастомного промпта: {e}")
            await message.reply("❌ Произошла ошибка при запуске генерации")
            await state.clear()

    async def _monitor_generation_status(self, message, generation, original_prompt: str, avatar_name: str):
        """Мониторит статус генерации и показывает результат автоматически"""
        
        import asyncio
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
                    await self._show_final_result(message, current_generation, original_prompt, avatar_name)
                    return
                    
                elif current_generation.status == GenerationStatus.FAILED:
                    # Генерация провалилась - показываем ошибку
                    await self._show_final_error(message, current_generation)
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

    async def _show_final_result(self, message, generation, original_prompt: str, avatar_name: str):
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

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Создать еще",
                        callback_data="generation_menu"
                    ),
                    InlineKeyboardButton(
                        text="🖼️ Галерея",
                        callback_data="my_gallery"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📝 Показать полный промпт",
                        callback_data=f"show_prompt:{generation.id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏠 Главное меню",
                        callback_data="main_menu"
                    )
                ]
            ])
            
            # Отправляем изображение
            result_url = generation.result_urls[0]
            await message.reply_photo(
                photo=result_url,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            # Удаляем сообщение о генерации
            await message.delete()
            
        except Exception as e:
            logger.exception(f"Ошибка показа финального результата: {e}")
            await message.edit_text(
                "❌ Ошибка при отображении результата",
                parse_mode="HTML"
            )

    async def _show_final_error(self, message, generation):
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
        """Показывает полный детальный промпт генерации"""
        
        try:
            # Извлекаем generation_id из callback_data (show_prompt:{generation_id})
            data_parts = callback.data.split(":")
            generation_id = UUID(data_parts[1])
            
            user_telegram_id = callback.from_user.id
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Получаем генерацию
            generation = await self.generation_service.get_generation_by_id(generation_id)
            if not generation:
                await callback.answer("❌ Генерация не найдена", show_alert=True)
                return
            
            # Проверяем принадлежность генерации пользователю
            if generation.user_id != user.id:
                await callback.answer("❌ Доступ запрещен", show_alert=True)
                return
            
            # Показываем полный промпт
            text = f"""📝 <b>Детальный профессиональный промпт</b>

🎭 <b>Аватар:</b> {generation.avatar.name}
📊 <b>ID генерации:</b> {str(generation.id)[:8]}...

📋 <b>Ваш простой промпт:</b>
<code>{generation.original_prompt}</code>

🎯 <b>Детальный промпт (создан GPT-4o):</b>
<pre>{generation.final_prompt}</pre>

✨ <b>Анализ качества промпта:</b>
• Длина: {len(generation.final_prompt)} символов
• Технические детали: ✅ Добавлены
• Композиция: ✅ Описана детально
• Освещение: ✅ Профессиональные параметры
• Качество: ✅ Максимальный фотореализм

💡 <b>Как это улучшает генерацию:</b>
Детальный промпт дает AI точные инструкции о композиции, освещении, технических параметрах и качестве, что значительно улучшает результат генерации."""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Обновить статус",
                        callback_data=f"gen_status:{generation.id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 К генерации",
                        callback_data="generation_menu"
                    )
                ]
            ])
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            await callback.answer()
            
        except ValueError as e:
            await callback.answer("❌ Неверный формат данных", show_alert=True)
        except Exception as e:
            logger.exception(f"Ошибка показа полного промпта: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)


# Создаем экземпляр обработчика
generation_handler = GenerationMainHandler()

# Регистрируем обработчики
@router.callback_query(F.data == "generation_menu")
async def handle_generation_menu(callback: CallbackQuery):
    """Обработчик главного меню генерации"""
    await generation_handler.show_generation_menu(callback)

@router.callback_query(F.data.startswith("gen_custom:"))
async def handle_custom_prompt_request(callback: CallbackQuery, state: FSMContext):
    """Обработчик запроса кастомного промпта"""
    await generation_handler.show_custom_prompt_input(callback, state)

@router.message(F.text, StateFilter(GenerationStates.waiting_for_custom_prompt))
async def handle_custom_prompt_text(message: Message, state: FSMContext):
    """Обработчик текста кастомного промпта"""
    await generation_handler.process_custom_prompt(message, state)

@router.callback_query(F.data.startswith("show_prompt:"))
async def handle_show_full_prompt(callback: CallbackQuery):
    """Обработчик показа полного промпта"""
    await generation_handler.show_full_prompt(callback)

# Заглушки для будущих функций
@router.callback_query(F.data.startswith("gen_template:"))
async def handle_template_details(callback: CallbackQuery):
    """Обработчик деталей шаблона"""
    await callback.answer("🚧 Шаблоны стилей в разработке", show_alert=True)

@router.callback_query(F.data.startswith("gen_category:"))
async def show_category(callback: CallbackQuery):
    """Обработчик показа категории"""
    await callback.answer("🚧 Категории стилей в разработке", show_alert=True)

@router.callback_query(F.data == "gen_all_categories")
async def show_all_categories(callback: CallbackQuery):
    """Обработчик показа всех категорий"""
    await callback.answer("🚧 Каталог стилей в разработке", show_alert=True)

@router.callback_query(F.data == "gen_favorites")
async def show_favorites(callback: CallbackQuery):
    """Обработчик показа избранных"""
    await callback.answer("🚧 Избранные стили в разработке", show_alert=True)

@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    """Обработчик пустых callback'ов"""
    await callback.answer() 