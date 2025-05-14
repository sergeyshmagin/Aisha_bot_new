from frontend_bot.config import (
    AVATAR_MIN_PHOTOS,
    AVATAR_MAX_PHOTOS,
    PROGRESSBAR_EMOJI_FILLED,
    PROGRESSBAR_EMOJI_CURRENT,
    PROGRESSBAR_EMOJI_EMPTY,
)


def get_progressbar(
    current: int,
    total: int,
    min_photos: int = AVATAR_MIN_PHOTOS,
    max_photos: int = AVATAR_MAX_PHOTOS,
    current_idx: int = None,
    filled: str = PROGRESSBAR_EMOJI_FILLED,
    current_emoji: str = PROGRESSBAR_EMOJI_CURRENT,
    empty: str = PROGRESSBAR_EMOJI_EMPTY,
) -> str:
    """
    Генерирует строку прогресс-бара для загрузки фото или других целей.
    """
    if current <= min_photos:
        bar_len = min_photos
    else:
        bar_len = max_photos
    bar = []
    for i in range(bar_len):
        if current_idx is not None and i == current_idx:
            bar.append(current_emoji)
        elif i < current:
            bar.append(filled)
        else:
            bar.append(empty)
    return f"{''.join(bar)} ({current}/{bar_len})"
