"""fix avatar status enum values

Revision ID: d2d95559daaf
Revises: 5f166bbd1e83
Create Date: 2025-06-04 08:11:03.982497+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2d95559daaf'
down_revision: Union[str, None] = '5f166bbd1e83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
