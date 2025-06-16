from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==================== LEGACY FUNCTIONS (ПОЛНОСТЬЮ ЗАКОММЕНТИРОВАНЫ) ====================
# TODO: Удалить после полного перехода на новую структуру меню
# Все функции ниже заменены на новую модульную структуру app/keyboards/menu/

# LEGACY: Старое главное меню - заменено на app/keyboards/menu/main.py
# def get_main_menu() -> InlineKeyboardMarkup:
#     """
#     🏠 LEGACY: Главное меню бота - 3 основных раздела
#     TODO: Удалить после тестирования новой структуры
#     """
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [
#             InlineKeyboardButton(
#                 text="🎨 Творчество",
#                 callback_data="ai_creativity_menu"  # LEGACY callback_data
#             ),
#             InlineKeyboardButton(
#                 text="🤖 ИИ Ассистент",
#                 callback_data="business_menu"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="⚙️ Настройки",
#                 callback_data="profile_menu"  # LEGACY callback_data
#             )
#         ]
#     ])

# LEGACY: Старое меню творчества - заменено на app/keyboards/menu/creativity.py
# def get_ai_creativity_menu() -> InlineKeyboardMarkup:
#     """
#     🎨 LEGACY: Творчество - создание и просмотр контента
#     TODO: Удалить после тестирования новой структуры
#     """
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [
#             InlineKeyboardButton(
#                 text="📷 Фото",
#                 callback_data="images_menu"  # LEGACY callback_data
#             ),
#             InlineKeyboardButton(
#                 text="🎬 Видео",
#                 callback_data="video_menu"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="📂 Мои работы",
#                 callback_data="my_projects_menu"  # LEGACY callback_data
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="🏠 Главное меню",
#                 callback_data="main_menu"
#             )
#         ]
#     ])

# LEGACY: Старое меню изображений - заменено на app/keyboards/menu/creativity.py
# def get_images_menu() -> InlineKeyboardMarkup:
#     """
#     📷 LEGACY: Фото - создание изображений
#     TODO: Удалить после тестирования новой структуры
#     """
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [
#             InlineKeyboardButton(
#                 text="📷 Фото со мной",
#                 callback_data="avatar_generation_menu"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="📝 По описанию",
#                 callback_data="imagen4_generation"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="🎬 Видео",
#                 callback_data="video_generation_stub"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="◀️ Назад",
#                 callback_data="ai_creativity_menu"  # LEGACY callback_data
#             ),
#             InlineKeyboardButton(
#                 text="🏠 Главное меню",
#                 callback_data="main_menu"
#             )
#         ]
#     ])

# LEGACY: Старое меню "Мои работы" - заменено на app/keyboards/menu/projects.py
# def get_my_projects_menu() -> InlineKeyboardMarkup:
#     """
#     📂 LEGACY: Мои работы - весь созданный контент
#     TODO: Удалить после тестирования новой структуры
#     """
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [
#             InlineKeyboardButton(
#                 text="👤 Мои образы",
#                 callback_data="avatar_gallery"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="🖼️ Все фото",
#                 callback_data="gallery_all"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="⭐ Избранное",
#                 callback_data="favorites"
#             ),
#             InlineKeyboardButton(
#                 text="📊 Статистика",
#                 callback_data="my_stats"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="◀️ Назад",
#                 callback_data="ai_creativity_menu"  # LEGACY callback_data
#             ),
#             InlineKeyboardButton(
#                 text="🏠 Главное меню",
#                 callback_data="main_menu"
#             )
#         ]
#     ])

# ==================== АКТИВНЫЕ ФУНКЦИИ ====================
# Эти функции остаются активными, так как используются в новой структуре

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
                callback_data="avatar_styles_stub"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="creativity_menu"  # Обновлено на новый callback_data
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
                text="📁 Мои видео",
                callback_data="my_videos"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="creativity_menu"  # Обновлено на новый callback_data
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

# Остальные активные функции остаются без изменений...
def get_tasks_menu() -> InlineKeyboardMarkup:
    """
    📋 Задачи - управление задачами и проектами
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ Новая задача",
                callback_data="task_create"
            ),
            InlineKeyboardButton(
                text="📋 Мои задачи",
                callback_data="task_list"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Проекты",
                callback_data="project_list"
            ),
            InlineKeyboardButton(
                text="📈 Аналитика",
                callback_data="task_analytics"
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
                callback_data="projects_menu"  # Обновлено на новый callback_data
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