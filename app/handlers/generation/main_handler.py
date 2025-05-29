"""
Главный обработчик для системы генерации изображений
"""
from typing import List
from uuid import UUID

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.core.di import get_user_service, get_avatar_service
from app.core.logger import get_logger
from app.services.generation.style_service import StyleService
from app.services.generation.generation_service import ImageGenerationService, GENERATION_COST
from app.database.models.generation import StyleCategory, StyleTemplate
from app.database.models import AvatarStatus

logger = get_logger(__name__)
router = Router()


class GenerationMainHandler:
    """Главный обработчик генерации изображений"""
    
    def __init__(self):
        self.style_service = StyleService()
        self.generation_service = ImageGenerationService()
    
    async def show_generation_menu(self, callback: CallbackQuery):
        """Показывает главное меню генерации"""
        
        user_telegram_id = callback.from_user.id
        
        try:
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
                
                # Получаем баланс пользователя
                user_balance = await user_service.get_user_balance(user.id)
            
            # Получаем основной аватар
            async with get_avatar_service() as avatar_service:
                main_avatar = await avatar_service.get_user_main_avatar(user.id)
                if not main_avatar:
                    await callback.answer("❌ У вас нет основного аватара. Создайте аватар сначала!", show_alert=True)
                    return
                
                # Проверяем статус аватара
                if main_avatar.status != AvatarStatus.COMPLETED:
                    await callback.answer("❌ Ваш аватар еще не готов. Дождитесь завершения обучения!", show_alert=True)
                    return
            
            # Получаем популярные категории
            popular_categories = await self.style_service.get_popular_categories(limit=4)
            
            # Получаем избранные шаблоны
            favorites = await self.style_service.get_user_favorites(user.id)
            
            # Формируем текст
            avatar_type_text = "Портретный" if main_avatar.training_type.value == "portrait" else "Стилевой"
            
            text = f"""🎨 **Создание изображения**
👤 Основной аватар: {main_avatar.name} ({avatar_type_text})
💰 Баланс: {user_balance:.0f} единиц
💎 Стоимость: {GENERATION_COST:.0f} единиц за изображение

🔥 **Популярные стили**"""
            
            # Формируем клавиатуру
            keyboard = self._build_generation_menu_keyboard(
                popular_categories, 
                favorites, 
                main_avatar.id,
                user_balance
            )
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            logger.info(f"Показано меню генерации для пользователя {user_telegram_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка показа меню генерации: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    def _build_generation_menu_keyboard(
        self, 
        popular_categories: List[StyleCategory],
        favorites: List[StyleTemplate],
        avatar_id: UUID,
        user_balance: float
    ) -> InlineKeyboardMarkup:
        """Строит клавиатуру главного меню генерации"""
        
        buttons = []
        
        # Проверяем, достаточно ли баланса
        has_balance = user_balance >= GENERATION_COST
        
        if has_balance:
            # Популярные стили (2x2)
            if popular_categories:
                popular_buttons = []
                for i in range(0, len(popular_categories), 2):
                    row = []
                    for j in range(2):
                        if i + j < len(popular_categories):
                            cat = popular_categories[i + j]
                            # Убираем эмодзи из названия для кнопки
                            name_parts = cat.name.split(' ', 1)
                            button_text = f"{cat.icon} {name_parts[1] if len(name_parts) > 1 else name_parts[0]}"
                            row.append(InlineKeyboardButton(
                                text=button_text,
                                callback_data=f"gen_category:{cat.id}"
                            ))
                    if row:
                        popular_buttons.append(row)
                buttons.extend(popular_buttons)
            
            # Все категории
            buttons.append([
                InlineKeyboardButton(
                    text="📂 Все категории",
                    callback_data="gen_all_categories"
                )
            ])
            
            # Избранные (если есть)
            if favorites:
                buttons.append([
                    InlineKeyboardButton(
                        text=f"✨ Мои избранные ({len(favorites)})",
                        callback_data="gen_favorites"
                    )
                ])
            
            # Свой промпт
            buttons.append([
                InlineKeyboardButton(
                    text="📝 Свой промпт",
                    callback_data=f"gen_custom:{avatar_id}"
                )
            ])
        else:
            # Недостаточно баланса
            buttons.append([
                InlineKeyboardButton(
                    text="💰 Пополнить баланс",
                    callback_data="balance_topup"
                )
            ])
        
        # Сменить аватар
        buttons.append([
            InlineKeyboardButton(
                text="🔄 Сменить аватар",
                callback_data="gen_change_avatar"
            )
        ])
        
        # Моя галерея
        buttons.append([
            InlineKeyboardButton(
                text="🖼️ Моя галерея",
                callback_data="my_gallery"
            )
        ])
        
        # Назад
        buttons.append([
            InlineKeyboardButton(
                text="🔙 Главное меню",
                callback_data="main_menu"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    async def show_template_details(self, callback: CallbackQuery):
        """Показывает детали шаблона перед генерацией"""
        
        try:
            template_id = callback.data.split(":")[1]
            user_telegram_id = callback.from_user.id
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
                
                # Получаем баланс
                user_balance = await user_service.get_user_balance(user.id)
            
            # Получаем шаблон
            template = await self.style_service.get_template_by_id(template_id)
            if not template:
                await callback.answer("❌ Шаблон не найден", show_alert=True)
                return
            
            # Получаем основной аватар
            async with get_avatar_service() as avatar_service:
                main_avatar = await avatar_service.get_user_main_avatar(user.id)
                if not main_avatar:
                    await callback.answer("❌ Аватар не найден", show_alert=True)
                    return
            
            # Проверяем, в избранном ли шаблон
            is_favorite = await self.style_service.is_template_favorite(user.id, template_id)
            
            # Формируем текст
            text = f"""📊 **{template.name}**

📝 **Промпт:**
_{template.prompt}_

⚙️ **Настройки по умолчанию:**
• Качество: ⚖️ Сбалансированное
• Формат: 🖼️ Квадрат (1:1)
• Количество: 1 изображение

💰 **Стоимость:** {GENERATION_COST:.0f} единиц
💳 **Ваш баланс:** {user_balance:.0f} единиц"""
            
            # Формируем клавиатуру
            keyboard = self._build_template_details_keyboard(
                template_id, 
                main_avatar.id, 
                is_favorite,
                user_balance >= GENERATION_COST
            )
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.exception(f"Ошибка показа деталей шаблона: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    def _build_template_details_keyboard(
        self, 
        template_id: str, 
        avatar_id: UUID, 
        is_favorite: bool,
        has_balance: bool
    ) -> InlineKeyboardMarkup:
        """Строит клавиатуру деталей шаблона"""
        
        buttons = []
        
        if has_balance:
            # Создать изображение
            buttons.append([
                InlineKeyboardButton(
                    text="🎨 Создать изображение",
                    callback_data=f"gen_start:{template_id}:{avatar_id}"
                )
            ])
            
            # Настройки генерации
            buttons.append([
                InlineKeyboardButton(
                    text="⚙️ Настройки генерации",
                    callback_data=f"gen_settings:{template_id}:{avatar_id}"
                )
            ])
        else:
            # Недостаточно баланса
            buttons.append([
                InlineKeyboardButton(
                    text="💰 Пополнить баланс",
                    callback_data="balance_topup"
                )
            ])
        
        # Избранное
        favorite_text = "💔 Удалить из избранного" if is_favorite else "❤️ В избранное"
        favorite_action = "remove" if is_favorite else "add"
        buttons.append([
            InlineKeyboardButton(
                text=favorite_text,
                callback_data=f"gen_favorite:{favorite_action}:{template_id}"
            )
        ])
        
        # Назад
        buttons.append([
            InlineKeyboardButton(
                text="🔙 К выбору стилей",
                callback_data="generation_menu"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    async def start_generation(self, callback: CallbackQuery):
        """Запускает генерацию изображения"""
        
        try:
            data_parts = callback.data.split(":")
            template_id = data_parts[1]
            avatar_id = UUID(data_parts[2])
            
            user_telegram_id = callback.from_user.id
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Запускаем генерацию
            generation = await self.generation_service.generate_from_template(
                user_id=user.id,
                avatar_id=avatar_id,
                template_id=template_id,
                quality_preset="balanced",
                aspect_ratio="1:1",
                num_images=1
            )
            
            # Показываем статус генерации
            await self._show_generation_status(callback, generation)
            
        except ValueError as e:
            # Ошибки валидации (недостаточно баланса и т.д.)
            await callback.answer(f"❌ {str(e)}", show_alert=True)
            
        except Exception as e:
            logger.exception(f"Ошибка запуска генерации: {e}")
            await callback.answer("❌ Произошла ошибка при запуске генерации", show_alert=True)
    
    async def _show_generation_status(self, callback: CallbackQuery, generation):
        """Показывает статус генерации"""
        
        template_name = generation.template.name if generation.template else "Кастомный промпт"
        
        text = f"""🎨 **Создаю ваше изображение...**

📊 **Шаблон:** {template_name}
🎭 **Аватар:** {generation.avatar.name}
⚡ **Качество:** Сбалансированное
🖼️ **Формат:** Квадрат (1:1)

⏱️ **Статус:** Обработка...
💡 Обычно генерация занимает 30-60 секунд"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Обновить статус",
                    callback_data=f"gen_status:{generation.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 К выбору стилей",
                    callback_data="generation_menu"
                )
            ]
        ])
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def toggle_favorite_template(self, callback: CallbackQuery):
        """Переключает статус избранного для шаблона"""
        
        try:
            data_parts = callback.data.split(":")
            action = data_parts[1]  # add или remove
            template_id = data_parts[2]
            
            user_telegram_id = callback.from_user.id
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            if action == "add":
                success = await self.style_service.add_to_favorites(user.id, template_id)
                message = "✅ Добавлено в избранное" if success else "❌ Ошибка добавления"
            else:
                success = await self.style_service.remove_from_favorites(user.id, template_id)
                message = "✅ Удалено из избранного" if success else "❌ Ошибка удаления"
            
            await callback.answer(message)
            
            # Обновляем детали шаблона
            callback.data = f"gen_template:{template_id}"
            await self.show_template_details(callback)
            
        except Exception as e:
            logger.exception(f"Ошибка переключения избранного: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)


# Создаем экземпляр обработчика
generation_handler = GenerationMainHandler()

# Регистрируем обработчики
@router.callback_query(F.data == "generation_menu")
async def handle_generation_menu(callback: CallbackQuery):
    """Обработчик главного меню генерации"""
    await generation_handler.show_generation_menu(callback)

@router.callback_query(F.data.startswith("gen_template:"))
async def handle_template_details(callback: CallbackQuery):
    """Обработчик деталей шаблона"""
    await generation_handler.show_template_details(callback)

@router.callback_query(F.data.startswith("gen_start:"))
async def handle_start_generation(callback: CallbackQuery):
    """Обработчик запуска генерации"""
    await generation_handler.start_generation(callback)

@router.callback_query(F.data.startswith("gen_favorite:"))
async def handle_toggle_favorite(callback: CallbackQuery):
    """Обработчик переключения избранного"""
    await generation_handler.toggle_favorite_template(callback)

@router.callback_query(F.data.startswith("gen_category:"))
async def show_category(callback: CallbackQuery):
    """Обработчик показа категории"""
    await generation_handler.show_category(callback)

@router.callback_query(F.data == "gen_all_categories")
async def show_all_categories(callback: CallbackQuery):
    """Обработчик показа всех категорий"""
    await generation_handler.show_all_categories(callback)

@router.callback_query(F.data == "gen_favorites")
async def show_favorites(callback: CallbackQuery):
    """Обработчик показа избранных"""
    await generation_handler.show_favorites(callback)

@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    """Обработчик пустых callback'ов"""
    await callback.answer() 