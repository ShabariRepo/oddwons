# FEATURE: Gemini Web Search → Groq Analysis Pipeline

## Overview

Use **Gemini 2.5 Flash-Lite** (cheap, 1,500 free searches/day) to gather real news context for each market category, then pass enriched data to **Groq** for analysis.

```
┌─────────────────────────────────────────────────────────────────┐
│  CURRENT FLOW (blind analysis)                                  │
│  Market data → Groq → "probably moved due to news" (guessing)   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  NEW FLOW (informed analysis)                                   │
│  Market data → Gemini web search → real headlines               │
│       ↓                                                         │
│  Market data + real news → Groq → informed analysis             │
└─────────────────────────────────────────────────────────────────┘
```

## Why This Architecture

| Component | Role | Cost |
|-----------|------|------|
| Gemini Flash-Lite | Web search (grounding) | FREE first 1,500/day |
| Groq | Fast inference | ~$0.05/1M tokens |

64 insights × 9 categories = ~9 search queries = FREE

## API Keys

Keys are stored in `keys.txt` (gitignored):
```
GEMINI_API_KEY=AIzaSy...  (already added)
GROQ_API_KEY=gsk_...      (in .env)
```

## Implementation Plan

### Step 1: Create Gemini Search Service

Create `app/services/gemini_search.py`:

```python
"""
Gemini Web Search Service.
Uses Gemini 2.5 Flash-Lite with Google Search grounding to fetch real news context.
"""
import os
import google.generativeai as genai
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

# Load API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def configure_gemini():
    """Configure Gemini with API key."""
    if not GEMINI_API_KEY:
        # Try loading from keys.txt
        try:
            with open("keys.txt", "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        key = line.strip().split("=", 1)[1]
                        genai.configure(api_key=key)
                        return True
        except FileNotFoundError:
            pass
        logger.warning("GEMINI_API_KEY not found")
        return False
    
    genai.configure(api_key=GEMINI_API_KEY)
    return True


async def search_category_news(category: str, market_titles: List[str]) -> Dict[str, any]:
    """
    Search for recent news related to a market category.
    
    Args:
        category: Category name (politics, sports, crypto, etc.)
        market_titles: List of market titles for context
        
    Returns:
        Dict with headlines, key events, and context
    """
    if not configure_gemini():
        return {"error": "Gemini not configured", "headlines": []}
    
    # Build search query based on category and top market titles
    top_markets = market_titles[:5]  # Use top 5 for context
    markets_context = "\n".join(f"- {t}" for t in top_markets)
    
    prompt = f"""Find the most recent news (last 7 days) relevant to these {category} prediction markets:

{markets_context}

Return a JSON object with:
{{
    "headlines": [
        {{"title": "...", "source": "...", "date": "...", "relevance": "which market this relates to"}}
    ],
    "key_events": [
        {{"event": "...", "date": "...", "impact": "how this affects the markets"}}
    ],
    "category_summary": "2-3 sentence overview of current {category} landscape"
}}

Be concise. Focus on facts that would move prediction market prices.
"""
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-lite",
            tools="google_search"  # Enable grounding with Google Search
        )
        
        response = model.generate_content(prompt)
        
        # Parse response
        import json
        text = response.text
        # Try to extract JSON from response
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
            
        return json.loads(text)
        
    except Exception as e:
        logger.error(f"Gemini search failed for {category}: {e}")
        return {
            "error": str(e),
            "headlines": [],
            "key_events": [],
            "category_summary": f"Unable to fetch recent {category} news"
        }


async def search_market_context(market_title: str) -> Dict[str, any]:
    """
    Search for specific context about a single market.
    Use sparingly - prefer batch category searches.
    """
    if not configure_gemini():
        return {"error": "Gemini not configured"}
    
    prompt = f"""Find recent news (last 7 days) about: {market_title}

Return JSON:
{{
    "headlines": [{{"title": "...", "source": "...", "date": "..."}}],
    "current_status": "What's the current situation?",
    "upcoming_events": ["event 1", "event 2"]
}}

Be concise and factual.
"""
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-lite",
            tools="google_search"
        )
        
        response = model.generate_content(prompt)
        
        import json
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
            
        return json.loads(text)
        
    except Exception as e:
        logger.error(f"Gemini market search failed: {e}")
        return {"error": str(e)}
```

### Step 2: Integrate into AI Agent

Modify `app/services/ai_agent.py` to use Gemini context:

```python
from app.services.gemini_search import search_category_news

async def analyze_category_batch(
    self,
    category: str,
    markets: List[Dict],
    patterns: List[Dict]
) -> Dict[str, Any]:
    """
    Analyze markets in a category with real news context.
    
    1. Fetch news context via Gemini (web search)
    2. Combine with market data
    3. Send to Groq for analysis
    """
    
    # Step 1: Get real news context from Gemini
    market_titles = [m.get("title", "") for m in markets]
    news_context = await search_category_news(category, market_titles)
    
    # Step 2: Build enriched prompt for Groq
    news_section = ""
    if news_context.get("headlines"):
        headlines = news_context["headlines"][:5]
        news_section = "RECENT NEWS:\n" + "\n".join(
            f"- {h.get('title', '')} ({h.get('source', '')}, {h.get('date', '')})"
            for h in headlines
        )
    
    if news_context.get("category_summary"):
        news_section += f"\n\nCATEGORY CONTEXT: {news_context['category_summary']}"
    
    if news_context.get("key_events"):
        events = news_context["key_events"][:3]
        news_section += "\n\nKEY EVENTS:\n" + "\n".join(
            f"- {e.get('event', '')} ({e.get('date', '')}): {e.get('impact', '')}"
            for e in events
        )
    
    # Step 3: Send enriched data to Groq
    prompt = f"""You are a prediction market analyst for oddwons.ai - but you're also a chill bro who makes finance fun.

Your vibe: Think smart friend who's really into prediction markets and explains things in a casual, engaging way. Use phrases like "yo", "lowkey", "no cap", "let's go", "wild", "spicy" etc naturally. Keep it fun but still informative.

CATEGORY: {category}

{news_section}

MARKETS TO ANALYZE:
{json.dumps(markets[:20], indent=2)}

For each interesting market, provide analysis that incorporates the recent news above.
Focus on WHY prices are where they are based on actual events.

TONE EXAMPLES:
- Instead of: "Market shows elevated probability due to recent polling"
- Say: "Yo this market is heating up - recent polls got it jumping to 62%, no cap"

- Instead of: "Significant price movement following news event"
- Say: "Bro this thing moved HARD after the news dropped - we're talking +12% in like 2 hours"

- Instead of: "Catalyst approaching that may impact pricing"
- Say: "Big date coming up fam - the Fed meeting on the 15th could make this spicy"

Return JSON with highlights...
"""
    
    # Call Groq with enriched context
    return await self._call_groq(prompt)
```

### Step 3: Update Pattern Engine

In `app/services/patterns/engine.py`, update `run_ai_analysis()`:

```python
async def run_ai_analysis(self, patterns, markets, session):
    """Run AI analysis with Gemini web search enrichment."""
    
    # Group markets by category (existing code)
    market_by_category = {}
    for market in markets:
        category = self._infer_category(market.title or "")
        if category not in market_by_category:
            market_by_category[category] = []
        market_by_category[category].append({...})
    
    # NEW: Fetch news context for each category via Gemini
    from app.services.gemini_search import search_category_news
    
    category_news = {}
    for category in market_by_category.keys():
        if len(market_by_category[category]) >= 3:
            titles = [m["title"] for m in market_by_category[category][:10]]
            logger.info(f"Fetching news context for {category}...")
            category_news[category] = await search_category_news(category, titles)
    
    # Pass news context to AI agent
    for category, category_markets in market_by_category.items():
        news = category_news.get(category, {})
        result = await ai_agent.analyze_category_batch(
            category=category,
            markets=category_markets,
            patterns=pattern_by_category.get(category, []),
            news_context=news  # NEW: Pass real news
        )
        # ... save highlights
```

### Step 4: Install Gemini SDK

```bash
pip install google-generativeai
# Add to requirements.txt
echo "google-generativeai" >> requirements.txt
```

### Step 5: Add Key to Environment

Either:
1. Add to `.env`: `GEMINI_API_KEY=AIzaSy...`
2. Or load from `keys.txt` (already implemented in service)

---

## Cost Estimate

| Category searches | Cost |
|-------------------|------|
| 9 categories × 1 search each | FREE (under 1,500/day limit) |
| Groq inference | ~$0.02 per run |
| **Total per analysis run** | **~$0.02** |

---

## Testing

```bash
# Test Gemini search
python -c "
import asyncio
from app.services.gemini_search import search_category_news

async def test():
    result = await search_category_news('politics', ['Will Trump win 2024?', 'Fed rate decision'])
    print(result)

asyncio.run(test())
"
```

---

## Files to Create/Edit

1. **CREATE** `app/services/gemini_search.py` - Gemini web search service
2. **EDIT** `app/services/ai_agent.py` - Add news_context parameter
3. **EDIT** `app/services/patterns/engine.py` - Fetch news before analysis
4. **EDIT** `requirements.txt` - Add `google-generativeai`

---

## Expected Result

**Before (blind + corporate):**
> "Market shows 62% probability. Movement likely due to recent developments."

**After (informed + bro vibes):**
> "Yo this Fed Chair market is getting spicy 🔥 Sitting at 62% right now after the WSJ dropped that Warsh met with the transition team on Jan 3rd. Both Kalshi and Poly jumped like +5% on that news, no cap. Big date coming up fam - announcement expected late January. This one's gonna move HARD when we get official word. Stay locked in! 📈"

---

## Commands for Claude Code

```bash
# 1. Install Gemini SDK
pip install google-generativeai

# 2. Create the gemini search service
# Create app/services/gemini_search.py with code above

# 3. Update ai_agent.py to accept news_context

# 4. Update pattern engine to fetch news first

# 5. Test the integration
python run_analysis.py
```
