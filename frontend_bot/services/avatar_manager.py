import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from PIL import Image
import io
import hashlib
import aiofiles.os
import logging

AVATAR_STORAGE = 'storage/avatars'


def get_user_dir(user_id: int) -> str:
    return os.path.join(AVATAR_STORAGE, str(user_id))


def get_avatar_dir(user_id: int, avatar_id: str) -> str:
    return os.path.join(get_user_dir(user_id), avatar_id)


def get_avatar_json_path(user_id: int, avatar_id: str) -> str:
    return os.path.join(get_avatar_dir(user_id, avatar_id), 'data.json')


def get_avatars_index_path(user_id: int) -> str:
    return os.path.join(get_user_dir(user_id), 'avatars.json')


def init_avatar_fsm(user_id: int, avatar_id: str, title: str = "", class_name: str = "", training_params: dict = None) -> None:
    avatar_dir = get_avatar_dir(user_id, avatar_id)
    print(f"[AVATAR_MANAGER] init_avatar_fsm: user_id={user_id}, avatar_id={avatar_id}, avatar_dir={avatar_dir}")
    os.makedirs(avatar_dir, exist_ok=True)
    data = {
        "photos": [],
        "title": title,
        "class_name": class_name,
        "finetune_id": None,
        "status": "pending",
        "avatar_url": None,
        "created_at": datetime.utcnow().isoformat(),
        "training_params": training_params or {}
    }
    print(f"[AVATAR_MANAGER] init_avatar_fsm: data={data}")
    save_avatar_fsm(user_id, avatar_id, data)
    # Не добавляем в avatars.json до завершения генерации


def load_avatar_fsm(user_id: int, avatar_id: str) -> Optional[Dict[str, Any]]:
    path = get_avatar_json_path(user_id, avatar_id)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_avatar_fsm(user_id: int, avatar_id: str, data: Dict[str, Any]) -> None:
    avatar_dir = get_avatar_dir(user_id, avatar_id)
    print(f"[AVATAR_MANAGER] save_avatar_fsm: user_id={user_id}, avatar_id={avatar_id}, avatar_dir={avatar_dir}")
    os.makedirs(avatar_dir, exist_ok=True)
    path = get_avatar_json_path(user_id, avatar_id)
    print(f"[AVATAR_MANAGER] save_avatar_fsm: path={path}")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[AVATAR_MANAGER] save_avatar_fsm: data saved")


def add_photo_to_avatar(user_id: int, avatar_id: str, photo_bytes: bytes, file_id: str = None) -> str:
    avatar_dir = get_avatar_dir(user_id, avatar_id)
    print(f"[AVATAR_MANAGER] add_photo_to_avatar: user_id={user_id}, avatar_id={avatar_id}, avatar_dir={avatar_dir}")
    os.makedirs(avatar_dir, exist_ok=True)
    existing = [
        f for f in os.listdir(avatar_dir)
        if f.startswith('photo_') and f.endswith('.jpg')
    ]
    photo_num = len(existing) + 1
    photo_path = os.path.join(avatar_dir, f'photo_{photo_num}.jpg')
    print(f"[AVATAR_MANAGER] add_photo_to_avatar: photo_path={photo_path}")
    with open(photo_path, 'wb') as f:
        f.write(photo_bytes)
    print(f"[AVATAR_MANAGER] add_photo_to_avatar: photo written")
    # Обновляем JSON
    data = load_avatar_fsm(user_id, avatar_id) or {
        "photos": [], "title": "", "class_name": "",
        "finetune_id": None, "status": "pending", "avatar_url": None,
        "created_at": None, "training_params": {}
    }
    if file_id is None:
        photo_entry = {"path": photo_path}
    else:
        photo_entry = {"path": photo_path, "file_id": file_id}
    data.setdefault('photos', []).append(photo_entry)
    # Оставляем только нужные поля
    data = {k: data.get(k) for k in ("photos", "title", "class_name", "finetune_id", "status", "avatar_url", "created_at", "training_params")}
    save_avatar_fsm(user_id, avatar_id, data)
    print(f"[AVATAR_MANAGER] add_photo_to_avatar: photo added to data.json")
    return photo_path


def update_avatar_fsm(user_id: int, avatar_id: str, **kwargs) -> None:
    data = load_avatar_fsm(user_id, avatar_id) or {
        "photos": [], "title": "", "class_name": "",
        "finetune_id": None, "status": "pending", "avatar_url": None,
        "created_at": None, "training_params": {}
    }
    for k in ("title", "class_name", "finetune_id", "status", "avatar_url", "created_at", "training_params"):
        if k in kwargs:
            data[k] = kwargs[k]
    # Оставляем только нужные поля
    data = {k: data.get(k) for k in ("photos", "title", "class_name", "finetune_id", "status", "avatar_url", "created_at", "training_params")}
    save_avatar_fsm(user_id, avatar_id, data)
    # Если обновили title/style/tune_id — обновить avatars.json
    update_avatar_in_index(user_id, avatar_id, data)


def clear_avatar_fsm(user_id: int, avatar_id: str) -> None:
    avatar_dir = get_avatar_dir(user_id, avatar_id)
    # Удаляем превью, если есть
    preview_path = os.path.join(avatar_dir, 'preview.jpg')
    if os.path.exists(preview_path):
        try:
            os.remove(preview_path)
            logging.info(f"[AVATAR_MANAGER] Превью удалено: {preview_path}")
        except Exception as e:
            logging.error(f"[AVATAR_MANAGER] Ошибка удаления превью {preview_path}: {e}")
    if os.path.exists(avatar_dir):
        for root, dirs, files in os.walk(avatar_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(avatar_dir)
    # Удаляем из avatars.json
    remove_avatar_from_index(user_id, avatar_id)


def get_avatars_index(user_id: int) -> List[Dict[str, Any]]:
    path = get_avatars_index_path(user_id)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f).get('avatars', [])
    return []


def add_avatar_to_index(user_id: int, avatar_id: str, title: str, style: str, created_at: str, preview_path: str = None) -> None:
    path = get_avatars_index_path(user_id)
    avatars = get_avatars_index(user_id)
    if not title:
        title = "Без имени"
    avatar_entry = {
        "avatar_id": avatar_id,
        "title": title,
        "style": style,
        "tune_id": None,
        "created_at": created_at
    }
    if preview_path:
        avatar_entry["preview_path"] = preview_path
    avatars.append(avatar_entry)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"avatars": avatars}, f, ensure_ascii=False, indent=2)


def update_avatar_in_index(user_id: int, avatar_id: str, data: Dict[str, Any]) -> None:
    path = get_avatars_index_path(user_id)
    avatars = get_avatars_index(user_id)
    for avatar in avatars:
        if avatar["avatar_id"] == avatar_id:
            avatar["title"] = data.get("title")
            avatar["style"] = data.get("style")
            avatar["tune_id"] = data.get("tune_id")
            if "preview_path" in data:
                avatar["preview_path"] = data["preview_path"]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"avatars": avatars}, f, ensure_ascii=False, indent=2)


def remove_avatar_from_index(user_id: int, avatar_id: str) -> None:
    path = get_avatars_index_path(user_id)
    avatars = get_avatars_index(user_id)
    avatars = [a for a in avatars if a["avatar_id"] != avatar_id]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"avatars": avatars}, f, ensure_ascii=False, indent=2)


def find_avatar_by_tune_id(tune_id: str):
    """Ищет аватар по tune_id среди всех пользователей. Возвращает (user_id, avatar_id, title) или None."""
    base_dir = AVATAR_STORAGE
    for user_id in os.listdir(base_dir):
        user_dir = os.path.join(base_dir, user_id)
        if not os.path.isdir(user_dir):
            continue
        for avatar_id in os.listdir(user_dir):
            avatar_dir = os.path.join(user_dir, avatar_id)
            json_path = os.path.join(avatar_dir, 'data.json')
            if not os.path.exists(json_path):
                continue
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('tune_id') == tune_id:
                    return user_id, avatar_id, data.get('title', '')
    return None


def mark_avatar_ready(user_id: int, avatar_id: str):
    """Помечает аватар как готовый (ready=True), генерирует превью и добавляет его в avatars.json."""
    data = load_avatar_fsm(user_id, avatar_id)
    if not data:
        return
    data['ready'] = True
    # Генерируем превью по первому фото
    preview_path = None
    if data.get('photos'):
        first_photo = data['photos'][0]
        photo_path = first_photo['path'] if isinstance(first_photo, dict) else first_photo
        preview_path = os.path.join(get_avatar_dir(user_id, avatar_id), 'preview.jpg')
        try:
            generate_avatar_preview(photo_path, preview_path)
            data['preview_path'] = preview_path
        except Exception as e:
            logging.error(f"[AVATAR_MANAGER] Не удалось сгенерировать превью: {e}")
            data['preview_path'] = None
    save_avatar_fsm(user_id, avatar_id, data)
    # Добавляем в avatars.json
    add_avatar_to_index(
        user_id,
        avatar_id,
        data.get('title', ''),
        data.get('style', ''),
        data.get('created_at', ''),
        data.get('preview_path')
    )


async def remove_photo_from_avatar(user_id: int, avatar_id: str, photo_idx: int) -> bool:
    """Асинхронно удаляет фото с сервера и из data.json. Возвращает True, если удалено."""
    data = load_avatar_fsm(user_id, avatar_id) or {}
    photos = data.get('photos', [])
    if 0 <= photo_idx < len(photos):
        photo = photos.pop(photo_idx)
        # Если dict — берём путь, иначе строка
        if isinstance(photo, dict):
            photo_path = photo.get('path')
        else:
            photo_path = photo
        if photo_path and isinstance(photo_path, str) and os.path.exists(photo_path):
            try:
                await aiofiles.os.remove(photo_path)
                logging.info(f"[AVATAR_MANAGER] Фото удалено: {photo_path}")
                result = True
            except Exception as e:
                logging.error(f"[AVATAR_MANAGER] Ошибка удаления фото {photo_path}: {e}")
                result = False
        else:
            logging.warning(f"[AVATAR_MANAGER] Путь к фото невалиден или файл уже удалён: {photo_path}")
            result = False
        data['photos'] = photos
        save_avatar_fsm(user_id, avatar_id, data)
        return result
    return False


def validate_photo(photo_bytes: bytes, existing_photo_paths: list, min_size=(512, 512), max_mb=20):
    """Проверяет размер, формат, разрешение и уникальность фото."""
    # Проверка размера файла
    if len(photo_bytes) > max_mb * 1024 * 1024:
        return False, "Фото слишком большое (максимум 20 МБ)."
    # Проверка формата и разрешения
    try:
        img = Image.open(io.BytesIO(photo_bytes))
        if img.format not in ("JPEG", "PNG"):
            return False, "Поддерживаются только JPEG и PNG."
        if img.size[0] < min_size[0] or img.size[1] < min_size[1]:
            return False, "Фото слишком маленькое (минимум 512x512 пикселей)."
    except Exception:
        return False, "Не удалось прочитать изображение."
    # Проверка уникальности
    photo_hash = hashlib.md5(photo_bytes).hexdigest()
    for path in existing_photo_paths:
        try:
            with open(path, 'rb') as f:
                if hashlib.md5(f.read()).hexdigest() == photo_hash:
                    return False, "Такое фото уже загружено."
        except Exception:
            continue
    return True, photo_hash


def generate_avatar_preview(photo_path: str, preview_path: str, size=(256, 256)) -> str:
    """
    Генерирует уменьшенное превью для аватара и сохраняет в preview_path.
    Возвращает путь к превью.
    """
    logger = logging.getLogger(__name__)
    try:
        img = Image.open(photo_path)
        img = img.convert("RGB")
        img.thumbnail(size)
        # Создаём директорию, если не существует
        os.makedirs(os.path.dirname(preview_path), exist_ok=True)
        img.save(preview_path, "JPEG", quality=90)
        logger.info(f"[AVATAR_MANAGER] Превью сгенерировано: {preview_path}")
        return preview_path
    except Exception as e:
        logger.error(f"[AVATAR_MANAGER] Ошибка генерации превью: {e}")
        raise
