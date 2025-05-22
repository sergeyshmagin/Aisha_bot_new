"""
Обработчики команд для работы с аватарами (aiogram 3.x)
"""
import logging
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aisha_v2.app.handlers.base import BaseHandler
from aisha_v2.app.keyboards.main import get_main_menu
from aisha_v2.app.keyboards.avatar import get_gender_keyboard
from aisha_v2.app.core.di import get_avatar_service, get_user_service

logger = logging.getLogger(__name__)

class AvatarHandler(BaseHandler):
    """
    Обработчик команд для работы с аватарами (aiogram 3.x)
    """
    def __init__(self):
        super().__init__()
        self.router = Router()
        # Регистрируем хендлеры сразу при создании
        self.router.message.register(self.cmd_create_avatar, F.text == "/create_avatar")
        self.router.message.register(self.cmd_my_avatars, F.text == "/my_avatars")
        self.router.callback_query.register(self.callback_select_gender, F.data.startswith("gender_"))
        self.router.callback_query.register(self.callback_select_avatar, F.data.startswith("avatar_"))
        self.router.message.register(self.process_avatar_photo, F.photo)

    async def cmd_create_avatar(self, message: Message):
        """Создание нового аватара"""
        await message.answer(
            "Выберите пол аватара:",
            reply_markup=get_gender_keyboard()
        )

    async def cmd_my_avatars(self, message: Message):
        """Просмотр существующих аватаров"""
        async with self.get_session() as session:
            avatar_service = get_avatar_service(session)
            avatars = await avatar_service.get_user_avatars(message.from_user.id)
        if not avatars:
            await message.answer("У вас пока нет созданных аватаров.")
            return
        
        text = "Ваши аватары:\n\n"
        for avatar in avatars:
            text += f"• {avatar.name} ({avatar.gender})\n"
        await message.answer(text)

    async def callback_select_gender(self, call: CallbackQuery):
        """Обработка выбора пола аватара"""
        gender = call.data.split("_")[1]
        await call.answer(f"Выбран пол: {gender}")
        await call.message.edit_text(
            f"Выбран пол: {gender}\nТеперь введите имя аватара:"
        )
        # Сохраняем выбранный пол в состоянии и устанавливаем флаг ожидания имени
        await self.state_storage.set_state(
            call.from_user.id,
            {"gender": gender, "waiting_for_name": True}
        )
        # Регистрируем обработчик имени только для этого пользователя
        self.router.message.register(
            self.process_avatar_name,
            F.text,
            lambda msg: msg.from_user.id == call.from_user.id
        )

    async def callback_select_avatar(self, call: CallbackQuery):
        """Обработка выбора существующего аватара"""
        avatar_id = call.data.split("_")[1]
        async with self.get_session() as session:
            avatar_service = get_avatar_service(session)
            avatar = await avatar_service.get_avatar(avatar_id)
        if not avatar:
            await call.answer("Аватар не найден")
            return
        
        await call.answer(f"Выбран аватар: {avatar.name}")
        await call.message.edit_text(
            f"Выбран аватар: {avatar.name}\nПол: {avatar.gender}"
        )

    async def process_avatar_name(self, message: Message):
        """Обработка ввода имени аватара"""
        state = await self.state_storage.get_state(message.from_user.id)
        if not state or not state.get("waiting_for_name"):
            return  # Игнорируем сообщение, если не ожидаем имя

        name = message.text.strip()
        if len(name) < 2:
            await message.answer("Имя должно содержать минимум 2 символа")
            return

        # Создаем аватар
        async with self.get_session() as session:
            avatar_service = get_avatar_service(session)
            avatar = await avatar_service.create_avatar(
                user_id=message.from_user.id,
                name=name,
                gender=state["gender"]
            )

        await message.answer(
            f"Аватар {name} успешно создан!\n"
            f"Теперь отправьте фото для аватара."
        )
        # Очищаем состояние
        await self.state_storage.clear_state(message.from_user.id)
        # Удаляем обработчик имени
        self.router.message.unregister(self.process_avatar_name)

    async def process_avatar_photo(self, message: Message):
        """Обработка загрузки фото аватара"""
        # Получаем последнее (самое качественное) фото
        photo = message.photo[-1]
        
        # Сохраняем фото
        file_info = await message.bot.get_file(photo.file_id)
        downloaded_file = await message.bot.download_file(file_info.file_path)
        
        # TODO: Обработка фото через AI
        await message.answer(
            "Фото получено и будет обработано.\n"
            "Это может занять некоторое время..."
        )

# Создаем экземпляр хендлера
handler = AvatarHandler()
