"""
Обработчики создания аватаров
Workflow: Тип обучения → Пол → Имя → Загрузка фото
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.keyboards.avatar_clean import get_avatar_gender_keyboard
from app.handlers.state import AvatarStates
from app.core.logger import get_logger

logger = get_logger(__name__)
router = Router()

@router.callback_query(F.data == "create_avatar")
async def start_avatar_creation(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс создания аватара с выбора типа обучения"""
    try:
        # Переходим к выбору типа обучения
        from .training_type_selection import show_training_type_selection
        await show_training_type_selection(callback, state)
        
        logger.info(f"Пользователь {callback.from_user.id} начал создание аватара")
        
    except Exception as e:
        logger.exception(f"Ошибка при начале создания аватара: {e}")
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
            reply_markup=keyboard,
            parse_mode="Markdown"
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
            text=text,
            parse_mode="Markdown"
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
✅ **Аватар создан!**

🎭 **Имя:** {name}
👤 **Пол:** {"Мужской" if gender == "male" else "Женский"}
🎯 **Тип:** {"Портретный" if training_type == "portrait" else "Художественный"}

📸 **Следующий шаг:** Загрузка фотографий

Минимум 10 фотографий для качественного обучения.
Рекомендуется 15-20 фото для лучшего результата.

🚀 **Готовы загружать фото?**
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
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        logger.info(f"Пользователь {message.from_user.id} создал аватар: {name} (ID: {avatar.id})")
        
    except Exception as e:
        logger.exception(f"Ошибка при создании аватара: {e}")
        await message.answer("❌ Произошла ошибка при создании аватара. Попробуйте еще раз.")

 