# X (Twitter) Integration - Teaser Posts to Funnel Users

## The Strategy

**Show the DATA, tease the ANALYSIS, funnel to oddwons.ai**

| What We Show | What We Tease | What's on Platform |
|--------------|---------------|-------------------|
| Prices, movements, % changes | "Why the jump?" | Full movement_context |
| Platform gaps | "What do they know?" | Complete analyst_note |
| Visual formatting | "One stat explains this..." | Source articles, deep dive |

## Example Posts

**Morning Movers:**
```
📊 Overnight Movers

Fed rate cut March?
├ Was: 45%
└ Now: 52% (+7%)

📈 What's behind the move?

Full analysis → oddwons.ai

[IMAGE from Kalshi/Polymarket]
```

**Platform Comparison:**
```
⚖️ Platforms disagree

Bitcoin $100K by June

Kalshi:     42% ████░░░░░░
Polymarket: 38% ████░░░░░░

🤔 Why the 4pt gap?

oddwons.ai has the breakdown

[IMAGE]
```

**Market Highlight:**
```
🔥 Market to Watch

Super Bowl winner odds shifting

├ Chiefs: 32%
├ 49ers: 28%
└ Lions: 18%

💡 One key factor is driving this...

Full analysis → oddwons.ai

[IMAGE]
```

## What's Happening Under the Hood

```
1. Pull AIInsight from DB (has the full analysis)
2. Extract DATA: prices, movements, percentages
3. Pass to Groq with TEASER prompt
4. Groq sees the context but only hints at it
5. Attach market image
6. Post with CTA to oddwons.ai
```

## Teaser Phrases Used

- "What's behind the move?"
- "Why the jump?"
- "We broke down the why..."
- "The story behind the numbers..."
- "One stat explains this..."
- "What do they know that you don't?"
- "There's more to this story..."

## What I Need You To Do

### 1. Test X Connection
```python
import asyncio
from app.services.x_poster import test_x_connection

result = asyncio.run(test_x_connection())
print(result)
```

### 2. Test a teaser tweet (without posting):
```python
import asyncio
from app.services.x_poster import generate_tweet_with_ai

# Groq sees the full context but only teases it
market_data = {
    "markets": [
        {
            "title": "Fed cuts rates in March",
            "current_odds": {"yes": 0.52, "no": 0.48},
            "recent_movement": "+7% this week",
            "movement_context": "Jobs report came in mixed, unemployment ticked up",  # Groq knows this
            "analyst_note": "Historical pattern suggests Fed acts within 60 days of labor weakness",  # But won't reveal
        }
    ]
}

tweet = asyncio.run(generate_tweet_with_ai(market_data, "morning_movers"))
print(tweet)
# Should tease "What shifted?" not explain the jobs report
```

### 3. Post a real teaser:
```python
import asyncio
from app.services.x_poster import post_morning_movers

result = asyncio.run(post_morning_movers())
print(result)
```

### 4. Verify you have GROQ_API_KEY in .env
Uses Groq (llama-3.3-70b) for tweet generation. Without it, falls back to static templates.

## Scheduled Posts

| Time (EST) | Post Type | Teaser Style |
|------------|-----------|--------------|
| 9:00 AM | Morning Movers | "What's behind the move?" |
| 2:00 PM | Platform Gap | "Why the gap?" |
| 6:00 PM | Market Highlight | "One factor is driving this..." |
| Sun 10 AM | Weekly Recap | Stats + "Follow for daily insights" |

## The Funnel

```
X Post (teaser)     →    oddwons.ai    →    Subscribe
   "Why did it move?"      Full analysis       $9.99/mo
   [visual data]           Source articles
   [market image]          AI insights
```

Users see enough to be intrigued, but need the platform for the full scoop.
