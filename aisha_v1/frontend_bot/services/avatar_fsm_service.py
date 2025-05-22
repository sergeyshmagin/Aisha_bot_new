from frontend_bot.services.avatar_workflow import update_draft_avatar, finalize_draft_avatar, delete_draft_avatar
from frontend_bot.services.state_utils import set_state_pg, clear_state_pg
from frontend_bot.services.photo_buffer import clear_photo_buffer_redis
from frontend_bot.handlers.avatar.state import user_session, user_gallery

async def set_avatar_type(user_id, avatar_id, gender, session):
    await update_draft_avatar(user_id, session, {"avatar_data": {"gender": gender}})
    await set_state_pg(user_id, {"state": "avatar_enter_name", "avatar_id": avatar_id}, session)

async def set_avatar_name(user_id, avatar_id, name, session):
    await update_draft_avatar(user_id, session, {"avatar_data": {"title": name}})
    await set_state_pg(user_id, {"state": "avatar_confirm", "avatar_id": avatar_id}, session)

async def confirm_avatar(user_id, avatar_id, session):
    await finalize_draft_avatar(user_id, avatar_id, session)
    await set_state_pg(user_id, "main_menu", session)

async def edit_avatar_name(user_id, avatar_id, session):
    await set_state_pg(user_id, {"state": "avatar_enter_name", "avatar_id": avatar_id}, session)

async def cleanup_state(user_id, avatar_id, session):
    await clear_state_pg(user_id, session)
    await delete_draft_avatar(user_id, avatar_id, session)
    await clear_photo_buffer_redis(user_id)
    user_session.pop(user_id, None)
    for key in list(user_gallery.keys()):
        if key.startswith(f"{user_id}:"):
            user_gallery.pop(key, None) 