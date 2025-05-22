"""Данные для галереи образов и стилей."""

from frontend_bot.config import settings

GALLERY_STYLES = [
    {"emoji": "👩🏼‍🦰", "name": "Женский"},
    {"emoji": "👨🏻", "name": "Мужской"},
    {"emoji": "👁", "name": "Портрет"},
    {"emoji": "🕴", "name": "Стильный"},
    {"emoji": "💼", "name": "Деловой"},
    {"emoji": "🎉", "name": "Праздники"},
    {"emoji": "🏙", "name": "Город"},
    {"emoji": "🌱", "name": "Природа"},
    {"emoji": "🏖", "name": "Отпуск"},
    {"emoji": "💎", "name": "Гламур"},
    {"emoji": "👑", "name": "Королева"},
    {"emoji": "👰", "name": "Невеста"},
    {"emoji": "🤰", "name": "Беременность"},
    {"emoji": "👶", "name": "Дети"},
    {"emoji": "👩‍💼", "name": "Профессии"},
    {"emoji": "⚽️", "name": "Спорт"},
    {"emoji": "🦌", "name": "Животные"},
    {"emoji": "🎬", "name": "Киногерои"},
    {"emoji": "🦄", "name": "Фэнтези"},
    {"emoji": "👗", "name": "Винтаж"},
    {"emoji": "✈️", "name": "Путешествия"},
    {"emoji": "🎭", "name": "Косплей"},
    {"emoji": "✨", "name": "Креатив"},
    {"emoji": "🪆", "name": "Куклы"},
    {"emoji": "🔥", "name": "Тренды"},
]

# Пути к изображениям в MinIO
GALLERY_IMAGES = [
    {
        "style": "Женский",
        "name": "Солнечное утро",
        "image_path": "gallery/woman_morning.jpg",  # Путь в MinIO
        "description": "Стиль: Женский\nОбраз: Солнечное утро",
    },
    {
        "style": "Женский",
        "name": "Вечерний шик",
        "image_path": "gallery/woman_evening.jpg",  # Путь в MinIO
        "description": "Стиль: Женский\nОбраз: Вечерний шик",
    },
    # ... другие образы
]

def get_gallery_image_url(image_path: str) -> str:
    """Получить URL изображения из MinIO."""
    return f"{settings.MINIO_ENDPOINT}/gallery/{image_path}"
