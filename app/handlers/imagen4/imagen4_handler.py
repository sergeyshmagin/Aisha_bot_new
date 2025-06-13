"""
Хэндлер для генерации изображений через Imagen 4
"""
import logging
from typing import Optional

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.database.models import UserSettings, ImageGeneration, GenerationStatus
from app.shared.handlers.base_handler import BaseHandler
from app.handlers.generation.states import GenerationStates
from app.handlers.generation.keyboards import (
    build_imagen4_menu_keyboard,
    build_imagen4_prompt_keyboard,
    build_imagen4_aspect_ratio_keyboard
)
from app.core.config import settings
from app.services.balance_service import BalanceService
from app.core.di import get_user_service
from app.core.database import get_session
from app.shared.decorators.auth_decorators import require_user
from app.utils.datetime_utils import now_utc
from app.services.generation.imagen4.models import Imagen4Request, AspectRatio, Imagen4GenerationStatus

logger = logging.getLogger(__name__)

# Создаем роутер
imagen4_router = Router(name="imagen4")


class Imagen4Handler(BaseHandler):
    """Обработчик Imagen 4 генерации"""
    
    def __init__(self):
        super().__init__()
    
    @require_user()
    async def show_prompt_input(self, callback: CallbackQuery, state: FSMContext, user=None):
        """Прямой запрос промпта для Imagen 4 (без лишних меню)"""
        try:
            await state.clear()
            
            # Проверяем баланс пользователя
            async with get_session() as session:
                balance_service = BalanceService(session)
                user_balance = await balance_service.get_balance(user.id)
                
                generation_cost = settings.IMAGEN4_GENERATION_COST
                
                if user_balance < generation_cost:
                    insufficient_text = f"""❌ <b>Недостаточно средств</b>

💎 Ваш баланс: <b>{user_balance} кредитов</b>
💰 Нужно для генерации: <b>{generation_cost} кредитов</b>

Пополните баланс в разделе "Профиль" → "Пополнить баланс"."""
                    
                    try:
                        await callback.message.edit_text(
                            text=insufficient_text,
                            parse_mode="HTML"
                        )
                    except Exception:
                        await callback.message.answer(
                            text=insufficient_text,
                            parse_mode="HTML"
                        )
                    
                    await callback.answer()
                    return
            
            # Текст запроса промпта
            prompt_text = f"""🎨 <b>Imagen 4 - Генерация изображений</b>

🌟 <b>Создавайте потрясающие изображения по текстовому описанию</b>
⚡ <b>Высокочественная генерация от Google</b>

💎 <b>Ваш баланс:</b> {user_balance} кредитов
💰 <b>Стоимость:</b> {generation_cost} кредитов за изображение

📝 <b>Опишите что хотите увидеть на изображении:</b>

💡 <b>Например:</b> "красивая девушка в красном платье на фоне заката"

⚠️ <b>Важно:</b>
• Описывайте на русском языке
• Будьте конкретны в деталях
• Избегайте неподходящего контента"""
            
            # Показываем запрос промпта
            keyboard = build_imagen4_prompt_keyboard()
            
            try:
                await callback.message.edit_text(
                    text=prompt_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            except Exception:
                await callback.message.answer(
                    text=prompt_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            
            # Устанавливаем состояние ожидания промпта
            await state.set_state(GenerationStates.waiting_for_imagen4_prompt)
            await callback.answer()
            
            logger.info(f"Показан запрос промпта Imagen 4 для пользователя {user.telegram_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка показа запроса промпта Imagen 4: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    @require_user()
    async def show_imagen4_menu(self, callback: CallbackQuery, state: FSMContext = None, user=None):
        """Показывает меню Imagen 4 (оставляем для совместимости)"""
        # Если state не передан, создаем заглушку
        if state is None:
            from aiogram.fsm.context import FSMContext
            from aiogram.fsm.storage.base import StorageKey
            # Создаем временный state для совместимости
            storage_key = StorageKey(bot_id=callback.bot.id, chat_id=callback.message.chat.id, user_id=callback.from_user.id)
            state = FSMContext(storage=callback.bot.session.storage, key=storage_key)
        
        # Перенаправляем на прямой запрос промпта
        await self.show_prompt_input(callback, state, user=user)
    
    async def process_prompt(self, message: Message, state: FSMContext):
        """Обработать введенный промпт и показать выбор aspect ratio"""
        try:
            prompt = message.text.strip()
            
            # Валидация промпта
            if len(prompt) < 3:
                await message.reply(
                    "❌ Описание слишком короткое\n\n"
                    "💡 Пожалуйста, напишите более подробное описание (минимум 3 символа)"
                )
                return
            
            if len(prompt) > 2000:
                await message.reply(
                    "❌ Описание слишком длинное\n\n"
                    "💡 Пожалуйста, сократите описание (максимум 2000 символов)"
                )
                return
            
            # Сохраняем промпт в состоянии
            await state.update_data(imagen4_prompt=prompt)
            
            # Показываем выбор соотношения сторон
            await self.show_aspect_ratio_selection(message, state)
            
        except Exception as e:
            logger.exception(f"Ошибка обработки промпта: {e}")
            await message.reply("❌ Произошла ошибка при обработке описания")
    
    async def show_aspect_ratio_selection(self, message: Message, state: FSMContext):
        """Показать выбор соотношения сторон"""
        try:
            text = (
                "📐 <b>Выберите соотношение сторон</b>\n\n"
                "🔲 <b>Квадрат (1:1)</b> - Instagram, профили\n"
                "📱 <b>Портрет (3:4)</b> - Вертикальные фото\n"
                "🎬 <b>Кино (16:9)</b> - Широкоэкранная\n"
                "📺 <b>Сторис (9:16)</b> - TikTok, Instagram Stories\n\n"
                "💡 Выберите формат, который лучше подходит для вашего изображения:"
            )
            
            keyboard = build_imagen4_aspect_ratio_keyboard()
            
            await message.answer(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            # Устанавливаем состояние выбора aspect ratio
            await state.set_state(GenerationStates.imagen4_selecting_aspect_ratio)
            
        except Exception as e:
            logger.exception(f"Ошибка показа выбора соотношения сторон: {e}")
            await message.reply("❌ Произошла ошибка")
    
    async def process_aspect_ratio_selection(self, callback: CallbackQuery, state: FSMContext):
        """Обработать выбор соотношения сторон и запустить генерацию"""
        try:
            # Извлекаем aspect ratio из callback
            callback_parts = callback.data.split(":")
            if len(callback_parts) < 3:
                await callback.answer("❌ Неверный формат данных", show_alert=True)
                return
            
            aspect_ratio = ":".join(callback_parts[1:])  # "imagen4_aspect_ratio:1:1" -> "1:1"
            
            # Проверяем валидность
            valid_options = UserSettings.get_aspect_ratio_options()
            if aspect_ratio not in valid_options:
                await callback.answer("❌ Неверное соотношение сторон", show_alert=True)
                return
            
            # Получаем данные из состояния
            data = await state.get_data()
            prompt = data.get("imagen4_prompt")
            
            if not prompt:
                await callback.answer("❌ Промпт не найден, начните заново", show_alert=True)
                await state.clear()
                return
            
            # Запускаем генерацию
            await self.start_generation(callback, state, prompt, aspect_ratio)
            
        except Exception as e:
            logger.exception(f"Ошибка обработки выбора соотношения сторон: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def start_generation(
        self, 
        callback: CallbackQuery, 
        state: FSMContext, 
        prompt: str, 
        aspect_ratio: str
    ):
        """Запустить генерацию изображения"""
        try:
            from app.services.generation.imagen4.imagen4_service import imagen4_service
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(callback.from_user.id)
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
                
                # Проверяем баланс еще раз
                async with get_session() as session:
                    balance_service = BalanceService(session)
                    user_balance = await balance_service.get_balance(user.id)
                    if user_balance < settings.IMAGEN4_GENERATION_COST:
                        await callback.answer("❌ Недостаточно кредитов для генерации", show_alert=True)
                        return
                    
                    # Получаем название соотношения для отображения
                    aspect_options = UserSettings.get_aspect_ratio_options()
                    aspect_name = aspect_options.get(aspect_ratio, {}).get("name", aspect_ratio)
                    
                    # Показываем сообщение о начале генерации
                    generation_text = (
                        f"🎨 <b>Запускаем генерацию Imagen 4...</b>\n\n"
                        f"📝 <b>Описание:</b> {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n"
                        f"📐 <b>Формат:</b> {aspect_name} ({aspect_ratio})\n"
                        f"💎 <b>Стоимость:</b> {settings.IMAGEN4_GENERATION_COST} кредитов\n\n"
                        f"⏳ Ожидайте, создаем ваше изображение..."
                    )
                    
                    try:
                        await callback.message.edit_text(
                            text=generation_text,
                            parse_mode="HTML"
                        )
                        await callback.answer()
                    except Exception:
                        await callback.message.answer(
                            text=generation_text,
                            parse_mode="HTML"
                        )
                        await callback.answer()
                    
                    # Запускаем генерацию в фоне
                    try:
                        from app.services.generation.imagen4.models import Imagen4Request, AspectRatio
                        
                        # Создаем запрос
                        request = Imagen4Request(
                            prompt=prompt,
                            aspect_ratio=AspectRatio(aspect_ratio),
                            num_images=1,
                            negative_prompt=None,
                            seed=None
                        )
                        
                        # Генерируем изображение
                        generation_result = await imagen4_service.generate_image(request)
                        
                        # Проверяем результат
                        if generation_result.status == "failed":
                            raise Exception(generation_result.error_message)
                        
                        # Списываем кредиты
                        async with get_session() as session:
                            balance_service = BalanceService(session)
                            charge_result = await balance_service.charge_balance(
                                user_id=user.id,
                                amount=generation_result.cost_credits,
                                description=f"Генерация изображения Imagen 4: {prompt[:50]}..."
                            )
                            
                            if not charge_result["success"]:
                                raise Exception(f"Ошибка списания баланса: {charge_result['error']}")
                                
                            user_balance = charge_result["new_balance"]
                        
                        # Создаем запись в базе
                        generation = await self.create_generation(
                            user_id=user.id,
                            prompt=prompt,
                            aspect_ratio=aspect_ratio
                        )
                        
                        # Сохраняем изображения в MinIO
                        logger.info(f"[Imagen4] Сохраняем {len(generation_result.response.images)} изображений в MinIO")
                        
                        from app.services.generation.storage.image_storage import ImageStorage
                        image_storage = ImageStorage()
                        
                        # Получаем URL изображений от FAL
                        fal_urls = [img.url for img in generation_result.response.images]
                        
                        # Сохраняем в MinIO
                        minio_urls = await image_storage.save_images_to_minio(generation, fal_urls)
                        
                        # Используем MinIO URL если удалось сохранить, иначе fallback к FAL URL
                        final_urls = minio_urls if minio_urls else fal_urls
                        
                        # Обновляем запись результатами
                        async with get_session() as session:
                            generation.status = "completed"
                            generation.result_urls = final_urls
                            generation.generation_time = generation_result.generation_time
                            generation.source_model = "fal-ai/imagen4/preview"
                            generation.completed_at = now_utc().replace(tzinfo=None)
                            await session.commit()
                        
                        # Кешируем результат в Redis для быстрого доступа
                        await self._cache_generation_result(generation, user.id)
                        
                        # Показываем результат
                        result_text = (
                            f"✅ <b>Изображение готово!</b>\n\n"
                            f"📝 <b>Описание:</b> {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n"
                            f"📐 <b>Формат:</b> {aspect_name} ({aspect_ratio})\n"
                            f"⏱ <b>Время:</b> {generation_result.generation_time:.1f}с\n"
                            f"💎 <b>Стоимость:</b> {generation_result.cost_credits} кредитов\n"
                            f"💾 <b>Сохранено в:</b> {'MinIO' if minio_urls else 'FAL (временно)'}\n\n"
                            f"🖼 <b>Результат:</b>"
                        )
                        
                        # Отправляем изображение
                        await callback.message.answer_photo(
                            photo=generation_result.response.images[0].url,
                            caption=result_text,
                            parse_mode="HTML"
                        )
                        
                        # Показываем меню
                        await callback.message.answer(
                            text="🎨 <b>Меню Imagen 4</b>\n\nВыберите действие:",
                            parse_mode="HTML",
                            reply_markup=build_imagen4_menu_keyboard(user_balance, settings.IMAGEN4_GENERATION_COST)
                        )
                        
                        # Очищаем состояние
                        await state.clear()
                        
                    except Exception as gen_error:
                        logger.exception(f"Ошибка генерации: {gen_error}")
                        error_text = (
                            "❌ <b>Ошибка генерации</b>\n\n"
                            "Произошла ошибка при создании изображения. "
                            "Попробуйте еще раз или обратитесь в поддержку.\n\n"
                            "💰 Кредиты не были списаны"
                        )
                        
                        try:
                            await callback.message.edit_text(
                                text=error_text,
                                parse_mode="HTML",
                                reply_markup=build_imagen4_menu_keyboard(user_balance, settings.IMAGEN4_GENERATION_COST)
                            )
                        except Exception:
                            await callback.message.answer(
                                text=error_text,
                                parse_mode="HTML",
                                reply_markup=build_imagen4_menu_keyboard(user_balance, settings.IMAGEN4_GENERATION_COST)
                            )
                        
                        await state.clear()
            
        except Exception as e:
            logger.exception(f"Ошибка запуска генерации: {e}")
            await callback.answer("❌ Произошла ошибка при запуске генерации", show_alert=True)
            await state.clear()

    async def create_generation(self, user_id, prompt: str, aspect_ratio: str):
        """Создает новую генерацию Imagen 4"""
        try:
            from app.database.models import ImageGeneration, GenerationStatus
            from uuid import uuid4
            
            generation = ImageGeneration(
                id=uuid4(),
                user_id=user_id,
                avatar_id=None,  # Imagen 4 не использует аватары
                template_id=None,  # Imagen 4 не использует шаблоны
                original_prompt=prompt,
                final_prompt=prompt,  # Для Imagen 4 промпт не изменяется
                quality_preset="standard",
                aspect_ratio=aspect_ratio,
                num_images=1,
                status=GenerationStatus.PENDING,
                generation_type="imagen4",  # Указываем тип генерации
                source_model="imagen4",    # Указываем модель
                created_at=now_utc().replace(tzinfo=None),      # Убираем timezone для PostgreSQL
                result_urls=None,
                error_message=None,
                is_favorite=False
            )
            
            # Сохраняем в БД
            async with get_session() as session:
                session.add(generation)
                await session.commit()
                await session.refresh(generation)
            
            logger.info(f"Создана новая генерация Imagen 4: {generation.id}")
            return generation
            
        except Exception as e:
            logger.exception(f"Ошибка создания генерации: {e}")
            return None
    
    async def _cache_generation_result(self, generation, user_id):
        """Кеширует результат генерации в Redis для быстрого доступа"""
        try:
            from app.core.di import get_redis
            import json
            
            redis = await get_redis()
            
            # Кешируем данные генерации
            cache_data = {
                "id": str(generation.id),
                "user_id": str(user_id),
                "prompt": generation.original_prompt,
                "aspect_ratio": generation.aspect_ratio,
                "result_urls": generation.result_urls,
                "generation_time": generation.generation_time,
                "created_at": generation.created_at.isoformat() if generation.created_at else None,
                "generation_type": generation.generation_type,
                "source_model": generation.source_model
            }
            
            # Кешируем на 1 час
            cache_key = f"imagen4:generation:{generation.id}"
            await redis.setex(cache_key, 3600, json.dumps(cache_data))
            
            # Добавляем в список последних генераций пользователя
            user_cache_key = f"imagen4:user_generations:{user_id}"
            await redis.lpush(user_cache_key, str(generation.id))
            await redis.ltrim(user_cache_key, 0, 49)  # Храним последние 50
            await redis.expire(user_cache_key, 86400)  # 24 часа
            
            # Инвалидируем кеш галереи пользователя
            gallery_cache_key = f"gallery:user_images:{user_id}"
            await redis.delete(gallery_cache_key)
            
            logger.info(f"[Redis Cache] Закешированы данные генерации {generation.id}")
            
        except Exception as e:
            logger.warning(f"[Redis Cache] Ошибка кеширования генерации {generation.id}: {e}")
            # Не прерываем выполнение, кеширование не критично


# Создаем экземпляр обработчика
imagen4_handler = Imagen4Handler()


# ==================== РОУТЫ ====================

@imagen4_router.callback_query(F.data == "imagen4_menu")
async def handle_imagen4_menu(callback: CallbackQuery, state: FSMContext):
    """Обработчик главного меню Imagen 4"""
    await imagen4_handler.show_imagen4_menu(callback, state)


@imagen4_router.callback_query(F.data == "imagen4_prompt")
async def handle_imagen4_prompt_request(callback: CallbackQuery, state: FSMContext):
    """Обработчик запроса ввода промпта для Imagen 4"""
    await imagen4_handler.show_prompt_input(callback, state)


@imagen4_router.message(F.text, StateFilter(GenerationStates.waiting_for_imagen4_prompt))
async def handle_imagen4_prompt_text(message: Message, state: FSMContext):
    """Обработчик текста промпта для Imagen 4"""
    await imagen4_handler.process_prompt(message, state)


@imagen4_router.callback_query(F.data.startswith("imagen4_aspect_ratio:"))
async def handle_imagen4_aspect_ratio_selection(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора соотношения сторон для Imagen 4"""
    await imagen4_handler.process_aspect_ratio_selection(callback, state)


# ==================== ОБРАБОТЧИКИ ОШИБОК ====================

@imagen4_router.message(F.text, StateFilter(GenerationStates.imagen4_selecting_aspect_ratio))
async def handle_text_instead_of_aspect_ratio(message: Message, state: FSMContext):
    """Обработчик текста вместо выбора размера"""
    await message.reply(
        "📐 Пожалуйста, выберите размер изображения из предложенных вариантов.\n\n"
        "💡 Используйте кнопки выше для выбора соотношения сторон.",
        parse_mode="HTML"
    ) 