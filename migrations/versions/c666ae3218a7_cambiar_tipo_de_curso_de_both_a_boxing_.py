"""Cambiar tipo de curso de both a boxing school

Revision ID: c666ae3218a7
Revises: 2e6e12ab2af4
Create Date: 2026-05-11 16:10:59.029066
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c666ae3218a7'
down_revision: Union[str, None] = '2e6e12ab2af4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE coursetype ADD VALUE 'BOXING_SCHOOL'"
    )


def downgrade() -> None:
    pass