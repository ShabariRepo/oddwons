"""
X (Twitter) Posting Service for OddWons.

Automated social media posting for market updates, movers, and insights.
Uses X API v2 with OAuth 1.0a authentication.

Free tier: 1,500 tweets/month (~50/day)
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import random
import tempfile
import os

import httpx
import tweepy
from groq import Groq
import uuid

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# =============================================================================
# BOT SETTINGS & POST TRACKING
# =============================================================================

async def get_bot_settings() -> Dict[str, Any]:
    """Get current bot settings from database."""
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.x_post import XBotSettings

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(XBotSettings).where(XBotSettings.id == "default")
        )
        settings_row = result.scalar_one_or_none()

        if not settings_row:
            # Create default settings if not exists
            settings_row = XBotSettings(id="default", enabled=True)
            session.add(settings_row)
            await session.commit()
            await session.refresh(settings_row)

        return settings_row.to_dict()


async def is_bot_enabled(post_type: str = None) -> bool:
    """Check if the bot is enabled (globally and for specific post type)."""
    try:
        settings = await get_bot_settings()

        # Check master switch
        if not settings.get("enabled", True):
            logger.info("X bot is disabled (master switch)")
            return False

        # Check specific post type if provided
        if post_type:
            type_key = f"{post_type}_enabled"
            if not settings.get(type_key, True):
                logger.info(f"X bot is disabled for {post_type}")
                return False

        return True
    except Exception as e:
        logger.error(f"Error checking bot settings: {e}")
        return True  # Default to enabled if error


async def save_x_post(
    post_type: str,
    content: str,
    tweet_result: Optional[Dict] = None,
    market_data: Optional[Dict] = None,
    insight_ids: Optional[List[str]] = None,
    market_ids: Optional[List[str]] = None,
    image_url: Optional[str] = None,
) -> Optional[str]:
    """Save an X post record to the database."""
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.x_post import XPost, XPostType, XPostStatus

    async with AsyncSessionLocal() as session:
        try:
            # Map post_type string to enum
            type_map = {
                "morning": XPostType.MORNING_MOVERS,
                "morning_movers": XPostType.MORNING_MOVERS,
                "afternoon": XPostType.PLATFORM_COMPARISON,
                "platform_comparison": XPostType.PLATFORM_COMPARISON,
                "evening": XPostType.MARKET_HIGHLIGHT,
                "market_highlight": XPostType.MARKET_HIGHLIGHT,
                "weekly": XPostType.WEEKLY_RECAP,
                "weekly_recap": XPostType.WEEKLY_RECAP,
                "stats": XPostType.DAILY_STATS,
                "daily_stats": XPostType.DAILY_STATS,
                "promo": XPostType.PROMO,
            }
            x_post_type = type_map.get(post_type, XPostType.MANUAL)

            # Determine status and tweet info
            if tweet_result and tweet_result.get("success"):
                status = XPostStatus.POSTED
                tweet_id = tweet_result.get("tweet_id")
                tweet_url = f"https://x.com/i/status/{tweet_id}" if tweet_id else None
                error_message = None
                posted_at = datetime.utcnow()
            elif tweet_result:
                status = XPostStatus.FAILED
                tweet_id = None
                tweet_url = None
                error_message = tweet_result.get("error", "Unknown error")
                posted_at = None
            else:
                status = XPostStatus.PENDING
                tweet_id = None
                tweet_url = None
                error_message = None
                posted_at = None

            post = XPost(
                id=str(uuid.uuid4()),
                tweet_id=tweet_id,
                tweet_url=tweet_url,
                post_type=x_post_type,
                status=status,
                content=content,
                has_image=bool(image_url) or (tweet_result and tweet_result.get("has_image", False)),
                image_url=image_url,
                market_data=market_data,
                insight_ids=insight_ids,
                market_ids=market_ids,
                error_message=error_message,
                posted_at=posted_at,
            )

            session.add(post)
            await session.commit()

            logger.info(f"Saved X post record: {post.id} ({status.value})")
            return post.id

        except Exception as e:
            logger.error(f"Failed to save X post record: {e}")
            return None


# =============================================================================
# TWEET TEMPLATES - Visually Formatted
# =============================================================================

TEMPLATES = {
    "morning_movers": [
        """📊 Overnight Movers

{market_1_title}
├ Was: {market_1_old}%
└ Now: {market_1_new}% ({market_1_change})

📈 What's behind the move?

Full analysis → oddwons.ai""",

        """⚡ Markets shifted overnight

1️⃣ {market_1_title}
   {market_1_new}% ({market_1_change})

2️⃣ {market_2_title}
   {market_2_new}% ({market_2_change})

💡 We broke down the why...

oddwons.ai""",

        """🌅 GM prediction markets

{market_1_title}
{market_1_old}% → {market_1_new}%
{change_bar}

🔍 The story behind the numbers...

Deep dive → oddwons.ai"""
    ],

    "platform_comparison": [
        """⚖️ Platforms disagree

{title}

Kalshi:     {kalshi}% {kalshi_bar}
Polymarket: {poly}% {poly_bar}

🤔 Why the {diff}pt gap?

oddwons.ai has the breakdown""",

        """🔍 Same event, different odds

{title}

┌─────────────────┐
│ Kalshi:     {kalshi}% │
│ Polymarket: {poly}% │
└─────────────────┘

📊 We explain the spread...

oddwons.ai""",

        """📊 Price Gap Alert

{title}

Kalshi ····· {kalshi}%
Poly ······· {poly}%

💡 What do they know that you don't?

oddwons.ai"""
    ],

    "market_highlight": [
        """🔥 Market to Watch

{title}

Currently: {price}%
Volume: ${volume}

📈 One key factor is driving this...

Full analysis → oddwons.ai""",

        """👀 Worth watching

{title}

{price}% {price_bar}

💡 There's more to this story...

Deep dive → oddwons.ai""",

        """📈 Trending Market

{title}

├ Price: {price}%
├ Volume: ${volume}
└ Platform: {platform}

🔍 Why is money flowing here?

oddwons.ai"""
    ],

    "weekly_recap_1": """📊 OddWons Weekly Recap

This week in prediction markets:

📈 {total_markets} markets tracked
💰 ${volume} in volume
🔄 {matches} cross-platform matches
⚡ {movers} big movers

Top categories:
{categories}""",

    "weekly_recap_2": """What moved this week:

1️⃣ {top_1}
2️⃣ {top_2}
3️⃣ {top_3}

Follow @oddwons for daily updates

📊 oddwons.ai""",

    "catalyst_alert": """⏰ Upcoming Catalyst

{event}
📅 {date}

Markets to watch:
• {market_1}
• {market_2}

Expect volatility 📈📉

oddwons.ai""",

    "daily_stat": """📊 Daily Stats

Markets tracked: {total}
├ Kalshi: {kalshi_count}
└ Polymarket: {poly_count}

24h volume: ${volume}
Cross-platform matches: {matches}

oddwons.ai"""
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def make_bar(percentage: float, length: int = 10) -> str:
    """Create a visual progress bar."""
    filled = int(percentage / 100 * length)
    empty = length - filled
    return "█" * filled + "░" * empty


def format_change(old_price: float, new_price: float) -> str:
    """Format price change with +/- sign."""
    change = new_price - old_price
    if change > 0:
        return f"+{change:.0f}%"
    elif change < 0:
        return f"{change:.0f}%"
    else:
        return "0%"


def truncate(text: str, max_length: int = 50) -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def format_volume(volume: float) -> str:
    """Format volume in K/M/B."""
    if volume >= 1_000_000_000:
        return f"{volume/1_000_000_000:.1f}B"
    elif volume >= 1_000_000:
        return f"{volume/1_000_000:.1f}M"
    elif volume >= 1_000:
        return f"{volume/1_000:.0f}K"
    else:
        return f"{volume:.0f}"


# =============================================================================
# X CLIENT SETUP
# =============================================================================

def get_x_client() -> Optional[tweepy.Client]:
    """Get authenticated X API v2 client."""
    if not all([
        settings.x_api_key,
        settings.x_api_secret,
        settings.x_consumer_key,
        settings.x_consumer_secret
    ]):
        logger.warning("X API credentials not configured - skipping X posts")
        return None
    
    try:
        client = tweepy.Client(
            consumer_key=settings.x_consumer_key,
            consumer_secret=settings.x_consumer_secret,
            access_token=settings.x_api_key,
            access_token_secret=settings.x_api_secret
        )
        return client
    except Exception as e:
        logger.error(f"Failed to create X client: {e}")
        return None


def get_x_api_v1() -> Optional[tweepy.API]:
    """Get X API v1.1 client for media uploads.
    
    Note: Media upload requires v1.1 API, then we use v2 for posting.
    """
    if not all([
        settings.x_api_key,
        settings.x_api_secret,
        settings.x_consumer_key,
        settings.x_consumer_secret
    ]):
        return None
    
    try:
        auth = tweepy.OAuth1UserHandler(
            settings.x_consumer_key,
            settings.x_consumer_secret,
            settings.x_api_key,
            settings.x_api_secret
        )
        return tweepy.API(auth)
    except Exception as e:
        logger.error(f"Failed to create X v1.1 client: {e}")
        return None


def get_groq_client() -> Optional[Groq]:
    """Get Groq client for tweet generation."""
    api_key = getattr(settings, 'groq_api_key', None)
    if not api_key:
        logger.warning("Groq API key not configured - using template tweets")
        return None

    try:
        return Groq(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to create Groq client: {e}")
        return None


# =============================================================================
# TWEET GENERATION
# =============================================================================

TWEET_PROMPT = """You are the social media voice for OddWons, a prediction market research platform.

PERSONALITY: You're chill and unbothered, but also genuinely interested in what's happening. Think "your friend who's weirdly into prediction markets explaining something cool at a party." You're not trying too hard, but you're also not boring. Casual, slightly witty, relatable to millennials and gen z.

VIBE EXAMPLES:
- "yo this market is moving" not "BREAKING: Market experiences significant movement"
- "why tho 🤔" not "What could be causing this?"
- "the platforms can't agree lol" not "There is disagreement between platforms"
- "anyway here's why it's interesting" not "This is noteworthy because"

Create a visually formatted tweet that TEASES analysis without giving it all away. Hook people and funnel them to oddwons.ai.

Guidelines:
- Use visual structure (├ └ emojis, line breaks) but keep it clean
- Show the DATA (prices, movements, percentages)
- Add ONE chill teaser line that hints at the "why"
- Be casual but not cringe - no "fellow kids" energy
- Can use lowercase for vibe, but keep data readable
- End with low-key CTA pointing to oddwons.ai
- Keep under 260 characters (leave room for hashtags)
- NO betting advice, we're just observing
- Occasional "lol", "ngl", "lowkey" is fine when natural
- ALWAYS end with hashtags: #OddWons #PredictionMarkets #Polymarket #Kalshi are REQUIRED on every tweet, then optionally add 1 more relevant one like #Crypto #Politics #Sports #Elections based on the topic

Market data:
{market_data}

Tweet type: {tweet_type}

Example good tweets:

1. Morning Movers:
"overnight moves hit different

Fed rate cut March?
├ Was: 45%
└ Now: 52% (+7%)

something shifted 👀

oddwons.ai

#OddWons #PredictionMarkets #Polymarket #Kalshi"

2. Platform Gap:
"the platforms can't agree lol

Bitcoin $100K by June
Kalshi: 42% ████░░░░░░
Poly:   38% ████░░░░░░

4 points is a lot... why tho?

oddwons.ai

#OddWons #PredictionMarkets #Polymarket #Kalshi"

3. Market Highlight:
"this one's getting spicy

Super Bowl odds rn:
├ Chiefs: 32%
├ 49ers: 28%
└ Lions: 18%

there's a reason for the shuffle

oddwons.ai

#OddWons #PredictionMarkets #Polymarket #Kalshi"

4. Big movement:
"yo this market MOVED

[Market name]
was 35% → now 52%

ngl the reason is kinda interesting

oddwons.ai

#OddWons #PredictionMarkets #Polymarket #Kalshi"

Write ONLY the tweet, nothing else. Match the chill energy and always include #OddWons #PredictionMarkets #Polymarket #Kalshi."""


async def generate_tweet_with_ai(
    market_data: Dict[str, Any],
    tweet_type: str = "mover"
) -> str:
    """Generate tweet content using Groq."""
    groq = get_groq_client()

    if not groq:
        return generate_template_tweet(market_data, tweet_type)

    try:
        response = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=300,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": TWEET_PROMPT.format(
                    market_data=json.dumps(market_data, indent=2),
                    tweet_type=tweet_type
                )
            }]
        )
        tweet = response.choices[0].message.content.strip()

        if len(tweet) > 280:
            tweet = tweet[:277] + "..."

        return tweet

    except Exception as e:
        logger.error(f"AI tweet generation failed: {e}")
        return generate_template_tweet(market_data, tweet_type)


def generate_template_tweet(
    market_data: Dict[str, Any],
    tweet_type: str = "mover"
) -> str:
    """Template-based tweet generation with visual formatting."""
    
    if tweet_type == "morning_movers":
        template = random.choice(TEMPLATES["morning_movers"])
        
        markets = market_data.get("markets", [])
        if len(markets) >= 1:
            m1 = markets[0]
            data = {
                "market_1_title": truncate(m1.get("title", "Market"), 40),
                "market_1_old": f"{m1.get('old_price', 50):.0f}",
                "market_1_new": f"{m1.get('new_price', 50):.0f}",
                "market_1_change": format_change(m1.get('old_price', 50), m1.get('new_price', 50)),
                "change_bar": make_bar(m1.get('new_price', 50)),
                "context": m1.get("context", "High activity overnight")[:60]
            }
            
            if len(markets) >= 2:
                m2 = markets[1]
                data.update({
                    "market_2_title": truncate(m2.get("title", "Market"), 40),
                    "market_2_old": f"{m2.get('old_price', 50):.0f}",
                    "market_2_new": f"{m2.get('new_price', 50):.0f}",
                    "market_2_change": format_change(m2.get('old_price', 50), m2.get('new_price', 50)),
                })
            
            if len(markets) >= 3:
                m3 = markets[2]
                data.update({
                    "market_3_title": truncate(m3.get("title", "Market"), 40),
                    "market_3_new": f"{m3.get('new_price', 50):.0f}",
                    "market_3_change": format_change(m3.get('old_price', 50), m3.get('new_price', 50)),
                })
            
            try:
                return template.format(**data)
            except KeyError:
                pass
        
        # Fallback
        return f"""📊 Morning Markets

Check today's top movers and insights

oddwons.ai"""

    elif tweet_type == "platform_comparison":
        template = random.choice(TEMPLATES["platform_comparison"])
        
        kalshi = market_data.get("kalshi_price", 50)
        poly = market_data.get("polymarket_price", 50)
        diff = abs(kalshi - poly)
        
        data = {
            "title": truncate(market_data.get("title", "Market"), 45),
            "kalshi": f"{kalshi:.0f}",
            "poly": f"{poly:.0f}",
            "diff": f"{diff:.0f}",
            "kalshi_bar": make_bar(kalshi),
            "poly_bar": make_bar(poly),
        }
        
        try:
            return template.format(**data)
        except KeyError:
            pass
        
        return f"""⚖️ Platform Gap

{truncate(market_data.get('title', 'Market'), 50)}

Kalshi: {kalshi:.0f}%
Polymarket: {poly:.0f}%

{diff:.0f} point difference

oddwons.ai"""

    elif tweet_type == "market_highlight":
        template = random.choice(TEMPLATES["market_highlight"])
        
        price = market_data.get("yes_price", 0.5) * 100
        volume = market_data.get("volume_24h", 0)
        
        data = {
            "title": truncate(market_data.get("title", "Market"), 45),
            "price": f"{price:.0f}",
            "price_bar": make_bar(price),
            "volume": format_volume(volume),
            "platform": market_data.get("platform", "").capitalize(),
            "summary": truncate(market_data.get("summary", "Trending market"), 80),
        }
        
        try:
            return template.format(**data)
        except KeyError:
            pass
        
        return f"""🔥 Market Spotlight

{truncate(market_data.get('title', 'Market'), 50)}

{price:.0f}% {make_bar(price)}

oddwons.ai"""

    elif tweet_type == "daily_stat":
        template = TEMPLATES["daily_stat"]
        
        data = {
            "total": market_data.get("total_markets", 0),
            "kalshi_count": market_data.get("kalshi_count", 0),
            "poly_count": market_data.get("poly_count", 0),
            "volume": format_volume(market_data.get("total_volume", 0)),
            "matches": market_data.get("matches", 0),
        }
        
        return template.format(**data)

    else:
        # Generic fallback
        title = market_data.get("title", "Market Update")
        return f"""📊 {truncate(title, 60)}

{truncate(market_data.get('summary', ''), 120)}

oddwons.ai"""


# =============================================================================
# IMAGE HANDLING
# =============================================================================

async def download_image(url: str) -> Optional[str]:
    """Download image from URL and save to temp file.
    
    Returns path to temp file or None if download failed.
    """
    if not url:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Determine file extension from content type or URL
            content_type = response.headers.get("content-type", "")
            if "png" in content_type or url.endswith(".png"):
                ext = ".png"
            elif "gif" in content_type or url.endswith(".gif"):
                ext = ".gif"
            elif "webp" in content_type or url.endswith(".webp"):
                ext = ".webp"
            else:
                ext = ".jpg"
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                f.write(response.content)
                return f.name
                
    except Exception as e:
        logger.warning(f"Failed to download image from {url}: {e}")
        return None


def upload_media(image_path: str) -> Optional[str]:
    """Upload image to X and return media_id.
    
    Uses X API v1.1 for media upload.
    """
    api = get_x_api_v1()
    if not api or not image_path:
        return None
    
    try:
        media = api.media_upload(filename=image_path)
        logger.info(f"Media uploaded: {media.media_id}")
        return str(media.media_id)
    except Exception as e:
        logger.error(f"Failed to upload media: {e}")
        return None
    finally:
        # Clean up temp file
        try:
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
        except:
            pass


async def upload_image_from_url(url: str) -> Optional[str]:
    """Download image from URL and upload to X.
    
    Returns media_id or None.
    """
    image_path = await download_image(url)
    if not image_path:
        return None
    
    return upload_media(image_path)


# =============================================================================
# POSTING FUNCTIONS
# =============================================================================

async def post_tweet(text: str, image_url: Optional[str] = None) -> Optional[Dict]:
    """Post a tweet to X, optionally with an image.
    
    Args:
        text: Tweet text (max 280 chars)
        image_url: Optional URL to image to attach
    """
    client = get_x_client()
    if not client:
        return None
    
    try:
        # Ensure under 280 chars
        if len(text) > 280:
            text = text[:277] + "..."
        
        # Upload image if provided
        media_ids = None
        if image_url:
            media_id = await upload_image_from_url(image_url)
            if media_id:
                media_ids = [media_id]
                logger.info(f"Attaching media {media_id} to tweet")
        
        # Post tweet
        if media_ids:
            response = client.create_tweet(text=text, media_ids=media_ids)
        else:
            response = client.create_tweet(text=text)
        
        tweet_id = response.data.get("id") if response.data else None
        logger.info(f"Tweet posted successfully: {tweet_id}")
        
        return {
            "success": True,
            "tweet_id": tweet_id,
            "text": text,
            "has_image": bool(media_ids)
        }
        
    except tweepy.TweepyException as e:
        logger.error(f"Failed to post tweet: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error posting tweet: {e}")
        return {"success": False, "error": str(e)}


async def post_thread(tweets: List[str]) -> List[Dict]:
    """Post a thread of tweets."""
    client = get_x_client()
    if not client:
        return []
    
    results = []
    previous_tweet_id = None
    
    for i, text in enumerate(tweets):
        try:
            if len(text) > 280:
                text = text[:277] + "..."
            
            if previous_tweet_id:
                response = client.create_tweet(
                    text=text,
                    in_reply_to_tweet_id=previous_tweet_id
                )
            else:
                response = client.create_tweet(text=text)
            
            tweet_id = response.data.get("id") if response.data else None
            previous_tweet_id = tweet_id
            
            results.append({
                "success": True,
                "tweet_id": tweet_id,
                "text": text,
                "position": i + 1
            })
            
        except Exception as e:
            logger.error(f"Failed to post thread tweet {i+1}: {e}")
            results.append({
                "success": False,
                "error": str(e),
                "position": i + 1
            })
            break
    
    return results


# =============================================================================
# SCHEDULED POSTING JOBS
# =============================================================================

async def post_morning_movers():
    """
    Post top market movers with AI-generated analysis.
    Scheduled: 9:00 AM EST / 14:00 UTC
    """
    from sqlalchemy import select, and_
    from app.core.database import AsyncSessionLocal
    from app.models.market import Market
    from app.models.ai_insight import AIInsight
    
    logger.info("Generating morning movers tweet with analysis...")
    
    async with AsyncSessionLocal() as session:
        try:
            yesterday = datetime.utcnow() - timedelta(hours=24)
            
            # First, try to get AI insights for movers (these have the analysis)
            insight_result = await session.execute(
                select(AIInsight)
                .where(
                    and_(
                        AIInsight.created_at >= yesterday,
                        AIInsight.recent_movement.isnot(None),
                        AIInsight.status == 'active'
                    )
                )
                .order_by(AIInsight.interest_score.desc())
                .limit(3)
            )
            insights = insight_result.scalars().all()
            
            if insights:
                # We have AI insights with analysis - use them!
                top_insight = insights[0]
                
                # Get image from associated market
                image_url = top_insight.image_url
                if not image_url and top_insight.market_id:
                    market_result = await session.execute(
                        select(Market).where(Market.id == top_insight.market_id)
                    )
                    market = market_result.scalar_one_or_none()
                    if market:
                        image_url = market.image_url
                
                # Build rich market data for AI tweet generation
                market_data = {
                    "markets": [
                        {
                            "title": i.market_title,
                            "platform": i.platform,
                            "current_odds": i.current_odds,
                            "recent_movement": i.recent_movement,
                            "movement_context": i.movement_context,  # THE ANALYSIS!
                            "analyst_note": i.analyst_note,  # MORE ANALYSIS!
                            "upcoming_catalyst": i.upcoming_catalyst,
                        }
                        for i in insights[:3]
                    ],
                    "lead_insight": {
                        "summary": top_insight.summary,
                        "movement_context": top_insight.movement_context,
                        "analyst_note": top_insight.analyst_note,
                    }
                }
                
                # Generate tweet with AI (includes analysis)
                tweet = await generate_tweet_with_ai(market_data, "morning_movers")
                
            else:
                # Fallback to raw market data
                result = await session.execute(
                    select(Market)
                    .where(
                        and_(
                            Market.updated_at >= yesterday,
                            Market.status == 'active',
                            Market.yes_price.isnot(None)
                        )
                    )
                    .order_by(Market.volume.desc())
                    .limit(5)
                )
                markets = result.scalars().all()
                
                if not markets:
                    logger.info("No markets found for morning movers")
                    return
                
                top_market = markets[0]
                image_url = top_market.image_url
                
                market_list = []
                for m in markets[:3]:
                    market_list.append({
                        "title": m.title,
                        "old_price": (m.yes_price or 0.5) * 100 - random.randint(-5, 5),
                        "new_price": (m.yes_price or 0.5) * 100,
                        "context": f"${format_volume(m.volume or 0)} volume"
                    })
                
                market_data = {"markets": market_list}
                tweet = generate_template_tweet(market_data, "morning_movers")
            
            result = await post_tweet(tweet, image_url=image_url)
            
            logger.info(f"Morning movers tweet: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to post morning movers: {e}")
            return None


async def post_platform_comparison():
    """
    Post cross-platform price differences with analytical context.
    Scheduled: 2:00 PM EST / 19:00 UTC
    """
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.market import Market
    from app.models.cross_platform_match import CrossPlatformMatch
    from app.models.ai_insight import AIInsight
    
    logger.info("Generating platform comparison tweet with analysis...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Get matches with significant price differences
            result = await session.execute(
                select(CrossPlatformMatch)
                .where(CrossPlatformMatch.price_gap_cents >= 0.03)
                .order_by(CrossPlatformMatch.price_gap_cents.desc())
                .limit(5)
            )
            matches = result.scalars().all()
            
            if not matches:
                logger.info("No significant platform gaps found")
                return
            
            match = matches[0]
            
            # Try to get AI insight for context on WHY there's a gap
            analyst_context = None
            if match.kalshi_market_id:
                insight_result = await session.execute(
                    select(AIInsight)
                    .where(AIInsight.market_id == match.kalshi_market_id)
                    .order_by(AIInsight.created_at.desc())
                    .limit(1)
                )
                insight = insight_result.scalar_one_or_none()
                if insight:
                    analyst_context = {
                        "movement_context": insight.movement_context,
                        "analyst_note": insight.analyst_note,
                        "upcoming_catalyst": insight.upcoming_catalyst,
                    }
            
            # Get image from one of the matched markets
            image_url = None
            if match.kalshi_market_id:
                market_result = await session.execute(
                    select(Market).where(Market.id == match.kalshi_market_id)
                )
                market = market_result.scalar_one_or_none()
                if market:
                    image_url = market.image_url
            
            if not image_url and match.polymarket_market_id:
                market_result = await session.execute(
                    select(Market).where(Market.id == match.polymarket_market_id)
                )
                market = market_result.scalar_one_or_none()
                if market:
                    image_url = market.image_url
            
            # Build data with analysis context
            market_data = {
                "title": match.topic or "Market",
                "kalshi_price": (match.kalshi_yes_price or 0.5) * 100,
                "polymarket_price": (match.polymarket_yes_price or 0.5) * 100,
                "price_gap_percent": match.price_gap_cents or 0,
                "analyst_context": analyst_context,  # Why might platforms disagree?
            }
            
            # Use AI to generate tweet with analysis
            tweet = await generate_tweet_with_ai(market_data, "platform_comparison")
            result = await post_tweet(tweet, image_url=image_url)
            
            logger.info(f"Platform comparison tweet: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to post platform comparison: {e}")
            return None


async def post_market_highlight():
    """
    Post a market highlight with full AI analysis - the showcase post.
    Scheduled: 6:00 PM EST / 23:00 UTC
    """
    from sqlalchemy import select, and_
    from app.core.database import AsyncSessionLocal
    from app.models.ai_insight import AIInsight
    from app.models.market import Market
    
    logger.info("Generating market highlight tweet with full analysis...")
    
    async with AsyncSessionLocal() as session:
        try:
            today = datetime.utcnow() - timedelta(hours=12)
            image_url = None
            
            # Get the BEST AI insight - this is the showcase
            result = await session.execute(
                select(AIInsight)
                .where(
                    and_(
                        AIInsight.created_at >= today,
                        AIInsight.status == 'active',
                        AIInsight.analyst_note.isnot(None)  # Must have analysis
                    )
                )
                .order_by(AIInsight.interest_score.desc())
                .limit(1)
            )
            insight = result.scalar_one_or_none()
            
            if insight:
                # Get image from the associated market
                image_url = insight.image_url
                if not image_url and insight.market_id:
                    market_result = await session.execute(
                        select(Market).where(Market.id == insight.market_id)
                    )
                    market = market_result.scalar_one_or_none()
                    if market:
                        image_url = market.image_url
                
                # Build RICH data with all the analysis
                market_data = {
                    "title": insight.market_title,
                    "platform": insight.platform,
                    "category": insight.category,
                    "current_odds": insight.current_odds,
                    "implied_probability": insight.implied_probability,
                    "summary": insight.summary,  # What this market is about
                    "recent_movement": insight.recent_movement,
                    "movement_context": insight.movement_context,  # WHY it moved
                    "analyst_note": insight.analyst_note,  # Expert context
                    "upcoming_catalyst": insight.upcoming_catalyst,  # What's coming
                    "volume_note": insight.volume_note,
                    # Teaser for the platform
                    "teaser": "Full analysis + source links on OddWons"
                }
                
                # Generate tweet with AI (full analysis showcase)
                tweet = await generate_tweet_with_ai(market_data, "market_highlight")
                
            else:
                # Fallback to top market by volume
                result = await session.execute(
                    select(Market)
                    .where(Market.status == 'active')
                    .order_by(Market.volume.desc())
                    .limit(1)
                )
                market = result.scalar_one_or_none()
                
                if not market:
                    logger.info("No markets for highlight")
                    return
                
                image_url = market.image_url
                
                market_data = {
                    "title": market.title,
                    "platform": market.platform,
                    "yes_price": market.yes_price or 0.5,
                    "volume_24h": market.volume or 0,
                    "summary": f"High activity market on {market.platform}",
                }
                tweet = generate_template_tweet(market_data, "market_highlight")
            
            result = await post_tweet(tweet, image_url=image_url)
            
            logger.info(f"Market highlight tweet: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to post market highlight: {e}")
            return None


async def post_weekly_recap():
    """
    Post weekly market recap thread.
    Scheduled: Sunday 10:00 AM EST / 15:00 UTC
    """
    from sqlalchemy import select, func
    from app.core.database import AsyncSessionLocal
    from app.models.market import Market
    from app.models.cross_platform_match import CrossPlatformMatch
    
    logger.info("Generating weekly recap thread...")
    
    async with AsyncSessionLocal() as session:
        try:
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            # Get stats
            market_result = await session.execute(
                select(
                    func.count(Market.id).label("total"),
                    func.sum(Market.volume).label("volume")
                ).where(Market.updated_at >= week_ago)
            )
            stats = market_result.first()
            
            # Get match count
            match_result = await session.execute(
                select(func.count(CrossPlatformMatch.id))
                .where(CrossPlatformMatch.created_at >= week_ago)
            )
            match_count = match_result.scalar() or 0
            
            # Get top markets
            top_result = await session.execute(
                select(Market)
                .where(Market.updated_at >= week_ago)
                .order_by(Market.volume.desc())
                .limit(3)
            )
            top_markets = top_result.scalars().all()
            
            # Build thread
            tweet_1 = TEMPLATES["weekly_recap_1"].format(
                total_markets=f"{stats.total or 0:,}",
                volume=format_volume(stats.volume or 0),
                matches=match_count,
                movers=min(stats.total or 0, 50),
                categories="🏛️ Politics │ 🏈 Sports │ 💰 Crypto"
            )
            
            top_1 = truncate(top_markets[0].title, 35) if len(top_markets) > 0 else "N/A"
            top_2 = truncate(top_markets[1].title, 35) if len(top_markets) > 1 else "N/A"
            top_3 = truncate(top_markets[2].title, 35) if len(top_markets) > 2 else "N/A"
            
            tweet_2 = TEMPLATES["weekly_recap_2"].format(
                top_1=top_1,
                top_2=top_2,
                top_3=top_3
            )
            
            results = await post_thread([tweet_1, tweet_2])
            logger.info(f"Weekly recap thread: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to post weekly recap: {e}")
            return None


async def post_daily_stats():
    """
    Post daily platform statistics.
    Can be called ad-hoc or scheduled.
    """
    from sqlalchemy import select, func
    from app.core.database import AsyncSessionLocal
    from app.models.market import Market
    from app.models.cross_platform_match import CrossPlatformMatch
    
    logger.info("Generating daily stats tweet...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Count by platform
            kalshi_result = await session.execute(
                select(func.count(Market.id))
                .where(Market.platform == 'kalshi')
            )
            kalshi_count = kalshi_result.scalar() or 0
            
            poly_result = await session.execute(
                select(func.count(Market.id))
                .where(Market.platform == 'polymarket')
            )
            poly_count = poly_result.scalar() or 0
            
            # Total volume
            volume_result = await session.execute(
                select(func.sum(Market.volume))
            )
            total_volume = volume_result.scalar() or 0
            
            # Match count
            match_result = await session.execute(
                select(func.count(CrossPlatformMatch.id))
            )
            match_count = match_result.scalar() or 0
            
            market_data = {
                "total_markets": kalshi_count + poly_count,
                "kalshi_count": kalshi_count,
                "poly_count": poly_count,
                "total_volume": total_volume,
                "matches": match_count,
            }
            
            tweet = generate_template_tweet(market_data, "daily_stat")
            result = await post_tweet(tweet)
            
            logger.info(f"Daily stats tweet: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to post daily stats: {e}")
            return None


async def post_promo():
    """
    Post daily promo tweet with logo.
    Static content highlighting what users can do on OddWons.
    Scheduled: 7:00 PM EST / 00:00 UTC
    """
    logger.info("Posting daily promo tweet...")

    # Static promo text - rotates through different messages
    promo_messages = [
        """what we do at OddWons 👇

📊 Track 70k+ prediction markets
⚖️ Compare Kalshi vs Polymarket odds
🔍 AI-powered market analysis
📈 Price movement alerts
🎯 Cross-platform price gaps

your research companion for prediction markets

oddwons.ai

#OddWons #PredictionMarkets #Polymarket #Kalshi""",

        """prediction markets, simplified 🎯

we track the markets so you don't have to:

├ Real-time odds from Kalshi + Polymarket
├ AI highlights on what's moving
├ Cross-platform comparisons
└ Daily briefings

oddwons.ai

#OddWons #PredictionMarkets #Polymarket #Kalshi""",

        """tired of checking multiple platforms?

OddWons brings it all together:

📊 70k+ markets tracked
🔄 Kalshi + Polymarket side-by-side
🤖 AI explains what's happening
📱 One dashboard, all the data

oddwons.ai

#OddWons #PredictionMarkets #Polymarket #Kalshi""",

        """your daily prediction market briefing 📰

├ Top movers
├ Platform price gaps
├ AI analysis
├ Key dates & catalysts
└ Volume trends

all in one place

oddwons.ai

#OddWons #PredictionMarkets #Polymarket #Kalshi""",

        """why check 2 platforms when you can check 1? 🤔

OddWons aggregates:
• Kalshi odds
• Polymarket odds
• Price gaps between them
• AI-powered context

the smarter way to research prediction markets

oddwons.ai

#OddWons #PredictionMarkets #Polymarket #Kalshi""",
    ]

    # Pick a random promo message
    import random
    promo_text = random.choice(promo_messages)

    # Logo URL - update this to your actual logo URL
    logo_url = os.getenv("ODDWONS_LOGO_URL", "https://oddwons.ai/oddwons-logo.png")

    try:
        result = await post_tweet(promo_text, image_url=logo_url)
        logger.info(f"Promo tweet posted: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to post promo: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# CATEGORY SPOTLIGHT POSTS
# =============================================================================

async def post_category_spotlight(category: str):
    """
    Post a spotlight on a specific market category.
    Shows top markets and interesting activity in that category.
    """
    from sqlalchemy import select, func
    from app.core.database import AsyncSessionLocal
    from app.models.market import Market

    logger.info(f"Generating {category} spotlight tweet...")

    category_hashtags = {
        "crypto": "#Crypto #Bitcoin #Ethereum",
        "politics": "#Politics #Elections #Trump",
        "sports": "#Sports #NFL #NBA #Betting",
        "finance": "#Finance #Stocks #Economy",
        "entertainment": "#Entertainment #Movies #Celebrities",
    }

    category_emojis = {
        "crypto": "🪙",
        "politics": "🏛️",
        "sports": "🏈",
        "finance": "📈",
        "entertainment": "🎬",
    }

    async with AsyncSessionLocal() as session:
        try:
            # Get top markets in this category by volume
            result = await session.execute(
                select(Market)
                .where(
                    Market.category.ilike(f"%{category}%"),
                    Market.status == 'active',
                    Market.yes_price.isnot(None)
                )
                .order_by(Market.volume.desc())
                .limit(3)
            )
            markets = result.scalars().all()

            if not markets:
                logger.info(f"No {category} markets found for spotlight")
                return None

            emoji = category_emojis.get(category, "📊")
            extra_hashtags = category_hashtags.get(category, "")

            # Build tweet
            lines = [f"{emoji} {category.upper()} SPOTLIGHT\n"]
            lines.append("what's moving rn:\n")

            for i, m in enumerate(markets[:3], 1):
                price_pct = int((m.yes_price or 0.5) * 100)
                title_short = m.title[:40] + "..." if len(m.title) > 40 else m.title
                lines.append(f"{i}. {title_short}")
                lines.append(f"   └ {price_pct}% yes\n")

            lines.append("\nfull analysis → oddwons.ai")
            lines.append(f"\n#OddWons #PredictionMarkets #Polymarket #Kalshi {extra_hashtags}")

            tweet = "".join(lines)

            # Ensure under 280 chars
            if len(tweet) > 280:
                tweet = tweet[:277] + "..."

            result = await post_tweet(tweet)
            logger.info(f"{category} spotlight posted: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to post {category} spotlight: {e}")
            return None


async def post_spotlight_crypto():
    """Post crypto category spotlight."""
    return await post_category_spotlight("crypto")


async def post_spotlight_politics():
    """Post politics category spotlight."""
    return await post_category_spotlight("politics")


async def post_spotlight_sports():
    """Post sports category spotlight."""
    return await post_category_spotlight("sports")


async def post_spotlight_finance():
    """Post finance category spotlight."""
    return await post_category_spotlight("finance")


async def post_spotlight_entertainment():
    """Post entertainment category spotlight."""
    return await post_category_spotlight("entertainment")


# =============================================================================
# DAILY POLL
# =============================================================================

async def post_poll():
    """
    Post an engagement poll about prediction markets.
    Note: X API free tier doesn't support creating polls programmatically,
    so we post a "soft poll" asking people to reply/like.
    """
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.market import Market

    logger.info("Generating daily poll tweet...")

    poll_templates = [
        {
            "question": "which platform do you trust more for odds?",
            "options": ["🅰️ Kalshi (regulated)", "🅱️ Polymarket (crypto)"],
            "cta": "reply with A or B 👇"
        },
        {
            "question": "what category are you watching most rn?",
            "options": ["🏛️ Politics", "🪙 Crypto", "🏈 Sports", "📈 Finance"],
            "cta": "drop your pick below 👇"
        },
        {
            "question": "when a market moves 10%+ overnight...",
            "options": ["📈 usually overreaction", "📉 usually correct"],
            "cta": "what's your take? 👇"
        },
        {
            "question": "how often do you check prediction markets?",
            "options": ["👀 multiple times/day", "📅 once a day", "📆 few times/week"],
            "cta": "be honest 👇"
        },
        {
            "question": "biggest edge in prediction markets?",
            "options": ["🔍 research", "⚡ speed", "🧠 contrarian thinking", "📊 data"],
            "cta": "what's your strategy? 👇"
        },
    ]

    import random
    poll = random.choice(poll_templates)

    lines = [f"quick poll 🗳️\n\n{poll['question']}\n"]
    for opt in poll["options"]:
        lines.append(f"\n{opt}")
    lines.append(f"\n\n{poll['cta']}")
    lines.append("\n\n#OddWons #PredictionMarkets #Polymarket #Kalshi")

    tweet = "".join(lines)

    try:
        result = await post_tweet(tweet)
        logger.info(f"Poll tweet posted: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to post poll: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# LATE NIGHT POSTS (Gambling Audience)
# =============================================================================

async def post_latenight_sports():
    """
    Late night sports post targeting gambling audience.
    Focus on upcoming games, spreads, over/unders.
    """
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.market import Market

    logger.info("Generating late night sports tweet...")

    async with AsyncSessionLocal() as session:
        try:
            # Get top sports markets
            result = await session.execute(
                select(Market)
                .where(
                    Market.category.ilike("%sport%"),
                    Market.status == 'active',
                    Market.yes_price.isnot(None)
                )
                .order_by(Market.volume.desc())
                .limit(2)
            )
            markets = result.scalars().all()

            if not markets:
                # Fallback generic sports tweet
                tweet = """🏈 late night sports check

prediction markets never sleep

who else is up tracking odds rn? 👀

oddwons.ai

#OddWons #PredictionMarkets #Polymarket #Kalshi #SportsBetting"""
            else:
                lines = ["🌙 late night sports update\n"]
                for m in markets:
                    price_pct = int((m.yes_price or 0.5) * 100)
                    title_short = m.title[:35] + "..." if len(m.title) > 35 else m.title
                    lines.append(f"\n{title_short}")
                    lines.append(f"└ {price_pct}% odds")

                lines.append("\n\ncan't sleep, might as well research")
                lines.append("\noddwons.ai")
                lines.append("\n\n#OddWons #PredictionMarkets #Polymarket #Kalshi #SportsBetting")
                tweet = "".join(lines)

            if len(tweet) > 280:
                tweet = tweet[:277] + "..."

            result = await post_tweet(tweet)
            logger.info(f"Late night sports posted: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to post late night sports: {e}")
            return None


async def post_latenight_crypto():
    """
    Late night crypto post - crypto never sleeps.
    """
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.market import Market

    logger.info("Generating late night crypto tweet...")

    async with AsyncSessionLocal() as session:
        try:
            # Get top crypto markets
            result = await session.execute(
                select(Market)
                .where(
                    Market.category.ilike("%crypto%"),
                    Market.status == 'active',
                    Market.yes_price.isnot(None)
                )
                .order_by(Market.volume.desc())
                .limit(2)
            )
            markets = result.scalars().all()

            if not markets:
                tweet = """🪙 crypto markets don't sleep

and neither do we apparently

what's your midnight thesis? 👇

oddwons.ai

#OddWons #PredictionMarkets #Polymarket #Kalshi #Crypto #Bitcoin"""
            else:
                lines = ["🌙 midnight crypto check\n"]
                for m in markets:
                    price_pct = int((m.yes_price or 0.5) * 100)
                    title_short = m.title[:35] + "..." if len(m.title) > 35 else m.title
                    lines.append(f"\n{title_short}")
                    lines.append(f"└ {price_pct}%")

                lines.append("\n\n24/7 markets, 24/7 tracking")
                lines.append("\noddwons.ai")
                lines.append("\n\n#OddWons #PredictionMarkets #Polymarket #Kalshi #Crypto")
                tweet = "".join(lines)

            if len(tweet) > 280:
                tweet = tweet[:277] + "..."

            result = await post_tweet(tweet)
            logger.info(f"Late night crypto posted: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to post late night crypto: {e}")
            return None


async def post_latenight_action():
    """
    Late night high-action markets post.
    Mix of sports + crypto for the degens still up.
    """
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.market import Market
    from app.models.cross_platform_match import CrossPlatformMatch

    logger.info("Generating late night action tweet...")

    async with AsyncSessionLocal() as session:
        try:
            # Get biggest cross-platform gap
            match_result = await session.execute(
                select(CrossPlatformMatch)
                .order_by(CrossPlatformMatch.price_gap_cents.desc())
                .limit(1)
            )
            match = match_result.scalar_one_or_none()

            if match and match.price_gap_cents and match.price_gap_cents >= 2:
                tweet = f"""🌙 1 AM market check

{match.topic[:40]}...

Kalshi: {int(match.kalshi_yes_price or 0)}%
Poly:   {int(match.polymarket_yes_price or 0)}%

{int(match.price_gap_cents)}% gap at 1am... interesting 👀

oddwons.ai

#OddWons #PredictionMarkets #Polymarket #Kalshi"""
            else:
                tweet = """🌙 still up tracking markets?

same

late night is when the real ones do their research

oddwons.ai

#OddWons #PredictionMarkets #Polymarket #Kalshi"""

            if len(tweet) > 280:
                tweet = tweet[:277] + "..."

            result = await post_tweet(tweet)
            logger.info(f"Late night action posted: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to post late night action: {e}")
            return None


# =============================================================================
# MAIN POSTING ORCHESTRATOR
# =============================================================================

async def run_scheduled_posts(post_type: str = "all"):
    """
    Run scheduled X posts with bot check and DB tracking.

    Args:
        post_type: "morning", "afternoon", "evening", "weekly", "stats", "promo", or "all"
    """
    results = {}

    # Check master bot switch first
    if not await is_bot_enabled():
        logger.info("X bot is disabled - skipping all posts")
        return {"skipped": True, "reason": "bot_disabled"}

    # Map post types to their functions and settings keys
    post_config = {
        "morning": ("morning_movers", post_morning_movers),
        "afternoon": ("platform_comparison", post_platform_comparison),
        "evening": ("market_highlight", post_market_highlight),
        "weekly": ("weekly_recap", post_weekly_recap),
        "stats": ("daily_stats", post_daily_stats),
    }

    async def run_and_save(key: str, func, settings_key: str):
        """Run a posting function and save the result."""
        # Check if this specific post type is enabled
        if not await is_bot_enabled(settings_key):
            logger.info(f"Skipping {key} - disabled in settings")
            return {"skipped": True, "reason": f"{settings_key}_disabled"}

        # Run the posting function
        result = await func()

        # Save to database
        if result:
            content = result.get("text", "") if isinstance(result, dict) else ""
            # For threads (weekly recap), content might be different
            if isinstance(result, list) and result:
                content = result[0].get("text", "") if isinstance(result[0], dict) else ""

            await save_x_post(
                post_type=key,
                content=content,
                tweet_result=result if isinstance(result, dict) else (result[0] if result else None),
            )

        return result

    if post_type in ["morning", "all"]:
        results["morning_movers"] = await run_and_save(
            "morning_movers", post_morning_movers, "morning_movers"
        )

    if post_type in ["afternoon", "all"]:
        results["platform_comparison"] = await run_and_save(
            "platform_comparison", post_platform_comparison, "platform_comparison"
        )

    if post_type in ["evening", "all"]:
        results["market_highlight"] = await run_and_save(
            "market_highlight", post_market_highlight, "market_highlight"
        )

    if post_type == "weekly":
        results["weekly_recap"] = await run_and_save(
            "weekly_recap", post_weekly_recap, "weekly_recap"
        )

    if post_type == "stats":
        results["daily_stats"] = await run_and_save(
            "daily_stats", post_daily_stats, "daily_stats"
        )

    if post_type == "promo":
        results["promo"] = await run_and_save(
            "promo", post_promo, "promo"
        )

    # Category Spotlights
    if post_type == "spotlight_crypto":
        results["spotlight_crypto"] = await run_and_save(
            "spotlight_crypto", post_spotlight_crypto, "morning_movers"  # Use existing toggle
        )

    if post_type == "spotlight_politics":
        results["spotlight_politics"] = await run_and_save(
            "spotlight_politics", post_spotlight_politics, "morning_movers"
        )

    if post_type == "spotlight_sports":
        results["spotlight_sports"] = await run_and_save(
            "spotlight_sports", post_spotlight_sports, "morning_movers"
        )

    if post_type == "spotlight_finance":
        results["spotlight_finance"] = await run_and_save(
            "spotlight_finance", post_spotlight_finance, "morning_movers"
        )

    if post_type == "spotlight_entertainment":
        results["spotlight_entertainment"] = await run_and_save(
            "spotlight_entertainment", post_spotlight_entertainment, "morning_movers"
        )

    # Daily Poll
    if post_type == "poll":
        results["poll"] = await run_and_save(
            "poll", post_poll, "morning_movers"  # Use existing toggle
        )

    # Late Night Posts
    if post_type == "latenight_sports":
        results["latenight_sports"] = await run_and_save(
            "latenight_sports", post_latenight_sports, "morning_movers"
        )

    if post_type == "latenight_crypto":
        results["latenight_crypto"] = await run_and_save(
            "latenight_crypto", post_latenight_crypto, "morning_movers"
        )

    if post_type == "latenight_action":
        results["latenight_action"] = await run_and_save(
            "latenight_action", post_latenight_action, "morning_movers"
        )

    logger.info(f"Scheduled posts complete: {post_type} -> {results}")
    return results


# =============================================================================
# TEST FUNCTION
# =============================================================================

async def test_x_connection() -> Dict:
    """Test X API connection without posting."""
    client = get_x_client()
    
    if not client:
        return {"success": False, "error": "X client not configured"}
    
    try:
        # Verify credentials by getting authenticated user
        me = client.get_me()
        if me.data:
            return {
                "success": True,
                "username": me.data.username,
                "name": me.data.name,
                "id": me.data.id
            }
        return {"success": False, "error": "Could not fetch user data"}
    except Exception as e:
        return {"success": False, "error": str(e)}
