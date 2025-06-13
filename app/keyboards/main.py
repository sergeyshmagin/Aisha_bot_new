from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu() -> InlineKeyboardMarkup:
    """
    🏠 Главное меню бота - 3 основных раздела
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎨 Творчество",
                callback_data="ai_creativity_menu"
            ),
            InlineKeyboardButton(
                text="🤖 ИИ Ассистент",
                callback_data="business_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="⚙️ Настройки",
                callback_data="profile_menu"
            )
        ]
    ])

def get_ai_creativity_menu() -> InlineKeyboardMarkup:
    """
    🎨 Творчество - создание и просмотр контента
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📷 Фото",
                callback_data="images_menu"
            ),
            InlineKeyboardButton(
                text="🎬 Видео",
                callback_data="video_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="📂 Мои работы",
                callback_data="my_projects_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])

def get_images_menu() -> InlineKeyboardMarkup:
    """
    📷 Фото - создание изображений
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📷 Фото со мной",
                callback_data="avatar_generation_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="📝 По описанию",
                callback_data="imagen4_generation"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎬 Видео",
                callback_data="video_generation_stub"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="ai_creativity_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])

def get_avatar_generation_menu() -> InlineKeyboardMarkup:
    """
    📸 С моим аватаром - 3 варианта
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✍️ Свой промпт",
                callback_data="avatar_custom_prompt"
            )
        ],
        [
            InlineKeyboardButton(
                text="📷 Генерация по фото",
                callback_data="avatar_from_photo"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎨 Выбрать стиль",
                callback_data="avatar_styles"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="images_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])

def get_video_menu() -> InlineKeyboardMarkup:
    """
    🎬 Видео - создание видеороликов
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎭 Hedra AI",
                callback_data="hedra_video"
            )
        ],
        [
            InlineKeyboardButton(
                text="🌟 Kling",
                callback_data="kling_video"
            ),
            InlineKeyboardButton(
                text="🎪 Weo3",
                callback_data="weo3_video"
            )
        ],
        [
            InlineKeyboardButton(
                text="📂 Мои видео",
                callback_data="my_videos"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="ai_creativity_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])

def get_business_menu() -> InlineKeyboardMarkup:
    """
    🤖 ИИ Ассистент - управление командой и задачами
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📋 Задачи",
                callback_data="tasks_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="📰 Новости",
                callback_data="news_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="📝 Голос в текст",
                callback_data="transcribe_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="👥 В группу",
                callback_data="add_to_chat"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])

def get_tasks_menu() -> InlineKeyboardMarkup:
    """
    📋 Задачи - поручения и контроль
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ Создать",
                callback_data="create_task"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Мои поручения",
                callback_data="my_tasks"
            ),
            InlineKeyboardButton(
                text="👥 Команда",
                callback_data="team_tasks"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏰ Напоминания",
                callback_data="task_reminders"
            ),
            InlineKeyboardButton(
                text="📈 Отчеты",
                callback_data="task_reports"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="business_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])

def get_news_menu() -> InlineKeyboardMarkup:
    """
    📰 Новости - мониторинг и аналитика
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📱 Мои каналы",
                callback_data="my_channels"
            ),
            InlineKeyboardButton(
                text="➕ Добавить",
                callback_data="add_channel"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔥 Сегодня",
                callback_data="trending_today"
            ),
            InlineKeyboardButton(
                text="📊 За неделю",
                callback_data="trending_week"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎯 Контент",
                callback_data="content_from_news"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="business_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])

def get_add_to_chat_menu() -> InlineKeyboardMarkup:
    """
    👥 Добавить бота в чат - управление рабочими чатами
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔗 Получить ссылку-приглашение",
                callback_data="get_invite_link"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Мои рабочие чаты",
                callback_data="my_work_chats"
            )
        ],
        [
            InlineKeyboardButton(
                text="⚙️ Настройки парсинга",
                callback_data="parsing_settings"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Аналитика чатов",
                callback_data="chat_analytics"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="business_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])

def get_my_projects_menu() -> InlineKeyboardMarkup:
    """
    📂 Мои работы - весь созданный контент
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👤 Мои образы",
                callback_data="avatar_gallery"
            )
        ],
        [
            InlineKeyboardButton(
                text="🖼️ Все фото",
                callback_data="gallery_all"
            )
        ],
        [
            InlineKeyboardButton(
                text="⭐ Избранное",
                callback_data="favorites"
            ),
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="my_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="ai_creativity_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])

def get_gallery_menu() -> InlineKeyboardMarkup:
    """
    🖼️ Галерея - просмотр по категориям
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📸 Фото со мной",
                callback_data="gallery_avatars"
            )
        ],
        [
            InlineKeyboardButton(
                text="🖼️ Изображения",
                callback_data="gallery_imagen"
            ),
            InlineKeyboardButton(
                text="🎬 Только видео",
                callback_data="gallery_video"
            )
        ],
        [
            InlineKeyboardButton(
                text="📅 По дате",
                callback_data="gallery_by_date"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="my_projects_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])

def get_quick_action_menu() -> InlineKeyboardMarkup:
    """
    ⚡ Быстрые действия для опытных пользователей
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚡ Быстрое изображение",
                callback_data="quick_image"
            ),
            InlineKeyboardButton(
                text="⚡ Быстрое видео",
                callback_data="quick_video"
            )
        ],
        [
            InlineKeyboardButton(
                text="📰 Последние новости",
                callback_data="latest_news"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ]) 