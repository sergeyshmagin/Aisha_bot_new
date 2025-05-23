"""add_avatar_models_and_enums

Revision ID: 291dbd04d153
Revises: 07aef818449d
Create Date: 2025-05-23 16:33:03.094305+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '291dbd04d153'
down_revision: Union[str, None] = '07aef818449d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
