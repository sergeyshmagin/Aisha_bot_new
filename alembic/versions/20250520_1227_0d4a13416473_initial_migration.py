"""Initial migration

Revision ID: 0d4a13416473
Revises: 20250520_initial
Create Date: 2025-05-20 12:27:32.980119+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d4a13416473'
down_revision: Union[str, None] = '20250520_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
