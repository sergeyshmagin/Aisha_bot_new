"""fix_enum_native_flag_and_defaults

Revision ID: 230ce2455211
Revises: 6f8aaa37f3fa
Create Date: 2025-05-24 08:48:49.721669+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '230ce2455211'
down_revision: Union[str, None] = '6f8aaa37f3fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
