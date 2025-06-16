"""
Обработчик навигации для кнопок "Назад"
Обеспечивает правильную иерархию переходов между меню
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.core.logger import get_logger
from app.shared.handlers.base_handler import BaseHandler

logger = get_logger(__name__)


class NavigationHandler(BaseHandler):
    """
    Обработчик навигации между меню
    
    Обеспечивает правильные переходы "Назад" согласно иерархии:
    - Главное меню → /start
    - Творчество → Главное меню
    - Фото/Видео/Аудио → Творчество
    - Аватары/Imagen4 → Фото
    - И т.д.
    """
    
    def __init__(self):
        super().__init__()
        self.router = Router(name="navigation")
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрирует обработчики навигации"""
        
        # Универсальные обработчики "Назад"
        self.router.callback_query.register(
            self.back_to_main_menu,
            F.data.in_(["back_to_main", "main_menu", "main_menu_v2"])
        )
        
        self.router.callback_query.register(
            self.back_to_creativity,
            F.data.in_(["back_to_creativity", "creativity_menu", "ai_creativity_menu"])
        )
        
        self.router.callback_query.register(
            self.back_to_photo_menu,
            F.data.in_(["back_to_photo", "photo_menu", "images_menu"])
        )
        
        self.router.callback_query.register(
            self.back_to_projects,
            F.data.in_(["back_to_projects", "projects_menu", "my_projects_menu"])
        )
        
        # Специфичные переходы
        self.router.callback_query.register(
            self.back_to_avatar_menu,
            F.data == "back_to_avatar_menu"
        )
    
    async def back_to_main_menu(self, callback: CallbackQuery, state: FSMContext):
        """Возврат в главное меню"""
        try:
            # ✅ БЫСТРЫЙ ОТВЕТ НА CALLBACK
            await callback.answer()
            
            # Импортируем и вызываем обработчик главного меню
            from app.handlers.menu.main_handler import main_menu_handler
            await main_menu_handler.show_main_menu(callback, state)
            
            logger.info(f"Пользователь {callback.from_user.id} вернулся в главное меню")
            
        except Exception as e:
            logger.exception(f"Ошибка возврата в главное меню: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def back_to_creativity(self, callback: CallbackQuery, state: FSMContext):
        """Возврат в меню творчества"""
        try:
            # ✅ БЫСТРЫЙ ОТВЕТ НА CALLBACK
            await callback.answer()
            
            # Импортируем и вызываем обработчик творчества
            from app.handlers.menu.creativity_handler import creativity_handler
            await creativity_handler.show_creativity_menu(callback, state)
            
            logger.info(f"Пользователь {callback.from_user.id} вернулся в меню творчества")
            
        except Exception as e:
            logger.exception(f"Ошибка возврата в меню творчества: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def back_to_photo_menu(self, callback: CallbackQuery, state: FSMContext):
        """Возврат в меню фото"""
        try:
            # ✅ БЫСТРЫЙ ОТВЕТ НА CALLBACK
            await callback.answer()
            
            # Импортируем и вызываем обработчик фото
            from app.handlers.menu.creativity_handler import creativity_handler
            await creativity_handler.show_photo_menu(callback, state)
            
            logger.info(f"Пользователь {callback.from_user.id} вернулся в меню фото")
            
        except Exception as e:
            logger.exception(f"Ошибка возврата в меню фото: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def back_to_projects(self, callback: CallbackQuery, state: FSMContext):
        """Возврат в меню проектов"""
        try:
            # ✅ БЫСТРЫЙ ОТВЕТ НА CALLBACK
            await callback.answer()
            
            # Импортируем и вызываем обработчик проектов
            from app.handlers.menu.projects_handler import projects_handler
            await projects_handler.show_projects_menu(callback, state)
            
            logger.info(f"Пользователь {callback.from_user.id} вернулся в меню проектов")
            
        except Exception as e:
            logger.exception(f"Ошибка возврата в меню проектов: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def back_to_avatar_menu(self, callback: CallbackQuery, state: FSMContext):
        """Возврат в меню аватаров"""
        try:
            # ✅ БЫСТРЫЙ ОТВЕТ НА CALLBACK
            await callback.answer()
            
            # Очищаем состояние
            await state.clear()
            
            # Импортируем и вызываем обработчик аватаров
            from app.handlers.avatar.main import avatar_main_handler
            await avatar_main_handler.show_avatar_menu(callback, state)
            
            logger.info(f"Пользователь {callback.from_user.id} вернулся в меню аватаров")
            
        except Exception as e:
            logger.exception(f"Ошибка возврата в меню аватаров: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)


# Создаем экземпляр обработчика
navigation_handler = NavigationHandler()

# Экспортируем роутер
router = navigation_handler.router 