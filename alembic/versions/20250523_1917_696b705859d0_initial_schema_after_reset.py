"""initial_schema_after_reset

Revision ID: 696b705859d0
Revises: create_avatars_manually
Create Date: 2025-05-23 19:17:04.114363+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '696b705859d0'
down_revision: Union[str, None] = 'create_avatars_manually'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
