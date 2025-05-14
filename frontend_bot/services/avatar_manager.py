import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from PIL import Image
import hashlib
import aiofiles.os
import logging
from frontend_bot.config import AVATAR_STORAGE_PATH, PHOTO_MAX_MB, PHOTO_MIN_RES
import aiofiles
from frontend_bot.services.file_utils import (
    async_exists,
    async_makedirs,
    async_remove,
    async_rmtree,
)
from frontend_bot.shared.image_processing import AsyncImageProcessor

AVATAR_STORAGE = AVATAR_STORAGE_PATH


def get_user_dir(user_id: int) -> str:
    return os.path.join(AVATAR_STORAGE, str(user_id))


def get_avatar_dir(user_id: int, avatar_id: str) -> str:
    return os.path.join(get_user_dir(user_id), avatar_id)


def get_avatar_json_path(user_id: int, avatar_id: str) -> str:
    return os.path.join(get_avatar_dir(user_id, avatar_id), "data.json")


def get_avatars_index_path(user_id: int) -> str:
    return os.path.join(get_user_dir(user_id), "avatars.json")


async def init_avatar_fsm(
    user_id: int,
    avatar_id: str,
    title: str = "",
    class_name: str = "",
    training_params: dict = None,
) -> None:
    avatar_dir = get_avatar_dir(user_id, avatar_id)
    print(
        f"[AVATAR_MANAGER] init_avatar_fsm: user_id={user_id}, "
        f"avatar_id={avatar_id}, avatar_dir={avatar_dir}"
    )
    await async_makedirs(avatar_dir, exist_ok=True)
    data = {
        "photos": [],
        "title": title,
        "class_name": class_name,
        "finetune_id": None,
        "status": "pending",
        "avatar_url": None,
        "created_at": datetime.utcnow().isoformat(),
        "training_params": training_params or {},
    }
    print(f"[AVATAR_MANAGER] init_avatar_fsm: data={data}")
    await save_avatar_fsm(user_id, avatar_id, data)
    # Не добавляем в avatars.json до завершения генерации


async def load_avatar_fsm(user_id: int, avatar_id: str) -> Optional[Dict[str, Any]]:
    path = get_avatar_json_path(user_id, avatar_id)
    if await async_exists(path):
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content)
    return None


async def save_avatar_fsm(user_id: int, avatar_id: str, data: Dict[str, Any]) -> None:
    avatar_dir = get_avatar_dir(user_id, avatar_id)
    print(
        f"[AVATAR_MANAGER] save_avatar_fsm: user_id={user_id}, "
        f"avatar_id={avatar_id}, avatar_dir={avatar_dir}"
    )
    await async_makedirs(avatar_dir, exist_ok=True)
    path = get_avatar_json_path(user_id, avatar_id)
    print(f"[AVATAR_MANAGER] save_avatar_fsm: path={path}")
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"[AVATAR_MANAGER] save_avatar_fsm: data saved")


async def add_photo_to_avatar(
    user_id: int, avatar_id: str, photo_bytes: bytes, file_id: str = None
) -> str:
    avatar_dir = get_avatar_dir(user_id, avatar_id)
    print(
        f"[AVATAR_MANAGER] add_photo_to_avatar: user_id={user_id}, "
        f"avatar_id={avatar_id}, avatar_dir={avatar_dir}"
    )
    await async_makedirs(avatar_dir, exist_ok=True)
    existing = [
        f
        for f in os.listdir(avatar_dir)
        if f.startswith("photo_") and f.endswith(".jpg")
    ]
    photo_num = len(existing) + 1
    photo_path = os.path.join(avatar_dir, f"photo_{photo_num}.jpg")
    print(f"[AVATAR_MANAGER] add_photo_to_avatar: photo_path={photo_path}")
    async with aiofiles.open(photo_path, "wb") as f:
        await f.write(photo_bytes)
    print(f"[AVATAR_MANAGER] add_photo_to_avatar: photo written")
    # Обновляем JSON
    data = await load_avatar_fsm(user_id, avatar_id) or {
        "photos": [],
        "title": "",
        "class_name": "",
        "finetune_id": None,
        "status": "pending",
        "avatar_url": None,
        "created_at": None,
        "training_params": {},
    }
    if file_id is None:
        photo_entry = {"path": photo_path}
    else:
        photo_entry = {"path": photo_path, "file_id": file_id}
    data.setdefault("photos", []).append(photo_entry)
    # Оставляем только нужные поля
    data = {
        k: data.get(k)
        for k in (
            "photos",
            "title",
            "class_name",
            "finetune_id",
            "status",
            "avatar_url",
            "created_at",
            "training_params",
        )
    }
    await save_avatar_fsm(user_id, avatar_id, data)
    print(f"[AVATAR_MANAGER] add_photo_to_avatar: photo added to data.json")
    return photo_path


async def update_avatar_fsm(user_id: int, avatar_id: str, **kwargs) -> None:
    data = await load_avatar_fsm(user_id, avatar_id) or {
        "photos": [],
        "title": "",
        "class_name": "",
        "finetune_id": None,
        "status": "pending",
        "avatar_url": None,
        "created_at": None,
        "training_params": {},
    }
    for k in (
        "title",
        "class_name",
        "finetune_id",
        "status",
        "avatar_url",
        "created_at",
        "training_params",
    ):
        if k in kwargs:
            data[k] = kwargs[k]
    # Оставляем только нужные поля
    data = {
        k: data.get(k)
        for k in (
            "photos",
            "title",
            "class_name",
            "finetune_id",
            "status",
            "avatar_url",
            "created_at",
            "training_params",
        )
    }
    await save_avatar_fsm(user_id, avatar_id, data)
    # Если обновили title/style/tune_id — обновить avatars.json
    await update_avatar_in_index(user_id, avatar_id, data)


async def clear_avatar_fsm(user_id: int, avatar_id: str) -> None:
    """
    Асинхронно удаляет все файлы аватара и запись из avatars.json.
    """
    logger = logging.getLogger(__name__)
    avatar_dir = get_avatar_dir(user_id, avatar_id)
    try:
        # Удаляем все файлы и поддиректории
        if await async_exists(avatar_dir):
            for root, dirs, files in os.walk(avatar_dir, topdown=False):
                for name in files:
                    file_path = os.path.join(root, name)
                    try:
                        await async_remove(file_path)
                        logger.info(f"[AVATAR_MANAGER] Файл удалён: {file_path}")
                    except Exception as e:
                        logger.exception(f"Ошибка удаления файла {file_path}: {e}")
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    try:
                        await async_rmtree(dir_path)
                        logger.info(f"[AVATAR_MANAGER] Папка удалена: {dir_path}")
                    except Exception as e:
                        logger.exception(f"Ошибка удаления папки {dir_path}: {e}")
            try:
                await async_rmtree(avatar_dir)
                logger.info(f"[AVATAR_MANAGER] Папка аватара удалена: {avatar_dir}")
            except Exception as e:
                logger.exception(f"Ошибка удаления папки аватара {avatar_dir}: {e}")
    except Exception as e:
        logger.exception(f"Ошибка при удалении аватара {avatar_id}: {e}")
    # Удаляем из avatars.json
    await remove_avatar_from_index(user_id, avatar_id)


async def migrate_avatars_index(user_id: int):
    """Миграция avatars.json: добавляет is_main, если нет; первый становится основным."""
    path = get_avatars_index_path(user_id)
    if not await async_exists(path):
        return
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        data = json.loads(await f.read())
    avatars = data.get("avatars", [])
    has_main = any(a.get("is_main") for a in avatars)
    if not has_main and avatars:
        avatars[0]["is_main"] = True
    for a in avatars:
        if "is_main" not in a:
            a["is_main"] = False
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps({"avatars": avatars}, ensure_ascii=False, indent=2))


async def get_avatars_index(user_id: int) -> List[Dict[str, Any]]:
    path = get_avatars_index_path(user_id)
    if await async_exists(path):
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            content = await f.read()
            avatars = json.loads(content).get("avatars", [])
            # Миграция на лету: если нет is_main, добавить
            has_main = any(a.get("is_main") for a in avatars)
            if not has_main and avatars:
                avatars[0]["is_main"] = True
            for a in avatars:
                if "is_main" not in a:
                    a["is_main"] = False
            return avatars
    return []


async def add_avatar_to_index(
    user_id: int,
    avatar_id: str,
    title: str,
    style: str,
    created_at: str,
    preview_path: str = None,
    status: str = "training",
    finetune_id: str = None,
    is_main: bool = False,
) -> None:
    logging.info(
        f"[add_avatar_to_index] called with: user_id={user_id}, avatar_id={avatar_id}, title={title}, style={style}, created_at={created_at}, preview_path={preview_path}, status={status}, finetune_id={finetune_id}, is_main={is_main}"
    )
    path = get_avatars_index_path(user_id)
    avatars = await get_avatars_index(user_id)
    logging.info(f"[add_avatar_to_index] avatars before: {avatars}")
    if not title:
        title = "Без имени"
    # Если это первый аватар — делаем его основным
    if not avatars:
        is_main = True
    avatar_entry = {
        "avatar_id": avatar_id,
        "title": title,
        "style": style,
        "tune_id": None,
        "created_at": created_at,
        "status": status,
        "finetune_id": finetune_id,
        "is_main": is_main,
    }
    if preview_path:
        avatar_entry["preview_path"] = preview_path
    avatars.append(avatar_entry)
    # Гарантируем, что только один is_main
    if is_main:
        for a in avatars:
            if a["avatar_id"] != avatar_id:
                a["is_main"] = False
    logging.info(f"[add_avatar_to_index] avatars after: {avatars}")
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps({"avatars": avatars}, ensure_ascii=False, indent=2))
    logging.info(f"[add_avatar_to_index] avatars.json written: {path}")


async def update_avatar_in_index(
    user_id: int, avatar_id: str, data: Dict[str, Any]
) -> None:
    path = get_avatars_index_path(user_id)
    avatars = await get_avatars_index(user_id)
    for avatar in avatars:
        if avatar["avatar_id"] == avatar_id:
            avatar["title"] = data.get("title")
            avatar["style"] = data.get("style")
            avatar["tune_id"] = data.get("tune_id")
            avatar["status"] = data.get("status", "training")
            avatar["finetune_id"] = data.get("finetune_id", None)
            if "preview_path" in data:
                avatar["preview_path"] = data["preview_path"]
            if "is_main" in data:
                avatar["is_main"] = data["is_main"]
    # Гарантируем, что только один is_main
    main_count = sum(1 for a in avatars if a.get("is_main"))
    if main_count == 0 and avatars:
        avatars[0]["is_main"] = True
    elif main_count > 1:
        first_main = next((a for a in avatars if a.get("is_main")), None)
        for a in avatars:
            if a is not first_main:
                a["is_main"] = False
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps({"avatars": avatars}, ensure_ascii=False, indent=2))


async def remove_avatar_from_index(user_id: int, avatar_id: str) -> None:
    path = get_avatars_index_path(user_id)
    avatars = await get_avatars_index(user_id)
    avatars = [a for a in avatars if a["avatar_id"] != avatar_id]
    # Если удалили основной — сделать основным первый оставшийся
    if avatars and not any(a.get("is_main") for a in avatars):
        avatars[0]["is_main"] = True
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps({"avatars": avatars}, ensure_ascii=False, indent=2))


async def find_avatar_by_tune_id(tune_id: str):
    """Ищет аватар по tune_id среди всех пользователей. Возвращает (user_id, avatar_id, title) или None."""
    base_dir = AVATAR_STORAGE
    for user_id in os.listdir(base_dir):
        user_dir = os.path.join(base_dir, user_id)
        if not os.path.isdir(user_dir):
            continue
        for avatar_id in os.listdir(user_dir):
            avatar_dir = os.path.join(user_dir, avatar_id)
            json_path = os.path.join(avatar_dir, "data.json")
            if not await async_exists(json_path):
                continue
            async with aiofiles.open(json_path, "r", encoding="utf-8") as f:
                data = json.loads(await f.read())
                if data.get("tune_id") == tune_id:
                    return user_id, avatar_id, data.get("title", "")
    return None


async def mark_avatar_ready(user_id: int, avatar_id: str):
    """Помечает аватар как готовый (ready=True), генерирует превью и добавляет его в avatars.json."""
    data = await load_avatar_fsm(user_id, avatar_id)
    if not data:
        return
    data["ready"] = True
    # Генерируем превью по первому фото
    preview_path = None
    if data.get("photos"):
        first_photo = data["photos"][0]
        photo_path = (
            first_photo["path"] if isinstance(first_photo, dict) else first_photo
        )
        preview_path = os.path.join(get_avatar_dir(user_id, avatar_id), "preview.jpg")
        try:
            await generate_avatar_preview(photo_path, preview_path)
            data["preview_path"] = preview_path
        except Exception as e:
            logging.error(f"[AVATAR_MANAGER] Не удалось сгенерировать превью: {e}")
            data["preview_path"] = None
    await save_avatar_fsm(user_id, avatar_id, data)
    # Добавляем в avatars.json
    await add_avatar_to_index(
        user_id,
        avatar_id,
        data.get("title", ""),
        data.get("style", ""),
        data.get("created_at", ""),
        data.get("preview_path"),
        data.get("status", "training"),
        data.get("finetune_id", None),
        data.get("is_main", False),
    )


async def remove_photo_from_avatar(
    user_id: int, avatar_id: str, photo_idx: int
) -> bool:
    """Асинхронно удаляет фото с сервера и из data.json. Возвращает True, если удалено."""
    data = await load_avatar_fsm(user_id, avatar_id) or {}
    photos = data.get("photos", [])
    if 0 <= photo_idx < len(photos):
        photo = photos.pop(photo_idx)
        # Если dict — берём путь, иначе строка
        if isinstance(photo, dict):
            photo_path = photo.get("path")
        else:
            photo_path = photo
        if (
            photo_path
            and isinstance(photo_path, str)
            and await async_exists(photo_path)
        ):
            try:
                await async_remove(photo_path)
                logging.info(f"[AVATAR_MANAGER] Фото удалено: {photo_path}")
                result = True
            except Exception as e:
                logging.error(
                    f"[AVATAR_MANAGER] Ошибка удаления фото {photo_path}: {e}"
                )
                result = False
        else:
            logging.warning(
                f"[AVATAR_MANAGER] Путь к фото невалиден или файл уже удалён: {photo_path}"
            )
            result = False
        data["photos"] = photos
        await save_avatar_fsm(user_id, avatar_id, data)
        return result
    return False


async def validate_photo(
    photo_bytes: bytes,
    existing_photo_paths: list,
    min_size=(PHOTO_MIN_RES, PHOTO_MIN_RES),
    max_mb=PHOTO_MAX_MB,
):
    """Проверяет размер, формат, разрешение и уникальность фото."""
    # Проверка размера файла
    if len(photo_bytes) > max_mb * 1024 * 1024:
        return False, (f"Фото слишком большое (максимум {PHOTO_MAX_MB} МБ).")
    # Проверка формата и разрешения
    try:
        img = await AsyncImageProcessor.open(photo_bytes)
        if img.format not in ("JPEG", "PNG"):
            return False, ("Поддерживаются только JPEG и PNG.")
        if img.size[0] < min_size[0] or img.size[1] < min_size[1]:
            return False, (
                f"Фото слишком маленькое (минимум {PHOTO_MIN_RES}x{PHOTO_MIN_RES})."
            )
    except Exception:
        return False, "Не удалось прочитать фото."
    # Проверка уникальности
    photo_hash = hashlib.md5(photo_bytes).hexdigest()
    for path in existing_photo_paths:
        try:
            async with aiofiles.open(path, "rb") as f:
                file_bytes = await f.read()
                if hashlib.md5(file_bytes).hexdigest() == photo_hash:
                    return False, "Такое фото уже загружено."
        except Exception:
            continue
    return True, photo_hash


async def generate_avatar_preview(
    photo_path: str, preview_path: str, size=(256, 256)
) -> str:
    """
    Генерирует уменьшенное превью для аватара и сохраняет в preview_path.
    Возвращает путь к превью.
    """
    logger = logging.getLogger(__name__)
    try:
        if photo_path.endswith((".jpg", ".png")):
            img = await AsyncImageProcessor.open(photo_path)
        else:
            img = await AsyncImageProcessor.open(photo_path)
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


async def process_avatar(self, photo_path: str) -> str:
    try:
        img = await AsyncImageProcessor.open(photo_path)
        # ... остальной код
    except Exception as e:
        logging.error(f"[AVATAR_MANAGER] Ошибка обработки аватара: {e}")
        raise
