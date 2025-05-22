"""add timezone field to user model

Revision ID: 2f2d8db39ac8
Revises: e16b2266875d
Create Date: 2025-05-21 09:17:22.624425+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f2d8db39ac8'
down_revision: Union[str, None] = 'e16b2266875d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поле timezone в таблицу users
    op.add_column('users', sa.Column('timezone', sa.String(32), nullable=True, server_default='UTC+5'))


def downgrade() -> None:
    # Удаляем поле timezone из таблицы users
    op.drop_column('users', 'timezone')
