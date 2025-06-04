"""
Обработчик промптов по фото для генерации изображений
"""
from uuid import UUID

from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.shared.handlers.base_handler import BaseHandler
from app.shared.decorators.auth_decorators import require_user, require_main_avatar
from app.core.logger import get_logger
from app.services.generation.image_analysis_service import ImageAnalysisService
from app.services.user_settings import UserSettingsService
from .states import GenerationStates
from .keyboards import build_photo_prompt_keyboard, build_aspect_ratio_keyboard

logger = get_logger(__name__)


class PhotoPromptHandler(BaseHandler):
    """Обработчик промптов по фото"""
    
    def __init__(self):
        self.image_analysis_service = ImageAnalysisService()
        self.user_settings_service = UserSettingsService()
    
    @require_user()
    @require_main_avatar(check_completed=True)
    async def show_photo_prompt_input(
        self, 
        callback: CallbackQuery, 
        state: FSMContext,
        user=None,
        main_avatar=None
    ):
        """Показывает форму для загрузки референсного фото"""
        
        try:
            # Извлекаем avatar_id из callback_data (gen_photo:{avatar_id})
            data_parts = callback.data.split(":")
            avatar_id = UUID(data_parts[1])
            
            # Проверяем что это тот же аватар
            if avatar_id != main_avatar.id:
                await callback.answer("❌ Неверный аватар", show_alert=True)
                return
            
            # Проверяем доступность Vision API
            if not self.image_analysis_service.is_available():
                await callback.answer("❌ Анализ изображений временно недоступен", show_alert=True)
                return
            
            # Показываем форму для загрузки фото
            text = f"""📸 <b>Промпт по референсному фото</b>

🎭 <b>Аватар:</b> {main_avatar.name}
✨ <b>Тип:</b> {main_avatar.training_type.value.title()}

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

            keyboard = build_photo_prompt_keyboard()
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            # Сохраняем avatar_id в состоянии для дальнейшей обработки
            await state.update_data(
                avatar_id=str(avatar_id),
                user_id=str(user.id)
            )
            await state.set_state(GenerationStates.waiting_for_reference_photo)
            
            logger.info(f"Пользователь {user.telegram_id} начал загрузку референсного фото для аватара {avatar_id}")
            
        except ValueError as e:
            await callback.answer("❌ Неверный формат данных", show_alert=True)
        except Exception as e:
            logger.exception(f"Ошибка показа формы фото-промпта: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
            await self.safe_clear_state(state)

    async def process_reference_photo(self, message: Message, state: FSMContext):
        """Обрабатывает референсное фото от пользователя"""
        
        try:
            # Получаем данные из состояния
            data = await state.get_data()
            avatar_id = data.get("avatar_id")
            user_id = data.get("user_id")
            
            if not avatar_id or not user_id:
                await message.reply("❌ Ошибка: не найдены данные аватара. Попробуйте еще раз.")
                await self.safe_clear_state(state)
                return
            
            # Получаем пользователя
            user = await self.get_user_from_message(message)
            if not user or user.id != UUID(user_id):
                await message.reply("❌ Ошибка авторизации")
                await self.safe_clear_state(state)
                return
            
            # Получаем аватар
            avatar = await self.get_avatar_by_id(
                UUID(avatar_id), 
                user_id=user.id,
                message=message
            )
            if not avatar:
                await self.safe_clear_state(state)
                return
            
            # Проверяем статус аватара
            if avatar.status != "completed":
                await message.reply("❌ Аватар еще не готов к генерации!")
                await self.safe_clear_state(state)
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
            
            # Получаем изображение
            image_bytes = await self._extract_image_from_message(message, analysis_message)
            if not image_bytes:
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
                await self.start_photo_generation(analysis_message, state, default_aspect_ratio, analysis_result)
            else:
                # Обычный режим - показываем выбор размера
                await self.show_photo_aspect_ratio_selection(analysis_message, state, analysis_result)
            
        except ValueError as e:
            # Ошибки валидации (недостаточно баланса и т.д.)
            await message.reply(f"❌ {str(e)}")
            await self.safe_clear_state(state)
            
        except Exception as e:
            logger.exception(f"Ошибка обработки референсного фото: {e}")
            await message.reply("❌ Произошла ошибка при анализе изображения")
            await self.safe_clear_state(state)
    
    async def _extract_image_from_message(self, message: Message, analysis_message: Message) -> bytes:
        """Извлекает изображение из сообщения"""
        
        try:
            if message.photo:
                # Берем фото наибольшего размера
                photo = message.photo[-1]
                file_info = await message.bot.get_file(photo.file_id)
                
                # Скачиваем файл
                image_data = await message.bot.download_file(file_info.file_path)
                image_bytes = image_data.read()
                
                logger.info(f"Получено фото: {len(image_bytes)} байт, file_id: {photo.file_id}")
                return image_bytes
                
            elif message.document and message.document.mime_type and message.document.mime_type.startswith('image/'):
                # Обрабатываем как документ (изображение)
                file_info = await message.bot.get_file(message.document.file_id)
                image_data = await message.bot.download_file(file_info.file_path)
                image_bytes = image_data.read()
                
                logger.info(f"Получен документ-изображение: {len(image_bytes)} байт, file_id: {message.document.file_id}")
                return image_bytes
                
            else:
                await analysis_message.edit_text(
                    "❌ Пожалуйста, отправьте изображение (фото или файл)",
                    parse_mode="HTML"
                )
                return None
                
        except Exception as e:
            logger.exception(f"Ошибка извлечения изображения: {e}")
            await analysis_message.edit_text(
                "❌ Ошибка при обработке изображения",
                parse_mode="HTML"
            )
            return None
    
    async def show_photo_aspect_ratio_selection(self, message: Message, state: FSMContext, analysis_result: dict):
        """Показывает выбор соотношения сторон для фото-промпта"""
        
        try:
            # Получаем данные из состояния
            data = await state.get_data()
            avatar_name = data.get("avatar_name")
            
            text = f"""📐 <b>Выберите формат изображения</b>

🎭 <b>Аватар:</b> {avatar_name}
🔍 <b>Анализ:</b> {analysis_result['analysis'][:100]}{"..." if len(analysis_result['analysis']) > 100 else ""}

👇 <b>Выберите соотношение сторон:</b>"""
            
            keyboard = build_aspect_ratio_keyboard()
            
            # Устанавливаем состояние ожидания выбора соотношения
            await state.set_state(GenerationStates.waiting_for_aspect_ratio_selection)
            
            await message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            logger.info(f"Показан выбор соотношения сторон для фото-промпта")
            
        except Exception as e:
            logger.exception(f"Ошибка показа выбора соотношения сторон: {e}")
            await message.reply("❌ Произошла ошибка")
            await self.safe_clear_state(state)
    
    async def start_photo_generation(self, message: Message, state: FSMContext, aspect_ratio: str, analysis_result: dict):
        """Запускает генерацию изображения по фото-промпту"""
        
        try:
            # Импортируем GenerationMonitor для запуска генерации
            from .generation_monitor import GenerationMonitor
            
            generation_monitor = GenerationMonitor()
            
            # Обновляем состояние с флагом фото-анализа
            await state.update_data(is_photo_analysis=True)
            
            # Запускаем генерацию через монитор
            await generation_monitor.start_generation(
                message, state, aspect_ratio, is_photo_analysis=True
            )
            
        except Exception as e:
            logger.exception(f"Ошибка запуска фото-генерации: {e}")
            await message.edit_text(
                "❌ Произошла ошибка при запуске генерации",
                parse_mode="HTML"
            )
            await self.safe_clear_state(state) 