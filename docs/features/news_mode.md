Фича: Просмотр новостей в отдельном потоке через DeepLink
Проект: Aisha v2
Цель: UX-изоляция новостей от основного чата
Архитектура: Clean Architecture
Стек: aiogram 3.x, SQLAlchemy 2.x (async), FSM, OpenAI API

🎯 Описание
Пользователь получает доступ к последним новостям в виде карточек через специальный режим общения с ботом (/start news). Это позволяет:

Не засорять основной диалог

Сфокусироваться на чтении новостей

Удобно листать их постранично

Получать краткую выжимку через OpenAI Assistant API

🧩 Компоненты архитектуры
Слой	Реализация
Presentation	handlers/news/news_viewer.py (FSM, Deeplink)
Business Logic	services/news/news_service.py, summary_service.py
Data Access	repositories/news_repository.py
UI	keyboards/news.py, texts/news.py
External API	OpenAI Assistants API
State Management	FSM NewsStates.viewing

🛠 План внедрения
1. ✅ Модель NewsMessage
Добавить поле summary:

python
Копировать
Редактировать
summary = Column(Text, nullable=True)
2. ✅ FSM состояние
python
Копировать
Редактировать
# app/handlers/news/states.py
from aiogram.fsm.state import State, StatesGroup

class NewsStates(StatesGroup):
    viewing = State()
3. ✅ Хендлер запуска по deeplink start=news
python
Копировать
Редактировать
# app/handlers/news/news_viewer.py

@router.message(CommandStart(deep_link="news"))
async def start_news_mode(message: Message, state: FSMContext):
    await state.set_state(NewsStates.viewing)
    await send_news_page(message.chat.id, page=0)
4. ✅ Функция send_news_page
python
Копировать
Редактировать
async def send_news_page(chat_id: int, page: int = 0, edit=False, message_id=None):
    offset = page * 3
    async with get_news_service() as svc:
        news = await svc.repo.get_latest(limit=3, offset=offset)

    if not news:
        await bot.send_message(chat_id, "😕 Новостей пока нет.")
        return

    buttons = []
    for item in news:
        summary = item.summary or item.text[:300]
        buttons.append([
            InlineKeyboardButton("📎 Читать оригинал", url=f"https://t.me/{item.channel}/{item.message_id}")
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"news_page:{page - 1}"))
    if len(news) == 3:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"news_page:{page + 1}"))
    if nav:
        buttons.append(nav)

    if edit:
        await bot.edit_message_text(chat_id, message_id, "<b>📰 Новости</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
    else:
        await bot.send_message(chat_id, "<b>📰 Новости</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
5. ✅ Callback-хендлер пагинации
python
Копировать
Редактировать
@router.callback_query(F.data.startswith("news_page:"))
async def paginate_news(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await send_news_page(chat_id=callback.message.chat.id, page=page, edit=True, message_id=callback.message.message_id)
6. ✅ Кнопка в главном меню
python
Копировать
Редактировать
# keyboards/main.py
InlineKeyboardButton(
    text="📰 Новости",
    url="https://t.me/YOUR_BOT_USERNAME?start=news"
)
7. ⛔ Выход из режима новостей (по команде)
python
Копировать
Редактировать
@router.message(Command("назад"))
async def exit_news_mode(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔙 Возвращаемся в главное меню.")
📦 Поддержка AI-анализов
Используем уже существующий NewsSummaryService, подключённый к OpenAI Assistant API:

python
Копировать
Редактировать
summary = await summary_service.summarize_news(text=item.text)
Готовая карточка новостей содержит:

канал

дату

суть

кнопку «Читать оригинал»

🧪 Тестирование
pytest-asyncio

tests/handlers/test_news_viewer.py — тесты FSM и пагинации

tests/services/test_summary_service.py — мок Assistant API

🧾 Пример deeplink
arduino
Копировать
Редактировать
https://t.me/aisha_bot?start=news
✅ Результат для пользователя
Лента новостей из каналов

Только выжимка, без лишнего шума

Быстрая навигация

Не мешает остальной работе Aisha

📌 Todo
 Добавить news_viewer.py, states.py

 Обновить main_menu.py, клавиатуру

 Добавить миграцию add_summary_to_news_messages

 Обновить документацию (docs/features/news_mode.md)

