"""
Обработчик раздела "💰 Баланс"
Переиспользует существующий функционал из app/handlers/profile/
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.core.logger import get_logger
from app.shared.handlers.base_handler import BaseHandler
from app.keyboards.menu.balance import get_balance_menu

# Импортируем существующий обработчик баланса
from app.handlers.profile.balance_handler import balance_handler

logger = get_logger(__name__)


class BalanceMenuHandler(BaseHandler):
    """
    Обработчик меню баланса
    Переиспользует существующий BalanceHandler из profile модуля
    """
    
    def __init__(self):
        super().__init__()
        self.router = Router(name="balance_menu")
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрирует обработчики callback_data"""
        # Новый callback
        self.router.callback_query.register(
            self.show_balance_menu,
            F.data == "balance_menu_v2"
        )
        
        # LEGACY: Старый callback
        self.router.callback_query.register(
            self.show_balance_menu_legacy,
            F.data == "balance_menu"
        )
        
        # Дополнительные обработчики баланса
        self.router.callback_query.register(
            self.show_balance_info,
            F.data == "profile_balance_info"
        )
        
        self.router.callback_query.register(
            self.show_topup_balance,
            F.data == "profile_topup_balance"
        )
        
        self.router.callback_query.register(
            self.show_balance_history,
            F.data == "balance_history"
        )
        
        self.router.callback_query.register(
            self.show_balance_analytics,
            F.data == "balance_analytics"
        )
    
    async def show_balance_menu(self, callback: CallbackQuery, state: FSMContext):
        """Показывает меню баланса"""
        try:
            text = """💰 **Управление балансом**

Здесь вы можете управлять своими средствами:
• Просматривать текущий баланс
• Пополнять счет различными способами
• Отслеживать историю операций
• Анализировать траты

💡 *Все операции с балансом безопасны и мгновенны*"""

            keyboard = get_balance_menu()
            
            await self.safe_edit_message(
                callback,
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            await callback.answer()
            logger.info("Показано меню баланса")
            
        except Exception as e:
            logger.exception(f"Ошибка показа меню баланса: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def show_balance_menu_legacy(self, callback: CallbackQuery, state: FSMContext):
        """LEGACY: Перенаправление на личный кабинет"""
        # Перенаправляем на личный кабинет (существующий функционал)
        from app.handlers.profile.main_handler import profile_handler
        await profile_handler.show_profile_menu(callback, state)
    
    async def show_balance_info(self, callback: CallbackQuery, state: FSMContext):
        """Показывает информацию о балансе"""
        try:
            # Получаем пользователя
            user = await self.get_user_from_callback(callback)
            if not user:
                return
            
            # Переиспользуем существующий обработчик
            await balance_handler.show_balance_info(callback, state)
            
        except Exception as e:
            logger.exception(f"Ошибка показа информации о балансе: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def show_topup_balance(self, callback: CallbackQuery, state: FSMContext):
        """Показывает меню пополнения баланса"""
        try:
            # Переиспользуем существующий обработчик
            await balance_handler.show_topup_menu(callback, state)
            
        except Exception as e:
            logger.exception(f"Ошибка показа меню пополнения: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def show_balance_history(self, callback: CallbackQuery, state: FSMContext):
        """Показывает историю операций"""
        try:
            # Переиспользуем существующий обработчик
            await balance_handler.show_balance_history(callback, state)
            
        except Exception as e:
            logger.exception(f"Ошибка показа истории: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def show_balance_analytics(self, callback: CallbackQuery, state: FSMContext):
        """Показывает аналитику расходов"""
        await callback.answer("📊 Аналитика расходов в разработке!", show_alert=True)


# Создаем экземпляр обработчика
balance_menu_handler = BalanceMenuHandler()

# Экспортируем роутер для использования в router.py
router = balance_menu_handler.router 