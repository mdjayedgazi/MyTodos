"""add phone number column for user

Revision ID: 344b2c14e511
Revises: 
Create Date: 2026-08-06 20:30:49.992401

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '344b2c14e511'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('phone', sa.String(15), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # DeepSeek v4: downgrade was a no-op (pass); implemented it properly
    op.drop_column('users', 'phone')
