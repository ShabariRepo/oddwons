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
