"""
Обработчик раздела "⚙️ Настройки"
Переиспользует существующий функционал из app/handlers/profile/
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.core.logger import get_logger
from app.shared.handlers.base_handler import BaseHandler
from app.keyboards.menu.settings import get_settings_menu

logger = get_logger(__name__)


class SettingsMenuHandler(BaseHandler):
    """
    Обработчик меню настроек
    Переиспользует существующий функционал из profile модуля
    """
    
    def __init__(self):
        super().__init__()
        self.router = Router(name="settings_menu")
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрирует обработчики callback_data"""
        # Новый callback
        self.router.callback_query.register(
            self.show_settings_menu,
            F.data == "settings_menu_v2"
        )
        
        # Дополнительные обработчики настроек
        self.router.callback_query.register(
            self.show_settings_notifications,
            F.data == "settings_notifications"
        )
        
        self.router.callback_query.register(
            self.show_profile_menu,
            F.data == "profile_menu"
        )
        
        self.router.callback_query.register(
            self.show_settings_language,
            F.data == "settings_language"
        )
        
        self.router.callback_query.register(
            self.show_settings_privacy,
            F.data == "settings_privacy"
        )
        
        self.router.callback_query.register(
            self.show_settings_payments,
            F.data == "settings_payments"
        )
        
        # LEGACY: Старый callback
        self.router.callback_query.register(
            self.show_settings_menu_legacy,
            F.data == "settings_menu"
        )
    
    async def show_settings_menu(self, callback: CallbackQuery, state: FSMContext):
        """Показывает меню настроек"""
        try:
            text = """⚙️ **Настройки**

Персонализируйте работу с ботом:
• Управление профилем и предпочтениями
• Настройки уведомлений и языка
• Параметры интерфейса и приватности
• Управление платежными методами

💡 *Настройте бота под себя для комфортной работы*"""

            keyboard = get_settings_menu()
            
            await self.safe_edit_message(
                callback,
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            await callback.answer()
            logger.info("Показано меню настроек")
            
        except Exception as e:
            logger.exception(f"Ошибка показа меню настроек: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def show_settings_menu_legacy(self, callback: CallbackQuery, state: FSMContext):
        """LEGACY: Перенаправление на личный кабинет"""
        # Перенаправляем на личный кабинет (существующий функционал)
        from app.handlers.profile.main_handler import profile_handler
        await profile_handler.show_profile_menu(callback, state)
    
    async def show_settings_notifications(self, callback: CallbackQuery, state: FSMContext):
        """Настройки уведомлений"""
        await callback.answer("🔔 Настройки уведомлений в разработке!", show_alert=True)
    
    async def show_profile_menu(self, callback: CallbackQuery, state: FSMContext):
        """Показывает меню профиля"""
        try:
            # Переиспользуем существующий обработчик профиля
            from app.handlers.profile.main_handler import profile_handler
            await profile_handler.show_profile_menu(callback, state)
        except Exception as e:
            logger.exception(f"Ошибка показа профиля: {e}")
            await callback.answer("❌ Ошибка загрузки профиля", show_alert=True)
    
    async def show_settings_language(self, callback: CallbackQuery, state: FSMContext):
        """Настройки языка"""
        await callback.answer("🌐 Настройки языка в разработке!", show_alert=True)
    
    async def show_settings_privacy(self, callback: CallbackQuery, state: FSMContext):
        """Настройки приватности"""
        await callback.answer("🔒 Настройки приватности в разработке!", show_alert=True)
    
    async def show_settings_payments(self, callback: CallbackQuery, state: FSMContext):
        """Настройки платежей"""
        await callback.answer("💳 Настройки платежей в разработке!", show_alert=True)


# Создаем экземпляр обработчика
settings_menu_handler = SettingsMenuHandler()

# Экспортируем роутер для использования в router.py
router = settings_menu_handler.router 