"""
LEGACY: Обработчик статистики пользователя
Функциональность мигрирована в app/handlers/menu/settings_handler.py
Оставлен для совместимости со старыми callback'ами
"""
from datetime import datetime, timedelta
from typing import Dict, Any

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.core.di import get_user_service, get_avatar_service
from app.core.logger import get_logger
from app.shared.handlers.base_handler import BaseHandler
from app.shared.decorators.auth_decorators import require_user
from app.database.models import AvatarStatus

logger = get_logger(__name__)
router = Router()


class StatsHandler(BaseHandler):
    """Обработчик статистики пользователя"""
    
    def __init__(self):
        super().__init__()
    
    @require_user()
    async def show_statistics(
        self, 
        callback: CallbackQuery, 
        state: FSMContext,
        user=None
    ):
        """Показывает общую статистику пользователя"""
        try:
            # Собираем статистику
            stats = await self._gather_user_stats(user)
            
            text = self._build_stats_text(user, stats)
            keyboard = self._build_stats_keyboard()
            
            await self.safe_edit_message(
                callback=callback,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            await callback.answer()
            logger.info(f"Показана статистика пользователя {user.telegram_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка показа статистики: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def show_achievements(self, callback: CallbackQuery):
        """Показывает достижения пользователя"""
        try:
            # Получаем достижения пользователя
            achievements = await self._get_user_achievements(callback.from_user.id)
            
            text = self._build_achievements_text(achievements)
            keyboard = self._build_achievements_keyboard()
            
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"Ошибка показа достижений: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def show_activity_chart(self, callback: CallbackQuery):
        """Показывает график активности"""
        try:
            text = """📊 <b>График активности</b>

📈 <b>Активность по дням недели</b>
Понедельник    ████████░░ 80%
Вторник       ████████░░ 75%
Среда         ██████████ 100%
Четверг       █████████░ 90%
Пятница       ███████░░░ 70%
Суббота       ████░░░░░░ 40%
Воскресенье   ██░░░░░░░░ 20%

⏰ <b>Активность по часам</b>
06:00-09:00   ██░░░░░░░░ 20%
09:00-12:00   ████████░░ 80%
12:00-15:00   ██████████ 100%
15:00-18:00   █████████░ 90%
18:00-21:00   ██████░░░░ 60%
21:00-00:00   ████░░░░░░ 40%

📈 <b>Выводы</b>
• Пик активности: Среда 12:00-15:00
• Самый продуктивный день: Четверг
• Рекомендуемое время для генерации: утро"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📈 Детальная аналитика",
                        url="https://aibots.kz/analytics"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 К статистике",
                        callback_data="profile_statistics"
                    )
                ]
            ])
            
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"Ошибка показа графика активности: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def _gather_user_stats(self, user) -> Dict[str, Any]:
        """Собирает статистику пользователя"""
        stats = {
            'balance': 0.0,
            'avatars_total': 0,
            'avatars_completed': 0,
            'avatars_training': 0,
            'generations_total': 0,
            'generations_today': 5,
            'generations_week': 32,
            'generations_month': 156,
            'member_since_days': 0,
            'last_activity': datetime.utcnow(),
            'favorite_style': 'Реалистичный',
            'total_spent': 1250,
            'average_daily_usage': 15
        }
        
        try:
            # Баланс
            async with get_user_service() as user_service:
                stats['balance'] = await user_service.get_user_balance(user.id)
            
            # Аватары
            async with get_avatar_service() as avatar_service:
                avatars = await avatar_service.get_user_avatars(user.id)
                stats['avatars_total'] = len(avatars)
                stats['avatars_completed'] = len([a for a in avatars if a.status == AvatarStatus.COMPLETED])
                stats['avatars_training'] = len([a for a in avatars if a.status == AvatarStatus.TRAINING])
                stats['generations_total'] = sum(a.generations_count for a in avatars)
            
            # Дни с регистрации
            if user.created_at:
                # Приводим created_at к datetime если это строка
                if isinstance(user.created_at, str):
                    created_dt = datetime.fromisoformat(user.created_at.replace('Z', '+00:00'))
                    created_dt = created_dt.replace(tzinfo=None)
                else:
                    created_dt = user.created_at
                    if created_dt.tzinfo is not None:
                        created_dt = created_dt.replace(tzinfo=None)
                        
                stats['member_since_days'] = (datetime.utcnow() - created_dt).days
                
        except Exception as e:
            logger.exception(f"Ошибка сбора статистики: {e}")
        
        return stats
    
    def _build_stats_text(self, user, stats: Dict[str, Any]) -> str:
        """Формирует текст статистики"""
        
        # Уровень активности
        if stats['generations_total'] >= 100:
            level_emoji = "🏆"
            level_text = "Эксперт"
        elif stats['generations_total'] >= 50:
            level_emoji = "💎"
            level_text = "Продвинутый"
        elif stats['generations_total'] >= 20:
            level_emoji = "⭐"
            level_text = "Активный"
        else:
            level_emoji = "🌱"
            level_text = "Новичок"
        
        # Эффективность
        efficiency = min(100, (stats['generations_total'] / max(1, stats['member_since_days'])) * 10)
        
        text = f"""📊 <b>Статистика активности</b>

{level_emoji} <b>Уровень:</b> {level_text}
📅 <b>С нами:</b> {stats['member_since_days']} дней

🎨 <b>Генерации изображений</b>
• Всего: {stats['generations_total']}
• Сегодня: {stats['generations_today']}
• За неделю: {stats['generations_week']}
• За месяц: {stats['generations_month']}

🎭 <b>Аватары</b>
• Создано: {stats['avatars_completed']}
• В обучении: {stats['avatars_training']}
• Всего: {stats['avatars_total']}

💰 <b>Экономика</b>
• Потрачено: {stats['total_spent']} монет
• В среднем в день: {stats['average_daily_usage']} монет
• Текущий баланс: {stats['balance']:.0f} монет

📈 <b>Эффективность:</b> {efficiency:.1f}%
🎨 <b>Любимый стиль:</b> {stats['favorite_style']}"""

        return text
    
    def _build_stats_keyboard(self) -> InlineKeyboardMarkup:
        """Строит клавиатуру статистики"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏆 Достижения",
                    callback_data="stats_achievements"
                ),
                InlineKeyboardButton(
                    text="📈 График активности",
                    callback_data="stats_activity_chart"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Сравнить с другими",
                    callback_data="stats_leaderboard"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🌐 Веб-аналитика",
                    url="https://aibots.kz/analytics"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="profile_menu"
                )
            ]
        ])
    
    async def _get_user_achievements(self, telegram_id: str) -> Dict[str, Any]:
        """Получает достижения пользователя"""
        # Пока возвращаем моковые данные
        return {
            'unlocked': [
                {"name": "Первый аватар", "icon": "🎭", "description": "Создали первый аватар"},
                {"name": "Творческий старт", "icon": "🎨", "description": "Сгенерировали 10 изображений"},
                {"name": "Постоянный клиент", "icon": "💎", "description": "Пользуетесь сервисом 7 дней подряд"},
                {"name": "Генератор идей", "icon": "💡", "description": "Использовали 5 разных стилей"},
            ],
            'locked': [
                {"name": "Мастер аватаров", "icon": "🏆", "description": "Создайте 5 аватаров"},
                {"name": "Художник", "icon": "🖼️", "description": "Сгенерируйте 100 изображений"},
                {"name": "VIP пользователь", "icon": "👑", "description": "Потратьте 1000 монет"},
            ]
        }
    
    def _build_achievements_text(self, achievements: Dict[str, Any]) -> str:
        """Формирует текст достижений"""
        text = """🏆 <b>Достижения</b>

✅ <b>Разблокированные</b>"""
        
        for achievement in achievements['unlocked']:
            text += f"\n{achievement['icon']} <b>{achievement['name']}</b>"
            text += f"\n   <i>{achievement['description']}</i>"
        
        text += "\n\n🔒 <b>Заблокированные</b>"
        
        for achievement in achievements['locked']:
            text += f"\n{achievement['icon']} <b>{achievement['name']}</b>"
            text += f"\n   <i>{achievement['description']}</i>"
        
        progress = len(achievements['unlocked']) / (len(achievements['unlocked']) + len(achievements['locked'])) * 100
        text += f"\n\n📊 <b>Прогресс:</b> {progress:.0f}% ({len(achievements['unlocked'])}/{len(achievements['unlocked']) + len(achievements['locked'])})"
        
        return text
    
    def _build_achievements_keyboard(self) -> InlineKeyboardMarkup:
        """Строит клавиатуру достижений"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎯 Как получить новые",
                    callback_data="achievements_guide"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 К статистике",
                    callback_data="profile_statistics"
                )
            ]
        ])


# Создаем экземпляр обработчика
stats_handler = StatsHandler()

# Регистрируем обработчики
@router.callback_query(F.data == "profile_statistics")
async def show_statistics_callback(callback: CallbackQuery, state: FSMContext):
    """Callback для показа статистики"""
    await stats_handler.show_statistics(callback, state)

@router.callback_query(F.data == "stats_achievements")
async def show_achievements_callback(callback: CallbackQuery):
    """Callback для показа достижений"""
    await stats_handler.show_achievements(callback)

@router.callback_query(F.data == "stats_activity_chart")
async def show_activity_chart_callback(callback: CallbackQuery):
    """Callback для показа графика активности"""
    await stats_handler.show_activity_chart(callback)

@router.callback_query(F.data == "stats_leaderboard")
async def show_leaderboard(callback: CallbackQuery):
    """Показывает рейтинг пользователей"""
    text = """📊 <b>Рейтинг пользователей</b>

🏆 <b>Топ по генерациям (эта неделя)</b>
1. 🥇 Алексей К. — 127 генераций
2. 🥈 Мария П. — 89 генераций  
3. 🥉 Дмитрий Л. — 73 генерации
4. 🏅 Анна С. — 61 генерация
5. 🏅 Иван М. — 55 генераций
...
15. 📍 <b>Вы</b> — 32 генерации

💎 <b>Топ по аватарам</b>
1. 🥇 Екатерина В. — 8 аватаров
2. 🥈 Сергей К. — 6 аватаров
3. 🥉 Ольга Н. — 5 аватаров
...
8. 📍 <b>Вы</b> — 2 аватара

🎯 <b>Ваша цель:</b> войти в топ-10!
💡 <b>Совет:</b> создайте еще аватаров для роста в рейтинге"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎨 Создать изображение",
                callback_data="generation_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎭 Создать аватар",
                callback_data="create_avatar"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 К статистике",
                callback_data="profile_statistics"
            )
        ]
    ])
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "achievements_guide")
async def show_achievements_guide(callback: CallbackQuery):
    """Показывает гайд по получению достижений"""
    text = """🎯 <b>Как получить достижения</b>

🎭 <b>Аватары</b>
• Мастер аватаров — создайте 5 аватаров
• Коллекционер — создайте 10 аватаров
• Профессионал — создайте аватар каждого типа

🎨 <b>Генерации</b>
• Художник — сгенерируйте 100 изображений
• Мастер кисти — сгенерируйте 500 изображений
• Творческий гений — сгенерируйте 1000 изображений

💰 <b>Экономика</b>
• VIP пользователь — потратьте 1000 монет
• Инвестор — потратьте 5000 монет
• Меценат — потратьте 10000 монет

📅 <b>Активность</b>
• Постоянный клиент — 7 дней подряд
• Верный друг — 30 дней подряд
• Легенда — 100 дней подряд

🎨 <b>Разнообразие</b>
• Экспериментатор — используйте 10 стилей
• Исследователь — попробуйте все функции
• Новатор — используйте кастомные промпты

💡 <b>Совет:</b> следите за прогрессом в разделе достижений!"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🏆 К достижениям",
                callback_data="stats_achievements"
            )
        ]
    ])
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer() 