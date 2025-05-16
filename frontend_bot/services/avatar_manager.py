"""
Сервис для управления аватарами пользователей.
"""

import os
import json
import io
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image
import hashlib
import aiofiles.os
import logging
from pathlib import Path
from frontend_bot.config import (
    AVATAR_STORAGE_PATH,
    PHOTO_MAX_MB,
    PHOTO_MIN_RES,
    STORAGE_DIR,
    AVATAR_MIN_PHOTOS,
    AVATAR_MAX_PHOTOS,
    THUMBNAIL_SIZE,
    ALLOWED_PHOTO_FORMATS,
    MAX_PHOTO_SIZE
)
import aiofiles
from frontend_bot.services.file_utils import (
    async_exists,
    async_makedirs,
    async_remove,
    async_rmtree,
)
from frontend_bot.shared.image_processing import AsyncImageProcessor
from frontend_bot.shared.file_operations import AsyncFileManager
from frontend_bot.config import AVATAR_DIR

AVATAR_STORAGE = Path(AVATAR_STORAGE_PATH)

logger = logging.getLogger(__name__)

# Глобальный словарь для хранения текущих avatar_id
_current_avatar_ids: Dict[int, str] = {}

async def validate_photo(photo_bytes: bytes, existing_paths: List[str] = None) -> Tuple[bool, str]:
    """
    Валидирует фото по размеру, формату и уникальности.
    
    Args:
        photo_bytes: Бинарные данные фото
        existing_paths: Список путей к существующим фото для проверки уникальности
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    try:
        # Проверка размера файла
        if len(photo_bytes) > MAX_PHOTO_SIZE:
            return False, f"Фото слишком большое. Максимальный размер: {PHOTO_MAX_MB}MB"
            
        # Проверка формата и размеров изображения
        img = Image.open(io.BytesIO(photo_bytes))
        if img.format.lower() not in ALLOWED_PHOTO_FORMATS:
            return False, f"Неподдерживаемый формат. Разрешены: {', '.join(ALLOWED_PHOTO_FORMATS)}"
            
        width, height = img.size
        if width < PHOTO_MIN_RES or height < PHOTO_MIN_RES:
            return False, f"Фото слишком маленькое. Минимальное разрешение: {PHOTO_MIN_RES}x{PHOTO_MIN_RES}"
            
        # Проверка уникальности
        if existing_paths:
            photo_hash = hashlib.md5(photo_bytes).hexdigest()
            for path in existing_paths:
                if os.path.exists(path):
                    with open(path, 'rb') as f:
                        existing_hash = hashlib.md5(f.read()).hexdigest()
                        if existing_hash == photo_hash:
                            return False, "Это фото уже добавлено"
                            
        return True, "OK"
        
    except Exception as e:
        logger.error(f"Ошибка валидации фото: {e}")
        return False, f"Ошибка при проверке фото: {str(e)}"

async def generate_avatar_preview(
    photo_path: Path, preview_path: Path, size=(256, 256)
) -> Path:
    """
    Генерирует уменьшенное превью для аватара.
    
    Args:
        photo_path: Путь к исходному фото
        preview_path: Путь для сохранения превью
        size: Размер превью
        
    Returns:
        Path: Путь к сгенерированному превью или None при ошибке
    """
    import os
    from io import BytesIO
    from pathlib import Path
    try:
        # Приведение путей к Path
        photo_path = Path(photo_path)
        preview_path = Path(preview_path)
        if not os.path.exists(photo_path):
            logger.error(f"[AVATAR_MANAGER] Исходный файл для превью не найден: {photo_path}")
            return None
        file_size = os.path.getsize(photo_path)
        logger.info(f"[AVATAR_MANAGER] Открываю фото для превью: {photo_path}, размер={file_size} байт")
        photo_bytes = await AsyncFileManager.read_binary(photo_path)
        img = await AsyncImageProcessor.open(photo_bytes)
        logger.info(f"[AVATAR_MANAGER] Формат исходного фото: {getattr(img, 'format', None)}, размер={img.size}")
        img = img.convert("RGB")
        img.thumbnail(size)
        await AsyncFileManager.ensure_dir(preview_path.parent)
        preview_bytes = BytesIO()
        img.save(preview_bytes, "JPEG", quality=90)
        await AsyncFileManager.write_binary(preview_path, preview_bytes.getvalue())
        logger.info(f"[AVATAR_MANAGER] Превью успешно создано: {preview_path}")
        return preview_path
    except Exception as e:
        logger.exception(f"[AVATAR_MANAGER] Ошибка генерации превью: {e} (photo_path={photo_path}, preview_path={preview_path})")
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
        data.get("gender", None),
    )

async def ensure_avatar_dirs(storage_dir: Path = STORAGE_DIR) -> None:
    """Создает необходимые директории для аватаров."""
    avatar_dir = storage_dir / AVATAR_DIR
    await AsyncFileManager.ensure_dir(storage_dir)
    await AsyncFileManager.ensure_dir(avatar_dir)

async def get_user_avatar_dir(user_id: str, storage_dir: Path = STORAGE_DIR) -> Path:
    """Получает директорию пользователя для аватаров."""
    avatar_dir = storage_dir / AVATAR_DIR
    user_dir = avatar_dir / str(user_id)
    await AsyncFileManager.ensure_dir(user_dir)
    return user_dir

async def save_avatar_photo(user_id: str, photo_data: bytes, photo_id: str, storage_dir: Path = STORAGE_DIR) -> Path:
    """Сохраняет фото пользователя."""
    user_dir = await get_user_avatar_dir(user_id, storage_dir)
    photo_path = user_dir / f"{photo_id}.jpg"
    await AsyncFileManager.write_binary(photo_path, photo_data)
    return photo_path

async def get_user_avatar_photos(user_id: str, storage_dir: Path = STORAGE_DIR) -> List[Path]:
    """Получает список фото пользователя."""
    user_dir = await get_user_avatar_dir(user_id, storage_dir)
    if not await AsyncFileManager.exists(user_dir):
        return []
    
    files = await AsyncFileManager.list_dir(user_dir)
    return [user_dir / f for f in files if f.endswith(".jpg")]

async def clear_user_avatar_photos(user_id: str, storage_dir: Path = STORAGE_DIR) -> None:
    """Очищает все фото пользователя."""
    user_dir = await get_user_avatar_dir(user_id, storage_dir)
    if await AsyncFileManager.exists(user_dir):
        await AsyncFileManager.safe_rmtree(user_dir)

def get_current_avatar_id(user_id: int) -> str | None:
    """Получает текущий avatar_id для пользователя."""
    return _current_avatar_ids.get(user_id)

def set_current_avatar_id(user_id: int, avatar_id: str | None) -> None:
    """Устанавливает текущий avatar_id для пользователя."""
    if avatar_id is None:
        _current_avatar_ids.pop(user_id, None)
    else:
        _current_avatar_ids[user_id] = avatar_id

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
    # Сохраняем gender, если есть
    if "gender" not in data:
        data["gender"] = None
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"[AVATAR_MANAGER] save_avatar_fsm: data saved")

async def add_photo_to_avatar(
    user_id: int, avatar_id: str, photo_bytes: bytes, file_id: str = None
) -> str:
    # Валидация фото на размер, формат, уникальность
    avatar_dir = get_avatar_dir(user_id, avatar_id)
    await async_makedirs(avatar_dir, exist_ok=True)
    existing = [
        os.path.join(avatar_dir, f)
        for f in os.listdir(avatar_dir)
        if f.startswith("photo_") and f.endswith(".jpg")
    ]
    is_valid, result = await validate_photo(photo_bytes, existing)
    if not is_valid:
        logging.warning(f"[AVATAR_MANAGER] Фото не прошло валидацию: {result}")
        raise ValueError(result)
    photo_num = len(existing) + 1
    photo_path = os.path.join(avatar_dir, f"photo_{photo_num}.jpg")
    async with aiofiles.open(photo_path, "wb") as f:
        await f.write(photo_bytes)
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
    # Генерируем превью, если это первое фото и превью ещё нет
    if len(data["photos"]) == 1 or not data.get("preview_path"):
        preview_path = os.path.join(avatar_dir, "preview.jpg")
        try:
            await generate_avatar_preview(photo_path, preview_path)
            data["preview_path"] = preview_path
        except Exception as e:
            print(f"[AVATAR_MANAGER] Ошибка генерации превью: {e}")
            data["preview_path"] = None
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
            "preview_path",
            "gender",
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
        "gender": None,
    }
    for k in (
        "title",
        "class_name",
        "finetune_id",
        "status",
        "avatar_url",
        "created_at",
        "training_params",
        "gender",
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
            "gender",
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
    gender: str = None,
) -> None:
    logging.info(
        f"[add_avatar_to_index] called with: user_id={user_id}, avatar_id={avatar_id}, title={title}, style={style}, created_at={created_at}, preview_path={preview_path}, status={status}, finetune_id={finetune_id}, is_main={is_main}, gender={gender}"
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
        "gender": gender,
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
    # Сначала обновляем нужный аватар
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
            if "gender" in data:
                avatar["gender"] = data["gender"]
    # Затем сбрасываем is_main у всех остальных
    main_id = None
    for avatar in avatars:
        if avatar.get("is_main"):
            main_id = avatar["avatar_id"]
            break
    if main_id:
        for avatar in avatars:
            if avatar["avatar_id"] != main_id:
                avatar["is_main"] = False
    # Гарантируем, что хотя бы один основной
    main_count = sum(1 for a in avatars if a.get("is_main"))
    if main_count == 0 and avatars:
        avatars[0]["is_main"] = True
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

async def remove_photo_from_avatar(user_id: int, avatar_id: str, photo_idx: int) -> bool:
    """
    Асинхронно удаляет фото с сервера и из data.json.
    
    Args:
        user_id: ID пользователя
        avatar_id: ID аватара
        photo_idx: Индекс фото для удаления
        
    Returns:
        bool: True если фото удалено, False если не удалено
    """
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
