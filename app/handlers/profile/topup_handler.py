"""
LEGACY: Обработчик пополнения баланса с поддержкой промокодов
Функциональность мигрирована в app/handlers/menu/settings_handler.py
Оставлен для совместимости со старыми callback'ами
"""
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional, Dict, Any

from app.core.logger import get_logger
from app.core.config import settings
from app.core.constants import TOPUP_PACKAGES
from app.handlers.base import BaseHandler
from app.keyboards.profile.topup import TopupKeyboard
from app.services.promokode_service import PromokodeService
from app.services.balance_service import BalanceService
from app.database.models import PromokodeType

logger = get_logger(__name__)


class TopupStates(StatesGroup):
    """Состояния пополнения баланса"""
    waiting_promokode = State()
    confirming_purchase = State()


class TopupHandler(BaseHandler):
    """Обработчик пополнения баланса"""
    
    def __init__(self):
        super().__init__()
        self.keyboard = TopupKeyboard()
    
    async def show_topup_menu(self, message: types.Message, state: FSMContext) -> None:
        """Показывает меню пополнения баланса"""
        try:
            await state.clear()
            
            async with self.get_session() as session:
                balance_service = BalanceService(session)
                user = await self.get_user(message.from_user.id, session)
                
                if not user:
                    await message.reply("❌ Ошибка получения данных пользователя")
                    return
                
                current_balance = await balance_service.get_balance(user.id)
                
                # Получаем пакеты пополнения из конфига
                packages = TOPUP_PACKAGES
                
                text = self._format_topup_text(current_balance, packages)
                keyboard = self.keyboard.create_packages_keyboard(packages)
                
                await message.reply(text, reply_markup=keyboard, parse_mode="HTML")
                
        except Exception as e:
            logger.exception(f"Ошибка показа меню пополнения: {e}")
            await message.reply("❌ Ошибка при загрузке меню пополнения")
    
    def _format_topup_text(self, balance: float, packages: Dict[str, Any]) -> str:
        """Форматирует текст меню пополнения"""
        text = f"""💰 <b>Пополнение баланса</b>

💎 Ваш текущий баланс: <b>{balance:.0f} монет</b>

📦 <b>Доступные пакеты:</b>

"""
        
        for package_id, package in packages.items():
            coins = package["coins"]
            price_rub = package["price_rub"]
            price_kzt = package["price_kzt"]
            popular = package.get("popular", False)
            
            popular_badge = " 🔥" if popular else ""
            
            text += f"💎 <b>{coins} монет</b>{popular_badge}\n"
            text += f"💵 {price_rub} ₽ / {price_kzt} ₸\n\n"
        
        text += """🎁 <b>Есть промокод?</b>
Нажмите "Ввести промокод" для получения бонуса!

📋 Стоимость услуг:
• Транскрибация: 10 монет/минута
• Генерация фото: 5 монет
• Видео 5 сек: 20 монет
• Видео 10 сек: 40 монет
• Создание аватара: 150 монет

📄 <a href="{offer_url}">Договор оферты</a> | <a href="{privacy_url}">Политика конфиденциальности</a>""".format(
            offer_url=settings.OFFER_URL,
            privacy_url=settings.PRIVACY_URL
        )
        
        return text
    
    async def handle_package_selection(self, callback: types.CallbackQuery, state: FSMContext) -> None:
        """Обрабатывает выбор пакета"""
        try:
            package_id = callback.data.split(":")[-1]
            packages = TOPUP_PACKAGES
            
            if package_id not in packages:
                await callback.answer("❌ Неверный пакет", show_alert=True)
                return
            
            package = packages[package_id]
            
            # Сохраняем данные пакета в состояние
            await state.update_data(
                package_id=package_id,
                package_data=package
            )
            
            text = self._format_package_confirmation(package_id, package)
            keyboard = self.keyboard.create_confirmation_keyboard(package_id)
            
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            await state.set_state(TopupStates.confirming_purchase)
            
        except Exception as e:
            logger.exception(f"Ошибка выбора пакета: {e}")
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
    
    def _format_package_confirmation(self, package_id: str, package: Dict[str, Any]) -> str:
        """Форматирует текст подтверждения покупки"""
        coins = package["coins"]
        price_rub = package["price_rub"]
        price_kzt = package["price_kzt"]
        
        package_names = {
            "small": "Стартовый",
            "medium": "Популярный",
            "large": "Максимальный"
        }
        
        package_name = package_names.get(package_id, package_id.title())
        
        return f"""💰 <b>Подтверждение покупки</b>

📦 Пакет: <b>{package_name}</b>
💎 Монеты: <b>{coins}</b>
💵 Стоимость: <b>{price_rub} ₽ / {price_kzt} ₸</b>

🎁 Есть промокод? Нажмите "Ввести промокод" для получения бонуса!

⚠️ После нажатия "Оплатить" будет создан счет для оплаты."""
    
    async def handle_promokode_input(self, callback: types.CallbackQuery, state: FSMContext) -> None:
        """Обрабатывает запрос на ввод промокода"""
        try:
            await callback.message.edit_text(
                "🎁 <b>Введите промокод</b>\n\n"
                "Отправьте сообщением ваш промокод для получения бонуса.\n\n"
                "Для отмены нажмите /cancel",
                parse_mode="HTML"
            )
            await state.set_state(TopupStates.waiting_promokode)
            
        except Exception as e:
            logger.exception(f"Ошибка запроса промокода: {e}")
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
    
    async def handle_promokode_message(self, message: types.Message, state: FSMContext) -> None:
        """Обрабатывает введенный промокод"""
        try:
            promokode = message.text.strip().upper()
            
            if not promokode:
                await message.reply("❌ Введите корректный промокод")
                return
            
            async with self.get_session() as session:
                promokode_service = PromokodeService(session)
                user = await self.get_user(message.from_user.id, session)
                
                if not user:
                    await message.reply("❌ Ошибка получения данных пользователя")
                    return
                
                # Проверяем промокод
                is_valid, error_msg, promokode_data = await promokode_service.validate_promokode(
                    promokode, user.id
                )
                
                if not is_valid:
                    await message.reply(f"❌ {error_msg}")
                    await self._return_to_topup_menu(message, state)
                    return
                
                # Сохраняем промокод в состояние
                await state.update_data(promokode=promokode_data)
                
                # Показываем информацию о бонусе
                bonus_text = self._format_promokode_bonus(promokode_data)
                await message.reply(bonus_text, parse_mode="HTML")
                
                # Возвращаемся к меню пополнения
                await self._return_to_topup_menu(message, state)
                
        except Exception as e:
            logger.exception(f"Ошибка обработки промокода: {e}")
            await message.reply("❌ Ошибка при проверке промокода")
    
    def _format_promokode_bonus(self, promokode_data: Dict[str, Any]) -> str:
        """Форматирует информацию о бонусе промокода"""
        code = promokode_data["code"]
        promokode_type = promokode_data["type"]
        
        if promokode_type == PromokodeType.BALANCE:
            balance_amount = promokode_data["balance_amount"]
            return f"🎉 <b>Промокод применен!</b>\n\n💎 Бонус: <b>{balance_amount} монет</b>"
        
        elif promokode_type == PromokodeType.BONUS:
            bonus_amount = promokode_data["bonus_amount"]
            return f"🎉 <b>Промокод применен!</b>\n\n🎁 Бонус при пополнении: <b>+{bonus_amount} монет</b>"
        
        elif promokode_type == PromokodeType.DISCOUNT:
            discount_percent = promokode_data["discount_percent"]
            return f"🎉 <b>Промокод применен!</b>\n\n💰 Скидка: <b>{discount_percent}%</b>"
        
        return f"🎉 <b>Промокод {code} применен!</b>"
    
    async def _return_to_topup_menu(self, message: types.Message, state: FSMContext) -> None:
        """Возвращает к меню пополнения с учетом промокода"""
        try:
            state_data = await state.get_data()
            promokode_data = state_data.get("promokode")
            
            async with self.get_session() as session:
                balance_service = BalanceService(session)
                user = await self.get_user(message.from_user.id, session)
                
                if not user:
                    await message.reply("❌ Ошибка получения данных пользователя")
                    return
                
                current_balance = await balance_service.get_balance(user.id)
                packages = TOPUP_PACKAGES
                
                text = self._format_topup_text_with_promokode(current_balance, packages, promokode_data)
                keyboard = self.keyboard.create_packages_keyboard(packages)
                
                await message.reply(text, reply_markup=keyboard, parse_mode="HTML")
                
        except Exception as e:
            logger.exception(f"Ошибка возврата к меню: {e}")
            await message.reply("❌ Ошибка при обновлении меню")
    
    def _format_topup_text_with_promokode(
        self, 
        balance: float, 
        packages: Dict[str, Any], 
        promokode_data: Optional[Dict[str, Any]]
    ) -> str:
        """Форматирует текст меню пополнения с промокодом"""
        text = self._format_topup_text(balance, packages)
        
        if promokode_data:
            code = promokode_data["code"]
            promokode_type = promokode_data["type"]
            
            text += f"\n\n🎁 <b>Активен промокод: {code}</b>\n"
            
            if promokode_type == PromokodeType.BALANCE:
                balance_amount = promokode_data["balance_amount"]
                text += f"💎 Бонус: +{balance_amount} монет"
            elif promokode_type == PromokodeType.BONUS:
                bonus_amount = promokode_data["bonus_amount"]
                text += f"🎁 Бонус при пополнении: +{bonus_amount} монет"
            elif promokode_type == PromokodeType.DISCOUNT:
                discount_percent = promokode_data["discount_percent"]
                text += f"💰 Скидка: {discount_percent}%"
        
        return text
    
    async def handle_payment_creation(self, callback: types.CallbackQuery, state: FSMContext) -> None:
        """Обрабатывает создание платежа"""
        try:
            state_data = await state.get_data()
            package_id = state_data.get("package_id")
            package_data = state_data.get("package_data")
            promokode_data = state_data.get("promokode")
            
            if not package_id or not package_data:
                await callback.answer("❌ Ошибка данных пакета", show_alert=True)
                return
            
            async with self.get_session() as session:
                user = await self.get_user(callback.from_user.id, session)
                
                if not user:
                    await callback.answer("❌ Ошибка получения данных пользователя", show_alert=True)
                    return
                
                # Применяем промокод если есть
                if promokode_data:
                    await self._apply_promokode(session, user.id, promokode_data, package_data)
                
                # TODO: Здесь должна быть интеграция с платежной системой
                # Для демонстрации просто показываем инструкции
                
                payment_text = self._format_payment_instructions(package_data, promokode_data)
                await callback.message.edit_text(payment_text, parse_mode="HTML")
                
                await state.clear()
                
        except Exception as e:
            logger.exception(f"Ошибка создания платежа: {e}")
            await callback.answer("❌ Ошибка создания платежа", show_alert=True)
    
    async def _apply_promokode(
        self, 
        session, 
        user_id, 
        promokode_data: Dict[str, Any], 
        package_data: Dict[str, Any]
    ) -> None:
        """Применяет промокод"""
        try:
            promokode_service = PromokodeService(session)
            balance_service = BalanceService(session)
            
            package_info = {
                "coins": package_data["coins"],
                "package_name": f"topup_{package_data['coins']}_coins"
            }
            
            success, message, result = await promokode_service.apply_promokode(
                code=promokode_data["code"],
                user_id=user_id,
                package_info=package_info
            )
            
            if success and promokode_data["type"] == PromokodeType.BALANCE:
                # Для промокодов баланса сразу зачисляем монеты
                await balance_service.add_balance(
                    user_id=user_id,
                    amount=result["total_coins_added"],
                    description=f"Промокод {promokode_data['code']}"
                )
                logger.info(f"Применен промокод баланса {promokode_data['code']} для пользователя {user_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка применения промокода: {e}")
    
    def _format_payment_instructions(
        self, 
        package_data: Dict[str, Any], 
        promokode_data: Optional[Dict[str, Any]]
    ) -> str:
        """Форматирует инструкции по оплате"""
        coins = package_data["coins"]
        price_rub = package_data["price_rub"]
        price_kzt = package_data["price_kzt"]
        
        text = f"""💳 <b>Инструкции по оплате</b>

📦 Пакет: <b>{coins} монет</b>
💵 Стоимость: <b>{price_rub} ₽ / {price_kzt} ₸</b>

"""
        
        if promokode_data and promokode_data["type"] != PromokodeType.BALANCE:
            text += f"🎁 Промокод: <b>{promokode_data['code']}</b>\n"
            
            if promokode_data["type"] == PromokodeType.BONUS:
                bonus = promokode_data["bonus_amount"]
                total_coins = coins + bonus
                text += f"💎 Итого монет с бонусом: <b>{total_coins}</b>\n\n"
            elif promokode_data["type"] == PromokodeType.DISCOUNT:
                discount = promokode_data["discount_percent"]
                text += f"💰 Скидка: <b>{discount}%</b>\n\n"
        
        text += """📱 <b>Способы оплаты:</b>

1️⃣ <b>Банковская карта</b>
2️⃣ <b>СБП (Система быстрых платежей)</b>
3️⃣ <b>Электронные кошельки</b>

⏰ После оплаты монеты будут зачислены автоматически в течение 5 минут.

❓ Возникли вопросы? Обратитесь в поддержку: @support"""
        
        return text
    
    async def handle_back_to_profile(self, callback: types.CallbackQuery, state: FSMContext) -> None:
        """Возвращает в профиль"""
        try:
            await state.clear()
            from app.handlers.profile.main_handler import ProfileHandler
            profile_handler = ProfileHandler()
            await profile_handler.show_profile(callback.message, state)
            
        except Exception as e:
            logger.exception(f"Ошибка возврата в профиль: {e}")
            await callback.answer("❌ Ошибка возврата в профиль", show_alert=True) 