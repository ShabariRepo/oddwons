"""
Gemini Web Search Service.
Uses Gemini 2.0 Flash with Google Search grounding to fetch real news context.

Cost: FREE for first 1,500 searches/day
"""
import os
import json
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


def _get_api_key() -> Optional[str]:
    """Get Gemini API key from environment or keys.txt."""
    # Try environment first
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key

    # Try keys.txt
    try:
        keys_path = os.path.join(os.path.dirname(__file__), "..", "..", "keys.txt")
        with open(keys_path, "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    return line.strip().split("=", 1)[1]
    except FileNotFoundError:
        pass

    return None


def _get_client():
    """Get configured Gemini client."""
    try:
        from google import genai
        from google.genai import types

        api_key = _get_api_key()
        if not api_key:
            logger.warning("GEMINI_API_KEY not found")
            return None, None

        client = genai.Client(api_key=api_key)
        return client, types
    except ImportError:
        logger.error("google-genai not installed. Run: pip install google-genai")
        return None, None


async def search_category_news(category: str, market_titles: List[str]) -> Dict[str, Any]:
    """
    Search for recent news related to a market category using Gemini with Google Search.

    Args:
        category: Category name (politics, sports, crypto, etc.)
        market_titles: List of market titles for context

    Returns:
        Dict with headlines, key events, and context
    """
    client, types = _get_client()
    if not client:
        return {
            "error": "Gemini not configured",
            "headlines": [],
            "key_events": [],
            "category_summary": f"Unable to fetch {category} news - Gemini not configured"
        }

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

Be concise. Focus on facts that would move prediction market prices. Return valid JSON only."""

    try:
        # Use Gemini 2.0 Flash with Google Search grounding
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.3,
            )
        )

        # Parse response - handle both raw JSON and markdown-wrapped JSON
        text = response.text.strip()

        # Try to extract JSON from response
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        result = json.loads(text)
        logger.info(f"Gemini search for {category}: {len(result.get('headlines', []))} headlines")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Gemini response not valid JSON for {category}: {e}")
        # Return raw text in error for debugging
        return {
            "error": f"Invalid JSON response: {str(e)}",
            "headlines": [],
            "key_events": [],
            "category_summary": f"Unable to parse {category} news response"
        }
    except Exception as e:
        logger.error(f"Gemini search failed for {category}: {e}")
        return {
            "error": str(e),
            "headlines": [],
            "key_events": [],
            "category_summary": f"Unable to fetch recent {category} news"
        }


async def search_market_context(market_title: str) -> Dict[str, Any]:
    """
    Search for specific context about a single market.
    Use sparingly - prefer batch category searches to stay under quota.
    """
    client, types = _get_client()
    if not client:
        return {"error": "Gemini not configured"}

    prompt = f"""Find recent news (last 7 days) about: {market_title}

Return JSON:
{{
    "headlines": [{{"title": "...", "source": "...", "date": "..."}}],
    "current_status": "What's the current situation?",
    "upcoming_events": ["event 1", "event 2"]
}}

Be concise and factual. Return valid JSON only."""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.3,
            )
        )

        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return json.loads(text)

    except Exception as e:
        logger.error(f"Gemini market search failed: {e}")
        return {"error": str(e)}


async def batch_search_categories(
    categories_with_markets: Dict[str, List[str]]
) -> Dict[str, Dict[str, Any]]:
    """
    Batch search news for multiple categories.

    Args:
        categories_with_markets: Dict mapping category -> list of market titles

    Returns:
        Dict mapping category -> news context
    """
    results = {}

    for category, market_titles in categories_with_markets.items():
        if not market_titles:
            continue

        logger.info(f"Fetching news context for {category} ({len(market_titles)} markets)...")
        results[category] = await search_category_news(category, market_titles)

    return results
