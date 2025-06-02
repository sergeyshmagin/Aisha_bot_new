"""Add generation system tables

Revision ID: 46c8b1038233
Revises: final_remove_order
Create Date: 2025-05-29 06:21:06.436231+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa# revision identifiers, used by Alembic.
revision: str = '46c8b1038233'
down_revision: Union[str, None] = 'final_remove_order'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = Nonedef upgrade() -> None:
    passdef downgrade() -> None:
    pass
