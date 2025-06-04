"""fix_enum_native_false

Revision ID: e518b8e01ac3
Revises: d2d95559daaf
Create Date: 2025-06-04 18:03:55.908837+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e518b8e01ac3'
down_revision: Union[str, None] = 'd2d95559daaf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
