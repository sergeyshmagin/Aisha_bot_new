"""
Обработчики для работы с аватарами (Фаза 3: FAL AI интеграция)
"""
import asyncio
from typing import Optional
from uuid import UUID, uuid4
import io

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, PhotoSize
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from ..core.config import settings
from ..core.logger import get_logger
from ..database.connection import get_session_dependency
from .state import AvatarStates
from ..keyboards.avatar import (
    get_avatar_main_menu, get_avatar_type_keyboard, get_gender_keyboard,
    get_photo_upload_keyboard, get_training_confirmation_keyboard,
    get_photo_gallery_keyboard, get_training_progress_keyboard
)
from ..texts.avatar import AvatarTexts
from ..database.models import AvatarType, AvatarGender, AvatarStatus
from ..services.avatar.avatar_service import AvatarService
from ..services.avatar.photo_service import PhotoUploadService
from ..services.avatar.training_service import AvatarTrainingService
from ..services.user import UserService

logger = get_logger(__name__)
router = Router()


class AvatarHandler:
    """
    Обработчик для создания и управления аватарами.
    
    Фаза 3 включает:
    - Интеграцию с FAL AI для обучения
    - Мониторинг прогресса обучения
    - Управление статусами аватаров
    - Обработку ошибок обучения
    """

    def __init__(self):
        self.texts = AvatarTexts()

    async def get_services(self):
        """Получает сервисы для работы с базой данных"""
        session = await get_session_dependency()
        return {
            'user_service': UserService(),
            'avatar_service': AvatarService(session),
            'photo_service': PhotoUploadService(session),
            'training_service': AvatarTrainingService(session),
            'session': session
        }

    async def register_handlers(self):
        """Регистрация обработчиков аватаров"""
        logger.info("Регистрация обработчиков аватаров (Фаза 3: FAL AI)")
        
        # === ОСНОВНОЕ МЕНЮ ===
        router.callback_query.register(
            self.show_avatar_menu,
            F.data == "avatar_menu"
        )
        
        # === СОЗДАНИЕ АВАТАРА ===
        router.callback_query.register(
            self.start_avatar_creation,
            F.data == "avatar_create"
        )
        
        router.callback_query.register(
            self.select_avatar_type,
            F.data.startswith("avatar_type_")
        )
        
        router.callback_query.register(
            self.select_gender,
            F.data.startswith("avatar_gender_")
        )
        
        router.message.register(
            self.process_avatar_name,
            StateFilter(AvatarStates.entering_name),
            F.text
        )
        
        # === ПРОСМОТР АВАТАРОВ ===
        router.callback_query.register(
            self.show_avatar_gallery,
            F.data == "avatar_gallery"
        )
        
        # === ЗАГРУЗКА ФОТОГРАФИЙ ===
        router.callback_query.register(
            self.start_photo_upload,
            F.data == "avatar_add_photos"
        )
        
        router.message.register(
            self.process_photo_upload,
            StateFilter(AvatarStates.uploading_photos),
            F.photo
        )
        
        # === ОБУЧЕНИЕ АВАТАРОВ (НОВОЕ В ФАЗЕ 3) ===
        router.callback_query.register(
            self.confirm_training,
            F.data == "avatar_photos_ready"
        )
        
        router.callback_query.register(
            self.start_training,
            F.data.startswith("avatar_start_training_")
        )
        
        router.callback_query.register(
            self.show_training_progress,
            F.data.startswith("avatar_training_progress_")
        )
        
        router.callback_query.register(
            self.cancel_training,
            F.data.startswith("avatar_cancel_training_")
        )
        
        # === НАЗАД И ОТМЕНА ===
        router.callback_query.register(
            self.handle_back,
            F.data.in_(["back_to_main", "avatar_menu_back"])
        )

    async def show_avatar_menu(self, call: CallbackQuery, state: FSMContext):
        """Показывает главное меню аватаров"""
        try:
            services = await self.get_services()
            user_service = services['user_service']
            avatar_service = services['avatar_service']
            
            user = await user_service.get_user_by_telegram_id(str(call.from_user.id))
            
            if not user:
                await call.answer("❌ Пользователь не найден", show_alert=True)
                return
            
            # Получаем реальное количество аватаров пользователя
            user_avatars = await avatar_service.get_user_avatars(user.id)
            avatars_count = len(user_avatars)
            
            await state.set_state(AvatarStates.menu)
            
            keyboard = get_avatar_main_menu(avatars_count)
            text = self.texts.get_main_menu_text(avatars_count)
            
            await call.message.edit_text(text, reply_markup=keyboard)
            await call.answer()
            
            logger.info(f"Показано меню аватаров пользователю {user.id}, аватаров: {avatars_count}")
            
        except Exception as e:
            logger.exception(f"Ошибка при показе меню аватаров: {e}")
            await call.answer("❌ Произошла ошибка", show_alert=True)

    async def start_avatar_creation(self, call: CallbackQuery, state: FSMContext):
        """Начинает процесс создания аватара"""
        try:
            await state.set_state(AvatarStates.selecting_type)
            
            keyboard = get_avatar_type_keyboard()
            text = self.texts.get_type_selection_text()
            
            await call.message.edit_text(text, reply_markup=keyboard)
            await call.answer()
            
            logger.info(f"Начато создание аватара пользователем {call.from_user.id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при начале создания аватара: {e}")
            await call.answer("❌ Произошла ошибка", show_alert=True)

    async def select_avatar_type(self, call: CallbackQuery, state: FSMContext):
        """Обрабатывает выбор типа аватара"""
        try:
            avatar_type_str = call.data.split("avatar_type_")[1]
            avatar_type = AvatarType(avatar_type_str)
            
            # Сохраняем выбранный тип
            await state.update_data(avatar_type=avatar_type)
            await state.set_state(AvatarStates.selecting_gender)
            
            keyboard = get_gender_keyboard()
            text = self.texts.get_gender_selection_text(avatar_type)
            
            await call.message.edit_text(text, reply_markup=keyboard)
            await call.answer()
            
            logger.info(f"Выбран тип аватара: {avatar_type.value}")
            
        except Exception as e:
            logger.exception(f"Ошибка при выборе типа аватара: {e}")
            await call.answer("❌ Произошла ошибка", show_alert=True)

    async def select_gender(self, call: CallbackQuery, state: FSMContext):
        """Обрабатывает выбор пола аватара"""
        try:
            gender_str = call.data.split("avatar_gender_")[1]
            gender = AvatarGender(gender_str)
            
            # Сохраняем выбранный пол
            await state.update_data(gender=gender)
            await state.set_state(AvatarStates.entering_name)
            
            text = self.texts.get_name_input_text(gender)
            
            # Убираем клавиатуру для ввода текста
            await call.message.edit_text(text, reply_markup=None)
            await call.answer()
            
            logger.info(f"Выбран пол аватара: {gender.value}")
            
        except Exception as e:
            logger.exception(f"Ошибка при выборе пола аватара: {e}")
            await call.answer("❌ Произошла ошибка", show_alert=True)

    async def process_avatar_name(self, message: Message, state: FSMContext):
        """Обрабатывает ввод имени аватара"""
        try:
            name = message.text.strip()
            
            # Валидируем имя
            if len(name) < 2:
                await message.reply("❌ Имя должно содержать минимум 2 символа")
                return
            
            if len(name) > 50:
                await message.reply("❌ Имя не может быть длиннее 50 символов")
                return
            
            # Получаем данные из состояния
            data = await state.get_data()
            avatar_type = data.get('avatar_type')
            gender = data.get('gender')
            
            if not avatar_type or not gender:
                await message.reply("❌ Ошибка: потеряны данные о типе или поле. Начните заново.")
                await state.clear()
                return
            
            # Получаем сервисы
            services = await self.get_services()
            user_service = services['user_service']
            avatar_service = services['avatar_service']
            
            user = await user_service.get_user_by_telegram_id(str(message.from_user.id))
            
            if not user:
                await message.reply("❌ Пользователь не найден")
                return
            
            # Создаем реальный аватар в базе данных
            try:
                avatar = await avatar_service.create_avatar(
                    user_id=user.id,
                    name=name,
                    avatar_type=avatar_type,
                    gender=gender
                )
                
                # Сохраняем ID реального аватара в состояние
                await state.update_data(avatar_id=str(avatar.id), name=name)
                await state.set_state(AvatarStates.uploading_photos)
                
                text = self.texts.get_photo_upload_text(name, 0, settings.AVATAR_MIN_PHOTOS)
                keyboard = get_photo_upload_keyboard(0, settings.AVATAR_MIN_PHOTOS, settings.AVATAR_MAX_PHOTOS)
                
                await message.reply(text, reply_markup=keyboard)
                
                logger.info(f"Создан аватар '{name}' (ID: {avatar.id}) для пользователя {user.id}")
                
            except ValueError as e:
                # Обрабатываем ошибки валидации (лимиты, дубликаты имен)
                await message.reply(f"❌ {str(e)}")
                logger.warning(f"Ошибка создания аватара для {user.id}: {e}")
                
        except Exception as e:
            logger.exception(f"Ошибка при обработке имени аватара: {e}")
            await message.reply("❌ Произошла ошибка при создании аватара")

    async def start_photo_upload(self, call: CallbackQuery, state: FSMContext):
        """Начинает процесс загрузки фотографий"""
        try:
            await state.set_state(AvatarStates.uploading_photos)
            
            text = self.texts.get_photo_upload_instruction_text()
            
            await call.message.edit_text(text, reply_markup=None)
            await call.answer()
            
            logger.info(f"Начата загрузка фотографий пользователем {call.from_user.id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при начале загрузки фотографий: {e}")
            await call.answer("❌ Произошла ошибка", show_alert=True)

    async def process_photo_upload(self, message: Message, state: FSMContext):
        """Обрабатывает загрузку фотографии"""
        try:
            data = await state.get_data()
            avatar_id = data.get('avatar_id')
            name = data.get('name', 'Аватар')
            
            if not avatar_id:
                await message.reply("❌ Ошибка: аватар не найден. Начните заново.")
                await state.clear()
                return
            
            # Получаем сервисы
            services = await self.get_services()
            user_service = services['user_service']
            photo_service = services['photo_service']
            
            user = await user_service.get_user_by_telegram_id(str(message.from_user.id))
            
            if not user:
                await message.reply("❌ Пользователь не найден")
                return
            
            # Получаем самое большое фото
            photo = message.photo[-1]  # Последнее фото - самое большое
            
            # Отправляем сообщение о начале загрузки
            loading_msg = await message.reply("⏳ Загружаю фотографию...")
            
            try:
                # Получаем файл из Telegram
                bot = Bot.get_current()
                file = await bot.get_file(photo.file_id)
                
                # Скачиваем данные фотографии
                photo_data = await bot.download_file(file.file_path)
                photo_bytes = photo_data.read()
                
                # Загружаем фотографию через PhotoUploadService
                avatar_photo = await photo_service.upload_photo(
                    avatar_id=UUID(avatar_id),
                    user_id=user.id,
                    photo_data=photo_bytes,
                    filename=f"photo_{photo.file_id}.jpg"
                )
                
                # Получаем текущее количество фотографий
                photos, total_count = await photo_service.get_avatar_photos(UUID(avatar_id))
                
                # Обновляем сообщение о загрузке
                await loading_msg.edit_text(f"✅ Фотография {total_count} загружена успешно!")
                
                # Обновляем интерфейс
                text = self.texts.get_photo_upload_text(name, total_count, settings.AVATAR_MIN_PHOTOS)
                keyboard = get_photo_upload_keyboard(total_count, settings.AVATAR_MIN_PHOTOS, settings.AVATAR_MAX_PHOTOS)
                
                await message.reply(text, reply_markup=keyboard)
                
                logger.info(f"Загружена фотография {total_count} для аватара {avatar_id}")
                
            except ValueError as e:
                # Ошибки валидации (размер, формат, дубликаты, лимиты)
                await loading_msg.edit_text(f"❌ {str(e)}")
                logger.warning(f"Ошибка валидации фотографии для аватара {avatar_id}: {e}")
                
            except Exception as e:
                # Другие ошибки (сеть, MinIO, база данных)
                await loading_msg.edit_text("❌ Ошибка при загрузке фотографии. Попробуйте еще раз.")
                logger.exception(f"Ошибка при загрузке фотографии для аватара {avatar_id}: {e}")
                
        except Exception as e:
            logger.exception(f"Критическая ошибка при обработке загрузки фотографии: {e}")
            await message.reply("❌ Произошла критическая ошибка")

    async def confirm_training(self, call: CallbackQuery, state: FSMContext):
        """Показывает подтверждение начала обучения"""
        try:
            data = await state.get_data()
            avatar_id = data.get('avatar_id')
            name = data.get('name', 'Аватар')
            
            if not avatar_id:
                await call.answer("❌ Ошибка: аватар не найден", show_alert=True)
                return
            
            # Получаем сервисы
            services = await self.get_services()
            photo_service = services['photo_service']
            
            # Получаем реальное количество фотографий
            photos, photos_count = await photo_service.get_avatar_photos(UUID(avatar_id))
            
            await state.set_state(AvatarStates.confirming_training)
            
            text = self.texts.get_training_confirmation_text(name, photos_count)
            keyboard = get_training_confirmation_keyboard(avatar_id)
            
            await call.message.edit_text(text, reply_markup=keyboard)
            await call.answer()
            
            logger.info(f"Показано подтверждение обучения для аватара {avatar_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при подтверждении обучения: {e}")
            await call.answer("❌ Произошла ошибка", show_alert=True)

    async def start_training(self, call: CallbackQuery, state: FSMContext):
        """Запускает обучение аватара"""
        try:
            # Извлекаем avatar_id из callback data
            avatar_id_str = call.data.split("avatar_start_training_")[1]
            avatar_id = UUID(avatar_id_str)
            
            # Получаем сервисы
            services = await self.get_services()
            training_service = services['training_service']
            avatar_service = services['avatar_service']
            
            # Получаем аватар для проверки прав пользователя
            avatar = await avatar_service.get_avatar_by_id(avatar_id)
            if not avatar:
                await call.answer("❌ Аватар не найден", show_alert=True)
                return
            
            # Проверяем права пользователя (опционально - можно добавить проверку user_id)
            
            # Показываем сообщение о запуске
            loading_msg = await call.message.edit_text(
                "🚀 Запускаю обучение аватара...\n"
                "Это может занять несколько минут.",
                reply_markup=None
            )
            
            try:
                # Запускаем обучение
                success = await training_service.start_training(avatar_id)
                
                if success:
                    # Успешный запуск
                    text = (
                        f"✅ Обучение аватара '{avatar.name}' запущено!\n\n"
                        "📊 Процесс может занять от 15 до 60 минут.\n"
                        "💬 Я уведомлю вас о завершении.\n"
                        "📈 Вы можете отслеживать прогресс в любое время."
                    )
                    
                    keyboard = get_training_progress_keyboard(str(avatar_id))
                    await loading_msg.edit_text(text, reply_markup=keyboard)
                    
                    # Очищаем состояние FSM
                    await state.clear()
                    
                    logger.info(f"Запущено обучение аватара {avatar_id}")
                    
                else:
                    # Ошибка запуска
                    await loading_msg.edit_text(
                        "❌ Не удалось запустить обучение.\n"
                        "Попробуйте еще раз или обратитесь в поддержку.",
                        reply_markup=get_avatar_main_menu(1)
                    )
                
            except ValueError as e:
                # Ошибки валидации (недостаточно фото, неправильный статус и т.д.)
                await loading_msg.edit_text(
                    f"❌ {str(e)}\n\n"
                    "Проверьте количество загруженных фотографий и попробуйте снова.",
                    reply_markup=get_avatar_main_menu(1)
                )
                logger.warning(f"Ошибка валидации при запуске обучения {avatar_id}: {e}")
                
            except Exception as e:
                # Критические ошибки
                await loading_msg.edit_text(
                    "❌ Произошла техническая ошибка при запуске обучения.\n"
                    "Мы уже работаем над исправлением.",
                    reply_markup=get_avatar_main_menu(1)
                )
                logger.exception(f"Критическая ошибка при запуске обучения {avatar_id}: {e}")
            
            await call.answer()
            
        except Exception as e:
            logger.exception(f"Ошибка в обработчике запуска обучения: {e}")
            await call.answer("❌ Произошла ошибка", show_alert=True)

    async def show_training_progress(self, call: CallbackQuery, state: FSMContext):
        """Показывает прогресс обучения аватара"""
        try:
            # Извлекаем avatar_id из callback data
            avatar_id_str = call.data.split("avatar_training_progress_")[1]
            avatar_id = UUID(avatar_id_str)
            
            # Получаем сервисы
            services = await self.get_services()
            training_service = services['training_service']
            
            # Получаем информацию о прогрессе
            progress_info = await training_service.get_training_progress(avatar_id)
            
            # Формируем текст с прогрессом
            text = self.texts.get_training_progress_text(progress_info)
            
            # Формируем клавиатуру в зависимости от статуса
            status = progress_info.get("status")
            if status in ["training", "ready"]:
                keyboard = get_training_progress_keyboard(avatar_id_str, show_cancel=True)
            else:
                keyboard = get_training_progress_keyboard(avatar_id_str, show_cancel=False)
            
            await call.message.edit_text(text, reply_markup=keyboard)
            await call.answer()
            
            logger.info(f"Показан прогресс обучения аватара {avatar_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при показе прогресса обучения: {e}")
            await call.answer("❌ Ошибка получения прогресса", show_alert=True)

    async def cancel_training(self, call: CallbackQuery, state: FSMContext):
        """Отменяет обучение аватара"""
        try:
            # Извлекаем avatar_id из callback data
            avatar_id_str = call.data.split("avatar_cancel_training_")[1]
            avatar_id = UUID(avatar_id_str)
            
            # Получаем сервисы
            services = await self.get_services()
            training_service = services['training_service']
            
            # Показываем подтверждение отмены
            confirmation_text = (
                "⚠️ Вы уверены, что хотите отменить обучение?\n\n"
                "После отмены потребуется запустить процесс заново."
            )
            
            # TODO: Добавить клавиатуру подтверждения отмены
            # Пока просто отменяем сразу
            
            try:
                success = await training_service.cancel_training(avatar_id)
                
                if success:
                    await call.message.edit_text(
                        "✅ Обучение отменено.\n\n"
                        "Вы можете запустить его заново в любое время.",
                        reply_markup=get_avatar_main_menu(1)
                    )
                    logger.info(f"Отменено обучение аватара {avatar_id}")
                else:
                    await call.message.edit_text(
                        "❌ Не удалось отменить обучение.\n"
                        "Возможно, оно уже завершено.",
                        reply_markup=get_training_progress_keyboard(avatar_id_str)
                    )
                
            except ValueError as e:
                await call.message.edit_text(
                    f"❌ {str(e)}",
                    reply_markup=get_training_progress_keyboard(avatar_id_str)
                )
                
            await call.answer()
            
        except Exception as e:
            logger.exception(f"Ошибка при отмене обучения: {e}")
            await call.answer("❌ Ошибка отмены обучения", show_alert=True)

    async def show_avatar_gallery(self, call: CallbackQuery, state: FSMContext):
        """Показывает галерею аватаров пользователя"""
        try:
            await state.set_state(AvatarStates.avatar_gallery)
            
            # Получаем сервисы
            services = await self.get_services()
            user_service = services['user_service']
            avatar_service = services['avatar_service']
            
            user = await user_service.get_user_by_telegram_id(str(call.from_user.id))
            
            if not user:
                await call.answer("❌ Пользователь не найден", show_alert=True)
                return
            
            # Получаем реальные аватары пользователя
            user_avatars = await avatar_service.get_user_avatars(user.id)
            avatars_count = len(user_avatars)
            
            text = self.texts.get_gallery_text(avatars_count)
            
            if avatars_count > 0:
                # TODO: Реализовать пагинацию для галереи аватаров
                # Пока возвращаемся к главному меню
                keyboard = get_avatar_main_menu(avatars_count)
            else:
                keyboard = get_avatar_main_menu(0)
            
            await call.message.edit_text(text, reply_markup=keyboard)
            await call.answer()
            
            logger.info(f"Показана галерея аватаров пользователю {call.from_user.id}, аватаров: {avatars_count}")
            
        except Exception as e:
            logger.exception(f"Ошибка при показе галереи аватаров: {e}")
            await call.answer("❌ Произошла ошибка", show_alert=True)

    async def handle_back(self, call: CallbackQuery, state: FSMContext):
        """Обрабатывает возврат назад"""
        try:
            await state.clear()
            
            # Импортируем здесь чтобы избежать циклических импортов
            from ..keyboards.main import get_main_menu
            from ..texts.main import MainTexts
            
            main_texts = MainTexts()
            text = main_texts.get_welcome_text()
            keyboard = get_main_menu()
            
            await call.message.edit_text(text, reply_markup=keyboard)
            await call.answer()
            
            logger.info(f"Возврат в главное меню от пользователя {call.from_user.id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при возврате назад: {e}")
            await call.answer("❌ Произошла ошибка", show_alert=True)


# Создаем экземпляр обработчика
avatar_handler = AvatarHandler()

# Регистрируем обработчики при импорте модуля
async def register_avatar_handlers():
    """Функция для регистрации обработчиков"""
    await avatar_handler.register_handlers()
