from fastapi import APIRouter, Request
import json
import os
import requests
import logging

router = APIRouter()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
webhook_logger = logging.getLogger('webhook')
if not webhook_logger.handlers:
    handler = logging.FileHandler(os.path.join(LOG_DIR, 'webhook.log'), encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    webhook_logger.addHandler(handler)
    webhook_logger.setLevel(logging.INFO)

def get_user_chat_id(user_id):
    return user_id

def parse_finetune_comment(comment: str):
    # Ожидается формат: 'user_id=...;avatar_id=...;...'
    result = {}
    if not comment:
        return result
    for part in comment.split(';'):
        if '=' in part:
            k, v = part.split('=', 1)
            result[k.strip()] = v.strip()
    return result

@router.post("/api/avatar/status_update")
async def avatar_status_update(request: Request):
    try:
        data = await request.json()
        webhook_logger.info(f"Webhook called: {data}")
        # fal.ai может прислать finetune_comment вместо user_id/avatar_id
        user_id = str(data.get("user_id") or "")
        avatar_id = data.get("avatar_id")
        new_status = data.get("status")
        comment = data.get("comment")
        finetune_id = data.get("finetune_id")
        preview_path = data.get("preview_path")
        # Парсим user_id и avatar_id из finetune_comment, если нужно
        if (not user_id or not avatar_id) and comment:
            parsed = parse_finetune_comment(comment)
            user_id = user_id or parsed.get("user_id")
            avatar_id = avatar_id or parsed.get("avatar_id")
        if not user_id or not avatar_id:
            webhook_logger.error(f"user_id or avatar_id not found in webhook: {data}")
            return {"ok": False, "error": "user_id or avatar_id not found"}
        avatars_path = f"storage/avatars/{user_id}/avatars.json"
        updated = False
        if os.path.exists(avatars_path):
            with open(avatars_path, "r", encoding="utf-8") as f:
                avatars_data = json.load(f)
            for avatar in avatars_data.get("avatars", []):
                if avatar["avatar_id"] == avatar_id:
                    avatar["status"] = new_status
                    if comment:
                        avatar["comment"] = comment
                    if finetune_id:
                        avatar["finetune_id"] = finetune_id
                    if preview_path:
                        avatar["preview_path"] = preview_path
                    updated = True
            with open(avatars_path, "w", encoding="utf-8") as f:
                json.dump(avatars_data, f, ensure_ascii=False, indent=2)
        # Отправить уведомление пользователю
        if updated:
            chat_id = get_user_chat_id(user_id)
            status_text = "✅ Ваш аватар готов!" if new_status == "ready" else "❌ Ошибка обучения аватара."
            requests.post(TELEGRAM_API_URL, json={
                "chat_id": chat_id,
                "text": status_text,
                "parse_mode": "HTML"
            })
            webhook_logger.info(f"Status updated for user_id={user_id}, avatar_id={avatar_id}, status={new_status}")
        else:
            webhook_logger.warning(f"Avatar not found or not updated: user_id={user_id}, avatar_id={avatar_id}")
        return {"ok": True}
    except Exception as e:
        webhook_logger.error(f"Exception in webhook: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}
