"""
LEGACY: Обработчик управления балансом пользователя
Функциональность мигрирована в app/handlers/menu/settings_handler.py
Оставлен для совместимости со старыми callback'ами
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.core.di import get_user_service
from app.core.logger import get_logger
from app.shared.handlers.base_handler import BaseHandler
from app.shared.decorators.auth_decorators import require_user

logger = get_logger(__name__)
router = Router()


class BalanceHandler(BaseHandler):
    """Обработчик для работы с балансом"""
    
    def __init__(self):
        super().__init__()
        # Тарифные планы для пополнения (пакеты монет)
        self.topup_packages = [
            {"amount": 150, "price_kzt": 1500, "price_rub": 300, "bonus": 0, "popular": False},
            {"amount": 250, "price_kzt": 2500, "price_rub": 500, "bonus": 25, "popular": True},
            {"amount": 500, "price_kzt": 5000, "price_rub": 1000, "bonus": 70, "popular": False},
            {"amount": 1000, "price_kzt": 10000, "price_rub": 2000, "bonus": 200, "popular": False},
        ]
    
    @require_user()
    async def show_balance_info(
        self, 
        callback: CallbackQuery, 
        state: FSMContext,
        user=None
    ):
        """Показывает детальную информацию о балансе"""
        try:
            # Получаем баланс
            async with get_user_service() as user_service:
                current_balance = await user_service.get_user_balance(user.id)
            
            text = f"""💰 <b>Информация о балансе</b>

💎 <b>Текущий баланс:</b> {current_balance:.0f} монет

📊 <b>Статистика трат</b>
• Сегодня: 25 монет
• За неделю: 180 монет  
• За месяц: 650 монет

💡 <b>Рекомендации:</b>
• Пополняйте баланс пакетами для бонусов
• Используйте промокоды
• Планируйте транскрипции заранее"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Пополнить баланс",
                        callback_data="profile_topup_balance"
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
            logger.exception(f"Ошибка показа информации о балансе: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    @require_user()
    async def show_topup_menu(
        self, 
        callback: CallbackQuery, 
        state: FSMContext,
        user=None
    ):
        """Показывает меню пополнения баланса"""
        try:
            # Получаем текущий баланс
            async with get_user_service() as user_service:
                current_balance = await user_service.get_user_balance(user.id)
            
            text = f"""💳 <b>Пополнение баланса</b>

💰 Текущий баланс: {current_balance:.0f} монет

<b>Выберите пакет пополнения:</b>

💡 <i>Чем больше пакет, тем выгоднее бонус!</i>"""
            
            buttons = []
            for i, package in enumerate(self.topup_packages):
                button_text = f"{package['amount']} монет"
                if package['bonus'] > 0:
                    button_text += f" (+{package['bonus']} бонус)"
                
                if package['popular']:
                    button_text = f"⭐ {button_text}"
                
                button_text += f" - {package['price_kzt']} ₸ / {package['price_rub']} ₽"
                
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
    
    async def show_payment_method(self, callback: CallbackQuery, package_id: int):
        """Показывает способы оплаты для выбранного пакета"""
        try:
            if package_id >= len(self.topup_packages):
                await callback.answer("❌ Неверный пакет", show_alert=True)
                return
            
            package = self.topup_packages[package_id]
            
            text = self._build_payment_text(package)
            keyboard = self._build_payment_keyboard(package_id)
            
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            await callback.answer()
            logger.info(f"Показаны способы оплаты для пакета {package['amount']} монет")
            
        except Exception as e:
            logger.exception(f"Ошибка показа способов оплаты: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def _get_spending_info(self, user) -> Dict[str, Any]:
        """Получает информацию о тратах пользователя"""
        # Пока возвращаем моковые данные
        # В будущем можно добавить таблицу транзакций
        return {
            'today_spent': 25,
            'week_spent': 180,
            'month_spent': 650,
            'total_spent': 2340,
            'average_daily': 15,
            'favorite_feature': 'Генерация изображений'
        }
    
    def _build_balance_info_text(self, balance: float, spending: Dict[str, Any]) -> str:
        """Формирует текст информации о балансе"""
        
        # Определяем статус баланса
        if balance >= 200:
            status_emoji = "🟢"
            status_text = "Отличный баланс"
        elif balance >= 100:
            status_emoji = "🟡"
            status_text = "Средний баланс"
        elif balance >= 50:
            status_emoji = "🟠"
            status_text = "Низкий баланс"
        else:
            status_emoji = "🔴"
            status_text = "Критически низкий"
        
        text = f"""💰 <b>Информация о балансе</b>

{status_emoji} <b>Текущий баланс:</b> {balance:.0f} монет
<i>{status_text}</i>

📊 <b>Статистика трат</b>
• Сегодня: {spending['today_spent']} монет
• За неделю: {spending['week_spent']} монет  
• За месяц: {spending['month_spent']} монет
• Всего потрачено: {spending['total_spent']} монет

📈 <b>Аналитика</b>
• Среднее в день: {spending['average_daily']} монет
• Любимая функция: {spending['favorite_feature']}

💡 <b>Рекомендации по экономии:</b>
• Создавайте аватары пакетами (экономия до 20%)
• Используйте готовые стили вместо кастомных промптов
• Планируйте генерации заранее"""

        # Добавляем рекомендации по пополнению
        if balance < 100:
            text += f"\n\n⚡ <b>Рекомендуем пополнить баланс</b> для комфортной работы"
            
        return text
    
    def _build_balance_info_keyboard(self) -> InlineKeyboardMarkup:
        """Строит клавиатуру информации о балансе"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Пополнить баланс",
                    callback_data="profile_topup_balance"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 История операций",
                    callback_data="balance_history"
                ),
                InlineKeyboardButton(
                    text="📈 Аналитика",
                    callback_data="balance_analytics"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="profile_menu"
                )
            ]
        ])
    
    def _build_topup_text(self, current_balance: float) -> str:
        """Формирует текст меню пополнения"""
        return f"""💳 <b>Пополнение баланса</b>

💰 Текущий баланс: {current_balance:.0f} монет

<b>Выберите пакет пополнения:</b>

💡 <i>Чем больше пакет, тем выгоднее бонус!</i>"""
    
    def _build_topup_keyboard(self) -> InlineKeyboardMarkup:
        """Строит клавиатуру пополнения баланса"""
        buttons = []
        
        for i, package in enumerate(self.topup_packages):
            # Формируем текст кнопки
            button_text = f"{package['amount']} монет"
            if package['bonus'] > 0:
                button_text += f" (+{package['bonus']} бонус)"
            
            if package['popular']:
                button_text = f"⭐ {button_text}"
            
            button_text += f" - {package['price']} ₸"
            
            buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"topup_package_{i}"
                )
            ])
        
        # Кнопка "Другая сумма"
        buttons.append([
            InlineKeyboardButton(
                text="💬 Другая сумма",
                callback_data="topup_custom"
            )
        ])
        
        # Кнопка назад
        buttons.append([
            InlineKeyboardButton(
                text="🔙 К балансу",
                callback_data="profile_balance_info"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def _build_payment_text(self, package: Dict) -> str:
        """Формирует текст выбора способа оплаты"""
        total_credits = package['amount'] + package['bonus']
        
        text = f"""💳 <b>Оплата пополнения</b>

📦 <b>Выбранный пакет:</b>
• {package['amount']} монет"""
        
        if package['bonus'] > 0:
            text += f"\n• +{package['bonus']} бонусных монет"
            
        text += f"""
• Итого: {total_credits} монет
• К оплате: {package['price_kzt']} ₸ / {package['price_rub']} ₽

<b>Выберите способ оплаты:</b>"""
        
        return text
    
    def _build_payment_keyboard(self, package_id: int) -> InlineKeyboardMarkup:
        """Строит клавиатуру способов оплаты"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Банковская карта",
                    callback_data=f"pay_card_{package_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📱 Kaspi Pay",
                    callback_data=f"pay_kaspi_{package_id}"
                ),
                InlineKeyboardButton(
                    text="🏦 Банковский перевод",
                    callback_data=f"pay_bank_{package_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Криптовалюта",
                    callback_data=f"pay_crypto_{package_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 К пакетам",
                    callback_data="profile_topup_balance"
                )
            ]
        ])


# Создаем экземпляр обработчика
balance_handler = BalanceHandler()

# Регистрируем обработчики
@router.callback_query(F.data == "profile_balance_info")
async def show_balance_info_callback(callback: CallbackQuery, state: FSMContext):
    """Callback для показа информации о балансе"""
    await balance_handler.show_balance_info(callback, state)

@router.callback_query(F.data == "profile_topup_balance")
async def show_topup_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Callback для показа меню пополнения"""
    await balance_handler.show_topup_menu(callback, state)

@router.callback_query(F.data.startswith("topup_package_"))
async def show_payment_method_callback(callback: CallbackQuery):
    """Callback для выбора пакета пополнения"""
    package_id = int(callback.data.split("_")[-1])
    await balance_handler.show_payment_method(callback, package_id)

@router.callback_query(F.data == "topup_custom")
async def show_custom_topup(callback: CallbackQuery):
    """Показывает форму для ввода произвольной суммы"""
    text = """💬 <b>Произвольная сумма</b>

Для пополнения на произвольную сумму обратитесь в поддержку:

📱 <b>Telegram:</b> @aisha_support_bot
📧 <b>Email:</b> support@aibots.kz

<b>Укажите в сообщении:</b>
• Желаемую сумму пополнения
• Ваш Telegram ID: <code>{callback.from_user.id}</code>
• Предпочитаемый способ оплаты

⏱️ <b>Время обработки:</b> до 2 часов в рабочее время"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💌 Написать в поддержку",
                url="https://t.me/aisha_support_bot"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 К пакетам",
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

@router.callback_query(F.data.startswith("pay_") & ~F.data.startswith("pay_transcription_"))
async def process_payment_method(callback: CallbackQuery):
    """Обрабатывает выбор способа оплаты (исключая транскрипцию)"""
    parts = callback.data.split("_")
    method = parts[1]  # card, kaspi, bank, crypto
    package_id = int(parts[2])
    
    # Получаем информацию о пакете
    if package_id >= len(balance_handler.topup_packages):
        await callback.answer("❌ Неверный пакет", show_alert=True)
        return
        
    package = balance_handler.topup_packages[package_id]
    
    # Создаем сообщение с инструкциями по оплате
    total_amount = package['amount'] + package['bonus']
    
    # Определяем способ оплаты для отображения
    payment_methods = {
        'card': 'Банковская карта',
        'kaspi': 'Kaspi Pay', 
        'bank': 'Банковский перевод',
        'crypto': 'Криптовалюта'
    }
    method_name = payment_methods.get(method, method)
    
    payment_text = f"""💳 <b>Оплата пакета {package['amount']} монет</b>

💰 <b>Сумма к оплате:</b> 
• {package['price_kzt']} ₸ 
• {package['price_rub']} ₽

🎁 <b>Бонус:</b> +{package['bonus']} монет
📊 <b>Итого получите:</b> {total_amount} монет
🔧 <b>Способ оплаты:</b> {method_name}

<b>Для оплаты обратитесь в поддержку:</b>

📱 <b>Telegram:</b> @aisha_support_bot
📧 <b>Email:</b> support@aibots.kz

<b>Укажите в сообщении:</b>
• Пакет: {package['amount']} монет (+{package['bonus']} бонус)
• Способ оплаты: {method_name}
• Валюта: тенге / рубли (на выбор)
• Ваш Telegram ID: <code>{callback.from_user.id}</code>

⏱️ <b>Время зачисления:</b> до 30 минут"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💌 Написать в поддержку",
                url="https://t.me/aisha_support_bot"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 К пакетам",
                callback_data="profile_topup_balance"
            )
        ]
    ])
    
    await callback.message.edit_text(
        text=payment_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "balance_history")
async def show_balance_history(callback: CallbackQuery):
    """Показывает историю операций с балансом"""
    # Пока показываем заглушку
    text = """📊 <b>История операций</b>

<b>Последние операции:</b>

<code>📈 +250</code> Пополнение баланса
<i>2024-06-07 14:30</i>

<code>📉 -60</code> Платная транскрипция
<i>2024-06-07 12:15</i>

<code>📉 -15</code> Короткая транскрипция  
<i>2024-06-07 11:45</i>

<code>📈 +150</code> Пополнение баланса  
<i>2024-06-06 16:20</i>

<code>📉 -30</code> Платная транскрипция
<i>2024-06-06 15:30</i>

💡 <i>Полная история доступна в веб-интерфейсе</i>"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🌐 Открыть веб-интерфейс",
                url="https://aibots.kz/profile"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 К балансу",
                callback_data="profile_balance_info"
            )
        ]
    ])
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "balance_analytics")
async def show_balance_analytics(callback: CallbackQuery):
    """Показывает аналитику трат"""
    text = """📈 <b>Аналитика трат</b>

📊 <b>Статистика по периодам</b>
• Сегодня: 25 монет
• Вчера: 40 монет  
• За неделю: 180 монет
• За месяц: 650 монет

🎯 <b>Распределение по функциям</b>
• 🎤 Транскрибация: 85% (553 монеты)
• 🎁 Промокоды: 10% (65 монет)
• 🔄 Прочие операции: 5% (32 монеты)

📈 <b>Тренды</b>
• Средний расход в день: 15 монет
• Пик активности: 14:00-16:00  
• Самый активный день: Четверг

💡 <b>Рекомендации</b>
• Пополняйте баланс пакетами для бонусов
• Используйте промокоды для экономии
• Планируйте длинные аудио заранее"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📊 Подробная аналитика",
                url="https://aibots.kz/analytics"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 К балансу",
                callback_data="profile_balance_info"
            )
        ]
    ])
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer() 