# План структуры классов для функционала аватаров (V2)

## 0. Аудио и транскрибация (audio)

### class AudioProcessingService (services/audio/service.py)
- async def save_audio_file(file_id: str, ext: str, bot: Bot) -> str
- async def convert_to_mp3(input_path: str) -> str
- async def split_by_silence(input_path: str, ...) -> list[str]
- async def recognize_audio(audio_path: str) -> str
- async def process_audio(message: Message, bot: Bot, user_id: str) -> tuple[bool, str, Optional[str]]

### class AudioHandler (handlers/audio.py)
- async def handle_audio_start(message: Message, state: FSMContext) -> None
- async def handle_audio(message: Message, state: FSMContext) -> None
- router: Router (aiogram)

### class AudioStates (handlers/audio.py)
- waiting_for_audio: State

### texts/audio_errors.py
- AUDIO_PROCESSING_ERROR
- FILE_TOO_LARGE_ERROR
- FFMPEG_NOT_FOUND_ERROR
- UNSUPPORTED_FORMAT_ERROR
- AUDIO_PROCESSING_START
- AUDIO_PROCESSING_CHUNK
- AUDIO_PROCESSING_DONE

### tests/services/test_audio_service.py
- Тесты для AudioProcessingService (pytest-asyncio, AsyncMock)

## 1. Модели (models.py)

### class Avatar
- id: UUID
- user_id: UUID
- name: str
- gender: str
- status: str
- avatar_data: dict
- created_at: datetime
- updated_at: datetime
- is_draft: bool

### class AvatarPhoto
- id: UUID
- avatar_id: UUID
- photo_key: str
- preview_key: str
- created_at: datetime
- order: int

## 2. Репозитории (repositories/avatar.py)

### class AvatarRepository
- async def create(self, user_id: UUID, data: dict) -> Avatar
- async def get_by_id(self, avatar_id: UUID) -> Optional[Avatar]
- async def get_by_user_id(self, user_id: UUID) -> list[Avatar]
- async def update(self, avatar_id: UUID, data: dict) -> Optional[Avatar]
- async def delete(self, avatar_id: UUID) -> bool

### class AvatarPhotoRepository
- async def create(self, avatar_id: UUID, photo_data: dict) -> AvatarPhoto
- async def get_by_id(self, photo_id: UUID) -> Optional[AvatarPhoto]
- async def get_by_avatar_id(self, avatar_id: UUID) -> list[AvatarPhoto]
- async def delete(self, photo_id: UUID) -> bool

## 3. Сервисы (services/avatar/)

### class AvatarService
- async def create_avatar(self, user_id: UUID, data: dict) -> Avatar
- async def delete_avatar(self, user_id: UUID, avatar_id: UUID) -> bool
- async def get_avatar(self, user_id: UUID, avatar_id: UUID) -> Optional[Avatar]
- async def list_avatars(self, user_id: UUID, limit: int = 10, offset: int = 0) -> list[Avatar]
- async def get_presigned_url(self, photo_key: str) -> str
- async def validate_limits(self, user_id: UUID) -> None

### class AvatarGalleryService
- async def get_gallery(self, user_id: UUID) -> list[Avatar]
- async def get_avatar_card(self, avatar: Avatar) -> dict
- async def navigate_gallery(self, user_id: UUID, direction: str) -> Avatar

### class AvatarValidationService
- async def validate_photo(self, photo: bytes) -> None
- async def validate_name(self, name: str) -> None
- async def validate_limits(self, user_id: UUID) -> None

### class AvatarFSMService
- async def start_wizard(self, user_id: UUID) -> None
- async def next_step(self, user_id: UUID, data: dict) -> None
- async def set_gender(self, user_id: UUID, gender: str) -> None
- async def set_name(self, user_id: UUID, name: str) -> None
- async def confirm(self, user_id: UUID) -> None

### class AvatarDraftService
- async def create_draft(self, user_id: UUID, data: dict) -> Avatar
- async def finalize_draft(self, user_id: UUID, avatar_id: UUID) -> Avatar
- async def delete_draft(self, user_id: UUID, avatar_id: UUID) -> bool

### class AvatarTrainingService
- async def start_training(self, avatar_id: UUID) -> None
- async def check_status(self, avatar_id: UUID) -> str
- async def cancel_training(self, avatar_id: UUID) -> None

## 4. Клавиатуры (keyboards/avatar.py)

### class AvatarKeyboardFactory
- @staticmethod
  def confirm_keyboard() -> InlineKeyboardMarkup
- @staticmethod
  def gallery_keyboard(current: int, total: int) -> InlineKeyboardMarkup
- @staticmethod
  def type_keyboard() -> InlineKeyboardMarkup
- ... (другие клавиатуры по этапам FSM)

## 5. Тексты (texts/avatar.py)

### class AvatarTextTemplates
- @staticmethod
  def creation_success(name: str) -> str
- @staticmethod
  def error_photo_invalid() -> str
- @staticmethod
  def prompt_enter_name() -> str
- ... (другие шаблоны сообщений)

## 6. FSM состояния (state.py)

### class AvatarFSMState(Enum)
- PHOTO_UPLOAD
- GENDER
- NAME
- CONFIRM
- TRAINING
- ... (доп. состояния по необходимости)

## 7. Тесты (tests/services/test_avatar_service.py и др.)
- Тестовые классы для каждого сервиса и FSM. 