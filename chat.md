# OddWons - Current Tasks

_Last updated: January 8, 2025_

---

## Production Status ✅

- **Frontend**: https://oddwons.ai
- **Backend**: https://api.oddwons.ai
- **Database**: 801 Kalshi + 1,533 Polymarket markets
- **Data Collection**: Every 15 min via scheduler

---

## TASK 1: SendGrid Email Service

### Create `app/services/email.py`

```python
"""
SendGrid Email Service for OddWons.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Brand colors
BRAND_PRIMARY = "#0ea5e9"
BRAND_DARK = "#0284c7"
BRAND_LIGHT = "#e0f2fe"
BRAND_SUCCESS = "#22c55e"
BRAND_WARNING = "#f59e0b"
BRAND_ERROR = "#ef4444"


def get_base_template(content: str, preview_text: str = "") -> str:
    """Wrap content in branded email template."""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OddWons</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <div style="display: none; max-height: 0; overflow: hidden;">{preview_text}</div>
    
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f3f4f6;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {BRAND_PRIMARY} 0%, {BRAND_DARK} 100%); padding: 32px; text-align: center;">
                            <img src="https://oddwons.ai/oddwons-logo.png" alt="OddWons" width="60" height="60" style="border-radius: 12px; margin-bottom: 12px;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700;">OddWons</h1>
                            <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">Your Prediction Market Companion 🎯</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 32px;">
                            {content}
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 24px 32px; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0 0 8px 0; font-size: 14px; color: #6b7280; text-align: center;">
                                💸 Compare markets • 🧠 AI insights • ⚡ Real-time alerts
                            </p>
                            <p style="margin: 0; font-size: 12px; color: #9ca3af; text-align: center;">
                                © {datetime.now().year} OddWons. All rights reserved.
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def button(text: str, url: str, color: str = BRAND_PRIMARY) -> str:
    return f"""
    <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 24px 0;">
        <tr>
            <td style="background-color: {color}; border-radius: 8px;">
                <a href="{url}" style="display: inline-block; padding: 14px 28px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px;">{text}</a>
            </td>
        </tr>
    </table>
    """


def info_box(content: str, emoji: str = "💡") -> str:
    return f"""
    <div style="background-color: {BRAND_LIGHT}; border-left: 4px solid {BRAND_PRIMARY}; padding: 16px; border-radius: 0 8px 8px 0; margin: 20px 0;">
        <p style="margin: 0; color: #0c4a6e; font-size: 14px;">{emoji} {content}</p>
    </div>
    """


async def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send email via SendGrid."""
    if not settings.sendgrid_api_key:
        logger.warning("SendGrid API key not configured")
        return False
    
    try:
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        message = Mail(
            from_email=Email(settings.from_email, "OddWons"),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        response = sg.send(message)
        logger.info(f"Email sent to {to_email}: {subject}")
        return response.status_code in [200, 201, 202]
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


# AUTH EMAILS
async def send_welcome_email(to_email: str, name: str = None) -> bool:
    display_name = name or to_email.split('@')[0]
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0;">Welcome aboard, {display_name}! 🎉</h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6;">You just joined the smartest prediction market community!</p>
        {info_box("Your 7-day free trial just started. Explore everything!", "🚀")}
        {button("Go to Dashboard", "https://oddwons.ai/dashboard")}
    """
    return await send_email(to_email, "Welcome to OddWons! 🎯", get_base_template(content, f"Welcome {display_name}!"))


async def send_password_reset_email(to_email: str, reset_token: str, name: str = None) -> bool:
    display_name = name or "there"
    reset_url = f"https://oddwons.ai/reset-password?token={reset_token}"
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0;">Reset your password 🔐</h2>
        <p style="color: #4b5563;">Hey {display_name}, click below to set a new password:</p>
        {button("Reset Password", reset_url)}
        {info_box("This link expires in 1 hour.", "⏰")}
    """
    return await send_email(to_email, "Reset your OddWons password", get_base_template(content))


async def send_password_changed_email(to_email: str, name: str = None) -> bool:
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0;">Password changed ✅</h2>
        <p style="color: #4b5563;">Your OddWons password was just changed.</p>
        {info_box("If you didn't make this change, contact us immediately.", "⚠️")}
    """
    return await send_email(to_email, "Your OddWons password was changed", get_base_template(content))


# SUBSCRIPTION EMAILS
async def send_subscription_confirmed_email(to_email: str, tier: str, amount: float, name: str = None) -> bool:
    display_name = name or "there"
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0;">You're officially {tier}! 🎊</h2>
        <p style="color: #4b5563;">Hey {display_name}, your payment of ${amount:.2f} was successful.</p>
        {button("Go to Dashboard", "https://oddwons.ai/dashboard")}
    """
    return await send_email(to_email, f"You're now OddWons {tier}! 🎉", get_base_template(content))


async def send_trial_ending_soon_email(to_email: str, days_left: int, name: str = None, tier: str = "BASIC") -> bool:
    display_name = name or "there"
    urgency = "tomorrow" if days_left == 1 else f"in {days_left} days"
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0;">Your trial ends {urgency} ⏰</h2>
        <p style="color: #4b5563;">Hey {display_name}, upgrade to keep your {tier} access.</p>
        {button("Upgrade Now", "https://oddwons.ai/settings")}
    """
    return await send_email(to_email, f"Your OddWons trial ends {urgency}", get_base_template(content))


async def send_payment_failed_email(to_email: str, amount: float, name: str = None) -> bool:
    content = f"""
        <h2 style="color: {BRAND_ERROR}; margin: 0 0 16px 0;">Payment failed ⚠️</h2>
        <p style="color: #4b5563;">We couldn't process your payment of ${amount:.2f}.</p>
        {button("Update Payment Method", "https://oddwons.ai/settings", BRAND_ERROR)}
    """
    return await send_email(to_email, "⚠️ Your OddWons payment failed", get_base_template(content))


async def send_subscription_cancelled_email(to_email: str, tier: str, end_date: str, name: str = None) -> bool:
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0;">We're sad to see you go 😢</h2>
        <p style="color: #4b5563;">Your {tier} subscription has been cancelled. Access until {end_date}.</p>
        {button("Resubscribe", "https://oddwons.ai/settings")}
    """
    return await send_email(to_email, "Your OddWons subscription has been cancelled", get_base_template(content))


# ALERT EMAILS
async def send_market_alert_email(to_email: str, market_title: str, alert_type: str, old_price: float, new_price: float, platform: str, name: str = None) -> bool:
    price_change = new_price - old_price
    direction = "up" if price_change > 0 else "down"
    emoji = "📈" if price_change > 0 else "📉"
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0;">Market Alert {emoji}</h2>
        <p style="color: #4b5563;"><strong>{market_title}</strong></p>
        <p style="color: #4b5563;">{platform}: {old_price:.0%} → {new_price:.0%} ({'+' if price_change > 0 else ''}{price_change:.0%})</p>
        {button("View Market", "https://oddwons.ai/markets")}
    """
    return await send_email(to_email, f"{emoji} {market_title} moved {direction}", get_base_template(content))


async def send_daily_digest_email(to_email: str, insights: List[Dict], stats: Dict, name: str = None) -> bool:
    display_name = name or "there"
    date = datetime.now().strftime("%A, %B %d")
    insights_html = "".join([f"<li style='margin: 8px 0;'><strong>{i.get('market_title', '')}</strong>: {i.get('summary', '')[:100]}...</li>" for i in insights[:5]])
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0;">Your Daily Digest 📰</h2>
        <p style="color: #6b7280;">{date}</p>
        <p style="color: #4b5563;">Hey {display_name}, here's what's happening:</p>
        <ul style="color: #4b5563; padding-left: 20px;">{insights_html}</ul>
        {button("See All Insights", "https://oddwons.ai/opportunities")}
    """
    return await send_email(to_email, f"📰 Your OddWons Daily Digest – {date}", get_base_template(content))


# BATCH PROCESSING
async def process_pending_alert_emails() -> dict:
    """Process all unsent alert emails at end of 15-min cycle."""
    from sqlalchemy import select, and_
    from app.core.database import AsyncSessionLocal
    from app.models.alert import Alert
    from app.models.user import User
    
    results = {"processed": 0, "sent": 0, "failed": 0}
    
    async with AsyncSessionLocal() as session:
        query = select(Alert, User).join(User).where(
            and_(Alert.email_sent == False, User.email_alerts_enabled == True)
        ).limit(100)
        
        result = await session.execute(query)
        for alert, user in result.all():
            results["processed"] += 1
            try:
                success = await send_market_alert_email(
                    user.email, alert.market_title, alert.alert_type,
                    alert.old_price, alert.new_price, alert.platform, user.name
                )
                if success:
                    alert.email_sent = True
                    alert.email_sent_at = datetime.utcnow()
                    results["sent"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Alert email failed: {e}")
                results["failed"] += 1
        
        await session.commit()
    
    logger.info(f"Alert emails: {results}")
    return results
```

---

## TASK 2: Update Scheduler with AI Analysis + Alert Emails

### Update `app/main.py`

```python
async def scheduled_collection():
    """Background task: collect data, run AI analysis, send alert emails."""
    logger.info("Starting scheduled data collection...")
    try:
        # Step 1: Data collection
        result = await data_collector.run_collection(run_pattern_detection=False)
        logger.info(f"Collection complete: {result}")
        
        # Step 2: AI analysis
        logger.info("Starting AI analysis...")
        from app.services.patterns.engine import pattern_engine
        from app.services.market_matcher import run_market_matching
        
        ai_enabled = settings.groq_api_key and len(settings.groq_api_key) > 0
        analysis_result = await pattern_engine.run_full_analysis(with_ai=ai_enabled)
        logger.info(f"AI analysis complete: {analysis_result}")
        
        # Step 3: Cross-platform matching
        match_result = await run_market_matching(min_volume=1000)
        logger.info(f"Market matching: {match_result}")
        
        # Step 4: Send pending alert emails
        logger.info("Processing alert emails...")
        from app.services.email import process_pending_alert_emails
        email_result = await process_pending_alert_emails()
        logger.info(f"Alert emails: {email_result}")
        
    except Exception as e:
        logger.error(f"Scheduled task failed: {e}", exc_info=True)
```

---

## TASK 3: Settings Page - Current Plan Highlight with Sparkles

### Create `frontend/src/components/SparkleCard.tsx`

```tsx
'use client'

import { useEffect, useRef } from 'react'

interface SparkleCardProps {
  children: React.ReactNode
  active?: boolean
  className?: string
}

export default function SparkleCard({ children, active = false, className = '' }: SparkleCardProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!active || !containerRef.current) return

    const container = containerRef.current
    const interval = setInterval(() => {
      const sparkle = document.createElement('div')
      const x = Math.random() * container.offsetWidth
      const size = 4 + Math.random() * 4
      
      sparkle.style.cssText = `
        position: absolute;
        left: ${x}px;
        bottom: 0;
        width: ${size}px;
        height: ${size}px;
        background: radial-gradient(circle, #ffd700 0%, #ffec80 50%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
        animation: sparkle-float ${2 + Math.random() * 2}s ease-out forwards;
        box-shadow: 0 0 ${size}px #ffd700;
      `
      
      container.appendChild(sparkle)
      setTimeout(() => sparkle.remove(), 4000)
    }, 150)

    return () => clearInterval(interval)
  }, [active])

  return (
    <div
      ref={containerRef}
      className={`relative overflow-visible ${active ? 'ring-2 ring-yellow-400 shadow-[0_0_30px_rgba(255,215,0,0.3)]' : ''} ${className}`}
    >
      {children}
      
      <style jsx global>{`
        @keyframes sparkle-float {
          0% { transform: translateY(0) scale(1); opacity: 1; }
          100% { transform: translateY(-120px) scale(0); opacity: 0; }
        }
      `}</style>
    </div>
  )
}
```

---

## TASK 4: Trial Persistence (No Gaming)

### Backend - `app/api/routes/billing.py`

```python
async def create_checkout_session(...):
    user = await get_current_user(...)
    
    # Calculate trial days - only give trial if never had one
    trial_days = 0
    if not user.trial_start_date:
        trial_days = 7
    elif user.trial_end_date and user.trial_end_date > datetime.utcnow():
        # Still in trial - use remaining days
        remaining = (user.trial_end_date - datetime.utcnow()).days
        trial_days = max(0, remaining)
    
    session = stripe.checkout.Session.create(
        # ... other params ...
        subscription_data={
            "trial_period_days": trial_days if trial_days > 0 else None,
        }
    )
```

---

## TASK 5: Sidebar Trial/Plan Badge

### Create `frontend/src/components/TierBadge.tsx`

```tsx
'use client'

import { useEffect, useRef } from 'react'

interface TierBadgeProps {
  tier: 'BASIC' | 'PREMIUM' | 'PRO'
  daysLeft?: number
}

export default function TierBadge({ tier, daysLeft }: TierBadgeProps) {
  const badgeRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!badgeRef.current || tier === 'BASIC') return
    
    const container = badgeRef.current
    const interval = setInterval(() => {
      const particle = document.createElement('div')
      const x = Math.random() * container.offsetWidth
      const size = 2 + Math.random() * 3
      const colors = { PREMIUM: '#d4af37', PRO: '#ffd700' }
      
      particle.style.cssText = `
        position: absolute; left: ${x}px; bottom: 0;
        width: ${size}px; height: ${size}px;
        background: ${colors[tier as keyof typeof colors]};
        border-radius: 50%; pointer-events: none;
        animation: tier-bubble ${1.5 + Math.random()}s ease-out forwards;
      `
      
      container.appendChild(particle)
      setTimeout(() => particle.remove(), 2500)
    }, tier === 'PRO' ? 100 : 200)

    return () => clearInterval(interval)
  }, [tier])

  // Trial countdown
  if (daysLeft !== undefined && daysLeft > 0) {
    return (
      <div className="mx-3 mb-4 p-3 bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-xl">
        <div className="flex items-center gap-2">
          <span className="text-lg">⏳</span>
          <div>
            <p className="text-sm font-semibold text-amber-800">{daysLeft} day{daysLeft !== 1 ? 's' : ''} left</p>
            <p className="text-xs text-amber-600">{tier} trial</p>
          </div>
        </div>
      </div>
    )
  }

  // Paid tier badges
  const styles = {
    BASIC: { bg: 'from-yellow-400 to-amber-400', text: 'text-yellow-900', icon: '⭐' },
    PREMIUM: { bg: 'from-amber-200 via-yellow-100 to-amber-200', text: 'text-amber-800', icon: '💎' },
    PRO: { bg: 'from-yellow-400 via-amber-300 to-yellow-400', text: 'text-yellow-900', icon: '👑' },
  }
  const style = styles[tier]

  return (
    <div className="mx-3 mb-4 relative overflow-visible">
      <div ref={badgeRef} className={`relative p-3 bg-gradient-to-r ${style.bg} rounded-xl shadow-lg overflow-visible`}>
        <div className="flex items-center justify-center gap-2">
          <span className="text-lg">{style.icon}</span>
          <span className={`font-bold ${style.text}`}>{tier}</span>
        </div>
      </div>
      
      <style jsx global>{`
        @keyframes tier-bubble {
          0% { transform: translateY(0) scale(1); opacity: 0.8; }
          100% { transform: translateY(-40px) scale(0); opacity: 0; }
        }
      `}</style>
    </div>
  )
}
```

---

## TASK 6: New Card Layout with Market Images + Platform Branding

### Design Spec

```
┌─────────────────────────────────────────┐
│                                         │
│         [MARKET IMAGE]                  │  ← Image from Kalshi/Polymarket API
│         (gradient overlay)              │     or fallback gradient
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  Market Title                           │
│  Category • Volume: $1.2M               │
│                                         │
│  Yes: 65%  ████████░░  No: 35%          │
│                                         │
│  [Other card details...]                │
│                                         │
├─────────────────────────────────────────┤
│ [LOGO]  Kalshi                          │  ← Platform footer
│ ████████████████████████████████████████│     Left: logo + name
└─────────────────────────────────────────┘     Right: brand color fill
```

### Platform Brand Colors & Logos

```typescript
// frontend/src/lib/platforms.ts

export const PLATFORMS = {
  kalshi: {
    name: 'Kalshi',
    color: '#00D26A',        // Kalshi green
    colorDark: '#00A855',
    colorLight: '#E6FFF2',
    logo: '/logos/kalshi-logo.svg',   // Download from Kalshi
    logoWhite: '/logos/kalshi-logo-white.svg',
  },
  polymarket: {
    name: 'Polymarket',
    color: '#7C3AED',        // Polymarket purple
    colorDark: '#6D28D9',
    colorLight: '#EDE9FE',
    logo: '/logos/polymarket-logo.svg',  // Download from Polymarket
    logoWhite: '/logos/polymarket-logo-white.svg',
  },
}

export type PlatformKey = keyof typeof PLATFORMS
```

### Download Platform Logos

**Kalshi:**
- Logo: https://kalshi.com/press (or extract from site)
- Primary color: #00D26A (green)

**Polymarket:**
- Logo: https://polymarket.com (extract from site)
- Primary color: #7C3AED (purple)

Save to:
- `frontend/public/logos/kalshi-logo.svg`
- `frontend/public/logos/kalshi-logo-white.svg`
- `frontend/public/logos/polymarket-logo.svg`
- `frontend/public/logos/polymarket-logo-white.svg`

### Update Market Model - Add Image URL

```python
# app/models/market.py

class Market(Base):
    # ... existing fields ...
    image_url = Column(String, nullable=True)  # Market/event image from API
```

### Update Data Collectors to Fetch Images

**Kalshi Client - `app/services/kalshi_client.py`:**

```python
# Kalshi events have images - extract from event data
# Check API response for: image_url, event_image, or similar field

async def fetch_all_markets(...):
    # When processing markets, extract image:
    market_data.image_url = event.get('image_url') or event.get('event', {}).get('image_url')
```

**Polymarket Client - `app/services/polymarket_client.py`:**

```python
# Polymarket events have images in the API response
# Check for: image, icon, or image_url field

async def fetch_all_markets(...):
    # Extract image from event:
    market_data.image_url = event.get('image') or event.get('icon')
```

### Create `frontend/src/components/MarketCard.tsx`

```tsx
'use client'

import Image from 'next/image'
import { PLATFORMS, PlatformKey } from '@/lib/platforms'

interface MarketCardProps {
  market: {
    id: string
    title: string
    category?: string
    volume?: number
    yes_price?: number
    no_price?: number
    image_url?: string
    platform: 'kalshi' | 'polymarket'
  }
  onClick?: () => void
}

export default function MarketCard({ market, onClick }: MarketCardProps) {
  const platform = PLATFORMS[market.platform as PlatformKey]
  const yesPercent = market.yes_price ? Math.round(market.yes_price * 100) : 50
  
  // Fallback gradient if no image
  const fallbackGradients = {
    kalshi: 'from-green-400 via-emerald-500 to-teal-600',
    polymarket: 'from-purple-400 via-violet-500 to-indigo-600',
  }

  return (
    <div 
      onClick={onClick}
      className="bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-lg transition-all cursor-pointer border border-gray-100"
    >
      {/* Image Header */}
      <div className="relative h-32 overflow-hidden">
        {market.image_url ? (
          <Image
            src={market.image_url}
            alt={market.title}
            fill
            className="object-cover"
          />
        ) : (
          <div className={`absolute inset-0 bg-gradient-to-br ${fallbackGradients[market.platform]}`} />
        )}
        
        {/* Gradient overlay for text readability */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
        
        {/* Category badge */}
        {market.category && (
          <span className="absolute top-3 left-3 px-2 py-1 bg-white/90 backdrop-blur-sm rounded-full text-xs font-medium text-gray-700">
            {market.category}
          </span>
        )}
      </div>

      {/* Card Body */}
      <div className="p-4">
        <h3 className="font-semibold text-gray-900 line-clamp-2 mb-2">
          {market.title}
        </h3>
        
        {market.volume && (
          <p className="text-sm text-gray-500 mb-3">
            Volume: ${(market.volume / 1000000).toFixed(1)}M
          </p>
        )}
        
        {/* Price bar */}
        <div className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-green-600 font-medium">Yes {yesPercent}%</span>
            <span className="text-red-500 font-medium">No {100 - yesPercent}%</span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden flex">
            <div 
              className="bg-green-500 transition-all"
              style={{ width: `${yesPercent}%` }}
            />
            <div 
              className="bg-red-400 transition-all"
              style={{ width: `${100 - yesPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Platform Footer */}
      <div className="flex items-center border-t border-gray-100">
        {/* Logo section - left */}
        <div className="flex items-center gap-2 px-4 py-2">
          <Image
            src={platform.logo}
            alt={platform.name}
            width={20}
            height={20}
            className="object-contain"
          />
          <span className="text-sm font-medium text-gray-700">{platform.name}</span>
        </div>
        
        {/* Brand color fill - right */}
        <div 
          className="flex-1 h-full min-h-[36px]"
          style={{ backgroundColor: platform.color }}
        />
      </div>
    </div>
  )
}
```

### Update Markets Page - Replace K/P with Logos

```tsx
// frontend/src/app/(app)/markets/page.tsx

import Image from 'next/image'
import { PLATFORMS } from '@/lib/platforms'

// Replace the simple K/P badges with:
<div className="flex items-center gap-1.5">
  <Image
    src={PLATFORMS[market.platform].logo}
    alt={PLATFORMS[market.platform].name}
    width={16}
    height={16}
  />
  <span className="text-xs text-gray-500">{PLATFORMS[market.platform].name}</span>
</div>
```

### Update AI Highlights Cards

Use the same `MarketCard` component or create a variant:

```tsx
// frontend/src/app/(app)/opportunities/page.tsx

import MarketCard from '@/components/MarketCard'

// For each insight, render:
<MarketCard 
  market={{
    id: insight.market_id,
    title: insight.market_title,
    category: insight.category,
    yes_price: insight.current_yes_price,
    image_url: insight.image_url,
    platform: insight.platform,
  }}
  onClick={() => router.push(`/insights/${insight.id}`)}
/>
```

### Update Cross-Platform Cards

```tsx
// frontend/src/app/(app)/cross-platform/page.tsx

// Show both platform logos side by side:
<div className="flex items-center gap-4 border-t border-gray-100 p-3">
  <div className="flex items-center gap-2">
    <Image src={PLATFORMS.kalshi.logo} alt="Kalshi" width={16} height={16} />
    <span className="text-sm">{match.kalshi_price}%</span>
  </div>
  <div className="flex items-center gap-2">
    <Image src={PLATFORMS.polymarket.logo} alt="Polymarket" width={16} height={16} />
    <span className="text-sm">{match.polymarket_price}%</span>
  </div>
</div>
```

---

## Files Checklist (COMPLETED Jan 8, 2026)

### Create: ✅
- [x] `app/services/email.py` (as notifications.py)
- [x] `frontend/src/components/SparkleCard.tsx`
- [x] `frontend/src/components/TierBadge.tsx`
- [x] `frontend/src/components/GameCard.tsx` (with pop-out hover effect)
- [x] `frontend/src/components/MarketCard.tsx`
- [x] `frontend/src/lib/platforms.ts`
- [x] `frontend/public/logos/kalshi-logo.svg`
- [x] `frontend/public/logos/kalshi-logo-white.svg`
- [x] `frontend/public/logos/polymarket-logo.svg`
- [x] `frontend/public/logos/polymarket-logo-white.svg`

### Modify: ✅
- [x] `app/main.py` - Add AI analysis + alert emails to scheduler + image_url migration
- [x] `app/api/routes/billing.py` - Trial persistence logic
- [x] `app/api/routes/auth.py` - Send welcome email on register
- [x] `app/models/user.py` - Add trial_start, email_alerts_enabled fields
- [x] `app/models/alert.py` - Add email_sent, email_sent_at fields
- [x] `app/models/market.py` - Add image_url field
- [x] `app/services/kalshi_client.py` - Extract image URLs
- [x] `app/services/polymarket_client.py` - Extract image URLs
- [x] `frontend/src/app/(app)/settings/page.tsx` - Use SparkleCard
- [x] `frontend/src/components/Sidebar.tsx` - Use TierBadge
- [x] `frontend/src/app/(app)/markets/page.tsx` - Use platform logos
- [x] `frontend/src/app/(app)/dashboard/page.tsx` - Use platform logos + GameCard
- [x] `frontend/src/app/(app)/opportunities/page.tsx` - Use GameCard
- [x] `frontend/src/app/(app)/cross-platform/page.tsx` - Use platform logos + GameCard

### Run: ✅
- [x] Database migration via /debug/migrate (trial_start, email fields, image_url)
- [x] Created platform logo SVGs
