# Тексты сообщений для сценариев аватаров

from frontend_bot.constants.avatar import AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS

PHOTO_REQUIREMENTS_TEXT = (
    f"ℹ️ <b>Требования к фото для генерации аватара:</b>\n"
    f"• Минимум {AVATAR_MIN_PHOTOS}, максимум {AVATAR_MAX_PHOTOS} фото.\n"
    "• Разные ракурсы, фоны, одежда, освещение.\n"
    "• Не используйте фото с другими людьми, гримасами или закрытым лицом.\n"
    "• Размер не менее 512x512 пикселей, формат JPEG или PNG.\n"
    "• Фото должны быть чёткими, цветными, без сильных фильтров, теней и "
    "бликов.\n\n"
    "<b>Пожалуйста, отправьте свои фото для создания аватара!"
    "</b>"
)

PHOTO_CHECKING_TEXT = "⏳ Идёт проверка фото..."
PHOTO_LIMIT_REACHED_TEXT = (
    "Достигнут лимит фото ({max_photos}). "
    "Удалите лишние фото, чтобы добавить новые."
)
PHOTO_NOT_ACCEPTED_TEXT = (
    "⚠️ Фото не принято: {reason}\n"
    "📸 Совет: используйте чёткие фото без фильтров."
)
PHOTO_SAVED_TEXT = (
    "Фото сохранено ({count}/{max_photos}). {progress} "
    "Можете добавить ещё фото или продолжить."
)
PHOTO_MINIMUM_REACHED_TEXT = (
    "Вы загрузили {min_photos} фото — этого достаточно для генерации аватара.\n"
    "Хотите добавить ещё фото (до {max_photos}) для лучшего качества "
    "или продолжить?\n{progress}"
)
PHOTO_MAXIMUM_REACHED_TEXT = (
    "Достигнут максимум {max_photos} фото. "
    "Можете только удалить лишние или продолжить.\n{progress}"
)
PHOTO_GALLERY_EMPTY_TEXT = "У вас пока нет загруженных фото."
PHOTO_GALLERY_WAIT_TEXT = "Ждём новое фото..."
PHOTO_NAME_PROMPT = (
    "Введите имя для вашего аватара (например, 'Сергей_Бизнес')."
)
PHOTO_NAME_EMPTY = (
    "Имя не может быть пустым. Введите имя для аватара:"
)
PHOTO_TYPE_PROMPT = (
    "Выберите тип для вашего аватара (это важно для качества генерации):"
)
PHOTO_TYPE_CHOSEN = (
    "Тип выбран: {type_name}. Теперь выберите базовую модель:"
)
PHOTO_BASE_MODEL_PROMPT = (
    "Базовая модель выбрана: {base_model_name}. Теперь выберите стиль:"
)
PHOTO_STYLE_PREVIEW_UNAVAILABLE = (
    "[{style_name}] пример недоступен."
)
PHOTO_STYLE_CONFIRM = (
    "\U0001F4F7 Фото: {photo_count}\nИмя: {title}\nТип: {type_name}\n"
    "Базовая модель: {base_tune}\nСтиль: {style_name}\n\n"
    "Проверьте данные. Всё верно?"
)
PHOTO_CONFIRM_SENT = (
    "Данные отправлены! Генерация аватара начнётся скоро."
)
PHOTO_ADD_MORE = (
    "Вы можете загрузить ещё фото (до {max_photos}). "
    "После этого нажмите 'Продолжить'."
)
PHOTO_CANCELLED = (
    "Создание аватара отменено. Вы вернулись к списку аватаров."
)
PHOTO_EXAMPLE_UNAVAILABLE = "Пример фото недоступен." 