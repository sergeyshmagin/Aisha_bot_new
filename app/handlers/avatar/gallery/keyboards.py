"""
Клавиатуры для галереи аватаров
Выделен из app/handlers/avatar/gallery.py для соблюдения правила ≤500 строк
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import AvatarStatus

class GalleryKeyboards:
    """Класс для создания клавиатур галереи аватаров"""
    
    @staticmethod
    def get_avatar_card_keyboard(
        avatar_idx: int, 
        total_avatars: int, 
        avatar_id: str, 
        is_main: bool = False, 
        avatar_status = None
    ) -> InlineKeyboardMarkup:
        """Создает клавиатуру для карточки аватара"""
        
        buttons = []
        
        # Навигация (если больше одного аватара)
        if total_avatars > 1:
            nav_buttons = []
            if avatar_idx > 0:
                nav_buttons.append(
                    InlineKeyboardButton(text="⬅️", callback_data=f"avatar_card_prev:{avatar_idx}")
                )
            
            nav_buttons.append(
                InlineKeyboardButton(text=f"{avatar_idx + 1}/{total_avatars}", callback_data="noop")
            )
            
            if avatar_idx < total_avatars - 1:
                nav_buttons.append(
                    InlineKeyboardButton(text="➡️", callback_data=f"avatar_card_next:{avatar_idx}")
                )
            
            buttons.append(nav_buttons)
        
        # 🚀 НОВОЕ: Кнопка генерации для завершенных аватаров
        if avatar_status == AvatarStatus.COMPLETED or avatar_status == "completed":
            buttons.append([
                InlineKeyboardButton(text="🎨 Генерировать", callback_data=f"avatar_generate:{avatar_id}")
            ])
        
        # Действия с аватаром
        action_buttons = []
        
        # Кнопка "Сделать основным" только если не основной И не черновик
        if not is_main and avatar_status not in [AvatarStatus.DRAFT, AvatarStatus.PHOTOS_UPLOADING]:
            action_buttons.append(
                InlineKeyboardButton(text="⭐ Основной", callback_data=f"avatar_set_main:{avatar_id}")
            )
        elif not is_main:
            # Для черновиков не показываем кнопку вообще (пустое место)
            pass
        else:
            # Если уже основной аватар - показываем неактивную кнопку
            action_buttons.append(
                InlineKeyboardButton(text="⭐ Основной", callback_data="noop")
            )
        
        # Кнопка "Продолжить" только для черновиков и загрузки фото
        if avatar_status in [AvatarStatus.DRAFT, AvatarStatus.PHOTOS_UPLOADING]:
            action_buttons.append(
                InlineKeyboardButton(text="🔄 Продолжить", callback_data=f"avatar_continue_creation:{avatar_id}")
            )
        
        # Удаление
        action_buttons.append(
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"avatar_delete:{avatar_id}")
        )
        
        buttons.append(action_buttons)
        
        # Возврат в меню
        buttons.append([
            InlineKeyboardButton(text="◀️ В меню аватаров", callback_data="avatar_menu")
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def get_delete_confirmation_keyboard(avatar_id: str) -> InlineKeyboardMarkup:
        """Создает клавиатуру подтверждения удаления аватара"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Да, удалить", 
                    callback_data=f"avatar_delete_confirm:{avatar_id}"
                ),
                InlineKeyboardButton(
                    text="✅ Отмена", 
                    callback_data=f"avatar_delete_cancel:{avatar_id}"
                )
            ]
        ])

    @staticmethod
    def get_avatar_photo_gallery_keyboard(
        photo_idx: int, 
        total_photos: int, 
        avatar_id: str
    ) -> InlineKeyboardMarkup:
        """Создает клавиатуру для галереи фотографий аватара"""
        
        buttons = []
        
        # Навигация по фото
        if total_photos > 1:
            nav_buttons = []
            if photo_idx > 0:
                nav_buttons.append(
                    InlineKeyboardButton(text="⬅️", callback_data=f"avatar_photo_prev:{avatar_id}:{photo_idx}")
                )
            
            nav_buttons.append(
                InlineKeyboardButton(text=f"{photo_idx + 1}/{total_photos}", callback_data="noop")
            )
            
            if photo_idx < total_photos - 1:
                nav_buttons.append(
                    InlineKeyboardButton(text="➡️", callback_data=f"avatar_photo_next:{avatar_id}:{photo_idx}")
                )
            
            buttons.append(nav_buttons)
        
        # Возврат к карточке аватара
        buttons.append([
            InlineKeyboardButton(text="◀️ К аватару", callback_data=f"avatar_view_card:{avatar_id}")
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def get_empty_gallery_keyboard() -> InlineKeyboardMarkup:
        """Создает клавиатуру для пустой галереи"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🆕 Создать аватар", callback_data="create_avatar")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="avatar_menu")]
        ]) 