"""
Главный обработчик меню

Управляет отображением главного меню и переходами между разделами.
Новая структура без LEGACY поддержки.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.shared.handlers.base_handler import BaseHandler
from app.keyboards.menu.main import get_main_menu
from app.core.di import get_user_service

logger = logging.getLogger(__name__)


class MainMenuHandler(BaseHandler):
    """Обработчик главного меню"""
    
    def __init__(self):
        super().__init__()
        self.router = Router(name="main_menu")
        self._register_handlers()
    
    async def get_user_balance(self, user_id: int) -> float:
        """Получает баланс пользователя"""
        try:
            async with get_user_service() as user_service:
                balance = await user_service.get_user_balance(user_id)
                return balance
        except Exception as e:
            logger.exception(f"Ошибка получения баланса пользователя {user_id}: {e}")
            return 0.0
    
    def _register_handlers(self):
        """Регистрирует обработчики callback_data"""
        # Команда /start
        self.router.message.register(
            self.handle_start_command,
            Command("start")
        )
        
        # Главное меню (новая структура)
        self.router.callback_query.register(
            self.show_main_menu,
            F.data.in_(["main_menu", "main_menu_v2"])
        )
        
        # ==================== LEGACY ОБРАБОТЧИКИ (ЗАКОММЕНТИРОВАНЫ) ====================
        # TODO: Удалить после полного перехода на новую структуру
        
        # LEGACY: Старое главное меню
        # self.router.callback_query.register(
        #     self.show_main_menu_legacy,
        #     F.data == "main_menu_legacy"
        # )
        
        # LEGACY: Бизнес-ассистент (временно закомментировано)
        # self.router.callback_query.register(
        #     self.show_business_menu,
        #     F.data == "business_menu"
        # )
    
    async def handle_start_command(self, message: Message, state: FSMContext):
        """
        Обработчик команды /start
        
        Отправляет приветственное сообщение и главное меню
        """
        try:
            # Получаем пользователя или автоматически регистрируем
            user = await self.get_user_from_message(message, auto_register=True)
            if not user:
                return
            
            # Очищаем состояние при старте
            await self.safe_clear_state(state)
            
            # Получаем баланс пользователя
            user_balance = await self.get_user_balance(user.id)
            
            # Приветственный текст
            welcome_text = f"""👋 <b>Добро пожаловать в Aisha!</b>

🤖 Привет, {message.from_user.first_name or 'дорогой пользователь'}!

<b>Aisha</b> - ваш личный ИИ-ассистент для творчества и бизнеса:

🎨 <b>Творчество:</b> Создавайте уникальные изображения и видео с вашим лицом
🎭 <b>Мои работы:</b> Управляйте своими созданными материалами  
🤖 <b>Бизнес-ассистент:</b> Автоматизируйте рабочие процессы
💰 <b>Баланс:</b> Управляйте финансами и покупками
⚙️ <b>Настройки:</b> Персонализируйте работу бота
❓ <b>Помощь:</b> Получите поддержку и обучение

<i>Выберите нужный раздел из меню ниже:</i>"""

            # Отправляем главное меню с балансом
            await message.answer(
                text=welcome_text,
                reply_markup=get_main_menu(balance=user_balance),
                parse_mode="HTML"
            )
            
            logger.info(f"Команда /start обработана для пользователя {message.from_user.id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при обработке команды /start: {e}")
            await message.reply("❌ Произошла ошибка. Попробуйте еще раз.")
    
    async def show_main_menu(self, callback: CallbackQuery, state: FSMContext):
        """
        Показывает главное меню
        
        6 основных разделов:
        - 🎨 Творчество
        - 🎭 Мои работы  
        - 🤖 Бизнес-ассистент
        - 💰 Баланс
        - ⚙️ Настройки
        - ❓ Помощь
        """
        try:
            # Получаем пользователя
            user = await self.get_user_from_callback(callback)
            if not user:
                return
            
            # Получаем баланс пользователя
            user_balance = await self.get_user_balance(user.id)
            
            await self.safe_edit_message(
                callback,
                text=(
                    "🏠 <b>Главное меню</b>\n\n"
                    "Выберите нужный раздел:\n\n"
                    "🎨 <b>Творчество</b> - создание контента\n"
                    "🎭 <b>Мои работы</b> - результаты и управление\n"
                    "🤖 <b>Бизнес-ассистент</b> - рабочие задачи\n"
                    "💰 <b>Баланс</b> - финансовые операции\n"
                    "⚙️ <b>Настройки</b> - персонализация\n"
                    "❓ <b>Помощь</b> - поддержка и обучение"
                ),
                reply_markup=get_main_menu(balance=user_balance),
                parse_mode="HTML"
            )
            
            await callback.answer()
            logger.info(f"Показано главное меню для пользователя {callback.from_user.id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при показе главного меню: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    # ==================== LEGACY МЕТОДЫ (ЗАКОММЕНТИРОВАНЫ) ====================
    # TODO: Удалить после полного перехода на новую структуру
    
    # async def show_main_menu_legacy(self, callback: CallbackQuery, state: FSMContext):
    #     """
    #     LEGACY: Показывает старое главное меню
    #     
    #     Для обратной совместимости и A/B тестирования
    #     """
    #     try:
    #         await self.safe_edit_message(
    #             callback.message,
    #             text=(
    #                 "🏠 <b>Главное меню</b>\n\n"
    #                 "LEGACY версия меню:\n\n"
    #                 "🎨 <b>Творчество</b> - создание и просмотр контента\n"
    #                 "🤖 <b>ИИ Ассистент</b> - управление командой и задачами\n"
    #                 "⚙️ <b>Настройки</b> - личный кабинет и настройки"
    #             ),
    #             reply_markup=get_main_menu_legacy(),
    #             parse_mode="HTML"
    #         )
    #         
    #         await callback.answer()
    #         logger.info(f"Показано LEGACY главное меню для пользователя {callback.from_user.id}")
    #         
    #     except Exception as e:
    #         logger.exception(f"Ошибка при показе LEGACY главного меню: {e}")
    #         await callback.answer("❌ Произошла ошибка", show_alert=True)


# Создаем экземпляр обработчика
main_menu_handler = MainMenuHandler()

# Экспортируем callback обработчики для использования в других модулях
show_main_menu_callback = main_menu_handler.show_main_menu

# ==================== LEGACY ЭКСПОРТЫ (ЗАКОММЕНТИРОВАНЫ) ====================
# TODO: Удалить после полного перехода на новую структуру

# show_main_menu_legacy_callback = main_menu_handler.show_main_menu_legacy
# show_business_menu_callback = main_menu_handler.show_business_menu 