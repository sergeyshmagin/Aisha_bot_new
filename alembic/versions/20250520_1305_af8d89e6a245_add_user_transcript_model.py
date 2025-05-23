"""add user transcript model

Revision ID: af8d89e6a245
Revises: 0d4a13416473
Create Date: 2025-05-20 13:05:29.594246+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af8d89e6a245'
down_revision: Union[str, None] = '0d4a13416473'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
