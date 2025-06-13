"""
Обработчик бизнес-меню

Управляет разделом "🤖 Бизнес-ассистент"
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.shared.handlers.base_handler import BaseHandler
from app.keyboards.menu.business import get_business_menu_v2
from app.keyboards.main import get_tasks_menu, get_news_menu, get_add_to_chat_menu

logger = logging.getLogger(__name__)


class BusinessHandler(BaseHandler):
    """Обработчик бизнес-ассистента"""
    
    def __init__(self):
        super().__init__()
        self.router = Router(name="business")
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрирует обработчики callback_data"""
        # Главное меню бизнеса
        self.router.callback_query.register(
            self.show_business_menu,
            F.data == "business_menu"
        )
        
        # Подразделы
        self.router.callback_query.register(
            self.show_tasks_menu,
            F.data == "tasks_menu"
        )
        
        self.router.callback_query.register(
            self.show_news_menu,
            F.data == "news_menu"
        )
        
        self.router.callback_query.register(
            self.show_add_to_chat_menu,
            F.data == "add_to_chat"
        )
        
        # Дополнительные обработчики
        self.router.callback_query.register(
            self.show_transcribe_menu,
            F.data == "transcribe_menu"
        )
        
        # === ОБРАБОТЧИКИ НОВОСТНЫХ CALLBACK'ОВ ===
        self.router.callback_query.register(
            self.handle_my_channels,
            F.data == "my_channels"
        )
        
        self.router.callback_query.register(
            self.handle_add_channel,
            F.data == "add_channel"
        )
        
        self.router.callback_query.register(
            self.handle_trending_week,
            F.data == "trending_week"
        )
        
        self.router.callback_query.register(
            self.handle_trending_today,
            F.data == "trending_today"
        )
        
        self.router.callback_query.register(
            self.handle_content_from_news,
            F.data == "content_from_news"
        )
        
        # === ОБРАБОТЧИКИ CHAT CALLBACK'ОВ ===
        self.router.callback_query.register(
            self.handle_get_invite_link,
            F.data == "get_invite_link"
        )
        
        self.router.callback_query.register(
            self.handle_my_work_chats,
            F.data == "my_work_chats"
        )
        
        self.router.callback_query.register(
            self.handle_parsing_settings,
            F.data == "parsing_settings"
        )
        
        self.router.callback_query.register(
            self.handle_chat_analytics,
            F.data == "chat_analytics"
        )
        
        # === ОБРАБОТЧИКИ TASKS CALLBACK'ОВ ===
        self.router.callback_query.register(
            self.handle_task_create,
            F.data == "task_create"
        )
        
        self.router.callback_query.register(
            self.handle_project_list,
            F.data == "project_list"
        )
        
        self.router.callback_query.register(
            self.handle_task_list,
            F.data == "task_list"
        )
        
        self.router.callback_query.register(
            self.handle_task_analytics,
            F.data == "task_analytics"
        )
    
    async def show_business_menu(self, call: CallbackQuery, state: FSMContext):
        """Показывает главное меню бизнес-ассистента"""
        await state.clear()
        
        menu_text = """🤖 **ИИ Ассистент**

🎯 **Ваш умный помощник:**

🎯 **Задачи** - создавайте поручения с дедлайнами и следите за их выполнением
📰 **Новости** - отслеживайте важные новости и тренды по вашим темам
📝 **Голос в текст** - превращайте аудиосообщения в удобный текст
👥 **В группу** - добавьте бота в рабочий чат для анализа переписки

🚀 **Автоматизируйте рутину и экономьте время**

Выберите что нужно:"""

        try:
            await self.safe_edit_message(
                call,
                menu_text,
                reply_markup=get_business_menu_v2(),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.exception(f"Ошибка меню ИИ ассистента: {e}")
            await call.answer("❌ Ошибка загрузки меню", show_alert=True)
    
    async def show_tasks_menu(self, call: CallbackQuery, state: FSMContext):
        """Показывает меню задач"""
        await state.clear()
        
        menu_text = """📋 **Задачи**

🎯 **Управление поручениями:**

➕ **Создать** - дайте задание сотруднику с указанием срока
📊 **Мои поручения** - задачи которые вы выдали подчинённым
👥 **Команда** - все задачи команды и их статусы

⏰ **Напоминания** - автоматические уведомления о сроках
📈 **Отчеты** - статистика выполнения и эффективности

🤖 **Aisha будет напоминать о дедлайнах и собирать отчёты**

Что нужно сделать?"""

        try:
            await self.safe_edit_message(
                call,
                menu_text,
                reply_markup=get_tasks_menu(),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.exception(f"Ошибка меню задач: {e}")
            await call.answer("❌ Ошибка загрузки меню", show_alert=True)
    
    async def show_news_menu(self, call: CallbackQuery, state: FSMContext):
        """Показывает меню новостей"""
        await state.clear()
        
        menu_text = """📰 **Новости и тренды**

🚀 **Мониторинг информационного поля:**

📱 **Мои каналы** - отслеживаемые источники информации
🔥 **Трендинг** - самые обсуждаемые темы для бизнеса
🎯 **Контент из новостей** - создание материалов на актуальные темы

## 💼 Бизнес-применение:
• Отслеживание отраслевых трендов  
• Мониторинг конкурентов
• Поиск возможностей для контент-маркетинга
• Анализ рыночных изменений

Выберите действие:"""

        try:
            await self.safe_edit_message(
                call,
                menu_text,
                reply_markup=get_news_menu(),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.exception(f"Ошибка меню новостей: {e}")
            await call.answer("❌ Ошибка загрузки меню", show_alert=True)
    
    async def show_add_to_chat_menu(self, call: CallbackQuery, state: FSMContext):
        """Показывает меню добавления в чат"""
        await state.clear()
        
        menu_text = """👥 **Добавить бота в чат**

🤖 **Сделайте Aisha участником вашей команды:**

🔗 **Получить ссылку-приглашение** - добавьте бота в рабочую группу
📋 **Мои рабочие чаты** - управление подключенными чатами
⚙️ **Настройки парсинга** - что анализировать в переписке
📊 **Аналитика чатов** - статистика общения и настроений

💡 **Aisha автоматически анализирует переписку, выделяет задачи и отслеживает настроения команды**

Выберите действие:"""

        try:
            await self.safe_edit_message(
                call,
                menu_text,
                reply_markup=get_add_to_chat_menu(),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.exception(f"Ошибка меню добавления в чат: {e}")
            await call.answer("❌ Ошибка загрузки меню", show_alert=True)
    
    async def show_transcribe_menu(self, call: CallbackQuery, state: FSMContext):
        """Показывает меню транскрипции"""
        await call.answer("🎙️ Транскрипция аудио в разработке!", show_alert=True)
    
    # === ОБРАБОТЧИКИ НОВОСТНЫХ CALLBACK'ОВ ===
    
    async def handle_my_channels(self, call: CallbackQuery, state: FSMContext):
        """Мои каналы"""
        await call.answer("📱 Мои каналы - в разработке!\n\nСкоро здесь будет список ваших отслеживаемых каналов.", show_alert=True)
    
    async def handle_add_channel(self, call: CallbackQuery, state: FSMContext):
        """Добавить канал"""
        await call.answer("➕ Добавление каналов - в разработке!\n\nВы сможете добавлять Telegram-каналы для мониторинга.", show_alert=True)
    
    async def handle_trending_week(self, call: CallbackQuery, state: FSMContext):
        """Тренды недели"""
        await call.answer("📊 Тренды недели - в разработке!\n\nАнализ самых популярных тем за неделю.", show_alert=True)
    
    async def handle_trending_today(self, call: CallbackQuery, state: FSMContext):
        """Тренды дня"""
        await call.answer("🔥 Тренды дня - в разработке!\n\nАнализ актуальных тем за сегодня.", show_alert=True)
    
    async def handle_content_from_news(self, call: CallbackQuery, state: FSMContext):
        """Контент из новостей"""
        await call.answer("📝 Генерация контента из новостей - в разработке!\n\nСоздание постов на основе трендовых новостей.", show_alert=True)
    
    # === ОБРАБОТЧИКИ CHAT CALLBACK'ОВ ===
    
    async def handle_get_invite_link(self, call: CallbackQuery, state: FSMContext):
        """Получить ссылку-приглашение"""
        await call.answer("🔗 Получение ссылки-приглашения - в разработке!\n\nСсылка для добавления бота в группы.", show_alert=True)
    
    async def handle_my_work_chats(self, call: CallbackQuery, state: FSMContext):
        """Мои рабочие чаты"""
        await call.answer("👥 Мои рабочие чаты - в разработке!\n\nСписок подключенных групп и каналов.", show_alert=True)
    
    async def handle_parsing_settings(self, call: CallbackQuery, state: FSMContext):
        """Настройки парсинга"""
        await call.answer("⚙️ Настройки парсинга - в разработке!\n\nНастройка анализа сообщений в чатах.", show_alert=True)
    
    async def handle_chat_analytics(self, call: CallbackQuery, state: FSMContext):
        """Аналитика чатов"""
        await call.answer("📈 Аналитика чатов - в разработке!\n\nСтатистика активности и настроений в чатах.", show_alert=True)
    
    # === ОБРАБОТЧИКИ TASKS CALLBACK'ОВ ===
    
    async def handle_task_create(self, call: CallbackQuery, state: FSMContext):
        """Создать задачу"""
        await call.answer("➕ Создание задач - в разработке!\n\nИнтерфейс для создания и назначения задач.", show_alert=True)
    
    async def handle_project_list(self, call: CallbackQuery, state: FSMContext):
        """Список проектов"""
        await call.answer("📋 Список проектов - в разработке!\n\nВсе ваши проекты и их статусы.", show_alert=True)
    
    async def handle_task_list(self, call: CallbackQuery, state: FSMContext):
        """Список задач"""
        await call.answer("📝 Список задач - в разработке!\n\nВсе поставленные задачи и их выполнение.", show_alert=True)
    
    async def handle_task_analytics(self, call: CallbackQuery, state: FSMContext):
        """Аналитика задач"""
        await call.answer("📊 Аналитика задач - в разработке!\n\nСтатистика выполнения и эффективности команды.", show_alert=True)


# Создаем экземпляр и экспортируем роутер
router = BusinessHandler().router 