"""
Обработчик раздела "❓ Помощь"
Переиспользует существующий функционал из app/handlers/profile/
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.core.logger import get_logger
from app.shared.handlers.base_handler import BaseHandler
from app.keyboards.menu.help import get_help_menu

logger = get_logger(__name__)


class HelpMenuHandler(BaseHandler):
    """
    Обработчик меню помощи
    Переиспользует существующий функционал
    """
    
    def __init__(self):
        super().__init__()
        self.router = Router(name="help_menu")
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрирует обработчики callback_data"""
        # Новый callback
        self.router.callback_query.register(
            self.show_help_menu,
            F.data == "help_menu_v2"
        )
        
        # Дополнительные обработчики помощи
        self.router.callback_query.register(
            self.show_profile_help,
            F.data == "profile_help"
        )
        
        self.router.callback_query.register(
            self.show_help_faq,
            F.data == "help_faq"
        )
        
        self.router.callback_query.register(
            self.show_help_changelog,
            F.data == "help_changelog"
        )
        
        # LEGACY: Старый callback
        self.router.callback_query.register(
            self.show_help_menu_legacy,
            F.data == "help_menu"
        )
    
    async def show_help_menu(self, callback: CallbackQuery, state: FSMContext):
        """Показывает меню помощи"""
        try:
            text = """❓ **Помощь**

Получите поддержку и узнайте больше:
• Руководство пользователя
• Связь с технической поддержкой
• Часто задаваемые вопросы
• Новости и обновления

🆘 *Мы всегда готовы помочь вам разобраться с ботом*"""

            keyboard = get_help_menu()
            
            await self.safe_edit_message(
                callback,
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            await callback.answer()
            logger.info("Показано меню помощи")
            
        except Exception as e:
            logger.exception(f"Ошибка показа меню помощи: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def show_help_menu_legacy(self, callback: CallbackQuery, state: FSMContext):
        """LEGACY: Перенаправление на справку профиля"""
        # Используем существующий обработчик справки
        from app.handlers.profile.main_handler import profile_handler
        await profile_handler.show_help_menu(callback, state)
    
    async def show_profile_help(self, callback: CallbackQuery, state: FSMContext):
        """Показывает помощь по профилю"""
        await callback.answer("👤 Справка по профилю в разработке!", show_alert=True)
    
    async def show_help_faq(self, callback: CallbackQuery, state: FSMContext):
        """Показывает часто задаваемые вопросы"""
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        faq_text = """❓ **Часто задаваемые вопросы**

**Q: Как создать аватар?**
A: Перейдите в "Творчество" → "Фото" → "Фото со мной"

**Q: Сколько стоит генерация?**
A: Imagen 4: 10 кредитов, Аватары: 5 кредитов

**Q: Как пополнить баланс?**
A: Через "Баланс" → "Пополнить"

**Q: Поддержка форматов?**
A: Изображения: JPG, PNG. Видео: MP4

**Q: Безопасность данных?**
A: Все данные шифруются и хранятся в безопасности"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="help_menu_v2"),
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
            ]
        ])

        try:
            await self.safe_edit_message(
                callback,
                faq_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.exception(f"Ошибка показа FAQ: {e}")
            await callback.answer("❌ Ошибка загрузки", show_alert=True)
        
        await callback.answer()
    
    async def show_help_changelog(self, callback: CallbackQuery, state: FSMContext):
        """Показывает список изменений"""
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        changelog_text = """📝 **Что нового в Aisha**

**v2.5.0 (13.06.2025)**
✅ Новая модульная структура меню
✅ Улучшенная навигация
✅ Исправления ошибок BaseHandler
✅ Добавлена команда /start

**v2.4.0**
• Интеграция Imagen 4
• Обновленные клавиатуры
• Улучшенная галерея

**v2.3.0**
• Система аватаров 2.0
• Новые стили генерации
• Оптимизация производительности"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="help_menu_v2"),
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
            ]
        ])

        try:
            await self.safe_edit_message(
                callback,
                changelog_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.exception(f"Ошибка показа changelog: {e}")
            await callback.answer("❌ Ошибка загрузки", show_alert=True)
        
        await callback.answer()


# Создаем экземпляр обработчика
help_menu_handler = HelpMenuHandler()

# Экспортируем роутер для использования в router.py
router = help_menu_handler.router 