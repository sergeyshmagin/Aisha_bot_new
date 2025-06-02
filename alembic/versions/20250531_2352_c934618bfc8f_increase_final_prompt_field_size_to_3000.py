"""increase_final_prompt_field_size_to_3000

Revision ID: c934618bfc8f
Revises: add_prompt_metadata_field
Create Date: 2025-05-31 23:52:51.276747+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa# revision identifiers, used by Alembic.
revision: str = 'c934618bfc8f'
down_revision: Union[str, None] = 'add_prompt_metadata_field'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = Nonedef upgrade() -> None:
    # Увеличиваем размер поля final_prompt с VARCHAR(1500) до VARCHAR(3000)
    op.alter_column(
        'image_generations',
        'final_prompt',
        type_=sa.String(3000),
        existing_type=sa.String(1500),
        nullable=False
    )def downgrade() -> None:
    # Возвращаем размер поля final_prompt обратно к VARCHAR(1500)
    # ВНИМАНИЕ: может привести к потере данных если есть промпты > 1500 символов
    op.alter_column(
        'image_generations', 
        'final_prompt',
        type_=sa.String(1500),
        existing_type=sa.String(3000),
        nullable=False
    )
