"""Add generation system tables with models

Revision ID: 0e2145738117
Revises: 664dc8b5f141
Create Date: 2025-05-29 09:53:33.473875+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa# revision identifiers, used by Alembic.
revision: str = '0e2145738117'
down_revision: Union[str, None] = '664dc8b5f141'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = Nonedef upgrade() -> None:
    passdef downgrade() -> None:
    pass
