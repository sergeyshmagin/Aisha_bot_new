"""
Современный обработчик личного кабинета и настроек
Миграция функциональности из старого profile модуля с улучшенным UX/UI
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from decimal import Decimal

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.core.di import get_user_service, get_avatar_service
from app.core.logger import get_logger
from app.shared.handlers.base_handler import BaseHandler
from app.shared.decorators.auth_decorators import require_user
from app.database.models import AvatarStatus

logger = get_logger(__name__)


class ModernProfileHandler(BaseHandler):
    """
    Современный обработчик личного кабинета
    Объединяет профиль, баланс, статистику и настройки в едином интерфейсе
    """
    
    def __init__(self):
        super().__init__()
        self.router = Router(name="modern_profile")
        
        # Тарифные планы для пополнения
        self.topup_packages = [
            {"amount": 150, "price_kzt": 1500, "price_rub": 300, "bonus": 0, "popular": False},
            {"amount": 250, "price_kzt": 2500, "price_rub": 500, "bonus": 25, "popular": True},
            {"amount": 500, "price_kzt": 5000, "price_rub": 1000, "bonus": 70, "popular": False},
            {"amount": 1000, "price_kzt": 10000, "price_rub": 2000, "bonus": 200, "popular": False},
        ]
        
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрирует обработчики callback_data"""
        
        # === ОСНОВНЫЕ МЕНЮ ===
        self.router.callback_query.register(
            self.show_profile_dashboard,
            F.data == "profile_dashboard"
        )
        
        self.router.callback_query.register(
            self.show_settings_menu,
            F.data == "settings_menu_v2"
        )
        
        # === ПРОФИЛЬ И БАЛАНС ===
        self.router.callback_query.register(
            self.show_balance_info,
            F.data == "profile_balance_info"
        )
        
        self.router.callback_query.register(
            self.show_topup_menu,
            F.data == "profile_topup_balance"
        )
        
        self.router.callback_query.register(
            self.process_topup_package,
            F.data.startswith("topup_package_")
        )
        
        # === СТАТИСТИКА ===
        self.router.callback_query.register(
            self.show_statistics,
            F.data == "profile_statistics"
        )
        
        self.router.callback_query.register(
            self.show_achievements,
            F.data == "stats_achievements"
        )
        
        self.router.callback_query.register(
            self.show_activity_chart,
            F.data == "stats_activity_chart"
        )
        
        # === НАСТРОЙКИ ===
        self.router.callback_query.register(
            self.show_profile_settings,
            F.data == "profile_settings"
        )
        
        self.router.callback_query.register(
            self.show_notifications_settings,
            F.data == "settings_notifications"
        )
        
        self.router.callback_query.register(
            self.show_language_settings,
            F.data == "settings_language"
        )
        
        self.router.callback_query.register(
            self.show_privacy_settings,
            F.data == "settings_privacy"
        )
        
        # === ПОДДЕРЖКА ===
        self.router.callback_query.register(
            self.show_profile_help,
            F.data == "profile_help"
        )
        
        self.router.callback_query.register(
            self.show_profile_support,
            F.data == "profile_support"
        )
        
        # === LEGACY ПОДДЕРЖКА ===
        self.router.callback_query.register(
            self.show_profile_dashboard,
            F.data == "profile_menu"  # Старый callback
        )

    # === ОСНОВНЫЕ МЕНЮ ===
    
    @require_user()
    async def show_profile_dashboard(
        self, 
        callback: CallbackQuery, 
        state: FSMContext,
        user=None
    ):
        """Показывает современную панель управления профилем"""
        try:
            await state.clear()
            
            # Собираем данные профиля
            profile_data = await self._gather_profile_data(user)
            
            text = f"""🏠 <b>Личный кабинет</b>

{self._get_status_emoji(profile_data)} <b>{user.first_name}</b> • {self._get_status_text(profile_data)}
{self._format_member_since(profile_data['member_since_days'])}

💰 <b>Баланс:</b> {profile_data['balance']:.0f} монет {self._get_balance_indicator(profile_data['balance'])}

📊 <b>Активность</b>
🎭 Аватары: {profile_data['completed_avatars']}/{profile_data['avatars_count']}
🎨 Генераций: {profile_data['generations_count']}
📈 За сегодня: {profile_data.get('today_generations', 5)}

{self._get_profile_tip(profile_data)}"""

            keyboard = self._build_profile_dashboard_keyboard(profile_data)
            
            await self.safe_edit_message(
                callback=callback,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            await callback.answer()
            logger.info(f"Показана панель профиля для пользователя {user.telegram_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка показа панели профиля: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def show_settings_menu(self, callback: CallbackQuery, state: FSMContext):
        """Показывает меню настроек"""
        try:
            text = """⚙️ <b>Настройки</b>

Персонализируйте работу с ботом:
• 👤 Управление профилем и данными  
• 🔔 Настройки уведомлений
• 🌍 Язык и регион
• 🔒 Приватность и безопасность

💡 <i>Настройте бота под свои потребности</i>"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👤 Профиль",
                        callback_data="profile_dashboard"
                    ),
                    InlineKeyboardButton(
                        text="🔔 Уведомления", 
                        callback_data="settings_notifications"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🌍 Язык",
                        callback_data="settings_language"
                    ),
                    InlineKeyboardButton(
                        text="🔒 Приватность",
                        callback_data="settings_privacy"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="◀️ Главное меню",
                        callback_data="main_menu"
                    )
                ]
            ])
            
            await self.safe_edit_message(
                callback,
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            await callback.answer()
            logger.info("Показано меню настроек")
            
        except Exception as e:
            logger.exception(f"Ошибка показа меню настроек: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    # === БАЛАНС И ПОПОЛНЕНИЕ ===
    
    @require_user()
    async def show_balance_info(
        self, 
        callback: CallbackQuery, 
        state: FSMContext,
        user=None
    ):
        """Показывает детальную информацию о балансе"""
        try:
            async with get_user_service() as user_service:
                current_balance = await user_service.get_user_balance(user.id)
            
            spending_info = await self._get_spending_info(user)
            
            status_emoji, status_text = self._get_balance_status(current_balance)
            
            text = f"""💰 <b>Информация о балансе</b>

{status_emoji} <b>Текущий баланс:</b> {current_balance:.0f} монет

📊 <b>Статистика трат</b>
• Сегодня: {spending_info['today_spent']} монет
• За неделю: {spending_info['week_spent']} монет  
• За месяц: {spending_info['month_spent']} монет
• Всего потрачено: {spending_info['total_spent']} монет

📈 <b>Аналитика</b>
• Среднее в день: {spending_info['average_daily']} монет
• Любимая функция: {spending_info['favorite_feature']}

💡 <b>Рекомендации:</b>
{self._get_balance_recommendations(current_balance)}"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Пополнить баланс",
                        callback_data="profile_topup_balance"
                    ),
                    InlineKeyboardButton(
                        text="📈 История",
                        callback_data="balance_history"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 В профиль",
                        callback_data="profile_dashboard"
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
            logger.exception(f"Ошибка показа информации о балансе: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    @require_user()
    async def show_topup_menu(
        self, 
        callback: CallbackQuery, 
        state: FSMContext,
        user=None
    ):
        """Показывает современное меню пополнения баланса"""
        try:
            async with get_user_service() as user_service:
                current_balance = await user_service.get_user_balance(user.id)
            
            text = f"""💳 <b>Пополнение баланса</b>

💰 Текущий баланс: {current_balance:.0f} монет

<b>💎 Выберите пакет пополнения:</b>

💡 <i>Чем больше пакет, тем выгоднее бонус!</i>"""
            
            buttons = []
            for i, package in enumerate(self.topup_packages):
                button_text = f"{package['amount']} монет"
                if package['bonus'] > 0:
                    button_text += f" (+{package['bonus']} 🎁)"
                
                if package['popular']:
                    button_text = f"⭐ {button_text}"
                
                price_text = f" • {package['price_kzt']} ₸"
                button_text += price_text
                
                buttons.append([
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"topup_package_{i}"
                    )
                ])
            
            buttons.append([
                InlineKeyboardButton(
                    text="🔙 К балансу",
                    callback_data="profile_balance_info"
                )
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            await self.safe_edit_message(
                callback=callback,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"Ошибка показа меню пополнения: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def process_topup_package(self, callback: CallbackQuery):
        """Обрабатывает выбор пакета пополнения"""
        try:
            package_id = int(callback.data.split("_")[-1])
            
            if package_id >= len(self.topup_packages):
                await callback.answer("❌ Неверный пакет", show_alert=True)
                return
            
            package = self.topup_packages[package_id]
            
            total_coins = package['amount'] + package['bonus']
            
            text = f"""💳 <b>Подтверждение покупки</b>

📦 <b>Пакет:</b> {package['amount']} монет
🎁 <b>Бонус:</b> +{package['bonus']} монет
💎 <b>Итого получите:</b> {total_coins} монет

💰 <b>К оплате:</b> {package['price_kzt']} ₸ / {package['price_rub']} ₽

<b>Выберите способ оплаты:</b>"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💳 Kaspi Pay",
                        callback_data=f"pay_kaspi_{package_id}"
                    ),
                    InlineKeyboardButton(
                        text="🏦 СБП (РФ)",
                        callback_data=f"pay_sbp_{package_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🌐 Другие способы",
                        callback_data=f"pay_other_{package_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Выбрать другой пакет",
                        callback_data="profile_topup_balance"
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
            logger.exception(f"Ошибка обработки пакета пополнения: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    # === СТАТИСТИКА И ДОСТИЖЕНИЯ ===
    
    @require_user()
    async def show_statistics(
        self, 
        callback: CallbackQuery, 
        state: FSMContext,
        user=None
    ):
        """Показывает статистику пользователя"""
        try:
            stats = await self._gather_user_stats(user)
            
            level_emoji, level_text = self._get_user_level(stats['generations_total'])
            efficiency = min(100, (stats['generations_total'] / max(1, stats['member_since_days'])) * 10)
            
            text = f"""📊 <b>Статистика активности</b>

{level_emoji} <b>Уровень:</b> {level_text}
⚡ <b>Эффективность:</b> {efficiency:.1f}%

🎨 <b>Генерации</b>
• Всего: {stats['generations_total']}
• Сегодня: {stats['generations_today']}
• За неделю: {stats['generations_week']}
• За месяц: {stats['generations_month']}

🎭 <b>Аватары</b>
• Всего: {stats['avatars_total']}
• Готовых: {stats['avatars_completed']}
• В обучении: {stats['avatars_training']}

📈 <b>Активность</b>
• Дней с нами: {stats['member_since_days']}
• Среднее в день: {stats['average_daily_usage']}
• Любимый стиль: {stats['favorite_style']}

💰 <b>Потрачено всего:</b> {stats['total_spent']} монет"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🏆 Достижения",
                        callback_data="stats_achievements"
                    ),
                    InlineKeyboardButton(
                        text="📈 График",
                        callback_data="stats_activity_chart"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 В профиль",
                        callback_data="profile_dashboard"
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
            logger.info(f"Показана статистика пользователя {user.telegram_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка показа статистики: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def show_achievements(self, callback: CallbackQuery):
        """Показывает достижения пользователя"""
        try:
            achievements = await self._get_user_achievements(callback.from_user.id)
            
            text = f"""🏆 <b>Достижения</b>

<b>🎖️ Получено ({achievements['earned']}/{achievements['total']}):</b>

{"🥇" if achievements['first_avatar'] else "⭕"} <b>Первый аватар</b>
{"🥈" if achievements['power_user'] else "⭕"} <b>Активный пользователь</b>
{"🥉" if achievements['big_spender'] else "⭕"} <b>Щедрый пользователь</b>
{"🏆" if achievements['veteran'] else "⭕"} <b>Ветеран платформы</b>
{"⭐" if achievements['premium'] else "⭕"} <b>Premium пользователь</b>

<b>🎯 В процессе:</b>
• Мастер генерации (78/100)
• Коллекционер стилей (4/10)
• Ранняя пташка (15/30 дней)

💡 <i>Достижения дают бонусы к балансу!</i>"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
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

⏰ <b>Пиковые часы работы</b>
09:00-12:00   ████████░░ 80%
12:00-15:00   ██████████ 100%
15:00-18:00   █████████░ 90%
18:00-21:00   ██████░░░░ 60%

📈 <b>Выводы и рекомендации</b>
• Пик активности: Среда 12:00-15:00
• Самый продуктивный день: Четверг
• Рекомендуемое время: будние дни утром"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
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

    # === НАСТРОЙКИ ===
    
    @require_user()
    async def show_profile_settings(
        self, 
        callback: CallbackQuery, 
        state: FSMContext,
        user=None
    ):
        """Показывает настройки профиля"""
        try:
            text = f"""⚙️ <b>Настройки профиля</b>

👤 <b>Основная информация</b>
• Имя: {user.first_name}
• Username: @{user.username or 'не указан'}
• Язык: {user.language_code.upper() if user.language_code else 'RU'}
• Часовой пояс: {user.timezone or 'UTC+5'}

🔔 <b>Уведомления</b>
• О завершении аватаров: ✅ Включены
• О пополнении баланса: ✅ Включены
• Новости и обновления: ✅ Включены

🎨 <b>Интерфейс</b>
• Тема: Автоматическая
• Компактный режим: ❌ Отключен

💰 <b>Платежи</b>
• Автопополнение: ❌ Отключено
• Уведомления об оплате: ✅ Включены"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔔 Уведомления",
                        callback_data="settings_notifications"
                    ),
                    InlineKeyboardButton(
                        text="🌍 Язык",
                        callback_data="settings_language"
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
                        text="🔙 К настройкам",
                        callback_data="settings_menu_v2"
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
            logger.exception(f"Ошибка показа настроек профиля: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def show_notifications_settings(self, callback: CallbackQuery):
        """Настройки уведомлений"""
        text = """🔔 <b>Настройки уведомлений</b>

<b>📱 Уведомления в боте</b>
✅ О завершении аватаров
✅ О пополнении баланса  
✅ Важные обновления
❌ Маркетинговые сообщения

<b>📧 Email уведомления</b>
❌ Еженедельные отчеты
❌ Специальные предложения

<b>⏰ Время уведомлений</b>
• С 09:00 до 21:00
• Выходные: включены

💡 <i>Настройки уведомлений в разработке</i>"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 К настройкам",
                    callback_data="profile_settings"
                )
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer("🔔 Полные настройки уведомлений в разработке!", show_alert=True)

    async def show_language_settings(self, callback: CallbackQuery):
        """Настройки языка"""
        text = """🌍 <b>Язык и регион</b>

<b>🗣️ Язык интерфейса</b>
🇷🇺 Русский (текущий)
🇺🇸 English
🇰🇿 Қазақша

<b>🌏 Регион</b>
🇰🇿 Казахстан (текущий)
🇷🇺 Россия
🌍 Другой

<b>⏰ Часовой пояс</b>
📍 UTC+5 Алматы (текущий)

💡 <i>Смена языка будет доступна в следующих обновлениях</i>"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 К настройкам",
                    callback_data="profile_settings"
                )
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer("🌍 Смена языка в разработке!", show_alert=True)

    async def show_privacy_settings(self, callback: CallbackQuery):
        """Настройки приватности"""
        text = """🔒 <b>Приватность и безопасность</b>

<b>👥 Видимость профиля</b>
✅ Базовая статистика доступна
❌ Детальная аналитика скрыта
❌ История активности приватна

<b>📊 Сбор данных</b>
✅ Аналитика использования
✅ Статистика генераций
❌ Персонализированная реклама

<b>🔐 Безопасность</b>
• Двухфакторная аутентификация: ❌
• Резервные копии: ✅ Автоматически
• Логи активности: 30 дней

💡 <i>Мы защищаем вашу приватность согласно политике конфиденциальности</i>"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Политика конфиденциальности",
                    url="https://aibots.kz/privacy"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 К настройкам",
                    callback_data="profile_settings"
                )
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    # === ПОДДЕРЖКА ===
    
    async def show_profile_help(self, callback: CallbackQuery):
        """Показывает справку по профилю"""
        text = """❓ <b>Справка по личному кабинету</b>

<b>💰 Баланс и оплата</b>
• Монеты списываются за каждую генерацию
• Пакеты дают бонусные монеты
• Оплата через Kaspi Pay и банковские карты

<b>🎭 Аватары</b>
• Создавайте персональные аватары из своих фото
• Время обучения: 15-30 минут
• Генерируйте до 100 изображений с одного аватара

<b>📊 Статистика</b>
• Отслеживайте использование и эффективность
• Получайте достижения за активность
• Анализируйте пиковые часы работы

<b>⚙️ Настройки</b>
• Персонализируйте уведомления
• Управляйте приватностью
• Настраивайте интерфейс

<b>🆘 Нужна помощь?</b>
Обратитесь в техподдержку!"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Техподдержка",
                    callback_data="profile_support"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 В профиль",
                    callback_data="profile_dashboard"
                )
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    async def show_profile_support(self, callback: CallbackQuery):
        """Показывает контакты поддержки"""
        text = """💬 <b>Техническая поддержка</b>

<b>📞 Контакты</b>
• Telegram: @aibots_support
• Email: support@aibots.kz
• Время работы: 09:00-21:00 (UTC+5)

<b>❓ Частые вопросы</b>
• Как создать аватар?
• Почему не работает генерация?
• Как пополнить баланс?
• Проблемы с оплатой

<b>🔧 Самостоятельное решение</b>
• Перезапустите бота: /start
• Проверьте баланс
• Убедитесь в стабильном интернете

<b>📝 Обращение в поддержку</b>
Опишите проблему максимально подробно:
• Что делали
• Что ожидали
• Что получили
• Скриншоты (если есть)

Мы стараемся отвечать в течение 2-х часов!"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать в поддержку",
                    url="https://t.me/aibots_support"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 К справке",
                    callback_data="profile_help"
                )
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    async def _gather_profile_data(self, user) -> Dict[str, Any]:
        """Собирает данные для профиля"""
        data = {
            'balance': 0.0,
            'avatars_count': 0,
            'completed_avatars': 0,
            'generations_count': 0,
            'member_since_days': 0,
            'premium': user.is_premium if hasattr(user, 'is_premium') else False,
            'timezone': user.timezone or "UTC+5",
            'today_generations': 5  # Mock data
        }
        
        try:
            async with get_user_service() as user_service:
                data['balance'] = await user_service.get_user_balance(user.id)
            
            async with get_avatar_service() as avatar_service:
                avatars = await avatar_service.get_user_avatars(user.id)
                data['avatars_count'] = len(avatars)
                data['completed_avatars'] = len([a for a in avatars if a.status == AvatarStatus.COMPLETED])
                data['generations_count'] = sum(a.generations_count for a in avatars)
            
            if user.created_at:
                if isinstance(user.created_at, str):
                    created_dt = datetime.fromisoformat(user.created_at.replace('Z', '+00:00'))
                    created_dt = created_dt.replace(tzinfo=None)
                else:
                    created_dt = user.created_at
                    if created_dt.tzinfo is not None:
                        created_dt = created_dt.replace(tzinfo=None)
                        
                data['member_since_days'] = (datetime.utcnow() - created_dt).days
                
        except Exception as e:
            logger.exception(f"Ошибка сбора данных профиля: {e}")
        
        return data

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
            'favorite_style': 'Реалистичный',
            'total_spent': 1250,
            'average_daily_usage': 15
        }
        
        try:
            async with get_user_service() as user_service:
                stats['balance'] = await user_service.get_user_balance(user.id)
            
            async with get_avatar_service() as avatar_service:
                avatars = await avatar_service.get_user_avatars(user.id)
                stats['avatars_total'] = len(avatars)
                stats['avatars_completed'] = len([a for a in avatars if a.status == AvatarStatus.COMPLETED])
                stats['avatars_training'] = len([a for a in avatars if a.status == AvatarStatus.TRAINING])
                stats['generations_total'] = sum(a.generations_count for a in avatars)
            
            if user.created_at:
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

    async def _get_spending_info(self, user) -> Dict[str, Any]:
        """Получает информацию о тратах пользователя"""
        return {
            'today_spent': 25,
            'week_spent': 180,
            'month_spent': 650,
            'total_spent': 2340,
            'average_daily': 15,
            'favorite_feature': 'Генерация изображений'
        }

    async def _get_user_achievements(self, telegram_id: str) -> Dict[str, Any]:
        """Получает достижения пользователя"""
        return {
            'total': 5,
            'earned': 3,
            'first_avatar': True,
            'power_user': True,
            'big_spender': True,
            'veteran': False,
            'premium': False
        }

    def _get_status_emoji(self, profile_data: Dict[str, Any]) -> str:
        """Возвращает эмодзи статуса пользователя"""
        return "👑" if profile_data['premium'] else "👤"

    def _get_status_text(self, profile_data: Dict[str, Any]) -> str:
        """Возвращает текст статуса пользователя"""
        return "Premium" if profile_data['premium'] else "Стандарт"

    def _format_member_since(self, days: int) -> str:
        """Форматирует период членства"""
        if days == 0:
            return "🎉 Новый пользователь"
        elif days < 7:
            return f"🌱 С нами {days} дн."
        elif days < 30:
            weeks = days // 7
            return f"🌿 С нами {weeks} нед."
        elif days < 365:
            months = days // 30
            return f"🌳 С нами {months} мес."
        else:
            years = days // 365
            return f"🏆 С нами {years} г."

    def _get_balance_indicator(self, balance: float) -> str:
        """Возвращает индикатор состояния баланса"""
        if balance >= 200:
            return "🟢"
        elif balance >= 100:
            return "🟡"
        elif balance >= 50:
            return "🟠"
        else:
            return "🔴"

    def _get_profile_tip(self, profile_data: Dict[str, Any]) -> str:
        """Возвращает подсказку для профиля"""
        if profile_data['avatars_count'] == 0:
            return "\n💡 <i>Создайте первый аватар для начала генерации!</i>"
        elif profile_data['balance'] < 50:
            return "\n💡 <i>Рекомендуем пополнить баланс для продолжения работы</i>"
        else:
            return "\n🚀 <i>Всё готово для создания потрясающих изображений!</i>"

    def _get_balance_status(self, balance: float) -> tuple:
        """Возвращает статус баланса"""
        if balance >= 200:
            return "🟢", "Отличный баланс"
        elif balance >= 100:
            return "🟡", "Средний баланс"
        elif balance >= 50:
            return "🟠", "Низкий баланс"
        else:
            return "🔴", "Критически низкий баланс"

    def _get_balance_recommendations(self, balance: float) -> str:
        """Возвращает рекомендации по балансу"""
        if balance >= 200:
            return "• Отличный баланс для активной работы\n• Используйте пакеты для бонусов"
        elif balance >= 100:
            return "• Хороший баланс для регулярного использования\n• Рассмотрите пополнение пакетами"
        elif balance >= 50:
            return "• Рекомендуем пополнить баланс\n• Выбирайте пакеты с бонусами"
        else:
            return "• Срочно пополните баланс\n• Воспользуйтесь промокодами"

    def _get_user_level(self, generations: int) -> tuple:
        """Возвращает уровень пользователя"""
        if generations >= 100:
            return "🏆", "Эксперт"
        elif generations >= 50:
            return "💎", "Продвинутый"
        elif generations >= 20:
            return "⭐", "Активный"
        else:
            return "🌱", "Новичок"

    def _build_profile_dashboard_keyboard(self, profile_data: Dict[str, Any]) -> InlineKeyboardMarkup:
        """Строит клавиатуру панели профиля"""
        buttons = []
        
        # Первая строка: Баланс и пополнение
        balance_text = f"💰 Баланс ({profile_data['balance']:.0f})"
        buttons.append([
            InlineKeyboardButton(
                text=balance_text,
                callback_data="profile_balance_info"
            ),
            InlineKeyboardButton(
                text="➕ Пополнить",
                callback_data="profile_topup_balance"
            )
        ])
        
        # Вторая строка: Статистика и настройки
        buttons.append([
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="profile_statistics"
            ),
            InlineKeyboardButton(
                text="⚙️ Настройки",
                callback_data="profile_settings"
            )
        ])
        
        # Третья строка: Мои данные  
        buttons.append([
            InlineKeyboardButton(
                text="🎭 Мои аватары",
                callback_data="avatar_menu"
            ),
            InlineKeyboardButton(
                text="🖼️ Галерея",
                callback_data="my_gallery"
            )
        ])
        
        # Четвертая строка: Помощь и главное меню
        buttons.append([
            InlineKeyboardButton(
                text="❓ Справка",
                callback_data="profile_help"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)


# Создаем экземпляр современного обработчика
modern_profile_handler = ModernProfileHandler()

# Экспортируем роутер
router = modern_profile_handler.router

# === LEGACY SUPPORT ===
# Оставляем для совместимости со старыми callback'ами
class SettingsMenuHandler(BaseHandler):
    """LEGACY: Обработчик настроек - перенаправляет на современный интерфейс"""
    
    def __init__(self):
        super().__init__()
        self.router = Router(name="settings_legacy")
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрирует LEGACY обработчики"""
        self.router.callback_query.register(
            self.redirect_to_modern,
            F.data == "settings_menu"
        )
    
    async def redirect_to_modern(self, callback: CallbackQuery, state: FSMContext):
        """LEGACY: Перенаправляет на современный интерфейс"""
        await modern_profile_handler.show_settings_menu(callback, state)


# LEGACY экземпляр для совместимости
settings_menu_handler = SettingsMenuHandler() 