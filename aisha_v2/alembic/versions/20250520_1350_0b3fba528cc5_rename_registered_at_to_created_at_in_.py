"""rename registered_at to created_at in users table

Revision ID: 0b3fba528cc5
Revises: 5c20774499ff
Create Date: 2025-05-20 13:50:07.632948+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b3fba528cc5'
down_revision: Union[str, None] = '5c20774499ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Проверяем, существует ли колонка registered_at
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('users')
    column_names = [column['name'] for column in columns]
    
    if 'registered_at' in column_names:
        # Переименовываем колонку registered_at в created_at
        op.alter_column('users', 'registered_at', new_column_name='created_at')
    elif 'created_at' not in column_names:
        # Если нет ни registered_at, ни created_at, добавляем created_at
        op.add_column('users', sa.Column('created_at', sa.DateTime(timezone=True), nullable=True))
        
        # Заполняем колонку текущим временем для существующих записей
        op.execute("UPDATE users SET created_at = updated_at WHERE created_at IS NULL")
        
        # Делаем колонку обязательной
        op.alter_column('users', 'created_at', nullable=False)


def downgrade() -> None:
    # Проверяем, существует ли колонка created_at
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('users')
    column_names = [column['name'] for column in columns]
    
    if 'created_at' in column_names:
        # Переименовываем колонку created_at в registered_at
        op.alter_column('users', 'created_at', new_column_name='registered_at')
    elif 'registered_at' not in column_names:
        # Если нет ни created_at, ни registered_at, добавляем registered_at
        op.add_column('users', sa.Column('registered_at', sa.DateTime(timezone=True), nullable=True))
        
        # Заполняем колонку текущим временем для существующих записей
        op.execute("UPDATE users SET registered_at = updated_at WHERE registered_at IS NULL")
        
        # Делаем колонку обязательной
        op.alter_column('users', 'registered_at', nullable=False)
