# URGENT: Implement AI-Powered Analysis with Groq

## The Problem

The current rule-based pattern detection is NOT the product. "Volume spike detected" is worthless - users can see that themselves. The VALUE PROP is AI agents finding NON-OBVIOUS patterns and generating intelligent, actionable insights.

## What Needs to Be Built NOW

### 1. Groq Integration

Create `services/ai_agent.py`:

```python
import os
from groq import Groq
from typing import List, Dict, Any
import json

class MarketAnalysisAgent:
    def __init__(self):
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        # GPT OSS 20B: Fastest (1000 TPS) and cheapest ($0.075/M input, $0.30/M output)
        self.model = os.environ.get("AI_MODEL", "gpt-oss-20b-128k")
        
        # Model options by priority:
        # 1. gpt-oss-20b-128k     - 1000 TPS, $0.075 in / $0.30 out  (DEFAULT - fastest, cheapest)
        # 2. qwen3-32b-131k       - 662 TPS,  $0.29 in / $0.59 out   (good balance)
        # 3. llama-4-scout-17bx16e-128k - 594 TPS, $0.11 in / $0.34 out (newer llama)
        # 4. llama-3.3-70b-versatile - 394 TPS, $0.59 in / $0.79 out (slowest, most expensive)
    
    def analyze_opportunity(self, market_data: Dict, historical_patterns: List[Dict]) -> Dict:
        """
        Analyze a single market opportunity with full context.
        Returns actionable insight with confidence score and reasoning.
        """
        
        prompt = f"""You are an expert prediction market analyst. Analyze this opportunity and provide actionable insights.

MARKET DATA:
{json.dumps(market_data, indent=2)}

HISTORICAL PATTERNS DETECTED:
{json.dumps(historical_patterns, indent=2)}

Provide your analysis in this exact JSON format:
{{
    "recommendation": "STRONG_BET" | "GOOD_BET" | "CAUTION" | "AVOID",
    "confidence_score": 0-100,
    "one_liner": "Single sentence a bettor can act on immediately",
    "reasoning": "2-3 sentences explaining WHY this is an opportunity",
    "risk_factors": ["risk1", "risk2"],
    "suggested_position": "YES" | "NO" | "WAIT",
    "edge_explanation": "What edge does the bettor have here that the market is missing?",
    "time_sensitivity": "ACT_NOW" | "HOURS" | "DAYS" | "WEEKS"
}}

Be specific. Be actionable. If there's no real edge, say so. Don't hype garbage opportunities."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def generate_daily_digest(self, all_opportunities: List[Dict]) -> Dict:
        """
        Generate the daily analysis digest for subscribers.
        Ranks opportunities and provides portfolio-level insights.
        """
        
        prompt = f"""You are an expert prediction market analyst creating a daily briefing for paying subscribers.

TODAY'S DETECTED OPPORTUNITIES:
{json.dumps(all_opportunities, indent=2)}

Create a daily digest in this exact JSON format:
{{
    "top_picks": [
        {{
            "market_id": "id",
            "market_title": "title",
            "recommendation": "STRONG_BET" | "GOOD_BET",
            "one_liner": "Why this is today's top pick",
            "confidence": 0-100
        }}
    ],
    "avoid_list": [
        {{
            "market_id": "id",
            "market_title": "title",
            "reason": "Why to stay away"
        }}
    ],
    "market_sentiment": "Brief overview of overall market conditions",
    "arbitrage_opportunities": [
        {{
            "description": "Cross-platform or related market arb",
            "potential_edge": "X%"
        }}
    ],
    "watchlist": [
        {{
            "market_id": "id",
            "market_title": "title",
            "trigger": "What would make this actionable"
        }}
    ]
}}

Be ruthless. Only include REAL opportunities. Subscribers are paying for alpha, not noise."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)

    def analyze_cross_platform_arbitrage(self, kalshi_markets: List[Dict], polymarket_markets: List[Dict]) -> List[Dict]:
        """
        Find arbitrage opportunities between Kalshi and Polymarket.
        """
        
        prompt = f"""You are an arbitrage specialist analyzing prediction markets across platforms.

KALSHI MARKETS:
{json.dumps(kalshi_markets, indent=2)}

POLYMARKET MARKETS:
{json.dumps(polymarket_markets, indent=2)}

Find ANY of these opportunities:
1. Same event priced differently across platforms
2. Related events where combined probabilities don't make sense
3. Temporal arbitrage (same event, different time horizons)
4. Hedging opportunities

Return JSON:
{{
    "arbitrage_opportunities": [
        {{
            "type": "CROSS_PLATFORM" | "RELATED_MARKET" | "TEMPORAL" | "HEDGE",
            "description": "Clear description",
            "kalshi_market": "market details",
            "polymarket_market": "market details", 
            "edge_percentage": "estimated edge",
            "execution_steps": ["step1", "step2"],
            "risks": ["risk1"],
            "confidence": 0-100
        }}
    ]
}}

Only include opportunities with >2% edge. Be specific about execution."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
```

### 2. Update Pattern Engine to Use AI Agent

Modify `services/pattern_engine.py`:

```python
from services.ai_agent import MarketAnalysisAgent

class PatternEngine:
    def __init__(self):
        self.ai_agent = MarketAnalysisAgent()
        # ... existing code
    
    def analyze_with_ai(self, detected_patterns: List[Dict], market_data: Dict) -> Dict:
        """
        Take rule-based detected patterns and enhance with AI analysis.
        """
        # Rule-based detection flags WHAT happened
        # AI agent explains WHY it matters and WHAT to do
        
        ai_insight = self.ai_agent.analyze_opportunity(
            market_data=market_data,
            historical_patterns=detected_patterns
        )
        
        return {
            "pattern_data": detected_patterns,
            "ai_analysis": ai_insight,
            "actionable": ai_insight["confidence_score"] > 60
        }
```

### 3. Update Data Collector to Trigger AI Analysis

In `services/data_collector.py`, after collecting data:

```python
async def collect_and_analyze(self):
    # Existing collection code...
    kalshi_data = await self.kalshi_client.get_markets()
    polymarket_data = await self.polymarket_client.get_markets()
    
    # Rule-based pattern detection (existing)
    patterns = self.pattern_engine.detect_patterns(kalshi_data, polymarket_data)
    
    # NEW: AI-powered analysis on detected patterns
    for pattern in patterns:
        if pattern["score"] > 50:  # Only analyze promising patterns
            ai_insight = self.ai_agent.analyze_opportunity(
                market_data=pattern["market_data"],
                historical_patterns=[pattern]
            )
            pattern["ai_analysis"] = ai_insight
    
    # NEW: Cross-platform arbitrage analysis
    arbitrage = self.ai_agent.analyze_cross_platform_arbitrage(
        kalshi_data, polymarket_data
    )
    
    # Store enhanced insights
    await self.store_insights(patterns, arbitrage)
```

### 4. New API Endpoint for AI Insights

Add to your routes:

```python
@app.get("/api/v1/insights/ai")
@require_subscription(min_tier="basic")
async def get_ai_insights(
    category: Optional[str] = None,
    tier: str = Depends(get_user_tier)
):
    """
    Get AI-powered insights based on subscription tier.
    """
    insights = await db.get_latest_ai_insights(category=category)
    
    # Tier-based filtering
    if tier == "basic":
        # Daily digest only, top 5 picks
        return {
            "insights": insights[:5],
            "refresh": "daily",
            "upgrade_prompt": "Get real-time alerts with Premium"
        }
    elif tier == "premium":
        # All insights + arbitrage
        return {
            "insights": insights,
            "arbitrage": await db.get_arbitrage_opportunities(),
            "refresh": "hourly"
        }
    elif tier == "pro":
        # Everything + custom analysis
        return {
            "insights": insights,
            "arbitrage": await db.get_arbitrage_opportunities(),
            "deep_analysis": await db.get_deep_analysis(),
            "refresh": "real-time"
        }
```

### 5. Environment Variables for Railway

Add to Railway environment:

```
GROQ_API_KEY=your_groq_key_here
AI_ANALYSIS_ENABLED=true
AI_MODEL=gpt-oss-20b-128k
```

**Model Options (set AI_MODEL to one of these):**
| Model | Speed | Cost (input/output per M) | Use Case |
|-------|-------|---------------------------|----------|
| `gpt-oss-20b-128k` | 1000 TPS | $0.075 / $0.30 | DEFAULT - fastest, cheapest |
| `qwen3-32b-131k` | 662 TPS | $0.29 / $0.59 | Good balance |
| `llama-4-scout-17bx16e-128k` | 594 TPS | $0.11 / $0.34 | Newer Llama |
| `llama-3.3-70b-versatile` | 394 TPS | $0.59 / $0.79 | Only if quality issues |

### 6. Database Schema Update

Add table for AI insights:

```sql
CREATE TABLE ai_insights (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(255),
    platform VARCHAR(50),
    pattern_type VARCHAR(100),
    ai_recommendation VARCHAR(50),
    confidence_score INTEGER,
    one_liner TEXT,
    reasoning TEXT,
    risk_factors JSONB,
    edge_explanation TEXT,
    time_sensitivity VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE TABLE arbitrage_opportunities (
    id SERIAL PRIMARY KEY,
    opportunity_type VARCHAR(50),
    kalshi_market_id VARCHAR(255),
    polymarket_market_id VARCHAR(255),
    edge_percentage DECIMAL(5,2),
    execution_steps JSONB,
    confidence_score INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active'
);
```

---

## Performance Architecture

**Where performance actually matters for USER experience:**
1. **API response time** - How fast users get insights (solved by Redis cache)
2. **Database query speed** - Fallback when cache misses (solved by proper indexing)

**What does NOT affect user experience:**
- Groq/AI inference latency - Runs in background, users pull pre-computed results
- Data collection speed - Background job, not user-facing
- External API rate limits - Background job problem, not user problem

Users never wait for AI inference. They fetch pre-computed insights from DB/cache.

---

## Hybrid Architecture: Home Server + Railway

Run background jobs (data collection + Groq API calls) from a home machine. Railway only hosts the API and database. Saves ~$10-15/mo in Railway compute.

```
┌─────────────────────────────────────────────────────────────┐
│              YOUR HOME SERVER (Jetson/PC/anything)          │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Cron: Data  │───▶│ Cron: Call  │───▶│ Push to     │     │
│  │ Collection  │    │ Groq API    │    │ Railway DB  │     │
│  │ (15 min)    │    │ (15 min)    │    │             │     │
│  └─────────────┘    └─────────────┘    └──────┬──────┘     │
│        │                   │                   │            │
│        ▼                   ▼                   │            │
│  Kalshi/Poly APIs     Groq Cloud              │            │
└───────────────────────────────────────────────┼────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAILWAY (Production)                     │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ PostgreSQL  │◀───│ API Server  │───▶│ Redis       │     │
│  │ + Timescale │    │ (FastAPI)   │    │ Cache       │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                            │                                │
└────────────────────────────┼────────────────────────────────┘
                             │
                             ▼
                         Users/App
```

### Cost Comparison

| Setup | Monthly Cost |
|-------|--------------|
| **Full Railway** (API + DB + Redis + 2 cron services + Groq) | ~$40-55/mo |
| **Hybrid** (Railway API + DB + Redis, home server runs jobs + Groq) | ~$25-35/mo |

### Home Server Setup

Any machine that stays on - old laptop, Raspberry Pi 4, Jetson, mini PC, NAS, whatever.

**1. Clone repo and install:**
```bash
git clone https://github.com/yourrepo/oddwons-jobs.git
cd oddwons-jobs
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Environment variables (`.env`):**
```bash
# Railway PostgreSQL - use PUBLIC URL (TCP proxy)
DATABASE_URL=postgresql://postgres:xxxxx@roundhouse.proxy.rlwy.net:12345/railway

# Groq
GROQ_API_KEY=gsk_xxxxxxxxxxxx
AI_MODEL=gpt-oss-20b-128k

# Optional: Redis for cache invalidation
REDIS_URL=redis://default:xxxxx@roundhouse.proxy.rlwy.net:23456
```

**3. Set up cron (`crontab -e`):**
```bash
# Data collection - every 15 minutes
*/15 * * * * cd /home/user/oddwons-jobs && ./venv/bin/python collect_data.py >> /var/log/oddwons/collect.log 2>&1

# AI analysis - every 15 minutes, offset by 5 min (runs after data is collected)
5,20,35,50 * * * * cd /home/user/oddwons-jobs && ./venv/bin/python run_analysis.py >> /var/log/oddwons/analysis.log 2>&1
```

**4. Or use systemd timer (more robust):**
```bash
# /etc/systemd/system/oddwons-collect.service
[Unit]
Description=Oddwons Data Collection

[Service]
Type=oneshot
WorkingDirectory=/home/user/oddwons-jobs
ExecStart=/home/user/oddwons-jobs/venv/bin/python collect_data.py
EnvironmentFile=/home/user/oddwons-jobs/.env
```

```bash
# /etc/systemd/system/oddwons-collect.timer
[Unit]
Description=Run data collection every 15 min

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable --now oddwons-collect.timer
```

### Database Connection: Home vs Railway

**From Railway services (private network, no egress cost):**
```
DATABASE_URL=postgresql://postgres:xxx@postgres.railway.internal:5432/railway
```

**From home server (public TCP proxy, small egress cost):**
```
DATABASE_URL=postgresql://postgres:xxx@roundhouse.proxy.rlwy.net:12345/railway
```

Egress is $0.05/GB. Pushing insights is ~KB per run = pennies/month.

### Failover Options

| Option | Setup | Cost |
|--------|-------|------|
| Railway cron as backup | Keep services deployed but scaled to 0, enable if home fails | $0 until used |
| Cheap VPS fallback | Hetzner/DigitalOcean $5/mo droplet | $5/mo |
| Just accept gaps | Miss a few 15-min windows, users won't notice | $0 |

---

### TimescaleDB (Use This)

TimescaleDB is a PostgreSQL extension for time-series data. Railway supports it. This is how you handle millions of market snapshots without breaking a sweat.

**Install extension and create hypertable:**
```sql
-- Enable TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Main market data table
CREATE TABLE market_snapshots (
    time TIMESTAMPTZ NOT NULL,
    market_id VARCHAR(255) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    price DECIMAL(10,4),
    volume BIGINT,
    yes_price DECIMAL(10,4),
    no_price DECIMAL(10,4),
    raw_data JSONB
);

-- Convert to hypertable (auto-partitions by time, 10-100x faster queries)
SELECT create_hypertable('market_snapshots', 'time');

-- Auto-compress data older than 7 days (90% storage reduction)
ALTER TABLE market_snapshots SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'market_id, platform'
);
SELECT add_compression_policy('market_snapshots', INTERVAL '7 days');
```

**Continuous Aggregates (pre-computed rollups):**
```sql
-- Hourly OHLCV candles, computed automatically
CREATE MATERIALIZED VIEW market_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    market_id,
    platform,
    FIRST(price, time) as open,
    MAX(price) as high,
    MIN(price) as low,
    LAST(price, time) as close,
    SUM(volume) as volume,
    COUNT(*) as num_snapshots
FROM market_snapshots
GROUP BY bucket, market_id, platform;

-- Auto-refresh every 15 minutes
SELECT add_continuous_aggregate_policy('market_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '15 minutes'
);

-- Daily summary for historical analysis
CREATE MATERIALIZED VIEW market_daily
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', time) AS bucket,
    market_id,
    platform,
    FIRST(price, time) as open,
    MAX(price) as high,
    MIN(price) as low,
    LAST(price, time) as close,
    SUM(volume) as total_volume,
    AVG(price) as avg_price
FROM market_snapshots
GROUP BY bucket, market_id, platform;

SELECT add_continuous_aggregate_policy('market_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 hour'
);
```

### Proper Indexing

```sql
-- Compound indexes for common query patterns
CREATE INDEX idx_snapshots_market_time ON market_snapshots (market_id, time DESC);
CREATE INDEX idx_snapshots_platform_time ON market_snapshots (platform, time DESC);

-- Partial index for "hot" data (only recent, smaller index)
CREATE INDEX idx_snapshots_recent ON market_snapshots (market_id, time DESC)
WHERE time > NOW() - INTERVAL '24 hours';

-- GIN index for JSONB queries
CREATE INDEX idx_snapshots_raw_gin ON market_snapshots USING GIN (raw_data);

-- AI insights - query by confidence and recency
CREATE INDEX idx_insights_actionable ON ai_insights (confidence_score DESC, created_at DESC)
WHERE confidence_score > 60;

-- Arbitrage - active opportunities only
CREATE INDEX idx_arbitrage_active ON arbitrage_opportunities (created_at DESC)
WHERE status = 'active';
```

### Connection Pooling (Critical)

Without pooling, Railway PostgreSQL will hit connection limits under load.

**Application-level pooling with SQLAlchemy:**
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    os.environ["DATABASE_URL"],
    poolclass=QueuePool,
    pool_size=5,           # Connections to keep open
    max_overflow=10,       # Extra connections under load  
    pool_timeout=30,       # Wait time for connection
    pool_recycle=1800,     # Recycle connections every 30 min
    pool_pre_ping=True,    # Verify connection before use
)
```

**Async with asyncpg (faster):**
```python
import asyncpg

class Database:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        self.pool = await asyncpg.create_pool(
            os.environ["DATABASE_URL"],
            min_size=5,
            max_size=20,
            command_timeout=60,
        )
    
    async def fetch_insights(self, category: str):
        async with self.pool.acquire() as conn:
            return await conn.fetch("""
                SELECT * FROM ai_insights 
                WHERE category = $1 AND confidence_score > 70
                ORDER BY created_at DESC LIMIT 10
            """, category)
```

### Redis Caching Layer

Database for storage, Redis for speed. Cache everything users hit frequently.

```python
import redis
import json
from functools import wraps

r = redis.from_url(os.environ["REDIS_URL"] + "?family=0")

def cache(ttl_seconds: int = 300):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function name + args
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Check cache
            cached = r.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Cache miss - execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            r.setex(cache_key, ttl_seconds, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator

# Usage
@cache(ttl_seconds=300)  # 5 minute cache
async def get_top_insights(category: str):
    return await db.fetch_insights(category)

@cache(ttl_seconds=60)   # 1 minute cache (fresher data)
async def get_latest_arbitrage():
    return await db.fetch_arbitrage()
```

**Cache latest prices (update every collection cycle):**
```python
async def cache_latest_prices(markets: list):
    """Bulk cache market prices - called by data collector"""
    pipe = r.pipeline()
    for m in markets:
        pipe.hset(f"price:{m['platform']}:{m['market_id']}", mapping={
            "price": str(m["price"]),
            "volume": str(m["volume"]),
            "updated": m["timestamp"].isoformat()
        })
        pipe.expire(f"price:{m['platform']}:{m['market_id']}", 900)  # 15 min TTL
    pipe.execute()  # Single round-trip for all writes

def get_cached_price(platform: str, market_id: str) -> dict:
    """Get price from cache - <1ms"""
    data = r.hgetall(f"price:{platform}:{market_id}")
    if data:
        return {k.decode(): v.decode() for k, v in data.items()}
    return None
```

**Cache invalidation on new analysis:**
```python
async def invalidate_insights_cache(category: str = None):
    """Call after AI analyzer runs"""
    if category:
        # Delete specific category cache
        for key in r.scan_iter(f"get_top_insights:*{category}*"):
            r.delete(key)
    else:
        # Nuclear option - clear all insight caches
        for key in r.scan_iter("get_top_insights:*"):
            r.delete(key)
```

### Request Flow Architecture

```
User Request: GET /api/v1/insights?category=politics
    │
    ▼
┌─────────────────┐
│  Redis Cache    │ ◄── HIT? Return instantly (<1ms)
└────────┬────────┘
         │ MISS
         ▼
┌─────────────────┐
│  PostgreSQL +   │ ◄── Query with indexes (~5-50ms)
│  TimescaleDB    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Cache Result    │ ◄── Store in Redis with TTL
└────────┬────────┘
         │
         ▼
    Return to User (total: ~50-100ms first request, <1ms cached)
```

```
Background: Data Collection (every 15 min)
    │
    ▼
┌─────────────────┐
│ Kalshi API      │ ◄── Fetch markets (~500ms-2s)
│ Polymarket API  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PostgreSQL      │ ◄── Bulk insert (~50ms for 1000 rows)
│ Bulk Insert     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Redis           │ ◄── Update price cache
│ Price Cache     │
└─────────────────┘
```

```
Background: AI Analysis (every 15 min, offset)
    │
    ▼
┌─────────────────┐
│ PostgreSQL      │ ◄── Fetch recent data (~10ms)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Pattern         │ ◄── Rule-based detection (~50ms)
│ Detection       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Groq API        │ ◄── AI analysis (~100-500ms PER CALL) ⚠️ BOTTLENECK
│ (GPT OSS 20B)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PostgreSQL      │ ◄── Store insights (~10ms)
│ Store Insights  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Invalidate      │ ◄── Clear stale cache
│ Redis Cache     │
└─────────────────┘
```

### Realistic Performance Numbers

With proper setup (TimescaleDB + indexes + Redis + connection pooling):

| Operation | Expected Latency |
|-----------|------------------|
| Insert 1000 market snapshots | ~50ms |
| Query latest price (Redis) | <1ms |
| Query latest price (DB fallback) | ~5ms |
| Query 24h price history | ~10ms |
| Query insights by category (cached) | <1ms |
| Query insights by category (uncached) | ~20ms |
| Pattern detection across all markets | ~100-500ms |
| AI analysis per opportunity | ~100-500ms ⚠️ |
| Full-text search markets | ~20ms |
| Bulk insert + cache update | ~100ms |

**Your actual bottleneck: Groq API at 100-500ms per call.**

To analyze 50 markets = 50 × 300ms = 15 seconds of AI time. 
This is why we batch and run in background, not on user request.

### Scaling Path

| Stage | Users | Setup |
|-------|-------|-------|
| **MVP** | 0-1,000 | Railway PostgreSQL + TimescaleDB + Redis |
| **Growth** | 1,000-10,000 | Add read replica (Supabase/Neon) |
| **Scale** | 10,000+ | Dedicated Postgres cluster, Redis cluster, CDN |

**Don't pre-optimize.** Railway PostgreSQL handles way more than you think. Optimize when you have the problem, not before.

---

## Cost Estimate (Groq with GPT OSS 20B)

- GPT OSS 20B: $0.075/million input tokens, $0.30/million output tokens
- Analyzing 100 markets/day: ~$0.05-0.15/day
- Analyzing 500 markets/day: ~$0.25-0.50/day
- **Monthly cost at scale: $5-15/month**
- INSANELY cheap for the value delivered

---

## Priority Order

1. **Create `services/ai_agent.py`** - The core AI brain
2. **Update pattern_engine.py** - Integrate AI with existing detection
3. **Add database tables** - Store AI insights
4. **Update API routes** - Expose AI insights by tier
5. **Test end-to-end** - Collect → Detect → AI Analyze → Store → Serve

---

## What This Delivers

BEFORE (rule-based):
> "Volume spike detected on market X"

AFTER (AI-powered):
> "STRONG_BET: Trump Iowa market at 62¢ is mispriced. Historical pattern shows 8% edge when volume spikes like this occur 48hrs before polling data releases. Similar setups have hit 73% of the time. Position: YES. Act within 6 hours before market corrects."

THAT is what people pay for.

---

## LOCAL DEV SETUP

Everything runs on your machine. No Railway needed until you ship.

### Docker Compose

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    container_name: oddwons-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: oddwons
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: oddwons-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

### Environment Variables

Create `.env` in project root:

```bash
# Database (local Docker)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/oddwons

# Redis (local Docker)
REDIS_URL=redis://localhost:6379

# Groq (get key from console.groq.com)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
AI_MODEL=gpt-oss-20b-128k
AI_ANALYSIS_ENABLED=true

# App
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SECRET_KEY=dev-secret-key-change-in-prod

# Stripe (test mode keys)
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxx
```

### Start Everything

```bash
# 1. Start Postgres + Redis
docker-compose up -d

# 2. Verify containers running
docker-compose ps

# 3. Run database migrations
alembic upgrade head

# 4. Start API server
uvicorn app.main:app --reload --port 8000

# 5. (In another terminal) Run data collection manually
python collect_data.py

# 6. (In another terminal) Run AI analysis manually
python run_analysis.py
```

### Test the Flow

```bash
# 1. Check API is running
curl http://localhost:8000/health

# 2. Trigger data collection
python collect_data.py

# 3. Verify data in DB
docker exec -it oddwons-postgres psql -U postgres -d oddwons -c "SELECT COUNT(*) FROM market_snapshots;"

# 4. Run AI analysis
python run_analysis.py

# 5. Verify insights generated
docker exec -it oddwons-postgres psql -U postgres -d oddwons -c "SELECT * FROM ai_insights LIMIT 5;"

# 6. Test API endpoint (need valid JWT token)
curl http://localhost:8000/api/v1/insights/ai \
  -H "Authorization: Bearer <your_test_token>"
```

### Quick DB Access

```bash
# Connect to Postgres
docker exec -it oddwons-postgres psql -U postgres -d oddwons

# Useful queries:
\dt                                    # List tables
SELECT COUNT(*) FROM market_snapshots; # Count snapshots
SELECT * FROM ai_insights LIMIT 5;     # View insights
SELECT * FROM arbitrage_opportunities WHERE status = 'active';
```

### Reset Everything

```bash
# Stop containers
docker-compose down

# Stop AND delete data
docker-compose down -v

# Start fresh
docker-compose up -d
alembic upgrade head
```

### Run Background Jobs Locally

For dev, just run manually or use a simple loop:

```bash
# Manual (run when needed)
python collect_data.py
python run_analysis.py

# Or: Simple watch loop (runs every 60 seconds)
watch -n 60 'python collect_data.py && python run_analysis.py'

# Or: Proper local cron (crontab -e)
* * * * * cd /path/to/project && /path/to/venv/bin/python collect_data.py
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| `connection refused` on Postgres | `docker-compose up -d` - container not running |
| `relation does not exist` | `alembic upgrade head` - migrations not run |
| `GROQ_API_KEY not set` | Check `.env` file, restart terminal |
| `redis connection error` | Check Redis container: `docker-compose logs redis` |
| Port 5432 already in use | Stop local Postgres or change port in docker-compose |

---

## PRODUCTION DEPLOYMENT ON RAILWAY

This is NOT a local hero app. It ships to production properly. Here's the comprehensive Railway deployment guide.

### Railway Plan Selection

| Plan | Cost | RAM | CPU | Volume | Use Case |
|------|------|-----|-----|--------|----------|
| **Free** | $0/mo | 0.5 GB | 1 vCPU | 0.5 GB | DON'T USE - services stop when credits run out |
| **Hobby** | $5/mo (+$5 credit) | 8 GB | 8 vCPU | 5 GB | Testing only |
| **Pro** | $20/mo (+$20 credit) | 32 GB | 32 vCPU | 50 GB | **USE THIS FOR PRODUCTION** |
| **Enterprise** | Custom | 48 GB | 64 vCPU | 2 TB | If you scale past Pro limits |

**Resource Pricing (on top of subscription):**
- RAM: $10/GB/month ($0.000231/GB/minute)
- CPU: $20/vCPU/month ($0.000463/vCPU/minute)
- Network Egress: $0.05/GB
- Volume Storage: $0.15/GB/month

**CRITICAL:** Free/Hobby plans will STOP your services if credits run out. Pro plan is mandatory for production.

---

### Multi-Service Architecture

Railway services needed (depends on your setup):

**Option A: Full Railway (everything on Railway)**
```
Railway Project: oddwons-production
├── api-server          (FastAPI - main API)          REQUIRED
├── data-collector      (Cron job - collects data)    REQUIRED
├── ai-analyzer         (Cron job - Groq analysis)    REQUIRED
├── postgres            (Database)                     REQUIRED
├── redis               (Cache)                        REQUIRED
└── frontend            (Next.js - optional, can use Vercel)
```

**Option B: Hybrid (home server runs background jobs)**
```
Railway Project: oddwons-production
├── api-server          (FastAPI - main API)          REQUIRED
├── postgres            (Database)                     REQUIRED
├── redis               (Cache)                        REQUIRED
└── frontend            (optional)

Home Server:
├── collect_data.py     (Cron - every 15 min)
└── run_analysis.py     (Cron - every 15 min, offset)
```

**Option B is cheaper** - saves ~$10-15/mo by not running cron services on Railway.

---

### Service 1: PostgreSQL Database

**Setup:**
1. In Railway project, right-click → Database → Add PostgreSQL
2. Railway auto-provisions and creates `DATABASE_URL` variable
3. Database automatically gets a volume for persistent storage

**Configuration:**
```
# Railway auto-generates these in the postgres service:
DATABASE_URL=postgresql://postgres:xxx@postgres.railway.internal:5432/railway
PGHOST=postgres.railway.internal
PGPORT=5432
PGUSER=postgres
PGPASSWORD=xxx
PGDATABASE=railway
```

**Connect from other services using shared variables:**
```
# In api-server service, add shared variable:
DATABASE_URL=${{postgres.DATABASE_URL}}
```

**Backups:** Enable Railway's native backup feature in database settings.

---

### Service 2: Redis

**Setup:**
1. Right-click → Database → Add Redis
2. Railway creates `REDIS_URL` variable

**CRITICAL for Private Networking:**
Redis requires `family=0` in connection string for IPv6/IPv4 dual-stack:

```python
# In your Python code:
import redis

# WRONG - will fail on Railway private network
# redis_client = redis.from_url(os.environ["REDIS_URL"])

# CORRECT - works with Railway private networking
redis_url = os.environ["REDIS_URL"]
if "?" in redis_url:
    redis_url += "&family=0"
else:
    redis_url += "?family=0"
redis_client = redis.from_url(redis_url)
```

**Shared variable for other services:**
```
REDIS_URL=${{redis.REDIS_URL}}?family=0
```

---

### Service 3: API Server (FastAPI)

**railway.json** (place in repo root or `/api` folder):
```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 120,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "numReplicas": 2
  }
}
```

**Required health endpoint:**
```python
@app.get("/health")
async def health_check():
    # Check database connection
    try:
        await db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
```

**Environment Variables (set in Railway dashboard):**
```
DATABASE_URL=${{postgres.DATABASE_URL}}
REDIS_URL=${{redis.REDIS_URL}}?family=0
GROQ_API_KEY=gsk_xxxxxxxxxxxx
AI_MODEL=gpt-oss-20b-128k
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxx
JWT_SECRET=your-256-bit-secret
ENVIRONMENT=production
```

**IMPORTANT:** Use Railway's "Sealed" option for sensitive variables (GROQ_API_KEY, STRIPE keys, JWT_SECRET). Sealed variables are encrypted and hidden from logs.

---

### Service 4: Data Collector (Cron Job)

**CRITICAL DIFFERENCE:** Cron services on Railway MUST exit after completion. They cannot be long-running processes with APScheduler.

**railway.json** for data-collector:
```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python collect_data.py",
    "cronSchedule": "*/15 * * * *",
    "restartPolicyType": "NEVER"
  }
}
```

**collect_data.py** (runs, collects, exits):
```python
import asyncio
import sys
from services.kalshi_client import KalshiClient
from services.polymarket_client import PolymarketClient
from services.database import Database

async def main():
    try:
        db = Database(os.environ["DATABASE_URL"])
        kalshi = KalshiClient()
        polymarket = PolymarketClient()
        
        # Collect data
        kalshi_markets = await kalshi.get_all_markets()
        poly_markets = await polymarket.get_all_markets()
        
        # Store in database
        await db.store_market_snapshot(kalshi_markets, "kalshi")
        await db.store_market_snapshot(poly_markets, "polymarket")
        
        print(f"Collected {len(kalshi_markets)} Kalshi, {len(poly_markets)} Polymarket markets")
        
        # Close connections
        await db.close()
        
        # EXIT CLEANLY - required for Railway cron
        sys.exit(0)
        
    except Exception as e:
        print(f"Collection failed: {e}")
        sys.exit(1)  # Non-zero exit triggers restart policy

if __name__ == "__main__":
    asyncio.run(main())
```

**Cron Schedule Examples:**
- `*/15 * * * *` - Every 15 minutes
- `0 * * * *` - Every hour
- `0 */6 * * *` - Every 6 hours
- `0 8 * * *` - Daily at 8 AM UTC

---

### Service 5: AI Analyzer (Cron Job)

**railway.json** for ai-analyzer:
```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python run_analysis.py",
    "cronSchedule": "5,20,35,50 * * * *",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

**run_analysis.py:**
```python
import asyncio
import sys
from services.ai_agent import MarketAnalysisAgent
from services.database import Database

async def main():
    try:
        db = Database(os.environ["DATABASE_URL"])
        agent = MarketAnalysisAgent()
        
        # Get recent market data from database
        recent_data = await db.get_recent_market_data(hours=1)
        
        # Detect patterns
        patterns = detect_patterns(recent_data)
        
        # AI analysis on promising patterns
        for pattern in patterns:
            if pattern["score"] > 50:
                ai_insight = agent.analyze_opportunity(
                    market_data=pattern["market_data"],
                    historical_patterns=[pattern]
                )
                await db.store_ai_insight(ai_insight)
        
        # Cross-platform arbitrage
        kalshi_data = [m for m in recent_data if m["platform"] == "kalshi"]
        poly_data = [m for m in recent_data if m["platform"] == "polymarket"]
        
        arbitrage = agent.analyze_cross_platform_arbitrage(kalshi_data, poly_data)
        await db.store_arbitrage_opportunities(arbitrage)
        
        await db.close()
        print(f"Analysis complete. {len(patterns)} patterns analyzed.")
        sys.exit(0)
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Private Networking

All services in the same Railway project/environment can communicate over private network (no egress charges).

**Private DNS format:**
```
<service-name>.railway.internal
```

**Example:**
```python
# API server connecting to postgres over private network
DATABASE_URL=postgresql://postgres:xxx@postgres.railway.internal:5432/railway

# NOT this (public, charged for egress)
DATABASE_URL=postgresql://postgres:xxx@roundhouse.proxy.rlwy.net:12345/railway
```

**IMPORTANT:** Private network is only for server-to-server. Client-side requests (browser) must use public URLs.

---

### Healthchecks & Restart Policies

**Railway healthchecks are deployment-time only** - they verify the new deployment is healthy before routing traffic. They do NOT continuously monitor.

**For continuous monitoring, deploy Uptime Kuma:**
```
Railway Templates → Search "Uptime Kuma" → Deploy
```

**Restart Policy Options:**
| Policy | Behavior |
|--------|----------|
| `NEVER` | Don't restart (use for cron jobs) |
| `ON_FAILURE` | Restart on non-zero exit (DEFAULT, max 10) |
| `ALWAYS` | Always restart (use for workers) |

**Set max retries:**
```json
{
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

### High Availability Setup

**Replicas** (Pro plan required):
```json
{
  "deploy": {
    "numReplicas": 2
  }
}
```

With 2+ replicas:
- Traffic load-balanced across instances
- If one crashes, others handle requests while it restarts
- Zero-downtime deployments

**Database HA:**
Railway's managed PostgreSQL is single-node. For true HA:
- Use Railway PostgreSQL for MVP
- Graduate to Supabase, Neon, or AWS RDS for production scale

---

### Complete Environment Variables

**API Server Service:**
```
# Database
DATABASE_URL=${{postgres.DATABASE_URL}}

# Cache
REDIS_URL=${{redis.REDIS_URL}}?family=0

# AI
GROQ_API_KEY=gsk_xxxxxxxxxxxx          # SEAL THIS
AI_MODEL=gpt-oss-20b-128k
AI_ANALYSIS_ENABLED=true

# Auth
JWT_SECRET=your-256-bit-secret          # SEAL THIS
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stripe
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxx  # SEAL THIS
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxx # SEAL THIS
STRIPE_PRICE_BASIC=price_xxxxxxxxxxxx
STRIPE_PRICE_PREMIUM=price_xxxxxxxxxxxx
STRIPE_PRICE_PRO=price_xxxxxxxxxxxx

# App
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://oddwons.ai,https://www.oddwons.ai

# Railway auto-injects
PORT                    # Railway sets this
RAILWAY_ENVIRONMENT     # production/staging
RAILWAY_SERVICE_NAME    # service name
```

**Data Collector & AI Analyzer Services:**
```
DATABASE_URL=${{postgres.DATABASE_URL}}
REDIS_URL=${{redis.REDIS_URL}}?family=0
GROQ_API_KEY=${{api-server.GROQ_API_KEY}}  # Reference from main service
AI_MODEL=gpt-oss-20b-128k
ENVIRONMENT=production
```

---

### Deployment Workflow

**1. Initial Setup:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create project
railway init

# Link to existing project
railway link
```

**2. Deploy from GitHub (recommended):**
- Connect GitHub repo in Railway dashboard
- Enable auto-deploy on push to `main`
- PR previews auto-deploy to staging environment

**3. Manual Deploy:**
```bash
railway up
```

**4. View Logs:**
```bash
railway logs
```

**5. Open Shell:**
```bash
railway shell
```

---

### Staging Environment

Railway supports multiple environments per project:

```
oddwons-production/
├── production/     (main branch)
│   ├── api-server
│   ├── postgres
│   └── ...
└── staging/        (develop branch)
    ├── api-server
    ├── postgres
    └── ...
```

**Setup:**
1. Project Settings → Environments → Create Environment
2. Name it "staging"
3. Link to `develop` branch
4. Each environment has isolated databases and variables

---

### Cost Estimate

**Option A: Full Railway**

| Service | RAM | CPU | Hours/Month | Cost |
|---------|-----|-----|-------------|------|
| API Server (2 replicas) | 512MB × 2 | 0.5 vCPU × 2 | 730 | ~$15 |
| PostgreSQL | 256MB | 0.25 vCPU | 730 | ~$5 |
| Redis | 128MB | 0.1 vCPU | 730 | ~$2 |
| Data Collector (cron) | 256MB | 0.5 vCPU | ~50 | ~$1 |
| AI Analyzer (cron) | 512MB | 0.5 vCPU | ~50 | ~$2 |
| **Railway Subtotal** | | | | **~$25** |
| Network Egress (~10GB) | | | | ~$0.50 |
| Groq AI | | | | ~$5-15 |
| **Total** | | | | **~$35-45/month** |

**Option B: Hybrid (Home Server runs jobs)**

| Service | RAM | CPU | Hours/Month | Cost |
|---------|-----|-----|-------------|------|
| API Server (2 replicas) | 512MB × 2 | 0.5 vCPU × 2 | 730 | ~$15 |
| PostgreSQL | 256MB | 0.25 vCPU | 730 | ~$5 |
| Redis | 128MB | 0.1 vCPU | 730 | ~$2 |
| **Railway Subtotal** | | | | **~$22** |
| Network Egress (~10GB) | | | | ~$0.50 |
| Groq AI | | | | ~$5-15 |
| Home server electricity | | | | ~$2-5 |
| **Total** | | | | **~$25-40/month** |

**Savings with Hybrid: ~$5-10/month** (more if you scale up cron frequency)

**Other Costs (both options):**
- Domain (oddwons.ai): ~$15/year
- Stripe fees: 2.9% + $0.30 per transaction

**Total Infrastructure: ~$35-45/month**

Break-even: ~4 subscribers at $9.99/month

---

### Monitoring & Alerts

**Built-in Railway:**
- Real-time logs
- Basic CPU/RAM/Network metrics
- Deploy status notifications

**Recommended Additions:**

1. **Uptime Kuma** (deploy via Railway template):
   - Continuous endpoint monitoring
   - Slack/Discord/Email alerts
   - Status page

2. **Sentry** (error tracking):
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn=os.environ["SENTRY_DSN"])
   ```

3. **PostHog/Plausible** (analytics):
   - User behavior tracking
   - Conversion funnels

---

### Pre-Launch Checklist

```
[ ] Pro plan activated
[ ] All environment variables set
[ ] Sensitive variables sealed
[ ] Health endpoints working
[ ] Private networking configured (no public DB access)
[ ] PostgreSQL backups enabled
[ ] 2+ replicas on API server
[ ] Custom domain configured (oddwons.ai)
[ ] SSL auto-provisioned (Railway handles this)
[ ] Staging environment tested
[ ] Uptime monitoring deployed
[ ] Error tracking (Sentry) configured
[ ] Stripe webhooks pointed to production URL
[ ] CORS configured for production domain
```

---

## DO NOT

- Skip the AI integration and ship rule-based garbage
- Overcomplicate with MCP servers
- Add unnecessary abstractions
- Wait for "Phase 5" - this IS the product
- Deploy to Free/Hobby tier for production (services WILL stop)
- Use APScheduler for cron jobs on Railway (use Railway's native cron)
- Expose database to public internet (use private networking)
- Forget to seal sensitive environment variables
- Run single replica in production (no HA)

The scaffolding is done. Now build the actual value prop and ship it.
