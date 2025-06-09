"""Add Promokode model

Revision ID: 500608a1c114
Revises: e58ecb22a742
Create Date: 2025-06-07 09:18:05.008938+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '500608a1c114'
down_revision: Union[str, None] = 'e58ecb22a742'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
