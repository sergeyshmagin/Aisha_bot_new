"""
Обработчики создания аватаров
Упрощенный workflow: Автоматическая портретная модель → Пол → Имя → Загрузка фото
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.keyboards.avatar_clean import get_avatar_gender_keyboard, get_avatar_main_menu
from app.handlers.state import AvatarStates
from app.core.logger import get_logger

logger = get_logger(__name__)
router = Router()

@router.callback_query(F.data == "create_avatar")
async def start_avatar_creation(callback: CallbackQuery, state: FSMContext):
    """Начинает создание аватара с упрощенным workflow - сразу портретная модель"""
    try:
        logger.info(f"[CREATE_AVATAR] Получен callback create_avatar от пользователя {callback.from_user.id}")
        
        # Автоматически устанавливаем портретную модель как лучший выбор
        await state.update_data(training_type="portrait")
        
        # Показываем приветствие и сразу переходим к выбору пола
        text = """
🎭 **Создание AI аватара** ⭐

**Мы выбрали для вас лучшую модель - Портретную!**

✨ **Что вы получите:**
• Высококачественные портреты с детализацией лица
• Автоматическая оптимизация для людей
• Быстрое обучение (3-15 минут)
• Превосходное качество для селфи и фото

🚀 **Процесс создания:**
1. ✅ Модель: Портретная (уже выбрана)
2. 👥 Выберите пол для оптимизации
3. 📝 Придумайте имя аватара  
4. 📸 Загрузите 10-20 фотографий
5. 🎯 Запустите обучение

Давайте начнём! Выберите пол для оптимизации модели:
"""
        
        keyboard = get_avatar_gender_keyboard()
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await state.set_state(AvatarStates.selecting_gender)
        
        logger.info(f"[CREATE_AVATAR] Пользователь {callback.from_user.id} начал упрощенное создание аватара")
        
    except Exception as e:
        logger.exception(f"[CREATE_AVATAR] Ошибка при начале создания аватара: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

@router.callback_query(F.data == "select_gender")
async def show_gender_selection(callback: CallbackQuery, state: FSMContext):
    """Показывает выбор пола аватара"""
    try:
        text = """
🎯 **Выберите пол аватара**

Это поможет настроить оптимальные параметры генерации.
"""
        
        keyboard = get_avatar_gender_keyboard()
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard
        )
        await state.set_state(AvatarStates.selecting_gender)
        
        logger.info(f"Пользователь {callback.from_user.id} перешел к выбору пола")
        
    except Exception as e:
        logger.exception(f"Ошибка при показе выбора пола: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

@router.callback_query(F.data.startswith("avatar_gender_"))
async def select_avatar_gender(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора пола аватара"""
    try:
        gender = callback.data.split("_", 2)[2]  # male, female
        
        # Валидируем пол (только мужской и женский)
        if gender not in ["male", "female"]:
            await callback.answer("❌ Неизвестный пол", show_alert=True)
            return
        
        # Сохраняем в состоянии
        await state.update_data(gender=gender)
        
        # Показываем запрос имени
        text = """
📝 **Введите имя аватара**

Придумайте уникальное имя для вашего аватара:

✅ **Требования:**
• От 2 до 50 символов
• Любые буквы и цифры
• Пробелы разрешены

💡 **Примеры:** Алексей, Maya, Cyber Alex, Анна-Мария

✍️ **Напишите имя:**
"""
        
        await callback.message.edit_text(
            text=text
        )
        
        await state.set_state(AvatarStates.entering_name)
        
        logger.info(f"Пользователь {callback.from_user.id} выбрал пол: {gender}")
        
    except Exception as e:
        logger.exception(f"Ошибка при выборе пола аватара: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

@router.message(AvatarStates.entering_name)
async def process_avatar_name(message: Message, state: FSMContext):
    """Обработка ввода имени аватара - принимает любые символы"""
    try:
        # Проверяем, что пользователь отправил текстовое сообщение
        if not message.text:
            await message.answer(
                "❌ Пожалуйста, отправьте имя аватара текстом.\n"
                "Не используйте стикеры, фото или другие файлы."
            )
            return
            
        name = message.text.strip()
        
        # Простая валидация - только длина
        if not name:
            await message.answer("❌ Имя не может быть пустым. Попробуйте еще раз:")
            return
            
        if len(name) < 2:
            await message.answer("❌ Имя слишком короткое. Минимум 2 символа:")
            return
            
        if len(name) > 50:
            await message.answer("❌ Имя слишком длинное. Максимум 50 символов:")
            return
        
        # ✅ Никаких ограничений на символы - принимаем любые буквы и цифры
        await state.update_data(avatar_name=name)
        
        # Получаем данные из состояния для создания аватара
        data = await state.get_data()
        gender = data.get("gender", "male")
        training_type = data.get("training_type", "portrait")
        
        # Создаем аватар в базе данных
        from app.core.di import get_user_service, get_avatar_service
        from app.database.models import AvatarGender, AvatarType, AvatarTrainingType
        
        async with get_user_service() as user_service:
            user = await user_service.get_user_by_telegram_id(message.from_user.id)
            if not user:
                await message.answer("❌ Пользователь не найден. Попробуйте позже.")
                return
            
            # Сохраняем user_id перед закрытием сессии
            user_id = user.id
        
        async with get_avatar_service() as avatar_service:
            avatar = await avatar_service.create_avatar(
                user_id=user_id,
                name=name,
                gender=AvatarGender(gender),
                avatar_type=AvatarType.CHARACTER,
                training_type=AvatarTrainingType(training_type)
            )
            
            # Сохраняем ID аватара в состоянии
            await state.update_data(avatar_id=str(avatar.id))
        
        # Показываем успешное сохранение имени и переход к загрузке фото
        text = f"""
✅ Аватар создан!

🎭 Имя: {name}
👤 Пол: {"Мужской" if gender == "male" else "Женский"}
🎯 Тип: {"Портретный" if training_type == "portrait" else "Художественный"}

📸 Следующий шаг: Загрузка фотографий

Минимум 10 фотографий для качественного обучения.
Рекомендуется 15-20 фото для лучшего результата.

🚀 Готовы загружать фото?
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📸 Начать загрузку фото",
                    callback_data="start_photo_upload"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Изменить имя",
                    callback_data="select_gender"
                )
            ]
        ])
        
        await message.answer(
            text=text,
            reply_markup=keyboard
        )
        
        logger.info(f"Пользователь {message.from_user.id} создал аватар: {name} (ID: {avatar.id})")
        
    except Exception as e:
        logger.exception(f"Ошибка при создании аватара: {e}")
        await message.answer("❌ Произошла ошибка при создании аватара. Попробуйте еще раз.")

@router.callback_query(F.data == "explain_gender_choice")
async def explain_gender_choice(callback: CallbackQuery, state: FSMContext):
    """Объясняет зачем нужно выбирать пол аватара"""
    try:
        text = """
💡 **Зачем указывать пол аватара?**

🎯 **Оптимизация обучения:**
• AI модель лучше понимает особенности внешности
• Более точное распознавание мужских/женских черт лица
• Улучшенное качество генерируемых портретов

🔬 **Технические преимущества:**
• Специализированные алгоритмы для каждого пола
• Лучшая обработка особенностей (борода, макияж и т.д.)
• Более естественные результаты

⚡ **Результат:**
• Портреты выглядят более реалистично
• AI лучше передает ваши уникальные черты
• Быстрее достигается качественный результат

🔄 **Можно изменить:** Если ошиблись с выбором, можно создать новый аватар

Готовы выбрать пол для оптимизации?
"""
        
        keyboard = get_avatar_gender_keyboard()
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        logger.info(f"Пользователь {callback.from_user.id} запросил объяснение выбора пола")
        
    except Exception as e:
        logger.exception(f"Ошибка при объяснении выбора пола: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

@router.callback_query(F.data == "cancel_avatar_creation")
async def cancel_avatar_creation(callback: CallbackQuery, state: FSMContext):
    """Отмена создания аватара"""
    try:
        # Очищаем состояние
        await state.clear()
        
        text = """
❌ **Создание аватара отменено**

Вы можете вернуться к созданию в любое время!

🎭 Аватары помогают создавать уникальные изображения с вашим лицом
"""
        
        # Возвращаемся к главному меню аватаров
        from .main import avatar_main_handler
        await avatar_main_handler.show_avatar_menu(callback, state)
        
        logger.info(f"Пользователь {callback.from_user.id} отменил создание аватара")
        
    except Exception as e:
        logger.exception(f"Ошибка при отмене создания аватара: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

@router.callback_query(F.data == "avatar_help")
async def show_avatar_help(callback: CallbackQuery, state: FSMContext):
    """Показывает помощь по работе с аватарами"""
    try:
        text = """
🎭 **Как работают портретные аватары?**

🎯 **Что это такое:**
Аватар — это ваша персональная AI модель, обученная на ваших фотографиях. Она умеет создавать новые изображения с вашим лицом в любых условиях и стилях.

🚀 **Процесс создания:**

**1. Выбор пола** 👥
Помогает AI лучше понять особенности вашей внешности

**2. Имя аватара** 📝  
Просто для удобства управления

**3. Загрузка фото** 📸
• Минимум 10 фотографий
• Рекомендуется 15-20 для лучшего качества
• Разные ракурсы, освещение, выражения лица

**4. Обучение** 🎓
• Занимает 3-15 минут
• Автоматическая обработка
• Создание LoRA модели

⭐ **Преимущества портретной модели:**
• Специальная оптимизация для лиц людей
• Быстрое обучение  
• Высокое качество портретов
• Простота использования

💡 **Советы для лучшего результата:**
• Используйте качественные фото
• Включайте разные эмоции
• Добавьте фото в разном освещении
• Избегайте групповых фото

🎨 **После обучения:**
Можете генерировать изображения с любыми промптами!

Готовы создать свой первый аватар?
"""
        
        keyboard = get_avatar_main_menu(0)  # Показываем меню создания
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        logger.info(f"Пользователь {callback.from_user.id} запросил помощь по аватарам")
        
    except Exception as e:
        logger.exception(f"Ошибка при показе помощи по аватарам: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)
