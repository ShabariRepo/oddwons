# Claude Code Instructions - Gemini + Groq Pipeline

## SUMMARY FOR CLAUDE CODE

Implement a two-stage AI analysis pipeline:
1. **Gemini** (free web search) → fetches real news for each category
2. **Groq** (cheap inference) → analyzes markets WITH real news context + bro personality

The AI should provide ACTUAL INSIGHTS (historical context, contrarian angles, value perspectives) not just restate numbers.

---

## PREREQUISITE FIX: Filter Resolved Markets

Before implementing the pipeline, ensure `load_market_data()` in `app/services/patterns/engine.py` has price filters:

```python
result = await session.execute(
    select(Market)
    .where(Market.status == "active")
    .where(Market.volume >= min_volume)
    .where(Market.yes_price > 0.02)   # Filter out resolved (0%)
    .where(Market.yes_price < 0.98)   # Filter out resolved (100%)
    .order_by(Market.volume.desc().nullslast())
    .limit(limit)
)
```

This prevents generating insights for already-decided markets.

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│  Market Data (by category)                                      │
│  - politics: 500 markets                                        │
│  - sports: 800 markets                                          │
│  - crypto: 200 markets                                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  GEMINI 2.0 Flash-Lite (FREE - 1,500 searches/day)              │
│  - Search recent news for each category                         │
│  - Returns: headlines, key events, category summary             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  GROQ (cheap/fast inference)                                    │
│  - Receives: market data + real news context                    │
│  - Analyzes with bro personality + actual insights              │
│  - Returns: highlights with historical context, angles, catalysts│
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  AI Insights (saved to database)                                │
│  - Real news-informed analysis                                  │
│  - Bro tone: "yo", "spicy", "no cap", etc.                     │
│  - Actual value: contrarian angles, hedge ideas, catalysts      │
└─────────────────────────────────────────────────────────────────┘
```

---

## API KEYS

**File: `keys.txt`** (already created, gitignored)
```
GEMINI_API_KEY=AIzaSyBzzBW46f9sMRDc66rihVTVYzJY-O75tcc
```

**Also add to `.env`:**
```
GEMINI_API_KEY=AIzaSyBzzBW46f9sMRDc66rihVTVYzJY-O75tcc
```

---

## STEP 1: Install Dependencies

```bash
pip install google-generativeai
echo "google-generativeai" >> requirements.txt
```

---

## STEP 2: Create Gemini Search Service

**Create file: `app/services/gemini_search.py`**

```python
"""
Gemini Web Search Service.
Uses Gemini 2.0 Flash-Lite with Google Search grounding to fetch real news context.
FREE: 1,500 grounded searches per day.
"""
import os
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Will be imported after install
genai = None

def _get_genai():
    """Lazy import of google.generativeai."""
    global genai
    if genai is None:
        try:
            import google.generativeai as _genai
            genai = _genai
        except ImportError:
            logger.error("google-generativeai not installed. Run: pip install google-generativeai")
            return None
    return genai


def _configure_gemini() -> bool:
    """Configure Gemini with API key from environment or keys.txt."""
    _genai = _get_genai()
    if _genai is None:
        return False
    
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        # Try loading from keys.txt
        try:
            keys_path = os.path.join(os.path.dirname(__file__), '..', '..', 'keys.txt')
            with open(keys_path, "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.strip().split("=", 1)[1]
                        break
        except FileNotFoundError:
            pass
    
    if not api_key:
        logger.warning("GEMINI_API_KEY not found in environment or keys.txt")
        return False
    
    _genai.configure(api_key=api_key)
    return True


async def search_category_news(category: str, market_titles: List[str]) -> Dict:
    """
    Search for recent news related to a market category using Gemini with Google Search.
    
    Args:
        category: Category name (politics, sports, crypto, finance, tech, etc.)
        market_titles: List of market titles for context
        
    Returns:
        Dict with headlines, key_events, category_summary
    """
    if not _configure_gemini():
        return {
            "error": "Gemini not configured",
            "headlines": [],
            "key_events": [],
            "category_summary": ""
        }
    
    _genai = _get_genai()
    
    # Use top 5 market titles for focused search
    top_markets = market_titles[:5]
    markets_context = "\n".join(f"- {t}" for t in top_markets)
    
    prompt = f"""Search for the most recent news (last 7 days) relevant to these {category} prediction markets:

{markets_context}

Return ONLY a JSON object (no markdown, no explanation):
{{
    "headlines": [
        {{"title": "headline text", "source": "news source", "date": "date", "relevance": "which market this relates to"}}
    ],
    "key_events": [
        {{"event": "what happened", "date": "when", "impact": "how this affects the markets"}}
    ],
    "category_summary": "2-3 sentence overview of the current {category} landscape"
}}

Focus on facts that would move prediction market prices. Be concise.
"""
    
    try:
        model = _genai.GenerativeModel('gemini-2.0-flash-lite')
        
        response = model.generate_content(
            prompt,
            tools='google_search_retrieval'
        )
        
        # Parse response - handle various formats
        text = response.text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        result = json.loads(text)
        logger.info(f"Gemini search for {category}: {len(result.get('headlines', []))} headlines found")
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response for {category}: {e}")
        return {
            "error": f"JSON parse error: {e}",
            "headlines": [],
            "key_events": [],
            "category_summary": ""
        }
    except Exception as e:
        logger.error(f"Gemini search failed for {category}: {e}")
        return {
            "error": str(e),
            "headlines": [],
            "key_events": [],
            "category_summary": ""
        }


async def search_market_news(market_title: str) -> Dict:
    """
    Search for news about a specific market. Use sparingly - prefer batch category searches.
    """
    if not _configure_gemini():
        return {"error": "Gemini not configured", "headlines": []}
    
    _genai = _get_genai()
    
    prompt = f"""Search for recent news (last 7 days) about: {market_title}

Return ONLY a JSON object:
{{
    "headlines": [{{"title": "...", "source": "...", "date": "..."}}],
    "current_status": "brief current situation",
    "upcoming_events": ["event 1", "event 2"]
}}
"""
    
    try:
        model = _genai.GenerativeModel('gemini-2.0-flash-lite')
        response = model.generate_content(prompt, tools='google_search_retrieval')
        
        text = response.text.strip()
        if "```" in text:
            text = text.split("```")[1] if "```json" not in text else text.split("```json")[1]
            text = text.split("```")[0]
        
        return json.loads(text.strip())
        
    except Exception as e:
        logger.error(f"Gemini market search failed: {e}")
        return {"error": str(e), "headlines": []}
```

---

## STEP 3: Update AI Agent

**Edit file: `app/services/ai_agent.py`**

Add this import at top:
```python
from app.services.gemini_search import search_category_news
```

Update `analyze_category_batch` method to accept and use news context:

```python
async def analyze_category_batch(
    self,
    category: str,
    markets: List[Dict[str, Any]],
    patterns: List[Dict[str, Any]] = None,
    news_context: Dict[str, Any] = None  # NEW PARAMETER
) -> Dict[str, Any]:
    """
    Analyze markets in a category with real news context.
    """
    if not self.is_enabled():
        return {"highlights": [], "error": "AI not enabled"}
    
    # Build news section from Gemini results
    news_section = ""
    if news_context:
        if news_context.get("headlines"):
            headlines = news_context["headlines"][:5]
            news_section = "RECENT NEWS (from web search):\n" + "\n".join(
                f"- {h.get('title', '')} ({h.get('source', '')}, {h.get('date', '')})"
                for h in headlines
            )
        
        if news_context.get("category_summary"):
            news_section += f"\n\nCURRENT LANDSCAPE: {news_context['category_summary']}"
        
        if news_context.get("key_events"):
            events = news_context["key_events"][:3]
            news_section += "\n\nKEY RECENT EVENTS:\n" + "\n".join(
                f"- {e.get('event', '')} ({e.get('date', '')}): {e.get('impact', '')}"
                for e in events
            )
    
    # Build the prompt with bro personality + actual insights requirement
    prompt = self._build_analysis_prompt(category, markets, news_section)
    
    # Call Groq
    return await self._call_groq_analysis(prompt, category)


def _build_analysis_prompt(self, category: str, markets: List[Dict], news_section: str) -> str:
    """Build the analysis prompt with bro personality and insight requirements."""
    
    markets_json = json.dumps(markets[:20], indent=2, default=str)
    
    return f"""You are a prediction market analyst for oddwons.ai - but you're also a chill bro who makes finance fun AND drops actual insights.

YOUR PERSONALITY:
- Smart friend who's really into prediction markets
- Knows historical context and spots interesting angles
- Casual and engaging: use "yo", "lowkey", "no cap", "spicy", "wild", "fam" naturally
- NOT a formal analyst - more like explaining to a friend over beers

CRITICAL - PROVIDE REAL INSIGHT:
Don't just restate the numbers. For each market provide:
- Historical context ("Fed's cut 3 times in a row")
- Trend analysis ("when they start cutting, they usually keep going")  
- Contrarian angles ("market might be underpricing this because...")
- Value perspective ("at 36% this could be interesting if you think...")
- Hedge ideas ("decent hedge play if you're worried about...")
- What would make this move (specific catalysts with dates)

NOT FINANCIAL ADVICE - just sharing perspectives like a smart friend would.

CATEGORY: {category}

{news_section if news_section else "No recent news available - analyze based on market data."}

MARKETS TO ANALYZE:
{markets_json}

RESPONSE FORMAT - Return valid JSON:
{{
    "highlights": [
        {{
            "market_id": "the market id",
            "market_title": "market title",
            "platform": "kalshi or polymarket",
            "summary": "1-2 sentence bro-style summary of what this market is",
            "current_odds": {{"yes": 0.36, "no": 0.64}},
            "implied_probability": "36% chance of X happening",
            "volume_note": "High volume" or "Low liquidity" etc,
            "recent_movement": "+5% in 24h" or "Stable" etc,
            "movement_context": "WHY it moved - reference actual news",
            "upcoming_catalyst": "Specific event + date that could move this",
            "analyst_note": "YOUR ACTUAL INSIGHT - historical context, contrarian angle, value perspective, hedge idea. This is the money shot - make it good. 2-4 sentences, bro tone."
        }}
    ],
    "category_summary": "2-3 sentence bro-style overview of this category right now"
}}

TONE EXAMPLES:

❌ BAD (boring, just restating):
"Market shows 36% probability of a rate cut. The Fed meeting is approaching."

✅ GOOD (actual insight + bro vibes):
"Yo this Fed cut market at 36% is lowkey interesting 👀 The Fed's been on a cutting streak - they've dropped rates 3 times in a row now. Market seems to be pricing in a pause, but historically when they start cutting they keep going until something breaks. At 36% this could be decent value as a hedge if you think the trend continues. CPI data next week is the catalyst to watch - hot print = this dumps, cool print = could rip to 50%+. Just saying fam 📊"

❌ BAD:
"Trump leads in polls with 62% probability."

✅ GOOD:
"Trump sitting at 62% but here's what's spicy - his numbers historically dip right before debates then recover after. If you think he'll do well, buying before the Jan 15 debate could be the move. Or if you're bearish, that's your window to fade. Either way, expect volatility around that date 📈"

Now analyze these {category} markets and give me those insights:"""
```

---

## STEP 4: Update Pattern Engine

**Edit file: `app/services/patterns/engine.py`**

Update the `run_ai_analysis` method:

```python
async def run_ai_analysis(
    self,
    patterns: List[PatternResult],
    markets: List[MarketData],
    session: AsyncSession
) -> int:
    """
    Run AI analysis on markets, grouped by category.
    NOW WITH GEMINI WEB SEARCH for real news context.
    """
    if not ai_agent.is_enabled():
        logger.warning("AI agent not enabled - skipping AI analysis")
        return 0

    saved = 0

    # Group markets by category
    market_by_category: Dict[str, List[Dict[str, Any]]] = {}
    
    for market in markets:
        category = self._infer_category(market.title or "")
        if category not in market_by_category:
            market_by_category[category] = []

        market_by_category[category].append({
            "market_id": market.market_id,
            "platform": market.platform,
            "title": market.title,
            "yes_price": market.yes_price,
            "no_price": market.no_price,
            "volume": market.volume,
            "price_history": market.price_history[-5:] if market.price_history else [],
        })

    # NEW: Fetch news context for each category via Gemini
    from app.services.gemini_search import search_category_news
    
    category_news: Dict[str, Dict] = {}
    for category, cat_markets in market_by_category.items():
        if len(cat_markets) >= 3:  # Only search for categories with enough markets
            titles = [m["title"] for m in cat_markets[:10]]
            logger.info(f"🔍 Fetching news context for {category} via Gemini...")
            try:
                category_news[category] = await search_category_news(category, titles)
                headlines_count = len(category_news[category].get("headlines", []))
                logger.info(f"✅ Got {headlines_count} headlines for {category}")
            except Exception as e:
                logger.error(f"❌ Gemini search failed for {category}: {e}")
                category_news[category] = {}

    # Analyze each category with news context
    for category, category_markets in market_by_category.items():
        if len(category_markets) < 3:
            continue

        try:
            logger.info(f"🤖 Analyzing {category}: {len(category_markets)} markets")
            
            # Pass news context to AI agent
            news = category_news.get(category, {})
            
            result = await ai_agent.analyze_category_batch(
                category=category,
                markets=category_markets,
                patterns=[],  # Can add pattern context if needed
                news_context=news  # NEW: Real news from Gemini
            )

            # Save highlights
            if result and result.get("highlights"):
                for highlight in result["highlights"]:
                    await self.save_market_highlight(highlight, category, session)
                    saved += 1
                    
            logger.info(f"✅ {category}: {len(result.get('highlights', []))} insights generated")

        except Exception as e:
            logger.error(f"❌ Category analysis failed for {category}: {e}")

    await session.commit()
    logger.info(f"🎉 AI analysis complete: {saved} insights saved")
    return saved
```

---

## STEP 5: Clear Old Insights & Test

```bash
# 1. Add Gemini key to .env
echo "GEMINI_API_KEY=AIzaSyBzzBW46f9sMRDc66rihVTVYzJY-O75tcc" >> .env

# 2. Clear old stale insights
psql -d oddwons -c "DELETE FROM ai_insights;"

# 3. Run analysis with new pipeline
cd ~/Desktop/code/oddwons
source venv/bin/activate
set -a && source .env && set +a
python run_analysis.py

# 4. Check new insights have bro vibes
psql -d oddwons -c "SELECT market_title, analyst_note FROM ai_insights LIMIT 5;"
```

---

## EXPECTED OUTPUT

**Before (blind + boring):**
> "Market shows 36% probability of a rate cut. The Fed meeting is approaching."

**After (informed + bro + actual insight):**
> "Yo this Fed cut market at 36% is lowkey interesting 👀 The Fed's been on a cutting streak - they've dropped rates 3 times in a row now. Market seems to be pricing in a pause, but historically when they start cutting they keep going until something breaks. At 36% this could be decent value as a hedge if you think the trend continues. CPI data drops next week and that's gonna be the big mover - hot CPI = this dumps, cool CPI = could rip to 50%+. Something to watch fam 📊"

---

## FILES CHECKLIST

- [ ] `app/services/gemini_search.py` - CREATE (Gemini web search service)
- [ ] `app/services/ai_agent.py` - EDIT (add news_context param, bro prompt)
- [ ] `app/services/patterns/engine.py` - EDIT (fetch news before analysis)
- [ ] `requirements.txt` - ADD `google-generativeai`
- [ ] `.env` - ADD `GEMINI_API_KEY`
- [ ] Verify `load_market_data()` has price filters (0.02 < yes_price < 0.98)

---

## COST

| Component | Cost |
|-----------|------|
| Gemini searches (9 categories) | FREE (under 1,500/day) |
| Groq inference | ~$0.02/run |
| **Total per analysis** | **~$0.02** |

---

# FEATURE: Clickable Market/Insight Cards → Detail Page

## THE PROBLEM

Currently market cards and insight cards are NOT clickable. Users can't:
- See the full research behind an insight
- View source articles (the "homework")
- Understand WHY the AI said what it said
- Verify the analysis themselves

## THE SOLUTION

Make every card clickable → opens a detail page with:
1. **Full Market Info** - title, prices on both platforms, volume, status
2. **AI Analysis** - the full insight with bro vibes
3. **Source Articles** - links to news articles Gemini found (show the homework)
4. **Price History** - chart showing movement
5. **Key Catalysts** - upcoming events that could move this
6. **Cross-Platform Comparison** - if exists on both Kalshi & Polymarket

## IMPLEMENTATION

### Step 1: Store Source Links in AI Insights

Update `AIInsight` model to store news sources:

**Edit `app/models/ai_insight.py`:**
```python
class AIInsight(Base):
    __tablename__ = "ai_insights"
    
    # ... existing fields ...
    
    # NEW: Store source articles from Gemini search
    source_articles = Column(JSONB, nullable=True)  # [{"title": "", "url": "", "source": "", "date": ""}]
    news_context = Column(JSONB, nullable=True)     # Full Gemini response for transparency
```

**Run migration:**
```bash
alembic revision --autogenerate -m "add source_articles to ai_insights"
alembic upgrade head
```

### Step 2: Save Sources When Generating Insights

**In `app/services/patterns/engine.py` `save_market_highlight()`:**
```python
async def save_market_highlight(
    self,
    highlight: Dict[str, Any],
    category: str,
    session: AsyncSession,
    news_context: Dict[str, Any] = None  # NEW: Pass news context
) -> None:
    insight = AIInsight(
        # ... existing fields ...
        
        # NEW: Store the homework
        source_articles=news_context.get("headlines", []) if news_context else [],
        news_context=news_context,  # Full context for debugging
    )
    session.add(insight)
```

### Step 3: Create Market Detail API Endpoint

**Edit `app/api/routes/insights.py`:**
```python
@router.get("/ai/{insight_id}")
async def get_insight_detail(
    insight_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get full detail for a single AI insight.
    Includes source articles, full analysis, price history.
    """
    result = await db.execute(
        select(AIInsight).where(AIInsight.id == insight_id)
    )
    insight = result.scalar_one_or_none()
    
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    # Get market details
    market_result = await db.execute(
        select(Market).where(Market.id == insight.market_id)
    )
    market = market_result.scalar_one_or_none()
    
    # Get price history
    history_result = await db.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.market_id == insight.market_id)
        .order_by(MarketSnapshot.timestamp.desc())
        .limit(50)
    )
    snapshots = history_result.scalars().all()
    
    # Check for cross-platform match
    cross_platform = None
    if market:
        from app.services.cross_platform import CrossPlatformService
        cp_service = CrossPlatformService(db)
        matches = await cp_service.find_matches_for_market(market.id)
        if matches:
            cross_platform = matches[0]
    
    return {
        "insight": {
            "id": insight.id,
            "market_id": insight.market_id,
            "market_title": insight.market_title,
            "platform": insight.platform,
            "category": insight.category,
            "summary": insight.summary,
            "current_odds": insight.current_odds,
            "implied_probability": insight.implied_probability,
            "volume_note": insight.volume_note,
            "recent_movement": insight.recent_movement,
            "movement_context": insight.movement_context,
            "upcoming_catalyst": insight.upcoming_catalyst,
            "analyst_note": insight.analyst_note,
            "created_at": insight.created_at,
        },
        "source_articles": insight.source_articles or [],  # THE HOMEWORK
        "market": {
            "id": market.id,
            "title": market.title,
            "platform": market.platform.value,
            "yes_price": market.yes_price,
            "no_price": market.no_price,
            "volume": market.volume,
            "status": market.status,
            "close_time": market.close_time,
            "url": _get_market_url(market),  # Link to actual market
        } if market else None,
        "price_history": [
            {"timestamp": s.timestamp, "yes_price": s.yes_price, "volume": s.volume}
            for s in snapshots
        ],
        "cross_platform": cross_platform,
    }


def _get_market_url(market: Market) -> str:
    """Get direct link to market on platform."""
    if market.platform.value == "kalshi":
        return f"https://kalshi.com/markets/{market.id}"
    else:
        return f"https://polymarket.com/event/{market.id}"
```

### Step 4: Create Frontend Detail Page

**Create `frontend/src/app/(app)/insights/[id]/page.tsx`:**
```tsx
'use client'

import { useParams } from 'next/navigation'
import { ArrowLeft, ExternalLink, TrendingUp, TrendingDown, Newspaper, Calendar, Scale } from 'lucide-react'
import Link from 'next/link'
import { useInsightDetail } from '@/hooks/useAPI'

export default function InsightDetailPage() {
  const { id } = useParams()
  const { data, isLoading, error } = useInsightDetail(id as string)

  if (isLoading) return <div className="lg:ml-64 p-6">Loading...</div>
  if (error) return <div className="lg:ml-64 p-6">Error loading insight</div>
  if (!data) return <div className="lg:ml-64 p-6">Insight not found</div>

  const { insight, source_articles, market, price_history, cross_platform } = data

  return (
    <div className="lg:ml-64 space-y-6 p-6">
      {/* Back Button */}
      <Link href="/opportunities" className="flex items-center gap-2 text-gray-500 hover:text-gray-700">
        <ArrowLeft className="w-4 h-4" />
        Back to Highlights
      </Link>

      {/* Header */}
      <div className="card">
        <div className="flex items-center gap-2 mb-2">
          <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
            {insight.platform}
          </span>
          <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-600">
            {insight.category}
          </span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{insight.market_title}</h1>
        <p className="text-gray-600">{insight.summary}</p>
      </div>

      {/* Current Odds */}
      {insight.current_odds && (
        <div className="grid grid-cols-2 gap-4">
          <div className="card bg-green-50">
            <p className="text-sm text-green-600 font-medium">Yes</p>
            <p className="text-3xl font-bold text-green-700">
              {(insight.current_odds.yes * 100).toFixed(0)}%
            </p>
          </div>
          <div className="card bg-red-50">
            <p className="text-sm text-red-600 font-medium">No</p>
            <p className="text-3xl font-bold text-red-700">
              {(insight.current_odds.no * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      )}

      {/* AI Analysis - The Good Stuff */}
      <div className="card border-l-4 border-primary-500">
        <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
          🧠 AI Analysis
        </h2>
        <p className="text-gray-700 whitespace-pre-wrap">{insight.analyst_note}</p>
        
        {insight.upcoming_catalyst && (
          <div className="mt-4 p-3 bg-yellow-50 rounded-lg">
            <p className="text-sm font-medium text-yellow-800 flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Upcoming Catalyst
            </p>
            <p className="text-yellow-700 mt-1">{insight.upcoming_catalyst}</p>
          </div>
        )}

        {insight.movement_context && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-sm font-medium text-blue-800">Why It Moved</p>
            <p className="text-blue-700 mt-1">{insight.movement_context}</p>
          </div>
        )}
      </div>

      {/* Source Articles - SHOW THE HOMEWORK */}
      {source_articles && source_articles.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Newspaper className="w-5 h-5" />
            Source Articles
            <span className="text-xs text-gray-500 font-normal">(our homework)</span>
          </h2>
          <div className="space-y-3">
            {source_articles.map((article, i) => (
              <a
                key={i}
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium text-gray-900">{article.title}</p>
                    <p className="text-sm text-gray-500">
                      {article.source} • {article.date}
                    </p>
                  </div>
                  <ExternalLink className="w-4 h-4 text-gray-400 flex-shrink-0" />
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Cross-Platform Comparison */}
      {cross_platform && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Scale className="w-5 h-5" />
            Cross-Platform Price
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-600 font-medium">Kalshi</p>
              <p className="text-2xl font-bold text-blue-800">
                {cross_platform.kalshi_price?.toFixed(0)}¢
              </p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <p className="text-sm text-purple-600 font-medium">Polymarket</p>
              <p className="text-2xl font-bold text-purple-800">
                {cross_platform.polymarket_price?.toFixed(0)}¢
              </p>
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-3">
            {cross_platform.gap_cents?.toFixed(1)}¢ gap between platforms
          </p>
        </div>
      )}

      {/* Trade Links */}
      {market && (
        <div className="card bg-gray-50">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Trade This Market</h2>
          <div className="flex gap-3">
            <a
              href={market.url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary flex items-center gap-2"
            >
              Open on {market.platform}
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
```

### Step 5: Add API Hook

**Edit `frontend/src/hooks/useAPI.ts`:**
```typescript
export function useInsightDetail(id: string | null) {
  return useSWR(
    id ? `insightDetail|${id}` : null,
    fetcher<Awaited<ReturnType<typeof api.getInsightDetail>>>
  )
}
```

**Edit `frontend/src/lib/api.ts`:**
```typescript
export async function getInsightDetail(id: string) {
  return fetchAPI<{
    insight: AIInsight
    source_articles: Array<{title: string, url: string, source: string, date: string}>
    market: Market | null
    price_history: Array<{timestamp: string, yes_price: number, volume: number}>
    cross_platform: CrossPlatformMatch | null
  }>(`/insights/ai/${id}`)
}
```

### Step 6: Make Cards Clickable

**Edit `frontend/src/app/(app)/opportunities/page.tsx`:**
```tsx
// Change InsightCard to be a link
import Link from 'next/link'

function InsightCard({ insight }: { insight: AIInsight }) {
  return (
    <Link href={`/insights/${insight.id}`}>
      <div className="card hover:shadow-md transition-shadow cursor-pointer">
        {/* ... existing card content ... */}
      </div>
    </Link>
  )
}
```

**Same for dashboard and markets pages - wrap cards in `<Link>`**

---

## DETAIL PAGE SHOWS:

| Section | Content |
|---------|----------|
| **Header** | Market title, platform, category |
| **Odds** | Current Yes/No percentages |
| **AI Analysis** | Full analyst note with bro vibes |
| **Catalyst** | Upcoming events that could move price |
| **Movement Context** | WHY it moved recently |
| **Source Articles** | Links to news (THE HOMEWORK) 📰 |
| **Cross-Platform** | Price on Kalshi vs Polymarket |
| **Trade Links** | Direct links to trade on platforms |

---

## USER FLOW

```
Dashboard/Highlights Page
    │
    │ (click any card)
    ▼
┌─────────────────────────────────────┐
│  INSIGHT DETAIL PAGE                │
│                                     │
│  📊 Current Odds: 36% Yes           │
│                                     │
│  🧠 AI Analysis:                    │
│  "Yo this Fed cut at 36% is lowkey  │
│  interesting..."                    │
│                                     │
│  📰 Source Articles (our homework): │
│  • WSJ: Fed signals pause - Jan 3   │
│  • Reuters: CPI data preview - Jan 5│
│  • Bloomberg: Rate cut odds drop    │
│                                     │
│  📅 Catalyst: CPI data Jan 10       │
│                                     │
│  ⚖️ Cross-Platform:                 │
│  Kalshi: 34¢ | Polymarket: 38¢      │
│                                     │
│  [Trade on Polymarket →]            │
└─────────────────────────────────────┘
```

---

## FILES TO CREATE/EDIT

- [ ] `app/models/ai_insight.py` - Add `source_articles`, `news_context` columns
- [ ] `app/api/routes/insights.py` - Add `/ai/{id}` detail endpoint
- [ ] `app/services/patterns/engine.py` - Save news context with insights
- [ ] `frontend/src/app/(app)/insights/[id]/page.tsx` - CREATE detail page
- [ ] `frontend/src/hooks/useAPI.ts` - Add `useInsightDetail` hook
- [ ] `frontend/src/lib/api.ts` - Add `getInsightDetail` function
- [ ] `frontend/src/app/(app)/opportunities/page.tsx` - Make cards clickable
- [ ] `frontend/src/app/(app)/dashboard/page.tsx` - Make cards clickable
- [ ] `frontend/src/app/(app)/markets/page.tsx` - Make market cards clickable
- [ ] Run Alembic migration for new columns

---

# FEATURE: Market Detail Page (for Markets Tab)

## THE PROBLEM

Market cards in the Markets tab are also not clickable. Users should be able to:
- Click any market → see full details
- View price history chart
- See if there's an AI insight for this market
- Check cross-platform pricing
- Get direct trade links

## IMPLEMENTATION

### Step 1: Create Market Detail API Endpoint

**Edit `app/api/routes/markets.py`:**
```python
@router.get("/{market_id}")
async def get_market_detail(
    market_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get full detail for a single market.
    Includes price history, AI insights if any, cross-platform match.
    """
    result = await db.execute(
        select(Market).where(Market.id == market_id)
    )
    market = result.scalar_one_or_none()
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    # Get price history
    history_result = await db.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.market_id == market_id)
        .order_by(MarketSnapshot.timestamp.desc())
        .limit(100)
    )
    snapshots = history_result.scalars().all()
    
    # Check for AI insight
    insight_result = await db.execute(
        select(AIInsight)
        .where(AIInsight.market_id == market_id)
        .where(AIInsight.status == "active")
        .order_by(AIInsight.created_at.desc())
        .limit(1)
    )
    insight = insight_result.scalar_one_or_none()
    
    # Check for cross-platform match
    from app.models.cross_platform import CrossPlatformMatch
    match_result = await db.execute(
        select(CrossPlatformMatch)
        .where(
            (CrossPlatformMatch.kalshi_market_id == market_id) |
            (CrossPlatformMatch.polymarket_market_id == market_id)
        )
        .limit(1)
    )
    cross_match = match_result.scalar_one_or_none()
    
    return {
        "market": {
            "id": market.id,
            "title": market.title,
            "platform": market.platform.value,
            "yes_price": market.yes_price,
            "no_price": market.no_price,
            "volume": market.volume,
            "volume_24h": market.volume_24h,
            "status": market.status,
            "category": market.category,
            "close_time": market.close_time,
            "url": _get_market_url(market),
            "created_at": market.created_at,
            "updated_at": market.updated_at,
        },
        "price_history": [
            {
                "timestamp": s.timestamp.isoformat(),
                "yes_price": s.yes_price,
                "no_price": s.no_price,
                "volume": s.volume,
            }
            for s in reversed(snapshots)  # Chronological order
        ],
        "ai_insight": {
            "id": insight.id,
            "summary": insight.summary,
            "analyst_note": insight.analyst_note,
            "upcoming_catalyst": insight.upcoming_catalyst,
            "source_articles": insight.source_articles,
            "created_at": insight.created_at,
        } if insight else None,
        "cross_platform": {
            "kalshi_market_id": cross_match.kalshi_market_id,
            "polymarket_market_id": cross_match.polymarket_market_id,
            "kalshi_price": cross_match.kalshi_price,
            "polymarket_price": cross_match.polymarket_price,
            "price_gap": abs(cross_match.kalshi_price - cross_match.polymarket_price) if cross_match.kalshi_price and cross_match.polymarket_price else None,
        } if cross_match else None,
    }


def _get_market_url(market: Market) -> str:
    """Get direct link to market on platform."""
    if market.platform.value == "kalshi":
        # Kalshi uses ticker format
        return f"https://kalshi.com/markets/{market.id}"
    else:
        # Polymarket uses slug
        return f"https://polymarket.com/event/{market.id}"
```

### Step 2: Create Frontend Market Detail Page

**Create `frontend/src/app/(app)/markets/[id]/page.tsx`:**
```tsx
'use client'

import { useParams } from 'next/navigation'
import { ArrowLeft, ExternalLink, TrendingUp, TrendingDown, Brain, Scale, Clock } from 'lucide-react'
import Link from 'next/link'
import { useMarketDetail } from '@/hooks/useAPI'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function MarketDetailPage() {
  const { id } = useParams()
  const { data, isLoading, error } = useMarketDetail(id as string)

  if (isLoading) return <div className="lg:ml-64 p-6">Loading...</div>
  if (error) return <div className="lg:ml-64 p-6">Error loading market</div>
  if (!data) return <div className="lg:ml-64 p-6">Market not found</div>

  const { market, price_history, ai_insight, cross_platform } = data

  return (
    <div className="lg:ml-64 space-y-6 p-6">
      {/* Back Button */}
      <Link href="/markets" className="flex items-center gap-2 text-gray-500 hover:text-gray-700">
        <ArrowLeft className="w-4 h-4" />
        Back to Markets
      </Link>

      {/* Header */}
      <div className="card">
        <div className="flex items-center gap-2 mb-2">
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            market.platform === 'kalshi' 
              ? 'bg-blue-100 text-blue-800' 
              : 'bg-purple-100 text-purple-800'
          }`}>
            {market.platform}
          </span>
          {market.category && (
            <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-600">
              {market.category}
            </span>
          )}
          <span className={`px-2 py-1 rounded text-xs ${
            market.status === 'active' 
              ? 'bg-green-100 text-green-800' 
              : 'bg-gray-100 text-gray-600'
          }`}>
            {market.status}
          </span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{market.title}</h1>
        
        {market.close_time && (
          <p className="text-sm text-gray-500 flex items-center gap-1">
            <Clock className="w-4 h-4" />
            Closes: {new Date(market.close_time).toLocaleDateString()}
          </p>
        )}
      </div>

      {/* Current Odds */}
      <div className="grid grid-cols-2 gap-4">
        <div className="card bg-green-50">
          <p className="text-sm text-green-600 font-medium">Yes</p>
          <p className="text-3xl font-bold text-green-700">
            {(market.yes_price * 100).toFixed(0)}%
          </p>
        </div>
        <div className="card bg-red-50">
          <p className="text-sm text-red-600 font-medium">No</p>
          <p className="text-3xl font-bold text-red-700">
            {(market.no_price * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Volume Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="card">
          <p className="text-sm text-gray-500">Total Volume</p>
          <p className="text-xl font-bold text-gray-900">
            ${market.volume?.toLocaleString() || '0'}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">24h Volume</p>
          <p className="text-xl font-bold text-gray-900">
            ${market.volume_24h?.toLocaleString() || '0'}
          </p>
        </div>
      </div>

      {/* Price History Chart */}
      {price_history && price_history.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Price History</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={price_history}>
                <XAxis 
                  dataKey="timestamp" 
                  tickFormatter={(t) => new Date(t).toLocaleDateString()}
                  fontSize={12}
                />
                <YAxis 
                  domain={[0, 1]} 
                  tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                  fontSize={12}
                />
                <Tooltip 
                  formatter={(v: number) => `${(v * 100).toFixed(1)}%`}
                  labelFormatter={(t) => new Date(t).toLocaleString()}
                />
                <Line 
                  type="monotone" 
                  dataKey="yes_price" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* AI Insight - if exists */}
      {ai_insight && (
        <div className="card border-l-4 border-purple-500">
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-500" />
            AI Analysis
          </h2>
          <p className="text-gray-700 whitespace-pre-wrap mb-4">{ai_insight.analyst_note}</p>
          
          {ai_insight.upcoming_catalyst && (
            <div className="p-3 bg-yellow-50 rounded-lg mb-4">
              <p className="text-sm font-medium text-yellow-800">📅 Upcoming Catalyst</p>
              <p className="text-yellow-700 mt-1">{ai_insight.upcoming_catalyst}</p>
            </div>
          )}

          {/* Source Articles */}
          {ai_insight.source_articles && ai_insight.source_articles.length > 0 && (
            <div className="border-t pt-4">
              <p className="text-sm font-medium text-gray-700 mb-2">📰 Sources (our homework)</p>
              <div className="space-y-2">
                {ai_insight.source_articles.map((article: any, i: number) => (
                  <a
                    key={i}
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-sm text-blue-600 hover:underline"
                  >
                    {article.title} ({article.source})
                  </a>
                ))}
              </div>
            </div>
          )}

          <Link 
            href={`/insights/${ai_insight.id}`}
            className="text-sm text-purple-600 hover:underline mt-3 inline-block"
          >
            View full insight →
          </Link>
        </div>
      )}

      {/* Cross-Platform Comparison */}
      {cross_platform && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Scale className="w-5 h-5" />
            Cross-Platform Pricing
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-600 font-medium">Kalshi</p>
              <p className="text-2xl font-bold text-blue-800">
                {(cross_platform.kalshi_price * 100).toFixed(0)}%
              </p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <p className="text-sm text-purple-600 font-medium">Polymarket</p>
              <p className="text-2xl font-bold text-purple-800">
                {(cross_platform.polymarket_price * 100).toFixed(0)}%
              </p>
            </div>
          </div>
          {cross_platform.price_gap && (
            <p className="text-sm text-gray-500 mt-3">
              {(cross_platform.price_gap * 100).toFixed(1)}% gap between platforms
            </p>
          )}
        </div>
      )}

      {/* Trade Links */}
      <div className="card bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Trade This Market</h2>
        <a
          href={market.url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-primary inline-flex items-center gap-2"
        >
          Open on {market.platform}
          <ExternalLink className="w-4 h-4" />
        </a>
      </div>
    </div>
  )
}
```

### Step 3: Add API Hook for Market Detail

**Edit `frontend/src/hooks/useAPI.ts`:**
```typescript
export function useMarketDetail(id: string | null) {
  return useSWR(
    id ? `marketDetail|${id}` : null,
    () => id ? api.getMarketDetail(id) : null
  )
}
```

**Edit `frontend/src/lib/api.ts`:**
```typescript
export async function getMarketDetail(id: string) {
  return fetchAPI<{
    market: Market
    price_history: Array<{timestamp: string, yes_price: number, no_price: number, volume: number}>
    ai_insight: AIInsight | null
    cross_platform: CrossPlatformMatch | null
  }>(`/markets/${id}`)
}
```

### Step 4: Make Market Cards Clickable

**Edit `frontend/src/app/(app)/markets/page.tsx`:**
```tsx
import Link from 'next/link'

function MarketCard({ market }: { market: Market }) {
  return (
    <Link href={`/markets/${market.id}`}>
      <div className="card hover:shadow-md transition-shadow cursor-pointer">
        {/* ... existing card content ... */}
      </div>
    </Link>
  )
}
```

---

## COMPLETE FILES CHECKLIST (ALL CLICKABLE CARDS)

### Backend
- [ ] `app/models/ai_insight.py` - Add `source_articles`, `news_context` columns
- [ ] `app/api/routes/insights.py` - Add `/ai/{id}` detail endpoint
- [ ] `app/api/routes/markets.py` - Add `/{market_id}` detail endpoint
- [ ] `app/services/patterns/engine.py` - Save news context with insights
- [ ] Run Alembic migration

### Frontend - New Pages
- [ ] `frontend/src/app/(app)/insights/[id]/page.tsx` - Insight detail page
- [ ] `frontend/src/app/(app)/markets/[id]/page.tsx` - Market detail page

### Frontend - API Layer
- [ ] `frontend/src/hooks/useAPI.ts` - Add `useInsightDetail`, `useMarketDetail`
- [ ] `frontend/src/lib/api.ts` - Add `getInsightDetail`, `getMarketDetail`

### Frontend - Make Cards Clickable
- [ ] `frontend/src/app/(app)/opportunities/page.tsx` - Insight cards → Link
- [ ] `frontend/src/app/(app)/dashboard/page.tsx` - Insight cards → Link
- [ ] `frontend/src/app/(app)/markets/page.tsx` - Market cards → Link
- [ ] `frontend/src/app/(app)/cross-platform/page.tsx` - Match cards → Link (optional)

---

## SUMMARY FOR CLAUDE CODE

Implement clickable cards throughout the app:

1. **Insight cards** (dashboard, opportunities) → `/insights/[id]` detail page
2. **Market cards** (markets tab) → `/markets/[id]` detail page
3. Both detail pages show:
   - Full data (prices, volume, status)
   - Price history chart
   - AI analysis with bro vibes
   - **Source articles (the homework)**
   - Cross-platform comparison
   - Direct trade links

---

# FIX: AI Highlights Showing Same Category / Not Rotating

## THE PROBLEM

The AI Highlights page shows 3 insights but:
- All 3 are from the same category (finance/polymarket)
- No variety across categories
- Doesn't show the "best" 3, just the newest 3
- When analysis runs, same 3 keep showing

## ROOT CAUSE

In `app/api/routes/insights.py`, the query is:
```python
query = query.order_by(
    AIInsight.interest_score.desc().nullslast(),  # All are 50!
    AIInsight.created_at.desc()
).limit(tier_limit)
```

Since all `interest_score` = 50 (default), it's just showing newest 3, which happen to all be finance.

## THE FIX

Update the query to ensure **category variety** for FREE tier:

**Edit `app/api/routes/insights.py` - `get_ai_insights()` function:**

```python
@router.get("/ai")
async def get_ai_insights(
    category: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tier = user.subscription_tier

    # Tier limits
    if tier == SubscriptionTier.FREE or tier is None:
        tier_limit = 3
    elif tier == SubscriptionTier.BASIC:
        tier_limit = min(limit, 10)
    elif tier == SubscriptionTier.PREMIUM:
        tier_limit = min(limit, 30)
    else:  # PRO
        tier_limit = limit

    # If category filter is set, just query that category
    if category:
        query = (
            select(AIInsight)
            .where(AIInsight.status == "active")
            .where(AIInsight.expires_at > datetime.utcnow())
            .where(AIInsight.category == category)
            .order_by(AIInsight.created_at.desc())
            .limit(tier_limit)
        )
        result = await db.execute(query)
        insights = result.scalars().all()
    else:
        # NO CATEGORY FILTER: Get variety across categories
        # For FREE tier especially, show 1 from each top category
        
        if tier == SubscriptionTier.FREE or tier is None:
            # Get 1 newest from each of the top categories
            insights = []
            priority_categories = ["politics", "finance", "crypto", "sports", "tech"]
            
            for cat in priority_categories:
                if len(insights) >= tier_limit:
                    break
                    
                result = await db.execute(
                    select(AIInsight)
                    .where(AIInsight.status == "active")
                    .where(AIInsight.expires_at > datetime.utcnow())
                    .where(AIInsight.category == cat)
                    .order_by(AIInsight.created_at.desc())
                    .limit(1)
                )
                cat_insight = result.scalar_one_or_none()
                if cat_insight:
                    insights.append(cat_insight)
            
            # If we still don't have enough, fill with any category
            if len(insights) < tier_limit:
                existing_ids = [i.id for i in insights]
                result = await db.execute(
                    select(AIInsight)
                    .where(AIInsight.status == "active")
                    .where(AIInsight.expires_at > datetime.utcnow())
                    .where(AIInsight.id.not_in(existing_ids) if existing_ids else True)
                    .order_by(AIInsight.created_at.desc())
                    .limit(tier_limit - len(insights))
                )
                insights.extend(result.scalars().all())
        else:
            # Paid tiers: Get newest, but ensure some variety
            # Use window function to get top N per category, then merge
            query = (
                select(AIInsight)
                .where(AIInsight.status == "active")
                .where(AIInsight.expires_at > datetime.utcnow())
                .order_by(
                    AIInsight.category,  # Group by category
                    AIInsight.created_at.desc()
                )
                .limit(tier_limit * 3)  # Get more, then dedupe
            )
            result = await db.execute(query)
            all_insights = result.scalars().all()
            
            # Take up to 3 from each category, round-robin style
            from collections import defaultdict
            by_category = defaultdict(list)
            for i in all_insights:
                by_category[i.category].append(i)
            
            insights = []
            max_per_category = max(3, tier_limit // len(by_category)) if by_category else tier_limit
            
            # Round-robin across categories
            idx = 0
            while len(insights) < tier_limit:
                added_this_round = False
                for cat in by_category:
                    if len(insights) >= tier_limit:
                        break
                    if idx < len(by_category[cat]) and idx < max_per_category:
                        insights.append(by_category[cat][idx])
                        added_this_round = True
                if not added_this_round:
                    break
                idx += 1

    # ... rest of the function (format response)
```

## SIMPLER ALTERNATIVE

If you want a quicker fix, just randomize which 3 show for FREE tier:

```python
from sqlalchemy import func

if tier == SubscriptionTier.FREE or tier is None:
    # Random 3 from different categories
    query = (
        select(AIInsight)
        .where(AIInsight.status == "active")
        .where(AIInsight.expires_at > datetime.utcnow())
        .order_by(func.random())  # Randomize!
        .distinct(AIInsight.category)  # One per category
        .limit(tier_limit)
    )
```

## ALSO: Update Interest Score

The `interest_score` is always 50. Make it dynamic based on:
- Volume (higher = more interesting)
- Recent movement (bigger moves = more interesting)
- Has upcoming catalyst
- Cross-platform gap exists

**In `app/services/patterns/engine.py` `save_market_highlight()`:**

```python
def calculate_interest_score(highlight: dict, market_data: dict = None) -> int:
    """Calculate how interesting/important this insight is."""
    score = 50  # Base
    
    # Volume boost
    volume = market_data.get("volume", 0) if market_data else 0
    if volume > 1_000_000:
        score += 20
    elif volume > 100_000:
        score += 10
    elif volume > 10_000:
        score += 5
    
    # Movement boost
    movement = highlight.get("recent_movement", "")
    if movement:
        try:
            pct = float(movement.replace("%", "").replace("+", "").replace("-", ""))
            if pct > 10:
                score += 15
            elif pct > 5:
                score += 10
            elif pct > 2:
                score += 5
        except:
            pass
    
    # Catalyst boost
    if highlight.get("upcoming_catalyst"):
        score += 10
    
    # Cap at 100
    return min(100, score)


async def save_market_highlight(self, highlight, category, session, news_context=None):
    # Calculate dynamic interest score
    interest = calculate_interest_score(highlight)
    
    insight = AIInsight(
        # ... existing fields ...
        interest_score=interest,  # Dynamic, not hardcoded 50
    )
```

---

## EXPECTED RESULT

**Before:** All 3 highlights are finance/polymarket

**After:** 
- 1 politics highlight
- 1 finance highlight  
- 1 crypto (or sports/tech) highlight

FREE users see variety, making the upgrade more compelling since they see value across categories.

---

# BUG FIX: Insight Detail Missing Data + Market Detail 404

## Issue 1: Insight Detail Page Looks "Plain"

**Cause:** FREE tier users don't get most fields due to tier-gating:

```python
# From insights.py - current tier gating:
- analyst_note → PRO only
- source_articles → PREMIUM+ only  
- movement_context → PREMIUM+ only
- upcoming_catalyst → PREMIUM+ only
```

So FREE users only see:
- Market title
- Summary  
- Current odds
- Price history chart

**Option A: Keep as-is** (strong upgrade incentive)

**Option B: Show teaser content** (better UX)

```python
# In get_insight_detail(), show blurred/truncated teasers for FREE:

# Example: Show first 100 chars of analyst_note with "Upgrade to see full analysis"
if tier == SubscriptionTier.FREE or tier is None:
    if insight.analyst_note:
        insight_data["analyst_note_preview"] = insight.analyst_note[:100] + "..."
        insight_data["analyst_note_locked"] = True
```

## Issue 2: "Error loading market" on View Market Details

**Cause:** The `market.id` stored in `ai_insights.market_id` doesn't match any market in the `markets` table.

**Debug Steps:**

```sql
-- Check what market_id is stored in the insight
SELECT id, market_id, market_title FROM ai_insights LIMIT 5;

-- Check if that market_id exists in markets table
SELECT id, title FROM markets WHERE id = '<market_id_from_above>';

-- Find the actual market
SELECT id, title FROM markets WHERE title ILIKE '%Kevin Hassett%';
```

**Likely Cause:** When AI analysis runs, it might be storing a different market ID format than what's in the database.

In `app/services/patterns/engine.py` `save_market_highlight()`:

```python
insight = AIInsight(
    market_id=highlight.get("market_id", "unknown"),  # This might be wrong!
    ...
)
```

**The Fix:**

Ensure consistent market_id when saving insights:

```python
async def save_market_highlight(
    self,
    highlight: Dict[str, Any],
    category: str,
    session: AsyncSession,
    news_context: Dict[str, Any] = None,
    original_market_data: Dict[str, Any] = None  # ADD: Pass original market
) -> None:
    # Use the ACTUAL market_id from the database, not from AI response
    actual_market_id = original_market_data.get("market_id") if original_market_data else highlight.get("market_id")
    
    insight = AIInsight(
        market_id=actual_market_id,  # Guaranteed to match markets table
        ...
    )
```

**Quick Fix for Existing Data:**

```sql
-- Update ai_insights to match market IDs by title
UPDATE ai_insights ai
SET market_id = m.id
FROM markets m
WHERE LOWER(ai.market_title) = LOWER(m.title)
AND ai.market_id != m.id;
```

## Issue 3: Frontend Should Handle Missing Market Gracefully

**In the insight detail page**, if market is null, don't show "View Market Details" button:

```tsx
{/* Only show if market exists and is valid */}
{market && market.id && (
  <Link
    href={`/markets/${market.id}`}
    className="btn-secondary flex items-center gap-2"
  >
    View Market Details
  </Link>
)}
```

## Summary of Fixes

1. **Debug market_id mismatch** - Run SQL queries to find the discrepancy
2. **Fix insight save** - Pass original market data to ensure correct market_id
3. **Frontend fallback** - Hide "View Market Details" if market lookup fails
4. **Optional: Teaser content** - Show previews to FREE users to entice upgrades

---

# FEATURE: Interactive Tier Banner with Bug Chase Animation

## THE IDEA

A fun, animated banner below the navbar that:
- Has scrolling marquee text (left to right)
- Shows user's current tier + a fun message
- Has a little bug 🐛 emoji "chasing" the text
- Subtle upgrade nudge for FREE/BASIC users

## IMPLEMENTATION

### Create the Component

**Create `frontend/src/components/TierBanner.tsx`:**

```tsx
'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'

const TIER_MESSAGES = {
  free: [
    "You're on FREE tier • 3 highlights daily • Upgrade for more insights",
    "FREE tier vibes • Want the full analysis? • Go Premium",
    "Exploring the markets • FREE tier • Unlock analyst notes with PRO",
  ],
  basic: [
    "BASIC tier unlocked • 10 highlights • Upgrade for catalysts & context",
    "You're BASIC (in a good way) • Want movement analysis? • Go Premium",
  ],
  premium: [
    "PREMIUM member • Full context unlocked • Upgrade to PRO for analyst notes",
    "PREMIUM vibes • Source articles unlocked • PRO gets real-time updates",
  ],
  pro: [
    "PRO member • Full access unlocked • You're him",
    "PRO status • Real-time insights • You're seeing everything",
    "Maximum PRO energy • All features unlocked • Let's get it",
  ],
}

const TIER_COLORS = {
  free: 'from-gray-600 to-gray-800',
  basic: 'from-blue-600 to-blue-800',
  premium: 'from-purple-600 to-purple-800',
  pro: 'from-amber-500 to-orange-600',
}

export default function TierBanner() {
  const { user } = useAuth()
  const [messageIndex, setMessageIndex] = useState(0)
  
  const tier = (user?.subscription_tier?.toLowerCase() || 'free') as keyof typeof TIER_MESSAGES
  const messages = TIER_MESSAGES[tier] || TIER_MESSAGES.free
  const colors = TIER_COLORS[tier] || TIER_COLORS.free
  
  // Rotate messages every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length)
    }, 10000)
    return () => clearInterval(interval)
  }, [messages.length])

  const currentMessage = messages[messageIndex]
  const showUpgrade = tier === 'free' || tier === 'basic'

  return (
    <div className={`relative overflow-hidden bg-gradient-to-r ${colors} text-white py-1.5`}>
      {/* Marquee Container */}
      <div className="marquee-container flex items-center">
        {/* Bug chasing the text */}
        <div className="marquee-content flex items-center gap-4 animate-marquee">
          <span className="bug-icon text-lg">🐛</span>
          <span className="whitespace-nowrap text-sm font-medium tracking-wide">
            {currentMessage}
          </span>
          <span className="whitespace-nowrap text-sm font-medium tracking-wide">
            {currentMessage}
          </span>
          <span className="bug-icon text-lg">🐛</span>
          <span className="whitespace-nowrap text-sm font-medium tracking-wide">
            {currentMessage}
          </span>
          <span className="whitespace-nowrap text-sm font-medium tracking-wide">
            {currentMessage}
          </span>
        </div>
      </div>

      {/* Upgrade button (fixed position on right) */}
      {showUpgrade && (
        <div className="absolute right-0 top-0 bottom-0 flex items-center pr-4 bg-gradient-to-l from-black/30 to-transparent pl-8">
          <Link
            href="/settings"
            className="text-xs font-bold bg-white/20 hover:bg-white/30 px-3 py-1 rounded-full transition-colors"
          >
            Upgrade →
          </Link>
        </div>
      )}

      <style jsx>{`
        .marquee-container {
          width: 100%;
        }
        
        .marquee-content {
          display: flex;
          animation: marquee 20s linear infinite;
        }
        
        @keyframes marquee {
          0% {
            transform: translateX(0%);
          }
          100% {
            transform: translateX(-50%);
          }
        }
        
        .bug-icon {
          animation: wiggle 0.5s ease-in-out infinite;
        }
        
        @keyframes wiggle {
          0%, 100% {
            transform: rotate(-5deg);
          }
          50% {
            transform: rotate(5deg);
          }
        }
      `}</style>
    </div>
  )
}
```

### Alternative: Tailwind-only Version (no styled-jsx)

**Add to `frontend/src/app/globals.css`:**

```css
/* Tier Banner Animations */
@keyframes marquee {
  0% {
    transform: translateX(0%);
  }
  100% {
    transform: translateX(-50%);
  }
}

@keyframes wiggle {
  0%, 100% {
    transform: rotate(-5deg) scale(1);
  }
  50% {
    transform: rotate(5deg) scale(1.1);
  }
}

@keyframes chase {
  0%, 100% {
    transform: translateX(0px);
  }
  50% {
    transform: translateX(10px);
  }
}

.animate-marquee {
  animation: marquee 25s linear infinite;
}

.animate-wiggle {
  animation: wiggle 0.4s ease-in-out infinite;
}

.animate-chase {
  animation: chase 0.8s ease-in-out infinite;
}
```

**Simplified Component:**

```tsx
'use client'

import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'

export default function TierBanner() {
  const { user } = useAuth()
  const tier = user?.subscription_tier?.toLowerCase() || 'free'
  
  const config = {
    free: {
      bg: 'bg-gradient-to-r from-gray-700 to-gray-900',
      message: "FREE tier • 3 highlights daily • Upgrade for full insights",
      showUpgrade: true,
    },
    basic: {
      bg: 'bg-gradient-to-r from-blue-600 to-blue-800',
      message: "BASIC tier • 10 highlights • Upgrade for analyst notes",
      showUpgrade: true,
    },
    premium: {
      bg: 'bg-gradient-to-r from-purple-600 to-purple-800',
      message: "PREMIUM • Full context unlocked • Go PRO for real-time",
      showUpgrade: true,
    },
    pro: {
      bg: 'bg-gradient-to-r from-amber-500 to-orange-600',
      message: "PRO • All features unlocked • You're him 👑",
      showUpgrade: false,
    },
  }[tier] || { bg: 'bg-gray-800', message: 'Welcome!', showUpgrade: true }

  return (
    <div className={`${config.bg} text-white overflow-hidden relative`}>
      <div className="flex animate-marquee whitespace-nowrap py-1.5">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="flex items-center mx-8">
            <span className="animate-wiggle inline-block mr-3">🐛</span>
            <span className="text-sm font-medium">{config.message}</span>
          </div>
        ))}
      </div>
      
      {config.showUpgrade && (
        <div className="absolute right-0 top-0 bottom-0 flex items-center bg-gradient-to-l from-black/40 to-transparent pl-12 pr-4">
          <Link
            href="/settings"
            className="text-xs font-bold bg-white/20 hover:bg-white/30 px-3 py-1 rounded-full transition-all hover:scale-105"
          >
            Upgrade →
          </Link>
        </div>
      )}
    </div>
  )
}
```

### Add to Layout

**Edit `frontend/src/app/(app)/layout.tsx`:**

```tsx
import TierBanner from '@/components/TierBanner'
import Sidebar from '@/components/Sidebar'
import Navbar from '@/components/Navbar'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <TierBanner />  {/* ADD THIS */}
      <Sidebar />
      <main>{children}</main>
    </div>
  )
}
```

---

## VISUAL PREVIEW

```
┌────────────────────────────────────────────────────────────┐
│  OddWons          [Search...]                    🔔  S  │  <- Navbar
├────────────────────────────────────────────────────────────┤
│ 🐛 FREE tier • 3 highlights • Upgrade for more 🐛 FREE tier...  [Upgrade →] │  <- Banner
├────────────┬───────────────────────────────────────────────┤
│  Sidebar   │                                              │
│            │   Market Highlights                          │
│  Dashboard │   ...                                        │
│  AI High.. │                                              │
```

## TIER COLORS

| Tier | Gradient | Vibe |
|------|----------|------|
| FREE | Gray | Neutral, "you're missing out" |
| BASIC | Blue | Getting somewhere |
| PREMIUM | Purple | VIP energy |
| PRO | Gold/Orange | You're him 👑 |

## FUN MESSAGES BY TIER

**FREE:**
- "🐛 FREE tier • 3 highlights daily • Upgrade for full insights"
- "🐛 Exploring free? • The real insights are in Premium"

**BASIC:**
- "🐛 BASIC unlocked • Want the analyst notes? • Go PRO fam"

**PREMIUM:**
- "🐛 PREMIUM vibes • Source articles unlocked • PRO gets real-time"

**PRO:**
- "🐛 PRO status • Full access • You're him 👑"
- "🐛 Maximum PRO energy • All features unlocked • Let's get it"

---

## FILES TO CREATE/EDIT

- [ ] `frontend/src/components/TierBanner.tsx` - CREATE the banner component
- [ ] `frontend/src/app/globals.css` - ADD animation keyframes
- [ ] `frontend/src/app/(app)/layout.tsx` - ADD TierBanner below Navbar

---

# BUG FIX: Stripe Subscription Not Syncing to Database

## THE PROBLEM

User has an active Basic trial in Stripe but shows as FREE tier in the app.

**Stripe shows:**
- 2x "OddWons Basic" subscriptions (Trial ends Jan 12)
- Customer ID: `cus_TjlM93Jp9yx7oR`
- user_id in metadata: `b12f1e71-6e54-45d2-9ea7-91ac8496eca3`

**App shows:**
- FREE tier

## ROOT CAUSES TO CHECK

### 1. Webhook Not Registered in Stripe Dashboard

**Check:** Go to Stripe Dashboard → Developers → Webhooks

**Should have:**
- Endpoint URL: `https://your-domain.com/api/v1/billing/webhook`
- Events: `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`

### 2. Webhook Secret Not Configured

**Check:** In `.env`:
```
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

If missing, the webhook will silently fail.

### 3. User ID Mismatch

The `user_id` in Stripe metadata might not match the user in the database.

**Debug queries:**
```sql
-- Check if user exists with that ID
SELECT id, email, subscription_tier, stripe_customer_id, stripe_subscription_id 
FROM users 
WHERE id = 'b12f1e71-6e54-45d2-9ea7-91ac8496eca3';

-- Check if user exists by email
SELECT id, email, subscription_tier, stripe_customer_id, stripe_subscription_id 
FROM users 
WHERE email = 'shabari.cs@gmail.com';

-- Check if stripe_customer_id is set
SELECT id, email, subscription_tier, stripe_customer_id 
FROM users 
WHERE stripe_customer_id = 'cus_TjlM93Jp9yx7oR';
```

### 4. Duplicate Subscriptions (Bug!)

The user has **2 subscriptions** - this is wrong. Cancel one in Stripe.

## IMMEDIATE FIX: Manual Database Update

```sql
-- Update the user's tier manually
UPDATE users 
SET 
    subscription_tier = 'BASIC',
    subscription_status = 'trialing',
    stripe_customer_id = 'cus_TjlM93Jp9yx7oR',
    stripe_subscription_id = '<get_from_stripe>'
WHERE email = 'shabari.cs@gmail.com';
```

## LONG-TERM FIX: Add Sync Endpoint

**Create `app/api/routes/billing.py` - add sync endpoint:**

```python
@router.post("/sync")
async def sync_subscription(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Sync subscription status from Stripe.
    Useful if webhook failed or user is stuck on wrong tier.
    """
    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer ID")
    
    try:
        # Get all subscriptions for this customer
        subscriptions = stripe.Subscription.list(
            customer=user.stripe_customer_id,
            status="all",
            limit=1,
        )
        
        if not subscriptions.data:
            # No active subscription - set to FREE
            user.subscription_tier = SubscriptionTier.FREE
            user.subscription_status = SubscriptionStatus.INACTIVE
            user.stripe_subscription_id = None
            await db.commit()
            return {"message": "No subscription found", "tier": "free"}
        
        # Get the most recent active/trialing subscription
        sub = subscriptions.data[0]
        
        # Get tier from price
        price_id = sub["items"]["data"][0]["price"]["id"]
        tier = PRICE_TO_TIER.get(price_id, SubscriptionTier.BASIC)
        
        # Map status
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "trialing": SubscriptionStatus.TRIALING,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELED,
        }
        
        user.subscription_tier = tier
        user.subscription_status = status_map.get(sub["status"], SubscriptionStatus.INACTIVE)
        user.stripe_subscription_id = sub["id"]
        
        if sub.get("current_period_end"):
            user.subscription_end = datetime.fromtimestamp(sub["current_period_end"])
        if sub.get("trial_end"):
            user.trial_end = datetime.fromtimestamp(sub["trial_end"])
        
        await db.commit()
        
        return {
            "message": "Subscription synced",
            "tier": tier.value,
            "status": sub["status"],
            "trial_end": user.trial_end.isoformat() if user.trial_end else None,
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Add to frontend Settings page - "Sync Subscription" button:**

```tsx
<button 
  onClick={async () => {
    const res = await fetch('/api/v1/billing/sync', { method: 'POST' })
    const data = await res.json()
    alert(`Synced: ${data.tier} tier`)
    window.location.reload()
  }}
  className="btn-secondary"
>
  Sync Subscription
</button>
```

## CHECKLIST

- [ ] Register webhook in Stripe Dashboard (if not done)
- [ ] Set `STRIPE_WEBHOOK_SECRET` in `.env`
- [ ] Cancel duplicate subscription in Stripe
- [ ] Run manual SQL update to fix this user
- [ ] Add `/billing/sync` endpoint for future issues
- [ ] ~~Add "Sync" button to Settings page~~ → Move to Admin Panel instead

---

# FEATURE: Admin Panel

## WHY

Problems like Stripe sync issues should be fixed by admins, not customers. We need a proper admin panel for managing users, subscriptions, content, and system health.

## ACCESS CONTROL

**Add `is_admin` field to User model:**

```python
# app/models/user.py
class User(Base):
    # ... existing fields ...
    is_admin = Column(Boolean, default=False, nullable=False)
```

**Admin auth dependency:**

```python
# app/services/auth.py
async def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

---

## ADMIN PANEL FEATURES

### 1. 👥 User Management

| Feature | Description |
|---------|-------------|
| **List Users** | Paginated table with search/filter |
| **User Details** | Email, tier, signup date, last active, Stripe IDs |
| **Change Tier** | Manually upgrade/downgrade user tier |
| **Sync Subscription** | Pull latest from Stripe → fix sync issues |
| **Grant Trial** | Give user X days free trial |
| **Impersonate** | View app as this user (for debugging) |
| **Suspend/Ban** | Disable user access |
| **Delete User** | Remove user and their data |

### 2. 💳 Billing & Revenue

| Feature | Description |
|---------|-------------|
| **Revenue Dashboard** | MRR, ARR, growth rate |
| **Subscription List** | All active/trialing/canceled subs |
| **Sync All Subs** | Batch sync all users from Stripe |
| **Failed Payments** | Users with payment issues |
| **Refund** | Process refund for user |
| **Extend Trial** | Add days to user's trial |

### 3. 🧠 Content Management

| Feature | Description |
|---------|-------------|
| **AI Insights** | View all insights, delete stale ones |
| **Regenerate Insights** | Trigger AI analysis manually |
| **Markets** | View market counts by platform/category |
| **Cross-Platform Matches** | View/manage matches |
| **Clear Cache** | Flush Redis cache |

### 4. 🔧 System Health

| Feature | Description |
|---------|-------------|
| **API Status** | Health check for Kalshi, Polymarket, Groq, Gemini |
| **Database Stats** | Table sizes, row counts |
| **Redis Status** | Cache hit rate, memory usage |
| **Webhook Logs** | Recent Stripe webhooks (success/fail) |
| **Error Logs** | Recent application errors |
| **Background Jobs** | Data collection status |

### 5. 📊 Analytics

| Feature | Description |
|---------|-------------|
| **User Growth** | Signups over time chart |
| **Active Users** | DAU/WAU/MAU |
| **Tier Distribution** | Pie chart of FREE/BASIC/PREMIUM/PRO |
| **Feature Usage** | Which features are most used |
| **Top Markets** | Most viewed markets/insights |

### 6. ⚙️ Configuration

| Feature | Description |
|---------|-------------|
| **Feature Flags** | Enable/disable features |
| **Tier Limits** | Configure highlights per tier |
| **Rate Limits** | API rate limit settings |

---

## IMPLEMENTATION

### Backend: Admin API Routes

**Create `app/api/routes/admin.py`:**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from datetime import datetime, timedelta
import stripe

from app.core.database import get_db
from app.models.user import User, SubscriptionTier, SubscriptionStatus
from app.models.ai_insight import AIInsight
from app.models.market import Market
from app.services.auth import require_admin
from app.services.billing import PRICE_TO_TIER
from app.config import get_settings

router = APIRouter(prefix="/admin", tags=["admin"])
settings = get_settings()


# ============ USER MANAGEMENT ============

@router.get("/users")
async def list_users(
    search: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users with search and filter."""
    query = select(User)
    
    if search:
        query = query.where(
            User.email.ilike(f"%{search}%") | 
            User.name.ilike(f"%{search}%")
        )
    
    if tier:
        query = query.where(User.subscription_tier == SubscriptionTier(tier.upper()))
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Paginate
    query = query.order_by(desc(User.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "subscription_tier": u.subscription_tier.value if u.subscription_tier else "free",
                "subscription_status": u.subscription_status.value if u.subscription_status else None,
                "stripe_customer_id": u.stripe_customer_id,
                "trial_end": u.trial_end.isoformat() if u.trial_end else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "is_admin": u.is_admin,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed user info."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get Stripe subscription details if exists
    stripe_sub = None
    if user.stripe_subscription_id:
        try:
            stripe_sub = stripe.Subscription.retrieve(user.stripe_subscription_id)
        except:
            pass
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "subscription_tier": user.subscription_tier.value if user.subscription_tier else "free",
            "subscription_status": user.subscription_status.value if user.subscription_status else None,
            "stripe_customer_id": user.stripe_customer_id,
            "stripe_subscription_id": user.stripe_subscription_id,
            "trial_end": user.trial_end.isoformat() if user.trial_end else None,
            "subscription_end": user.subscription_end.isoformat() if user.subscription_end else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "is_admin": user.is_admin,
        },
        "stripe_subscription": {
            "id": stripe_sub.id,
            "status": stripe_sub.status,
            "current_period_end": stripe_sub.current_period_end,
            "trial_end": stripe_sub.trial_end,
            "cancel_at_period_end": stripe_sub.cancel_at_period_end,
        } if stripe_sub else None,
    }


@router.post("/users/{user_id}/sync-subscription")
async def sync_user_subscription(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Sync user's subscription from Stripe."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.stripe_customer_id:
        return {"message": "No Stripe customer ID", "synced": False}
    
    try:
        subscriptions = stripe.Subscription.list(
            customer=user.stripe_customer_id,
            status="all",
            limit=1,
        )
        
        if not subscriptions.data:
            user.subscription_tier = SubscriptionTier.FREE
            user.subscription_status = SubscriptionStatus.INACTIVE
            user.stripe_subscription_id = None
            await db.commit()
            return {"message": "No subscription found - set to FREE", "synced": True, "tier": "free"}
        
        sub = subscriptions.data[0]
        price_id = sub["items"]["data"][0]["price"]["id"]
        tier = PRICE_TO_TIER.get(price_id, SubscriptionTier.BASIC)
        
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "trialing": SubscriptionStatus.TRIALING,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELED,
        }
        
        user.subscription_tier = tier
        user.subscription_status = status_map.get(sub["status"], SubscriptionStatus.INACTIVE)
        user.stripe_subscription_id = sub["id"]
        
        if sub.get("current_period_end"):
            user.subscription_end = datetime.fromtimestamp(sub["current_period_end"])
        if sub.get("trial_end"):
            user.trial_end = datetime.fromtimestamp(sub["trial_end"])
        
        await db.commit()
        
        return {
            "message": "Subscription synced",
            "synced": True,
            "tier": tier.value,
            "status": sub["status"],
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/change-tier")
async def change_user_tier(
    user_id: str,
    tier: str = Query(..., description="new tier: free, basic, premium, pro"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manually change user's tier (for comp accounts, testing, etc)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_tier = user.subscription_tier.value if user.subscription_tier else "free"
    user.subscription_tier = SubscriptionTier(tier.upper())
    
    if tier.upper() != "FREE":
        user.subscription_status = SubscriptionStatus.ACTIVE
    
    await db.commit()
    
    return {
        "message": f"Tier changed from {old_tier} to {tier}",
        "user_id": user_id,
        "old_tier": old_tier,
        "new_tier": tier,
    }


@router.post("/users/{user_id}/grant-trial")
async def grant_trial(
    user_id: str,
    days: int = Query(7, ge=1, le=90),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Grant user a trial period."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.trial_end = datetime.utcnow() + timedelta(days=days)
    user.subscription_status = SubscriptionStatus.TRIALING
    
    if user.subscription_tier == SubscriptionTier.FREE:
        user.subscription_tier = SubscriptionTier.BASIC
    
    await db.commit()
    
    return {
        "message": f"Granted {days} day trial",
        "trial_end": user.trial_end.isoformat(),
    }


# ============ STATS & ANALYTICS ============

@router.get("/stats")
async def get_admin_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get admin dashboard stats."""
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # User counts
    total_users = await db.scalar(select(func.count()).select_from(User))
    new_users_24h = await db.scalar(
        select(func.count()).select_from(User).where(User.created_at > day_ago)
    )
    new_users_7d = await db.scalar(
        select(func.count()).select_from(User).where(User.created_at > week_ago)
    )
    
    # Tier distribution
    tier_counts = {}
    for tier in SubscriptionTier:
        count = await db.scalar(
            select(func.count()).select_from(User).where(User.subscription_tier == tier)
        )
        tier_counts[tier.value.lower()] = count or 0
    
    # Trialing users
    trialing = await db.scalar(
        select(func.count()).select_from(User)
        .where(User.subscription_status == SubscriptionStatus.TRIALING)
    )
    
    # Content stats
    total_markets = await db.scalar(select(func.count()).select_from(Market))
    total_insights = await db.scalar(
        select(func.count()).select_from(AIInsight).where(AIInsight.status == "active")
    )
    
    # Revenue estimate (paid users * avg price)
    paid_users = (tier_counts.get("basic", 0) + 
                  tier_counts.get("premium", 0) + 
                  tier_counts.get("pro", 0))
    estimated_mrr = (
        tier_counts.get("basic", 0) * 9.99 +
        tier_counts.get("premium", 0) * 19.99 +
        tier_counts.get("pro", 0) * 29.99
    )
    
    return {
        "users": {
            "total": total_users,
            "new_24h": new_users_24h,
            "new_7d": new_users_7d,
            "trialing": trialing,
        },
        "tiers": tier_counts,
        "revenue": {
            "paid_users": paid_users,
            "estimated_mrr": round(estimated_mrr, 2),
        },
        "content": {
            "total_markets": total_markets,
            "active_insights": total_insights,
        },
    }


@router.get("/webhook-logs")
async def get_webhook_logs(
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(require_admin),
):
    """Get recent Stripe webhook events."""
    try:
        events = stripe.Event.list(limit=limit)
        return {
            "events": [
                {
                    "id": e.id,
                    "type": e.type,
                    "created": datetime.fromtimestamp(e.created).isoformat(),
                    "data": {
                        "object_id": e.data.object.get("id") if hasattr(e.data, "object") else None,
                    },
                }
                for e in events.data
            ]
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ CONTENT MANAGEMENT ============

@router.post("/insights/regenerate")
async def regenerate_insights(
    category: Optional[str] = Query(None),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Trigger AI insight regeneration."""
    from app.services.patterns.engine import pattern_engine
    
    try:
        results = await pattern_engine.run_full_analysis(with_ai=True)
        return {
            "message": "Insights regenerated",
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/insights/clear-stale")
async def clear_stale_insights(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete expired/stale AI insights."""
    result = await db.execute(
        select(func.count()).select_from(AIInsight)
        .where(AIInsight.expires_at < datetime.utcnow())
    )
    stale_count = result.scalar() or 0
    
    await db.execute(
        AIInsight.__table__.delete().where(AIInsight.expires_at < datetime.utcnow())
    )
    await db.commit()
    
    return {"message": f"Deleted {stale_count} stale insights"}


# ============ SYSTEM HEALTH ============

@router.get("/health")
async def system_health(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Check system health."""
    from app.core.database import get_redis
    
    health = {
        "database": "unknown",
        "redis": "unknown",
        "stripe": "unknown",
    }
    
    # Database
    try:
        await db.execute(select(1))
        health["database"] = "healthy"
    except Exception as e:
        health["database"] = f"error: {str(e)}"
    
    # Redis
    try:
        r = await get_redis()
        await r.ping()
        health["redis"] = "healthy"
    except Exception as e:
        health["redis"] = f"error: {str(e)}"
    
    # Stripe
    try:
        stripe.Account.retrieve()
        health["stripe"] = "healthy"
    except Exception as e:
        health["stripe"] = f"error: {str(e)}"
    
    return health
```

**Register admin routes in `app/api/routes/__init__.py`:**

```python
from app.api.routes import admin

api_router.include_router(admin.router)
```

---

### Frontend: Admin Panel Pages

**Create `frontend/src/app/(app)/admin/layout.tsx`:**

```tsx
'use client'

import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import Link from 'next/link'
import { Users, CreditCard, Brain, Activity, Settings, BarChart3 } from 'lucide-react'

const adminNavItems = [
  { href: '/admin', label: 'Dashboard', icon: BarChart3 },
  { href: '/admin/users', label: 'Users', icon: Users },
  { href: '/admin/billing', label: 'Billing', icon: CreditCard },
  { href: '/admin/content', label: 'Content', icon: Brain },
  { href: '/admin/system', label: 'System', icon: Activity },
  { href: '/admin/config', label: 'Config', icon: Settings },
]

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (user && !user.is_admin) {
      router.push('/dashboard')
    }
  }, [user, router])

  if (!user?.is_admin) {
    return (
      <div className="lg:ml-64 p-6">
        <div className="card text-center py-12">
          <h2 className="text-xl font-bold text-gray-900">Access Denied</h2>
          <p className="text-gray-500 mt-2">Admin access required</p>
        </div>
      </div>
    )
  }

  return (
    <div className="lg:ml-64 p-6">
      {/* Admin Header */}
      <div className="mb-6 pb-4 border-b">
        <h1 className="text-2xl font-bold text-gray-900">🔐 Admin Panel</h1>
        <p className="text-gray-500">Manage users, billing, and system</p>
      </div>

      {/* Admin Nav */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {adminNavItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 whitespace-nowrap"
          >
            <item.icon className="w-4 h-4" />
            {item.label}
          </Link>
        ))}
      </div>

      {children}
    </div>
  )
}
```

**Create `frontend/src/app/(app)/admin/page.tsx` (Dashboard):**

```tsx
'use client'

import { useAdminStats } from '@/hooks/useAPI'
import { Users, DollarSign, TrendingUp, Brain } from 'lucide-react'

export default function AdminDashboard() {
  const { data: stats, isLoading } = useAdminStats()

  if (isLoading) return <div>Loading...</div>

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Dashboard</h2>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Users</p>
              <p className="text-2xl font-bold">{stats?.users?.total || 0}</p>
            </div>
          </div>
          <p className="text-xs text-green-600 mt-2">+{stats?.users?.new_7d || 0} this week</p>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <DollarSign className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Est. MRR</p>
              <p className="text-2xl font-bold">${stats?.revenue?.estimated_mrr || 0}</p>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">{stats?.revenue?.paid_users || 0} paid users</p>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Trialing</p>
              <p className="text-2xl font-bold">{stats?.users?.trialing || 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Brain className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">AI Insights</p>
              <p className="text-2xl font-bold">{stats?.content?.active_insights || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tier Distribution */}
      <div className="card">
        <h3 className="font-semibold mb-4">Tier Distribution</h3>
        <div className="grid grid-cols-4 gap-4">
          {Object.entries(stats?.tiers || {}).map(([tier, count]) => (
            <div key={tier} className="text-center">
              <p className="text-2xl font-bold">{count as number}</p>
              <p className="text-sm text-gray-500 capitalize">{tier}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
```

**Create `frontend/src/app/(app)/admin/users/page.tsx`:**

```tsx
'use client'

import { useState } from 'react'
import { useAdminUsers } from '@/hooks/useAPI'
import { Search, RefreshCw, ChevronRight } from 'lucide-react'
import Link from 'next/link'

export default function AdminUsersPage() {
  const [search, setSearch] = useState('')
  const [tierFilter, setTierFilter] = useState('')
  const { data, isLoading, mutate } = useAdminUsers({ search, tier: tierFilter })

  const handleSync = async (userId: string) => {
    const res = await fetch(`/api/v1/admin/users/${userId}/sync-subscription`, {
      method: 'POST',
    })
    const result = await res.json()
    alert(result.message)
    mutate()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Users</h2>
        <span className="text-gray-500">{data?.total || 0} total</span>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by email or name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg"
          />
        </div>
        <select
          value={tierFilter}
          onChange={(e) => setTierFilter(e.target.value)}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="">All Tiers</option>
          <option value="free">Free</option>
          <option value="basic">Basic</option>
          <option value="premium">Premium</option>
          <option value="pro">Pro</option>
        </select>
      </div>

      {/* Users Table */}
      <div className="card overflow-hidden p-0">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Email</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Tier</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Joined</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data?.users?.map((user: any) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div>
                    <p className="font-medium">{user.email}</p>
                    <p className="text-xs text-gray-500">{user.name || 'No name'}</p>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    user.subscription_tier === 'pro' ? 'bg-amber-100 text-amber-800' :
                    user.subscription_tier === 'premium' ? 'bg-purple-100 text-purple-800' :
                    user.subscription_tier === 'basic' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {user.subscription_tier}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-gray-600">
                    {user.subscription_status || '-'}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">
                  {user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleSync(user.id)}
                      className="p-1 hover:bg-gray-100 rounded"
                      title="Sync Subscription"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </button>
                    <Link
                      href={`/admin/users/${user.id}`}
                      className="p-1 hover:bg-gray-100 rounded"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
```

---

## FILES TO CREATE/EDIT

### Backend
- [ ] `app/models/user.py` - Add `is_admin` field
- [ ] `app/services/auth.py` - Add `require_admin` dependency
- [ ] `app/api/routes/admin.py` - CREATE admin API routes
- [ ] `app/api/routes/__init__.py` - Register admin router
- [ ] Run Alembic migration for `is_admin` column

### Frontend
- [ ] `frontend/src/app/(app)/admin/layout.tsx` - Admin layout with nav
- [ ] `frontend/src/app/(app)/admin/page.tsx` - Dashboard
- [ ] `frontend/src/app/(app)/admin/users/page.tsx` - User list
- [ ] `frontend/src/app/(app)/admin/users/[id]/page.tsx` - User detail
- [ ] `frontend/src/app/(app)/admin/billing/page.tsx` - Billing management
- [ ] `frontend/src/app/(app)/admin/content/page.tsx` - Content management
- [ ] `frontend/src/app/(app)/admin/system/page.tsx` - System health
- [ ] `frontend/src/hooks/useAPI.ts` - Add admin API hooks
- [ ] `frontend/src/lib/api.ts` - Add admin API functions

### Database
- [ ] Set yourself as admin:
```sql
UPDATE users SET is_admin = true WHERE email = 'your-email@example.com';
```

### Sidebar
- [ ] Add "Admin" link to sidebar (only visible if `user.is_admin`)

---

## ADMIN PANEL SUMMARY

| Section | Features |
|---------|----------|
| **Dashboard** | Stats, MRR, user counts, tier distribution |
| **Users** | List, search, sync subscription, change tier, grant trial |
| **Billing** | Webhook logs, failed payments, revenue |
| **Content** | Regenerate insights, clear stale data |
| **System** | Health checks, API status |
| **Config** | Feature flags, tier limits |

---

# ADMIN FEATURE: Manage Stripe Subscriptions (Cancel Duplicates)

## THE PROBLEM

Sync only reads from Stripe. When a user has duplicate subscriptions, sync doesn't cancel them - it just picks the first one.

## SOLUTION: Add Stripe Management Actions

### 1. List User's Stripe Subscriptions

**Add to `app/api/routes/admin.py`:**

```python
@router.get("/users/{user_id}/stripe-subscriptions")
async def list_user_stripe_subscriptions(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List ALL subscriptions for a user in Stripe.
    Useful for finding duplicates.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.stripe_customer_id:
        return {"subscriptions": [], "message": "No Stripe customer ID"}
    
    try:
        # Get ALL subscriptions (not just active)
        subscriptions = stripe.Subscription.list(
            customer=user.stripe_customer_id,
            status="all",  # active, trialing, canceled, etc.
            limit=10,
        )
        
        return {
            "customer_id": user.stripe_customer_id,
            "subscriptions": [
                {
                    "id": sub.id,
                    "status": sub.status,
                    "price_id": sub["items"]["data"][0]["price"]["id"],
                    "product_name": sub["items"]["data"][0]["price"].get("nickname", "Unknown"),
                    "current_period_end": datetime.fromtimestamp(sub.current_period_end).isoformat(),
                    "trial_end": datetime.fromtimestamp(sub.trial_end).isoformat() if sub.trial_end else None,
                    "cancel_at_period_end": sub.cancel_at_period_end,
                    "created": datetime.fromtimestamp(sub.created).isoformat(),
                }
                for sub in subscriptions.data
            ],
            "count": len(subscriptions.data),
            "has_duplicates": len([s for s in subscriptions.data if s.status in ["active", "trialing"]]) > 1,
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/cancel-stripe-subscription/{subscription_id}")
async def cancel_stripe_subscription(
    user_id: str,
    subscription_id: str,
    immediately: bool = Query(False, description="Cancel immediately vs at period end"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a specific Stripe subscription.
    Use this to clean up duplicates.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        if immediately:
            # Cancel immediately - no more access
            canceled_sub = stripe.Subscription.cancel(subscription_id)
            message = "Subscription canceled immediately"
        else:
            # Cancel at period end - user keeps access until then
            canceled_sub = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            message = "Subscription will cancel at period end"
        
        # If this was the user's active subscription, clear it from DB
        if user.stripe_subscription_id == subscription_id:
            user.stripe_subscription_id = None
            if immediately:
                user.subscription_tier = SubscriptionTier.FREE
                user.subscription_status = SubscriptionStatus.INACTIVE
            await db.commit()
        
        return {
            "message": message,
            "subscription_id": subscription_id,
            "new_status": canceled_sub.status,
            "cancel_at_period_end": canceled_sub.cancel_at_period_end,
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/cleanup-duplicate-subscriptions")
async def cleanup_duplicate_subscriptions(
    user_id: str,
    keep_subscription_id: Optional[str] = Query(None, description="ID of subscription to keep (newest if not specified)"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Find and cancel duplicate subscriptions, keeping only one.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.stripe_customer_id:
        raise HTTPException(status_code=404, detail="User not found or no Stripe customer")
    
    try:
        # Get active/trialing subscriptions
        subscriptions = stripe.Subscription.list(
            customer=user.stripe_customer_id,
            status="all",
            limit=10,
        )
        
        active_subs = [s for s in subscriptions.data if s.status in ["active", "trialing"]]
        
        if len(active_subs) <= 1:
            return {"message": "No duplicates found", "active_count": len(active_subs)}
        
        # Determine which to keep (newest by default, or specified)
        if keep_subscription_id:
            keep_sub = next((s for s in active_subs if s.id == keep_subscription_id), None)
            if not keep_sub:
                raise HTTPException(status_code=400, detail="Specified subscription not found")
        else:
            # Keep the newest one
            keep_sub = max(active_subs, key=lambda s: s.created)
        
        # Cancel all others immediately
        canceled = []
        for sub in active_subs:
            if sub.id != keep_sub.id:
                stripe.Subscription.cancel(sub.id)
                canceled.append(sub.id)
        
        # Update user's subscription ID to the kept one
        user.stripe_subscription_id = keep_sub.id
        
        # Get tier from kept subscription
        price_id = keep_sub["items"]["data"][0]["price"]["id"]
        tier = PRICE_TO_TIER.get(price_id, SubscriptionTier.BASIC)
        user.subscription_tier = tier
        
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "trialing": SubscriptionStatus.TRIALING,
        }
        user.subscription_status = status_map.get(keep_sub.status, SubscriptionStatus.ACTIVE)
        
        if keep_sub.trial_end:
            user.trial_end = datetime.fromtimestamp(keep_sub.trial_end)
        if keep_sub.current_period_end:
            user.subscription_end = datetime.fromtimestamp(keep_sub.current_period_end)
        
        await db.commit()
        
        return {
            "message": f"Cleaned up {len(canceled)} duplicate subscription(s)",
            "kept_subscription": keep_sub.id,
            "canceled_subscriptions": canceled,
            "user_tier": tier.value,
            "user_status": user.subscription_status.value,
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. Frontend: User Detail Page with Subscription Management

**Create `frontend/src/app/(app)/admin/users/[id]/page.tsx`:**

```tsx
'use client'

import { useParams } from 'next/navigation'
import { useState } from 'react'
import { ArrowLeft, RefreshCw, Trash2, AlertTriangle, CheckCircle } from 'lucide-react'
import Link from 'next/link'
import useSWR from 'swr'

export default function AdminUserDetailPage() {
  const { id } = useParams()
  const [loading, setLoading] = useState<string | null>(null)
  
  const { data: userData, mutate: mutateUser } = useSWR(
    `/api/v1/admin/users/${id}`,
    (url) => fetch(url).then(r => r.json())
  )
  
  const { data: subsData, mutate: mutateSubs } = useSWR(
    `/api/v1/admin/users/${id}/stripe-subscriptions`,
    (url) => fetch(url).then(r => r.json())
  )

  const handleSync = async () => {
    setLoading('sync')
    const res = await fetch(`/api/v1/admin/users/${id}/sync-subscription`, { method: 'POST' })
    const result = await res.json()
    alert(result.message)
    mutateUser()
    mutateSubs()
    setLoading(null)
  }

  const handleCancelSubscription = async (subId: string, immediately: boolean) => {
    if (!confirm(`Cancel subscription ${immediately ? 'immediately' : 'at period end'}?`)) return
    
    setLoading(subId)
    const res = await fetch(
      `/api/v1/admin/users/${id}/cancel-stripe-subscription/${subId}?immediately=${immediately}`,
      { method: 'POST' }
    )
    const result = await res.json()
    alert(result.message)
    mutateSubs()
    mutateUser()
    setLoading(null)
  }

  const handleCleanupDuplicates = async () => {
    if (!confirm('This will cancel all duplicate subscriptions, keeping only the newest. Continue?')) return
    
    setLoading('cleanup')
    const res = await fetch(`/api/v1/admin/users/${id}/cleanup-duplicate-subscriptions`, { method: 'POST' })
    const result = await res.json()
    alert(result.message)
    mutateSubs()
    mutateUser()
    setLoading(null)
  }

  const handleChangeTier = async (newTier: string) => {
    setLoading('tier')
    const res = await fetch(`/api/v1/admin/users/${id}/change-tier?tier=${newTier}`, { method: 'POST' })
    const result = await res.json()
    alert(result.message)
    mutateUser()
    setLoading(null)
  }

  const user = userData?.user
  const stripeSub = userData?.stripe_subscription
  const allSubs = subsData?.subscriptions || []
  const hasDuplicates = subsData?.has_duplicates

  return (
    <div className="space-y-6">
      <Link href="/admin/users" className="flex items-center gap-2 text-gray-500 hover:text-gray-700">
        <ArrowLeft className="w-4 h-4" /> Back to Users
      </Link>

      {/* User Info */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">User Details</h2>
        {user && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Email</p>
              <p className="font-medium">{user.email}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Name</p>
              <p className="font-medium">{user.name || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Current Tier (Database)</p>
              <span className={`px-2 py-1 rounded text-sm font-medium ${
                user.subscription_tier === 'pro' ? 'bg-amber-100 text-amber-800' :
                user.subscription_tier === 'premium' ? 'bg-purple-100 text-purple-800' :
                user.subscription_tier === 'basic' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {user.subscription_tier}
              </span>
            </div>
            <div>
              <p className="text-sm text-gray-500">Status</p>
              <p className="font-medium">{user.subscription_status || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Stripe Customer ID</p>
              <p className="font-mono text-sm">{user.stripe_customer_id || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Trial End</p>
              <p className="font-medium">
                {user.trial_end ? new Date(user.trial_end).toLocaleDateString() : '-'}
              </p>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="flex gap-2 mt-6 pt-4 border-t">
          <button
            onClick={handleSync}
            disabled={loading === 'sync'}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading === 'sync' ? 'animate-spin' : ''}`} />
            Sync from Stripe
          </button>
          
          <select
            onChange={(e) => e.target.value && handleChangeTier(e.target.value)}
            className="px-3 py-2 border rounded-lg"
            defaultValue=""
          >
            <option value="" disabled>Change Tier...</option>
            <option value="free">Free</option>
            <option value="basic">Basic</option>
            <option value="premium">Premium</option>
            <option value="pro">Pro</option>
          </select>
        </div>
      </div>

      {/* Stripe Subscriptions */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Stripe Subscriptions</h2>
          {hasDuplicates && (
            <button
              onClick={handleCleanupDuplicates}
              disabled={loading === 'cleanup'}
              className="btn-primary flex items-center gap-2 bg-red-600 hover:bg-red-700"
            >
              <Trash2 className="w-4 h-4" />
              Cleanup Duplicates
            </button>
          )}
        </div>

        {hasDuplicates && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            <span className="text-yellow-800">This user has duplicate subscriptions!</span>
          </div>
        )}

        {allSubs.length === 0 ? (
          <p className="text-gray-500">No subscriptions found in Stripe</p>
        ) : (
          <div className="space-y-3">
            {allSubs.map((sub: any) => (
              <div
                key={sub.id}
                className={`p-4 border rounded-lg ${
                  sub.status === 'active' || sub.status === 'trialing'
                    ? 'border-green-200 bg-green-50'
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm">{sub.id}</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        sub.status === 'active' ? 'bg-green-200 text-green-800' :
                        sub.status === 'trialing' ? 'bg-blue-200 text-blue-800' :
                        sub.status === 'canceled' ? 'bg-red-200 text-red-800' :
                        'bg-gray-200 text-gray-800'
                      }`}>
                        {sub.status}
                      </span>
                      {sub.cancel_at_period_end && (
                        <span className="text-xs text-orange-600">Cancels at period end</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      Created: {new Date(sub.created).toLocaleDateString()}
                      {sub.trial_end && ` • Trial ends: ${new Date(sub.trial_end).toLocaleDateString()}`}
                    </p>
                  </div>
                  
                  {(sub.status === 'active' || sub.status === 'trialing') && !sub.cancel_at_period_end && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleCancelSubscription(sub.id, false)}
                        disabled={loading === sub.id}
                        className="text-sm px-3 py-1 border rounded hover:bg-gray-100"
                      >
                        Cancel at End
                      </button>
                      <button
                        onClick={() => handleCancelSubscription(sub.id, true)}
                        disabled={loading === sub.id}
                        className="text-sm px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
                      >
                        Cancel Now
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
```

---

## ADMIN ACTIONS FOR STRIPE

| Action | What It Does |
|--------|-------------|
| **Sync Subscription** | Read from Stripe → update database (doesn't change Stripe) |
| **List Subscriptions** | Show ALL subscriptions in Stripe for user |
| **Cancel at End** | Set `cancel_at_period_end=true` (user keeps access until period ends) |
| **Cancel Now** | Immediately cancel (user loses access) |
| **Cleanup Duplicates** | Auto-cancel all but newest subscription |

---

## WORKFLOW TO FIX DUPLICATE SUBSCRIPTIONS

1. **Admin → Users → Click User**
2. See warning: "⚠️ This user has duplicate subscriptions!"
3. Click **"Cleanup Duplicates"** button
4. System auto-cancels extras, keeps newest
5. Database synced automatically

Or manually:
1. View all subscriptions
2. Click **"Cancel Now"** on the duplicate(s)
3. Click **"Sync from Stripe"** to update database

---

# FEATURE: Landing Page Hero Pattern Background

## THE IDEA

The hero section of the landing/splash page should have a fun, repeating pattern background with:
- **OddWons logo** (`/oddwons-logo.png`)
- **Cash emoji** 💸
- **Smiley face emoji** 😁

The pattern should be subtle (low opacity) so the main content is still readable, but adds personality and brand vibe.

## IMPLEMENTATION

### Option 1: CSS Repeating Background with Emoji + Logo

**Create a pattern component `frontend/src/components/HeroPattern.tsx`:**

```tsx
'use client'

export default function HeroPattern() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* Pattern Grid */}
      <div 
        className="absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage: `
            url('/oddwons-logo.png'),
            url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>💸</text></svg>"),
            url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>😁</text></svg>")
          `,
          backgroundSize: '80px 80px, 60px 60px, 60px 60px',
          backgroundPosition: '0 0, 120px 40px, 240px 80px',
          backgroundRepeat: 'repeat',
        }}
      />
    </div>
  )
}
```

### Option 2: Scattered Pattern with Animation (More Fun!)

**Create `frontend/src/components/HeroPattern.tsx`:**

```tsx
'use client'

import Image from 'next/image'

const PATTERN_ITEMS = [
  { type: 'logo', x: 5, y: 10, rotate: -15, size: 40 },
  { type: 'cash', x: 25, y: 5, rotate: 10, size: 35 },
  { type: 'smile', x: 45, y: 15, rotate: -5, size: 30 },
  { type: 'logo', x: 65, y: 8, rotate: 20, size: 35 },
  { type: 'cash', x: 85, y: 12, rotate: -10, size: 40 },
  { type: 'smile', x: 10, y: 35, rotate: 15, size: 35 },
  { type: 'logo', x: 30, y: 40, rotate: -20, size: 30 },
  { type: 'cash', x: 50, y: 32, rotate: 5, size: 40 },
  { type: 'smile', x: 70, y: 38, rotate: -15, size: 35 },
  { type: 'logo', x: 90, y: 42, rotate: 10, size: 30 },
  { type: 'cash', x: 15, y: 60, rotate: -5, size: 35 },
  { type: 'smile', x: 35, y: 65, rotate: 20, size: 40 },
  { type: 'logo', x: 55, y: 58, rotate: -10, size: 35 },
  { type: 'cash', x: 75, y: 62, rotate: 15, size: 30 },
  { type: 'smile', x: 95, y: 68, rotate: -20, size: 35 },
  { type: 'logo', x: 8, y: 85, rotate: 5, size: 40 },
  { type: 'cash', x: 28, y: 90, rotate: -15, size: 35 },
  { type: 'smile', x: 48, y: 82, rotate: 10, size: 30 },
  { type: 'logo', x: 68, y: 88, rotate: -5, size: 40 },
  { type: 'cash', x: 88, y: 92, rotate: 20, size: 35 },
]

export default function HeroPattern() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {PATTERN_ITEMS.map((item, i) => (
        <div
          key={i}
          className="absolute opacity-[0.08] select-none"
          style={{
            left: `${item.x}%`,
            top: `${item.y}%`,
            transform: `rotate(${item.rotate}deg)`,
            fontSize: `${item.size}px`,
          }}
        >
          {item.type === 'logo' ? (
            <Image
              src="/oddwons-logo.png"
              alt=""
              width={item.size}
              height={item.size}
              className="opacity-80"
            />
          ) : item.type === 'cash' ? (
            '💸'
          ) : (
            '😁'
          )}
        </div>
      ))}
    </div>
  )
}
```

### Option 3: Animated Floating Pattern (Most Fun!)

**Create `frontend/src/components/HeroPattern.tsx`:**

```tsx
'use client'

import Image from 'next/image'

const PATTERN_ITEMS = [
  { type: 'logo', x: 5, y: 10, delay: 0 },
  { type: 'cash', x: 20, y: 25, delay: 0.5 },
  { type: 'smile', x: 35, y: 8, delay: 1 },
  { type: 'logo', x: 50, y: 30, delay: 1.5 },
  { type: 'cash', x: 65, y: 15, delay: 2 },
  { type: 'smile', x: 80, y: 35, delay: 2.5 },
  { type: 'logo', x: 10, y: 55, delay: 3 },
  { type: 'cash', x: 25, y: 70, delay: 0.3 },
  { type: 'smile', x: 40, y: 50, delay: 0.8 },
  { type: 'logo', x: 55, y: 75, delay: 1.3 },
  { type: 'cash', x: 70, y: 60, delay: 1.8 },
  { type: 'smile', x: 85, y: 80, delay: 2.3 },
  { type: 'logo', x: 15, y: 90, delay: 0.6 },
  { type: 'cash', x: 45, y: 85, delay: 1.1 },
  { type: 'smile', x: 75, y: 92, delay: 1.6 },
  { type: 'cash', x: 92, y: 45, delay: 2.1 },
]

export default function HeroPattern() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {PATTERN_ITEMS.map((item, i) => (
        <div
          key={i}
          className="absolute opacity-[0.1] select-none animate-float"
          style={{
            left: `${item.x}%`,
            top: `${item.y}%`,
            animationDelay: `${item.delay}s`,
            fontSize: '40px',
          }}
        >
          {item.type === 'logo' ? (
            <Image
              src="/oddwons-logo.png"
              alt=""
              width={50}
              height={50}
              className="opacity-70"
            />
          ) : item.type === 'cash' ? (
            '💸'
          ) : (
            '😁'
          )}
        </div>
      ))}
    </div>
  )
}
```

**Add animation to `frontend/src/app/globals.css`:**

```css
@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  25% {
    transform: translateY(-10px) rotate(3deg);
  }
  50% {
    transform: translateY(-5px) rotate(-2deg);
  }
  75% {
    transform: translateY(-15px) rotate(2deg);
  }
}

.animate-float {
  animation: float 6s ease-in-out infinite;
}
```

### Use in Landing Page Hero

**Update `frontend/src/app/page.tsx` (or wherever the landing page is):**

```tsx
import HeroPattern from '@/components/HeroPattern'

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white py-24 overflow-hidden">
        {/* Pattern Background */}
        <HeroPattern />
        
        {/* Hero Content (on top of pattern) */}
        <div className="relative z-10 container mx-auto px-6 text-center">
          <h1 className="text-5xl md:text-6xl font-bold mb-6">
            Your Prediction Market
            <span className="text-primary-400"> Companion</span>
          </h1>
          <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
            AI-powered market analysis across Kalshi and Polymarket.
            Stay informed. Make smarter decisions.
          </p>
          <div className="flex gap-4 justify-center">
            <a href="/signup" className="btn-primary text-lg px-8 py-3">
              Start Free Trial
            </a>
            <a href="/login" className="btn-secondary text-lg px-8 py-3">
              Sign In
            </a>
          </div>
        </div>
      </section>
      
      {/* Rest of landing page... */}
    </div>
  )
}
```

---

## VISUAL PREVIEW

```
┌─────────────────────────────────────────────────────────────┐
│  💸        [logo]           😁          💸                  │
│       😁          💸              [logo]        😁          │
│  [logo]        😁        💸           😁        [logo]      │
│      ┌─────────────────────────────────────┐               │
│  💸  │   Your Prediction Market           │  [logo]        │
│      │        COMPANION                   │        😁      │
│ 😁   │                                    │  💸            │
│      │   AI-powered market analysis...    │       [logo]   │
│      │                                    │                │
│ [logo]│   [Start Free Trial] [Sign In]    │  😁     💸    │
│      └─────────────────────────────────────┘               │
│  💸       😁        [logo]       💸          😁    [logo]  │
└─────────────────────────────────────────────────────────────┘
```

---

## DESIGN NOTES

| Setting | Value | Why |
|---------|-------|-----|
| **Opacity** | 0.07-0.1 | Subtle, doesn't distract from content |
| **Pattern size** | 40-60px | Visible but not overwhelming |
| **Rotation** | Random ±20° | Adds playfulness, feels less rigid |
| **Animation** | Slow float | Optional - adds life without being distracting |

## FILES TO CREATE/EDIT

- [ ] `frontend/src/components/HeroPattern.tsx` - CREATE pattern component
- [ ] `frontend/src/app/globals.css` - ADD float animation (if using animated version)
- [ ] `frontend/src/app/page.tsx` - ADD HeroPattern to hero section
- [ ] Ensure `frontend/public/oddwons-logo.png` exists

---

# FIX: Hero Pattern Shows Grey Blobs Instead of Logo/Emojis

## THE PROBLEM

The current implementation uses inline SVG with hand-drawn shapes (rectangles, "OW" text) instead of:
- The actual `oddwons-logo.png` image
- The 💸 emoji
- The 😁 emoji

Result: Grey blobs instead of the fun pattern we want.

## THE FIX

Use actual DOM elements with the real logo and emojis, positioned absolutely.

### Create `frontend/src/components/BrandPattern.tsx`:

```tsx
'use client'

import Image from 'next/image'

interface PatternItem {
  type: 'logo' | 'cash' | 'smile'
  x: number
  y: number
  rotate: number
  size: number
  delay: number
}

// Generate a grid of pattern items
const generatePattern = (): PatternItem[] => {
  const items: PatternItem[] = []
  const types: ('logo' | 'cash' | 'smile')[] = ['logo', 'cash', 'smile']
  
  // Create a grid pattern
  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 10; col++) {
      const typeIndex = (row + col) % 3
      items.push({
        type: types[typeIndex],
        x: col * 10 + (row % 2) * 5 + Math.random() * 3, // Staggered grid with slight randomness
        y: row * 12 + Math.random() * 3,
        rotate: Math.random() * 30 - 15, // -15 to +15 degrees
        size: 30 + Math.random() * 15, // 30-45px
        delay: Math.random() * 3, // 0-3s animation delay
      })
    }
  }
  return items
}

const PATTERN_ITEMS = generatePattern()

interface BrandPatternProps {
  className?: string
  opacity?: number
  animated?: boolean
}

export default function BrandPattern({ 
  className = '', 
  opacity = 0.08,
  animated = true 
}: BrandPatternProps) {
  return (
    <div className={`absolute inset-0 overflow-hidden pointer-events-none ${className}`}>
      {PATTERN_ITEMS.map((item, i) => (
        <div
          key={i}
          className={`absolute select-none ${animated ? 'animate-float' : ''}`}
          style={{
            left: `${item.x}%`,
            top: `${item.y}%`,
            transform: `rotate(${item.rotate}deg)`,
            opacity: opacity,
            animationDelay: animated ? `${item.delay}s` : undefined,
          }}
        >
          {item.type === 'logo' ? (
            <Image
              src="/oddwons-logo.png"
              alt=""
              width={item.size}
              height={item.size}
              className="rounded-lg"
            />
          ) : (
            <span style={{ fontSize: `${item.size}px` }}>
              {item.type === 'cash' ? '💸' : '😁'}
            </span>
          )}
        </div>
      ))}
    </div>
  )
}
```

### Add animation to `frontend/src/app/globals.css`:

```css
/* Brand Pattern Float Animation */
@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(var(--rotate, 0deg));
  }
  50% {
    transform: translateY(-8px) rotate(var(--rotate, 0deg));
  }
}

.animate-float {
  animation: float 4s ease-in-out infinite;
}
```

### Update Landing Page Hero `frontend/src/app/(public)/page.tsx`:

Replace the current SVG pattern section with:

```tsx
import BrandPattern from '@/components/BrandPattern'

// In the Hero section:
<section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
  {/* Brand Pattern Background */}
  <BrandPattern opacity={0.06} animated={true} />
  
  {/* Hero Content */}
  <div className="max-w-4xl mx-auto text-center relative z-10">
    {/* ... existing content ... */}
  </div>
</section>
```

**Delete the old `heroPatternSvg` variable and the inline `<style jsx>` block.**

---

# FEATURE: Add Brand Pattern to Login & Register Pages

## Login Page - Full Background Pattern

**Update `frontend/src/app/login/page.tsx`:**

```tsx
import BrandPattern from '@/components/BrandPattern'

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 relative overflow-hidden">
      {/* Background Pattern */}
      <BrandPattern opacity={0.05} animated={false} />
      
      {/* Login Form - Higher z-index */}
      <div className="relative z-10 w-full max-w-md p-8">
        <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-xl p-8">
          {/* ... existing login form content ... */}
        </div>
      </div>
    </div>
  )
}
```

## Register Page - Pattern on LEFT Side Only

The register page likely has a split layout (form on left, blue promo on right). Pattern should only be on the left.

**Update `frontend/src/app/register/page.tsx`:**

```tsx
import BrandPattern from '@/components/BrandPattern'

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex">
      {/* LEFT SIDE - Form with Pattern Background */}
      <div className="flex-1 flex items-center justify-center bg-gray-50 relative overflow-hidden">
        {/* Pattern - Only on this side */}
        <BrandPattern opacity={0.05} animated={false} />
        
        {/* Register Form - Higher z-index */}
        <div className="relative z-10 w-full max-w-md p-8">
          <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Create your account</h2>
            {/* ... form fields ... */}
          </div>
        </div>
      </div>

      {/* RIGHT SIDE - Blue promo (NO pattern here) */}
      <div className="hidden lg:flex flex-1 bg-primary-600 items-center justify-center p-12">
        <div className="max-w-md text-white">
          <h2 className="text-3xl font-bold mb-4">Start your journey</h2>
          <p className="text-primary-100">
            Join thousands of prediction market enthusiasts using OddWons.
          </p>
          {/* ... promo content ... */}
        </div>
      </div>
    </div>
  )
}
```

---

## VISUAL RESULT

### Landing Page Hero:
```
┌───────────────────────────────────────────────────┐
│  💸     [LOGO]      😁       💸     [LOGO]     │
│     😁        💸       [LOGO]      😁        │
│  [LOGO]    😁        💸       😁     [LOGO]   │
│       Your Prediction Market                  │
│  💸         COMPANION            💸          │
│     [LOGO]                    [LOGO]    😁    │
│  😁      [Start Trial]  [Sign In]      💸    │
└───────────────────────────────────────────────────┘
```

### Register Page (Split Layout):
```
┌──────────────────────────┬────────────────────────┐
│  💸   [LOGO]   😁         │                        │
│     😁    💸    [LOGO]    │   (BLUE BACKGROUND)    │
│  [LOGO]               😁  │                        │
│  ┌──────────────────┐    │   Start your journey   │
│  │ Create Account │ 💸  │                        │
│  │                │    │   Join thousands of    │
│  │ [Email]        │    │   prediction market    │
│ 😁│ [Password]     │    │   enthusiasts...       │
│  │ [Sign Up]      │    │                        │
│  └──────────────────┘    │   NO PATTERN HERE      │
│  💸   [LOGO]   😁  💸    │                        │
└──────────────────────────┴────────────────────────┘
        LEFT (with pattern)     RIGHT (solid blue)
```

---

## KEY POINTS FOR IMPLEMENTATION

1. **Delete** the old `heroPatternSvg` SVG string from the landing page
2. **Create** new `BrandPattern.tsx` component using real Image + emojis
3. **Use `z-index`** to ensure form content appears above pattern
4. **Use `bg-white/95 backdrop-blur-sm`** on form cards for slight transparency
5. **Pattern opacity**: ~5-8% so it's subtle but visible
6. **Register page**: Pattern only in the LEFT container, not the right blue side

## FILES TO CREATE/EDIT

- [ ] `frontend/src/components/BrandPattern.tsx` - CREATE new component
- [ ] `frontend/src/app/(public)/page.tsx` - REPLACE SVG pattern with BrandPattern
- [ ] `frontend/src/app/login/page.tsx` - ADD BrandPattern background
- [ ] `frontend/src/app/register/page.tsx` - ADD BrandPattern to LEFT side only
- [ ] `frontend/src/app/globals.css` - ADD float animation
