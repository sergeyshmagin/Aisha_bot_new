"""add registered_at field to users table

Revision ID: 5c20774499ff
Revises: af8d89e6a245
Create Date: 2025-05-20 13:47:10.967616+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c20774499ff'
down_revision: Union[str, None] = 'af8d89e6a245'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем колонку registered_at в таблицу users
    op.add_column('users', sa.Column('registered_at', sa.DateTime(timezone=True), nullable=True))
    
    # Заполняем колонку текущим временем для существующих записей
    op.execute("UPDATE users SET registered_at = updated_at WHERE registered_at IS NULL")
    
    # Делаем колонку обязательной
    op.alter_column('users', 'registered_at', nullable=False)


def downgrade() -> None:
    # Удаляем колонку registered_at из таблицы users
    op.drop_column('users', 'registered_at')
