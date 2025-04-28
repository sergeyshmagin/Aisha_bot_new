"""Сервис для работы с паками Astria, сохранёнными в JSON-файле."""

import json
import os
from functools import lru_cache

PACKS_PATH = os.path.join(os.path.dirname(__file__), "astria_packs.json")

@lru_cache(maxsize=1)
def get_all_packs():
    """Загружает все паки Astria из локального JSON-файла."""
    with open(PACKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_pack_by_id(pack_id):
    """Возвращает пак по его id."""
    packs = get_all_packs()
    for pack in packs:
        if str(pack.get("id")) == str(pack_id):
            return pack
    return None


def get_pack_by_slug(slug):
    """Возвращает пак по его slug."""
    packs = get_all_packs()
    for pack in packs:
        if pack.get("slug") == slug:
            return pack
    return None 