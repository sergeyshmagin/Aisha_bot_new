"""
LEGACY: Основной обработчик личного кабинета пользователя
Заменен на современный интерфейс в app/handlers/menu/settings_handler.py
Оставлен для совместимости со старыми callback'ами
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

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


class ProfileMainHandler(BaseHandler):
    """Главный обработчик личного кабинета"""
    
    def __init__(self):
        super().__init__()
    
    @require_user()
    async def show_profile_menu(
        self, 
        callback: CallbackQuery, 
        state: FSMContext,
        user=None
    ):
        """Показывает главный экран личного кабинета"""
        try:
            await state.clear()
            
            # Собираем данные пользователя
            profile_data = await self._gather_profile_data(user)
            
            # Формируем текст и клавиатуру
            text = self._build_profile_text(user, profile_data)
            keyboard = self._build_profile_keyboard(profile_data)
            
            # Безопасное обновление сообщения
            await self.safe_edit_message(
                callback=callback,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            await callback.answer()
            logger.info(f"Показан личный кабинет пользователя {user.telegram_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка показа личного кабинета: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def _gather_profile_data(self, user) -> Dict[str, Any]:
        """Собирает данные для личного кабинета"""
        data = {
            'balance': 0.0,
            'avatars_count': 0,
            'completed_avatars': 0,
            'generations_count': 0,
            'member_since_days': 0,
            'last_activity': None,
            'premium': user.is_premium,
            'timezone': user.timezone or "UTC+5"
        }
        
        try:
            # Баланс пользователя
            async with get_user_service() as user_service:
                data['balance'] = await user_service.get_user_balance(user.id)
            
            # Статистика аватаров
            async with get_avatar_service() as avatar_service:
                avatars = await avatar_service.get_user_avatars(user.id)
                data['avatars_count'] = len(avatars)
                data['completed_avatars'] = len([a for a in avatars if a.status == AvatarStatus.COMPLETED])
                data['generations_count'] = sum(a.generations_count for a in avatars)
            
            # Дни с регистрации
            if user.created_at:
                # Приводим created_at к datetime если это строка
                if isinstance(user.created_at, str):
                    created_dt = datetime.fromisoformat(user.created_at.replace('Z', '+00:00'))
                    # Убираем timezone для корректного вычитания
                    created_dt = created_dt.replace(tzinfo=None)
                else:
                    created_dt = user.created_at
                    # Убираем timezone если есть
                    if created_dt.tzinfo is not None:
                        created_dt = created_dt.replace(tzinfo=None)
                    
                days_diff = (datetime.utcnow() - created_dt).days
                data['member_since_days'] = days_diff
                
        except Exception as e:
            logger.exception(f"Ошибка сбора данных профиля: {e}")
        
        return data
    
    def _build_profile_text(self, user, data: Dict[str, Any]) -> str:
        """Формирует текст личного кабинета"""
        
        # Статус пользователя
        status_icon = "👑" if data['premium'] else "👤"
        status_text = "Premium" if data['premium'] else "Стандарт"
        
        # Статистика активности
        member_text = self._format_member_since(data['member_since_days'])
        
        # Главная информация
        text = f"""🏠 <b>Личный кабинет</b>

{status_icon} <b>{user.first_name}</b> • {status_text}
{member_text}

💰 <b>Баланс:</b> {data['balance']:.0f} монет

📊 <b>Статистика</b>
🎭 Аватары: {data['completed_avatars']}/{data['avatars_count']}
🎨 Генераций: {data['generations_count']}
🌍 Часовой пояс: {data['timezone']}"""

        # Добавляем подсказки для новых пользователей
        if data['avatars_count'] == 0:
            text += "\n\n💡 <i>Создайте первый аватар для начала генерации изображений!</i>"
        elif data['balance'] < 50:
            text += "\n\n💡 <i>Рекомендуем пополнить баланс для продолжения работы</i>"
            
        return text
    
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
    
    def _build_profile_keyboard(self, data: Dict[str, Any]) -> InlineKeyboardMarkup:
        """Строит клавиатуру личного кабинета"""
        
        buttons = []
        
        # Первая строка: Баланс и пополнение
        balance_text = f"💰 Баланс ({data['balance']:.0f})"
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
                text="🖼️ Моя галерея",
                callback_data="my_gallery"
            )
        ])
        
        # Четвертая строка: Помощь и поддержка
        buttons.append([
            InlineKeyboardButton(
                text="❓ Справка",
                callback_data="profile_help"
            ),
            InlineKeyboardButton(
                text="💌 Поддержка",
                callback_data="profile_support"
            )
        ])
        
        # Пятая строка: Назад
        buttons.append([
            InlineKeyboardButton(
                text="🔙 Главное меню",
                callback_data="main_menu"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)


# Регистрируем обработчики
profile_handler = ProfileMainHandler()

@router.callback_query(F.data == "profile_menu")
async def show_profile_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Callback для показа личного кабинета"""
    await profile_handler.show_profile_menu(callback, state)

@router.callback_query(F.data == "profile_help")
async def show_profile_help(callback: CallbackQuery):
    """Показывает справку личного кабинета"""
    help_text = """❓ <b>Справка по личному кабинету</b>

🏠 <b>Личный кабинет</b> - центр управления вашим аккаунтом

<b>Основные функции:</b>

💰 <b>Баланс</b>
• Отслеживайте количество кредитов
• Пополняйте баланс для генерации
• Просматривайте историю операций

📊 <b>Статистика</b>
• Количество созданных аватаров
• Число генераций изображений
• Активность по периодам

⚙️ <b>Настройки</b>
• Часовой пояс
• Язык интерфейса
• Уведомления

🎭 <b>Мои данные</b>
• Управление аватарами
• Галерея изображений
• История активности

💡 <b>Совет:</b> Регулярно проверяйте баланс и статистику для оптимального использования сервиса."""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В кабинет", callback_data="profile_menu")]
    ])
    
    await callback.message.edit_text(
        text=help_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "profile_support")
async def show_profile_support(callback: CallbackQuery):
    """Показывает контакты поддержки"""
    support_text = """💌 <b>Поддержка пользователей</b>

Мы всегда готовы помочь вам!

<b>Способы связи:</b>

📧 <b>Email:</b> support@aibots.kz
📱 <b>Telegram:</b> @aisha_support_bot
🌐 <b>Сайт:</b> https://aibots.kz

<b>Время работы:</b>
Пн-Пт: 09:00 - 18:00 (UTC+5)
Сб-Вс: 10:00 - 16:00 (UTC+5)

<b>Что включить в обращение:</b>
• Описание проблемы
• Скриншоты (если применимо)
• Ваш Telegram ID: <code>{callback.from_user.id}</code>

💡 <b>Часто задаваемые вопросы</b> доступны в разделе Справка."""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❓ FAQ", callback_data="profile_help"),
            InlineKeyboardButton(text="🔙 В кабинет", callback_data="profile_menu")
        ]
    ])
    
    await callback.message.edit_text(
        text=support_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer() 