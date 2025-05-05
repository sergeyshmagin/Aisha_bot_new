"""Сервис для хранения аватаров пользователя в JSON-файле."""

import json
import os
from threading import Lock

AVATAR_PATH = os.path.join(os.path.dirname(__file__), "avatars.json")
_storage_lock = Lock()

# Загружаем все аватары из файла
def load_avatars():
    if not os.path.exists(AVATAR_PATH):
        return {}
    with _storage_lock, open(AVATAR_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# Сохраняем все аватары в файл
def save_avatars(data):
    with _storage_lock, open(AVATAR_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Получить список аватаров пользователя
def get_user_avatars(user_id):
    data = load_avatars()
    return data.get(str(user_id), [])

# Установить список аватаров пользователя
def set_user_avatars(user_id, avatars):
    data = load_avatars()
    data[str(user_id)] = avatars
    save_avatars(data) 