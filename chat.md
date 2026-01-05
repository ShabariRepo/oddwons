# FRONTEND ISSUES - ALL RESOLVED

## Status: ALL COMPLETE (Jan 2026)

All critical issues have been fixed and deployed.

---

## Issue 1: Showing RESOLVED Markets - FIXED

**What was fixed:**
- Added `WHERE yes_price > 0.02 AND yes_price < 0.98` filter to:
  - `GET /api/v1/markets` endpoint
  - `GET /api/v1/insights/ai` endpoint (with join to markets table)
  - `GET /api/v1/cross-platform/matches` endpoint
- Ran SQL to update 88,459 markets to 'resolved' and 3,184 to 'closed'

---

## Issue 2: Cross-Platform Data Not Loading - FIXED

**What was fixed:**
- Updated `app/api/routes/cross_platform.py` `/matches` endpoint to return:
  ```json
  {"matches": [...], "total": N, "total_volume": N}
  ```
- Added fields: `kalshi_yes_price`, `polymarket_yes_price`, `gap_direction`, `similarity_score`
- Fixed `/stats` endpoint to return `avg_price_gap` field

---

## Issue 3: No Kalshi Markets Showing - INVESTIGATED

**Finding:**
- Kalshi markets exist (13,265 active) but rank lower by volume
- Polymarket has higher individual market volumes
- This is expected behavior, not a bug
- AI insights only have Polymarket data (generation issue, not display)

---

## Issue 4: Status Field Not Updated - FIXED

**What was fixed:**
- Ran SQL migration:
  - 88,459 markets -> 'resolved' (yes_price < 0.02 OR > 0.98)
  - 3,184 markets -> 'closed' (close_time in past)

---

## Issue 5: Wrong Language - FIXED

**Files updated:**
- `frontend/src/app/(public)/page.tsx` - Hero, features, tiers, CTA
- `frontend/src/app/register/page.tsx` - Testimonial, features
- `frontend/src/app/(app)/settings/page.tsx` - Tier descriptions, notification labels
- `frontend/src/lib/types.ts` - Pattern labels (Arb -> Gap)
- Deleted unused `frontend/src/components/OpportunityCard.tsx`

**Language changes:**
- "opportunity" -> "highlight", "insight"
- "arbitrage" -> "price comparison", "price gap"
- "Cross-Platform Arb" -> "Cross-Platform Gap"

---

## Commits

1. `7fce4f7` - Update language from 'opportunity/arbitrage' to 'highlight/comparison'
2. Previous session commits for API fixes and resolved market filtering

All changes pushed to main branch.
