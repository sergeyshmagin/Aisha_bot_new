"""change_telegram_id_to_string

Revision ID: 6a15ef710de2
Revises: 35d5bb5c59aa
Create Date: 2025-05-21 12:48:03.108662+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a15ef710de2'
down_revision: Union[str, None] = '35d5bb5c59aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Изменяем тип поля telegram_id с BIGINT на VARCHAR(50)
    op.alter_column('users', 'telegram_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.VARCHAR(length=50),
                    existing_nullable=False,
                    postgresql_using="telegram_id::varchar")


def downgrade() -> None:
    # Возвращаем тип поля telegram_id с VARCHAR(50) на BIGINT
    op.alter_column('users', 'telegram_id',
                    existing_type=sa.VARCHAR(length=50),
                    type_=sa.BIGINT(),
                    existing_nullable=False,
                    postgresql_using="telegram_id::bigint")
