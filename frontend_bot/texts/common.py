from frontend_bot.config import settings
from frontend_bot.shared.progress import get_progressbar

# --- Шаблоны ошибок ---
ERROR_NO_PHOTOS = "У вас пока нет загруженных фото."
ERROR_USER_AVATAR = "Ошибка: не найден аватар или пользователь."
ERROR_INDEX = "Ошибка: индекс фото вне диапазона."
ERROR_CALLBACK_DATA = "Ошибка: некорректные данные callback."
ERROR_FILE = "Ошибка при работе с файлом. Попробуйте ещё раз."
ERROR_NO_AVATAR_ID = (
    "Ошибка: не найден идентификатор аватара. "
    "Пожалуйста, начните создание аватара заново."
)
ERROR_NO_PHOTOS = (
    "Нет фото для отображения. " "Пожалуйста, загрузите хотя бы одно фото."
)
ERROR_GALLERY = (
    "Ошибка при отображении галереи. " "Попробуйте ещё раз или обратитесь в поддержку."
)
PROMPT_ENTER_AVATAR_NAME = "Теперь введите имя для вашего аватара:"
PROMPT_AVATAR_NAME_EMPTY = "Имя не может быть пустым. " "Введите имя для аватара:"
PROMPT_AVATAR_CANCELLED = (
    "Создание аватара отменено. " "Вы вернулись к списку аватаров."
)
PROMPT_TYPE_MENU = (
    "👤 Выберите пол для вашего аватара:\n\n"
    "Это важно для качества генерации. "
    "Пожалуйста, выберите тот вариант, который соответствует человеку на фото."
)


# --- Caption для галереи ---
def get_gallery_caption(idx: int, total: int) -> str:
    progress = get_progressbar(
        total, settings.AVATAR_MAX_PHOTOS, settings.AVATAR_MIN_PHOTOS, settings.AVATAR_MAX_PHOTOS, idx
    )
    if total == settings.AVATAR_MIN_PHOTOS:
        return (
            f"Фото {idx+1} из {total}\n{progress}\n\n"
            f"✅ Вы загрузили минимально необходимое количество фото (<b>{settings.AVATAR_MIN_PHOTOS}</b>).\n\n"
            f"🔝 Для лучшего качества генерации рекомендуем добавить ещё до <b>{settings.AVATAR_MAX_PHOTOS}</b> фото.\n\n"
            f"➡️ Вы можете продолжить или добавить ещё фото."
        )
    elif settings.AVATAR_MIN_PHOTOS < total < settings.AVATAR_MAX_PHOTOS:
        return (
            f"Фото {idx+1} из {total}\n{progress}\n\n"
            f"🔝 Можно добавить ещё <b>{settings.AVATAR_MAX_PHOTOS - total}</b> фото для лучшего качества.\n\n"
            f"➡️ Или продолжить к генерации аватара."
        )
    elif total == settings.AVATAR_MAX_PHOTOS:
        return (
            f"Фото {idx+1} из {total}\n{progress}\n\n"
            f"Достигнут максимум фото. Можете только продолжить."
        )
    else:
        return (
            f"Фото {idx+1} из {total}\n{progress}\n\n"
            f"❗️Минимум для старта: <b>{settings.AVATAR_MIN_PHOTOS}</b> фото.\n"
            f"Осталось загрузить: <b>{settings.AVATAR_MIN_PHOTOS - total}</b> фото.\n\n"
            f"Добавьте ещё фото для лучшего качества."
        )

HELP_TEXT = (
    "ℹ️ <b>Помощь</b>\n\n"
    "Этот бот поможет вам создавать аватары, работать с фото, вести бизнес-протоколы и многое другое.\n"
    "Основные команды:\n"
    "• 📷 Создать аватар\n"
    "• 👁 Просмотреть аватары\n"
    "• 🧑‍🎨 ИИ фотограф\n"
    "• ✨ Улучшить фото\n"
    "• 🖼 Мои аватары\n"
    "• 🖼 Работа с фото\n"
    "• 🖼 Образы\n"
    "• ❓ Помощь — это сообщение\n"
    "\nЕсли возникли вопросы — напишите /support."
)
