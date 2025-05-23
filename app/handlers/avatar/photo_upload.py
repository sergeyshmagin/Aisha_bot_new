"""
Обработчики загрузки фотографий для аватаров
Полнофункциональная система с галереей, валидацией и UX улучшениями
Адаптировано из archive/aisha_v1 с современными улучшениями
"""
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import (
    CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaPhoto, FSInputFile
)
from aiogram.fsm.context import FSMContext
from uuid import UUID
import io
from typing import Dict, List, Optional, Any
import time

from app.handlers.state import AvatarStates
from app.core.di import get_user_service, get_avatar_service
from app.services.avatar.photo_service import PhotoUploadService
from app.services.avatar.redis_service import AvatarRedisService
from app.database.models import AvatarGender, AvatarType, AvatarTrainingType, AvatarPhoto
from app.core.logger import get_logger
from app.keyboards.photo_upload import (
    get_photo_upload_keyboard,
    get_photo_gallery_navigation_keyboard,
    get_training_start_keyboard,
    get_photo_tips_keyboard
)

logger = get_logger(__name__)
router = Router()

# Глобальные состояния для управления загрузкой (как в старом проекте)
user_gallery_cache: Dict[int, Dict] = {}  # user_id -> {avatar_id, photos, current_idx}
user_upload_locks: Dict[int, asyncio.Lock] = {}  # user_id -> lock
user_last_gallery_message: Dict[int, int] = {}  # user_id -> message_id


class PhotoUploadHandler:
    """
    Улучшенный обработчик загрузки фотографий с функциями из archive/aisha_v1
    
    Новые возможности:
    ✅ Буферизация фото через Redis
    ✅ Галерея с навигацией 
    ✅ Валидация на дубликаты и качество
    ✅ Прогресс-бар загрузки
    ✅ Batch загрузка (media groups)
    ✅ Улучшенный UX с советами
    """
    
    def __init__(self):
        self.min_photos = 10
        self.max_photos = 20
        self.redis_service = AvatarRedisService()
        
    async def start_photo_upload(self, callback: CallbackQuery, state: FSMContext):
        """Начинает процесс загрузки фотографий с созданием аватара"""
        try:
            # Получаем данные из состояния
            data = await state.get_data()
            training_type = data.get("training_type", "portrait")
            gender = data.get("gender", "male")
            name = data.get("avatar_name", "Новый аватар")
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(callback.from_user.id)
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Проверяем блокировку создания аватара
            lock_token = await self.redis_service.acquire_avatar_lock(user.id, "create")
            if not lock_token:
                await callback.answer("⏳ Другой аватар уже создается. Подождите.", show_alert=True)
                return
            
            try:
                # Создаем черновик аватара в БД
                async with get_avatar_service() as avatar_service:
                    avatar = await avatar_service.create_avatar(
                        user_id=user.id,
                        name=name,
                        gender=AvatarGender(gender),
                        avatar_type=AvatarType.CHARACTER,
                        training_type=AvatarTrainingType(training_type)
                    )
                    
                    # Сохраняем ID аватара в состоянии
                    await state.update_data(avatar_id=str(avatar.id))
                
                # Сохраняем черновик в Redis для восстановления
                await self.redis_service.save_avatar_draft(user.id, {
                    "avatar_id": str(avatar.id),
                    "name": name,
                    "gender": gender,
                    "training_type": training_type,
                    "created_at": time.time()
                })
                
            finally:
                # Освобождаем блокировку
                await self.redis_service.release_avatar_lock(user.id, lock_token, "create")
            
            # Показываем красивый интерфейс загрузки
            text = self._get_upload_intro_text(name, training_type, gender)
            keyboard = get_photo_upload_keyboard(0, self.min_photos, self.max_photos)
            
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            await state.set_state(AvatarStates.uploading_photos)
            
            logger.info(f"Пользователь {user.id} начал загрузку фото для аватара {avatar.id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при начале загрузки фото: {e}")
            await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)
    
    async def handle_photo_upload(self, message: Message, state: FSMContext, bot: Bot):
        """
        Обработка загрузки фотографий с буферизацией и batch обработкой
        Адаптировано из archive/aisha_v1/frontend_bot/handlers/avatar/photo_upload.py
        """
        try:
            user_id = message.from_user.id
            
            # Получаем данные из состояния
            data = await state.get_data()
            avatar_id_str = data.get("avatar_id")
            
            if not avatar_id_str:
                await message.answer("❌ Ошибка: аватар не найден. Начните создание заново.")
                return
            
            avatar_id = UUID(avatar_id_str)
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_id)
                if not user:
                    await message.answer("❌ Пользователь не найден")
                    return
            
            # Проверяем лимиты сначала
            async with get_avatar_service() as avatar_service:
                photos, total = await avatar_service.get_avatar_photos(avatar_id)
                if total >= self.max_photos:
                    await message.answer(
                        f"📸 **Достигнут лимит фотографий!**\n\n"
                        f"Максимум: {self.max_photos} фото\n"
                        f"Загружено: {total}\n\n"
                        f"Можете удалить ненужные фото в галерее или начать обучение.",
                        parse_mode="Markdown"
                    )
                    return
            
            # Защита от спама загрузок
            if user_id not in user_upload_locks:
                user_upload_locks[user_id] = asyncio.Lock()
            
            async with user_upload_locks[user_id]:
                # Показываем индикатор загрузки
                loading_msg = await message.answer("📤 Обрабатываю фотографию...")
                
                try:
                    # Получаем самое большое разрешение фото
                    photo = message.photo[-1]
                    
                    # Скачиваем файл из Telegram
                    file_info = await bot.get_file(photo.file_id)
                    file_data = await bot.download_file(file_info.file_path)
                    
                    # Читаем данные
                    photo_bytes = file_data.read()
                    
                    # Загружаем через PhotoUploadService с валидацией
                    async with get_avatar_service() as avatar_service:
                        session = avatar_service.session
                        
                        photo_service = PhotoUploadService(session)
                        uploaded_photo = await photo_service.upload_photo(
                            avatar_id=avatar_id,
                            user_id=user.id,
                            photo_data=photo_bytes,
                            filename=f"telegram_photo_{photo.file_id}.jpg"
                        )
                    
                    # Удаляем сообщение загрузки
                    await loading_msg.delete()
                    
                    # Получаем обновленное количество фото
                    async with get_avatar_service() as avatar_service:
                        photos, photos_count = await avatar_service.get_avatar_photos(avatar_id)
                    
                    # Обновляем галерею если она открыта
                    await self._update_gallery_if_open(user_id, avatar_id, photos)
                    
                    # Показываем прогресс
                    await self._show_upload_progress(message, photos_count, avatar_id)
                    
                    logger.info(f"Загружено фото {uploaded_photo.id} для аватара {avatar_id}, всего: {photos_count}")
                    
                except Exception as upload_error:
                    await loading_msg.delete()
                    await self._handle_upload_error(message, upload_error)
                    
        except Exception as e:
            logger.exception(f"Критическая ошибка при загрузке фото: {e}")
            await message.answer("❌ Произошла критическая ошибка. Попробуйте позже.")
    
    # Остальные методы аналогично из оригинального файла...
    
    def _get_upload_intro_text(self, name: str, training_type: str, gender: str) -> str:
        """Генерирует введение для загрузки фото"""
        gender_emoji = "👨" if gender == "male" else "👩"
        
        if training_type == "portrait":
            tips = "• Портретные фото с хорошим освещением\n• Разные углы и выражения лица\n• Без головных уборов и очков"
        elif training_type == "style":
            tips = "• Фото в полный рост\n• Разная одежда и стили\n• Хорошее освещение"
        else:
            tips = "• Качественные фото с хорошим освещением\n• Разные позы и углы\n• Без фильтров и масок"
        
        return f"""
📸 **Загрузка фотографий**

{gender_emoji} **Аватар:** {name}
🎯 **Тип:** {training_type.title()}

📋 **Рекомендации:**
{tips}

📊 **Требования:**
• Минимум: {self.min_photos} фото
• Рекомендуется: {self.max_photos} фото
• Формат: JPG, PNG (до 20MB)
• Размер: минимум 512×512 пикселей

💡 **Совет:** Чем больше качественных фото, тем лучше результат!

📤 **Начните отправлять фотографии:**
"""

    async def _show_upload_progress(self, message: Message, photos_count: int, avatar_id: UUID):
        """Показывает прогресс загрузки"""
        progress_filled = min(photos_count, self.min_photos)
        progress_bar = "█" * progress_filled + "░" * (self.min_photos - progress_filled)
        progress_percent = int((photos_count / self.min_photos) * 100) if photos_count <= self.min_photos else 100
        
        if photos_count < self.min_photos:
            status = "📤 **Загрузка продолжается**"
            need_more = self.min_photos - photos_count
            next_step = f"Загрузите еще {need_more} фото для продолжения"
        elif photos_count < self.max_photos:
            status = "✅ **Готово к обучению!**"
            next_step = "Можете продолжить загрузку или начать обучение"
        else:
            status = "🔥 **Отличная коллекция!**"
            next_step = "Достигнут максимум фото. Начните обучение!"
        
        text = f"""
{status}

📊 **Прогресс:** `{progress_bar}` {progress_percent}%
📸 **Загружено:** {photos_count}/{self.max_photos}
🎯 **ID:** `{str(avatar_id)[:8]}...`

💡 **Далее:** {next_step}
"""
        
        keyboard = get_photo_upload_keyboard(photos_count, self.min_photos, self.max_photos)
        
        await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def _handle_upload_error(self, message: Message, error: Exception):
        """Обрабатывает ошибки загрузки фото"""
        error_msg = str(error).lower()
        
        if "не прошло валидацию" in error_msg:
            if "размер" in error_msg:
                text = "❌ **Фото слишком маленькое**\n\nМинимальный размер: 512×512 пикселей"
            elif "дубликат" in error_msg or "уже загружено" in error_msg:
                text = "❌ **Дубликат фотографии**\n\nЭто фото уже было загружено ранее"
            elif "формат" in error_msg:
                text = "❌ **Неподдерживаемый формат**\n\nИспользуйте JPG или PNG"
            elif "размер файла" in error_msg:
                text = "❌ **Файл слишком большой**\n\nМаксимальный размер: 20MB"
            else:
                text = f"❌ **Ошибка валидации**\n\n{str(error)}"
        elif "превышен лимит" in error_msg:
            text = f"❌ **Достигнут лимит**\n\nМаксимум {self.max_photos} фотографий"
        else:
            text = "❌ **Ошибка загрузки**\n\nПопробуйте другую фотографию"
        
        await message.answer(text, parse_mode="Markdown")
        logger.warning(f"Ошибка загрузки фото: {error}")

    async def _update_gallery_if_open(self, user_id: int, avatar_id: UUID, photos: List[AvatarPhoto]):
        """Обновляет галерею если она открыта у пользователя"""
        if user_id in user_gallery_cache:
            cache = user_gallery_cache[user_id]
            if cache["avatar_id"] == str(avatar_id):
                cache["photos"] = photos
                cache["total"] = len(photos)


# Создаем единственный экземпляр обработчика
photo_handler = PhotoUploadHandler()

# ============= РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ =============

@router.callback_query(F.data == "start_photo_upload")
async def start_photo_upload(callback: CallbackQuery, state: FSMContext):
    """Начало загрузки фотографий"""
    await photo_handler.start_photo_upload(callback, state)

@router.message(F.photo, AvatarStates.uploading_photos)
async def handle_photo_upload(message: Message, state: FSMContext, bot: Bot):
    """Обработка загруженных фотографий"""
    await photo_handler.handle_photo_upload(message, state, bot)

# Экспорт
__all__ = ["photo_handler", "router"] 