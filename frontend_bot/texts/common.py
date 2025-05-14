from frontend_bot.config import AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS
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
        total, AVATAR_MAX_PHOTOS, AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS, idx
    )
    if total == AVATAR_MIN_PHOTOS:
        return (
            f"Фото {idx+1} из {total}\n{progress}\n\n"
            f"✅ Вы загрузили минимально необходимое количество фото (<b>{AVATAR_MIN_PHOTOS}</b>).\n\n"
            f"🔝 Для лучшего качества генерации рекомендуем добавить ещё до <b>{AVATAR_MAX_PHOTOS}</b> фото.\n\n"
            f"➡️ Вы можете продолжить или добавить ещё фото."
        )
    elif AVATAR_MIN_PHOTOS < total < AVATAR_MAX_PHOTOS:
        return (
            f"Фото {idx+1} из {total}\n{progress}\n\n"
            f"🔝 Можно добавить ещё <b>{AVATAR_MAX_PHOTOS - total}</b> фото для лучшего качества.\n\n"
            f"➡️ Или продолжить к генерации аватара."
        )
    elif total == AVATAR_MAX_PHOTOS:
        return (
            f"Фото {idx+1} из {total}\n{progress}\n\n"
            f"Достигнут максимум фото. Можете только продолжить."
        )
    else:
        return (
            f"Фото {idx+1} из {total}\n{progress}\n\n"
            f"❗️Минимум для старта: <b>{AVATAR_MIN_PHOTOS}</b> фото.\n"
            f"Осталось загрузить: <b>{AVATAR_MIN_PHOTOS - total}</b> фото.\n\n"
            f"Добавьте ещё фото для лучшего качества."
        )
