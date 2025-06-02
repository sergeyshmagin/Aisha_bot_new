"""Remove legacy fields from Avatar and AvatarPhoto models

⚠️  ВАЖНО: Эта миграция удаляет Legacy поля. Убедитесь что:
1. Все данные migrated
2. Код не использует Legacy поля  
3. Создан бэкап БД

Legacy поля к удалению:
- avatars.is_draft → заменено на status
- avatars.photo_key → не используется 
- avatars.preview_key → не используется
- avatar_photos.order → заменено на upload_order

Revision ID: e3da12f2e9cc
Revises: b2df0db38780
Create Date: 2025-05-24 17:24:50.218810+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
