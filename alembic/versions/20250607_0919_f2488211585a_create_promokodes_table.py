"""Create promokodes table

Revision ID: f2488211585a
Revises: 500608a1c114
Create Date: 2025-06-07 09:19:31.201957+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2488211585a'
down_revision: Union[str, None] = '500608a1c114'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
