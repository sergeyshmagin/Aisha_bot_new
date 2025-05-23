"""
Обработчики создания аватара
Часть основного workflow создания аватара
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.keyboards.avatar import get_avatar_gender_keyboard
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

async def show_gender_selection(callback: CallbackQuery, state: FSMContext):
    """Показывает выбор пола аватара"""
    try:
        data = await state.get_data()
        training_type = data.get("training_type", "portrait")
        
        text = f"""
🎯 **Выберите пол аватара**

Тип обучения: {training_type.title()}
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
        gender = callback.data.split("_", 2)[2]  # male, female, other
        
        # Валидируем пол
        if gender not in ["male", "female", "other"]:
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
• Буквы, цифры, пробелы
• Без специальных символов

💡 **Примеры:** Алексей, Maya, Cyber Alex

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

@router.message(F.text, AvatarStates.entering_name)
async def process_avatar_name(message: Message, state: FSMContext):
    """Обработка ввода имени аватара"""
    try:
        name = message.text.strip()
        
        # Валидация имени
        if len(name) < 2:
            await message.answer("❌ Имя слишком короткое. Минимум 2 символа.")
            return
        
        if len(name) > 50:
            await message.answer("❌ Имя слишком длинное. Максимум 50 символов.")
            return
        
        # Проверка на недопустимые символы
        allowed_chars = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюяABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_")
        if not all(c in allowed_chars for c in name):
            await message.answer("❌ Используйте только буквы, цифры, пробелы и дефисы.")
            return
        
        # Сохраняем имя
        await state.update_data(name=name)
        
        # Показываем итоговую информацию и переход к загрузке фото
        data = await state.get_data()
        training_type = data.get("training_type", "portrait")
        gender = data.get("gender", "other")
        
        gender_text = {"male": "👨 Мужской", "female": "👩 Женский", "other": "🤖 Другое"}
        
        text = f"""
✅ **Аватар настроен!**

🎭 **Имя:** {name}
🎯 **Тип обучения:** {training_type.title()}
👥 **Пол:** {gender_text.get(gender, "🤖 Другое")}

📸 **Следующий шаг:** Загрузка фотографий

Минимум 10 фотографий для качественного обучения.
Рекомендуется 15-20 фото для лучшего результата.

🚀 **Готовы загружать фото?**
"""
        
        # Создаем клавиатуру для перехода к загрузке
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📸 Начать загрузку фото",
                    callback_data="start_photo_upload"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Изменить настройки",
                    callback_data="select_training_type"
                )
            ]
        ])
        
        await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        logger.info(f"Пользователь {message.from_user.id} ввел имя аватара: {name}")
        
    except Exception as e:
        logger.exception(f"Ошибка при обработке имени аватара: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте ввести имя еще раз.")

@router.callback_query(F.data == "start_photo_upload")
async def start_photo_upload(callback: CallbackQuery, state: FSMContext):
    """Начало загрузки фотографий"""
    try:
        await callback.message.edit_text(
            text="🔄 Подготавливаем загрузку фотографий...",
            parse_mode="Markdown"
        )
        
        # Здесь будет переход к модулю загрузки фото
        # TODO: Реализовать в следующем этапе
        
        await callback.message.edit_text(
            text="🚧 Загрузка фотографий в разработке...\n\nВозвращайтесь позже!",
            parse_mode="Markdown"
        )
        
        logger.info(f"Пользователь {callback.from_user.id} начал загрузку фото")
        
    except Exception as e:
        logger.exception(f"Ошибка при начале загрузки фото: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True) 