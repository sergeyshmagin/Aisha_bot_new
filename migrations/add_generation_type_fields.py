"""add generation type fields

Revision ID: add_generation_type_fields
Revises: 
Create Date: 2024-12-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_generation_type_fields'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавляем поля типизации генерации"""
    
    # Добавляем новые поля
    op.add_column('image_generations', sa.Column('generation_type', sa.String(50), nullable=False, server_default='avatar'))
    op.add_column('image_generations', sa.Column('source_model', sa.String(100), nullable=True))
    
    # Делаем avatar_id опциональным (уже может быть NULL в некоторых случаях)
    op.alter_column('image_generations', 'avatar_id', nullable=True)
    
    # Создаем индекс для быстрого поиска по типу генерации
    op.create_index('idx_image_generations_type', 'image_generations', ['generation_type'])
    op.create_index('idx_image_generations_user_type', 'image_generations', ['user_id', 'generation_type'])


def downgrade() -> None:
    """Откатываем изменения"""
    
    # Удаляем индексы
    op.drop_index('idx_image_generations_user_type', 'image_generations')
    op.drop_index('idx_image_generations_type', 'image_generations')
    
    # Удаляем столбцы
    op.drop_column('image_generations', 'source_model')
    op.drop_column('image_generations', 'generation_type')
    
    # Возвращаем avatar_id как обязательный (осторожно - может сломать данные)
    op.alter_column('image_generations', 'avatar_id', nullable=False) 