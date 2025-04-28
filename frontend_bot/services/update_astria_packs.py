"""Скрипт для скачивания и сохранения паков Astria в JSON-файл."""

import requests
import json
import os

PACKS_URL = "https://api.astria.ai/gallery/packs"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "astria_packs.json")


def fetch_and_save_packs():
    """Скачивает паки Astria и сохраняет их в локальный JSON-файл."""
    try:
        response = requests.get(PACKS_URL, timeout=10)
        response.raise_for_status()
        packs = response.json()
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(packs, f, ensure_ascii=False, indent=2)
        print(f"[OK] Скачано и сохранено {len(packs)} паков в {OUTPUT_PATH}")
    except Exception as e:
        print(f"[ERROR] Не удалось обновить паки: {e}")


if __name__ == "__main__":
    fetch_and_save_packs() 