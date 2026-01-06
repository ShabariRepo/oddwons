"""add_is_admin_to_users

Revision ID: 0af876c0ab82
Revises: 6877fca0b448
Create Date: 2026-01-06 15:31:03.785927

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0af876c0ab82'
down_revision: Union[str, Sequence[str], None] = '6877fca0b448'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_admin column to users table."""
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True, server_default='false'))


def downgrade() -> None:
    """Remove is_admin column from users table."""
    op.drop_column('users', 'is_admin')
