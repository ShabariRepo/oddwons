"""add source_articles to ai_insights

Revision ID: 6877fca0b448
Revises: 7353256d44b8
Create Date: 2026-01-06 13:44:22.230049

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6877fca0b448'
down_revision: Union[str, Sequence[str], None] = '7353256d44b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add source_articles and news_context columns to ai_insights."""
    op.add_column('ai_insights', sa.Column('source_articles', sa.JSON(), nullable=True))
    op.add_column('ai_insights', sa.Column('news_context', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove source_articles and news_context columns from ai_insights."""
    op.drop_column('ai_insights', 'news_context')
    op.drop_column('ai_insights', 'source_articles')
