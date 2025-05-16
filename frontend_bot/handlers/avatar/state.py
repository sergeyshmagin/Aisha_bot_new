# Глобальное состояние FSM и галереи для аватаров

def safe_dict():
    class SafeDict(dict):
        def __setitem__(self, key, value):
            if isinstance(key, (list, dict, set)):
                raise TypeError(f"[SAFE_DICT] Нельзя использовать {type(key)} как ключ словаря: {key}")
            return super().__setitem__(key, value)
        def __getitem__(self, key):
            if isinstance(key, (list, dict, set)):
                raise TypeError(f"[SAFE_DICT] Нельзя использовать {type(key)} как ключ словаря: {key}")
            return super().__getitem__(key)
        def get(self, key, default=None):
            if isinstance(key, (list, dict, set)):
                raise TypeError(f"[SAFE_DICT] Нельзя использовать {type(key)} как ключ словаря: {key}")
            return super().get(key, default)
        def setdefault(self, key, default=None):
            if isinstance(key, (list, dict, set)):
                raise TypeError(f"[SAFE_DICT] Нельзя использовать {type(key)} как ключ словаря: {key}")
            return super().setdefault(key, default)
        def pop(self, key, default=None):
            if isinstance(key, (list, dict, set)):
                raise TypeError(f"[SAFE_DICT] Нельзя использовать {type(key)} как ключ словаря: {key}")
            return super().pop(key, default)
    return SafeDict()

user_session = safe_dict()  # user_id -> dict: wizard_message_ids, last_wizard_state, uploaded_photo_msgs, last_error_msg, last_info_msg_id
user_gallery = safe_dict()  # f"{user_id}:{avatar_id}" -> dict: index, last_switch
user_media_group_queue = safe_dict()  # user_id -> list of (media_group_id, photos)
user_media_group_processing = set()  # user_id, если сейчас идёт обработка
user_single_photo_buffer = safe_dict()  # user_id -> [photo_bytes, ...]
user_media_group_buffer = safe_dict()  # user_id -> media_group_id -> [photo_bytes, ...]
user_media_group_timers = safe_dict()  # user_id -> media_group_id -> asyncio.Task
user_single_photo_timer = safe_dict()  # user_id -> asyncio.Task
user_locks = safe_dict()  # user_id -> asyncio.Lock
user_media_groups = safe_dict()  # f"{user_id}:{media_group_id}" -> [(file_id, photo_bytes), ...]
user_gallery_index = safe_dict()  # f"{user_id}:{avatar_id}" -> int
user_gallery_last_switch = safe_dict()  # f"{user_id}:{avatar_id}" -> timestamp
user_media_group_msg_ids = safe_dict()  # user_id -> media_group_id -> [message_id, ...]

def get_gallery_key(user_id: int, avatar_id: str) -> str:
    """Получает ключ для галереи."""
    return f"{user_id}:{avatar_id}"

def get_media_group_key(user_id: int, media_group_id: str) -> str:
    """Получает ключ для медиа-группы."""
    return f"{user_id}:{media_group_id}"
