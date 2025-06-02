"""Add generation system tables

Revision ID: 664dc8b5f141
Revises: 43b44a2e1001
Create Date: 2025-05-29 09:53:07.840886+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa# revision identifiers, used by Alembic.
revision: str = '664dc8b5f141'
down_revision: Union[str, None] = '43b44a2e1001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = Nonedef upgrade() -> None:
    passdef downgrade() -> None:
    pass
