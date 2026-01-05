"""Companion approach schema - insights become highlights

Revision ID: a2b3c4d5e6f7
Revises: 0158ed6404e8
Create Date: 2026-01-04 20:30:00.000000

COMPANION APP: We inform and contextualize, NOT recommend bets.
This migration transforms the schema from "alpha hunter" to "research companion".
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, Sequence[str], None] = '0158ed6404e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade to companion approach schema."""

    # ==========================================================================
    # AI INSIGHTS TABLE - Transform from betting tips to market highlights
    # ==========================================================================

    # Add new companion columns
    op.add_column('ai_insights', sa.Column('market_title', sa.Text(), nullable=True))
    op.add_column('ai_insights', sa.Column('category', sa.String(length=50), nullable=True))
    op.add_column('ai_insights', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('ai_insights', sa.Column('current_odds', sa.JSON(), nullable=True))
    op.add_column('ai_insights', sa.Column('implied_probability', sa.Text(), nullable=True))
    op.add_column('ai_insights', sa.Column('volume_note', sa.String(length=100), nullable=True))
    op.add_column('ai_insights', sa.Column('recent_movement', sa.String(length=100), nullable=True))
    op.add_column('ai_insights', sa.Column('movement_context', sa.Text(), nullable=True))
    op.add_column('ai_insights', sa.Column('upcoming_catalyst', sa.Text(), nullable=True))
    op.add_column('ai_insights', sa.Column('analyst_note', sa.Text(), nullable=True))
    op.add_column('ai_insights', sa.Column('interest_score', sa.Integer(), nullable=True))

    # Drop old betting-focused columns (make nullable first to avoid data issues)
    op.alter_column('ai_insights', 'recommendation', nullable=True)
    op.alter_column('ai_insights', 'confidence_score', nullable=True)
    op.alter_column('ai_insights', 'one_liner', nullable=True)

    # Drop old indexes that reference removed/renamed concepts
    op.drop_index('idx_insights_actionable', table_name='ai_insights')
    op.drop_index('idx_insights_recommendation', table_name='ai_insights')

    # Create new companion-style indexes
    op.create_index('idx_insights_category_recent', 'ai_insights', ['category', 'created_at'], unique=False)
    op.create_index('idx_insights_interest', 'ai_insights', ['interest_score', 'created_at'], unique=False)

    # ==========================================================================
    # DAILY DIGESTS TABLE - Transform from betting tips to news briefing
    # ==========================================================================

    # Add new companion columns
    op.add_column('daily_digests', sa.Column('headline', sa.Text(), nullable=True))
    op.add_column('daily_digests', sa.Column('top_movers', sa.JSON(), nullable=True))
    op.add_column('daily_digests', sa.Column('most_active', sa.JSON(), nullable=True))
    op.add_column('daily_digests', sa.Column('upcoming_catalysts', sa.JSON(), nullable=True))
    op.add_column('daily_digests', sa.Column('category_snapshots', sa.JSON(), nullable=True))
    op.add_column('daily_digests', sa.Column('notable_price_gaps', sa.JSON(), nullable=True))

    # Note: Keep old columns for now to preserve any existing data
    # They can be dropped in a future migration after data migration


def downgrade() -> None:
    """Downgrade to alpha-hunter schema."""

    # Daily digests - remove companion columns
    op.drop_column('daily_digests', 'notable_price_gaps')
    op.drop_column('daily_digests', 'category_snapshots')
    op.drop_column('daily_digests', 'upcoming_catalysts')
    op.drop_column('daily_digests', 'most_active')
    op.drop_column('daily_digests', 'top_movers')
    op.drop_column('daily_digests', 'headline')

    # AI insights - restore old indexes
    op.drop_index('idx_insights_interest', table_name='ai_insights')
    op.drop_index('idx_insights_category_recent', table_name='ai_insights')
    op.create_index('idx_insights_recommendation', 'ai_insights', ['recommendation', 'created_at'], unique=False)
    op.create_index('idx_insights_actionable', 'ai_insights', ['confidence_score', 'created_at'], unique=False, postgresql_where=sa.text('confidence_score > 60'))

    # Restore NOT NULL constraints
    op.alter_column('ai_insights', 'one_liner', nullable=False)
    op.alter_column('ai_insights', 'confidence_score', nullable=False)
    op.alter_column('ai_insights', 'recommendation', nullable=False)

    # Remove companion columns
    op.drop_column('ai_insights', 'interest_score')
    op.drop_column('ai_insights', 'analyst_note')
    op.drop_column('ai_insights', 'upcoming_catalyst')
    op.drop_column('ai_insights', 'movement_context')
    op.drop_column('ai_insights', 'recent_movement')
    op.drop_column('ai_insights', 'volume_note')
    op.drop_column('ai_insights', 'implied_probability')
    op.drop_column('ai_insights', 'current_odds')
    op.drop_column('ai_insights', 'summary')
    op.drop_column('ai_insights', 'category')
    op.drop_column('ai_insights', 'market_title')
