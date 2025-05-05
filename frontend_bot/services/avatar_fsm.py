import os
import json
from datetime import datetime
from typing import Optional, Dict, Any

AVATAR_STORAGE = 'storage/avatars'


def get_user_dir(user_id: int) -> str:
    return os.path.join(AVATAR_STORAGE, str(user_id))


def get_user_json_path(user_id: int) -> str:
    return os.path.join(get_user_dir(user_id), 'data.json')


def init_user_fsm(user_id: int) -> None:
    user_dir = get_user_dir(user_id)
    os.makedirs(user_dir, exist_ok=True)
    data = {
        "state": "awaiting_photos",
        "photos": [],
        "title": None,
        "subject": "person",
        "style": "realistic",
        "branch": "fast",
        "callback": None,
        "created_at": datetime.utcnow().isoformat()
    }
    save_user_fsm(user_id, data)


def load_user_fsm(user_id: int) -> Optional[Dict[str, Any]]:
    path = get_user_json_path(user_id)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_user_fsm(user_id: int, data: Dict[str, Any]) -> None:
    user_dir = get_user_dir(user_id)
    os.makedirs(user_dir, exist_ok=True)
    path = get_user_json_path(user_id)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_photo(user_id: int, photo_bytes: bytes) -> str:
    user_dir = get_user_dir(user_id)
    os.makedirs(user_dir, exist_ok=True)
    # Генерируем уникальное имя файла
    existing = [
        f for f in os.listdir(user_dir)
        if f.startswith('photo_') and f.endswith('.jpg')
    ]
    photo_num = len(existing) + 1
    photo_path = os.path.join(user_dir, f'photo_{photo_num}.jpg')
    with open(photo_path, 'wb') as f:
        f.write(photo_bytes)
    # Обновляем JSON
    data = load_user_fsm(user_id) or {}
    data.setdefault('photos', []).append(photo_path)
    save_user_fsm(user_id, data)
    return photo_path


def update_user_fsm(user_id: int, **kwargs) -> None:
    data = load_user_fsm(user_id) or {}
    data.update(kwargs)
    save_user_fsm(user_id, data)


def clear_user_fsm(user_id: int) -> None:
    user_dir = get_user_dir(user_id)
    if os.path.exists(user_dir):
        for root, dirs, files in os.walk(user_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(user_dir) 