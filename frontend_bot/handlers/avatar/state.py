# Глобальное состояние FSM и галереи для аватаров

user_session = {}  # user_id -> dict: wizard_message_ids, last_wizard_state, uploaded_photo_msgs, last_error_msg, last_info_msg_id
user_gallery = {}  # (user_id, avatar_id) -> dict: index, last_switch
user_media_group_queue = {}  # user_id -> list of (media_group_id, photos)
user_media_group_processing = set()  # user_id, если сейчас идёт обработка
user_single_photo_buffer = {}  # user_id -> [photo_bytes, ...]
user_media_group_buffer = {}   # user_id -> media_group_id -> [photo_bytes, ...]
user_media_group_timers = {}   # user_id -> media_group_id -> asyncio.Task
user_single_photo_timer = {}   # user_id -> asyncio.Task
user_locks = {}  # user_id -> asyncio.Lock
user_media_groups = {}  # (user_id, media_group_id) -> [(file_id, photo_bytes), ...]
user_gallery_index = {}  # (user_id, avatar_id) -> int
user_gallery_last_switch = {}  # (user_id, avatar_id) -> timestamp 