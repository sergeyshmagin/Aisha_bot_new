"""change_telegram_id_to_bigint

Revision ID: 35d5bb5c59aa
Revises: d526093a1ae3
Create Date: 2025-05-21 12:42:28.768594+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '35d5bb5c59aa'
down_revision: Union[str, None] = 'd526093a1ae3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Изменяем тип поля telegram_id с INTEGER на BIGINT
    op.alter_column('users', 'telegram_id',
                    existing_type=sa.INTEGER(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)


def downgrade() -> None:
    # Возвращаем тип поля telegram_id с BIGINT на INTEGER
    op.alter_column('users', 'telegram_id',
                    existing_type=sa.BigInteger(),
                    type_=sa.INTEGER(),
                    existing_nullable=False)
