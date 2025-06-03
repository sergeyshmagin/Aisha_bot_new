"""ensure_order_field_removed

Revision ID: e3e0f1fd5585
Revises: e3da12f2e9cc
Create Date: 2025-05-24 22:13:36.506602+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3e0f1fd5585'
down_revision: Union[str, None] = 'e3da12f2e9cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
