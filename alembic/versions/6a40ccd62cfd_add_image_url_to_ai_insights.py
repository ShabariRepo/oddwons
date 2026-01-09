"""add image_url to ai_insights

Revision ID: 6a40ccd62cfd
Revises: e8423f935861
Create Date: 2026-01-09 01:46:00.105583

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6a40ccd62cfd'
down_revision: Union[str, Sequence[str], None] = 'e8423f935861'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('ai_insights', sa.Column('image_url', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('ai_insights', 'image_url')
