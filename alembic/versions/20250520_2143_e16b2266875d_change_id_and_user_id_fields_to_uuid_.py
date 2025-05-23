"""add transcript_metadata column to user_transcripts table

Revision ID: e16b2266875d
Revises: 7041f2631f06
Create Date: 2025-05-20 21:43:49.254663+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e16b2266875d'
down_revision: Union[str, None] = '7041f2631f06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем колонку transcript_metadata в таблицу user_transcripts
    op.add_column('user_transcripts', sa.Column('transcript_metadata', sa.JSON(), nullable=True))
    
    # Устанавливаем значение по умолчанию для существующих записей
    op.execute("UPDATE user_transcripts SET transcript_metadata = '{}'::jsonb WHERE transcript_metadata IS NULL")


def downgrade() -> None:
    # Удаляем колонку transcript_metadata из таблицы user_transcripts
    op.drop_column('user_transcripts', 'transcript_metadata')
