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
from app.services.generation.image_analysis_service import ImageAnalysisService
from app.services.user_settings import UserSettingsService
from app.database.models.generation import StyleCategory, StyleTemplate, ImageGeneration, GenerationStatus
from app.database.models import AvatarStatus, UserSettings
from .states import GenerationStates
from app.shared.utils.telegram_utils import safe_edit_callback_message

logger = get_logger(__name__)
router = Router()


class GenerationMainHandler:
    """Главный обработчик генерации изображений"""
    
    def __init__(self):
        self.style_service = StyleService()
        self.generation_service = ImageGenerationService()
        self.image_analysis_service = ImageAnalysisService()
        self.user_settings_service = UserSettingsService()
    
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
            
            # Используем безопасное редактирование
            success = await safe_edit_callback_message(
                callback=callback,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            if success:
                logger.info(f"Показано меню генерации для пользователя {user_telegram_id}")
            else:
                logger.info(f"Меню генерации уже показано пользователю {user_telegram_id}")
            
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
            # Два варианта создания промпта в одной строке
            buttons.append([
                InlineKeyboardButton(
                    text="📝 Свой промпт",
                    callback_data=f"gen_custom:{avatar_id}"
                ),
                InlineKeyboardButton(
                    text="📸 Промпт по фото",
                    callback_data=f"gen_photo:{avatar_id}"
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

🎯 <b>НОВАЯ система максимального фотореализма:</b>
• 🌐 Автоматический перевод с русского на английский
• 📸 Создание ЕСТЕСТВЕННЫХ фотореалистичных изображений
• ✨ Реалистичные текстуры кожи и натуральная щетина
• 🎨 Поддержка полного роста и художественной фотографии
• ⚡ Борьба с "пластиковым" эффектом

💡 <b>Поддерживаемые типы кадров:</b>
• "портрет в офисе" → деловой портрет в окружении
• "полный рост" → художественное фото в полный рост  
• "casual фото" → естественная фотография в жизни
• "Superman costume полный рост" → персонаж в полный рост

✨ <b>Преимущества новой системы:</b>
• Естественные текстуры кожи с порами
• Реалистичная щетина без артефактов
• Натуральное освещение и тени
• Максимальная фотореалистичность

✍️ <b>Введите ЛЮБОЙ промпт:</b>
Система создаст фотореалистичное описание для FLUX Pro!"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад к стилям",
                        callback_data="generation_menu"
                    )
                ]
            ])
            
            # Используем безопасное редактирование
            success = await safe_edit_callback_message(
                callback=callback,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            # Сохраняем avatar_id в состоянии для дальнейшей обработки
            await state.update_data(avatar_id=str(avatar_id))
            await state.set_state(GenerationStates.waiting_for_custom_prompt)
            
            if success:
                logger.info(f"Пользователь {user_telegram_id} начал ввод кастомного промпта для аватара {avatar_id}")
            else:
                logger.info(f"Форма кастомного промпта уже показана пользователю {user_telegram_id}")
            
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
            
            # Проверяем настройки пользователя - быстрый режим или выбор размера
            user_settings = await self.user_settings_service.get_user_settings(user.id)
            quick_mode = user_settings.quick_generation_mode if user_settings else False
            
            # Сохраняем промпт в состоянии
            await state.update_data(
                avatar_id=str(avatar_id),
                custom_prompt=custom_prompt,
                avatar_name=avatar.name
            )
            
            if quick_mode:
                # Быстрый режим - сразу запускаем генерацию с настройками по умолчанию
                default_aspect_ratio = user_settings.default_aspect_ratio if user_settings else "1:1"
                await self._start_generation(message, state, default_aspect_ratio)
            else:
                # Обычный режим - показываем выбор размера
                await self.show_aspect_ratio_selection(message, state)
            
        except ValueError as e:
            # Ошибки валидации (недостаточно баланса и т.д.)
            await message.reply(f"❌ {str(e)}")
            await state.clear()
            
        except Exception as e:
            logger.exception(f"Ошибка обработки кастомного промпта: {e}")
            await message.reply("❌ Произошла ошибка при запуске генерации")
            await state.clear()
    
    async def show_aspect_ratio_selection(self, message: Message, state: FSMContext):
        """Показывает выбор соотношения сторон изображения"""
        
        try:
            data = await state.get_data()
            custom_prompt = data.get("custom_prompt", "")
            avatar_name = data.get("avatar_name", "")
            
            # Получаем настройки пользователя для дефолтного выбора
            user_telegram_id = message.from_user.id
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                default_ratio = "1:1"
                if user:
                    default_ratio = await self.user_settings_service.get_default_aspect_ratio(user.id)
            
            # Получаем доступные варианты
            aspect_options = UserSettings.get_aspect_ratio_options()
            
            # ✅ БЕЗОПАСНАЯ ОБРАБОТКА ДАННЫХ АНАЛИЗА
            analysis_text = str(analysis_result.get('analysis', 'Анализ не выполнен'))
            analysis_preview = analysis_text[:100] + ('...' if len(analysis_text) > 100 else '')
            
            # Показываем краткое описание промпта вместо его содержимого
            prompt_info = f"Создан ({len(analysis_result.get('prompt', ''))} символов)"
            
            text = f"""📐 <b>Выберите размер изображения</b>

🔍 <b>Анализ:</b> {analysis_preview}

✍️ <b>Промпт:</b> {prompt_info}
🎭 <b>Аватар:</b> {avatar_name}

🎯 <b>Доступные размеры:</b>"""

            # Строим клавиатуру с выбором размеров
            keyboard_rows = []
            
            logger.info(f"[DEBUG] Генерируем кнопки для соотношений: {list(aspect_options.keys())}")
            
            for ratio_key, ratio_info in aspect_options.items():
                # Отмечаем дефолтный вариант
                icon = "✅" if ratio_key == default_ratio else ""
                button_text = f"{icon} {ratio_info['name']}"
                callback_data = f"aspect_ratio:{ratio_key}"
                
                logger.info(f"[DEBUG] Создаю кнопку: text='{button_text}', callback_data='{callback_data}'")
                
                keyboard_rows.append([
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=callback_data
                    )
                ])
                
                # Добавляем описание в текст
                text += f"\n{ratio_info['name']} - {ratio_info['description']}"
            
            # Добавляем кнопки управления
            keyboard_rows.append([
                InlineKeyboardButton(
                    text="⚙️ Настройки",
                    callback_data="user_settings"
                )
            ])
            
            keyboard_rows.append([
                InlineKeyboardButton(
                    text="🔙 Изменить промпт",
                    callback_data="generation_menu"
                )
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
            
            await message.reply(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            # Переходим в состояние ожидания выбора размера
            await state.set_state(GenerationStates.waiting_for_aspect_ratio_selection)
            
            logger.info(f"Показан выбор размера для пользователя {user_telegram_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка показа выбора размера: {e}")
            await message.reply("❌ Произошла ошибка")
            await state.clear()
    
    async def process_aspect_ratio_selection(self, callback: CallbackQuery, state: FSMContext):
        """Обрабатывает выбор соотношения сторон"""
        logger.info(f"[DEBUG] Получен aspect_ratio callback: {callback.data}")
        try:
            # Извлекаем выбранное соотношение из callback_data
            callback_parts = callback.data.split(":")
            aspect_ratio = ":".join(callback_parts[1:])  # Берет "3:4" из "aspect_ratio:3:4"
            logger.info(f"[DEBUG] Извлеченное соотношение: {aspect_ratio}")
            
            # Проверяем что соотношение валидно
            valid_options = UserSettings.get_aspect_ratio_options()
            logger.info(f"[DEBUG] Доступные варианты: {list(valid_options.keys())}")
            
            if aspect_ratio not in valid_options:
                logger.warning(f"[DEBUG] Соотношение {aspect_ratio} не найдено в {list(valid_options.keys())}")
                try:
                    await callback.answer("❌ Неверное соотношение сторон", show_alert=True)
                except TelegramBadRequest:
                    logger.warning("Callback устарел при проверке соотношения")
                return
            
            logger.info(f"[DEBUG] Соотношение {aspect_ratio} найдено, запускаем генерацию")
            
            # Получаем данные из состояния
            data = await state.get_data()
            is_photo_analysis = data.get("is_photo_analysis", False)
            
            if is_photo_analysis:
                # Для фото-анализа создаем analysis_result из сохраненных данных
                analysis_result = {
                    'analysis': data.get("original_analysis", ""),
                    'prompt': data.get("custom_prompt", "")
                }
                
                # Запускаем фото-генерацию
                await self._start_photo_generation(callback.message, state, aspect_ratio, analysis_result)
            else:
                # Обычная генерация
                await self._start_generation_from_callback(callback, state, aspect_ratio)
            
            # ✅ БЕЗОПАСНОЕ ЗАВЕРШЕНИЕ - callback.answer() только если не устарел
            try:
                await callback.answer()
            except TelegramBadRequest as e:
                if "query is too old" in str(e):
                    logger.info(f"Callback устарел для {callback.from_user.id}, но генерация запущена")
                else:
                    logger.warning(f"Ошибка callback.answer() в process_aspect_ratio_selection: {e}")
            
        except Exception as e:
            logger.exception(f"Ошибка обработки выбора размера: {e}")
            # ✅ БЕЗОПАСНАЯ ОБРАБОТКА ОШИБОК  
            try:
                await callback.answer("❌ Произошла ошибка", show_alert=True)
            except TelegramBadRequest:
                logger.warning(f"Callback устарел при обработке ошибки: {e}")
    
    async def _start_generation(self, message: Message, state: FSMContext, aspect_ratio: str):
        """Запускает генерацию с выбранными параметрами"""
        
        try:
            data = await state.get_data()
            avatar_id = data.get("avatar_id")
            custom_prompt = data.get("custom_prompt")
            avatar_name = data.get("avatar_name")
            
            if not all([avatar_id, custom_prompt]):
                await message.reply("❌ Ошибка: не найдены данные для генерации")
                await state.clear()
                return
            
            user_telegram_id = message.from_user.id
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await message.reply("❌ Пользователь не найден")
                    await state.clear()
                    return
            
            # Получаем название размера для отображения
            aspect_options = UserSettings.get_aspect_ratio_options()
            aspect_name = aspect_options.get(aspect_ratio, {}).get("name", aspect_ratio)
            
            # Показываем сообщение о генерации
            processing_message = await message.reply(
                f"""🎨 <b>Создаю изображение...</b>

📝 <b>Промпт:</b> {custom_prompt[:60]}{'...' if len(custom_prompt) > 60 else ''}
🎭 <b>Аватар:</b> {avatar_name}
📐 <b>Размер:</b> {aspect_name}
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
                aspect_ratio=aspect_ratio,
                num_images=1
            )
            
            # Сразу запускаем мониторинг статуса
            await self._monitor_generation_status(processing_message, generation, custom_prompt, avatar_name)
            
            await state.clear()
            logger.info(f"Запущена генерация {generation.id} с размером {aspect_ratio} для пользователя {user_telegram_id}")
            
        except ValueError as e:
            await message.reply(f"❌ {str(e)}")
            await state.clear()
        except Exception as e:
            logger.exception(f"Ошибка запуска генерации: {e}")
            await message.reply("❌ Произошла ошибка при запуске генерации")
            await state.clear()
    
    async def _start_generation_from_callback(self, callback: CallbackQuery, state: FSMContext, aspect_ratio: str):
        """Запускает генерацию из callback (при выборе размера)"""
        
        try:
            data = await state.get_data()
            avatar_id = data.get("avatar_id")
            custom_prompt = data.get("custom_prompt")
            avatar_name = data.get("avatar_name")
            
            if not all([avatar_id, custom_prompt]):
                # Используем безопасный ответ - если callback устарел, молча игнорируем
                try:
                    await callback.answer("❌ Ошибка: не найдены данные для генерации", show_alert=True)
                except TelegramBadRequest:
                    logger.warning(f"Callback устарел, но продолжаем генерацию для пользователя {callback.from_user.id}")
                await state.clear()
                return
            
            user_telegram_id = callback.from_user.id
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    try:
                        await callback.answer("❌ Пользователь не найден", show_alert=True)
                    except TelegramBadRequest:
                        logger.warning(f"Callback устарел при проверке пользователя {user_telegram_id}")
                    await state.clear()
                    return
            
            # Получаем название размера для отображения
            aspect_options = UserSettings.get_aspect_ratio_options()
            aspect_name = aspect_options.get(aspect_ratio, {}).get("name", aspect_ratio)
            
            # Обновляем сообщение на генерацию
            await callback.message.edit_text(
                f"""🎨 <b>Создаю изображение...</b>

📝 <b>Промпт:</b> {custom_prompt[:60]}{'...' if len(custom_prompt) > 60 else ''}
🎭 <b>Аватар:</b> {avatar_name}
📐 <b>Размер:</b> {aspect_name} (соотношение {aspect_ratio})
⚡ <b>Модель:</b> FLUX 1.1 Ultra (максимальный фотореализм)

⏳ <b>Генерация запущена...</b>
💡 Обычно занимает 30-60 секунд""",
                parse_mode="HTML"
            )
            
            # ✅ ВАЖНО: НЕ ИСПОЛЬЗУЕМ await callback.answer() в начале!
            # Запускаем генерацию
            generation = await self.generation_service.generate_custom(
                user_id=user.id,
                avatar_id=UUID(avatar_id),
                custom_prompt=custom_prompt,
                quality_preset="photorealistic_max",
                aspect_ratio=aspect_ratio,  # ✅ Передаем правильное соотношение
                num_images=1
            )
            
            # Сразу запускаем мониторинг статуса
            await self._monitor_generation_status(callback.message, generation, custom_prompt, avatar_name)
            
            await state.clear()
            
            # ✅ БЕЗОПАСНЫЙ callback.answer() В КОНЦЕ
            # Если callback уже устарел - молча игнорируем
            try:
                await callback.answer()
            except TelegramBadRequest as e:
                if "query is too old" in str(e):
                    logger.info(f"Callback устарел для пользователя {user_telegram_id}, но генерация запущена успешно")
                else:
                    logger.warning(f"Ошибка callback.answer(): {e}")
            
            logger.info(f"Запущена генерация {generation.id} с размером {aspect_ratio} для пользователя {user_telegram_id}")
            
        except ValueError as e:
            try:
                await callback.answer(f"❌ {str(e)}", show_alert=True)
            except TelegramBadRequest:
                logger.warning(f"Callback устарел при ошибке валидации: {e}")
            await state.clear()
        except Exception as e:
            logger.exception(f"Ошибка запуска генерации из callback: {e}")
            try:
                await callback.answer("❌ Произошла ошибка при запуске генерации", show_alert=True)
            except TelegramBadRequest:
                logger.warning(f"Callback устарел при критической ошибке: {e}")
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
                    from aiogram.types import BufferedInputFile
                    
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
        """Показывает полный детальный промпт генерации в копируемом формате"""
        
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
            
            # Отправляем отдельное сообщение с промптом в копируемом формате
            prompt_text = f"""{generation.final_prompt}"""

            # Создаем информационное сообщение с кнопками
            info_text = f"""📝 ДЕТАЛЬНЫЙ ПРОМПТ

🎭 Аватар: {generation.avatar.name}
📊 ID: {str(generation.id)[:8]}
💡 Длина: {len(generation.final_prompt)} символов

📋 Ваш промпт: {generation.original_prompt}

👆 Промпт выше можно скопировать нажав на него"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 К генерации",
                        callback_data="generation_menu"
                    ),
                    InlineKeyboardButton(
                        text="🖼️ Галерея",
                        callback_data="my_gallery"
                    )
                ]
            ])
            
            # Сначала отправляем чистый промпт без форматирования
            await callback.message.reply(
                prompt_text,
                parse_mode=None  # Без форматирования для копирования
            )
            
            # Затем отправляем информационное сообщение с кнопками
            await callback.message.reply(
                info_text,
                reply_markup=keyboard,
                parse_mode=None  # Без HTML для простоты
            )
            
            await callback.answer("📝 Промпт отправлен! Нажмите на сообщение выше чтобы скопировать")
            
        except ValueError as e:
            await callback.answer("❌ Неверный формат данных", show_alert=True)
        except Exception as e:
            logger.exception(f"Ошибка показа полного промпта: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def show_photo_prompt_input(self, callback: CallbackQuery, state: FSMContext):
        """Показывает форму для загрузки референсного фото"""
        
        try:
            # Извлекаем avatar_id из callback_data (gen_photo:{avatar_id})
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
            
            # Проверяем доступность Vision API
            if not self.image_analysis_service.is_available():
                await callback.answer("❌ Анализ изображений временно недоступен", show_alert=True)
                return
            
            # Показываем форму для загрузки фото
            text = f"""📸 <b>Промпт по референсному фото</b>

🎭 <b>Аватар:</b> {avatar.name}
✨ <b>Тип:</b> {avatar.training_type.value.title()}

📋 <b>Отправьте фото для анализа:</b>

🤖 <b>ИИ-анализ изображения:</b>
• 🔍 GPT-4 Vision проанализирует ваше фото
• ✍️ Создаст детальный фотореалистичный промпт
• 🎨 Автоматически запустит генерацию
• 🗑️ Ваше фото будет удалено после анализа

💡 <b>Лучшие результаты:</b>
• Четкие фотографии с хорошим освещением
• Видимые детали лица, одежды, окружения
• Портреты, полный рост, тематические кадры
• Профессиональные или качественные любительские фото

📱 <b>Отправьте изображение:</b>
Просто прикрепите фото к сообщению и отправьте!"""

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
            await state.set_state(GenerationStates.waiting_for_reference_photo)
            
            logger.info(f"Пользователь {user_telegram_id} начал загрузку референсного фото для аватара {avatar_id}")
            
        except ValueError as e:
            await callback.answer("❌ Неверный формат данных", show_alert=True)
        except Exception as e:
            logger.exception(f"Ошибка показа формы фото-промпта: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def process_reference_photo(self, message: Message, state: FSMContext):
        """Обрабатывает референсное фото от пользователя"""
        
        try:
            # Получаем данные из состояния
            data = await state.get_data()
            avatar_id = data.get("avatar_id")
            
            if not avatar_id:
                await message.reply("❌ Ошибка: не найдены данные аватара. Попробуйте еще раз.")
                await state.clear()
                return
            
            user_telegram_id = message.from_user.id
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await message.reply("❌ Пользователь не найден")
                    await state.clear()
                    return
            
            # Получаем аватар ДО анализа
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
            
            # Показываем сообщение об анализе
            analysis_message = await message.reply(
                f"""🔍 <b>Анализирую изображение...</b>

🎭 <b>Аватар:</b> {avatar.name}
🤖 <b>ИИ-анализ:</b> GPT-4 Vision
⚡ <b>Модель:</b> FLUX 1.1 Ultra

⏳ <b>Этапы обработки:</b>
• 📸 Анализ изображения...
• ✍️ Создание промпта...
• 🎨 Запуск генерации...

💡 Обычно занимает 30-60 секунд""",
                parse_mode="HTML"
            )
            
            # Получаем фото
            if message.photo:
                # Берем фото наибольшего размера
                photo = message.photo[-1]
                file_info = await message.bot.get_file(photo.file_id)
                
                # Скачиваем файл
                image_data = await message.bot.download_file(file_info.file_path)
                image_bytes = image_data.read()
                
                logger.info(f"Получено фото: {len(image_bytes)} байт, file_id: {photo.file_id}")
            elif message.document and message.document.mime_type and message.document.mime_type.startswith('image/'):
                # Обрабатываем как документ (изображение)
                file_info = await message.bot.get_file(message.document.file_id)
                image_data = await message.bot.download_file(file_info.file_path)
                image_bytes = image_data.read()
                
                logger.info(f"Получен документ-изображение: {len(image_bytes)} байт, file_id: {message.document.file_id}")
            else:
                await analysis_message.edit_text(
                    "❌ Пожалуйста, отправьте изображение (фото или файл)",
                    parse_mode="HTML"
                )
                return
            
            # Анализируем изображение
            avatar_type = avatar.training_type.value if avatar.training_type else "portrait"
            analysis_result = await self.image_analysis_service.analyze_image_for_prompt(
                image_bytes, avatar_type
            )
            
            if not analysis_result.get("prompt"):
                await analysis_message.edit_text(
                    f"""❌ <b>Ошибка анализа изображения</b>

🚫 <b>Причина:</b> {analysis_result.get('error', 'Не удалось создать промпт из изображения')}

💡 <b>Попробуйте:</b>
• Отправить другое изображение
• Убедиться что изображение четкое
• Использовать стандартные форматы (JPG, PNG)""",
                    parse_mode="HTML"
                )
                return
            
            # Удаляем сообщение пользователя с фото
            try:
                await message.delete()
                logger.info(f"Сообщение пользователя с фото удалено (message_id: {message.message_id})")
            except Exception as e:
                logger.warning(f"Не удалось удалить сообщение с фото: {e}")
            
            # Обновляем сообщение с результатом анализа
            await analysis_message.edit_text(
                f"""✅ <b>Анализ завершен!</b>

🔍 <b>Анализ изображения:</b>
{analysis_result['analysis']}

✍️ <b>Создан детальный кинематографический промпт:</b>
• Длина: {len(analysis_result['prompt'])} символов
• Стиль: Профессиональная фотография 8K
• Технические детали: Добавлены автоматически

📐 <b>Выберите размер изображения...</b>""",
                parse_mode="HTML"
            )
            
            # Проверяем настройки пользователя - быстрый режим или выбор размера
            user_settings = await self.user_settings_service.get_user_settings(user.id)
            quick_mode = user_settings.quick_generation_mode if user_settings else False
            
            # Сохраняем данные анализа в состоянии
            await state.update_data(
                avatar_id=str(avatar_id),
                custom_prompt=analysis_result['prompt'],  # Используем промпт от GPT Vision
                avatar_name=avatar.name,
                is_photo_analysis=True,
                original_analysis=analysis_result['analysis']
            )
            
            if quick_mode:
                # Быстрый режим - сразу запускаем генерацию с настройками по умолчанию
                default_aspect_ratio = user_settings.default_aspect_ratio if user_settings else "1:1"
                await self._start_photo_generation(analysis_message, state, default_aspect_ratio, analysis_result)
            else:
                # Обычный режим - показываем выбор размера
                await self._show_photo_aspect_ratio_selection(analysis_message, state, analysis_result)
            
        except ValueError as e:
            # Ошибки валидации (недостаточно баланса и т.д.)
            await message.reply(f"❌ {str(e)}")
            await state.clear()
            
        except Exception as e:
            logger.exception(f"Ошибка обработки референсного фото: {e}")
            await message.reply("❌ Произошла ошибка при анализе изображения")
            await state.clear()

    async def _show_photo_aspect_ratio_selection(self, message: Message, state: FSMContext, analysis_result: dict):
        """Показывает выбор размера для фото-генерации"""
        
        try:
            data = await state.get_data()
            custom_prompt = data.get("custom_prompt", "")
            avatar_name = data.get("avatar_name", "")
            
            # Получаем настройки пользователя для дефолтного выбора
            user_telegram_id = message.chat.id  # Для сообщений используем chat.id
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                default_ratio = "1:1"
                if user:
                    default_ratio = await self.user_settings_service.get_default_aspect_ratio(user.id)
            
            # Получаем доступные варианты
            aspect_options = UserSettings.get_aspect_ratio_options()
            
            # ✅ БЕЗОПАСНАЯ ОБРАБОТКА ДАННЫХ АНАЛИЗА
            analysis_text = str(analysis_result.get('analysis', 'Анализ не выполнен'))
            analysis_preview = analysis_text[:100] + ('...' if len(analysis_text) > 100 else '')
            
            # Показываем краткое описание промпта вместо его содержимого
            prompt_info = f"Создан ({len(analysis_result.get('prompt', ''))} символов)"
            
            text = f"""📐 <b>Выберите размер изображения</b>

🔍 <b>Анализ:</b> {analysis_preview}

✍️ <b>Промпт:</b> {prompt_info}
🎭 <b>Аватар:</b> {avatar_name}

🎯 <b>Доступные размеры:</b>"""

            # Строим клавиатуру с выбором размеров
            keyboard_rows = []
            
            for ratio_key, ratio_info in aspect_options.items():
                # Отмечаем дефолтный вариант
                icon = "✅" if ratio_key == default_ratio else ""
                button_text = f"{icon} {ratio_info['name']}"
                
                keyboard_rows.append([
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"aspect_ratio:{ratio_key}"
                    )
                ])
                
                # Добавляем описание в текст
                text += f"\n{ratio_info['name']} - {ratio_info['description']}"
            
            # Добавляем кнопки управления
            keyboard_rows.append([
                InlineKeyboardButton(
                    text="🔙 Изменить фото",
                    callback_data="generation_menu"
                )
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
            
            await message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            # Переходим в состояние ожидания выбора размера
            await state.set_state(GenerationStates.waiting_for_aspect_ratio_selection)
            
            logger.info(f"Показан выбор размера для фото-генерации пользователя {user_telegram_id}")
            logger.info(f"[DEBUG] Analysis data: {analysis_result}")  # Дебаг информация
            
        except Exception as e:
            logger.exception(f"Ошибка показа выбора размера для фото: {e}")
            await message.edit_text("❌ Произошла ошибка")
            await state.clear()
    
    async def _start_photo_generation(self, message: Message, state: FSMContext, aspect_ratio: str, analysis_result: dict):
        """Запускает генерацию для фото-анализа с революционнами улучшениями"""
        
        try:
            data = await state.get_data()
            avatar_id = data.get("avatar_id")
            custom_prompt = data.get("custom_prompt")
            avatar_name = data.get("avatar_name")
            
            if not all([avatar_id, custom_prompt]):
                await message.edit_text("❌ Ошибка: не найдены данные для генерации")
                await state.clear()
                return
            
            user_telegram_id = message.chat.id
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await message.edit_text("❌ Пользователь не найден")
                    await state.clear()
                    return
            
            # Получаем название размера для отображения
            aspect_options = UserSettings.get_aspect_ratio_options()
            aspect_name = aspect_options.get(aspect_ratio, {}).get("name", aspect_ratio)
            
            # Обновляем сообщение на генерацию
            await message.edit_text(
                f"""🎨 <b>Создаю изображение по фото...</b>

🔍 <b>Анализ:</b> {str(analysis_result.get('analysis', 'Анализ выполнен'))[:80]}{'...' if len(str(analysis_result.get('analysis', ''))) > 80 else ''}
🎭 <b>Аватар:</b> {avatar_name}
📐 <b>Размер:</b> {aspect_name}
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
                aspect_ratio=aspect_ratio,
                num_images=1
            )
            
            # 🎯 РЕВОЛЮЦИОННОЕ УЛУЧШЕНИЕ: сохраняем ВСЕ данные анализа в метаданные
            if hasattr(generation, 'prompt_metadata'):
                if not generation.prompt_metadata:
                    generation.prompt_metadata = {}
                
                # Базовая информация анализа
                generation.prompt_metadata['vision_analysis'] = {
                    'analysis': analysis_result['analysis'],
                    'original_prompt_from_image': analysis_result['prompt'],
                    'reference_photo_processed': True,
                    'revolutionary_negatives_applied': analysis_result.get('revolutionary_negatives_applied', False)
                }
                
                # 🎯 КРИТИЧЕСКИ ВАЖНО: сохраняем negative_prompt из анализа фото
                if analysis_result.get('negative_prompt'):
                    # Если есть negative_prompt - перезаписываем в prompt_processing
                    if 'prompt_processing' not in generation.prompt_metadata:
                        generation.prompt_metadata['prompt_processing'] = {}
                    
                    generation.prompt_metadata['prompt_processing']['negative_prompt'] = analysis_result['negative_prompt']
                    generation.prompt_metadata['prompt_processing']['negative_prompt_source'] = 'vision_analysis'
                    
                    logger.info(f"[Photo Analysis] Negative prompt из анализа сохранен: {len(analysis_result['negative_prompt'])} символов")
                elif analysis_result.get('revolutionary_negatives_applied'):
                    # Для FLUX Pro негативы встроены в основной промпт
                    if 'prompt_processing' not in generation.prompt_metadata:
                        generation.prompt_metadata['prompt_processing'] = {}
                    
                    generation.prompt_metadata['prompt_processing']['negative_prompt'] = None
                    generation.prompt_metadata['prompt_processing']['negative_prompt_source'] = 'flux_pro_embedded'
                    
                    logger.info(f"[Photo Analysis] Негативы встроены в основной промпт для FLUX Pro")
            
            # Сразу запускаем мониторинг статуса
            await self._monitor_generation_status(
                message, 
                generation, 
                f"[Фото-анализ] {custom_prompt}", 
                avatar_name
            )
            
            await state.clear()
            logger.info(f"Запущена революционная фото-генерация {generation.id} с размером {aspect_ratio} для пользователя {user_telegram_id}")
            
        except ValueError as e:
            await message.edit_text(f"❌ {str(e)}")
            await state.clear()
        except Exception as e:
            logger.exception(f"Ошибка запуска фото-генерации: {e}")
            await message.edit_text("❌ Произошла ошибка при запуске генерации")
            await state.clear()


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

@router.callback_query(F.data.startswith("gen_photo:"))
async def handle_photo_prompt_request(callback: CallbackQuery, state: FSMContext):
    """Обработчик запроса фото-промпта"""
    await generation_handler.show_photo_prompt_input(callback, state)

@router.message(F.photo, StateFilter(GenerationStates.waiting_for_reference_photo))
async def handle_reference_photo(message: Message, state: FSMContext):
    """Обработчик референсного фото от пользователя"""
    await generation_handler.process_reference_photo(message, state)

@router.message(F.document, StateFilter(GenerationStates.waiting_for_reference_photo))
async def handle_reference_photo_document(message: Message, state: FSMContext):
    """Обработчик референсного фото как документа от пользователя"""
    await generation_handler.process_reference_photo(message, state)

@router.message(F.text, StateFilter(GenerationStates.waiting_for_reference_photo))
async def handle_text_instead_of_photo(message: Message, state: FSMContext):
    """Обработчик текста вместо фото в состоянии ожидания фото"""
    await message.reply(
        "📸 Пожалуйста, отправьте изображение, а не текст.\n\n"
        "💡 Прикрепите фото к сообщению или отправьте изображение как файл.",
        parse_mode="HTML"
    )

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

@router.callback_query(F.data.startswith("aspect_ratio:"))
async def handle_aspect_ratio_selection(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора соотношения сторон"""
    logger.info(f"[DEBUG] Получен aspect_ratio callback: {callback.data}")
    await generation_handler.process_aspect_ratio_selection(callback, state)

@router.callback_query(F.data == "user_settings")
async def handle_user_settings_request(callback: CallbackQuery):
    """Обработчик запроса настроек пользователя"""
    await callback.answer("🚧 Настройки пользователя в разработке", show_alert=True)

@router.message(F.text, StateFilter(GenerationStates.waiting_for_aspect_ratio_selection))
async def handle_text_instead_of_aspect_ratio(message: Message, state: FSMContext):
    """Обработчик текста вместо выбора размера"""
    await message.reply(
        "📐 Пожалуйста, выберите размер изображения из предложенных вариантов.\n\n"
        "💡 Используйте кнопки выше для выбора соотношения сторон.",
        parse_mode="HTML"
    )

@router.callback_query(F.data == "gen_change_avatar")
async def handle_change_avatar_request(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает запрос на смену аватара"""
    # Импортируем обработчик аватаров
    from app.handlers.avatar import avatar_main_handler
    
    # Очищаем состояние, если есть
    await state.clear()
    
    # Перенаправляем на меню аватаров
    await avatar_main_handler.show_avatar_menu(callback, state) 