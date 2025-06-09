"""Add UserBalance and Promokode models for paid transcription

Revision ID: e58ecb22a742
Revises: 8dd2a1d651eb
Create Date: 2025-06-07 09:14:53.184521+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e58ecb22a742'
down_revision: Union[str, None] = '8dd2a1d651eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
