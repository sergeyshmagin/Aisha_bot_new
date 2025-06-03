"""Add user settings table

Revision ID: 5f166bbd1e83
Revises: c934618bfc8f
Create Date: 2025-06-01 10:02:50.792541+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5f166bbd1e83'
down_revision: Union[str, None] = 'c934618bfc8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаем таблицу user_settings
    op.create_table('user_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('default_aspect_ratio', sa.String(length=10), nullable=False),
        sa.Column('quick_generation_mode', sa.Boolean(), nullable=False),
        sa.Column('auto_enhance_prompts', sa.Boolean(), nullable=False),
        sa.Column('language_preference', sa.String(length=5), nullable=False),
        sa.Column('show_technical_details', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_settings_user_id'), 'user_settings', ['user_id'], unique=False)


def downgrade() -> None:
    # Удаляем таблицу user_settings
    op.drop_index(op.f('ix_user_settings_user_id'), table_name='user_settings')
    op.drop_table('user_settings')
