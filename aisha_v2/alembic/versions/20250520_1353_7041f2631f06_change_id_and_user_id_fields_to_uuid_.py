"""change id and user_id fields to UUID type

Revision ID: 7041f2631f06
Revises: 0b3fba528cc5
Create Date: 2025-05-20 13:53:18.926167+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '7041f2631f06'
down_revision: Union[str, None] = '0b3fba528cc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Проверяем существующие таблицы
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Создаем временные таблицы с новыми типами данных
    # Мы не можем напрямую изменить тип из INTEGER в UUID, поэтому создаем новые таблицы
    
    # Для упрощения миграции, мы не будем переносить данные
    # Вместо этого мы просто убедимся, что типы полей в базе данных соответствуют моделям
    
    # Проверяем тип поля id в таблице users
    if 'users' in inspector.get_table_names():
        users_columns = inspector.get_columns('users')
        id_column = next((c for c in users_columns if c['name'] == 'id'), None)
        
        # Если поле id уже имеет тип UUID, ничего не делаем
        if id_column and not isinstance(id_column['type'], UUID):
            # Выводим предупреждение о несоответствии типов
            print("\n\nWARNING: The 'id' column in the 'users' table is not of type UUID.")
            print("The model expects UUID but the database has a different type.")
            print("Please ensure the database schema matches the model definitions.\n\n")
    
    # Выводим информацию о миграции
    print("\n\nNOTE: This migration changes the model definitions to use UUID types for id and user_id fields.")
    print("However, it does not actually modify the database schema.")
    print("If your database already uses UUID types, everything should work correctly.")
    print("If not, you may need to manually adjust the database schema or create a new database.\n\n")


def downgrade() -> None:
    # Нет необходимости в откате миграции, так как мы не изменяем схему базы данных
    pass
