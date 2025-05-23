"""manual_convert_telegram_id

Revision ID: manual_convert_telegram_id
Revises: 6a15ef710de2
Create Date: 2025-05-21 12:58:00.000000+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'manual_convert_telegram_id'
down_revision: Union[str, None] = '6a15ef710de2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаем временную колонку для хранения строковых значений telegram_id
    op.add_column('users', sa.Column('telegram_id_str', sa.String(50), nullable=True))
    
    # Копируем данные из telegram_id в telegram_id_str, преобразуя их в строки
    op.execute("UPDATE users SET telegram_id_str = telegram_id::text")
    
    # Удаляем колонку telegram_id
    op.drop_column('users', 'telegram_id')
    
    # Переименовываем telegram_id_str в telegram_id
    op.alter_column('users', 'telegram_id_str', new_column_name='telegram_id')
    
    # Делаем колонку telegram_id NOT NULL, добавляем индекс и ограничение уникальности
    op.alter_column('users', 'telegram_id', nullable=False)
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)


def downgrade() -> None:
    # Удаляем индекс
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    
    # Создаем временную колонку для хранения целочисленных значений telegram_id
    op.add_column('users', sa.Column('telegram_id_int', sa.BigInteger(), nullable=True))
    
    # Копируем данные из telegram_id в telegram_id_int, преобразуя их в целые числа
    op.execute("UPDATE users SET telegram_id_int = telegram_id::bigint WHERE telegram_id ~ '^[0-9]+$'")
    
    # Удаляем колонку telegram_id
    op.drop_column('users', 'telegram_id')
    
    # Переименовываем telegram_id_int в telegram_id
    op.alter_column('users', 'telegram_id_int', new_column_name='telegram_id')
    
    # Делаем колонку telegram_id NOT NULL, добавляем индекс и ограничение уникальности
    op.alter_column('users', 'telegram_id', nullable=False)
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)
