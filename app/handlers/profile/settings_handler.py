"""
LEGACY: Обработчик настроек пользователя
Функциональность мигрирована в app/handlers/menu/settings_handler.py
Оставлен для совместимости со старыми callback'ами
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.core.logger import get_logger
from app.shared.handlers.base_handler import BaseHandler
from app.shared.decorators.auth_decorators import require_user

logger = get_logger(__name__)
router = Router()


class SettingsHandler(BaseHandler):
    """Обработчик настроек пользователя"""
    
    @require_user()
    async def show_settings(
        self, 
        callback: CallbackQuery, 
        state: FSMContext,
        user=None
    ):
        """Показывает настройки пользователя"""
        try:
            text = f"""⚙️ <b>Настройки профиля</b>

👤 <b>Основная информация</b>
• Имя: {user.first_name}
• Username: @{user.username or 'не указан'}
• Язык: {user.language_code.upper()}
• Часовой пояс: {user.timezone or 'UTC+5'}

🔔 <b>Уведомления</b>
• О завершении аватаров: ✅ Включены
• О пополнении баланса: ✅ Включены
• Новости и обновления: ✅ Включены

🎨 <b>Интерфейс</b>
• Тема: Светлая
• Язык интерфейса: Русский
• Компактные кнопки: ❌ Отключено

💰 <b>Платежи</b>
• Автопополнение: ❌ Отключено
• Минимальный баланс: не установлен"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔔 Уведомления",
                        callback_data="settings_notifications"
                    ),
                    InlineKeyboardButton(
                        text="🌍 Язык и регион",
                        callback_data="settings_language"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🎨 Интерфейс",
                        callback_data="settings_interface"
                    ),
                    InlineKeyboardButton(
                        text="💳 Платежи",
                        callback_data="settings_payments"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔒 Приватность",
                        callback_data="settings_privacy"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="profile_menu"
                    )
                ]
            ])
            
            await self.safe_edit_message(
                callback=callback,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"Ошибка показа настроек: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True) 