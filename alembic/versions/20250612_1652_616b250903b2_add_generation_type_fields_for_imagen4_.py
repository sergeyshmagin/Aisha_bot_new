"""add generation type fields for imagen4 support

Revision ID: 616b250903b2
Revises: f2488211585a
Create Date: 2025-06-12 16:52:05.825553+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '616b250903b2'
down_revision: Union[str, None] = 'f2488211585a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавляем поля типизации генерации для поддержки Imagen 4"""
    
    # Добавляем новые поля
    op.add_column('image_generations', sa.Column('generation_type', sa.String(50), nullable=False, server_default='avatar'))
    op.add_column('image_generations', sa.Column('source_model', sa.String(100), nullable=True))
    
    # Делаем avatar_id опциональным для Imagen 4 (может быть NULL)
    op.alter_column('image_generations', 'avatar_id', nullable=True)
    
    # Создаем индексы для быстрого поиска по типу генерации
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
    
    # Возвращаем avatar_id как обязательный (ВНИМАНИЕ: может сломать данные если есть NULL)
    # op.alter_column('image_generations', 'avatar_id', nullable=False)
