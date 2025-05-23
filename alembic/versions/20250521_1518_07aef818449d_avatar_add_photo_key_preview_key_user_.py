"""avatar: add photo_key, preview_key, user_id, photo_metadata, photo_hash; add UserProfile, UserTranscriptCache

Revision ID: 07aef818449d
Revises: manual_convert_telegram_id
Create Date: 2025-05-21 15:18:00.008416+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07aef818449d'
down_revision: Union[str, None] = 'manual_convert_telegram_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
