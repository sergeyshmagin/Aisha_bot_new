"""add prompt_metadata field to image generation

Revision ID: add_prompt_metadata_field
Revises: 0e2145738117
Create Date: 2025-05-31 21:27:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_prompt_metadata_field'
down_revision = '0e2145738117'
branch_labels = None
depends_on = Nonedef upgrade() -> None:
    # Добавляем поле prompt_metadata в таблицу image_generations
    op.add_column('image_generations', sa.Column('prompt_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))def downgrade() -> None:
    # Удаляем поле prompt_metadata из таблицы image_generations
    op.drop_column('image_generations', 'prompt_metadata')
