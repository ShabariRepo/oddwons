# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OddWons is a subscription-based prediction market analysis app that analyzes Kalshi and Polymarket markets using AI agents to identify betting opportunities, patterns, and market inefficiencies.

## API Integration

### Kalshi API
- Base URL: `https://api.elections.kalshi.com/trade-api/v2`
- Key endpoints: `/markets`, `/markets/trades`, `/events`
- WebSocket available for real-time streaming

### Polymarket API
- Gamma API: `https://gamma-api.polymarket.com/events` (market discovery)
- CLOB API: `https://clob.polymarket.com/` (pricing, orderbook)
- GraphQL subgraph available for aggregate queries
- WebSocket for real-time orderbook updates

### MCP Servers (Recommended Approach)
- Multi-platform: https://www.pulsemcp.com/servers/jamesanz-prediction-markets (covers Kalshi, Polymarket, PredictIt)
- Polymarket Rust: https://github.com/ozgureyilmaz/polymarket-mcp

## Architecture

### Data Strategy
- Batch data collection every 15-30 minutes stored in PostgreSQL
- Batch analysis on stored data (avoids rate limits)
- Real-time monitoring only for premium alert triggers on high-value markets

### Core Components
- **Pattern Detection Engine**: Volume analysis, price movement, arbitrage detection, sentiment analysis
- **Scoring System**: Confidence score, profit potential, time sensitivity, risk assessment (all 0-100 or 1-5 scales)
- **Alert System**: Tier-based thresholds, multi-channel delivery (email, SMS, push, webhooks)

### Subscription Tiers
- Basic ($9.99): Daily digest, top 5 opportunities, email notifications
- Premium ($19.99): Real-time alerts, custom parameters, SMS, Discord/Slack
- Pro ($29.99): Custom analysis, advanced patterns, API access, priority support

## Tech Stack

### Backend
- Node.js/Express.js or Python/FastAPI
- PostgreSQL + Redis
- Bull/BullMQ for background jobs

### Frontend
- React/Next.js or Vue/Nuxt
- Tailwind CSS
- Chart.js or D3.js for visualization

### Infrastructure
- Railway for hosting
- Stripe for payments
- SendGrid/Mailgun for email
- Twilio for SMS

## Development Notes

- Prioritize MCP server integration over direct API implementation
- Design for horizontal scaling from the start
- Implement aggressive caching to handle rate limits
- Keep 6-12 months of historical data for pattern detection
