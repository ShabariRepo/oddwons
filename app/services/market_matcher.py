"""
Dynamic Market Matcher Service.

Uses fuzzy string matching to find markets that exist on both Kalshi and Polymarket.
This replaces the hardcoded regex patterns with automatic discovery.
"""
import re
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from rapidfuzz import fuzz, process
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import Market, Platform
from app.models.cross_platform_match import CrossPlatformMatch

logger = logging.getLogger(__name__)


@dataclass
class MatchCandidate:
    """Internal representation of a potential match."""
    kalshi: Market
    polymarket: Market
    similarity: float


class MarketMatcher:
    """
    Dynamically matches markets across Kalshi and Polymarket.
    Uses fuzzy string matching - NOT hardcoded patterns.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.similarity_threshold = 70  # Minimum similarity score (0-100)

    async def find_all_matches(
        self,
        min_volume: float = 1000,
        max_price: float = 0.98,
        min_price: float = 0.02,
    ) -> List[MatchCandidate]:
        """
        Find ALL cross-platform matches.

        1. Get all Kalshi markets with volume > min_volume
        2. Get all Polymarket markets with volume > min_volume
        3. For each Kalshi market, fuzzy match against all Polymarket titles
        4. If similarity > threshold, it's a match
        """
        # Get Kalshi markets
        kalshi_result = await self.session.execute(
            select(Market)
            .where(Market.platform == Platform.KALSHI)
            .where(Market.volume >= min_volume)
            .where(Market.status.in_(["active", "open"]))
            .where(Market.yes_price.between(min_price, max_price))
        )
        kalshi_markets = kalshi_result.scalars().all()
        logger.info(f"Loaded {len(kalshi_markets)} Kalshi markets for matching")

        # Get Polymarket markets
        poly_result = await self.session.execute(
            select(Market)
            .where(Market.platform == Platform.POLYMARKET)
            .where(Market.volume >= min_volume)
            .where(Market.status.in_(["active", "open"]))
            .where(Market.yes_price.between(min_price, max_price))
        )
        poly_markets = poly_result.scalars().all()
        logger.info(f"Loaded {len(poly_markets)} Polymarket markets for matching")

        if not kalshi_markets or not poly_markets:
            logger.warning("No markets found for one or both platforms")
            return []

        # Build Polymarket lookup
        poly_lookup: Dict[str, Market] = {}
        poly_titles: List[str] = []
        for m in poly_markets:
            normalized = self.normalize_title(m.title)
            poly_lookup[normalized] = m
            poly_titles.append(normalized)

        matches: List[MatchCandidate] = []
        seen_poly_ids = set()  # Avoid duplicate matches

        for kalshi in kalshi_markets:
            normalized_kalshi = self.normalize_title(kalshi.title)

            # Find best match in Polymarket using fuzzy matching
            result = process.extractOne(
                normalized_kalshi,
                poly_titles,
                scorer=fuzz.token_sort_ratio,
                score_cutoff=self.similarity_threshold
            )

            if result:
                matched_title, score, _ = result
                poly_market = poly_lookup.get(matched_title)

                if poly_market and poly_market.id not in seen_poly_ids:
                    # Verify it's actually the same event
                    if self.verify_match(kalshi, poly_market):
                        matches.append(MatchCandidate(
                            kalshi=kalshi,
                            polymarket=poly_market,
                            similarity=score / 100
                        ))
                        seen_poly_ids.add(poly_market.id)
                        logger.debug(f"Match found: {kalshi.title[:40]}... <-> {poly_market.title[:40]}... ({score}%)")

        # Sort by combined volume
        matches.sort(
            key=lambda m: (m.kalshi.volume or 0) + (m.polymarket.volume or 0),
            reverse=True
        )

        logger.info(f"Found {len(matches)} cross-platform matches")
        return matches

    def normalize_title(self, title: str) -> str:
        """Normalize title for better matching."""
        if not title:
            return ""

        title = title.lower()

        # Remove common prefixes
        title = re.sub(r'^will\s+', '', title)
        title = re.sub(r'^does\s+', '', title)
        title = re.sub(r'^is\s+', '', title)

        # Remove question mark and common suffixes
        title = re.sub(r'\?$', '', title)
        title = re.sub(r'\s+in\s+\d{4}$', '', title)  # Remove "in 2025"

        # Remove platform-specific formatting
        title = re.sub(r'\s+', ' ', title).strip()

        # Remove special characters but keep alphanumeric and spaces
        title = re.sub(r'[^\w\s]', '', title)

        return title

    def verify_match(self, kalshi: Market, poly: Market) -> bool:
        """Additional verification that markets are actually the same event."""
        # Skip if titles are too different in length
        len_ratio = len(kalshi.title) / len(poly.title) if poly.title else 0
        if len_ratio < 0.3 or len_ratio > 3:
            return False

        # Check close dates are similar (within 365 days for long-term markets)
        if kalshi.close_time and poly.close_time:
            diff = abs((kalshi.close_time - poly.close_time).days)
            if diff > 365:
                return False

        # Skip known false positives
        false_positive_patterns = [
            # Different question structures
            (r'first.*\$\d+', r'hit.*\$\d+'),  # "first to $X" vs "hit $X"
            (r'before.*\d{4}', r'in.*\d{4}'),  # "before 2025" vs "in 2025"
        ]

        kalshi_lower = kalshi.title.lower()
        poly_lower = poly.title.lower()

        for k_pattern, p_pattern in false_positive_patterns:
            if re.search(k_pattern, kalshi_lower) and not re.search(k_pattern, poly_lower):
                if re.search(p_pattern, poly_lower):
                    return False

        return True

    def generate_match_id(self, title: str) -> str:
        """Generate a URL-friendly match ID from title."""
        if not title:
            return "unknown"

        match_id = title.lower()

        # Remove common words
        for word in ['will', 'the', 'be', 'a', 'an', 'to', 'in', 'of', 'for', 'on', 'as']:
            match_id = re.sub(rf'\b{word}\b', '', match_id)

        # Keep only alphanumeric and spaces
        match_id = re.sub(r'[^a-z0-9\s]', '', match_id)

        # Convert spaces to hyphens
        match_id = re.sub(r'\s+', '-', match_id).strip('-')

        # Remove double hyphens
        match_id = re.sub(r'-+', '-', match_id)

        # Truncate and ensure uniqueness with hash if needed
        if len(match_id) > 50:
            import hashlib
            hash_suffix = hashlib.md5(title.encode()).hexdigest()[:6]
            match_id = match_id[:43] + '-' + hash_suffix

        return match_id or "unknown"

    async def save_matches(self, matches: List[MatchCandidate]) -> Tuple[int, int]:
        """
        Save discovered matches to database.
        Returns (new_count, updated_count).
        """
        new_count = 0
        updated_count = 0

        for match in matches:
            kalshi = match.kalshi
            poly = match.polymarket

            # Generate match_id from topic
            match_id = self.generate_match_id(kalshi.title)

            # Calculate gap (in cents, 0-100 scale)
            k_price = (kalshi.yes_price or 0) * 100
            p_price = (poly.yes_price or 0) * 100
            gap = abs(k_price - p_price)

            if k_price > p_price:
                direction = "kalshi_higher"
            elif p_price > k_price:
                direction = "polymarket_higher"
            else:
                direction = "equal"

            # Check if match exists
            existing = await self.session.execute(
                select(CrossPlatformMatch).where(CrossPlatformMatch.match_id == match_id)
            )
            existing_match = existing.scalar_one_or_none()

            if existing_match:
                # Update existing match
                existing_match.kalshi_yes_price = kalshi.yes_price
                existing_match.kalshi_volume = kalshi.volume
                existing_match.polymarket_yes_price = poly.yes_price
                existing_match.polymarket_volume = poly.volume
                existing_match.price_gap_cents = gap
                existing_match.gap_direction = direction
                existing_match.combined_volume = (kalshi.volume or 0) + (poly.volume or 0)
                existing_match.last_updated = datetime.utcnow()
                existing_match.is_active = True
                updated_count += 1
            else:
                # Create new match
                new_match = CrossPlatformMatch(
                    match_id=match_id,
                    topic=kalshi.title,  # Use Kalshi title as canonical
                    category=kalshi.category or poly.category,
                    kalshi_market_id=kalshi.id,
                    kalshi_title=kalshi.title,
                    kalshi_yes_price=kalshi.yes_price,
                    kalshi_volume=kalshi.volume,
                    kalshi_close_time=kalshi.close_time,
                    polymarket_market_id=poly.id,
                    polymarket_title=poly.title,
                    polymarket_yes_price=poly.yes_price,
                    polymarket_volume=poly.volume,
                    polymarket_close_time=poly.close_time,
                    price_gap_cents=gap,
                    gap_direction=direction,
                    combined_volume=(kalshi.volume or 0) + (poly.volume or 0),
                    similarity_score=match.similarity,
                    is_active=True,
                )
                self.session.add(new_match)
                new_count += 1

        await self.session.commit()
        logger.info(f"Saved matches: {new_count} new, {updated_count} updated")
        return new_count, updated_count

    async def deactivate_stale_matches(self, active_match_ids: List[str]) -> int:
        """Mark matches that no longer exist as inactive."""
        if not active_match_ids:
            return 0

        # Use SQLAlchemy ORM for proper parameter binding
        from sqlalchemy import update
        result = await self.session.execute(
            update(CrossPlatformMatch)
            .where(CrossPlatformMatch.is_active == True)
            .where(CrossPlatformMatch.match_id.not_in(active_match_ids))
            .values(is_active=False, last_updated=datetime.utcnow())
        )
        await self.session.commit()

        deactivated = result.rowcount
        if deactivated > 0:
            logger.info(f"Deactivated {deactivated} stale matches")
        return deactivated


async def run_market_matching(min_volume: float = 1000) -> Dict:
    """
    Run the full market matching process.
    Called from run_analysis.py or manually.
    """
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        matcher = MarketMatcher(session)

        # Find matches
        matches = await matcher.find_all_matches(min_volume=min_volume)

        if not matches:
            return {
                "status": "completed",
                "matches_found": 0,
                "new_matches": 0,
                "updated_matches": 0,
            }

        # Save to database
        new_count, updated_count = await matcher.save_matches(matches)

        # Deactivate stale matches
        active_ids = [matcher.generate_match_id(m.kalshi.title) for m in matches]
        deactivated = await matcher.deactivate_stale_matches(active_ids)

        return {
            "status": "completed",
            "matches_found": len(matches),
            "new_matches": new_count,
            "updated_matches": updated_count,
            "deactivated_matches": deactivated,
            "top_matches": [
                {
                    "topic": m.kalshi.title[:60],
                    "kalshi_price": (m.kalshi.yes_price or 0) * 100,
                    "poly_price": (m.polymarket.yes_price or 0) * 100,
                    "gap_cents": abs((m.kalshi.yes_price or 0) - (m.polymarket.yes_price or 0)) * 100,
                    "combined_volume": (m.kalshi.volume or 0) + (m.polymarket.volume or 0),
                    "similarity": m.similarity,
                }
                for m in matches[:10]
            ],
        }
