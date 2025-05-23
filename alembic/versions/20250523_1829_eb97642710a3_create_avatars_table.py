"""create_avatars_table

Revision ID: eb97642710a3
Revises: 291dbd04d153
Create Date: 2025-05-23 18:29:32.550973+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb97642710a3'
down_revision: Union[str, None] = '291dbd04d153'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
