import os
from typing import Optional


def save_file(path: str, data: bytes) -> None:
    """Сохраняет данные в файл по указанному пути."""
    with open(path, 'wb') as f:
        f.write(data)


def remove_file(path: str) -> None:
    """Удаляет файл, если он существует."""
    if os.path.exists(path):
        os.remove(path)


def file_exists(path: str) -> bool:
    """Проверяет существование файла."""
    return os.path.exists(path)


def get_file_size(path: str) -> Optional[int]:
    """Возвращает размер файла в байтах, если файл существует."""
    if os.path.exists(path):
        return os.path.getsize(path)
    return None


def make_user_dir(base_dir: str, user_id: str) -> str:
    """Создаёт директорию пользователя и возвращает её путь."""
    user_dir = os.path.join(base_dir, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir 