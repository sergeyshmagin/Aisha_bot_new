"""
Состояния для FSM
"""
from aiogram.fsm.state import StatesGroup, State

class TranscribeStates(StatesGroup):
    """Состояния для транскрибации"""
    menu = State()  # Меню транскрибации
    waiting_audio = State()  # Ожидание аудио
    waiting_text = State()  # Ожидание текста
    processing = State()  # Обработка файла
    result = State()  # Показ результата
    format_selection = State()  # Выбор формата
    error = State()  # Состояние ошибки
    
    # Состояния платной транскрипции
    showing_quote = State()  # Показ расценок
    waiting_payment_confirmation = State()  # Ожидание подтверждения оплаты
    payment_processing = State()  # Обработка платежа
    payment_success = State()  # Успешная оплата
    payment_failed = State()  # Неудачная оплата
    
    # Состояния промо-кодов
    waiting_promo_code = State()  # Ожидание ввода промо-кода
    promo_processing = State()  # Обработка промо-кода
    promo_applied = State()  # Промо-код применен


class AvatarStates(StatesGroup):
    """Состояния для создания и управления аватарами"""
    
    # Выбор типа обучения (новые состояния)
    viewing_training_info = State()       # Просмотр информации о типе
    viewing_training_comparison = State() # Сравнение типов обучения
    
    # Основные состояния
    menu = State()                    # Главное меню аватаров
    selecting_type = State()          # Выбор типа аватара (character/style/custom)
    selecting_gender = State()        # Выбор пола аватара
    entering_name = State()           # Ввод имени аватара
    
    # Загрузка фотографий
    uploading_photos = State()        # Загрузка фотографий
    photo_validation = State()        # Валидация фотографий
    photos_gallery = State()          # Просмотр галереи фотографий
    
    # Настройки обучения
    training_settings = State()       # Настройки обучения
    confirming_training = State()     # Подтверждение обучения
    
    # Процесс обучения
    training_in_progress = State()    # Процесс обучения
    training_complete = State()       # Обучение завершено
    training_error = State()          # Ошибка обучения
    
    # Использование аватара
    avatar_gallery = State()          # Галерея аватаров пользователя
    avatar_details = State()          # Детали конкретного аватара
    generating_image = State()        # Генерация изображения
    generation_settings = State()     # Настройки генерации
    
    # Управление
    editing_avatar = State()          # Редактирование аватара
    deleting_avatar = State()         # Удаление аватара
    renaming_avatar = State()         # Переименование аватара
    
    # New state for training
    training = State()                # Обучение в процессе 