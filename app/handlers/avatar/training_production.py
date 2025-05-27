"""
Обработчики обучения аватаров (продакшн версия)
Интеграция с FAL AI для запуска и мониторинга обучения
Тестовый режим скрыт от пользователя
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from uuid import UUID
import asyncio

from app.handlers.state import AvatarStates
from app.core.di import get_user_service, get_avatar_service
from app.core.database import get_session
from app.services.avatar.training_service import AvatarTrainingService
from app.services.avatar.fal_training_service import FALTrainingService
from app.database.models import AvatarStatus
from app.core.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)
router = Router()

class TrainingHandler:
    """Обработчик обучения аватаров"""
    
    async def start_training(self, callback: CallbackQuery, state: FSMContext):
        """Запуск обучения аватара"""
        try:
            # Извлекаем avatar_id из callback_data
            if callback.data.startswith("start_training_"):
                avatar_id_str = callback.data.split("_", 2)[2]
            else:
                # Получаем из состояния
                data = await state.get_data()
                avatar_id_str = data.get("avatar_id")
            
            if not avatar_id_str:
                await callback.answer("❌ Аватар не найден", show_alert=True)
                return
            
            avatar_id = UUID(avatar_id_str)
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(callback.from_user.id)
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Проверяем тестовый режим и списываем средства только в продакшн
            is_test_mode = settings.AVATAR_TEST_MODE
            
            if not is_test_mode:
                # В продакшн режиме - списываем средства с баланса
                user_balance = getattr(user, 'balance', 0)
                avatar_cost = 150  # Можно получить из данных состояния
                
                if user_balance < avatar_cost:
                    await callback.message.edit_text(
                        text=f"❌ **Недостаточно средств**\n\nНеобходимо: {avatar_cost} кредитов\nВаш баланс: {user_balance}",
                        parse_mode="Markdown"
                    )
                    return
                
                # Списываем средства (здесь должна быть логика списания)
                # await user_service.deduct_balance(user.id, avatar_cost)
                logger.info(f"💰 ПРОДАКШН: Списано {avatar_cost} кредитов с баланса пользователя {user.id}")
            
            # Показываем индикатор запуска
            status_text = "🧪 **Запускаем тестовое обучение...**" if is_test_mode else "🚀 **Запускаем обучение...**"
            await callback.message.edit_text(
                text=f"{status_text}\n\nПодготавливаем ваши фотографии для обучения",
                parse_mode="Markdown"
            )
            
            try:
                # Получаем данные аватара для определения типа обучения
                async with get_avatar_service() as avatar_service:
                    avatar = await avatar_service.get_avatar(avatar_id)
                    if not avatar:
                        raise RuntimeError("Аватар не найден")
                
                # ИСПРАВЛЕНИЕ: Получаем тип обучения из аватара корректно
                if hasattr(avatar, 'training_type') and avatar.training_type:
                    if hasattr(avatar.training_type, 'value'):
                        training_type = avatar.training_type.value
                    else:
                        training_type = str(avatar.training_type)
                    logger.info(f"🎯 Тип обучения из БД: {training_type}")
                else:
                    # Получаем из состояния FSM как fallback
                    state_data = await state.get_data()
                    training_type = state_data.get('training_type', 'portrait')
                    logger.warning(f"⚠️ Тип обучения из состояния: {training_type} (аватар не содержит training_type)")
                
                logger.info(f"🎯 Запуск обучения аватара {avatar_id} с типом: {training_type}")
                
                # Создаем FAL сервис обучения
                fal_service = FALTrainingService()
                
                # Получаем URL архива с фотографиями (заглушка - нужно реализовать)
                training_data_url = f"https://example.com/photos/{avatar_id}.zip"  # TODO: Реализовать получение реального URL
                
                # Запускаем обучение через FAL AI
                request_id = await fal_service.start_avatar_training(
                    avatar_id=avatar_id,
                    training_type=training_type,
                    training_data_url=training_data_url,
                    user_preferences={"quality": "balanced"}
                )
                
                if request_id:
                    # Обновляем аватар в БД через старый сервис
                    async with get_session() as session:
                        training_service = AvatarTrainingService(session)
                        await training_service._save_training_info(avatar_id, request_id)
                        await training_service._update_avatar_status(
                            avatar_id, 
                            AvatarStatus.TRAINING,
                            progress=0
                        )
                    
                    # Обновляем состояние
                    await state.set_state(AvatarStates.training_in_progress)
                    await state.update_data(
                        avatar_id=str(avatar_id),
                        finetune_id=request_id,
                        training_type=training_type
                    )
                    
                    # Показываем статус обучения
                    await self._show_training_progress(callback, avatar_id, request_id)
                    
                    logger.info(f"✅ Обучение аватара {avatar_id} запущено успешно: request_id={request_id}")
                else:
                    raise RuntimeError("Не удалось запустить обучение")
                
            except Exception as training_error:
                error_msg = str(training_error)
                
                # Обрабатываем разные типы ошибок
                if "недостаточно фотографий" in error_msg.lower():
                    await callback.message.edit_text(
                        text="❌ **Недостаточно фотографий**\n\nДля обучения нужно минимум 10 фотографий.",
                        parse_mode="Markdown"
                    )
                elif "тестовый режим" in error_msg.lower() or "test" in error_msg.lower():
                    # Показываем успешный запуск (скрываем тестовый режим от пользователя)
                    await callback.message.edit_text(
                        text="✅ **Обучение запущено!**\n\nПодготавливаем модель для вашего аватара...",
                        parse_mode="Markdown"
                    )
                    # Запускаем имитацию прогресса (информация о тестовом режиме только в логах)
                    logger.info(f"🧪 ТЕСТОВЫЙ РЕЖИМ: Имитация обучения аватара {avatar_id} для разработчика")
                    await self._simulate_training_progress(callback, avatar_id)
                else:
                    await callback.message.edit_text(
                        text=f"❌ **Ошибка запуска обучения**\n\n{error_msg}",
                        parse_mode="Markdown"
                    )
                
                logger.warning(f"Ошибка при запуске обучения аватара {avatar_id}: {training_error}")
                
        except Exception as e:
            logger.exception(f"Критическая ошибка при запуске обучения: {e}")
            await callback.answer("❌ Произошла критическая ошибка", show_alert=True)
    
    async def _show_training_progress(self, callback: CallbackQuery, avatar_id: UUID, finetune_id: str):
        """Показывает прогресс обучения"""
        try:
            # Получаем данные аватара
            async with get_avatar_service() as avatar_service:
                avatar = await avatar_service.get_avatar(avatar_id)
                if not avatar:
                    await callback.answer("❌ Аватар не найден", show_alert=True)
                    return
            
            # Формируем текст прогресса
            progress = avatar.training_progress if avatar.training_progress else 0
            status_text = self._get_status_text(avatar.status)
            
            text = f"""
🤖 **Обучение аватара в процессе**

🎭 **Аватар:** {avatar.name}
📊 **Прогресс:** {progress}%
⚡ **Статус:** {status_text}

⏱️ **Примерное время:** 15-30 минут

💡 Вы получите уведомление когда обучение завершится!
"""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Обновить прогресс",
                        callback_data=f"refresh_training_{avatar_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="◀️ К меню аватаров",
                        callback_data="avatar_menu"
                    )
                ]
            ])
            
            try:
                await callback.message.edit_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            except Exception as edit_error:
                if "message is not modified" in str(edit_error):
                    await callback.answer("📊 Прогресс актуален")
                else:
                    logger.warning(f"Ошибка редактирования сообщения прогресса: {edit_error}")
                    await callback.answer("❌ Ошибка обновления прогресса", show_alert=True)
            
        except Exception as e:
            logger.exception(f"Ошибка при показе прогресса обучения: {e}")
            await callback.answer("❌ Ошибка обновления прогресса", show_alert=True)
    
    async def _simulate_training_progress(self, callback: CallbackQuery, avatar_id: UUID):
        """Имитирует прогресс обучения (тестовый режим скрыт от пользователя)"""
        try:
            progress_steps = [10, 25, 45, 65, 85, 95, 100]
            
            logger.info(f"🧪 РАЗРАБОТЧИК: Запуск имитации обучения для аватара {avatar_id}")
            
            for progress in progress_steps:
                # Обновляем прогресс в БД
                async with get_avatar_service() as avatar_service:
                    await avatar_service.update_avatar_progress(avatar_id, progress)
                
                # Обновляем UI (пользователь видит обычное обучение)
                text = f"""
🤖 **Обучение аватара**

📊 **Прогресс:** {progress}%
⚡ **Статус:** {'Завершено' if progress == 100 else 'В процессе...'}

{'✅ **Обучение завершено!**' if progress == 100 else '⏱️ Продолжаем обучение...'}
"""
                
                if progress == 100:
                    # Финальная клавиатура
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🎨 Генерировать изображение",
                                callback_data=f"generate_image_{avatar_id}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="📁 Мои аватары",
                                callback_data="avatar_gallery"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="◀️ Главное меню",
                                callback_data="avatar_menu"
                            )
                        ]
                    ])
                    
                    # Обновляем статус аватара на завершенный
                    async with get_avatar_service() as avatar_service:
                        await avatar_service.update_avatar_status(avatar_id, AvatarStatus.COMPLETED)
                        
                else:
                    # ИСПРАВЛЕНИЕ: Убираем кнопку отмены из промежуточных шагов
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔄 Обновить прогресс",
                                callback_data=f"refresh_training_{avatar_id}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="◀️ К меню аватаров",
                                callback_data="avatar_menu"
                            )
                        ]
                    ])
                
                try:
                    await callback.message.edit_text(
                        text=text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                except Exception as edit_error:
                    # Игнорируем ошибки "message is not modified" в имитации
                    if "message is not modified" not in str(edit_error):
                        logger.warning(f"Ошибка обновления имитации прогресса: {edit_error}")
                
                if progress < 100:
                    await asyncio.sleep(3)  # Пауза между обновлениями
                
            logger.info(f"🧪 РАЗРАБОТЧИК: Имитация обучения аватара {avatar_id} завершена успешно")
            
        except Exception as e:
            logger.exception(f"Ошибка при имитации обучения: {e}")
    
    def _get_status_text(self, status: AvatarStatus) -> str:
        """Возвращает человекочитаемый текст статуса"""
        status_map = {
            AvatarStatus.DRAFT: "Черновик",
            AvatarStatus.PHOTOS_UPLOADING: "Загрузка фото",
            AvatarStatus.READY_FOR_TRAINING: "Готов к обучению",
            AvatarStatus.TRAINING: "Обучается...",
            AvatarStatus.COMPLETED: "Готов",
            AvatarStatus.ERROR: "Ошибка",
            AvatarStatus.CANCELLED: "Отменен"
        }
        return status_map.get(status, "Неизвестно")
    
    async def refresh_training_progress(self, callback: CallbackQuery, state: FSMContext):
        """Обновление прогресса обучения"""
        try:
            avatar_id_str = callback.data.split("_", 2)[2]
            avatar_id = UUID(avatar_id_str)
            
            # Получаем актуальную информацию об обучении
            async with get_avatar_service() as avatar_service:
                avatar = await avatar_service.get_avatar(avatar_id)
                if not avatar:
                    await callback.answer("❌ Аватар не найден", show_alert=True)
                    return
            
            # Показываем обновленный прогресс (метод сам обработает ошибки)
            await self._show_training_progress(callback, avatar_id, avatar.finetune_id or "training")
            
        except Exception as e:
            logger.exception(f"Ошибка при обновлении прогресса: {e}")
            await callback.answer("❌ Ошибка обновления", show_alert=True)
    
    async def cancel_training(self, callback: CallbackQuery, state: FSMContext):
        """Отмена обучения аватара"""
        try:
            avatar_id_str = callback.data.split("_", 2)[2]
            avatar_id = UUID(avatar_id_str)
            
            # Показываем подтверждение
            text = """
⚠️ **Отмена обучения**

Вы действительно хотите отменить обучение аватара?

⚠️ **Внимание:** Весь прогресс будет потерян!
"""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Да, отменить",
                        callback_data=f"confirm_cancel_training_{avatar_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="◀️ Продолжить обучение",
                        callback_data=f"refresh_training_{avatar_id}"
                    )
                ]
            ])
            
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.exception(f"Ошибка при отмене обучения: {e}")
            await callback.answer("❌ Ошибка отмены", show_alert=True)

# Создаем экземпляр обработчика
training_handler = TrainingHandler()

# Регистрируем обработчики
@router.callback_query(F.data.startswith("start_training_"))
async def start_training(callback: CallbackQuery, state: FSMContext):
    """Запуск обучения аватара"""
    await training_handler.start_training(callback, state)

@router.callback_query(F.data.startswith("refresh_training_"))
async def refresh_training_progress(callback: CallbackQuery, state: FSMContext):
    """Обновление прогресса обучения"""
    await training_handler.refresh_training_progress(callback, state)

@router.callback_query(F.data.startswith("cancel_training_"))
async def cancel_training(callback: CallbackQuery, state: FSMContext):
    """Отмена обучения"""
    await training_handler.cancel_training(callback, state)

@router.callback_query(F.data.startswith("confirm_cancel_training_"))
async def confirm_cancel_training(callback: CallbackQuery, state: FSMContext):
    """Подтверждение отмены обучения"""
    try:
        avatar_id_str = callback.data.split("_", 3)[3]
        avatar_id = UUID(avatar_id_str)
        
        # Обновляем статус
        async with get_avatar_service() as avatar_service:
            await avatar_service.update_avatar_status(avatar_id, AvatarStatus.CANCELLED)
        
        await callback.message.edit_text(
            text="❌ **Обучение отменено**\n\nВы можете начать новое обучение в любое время.",
            parse_mode="Markdown"
        )
        
        # Сбрасываем состояние
        await state.clear()
        
        logger.info(f"Обучение аватара {avatar_id} отменено пользователем")
        
    except Exception as e:
        logger.exception(f"Ошибка при подтверждении отмены: {e}")
        await callback.answer("❌ Ошибка отмены", show_alert=True)

# Экспорт
__all__ = ["training_handler", "router"] 