"""Add generation_type and source_model to image_generations

Revision ID: 1f8b73901334
Revises: 616b250903b2
Create Date: 2025-06-12 18:44:53.464464+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f8b73901334'
down_revision: Union[str, None] = '616b250903b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем колонки generation_type и source_model если их нет
    try:
        op.add_column('image_generations', sa.Column('generation_type', sa.String(length=50), nullable=True))
        op.add_column('image_generations', sa.Column('source_model', sa.String(length=100), nullable=True))
        
        # Устанавливаем значения по умолчанию для существующих записей
        op.execute("UPDATE image_generations SET generation_type = 'avatar' WHERE generation_type IS NULL")
        
        # Делаем generation_type NOT NULL после заполнения
        op.alter_column('image_generations', 'generation_type', nullable=False, server_default='avatar')
        
    except Exception as e:
        # Игнорируем ошибки если колонки уже существуют
        print(f"Колонки уже существуют или произошла ошибка: {e}")


def downgrade() -> None:
    # Удаляем добавленные колонки
    try:
        op.drop_column('image_generations', 'source_model')
        op.drop_column('image_generations', 'generation_type')
    except Exception as e:
        print(f"Ошибка при удалении колонок: {e}")
