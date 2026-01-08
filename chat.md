# OddWons - Production Tasks

_Last updated: January 8, 2026_

## PRODUCTION STATUS: ✅ LIVE

**Backend:** https://api.oddwons.ai
**Frontend:** https://oddwons.ai

### Latest Fix (Jan 8, 2026)
- Fixed `market_matcher.py` Platform enum comparison bug
- Was comparing `"KALSHI"` (string) vs `Platform.KALSHI` (enum value `"kalshi"`)
- Cross-platform matches should now populate after next 15-min cycle

---

## TASK 1: SendGrid Email Service (Complete Implementation)

### Create `app/services/email.py`

```python
"""
SendGrid Email Service for OddWons.

Handles all transactional emails with branded templates.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Brand colors
BRAND_PRIMARY = "#0ea5e9"  # Sky blue
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
    <!--[if !mso]><!-->
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    </style>
    <!--<![endif]-->
</head>
<body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <!-- Preview text -->
    <div style="display: none; max-height: 0; overflow: hidden;">
        {preview_text}
    </div>
    
    <!-- Email container -->
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f3f4f6;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                    
                    <!-- Header with logo -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {BRAND_PRIMARY} 0%, {BRAND_DARK} 100%); padding: 32px; text-align: center;">
                            <img src="https://oddwons.ai/oddwons-logo.png" alt="OddWons" width="60" height="60" style="border-radius: 12px; margin-bottom: 12px;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700;">OddWons</h1>
                            <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">Your Prediction Market Companion 🎯</p>
                        </td>
                    </tr>
                    
                    <!-- Main content -->
                    <tr>
                        <td style="padding: 40px 32px;">
                            {content}
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 24px 32px; border-top: 1px solid #e5e7eb;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td style="text-align: center;">
                                        <p style="margin: 0 0 8px 0; font-size: 14px; color: #6b7280;">
                                            💸 Compare markets • 🧠 AI insights • ⚡ Real-time alerts
                                        </p>
                                        <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                                            © {datetime.now().year} OddWons. All rights reserved.
                                        </p>
                                        <p style="margin: 8px 0 0 0; font-size: 12px; color: #9ca3af;">
                                            <a href="https://oddwons.ai/settings" style="color: {BRAND_PRIMARY}; text-decoration: none;">Manage preferences</a>
                                            &nbsp;•&nbsp;
                                            <a href="https://oddwons.ai" style="color: {BRAND_PRIMARY}; text-decoration: none;">Visit OddWons</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
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
    """Generate a styled button."""
    return f"""
    <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 24px 0;">
        <tr>
            <td style="background-color: {color}; border-radius: 8px;">
                <a href="{url}" style="display: inline-block; padding: 14px 28px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px;">
                    {text}
                </a>
            </td>
        </tr>
    </table>
    """


def info_box(content: str, emoji: str = "💡") -> str:
    """Generate an info box."""
    return f"""
    <div style="background-color: {BRAND_LIGHT}; border-left: 4px solid {BRAND_PRIMARY}; padding: 16px; border-radius: 0 8px 8px 0; margin: 20px 0;">
        <p style="margin: 0; color: #0c4a6e; font-size: 14px;">
            {emoji} {content}
        </p>
    </div>
    """


def feature_list(features: List[str]) -> str:
    """Generate a feature list with checkmarks."""
    items = "".join([f"""
        <tr>
            <td style="padding: 8px 0; color: #374151; font-size: 15px;">
                <span style="color: {BRAND_SUCCESS}; margin-right: 8px;">✓</span> {feature}
            </td>
        </tr>
    """ for feature in features])
    return f"""
    <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 16px 0;">
        {items}
    </table>
    """


def tier_badge(tier: str) -> str:
    """Generate a tier badge."""
    colors = {
        "FREE": ("#6b7280", "#f3f4f6"),
        "BASIC": ("#0ea5e9", "#e0f2fe"),
        "PREMIUM": ("#8b5cf6", "#ede9fe"),
        "PRO": ("#f59e0b", "#fef3c7"),
    }
    text_color, bg_color = colors.get(tier.upper(), colors["FREE"])
    return f"""<span style="display: inline-block; background-color: {bg_color}; color: {text_color}; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600;">{tier.upper()}</span>"""


# =============================================================================
# EMAIL FUNCTIONS
# =============================================================================

async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    from_email: str = None
) -> bool:
    """Send email via SendGrid."""
    if not settings.sendgrid_api_key:
        logger.warning("SendGrid API key not configured - skipping email")
        return False
    
    try:
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        
        message = Mail(
            from_email=Email(from_email or settings.from_email, "OddWons"),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        
        response = sg.send(message)
        logger.info(f"Email sent to {to_email}: {subject} (status: {response.status_code})")
        return response.status_code in [200, 201, 202]
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


# -----------------------------------------------------------------------------
# AUTH EMAILS
# -----------------------------------------------------------------------------

async def send_welcome_email(to_email: str, name: str = None) -> bool:
    """Welcome email after registration."""
    display_name = name or to_email.split('@')[0]
    
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            Welcome aboard, {display_name}! 🎉
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            You just joined the smartest prediction market community. We're pumped to have you here!
        </p>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            OddWons gives you the edge by aggregating data from Kalshi and Polymarket, then serving you AI-powered insights so you can make smarter decisions.
        </p>
        
        {info_box("Your 7-day free trial just started. Explore everything!", "🚀")}
        
        <p style="color: #111827; font-weight: 600; margin: 24px 0 12px 0;">Here's what you can do:</p>
        
        {feature_list([
            "Browse 2,000+ markets from Kalshi & Polymarket",
            "Get AI-generated market highlights daily",
            "Compare prices across platforms instantly",
            "Set alerts for markets you care about",
        ])}
        
        {button("Go to Dashboard", "https://oddwons.ai/dashboard")}
        
        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            Questions? Just reply to this email – we actually read them! 😄
        </p>
    """
    
    return await send_email(
        to_email=to_email,
        subject="Welcome to OddWons! 🎯 Your prediction market journey starts now",
        html_content=get_base_template(content, f"Hey {display_name}! Welcome to OddWons - your prediction market companion.")
    )


async def send_password_reset_email(to_email: str, reset_token: str, name: str = None) -> bool:
    """Password reset request email."""
    display_name = name or "there"
    reset_url = f"https://oddwons.ai/reset-password?token={reset_token}"
    
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            Reset your password 🔐
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, we got a request to reset your OddWons password. No worries – it happens to the best of us!
        </p>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Click the button below to set a new password:
        </p>
        
        {button("Reset Password", reset_url)}
        
        {info_box("This link expires in 1 hour for security reasons.", "⏰")}
        
        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            Didn't request this? No worries – just ignore this email and your password stays the same.
        </p>
    """
    
    return await send_email(
        to_email=to_email,
        subject="Reset your OddWons password",
        html_content=get_base_template(content, "Reset your OddWons password - link expires in 1 hour")
    )


async def send_password_changed_email(to_email: str, name: str = None) -> bool:
    """Confirmation that password was changed."""
    display_name = name or "there"
    
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            Password changed successfully ✅
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, just confirming that your OddWons password was just changed.
        </p>
        
        {info_box("If you didn't make this change, please contact us immediately by replying to this email.", "⚠️")}
        
        {button("Go to OddWons", "https://oddwons.ai")}
    """
    
    return await send_email(
        to_email=to_email,
        subject="Your OddWons password was changed",
        html_content=get_base_template(content, "Your password was successfully changed")
    )


# -----------------------------------------------------------------------------
# SUBSCRIPTION EMAILS
# -----------------------------------------------------------------------------

async def send_trial_started_email(to_email: str, name: str = None, tier: str = "BASIC") -> bool:
    """Trial period started."""
    display_name = name or to_email.split('@')[0]
    
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            Your free trial is active! 🎁
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 8px 0;">
            Hey {display_name}, you've got <strong>7 days</strong> to explore OddWons {tier_badge(tier)} features.
        </p>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            No credit card charged until your trial ends. Cancel anytime.
        </p>
        
        <p style="color: #111827; font-weight: 600; margin: 24px 0 12px 0;">What you get during your trial:</p>
        
        {feature_list([
            "Full access to AI-powered market highlights",
            "Cross-platform price comparison",
            "Real-time market alerts",
            "All premium features unlocked",
        ])}
        
        {button("Start Exploring", "https://oddwons.ai/dashboard")}
        
        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            Make the most of your trial – we'll remind you before it ends! 💪
        </p>
    """
    
    return await send_email(
        to_email=to_email,
        subject=f"Your {tier} trial is now active – 7 days free! 🎉",
        html_content=get_base_template(content, f"Your 7-day free trial of OddWons {tier} is now active!")
    )


async def send_trial_ending_soon_email(to_email: str, days_left: int, name: str = None, tier: str = "BASIC") -> bool:
    """Trial ending reminder (3 days or 1 day)."""
    display_name = name or "there"
    urgency = "tomorrow" if days_left == 1 else f"in {days_left} days"
    emoji = "⚠️" if days_left == 1 else "⏰"
    
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            Your trial ends {urgency} {emoji}
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, just a heads up – your OddWons {tier_badge(tier)} trial wraps up {urgency}.
        </p>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            To keep your access to AI insights and market analysis, upgrade to a paid plan:
        </p>
        
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin: 24px 0;">
            <tr>
                <td style="background-color: #f9fafb; border-radius: 12px; padding: 20px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">
                                <strong style="color: #111827;">Basic</strong>
                                <span style="float: right; color: {BRAND_PRIMARY}; font-weight: 600;">$9.99/mo</span>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">
                                <strong style="color: #111827;">Premium</strong>
                                <span style="float: right; color: #8b5cf6; font-weight: 600;">$19.99/mo</span>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;">
                                <strong style="color: #111827;">Pro</strong>
                                <span style="float: right; color: #f59e0b; font-weight: 600;">$29.99/mo</span>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        {button("Upgrade Now", "https://oddwons.ai/settings")}
        
        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            Not ready? No pressure – you can always come back later. We'll keep your account safe.
        </p>
    """
    
    return await send_email(
        to_email=to_email,
        subject=f"{emoji} Your OddWons trial ends {urgency}",
        html_content=get_base_template(content, f"Your free trial ends {urgency} – upgrade to keep access")
    )


async def send_trial_ended_email(to_email: str, name: str = None) -> bool:
    """Trial has ended."""
    display_name = name or "there"
    
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            Your trial has ended 😢
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, your 7-day OddWons trial is now over.
        </p>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            You've been downgraded to the free tier, which means limited access to insights and features.
        </p>
        
        {info_box("Upgrade anytime to get full access back – your data is still here!", "💾")}
        
        <p style="color: #111827; font-weight: 600; margin: 24px 0 12px 0;">What you're missing:</p>
        
        {feature_list([
            "Full AI-powered market analysis",
            "Unlimited market highlights",
            "Real-time alerts",
            "Cross-platform arbitrage detection",
        ])}
        
        {button("Upgrade to Premium", "https://oddwons.ai/settings", BRAND_PRIMARY)}
        
        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            We hope to see you back soon! 🙏
        </p>
    """
    
    return await send_email(
        to_email=to_email,
        subject="Your OddWons trial has ended – we miss you already! 😢",
        html_content=get_base_template(content, "Your trial ended but you can upgrade anytime")
    )


async def send_subscription_confirmed_email(to_email: str, tier: str, amount: float, name: str = None) -> bool:
    """Subscription payment confirmed."""
    display_name = name or "there"
    
    tier_features = {
        "BASIC": [
            "Daily AI market highlights",
            "Top 10 market insights",
            "Email notifications",
            "Basic market alerts",
        ],
        "PREMIUM": [
            "Everything in Basic",
            "Real-time alerts",
            "Custom alert parameters",
            "SMS notifications",
            "Discord/Slack integration",
        ],
        "PRO": [
            "Everything in Premium",
            "API access",
            "Advanced pattern detection",
            "Priority support",
            "Early feature access",
        ],
    }
    
    features = tier_features.get(tier.upper(), tier_features["BASIC"])
    
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            You're officially {tier_badge(tier)}! 🎊
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, welcome to OddWons {tier}! Your payment of <strong>${amount:.2f}</strong> was successful.
        </p>
        
        <p style="color: #111827; font-weight: 600; margin: 24px 0 12px 0;">Here's what you now have access to:</p>
        
        {feature_list(features)}
        
        {button("Go to Dashboard", "https://oddwons.ai/dashboard")}
        
        {info_box("Your subscription renews automatically each month. Manage it anytime in Settings.", "📅")}
        
        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            Thanks for supporting OddWons! You're gonna love it. 🚀
        </p>
    """
    
    return await send_email(
        to_email=to_email,
        subject=f"You're now OddWons {tier}! 🎉",
        html_content=get_base_template(content, f"Welcome to OddWons {tier} – your subscription is active!")
    )


async def send_subscription_upgraded_email(to_email: str, old_tier: str, new_tier: str, name: str = None) -> bool:
    """Subscription upgraded."""
    display_name = name or "there"
    
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            Upgrade complete! 🚀
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, you just leveled up from {tier_badge(old_tier)} to {tier_badge(new_tier)}!
        </p>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Your new features are already active. Go check them out!
        </p>
        
        {button("Explore New Features", "https://oddwons.ai/dashboard")}
        
        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            Thanks for upgrading – you won't regret it! 💪
        </p>
    """
    
    return await send_email(
        to_email=to_email,
        subject=f"You upgraded to {new_tier}! 🎉",
        html_content=get_base_template(content, f"You've been upgraded from {old_tier} to {new_tier}")
    )


async def send_subscription_downgraded_email(to_email: str, old_tier: str, new_tier: str, name: str = None) -> bool:
    """Subscription downgraded."""
    display_name = name or "there"
    
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            Plan changed to {new_tier}
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, your plan has been changed from {tier_badge(old_tier)} to {tier_badge(new_tier)}.
        </p>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Some features may no longer be available. You can upgrade again anytime.
        </p>
        
        {button("View Plans", "https://oddwons.ai/settings")}
        
        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            We're still here whenever you're ready to upgrade again! 🙂
        </p>
    """
    
    return await send_email(
        to_email=to_email,
        subject=f"Your OddWons plan has been changed",
        html_content=get_base_template(content, f"Your plan changed from {old_tier} to {new_tier}")
    )


async def send_subscription_cancelled_email(to_email: str, tier: str, end_date: str, name: str = None) -> bool:
    """Subscription cancelled."""
    display_name = name or "there"
    
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            We're sad to see you go 😢
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, your {tier_badge(tier)} subscription has been cancelled.
        </p>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            You'll still have access to your current features until <strong>{end_date}</strong>, then you'll be moved to the free tier.
        </p>
        
        {info_box("Changed your mind? You can resubscribe anytime before your access ends.", "💡")}
        
        {button("Resubscribe", "https://oddwons.ai/settings")}
        
        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            If you have feedback on how we can improve, just reply to this email. We'd love to hear from you!
        </p>
    """
    
    return await send_email(
        to_email=to_email,
        subject="Your OddWons subscription has been cancelled",
        html_content=get_base_template(content, f"Your subscription is cancelled but you have access until {end_date}")
    )


async def send_payment_failed_email(to_email: str, amount: float, name: str = None) -> bool:
    """Payment failed notification."""
    display_name = name or "there"
    
    content = f"""
        <h2 style="color: {BRAND_ERROR}; margin: 0 0 16px 0; font-size: 24px;">
            Payment failed ⚠️
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, we couldn't process your payment of <strong>${amount:.2f}</strong>.
        </p>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            This could happen if your card expired, has insufficient funds, or was declined by your bank.
        </p>
        
        {info_box("Please update your payment method to avoid losing access to your subscription.", "🔧")}
        
        {button("Update Payment Method", "https://oddwons.ai/settings", BRAND_ERROR)}
        
        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            We'll retry the payment in a few days. If you need help, just reply to this email.
        </p>
    """
    
    return await send_email(
        to_email=to_email,
        subject="⚠️ Your OddWons payment failed",
        html_content=get_base_template(content, "Your payment couldn't be processed – please update your payment method")
    )


async def send_payment_receipt_email(
    to_email: str, 
    amount: float, 
    tier: str, 
    invoice_id: str,
    name: str = None
) -> bool:
    """Payment receipt/invoice."""
    display_name = name or "there"
    date = datetime.now().strftime("%B %d, %Y")
    
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            Payment received ✅
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 24px 0;">
            Hey {display_name}, thanks for your payment!
        </p>
        
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f9fafb; border-radius: 12px; padding: 20px; margin: 0 0 24px 0;">
            <tr>
                <td style="padding: 12px 20px; border-bottom: 1px solid #e5e7eb;">
                    <span style="color: #6b7280;">Invoice</span>
                    <span style="float: right; color: #111827; font-family: monospace;">{invoice_id}</span>
                </td>
            </tr>
            <tr>
                <td style="padding: 12px 20px; border-bottom: 1px solid #e5e7eb;">
                    <span style="color: #6b7280;">Date</span>
                    <span style="float: right; color: #111827;">{date}</span>
                </td>
            </tr>
            <tr>
                <td style="padding: 12px 20px; border-bottom: 1px solid #e5e7eb;">
                    <span style="color: #6b7280;">Plan</span>
                    <span style="float: right;">{tier_badge(tier)}</span>
                </td>
            </tr>
            <tr>
                <td style="padding: 12px 20px;">
                    <span style="color: #6b7280; font-weight: 600;">Total</span>
                    <span style="float: right; color: #111827; font-weight: 700; font-size: 18px;">${amount:.2f}</span>
                </td>
            </tr>
        </table>
        
        <p style="color: #6b7280; font-size: 14px; margin: 0;">
            This receipt was sent to {to_email}. Keep it for your records.
        </p>
    """
    
    return await send_email(
        to_email=to_email,
        subject=f"Receipt for your OddWons {tier} subscription",
        html_content=get_base_template(content, f"Payment receipt for ${amount:.2f}")
    )


# -----------------------------------------------------------------------------
# PRODUCT/ALERT EMAILS
# -----------------------------------------------------------------------------

async def send_market_alert_email(
    to_email: str,
    market_title: str,
    alert_type: str,
    old_price: float,
    new_price: float,
    platform: str,
    name: str = None
) -> bool:
    """Market price movement alert."""
    display_name = name or "there"
    
    price_change = new_price - old_price
    direction = "up" if price_change > 0 else "down"
    direction_emoji = "📈" if price_change > 0 else "📉"
    direction_color = BRAND_SUCCESS if price_change > 0 else BRAND_ERROR
    
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            Market Alert {direction_emoji}
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, a market you're watching just moved!
        </p>
        
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f9fafb; border-radius: 12px; overflow: hidden; margin: 0 0 24px 0;">
            <tr>
                <td style="padding: 20px;">
                    <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 12px; text-transform: uppercase;">{platform}</p>
                    <h3 style="margin: 0 0 16px 0; color: #111827; font-size: 18px;">{market_title}</h3>
                    
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                        <tr>
                            <td style="text-align: center; padding: 12px;">
                                <p style="margin: 0; color: #6b7280; font-size: 12px;">Was</p>
                                <p style="margin: 4px 0 0 0; color: #111827; font-size: 24px; font-weight: 700;">{old_price:.0%}</p>
                            </td>
                            <td style="text-align: center; padding: 12px;">
                                <p style="margin: 0; color: #6b7280; font-size: 12px;">Now</p>
                                <p style="margin: 4px 0 0 0; color: {direction_color}; font-size: 24px; font-weight: 700;">{new_price:.0%}</p>
                            </td>
                            <td style="text-align: center; padding: 12px;">
                                <p style="margin: 0; color: #6b7280; font-size: 12px;">Change</p>
                                <p style="margin: 4px 0 0 0; color: {direction_color}; font-size: 24px; font-weight: 700;">{'+' if price_change > 0 else ''}{price_change:.0%}</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        {button("View Market", "https://oddwons.ai/markets")}
        
        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            <a href="https://oddwons.ai/settings" style="color: {BRAND_PRIMARY};">Manage your alerts</a>
        </p>
    """
    
    return await send_email(
        to_email=to_email,
        subject=f"{direction_emoji} {market_title} moved {direction} {abs(price_change):.0%}",
        html_content=get_base_template(content, f"Market alert: {market_title} is now at {new_price:.0%}")
    )


async def send_daily_digest_email(
    to_email: str,
    insights: List[Dict[str, Any]],
    stats: Dict[str, Any],
    name: str = None
) -> bool:
    """Daily digest with top AI insights."""
    display_name = name or "there"
    date = datetime.now().strftime("%A, %B %d")
    
    # Build insights HTML
    insights_html = ""
    for i, insight in enumerate(insights[:5], 1):
        title = insight.get("market_title", "Market")
        summary = insight.get("summary", "")
        price = insight.get("yes_price", 0)
        platform = insight.get("platform", "")
        
        insights_html += f"""
        <tr>
            <td style="padding: 16px 0; border-bottom: 1px solid #e5e7eb;">
                <p style="margin: 0 0 4px 0; color: #6b7280; font-size: 12px; text-transform: uppercase;">{platform}</p>
                <h4 style="margin: 0 0 8px 0; color: #111827; font-size: 16px;">{title}</h4>
                <p style="margin: 0 0 8px 0; color: #4b5563; font-size: 14px; line-height: 1.5;">{summary[:150]}...</p>
                <span style="display: inline-block; background-color: {BRAND_LIGHT}; color: {BRAND_DARK}; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;">Yes: {price:.0%}</span>
            </td>
        </tr>
        """
    
    content = f"""
        <h2 style="color: #111827; margin: 0 0 8px 0; font-size: 24px;">
            Your Daily Digest 📰
        </h2>
        <p style="color: #6b7280; margin: 0 0 24px 0; font-size: 14px;">{date}</p>
        
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 24px 0;">
            Hey {display_name}, here's what's happening in prediction markets today:
        </p>
        
        <!-- Stats bar -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: {BRAND_LIGHT}; border-radius: 12px; margin: 0 0 24px 0;">
            <tr>
                <td style="padding: 16px; text-align: center; border-right: 1px solid {BRAND_PRIMARY}20;">
                    <p style="margin: 0; color: {BRAND_DARK}; font-size: 24px; font-weight: 700;">{stats.get('total_markets', 0):,}</p>
                    <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 12px;">Markets</p>
                </td>
                <td style="padding: 16px; text-align: center; border-right: 1px solid {BRAND_PRIMARY}20;">
                    <p style="margin: 0; color: {BRAND_DARK}; font-size: 24px; font-weight: 700;">{stats.get('movers', 0)}</p>
                    <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 12px;">Big Movers</p>
                </td>
                <td style="padding: 16px; text-align: center;">
                    <p style="margin: 0; color: {BRAND_DARK}; font-size: 24px; font-weight: 700;">${stats.get('volume', 0)/1e9:.1f}B</p>
                    <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 12px;">Volume</p>
                </td>
            </tr>
        </table>
        
        <h3 style="color: #111827; margin: 0 0 16px 0; font-size: 18px;">🧠 Today's Top Insights</h3>
        
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
            {insights_html}
        </table>
        
        {button("See All Insights", "https://oddwons.ai/opportunities")}
        
        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            <a href="https://oddwons.ai/settings" style="color: {BRAND_PRIMARY};">Adjust digest preferences</a>
        </p>
    """
    
    return await send_email(
        to_email=to_email,
        subject=f"📰 Your OddWons Daily Digest – {date}",
        html_content=get_base_template(content, f"Your daily prediction market insights for {date}")
    )


async def send_weekly_recap_email(
    to_email: str,
    weekly_stats: Dict[str, Any],
    top_movers: List[Dict[str, Any]],
    name: str = None
) -> bool:
    """Weekly recap email."""
    display_name = name or "there"
    
    # Build movers HTML
    movers_html = ""
    for mover in top_movers[:5]:
        title = mover.get("title", "Market")
        change = mover.get("price_change", 0)
        direction = "📈" if change > 0 else "📉"
        color = BRAND_SUCCESS if change > 0 else BRAND_ERROR
        
        movers_html += f"""
        <tr>
            <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;">
                <span style="color: #111827;">{title[:50]}...</span>
                <span style="float: right; color: {color}; font-weight: 600;">{direction} {'+' if change > 0 else ''}{change:.0%}</span>
            </td>
        </tr>
        """
    
    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            Your Week in Review 📊
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 24px 0;">
            Hey {display_name}, here's your weekly prediction market recap:
        </p>
        
        <h3 style="color: #111827; margin: 0 0 16px 0; font-size: 18px;">🔥 Biggest Movers This Week</h3>
        
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin: 0 0 24px 0;">
            {movers_html}
        </table>
        
        {button("Explore Markets", "https://oddwons.ai/markets")}
        
        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            See you next week! 👋
        </p>
    """
    
    return await send_email(
        to_email=to_email,
        subject="📊 Your OddWons Weekly Recap",
        html_content=get_base_template(content, "Your weekly prediction market recap is here")
    )
```

---

## TASK 2: Hook Emails Into App

### 2a. Auth Routes - `app/api/routes/auth.py`

Add at the top:
```python
from app.services.email import send_welcome_email, send_password_reset_email, send_password_changed_email
```

**After successful registration** (in register endpoint):
```python
# Send welcome email (fire and forget)
import asyncio
asyncio.create_task(send_welcome_email(user.email, user.name))
```

**After password reset request** (if you have this endpoint):
```python
asyncio.create_task(send_password_reset_email(user.email, reset_token, user.name))
```

**After password change**:
```python
asyncio.create_task(send_password_changed_email(user.email, user.name))
```

### 2b. Billing Webhook - `app/api/routes/billing.py`

Add at the top:
```python
from app.services.email import (
    send_trial_started_email,
    send_subscription_confirmed_email,
    send_subscription_cancelled_email,
    send_payment_failed_email,
    send_payment_receipt_email,
)
```

**In webhook handler, add email sends for each event:**

```python
# After checkout.session.completed (new subscription)
asyncio.create_task(send_subscription_confirmed_email(
    to_email=user.email,
    tier=tier.value,
    amount=session.amount_total / 100,
    name=user.name
))

# After invoice.paid
asyncio.create_task(send_payment_receipt_email(
    to_email=user.email,
    amount=invoice.amount_paid / 100,
    tier=user.subscription_tier.value,
    invoice_id=invoice.id,
    name=user.name
))

# After invoice.payment_failed
asyncio.create_task(send_payment_failed_email(
    to_email=user.email,
    amount=invoice.amount_due / 100,
    name=user.name
))

# After customer.subscription.deleted
asyncio.create_task(send_subscription_cancelled_email(
    to_email=user.email,
    tier=user.subscription_tier.value,
    end_date=subscription.current_period_end.strftime("%B %d, %Y"),
    name=user.name
))
```

---

## TASK 3: Add AI Analysis to Scheduler

### Update `app/main.py`

Modify the `scheduled_collection` function to run AI analysis after data collection:

```python
async def scheduled_collection():
    """Background task for collecting market data and running AI analysis."""
    logger.info("Starting scheduled data collection...")
    try:
        # Run data collection
        result = await data_collector.run_collection(run_pattern_detection=False)
        logger.info(f"Collection complete: {result}")
        
        # Run AI analysis (every collection cycle)
        logger.info("Starting AI analysis...")
        from app.services.patterns.engine import pattern_engine
        from app.services.market_matcher import run_market_matching
        
        # Pattern detection + AI insights
        ai_enabled = settings.groq_api_key and len(settings.groq_api_key) > 0
        analysis_result = await pattern_engine.run_full_analysis(with_ai=ai_enabled)
        logger.info(f"AI analysis complete: {analysis_result}")
        
        # Cross-platform matching
        match_result = await run_market_matching(min_volume=1000)
        logger.info(f"Market matching complete: {match_result}")
        
    except Exception as e:
        logger.error(f"Scheduled task failed: {e}", exc_info=True)
```

---

## TASK 4: Trial Reminder Cron Job (Optional)

Add a daily job to check for expiring trials:

```python
# In app/main.py, add to lifespan startup:

async def check_expiring_trials():
    """Send reminder emails for expiring trials."""
    from sqlalchemy import select, and_
    from datetime import datetime, timedelta
    from app.models.user import User
    from app.services.email import send_trial_ending_soon_email
    
    async with AsyncSessionLocal() as session:
        # Find users with trials ending in 3 days
        three_days = datetime.utcnow() + timedelta(days=3)
        four_days = datetime.utcnow() + timedelta(days=4)
        
        result = await session.execute(
            select(User).where(
                and_(
                    User.trial_end >= three_days,
                    User.trial_end < four_days,
                    User.subscription_status == "trialing"
                )
            )
        )
        
        for user in result.scalars():
            await send_trial_ending_soon_email(user.email, 3, user.name)
        
        # Find users with trials ending tomorrow
        one_day = datetime.utcnow() + timedelta(days=1)
        two_days = datetime.utcnow() + timedelta(days=2)
        
        result = await session.execute(
            select(User).where(
                and_(
                    User.trial_end >= one_day,
                    User.trial_end < two_days,
                    User.subscription_status == "trialing"
                )
            )
        )
        
        for user in result.scalars():
            await send_trial_ending_soon_email(user.email, 1, user.name)

# Add to scheduler in lifespan:
scheduler.add_job(
    check_expiring_trials,
    "cron",
    hour=9,  # Run at 9 AM UTC daily
    id="trial_reminders",
    replace_existing=True,
)
```

---

## Summary

| Email Type | Trigger |
|------------|---------|
| Welcome | After registration |
| Password Reset | Password reset request |
| Password Changed | After password update |
| Trial Started | After checkout with trial |
| Trial Ending (3 days) | Daily cron job |
| Trial Ending (1 day) | Daily cron job |
| Trial Ended | Stripe webhook (subscription status change) |
| Subscription Confirmed | Stripe webhook (checkout.session.completed) |
| Subscription Upgraded | Stripe webhook (subscription updated) |
| Subscription Downgraded | Stripe webhook (subscription updated) |
| Subscription Cancelled | Stripe webhook (subscription deleted) |
| Payment Failed | Stripe webhook (invoice.payment_failed) |
| Payment Receipt | Stripe webhook (invoice.paid) |
| Market Alert | Alert system (when triggered) |
| Daily Digest | Daily cron job |
| Weekly Recap | Weekly cron job |

---

## TASK 5: Batch Alert Email Processing (End of Cycle)

Alerts are created during the 15-min analysis cycle. At the end of each cycle, query for unsent alerts and send emails.

### Add to `app/services/email.py`:

```python
# -----------------------------------------------------------------------------
# BATCH ALERT PROCESSING
# -----------------------------------------------------------------------------

async def process_pending_alert_emails() -> dict:
    """
    Process all unsent alert emails.
    Called at the end of each 15-min collection/analysis cycle.
    Returns count of emails sent.
    """
    from sqlalchemy import select, and_
    from app.core.database import AsyncSessionLocal
    from app.models.alert import Alert  # Adjust import based on your model
    from app.models.user import User
    
    results = {"processed": 0, "sent": 0, "failed": 0}
    
    async with AsyncSessionLocal() as session:
        # Get all unsent alerts with user info
        # Assuming Alert model has: id, user_id, market_title, alert_type, 
        # old_price, new_price, platform, email_sent (bool), created_at
        query = select(Alert, User).join(User).where(
            and_(
                Alert.email_sent == False,
                User.email_alerts_enabled == True  # Respect user preferences
            )
        ).order_by(Alert.created_at.desc()).limit(100)  # Batch limit
        
        result = await session.execute(query)
        alerts_with_users = result.all()
        
        for alert, user in alerts_with_users:
            results["processed"] += 1
            
            try:
                # Send the alert email
                success = await send_market_alert_email(
                    to_email=user.email,
                    market_title=alert.market_title,
                    alert_type=alert.alert_type,
                    old_price=alert.old_price,
                    new_price=alert.new_price,
                    platform=alert.platform,
                    name=user.name
                )
                
                if success:
                    # Mark as sent
                    alert.email_sent = True
                    alert.email_sent_at = datetime.utcnow()
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    
            except Exception as e:
                logger.error(f"Failed to send alert email for alert {alert.id}: {e}")
                results["failed"] += 1
        
        # Commit all the email_sent updates
        await session.commit()
    
    logger.info(f"Alert email batch complete: {results}")
    return results
```

### Update Alert Model (if needed)

Make sure your `Alert` model in `app/models/alert.py` has these fields:

```python
class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    market_id = Column(String, nullable=False)
    market_title = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)  # e.g., "price_spike", "volume_surge"
    old_price = Column(Float)
    new_price = Column(Float)
    
    # Email tracking
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Update User Model (if needed)

Add email preference field to `app/models/user.py`:

```python
class User(Base):
    # ... existing fields ...
    
    # Email preferences
    email_alerts_enabled = Column(Boolean, default=True)
    email_digest_enabled = Column(Boolean, default=True)
```

### Update Scheduler in `app/main.py`

```python
async def scheduled_collection():
    """Background task for collecting market data, running AI analysis, and sending alerts."""
    logger.info("Starting scheduled data collection...")
    try:
        # Step 1: Run data collection
        result = await data_collector.run_collection(run_pattern_detection=False)
        logger.info(f"Collection complete: {result}")
        
        # Step 2: Run AI analysis
        logger.info("Starting AI analysis...")
        from app.services.patterns.engine import pattern_engine
        from app.services.market_matcher import run_market_matching
        
        ai_enabled = settings.groq_api_key and len(settings.groq_api_key) > 0
        analysis_result = await pattern_engine.run_full_analysis(with_ai=ai_enabled)
        logger.info(f"AI analysis complete: {analysis_result}")
        
        # Step 3: Cross-platform matching
        match_result = await run_market_matching(min_volume=1000)
        logger.info(f"Market matching complete: {match_result}")
        
        # Step 4: Process pending alert emails (NEW)
        logger.info("Processing pending alert emails...")
        from app.services.email import process_pending_alert_emails
        email_result = await process_pending_alert_emails()
        logger.info(f"Alert emails processed: {email_result}")
        
    except Exception as e:
        logger.error(f"Scheduled task failed: {e}", exc_info=True)
```

---

## TASK 6: Daily Digest Email (9 AM UTC)

Send daily digest to users who have it enabled.

### Add to `app/main.py` (in lifespan startup):

```python
async def send_daily_digest_emails():
    """Send daily digest emails to all subscribed users."""
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.user import User
    from app.models.ai_insight import AIInsight
    from app.services.email import send_daily_digest_email
    
    logger.info("Starting daily digest email job...")
    
    async with AsyncSessionLocal() as session:
        # Get users with digest enabled (paid tiers only)
        users_result = await session.execute(
            select(User).where(
                and_(
                    User.email_digest_enabled == True,
                    User.subscription_tier.in_(["BASIC", "PREMIUM", "PRO"])
                )
            )
        )
        users = users_result.scalars().all()
        
        if not users:
            logger.info("No users subscribed to daily digest")
            return
        
        # Get today's top insights
        insights_result = await session.execute(
            select(AIInsight)
            .where(AIInsight.status == "active")
            .order_by(AIInsight.created_at.desc())
            .limit(5)
        )
        insights = insights_result.scalars().all()
        
        # Get stats
        from app.models.market import Market
        from sqlalchemy import func
        
        market_count = await session.scalar(select(func.count()).select_from(Market))
        total_volume = await session.scalar(select(func.sum(Market.volume)).select_from(Market)) or 0
        
        stats = {
            "total_markets": market_count,
            "movers": len([i for i in insights if i.recent_movement]),
            "volume": total_volume
        }
        
        # Convert insights to dicts
        insights_data = [
            {
                "market_title": i.market_title,
                "summary": i.summary,
                "yes_price": i.current_yes_price or 0,
                "platform": i.platform
            }
            for i in insights
        ]
        
        # Send to each user
        sent_count = 0
        for user in users:
            try:
                success = await send_daily_digest_email(
                    to_email=user.email,
                    insights=insights_data,
                    stats=stats,
                    name=user.name
                )
                if success:
                    sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send digest to {user.email}: {e}")
        
        logger.info(f"Daily digest sent to {sent_count}/{len(users)} users")


# Add to scheduler in lifespan:
scheduler.add_job(
    send_daily_digest_emails,
    "cron",
    hour=9,  # 9 AM UTC
    minute=0,
    id="daily_digest",
    replace_existing=True,
)
```

---

## Complete Scheduler Setup in `app/main.py`

Here's the full lifespan with all jobs:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting OddWons API...")
    await init_db()
    logger.info("Database initialized")

    # Job 1: Data collection + AI analysis + alert emails (every 15 min)
    scheduler.add_job(
        scheduled_collection,
        "interval",
        minutes=settings.collection_interval_minutes,
        id="data_collection",
        replace_existing=True,
    )
    
    # Job 2: Trial expiration reminders (daily at 9 AM UTC)
    scheduler.add_job(
        check_expiring_trials,
        "cron",
        hour=9,
        minute=0,
        id="trial_reminders",
        replace_existing=True,
    )
    
    # Job 3: Daily digest emails (daily at 9:30 AM UTC, after trial reminders)
    scheduler.add_job(
        send_daily_digest_emails,
        "cron",
        hour=9,
        minute=30,
        id="daily_digest",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info(f"Scheduler started with 3 jobs")

    yield

    # Shutdown
    logger.info("Shutting down OddWons API...")
    scheduler.shutdown(wait=False)
    await kalshi_client.close()
    await polymarket_client.close()
    await close_db()
    logger.info("Shutdown complete")
```

---

## Email Flow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                     EMAIL TRIGGER FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  IMMEDIATE (API Response)                                       │
│  ├── User registers → Welcome email                            │
│  ├── Password reset request → Reset email                      │
│  └── Password changed → Confirmation email                     │
│                                                                 │
│  STRIPE WEBHOOK (Real-time)                                     │
│  ├── checkout.session.completed → Subscription confirmed       │
│  ├── invoice.paid → Payment receipt                            │
│  ├── invoice.payment_failed → Payment failed                   │
│  └── customer.subscription.deleted → Cancellation email        │
│                                                                 │
│  15-MIN CYCLE (End of scheduled_collection)                     │
│  └── process_pending_alert_emails() → Market alerts            │
│                                                                 │
│  DAILY CRON (9:00 AM UTC)                                       │
│  └── check_expiring_trials() → Trial reminder emails           │
│                                                                 │
│  DAILY CRON (9:30 AM UTC)                                       │
│  └── send_daily_digest_emails() → Daily digest                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Files to Create/Modify

- [ ] CREATE `app/services/email.py` - Full email service with all templates + batch processing
- [ ] MODIFY `app/models/alert.py` - Add email_sent, email_sent_at fields
- [ ] MODIFY `app/models/user.py` - Add email_alerts_enabled, email_digest_enabled fields
- [ ] MODIFY `app/api/routes/auth.py` - Add welcome email on register
- [ ] MODIFY `app/api/routes/billing.py` - Add subscription emails in webhook
- [ ] MODIFY `app/main.py` - Add AI analysis + alert emails to scheduler, add daily cron jobs
- [ ] RUN migration for new User/Alert fields

---

## TASK 7: Settings Page - Highlight Current Plan with Magic Animation

### Problem
- Settings page shows "Start Free Trial" on ALL plans even if user is already subscribed
- No indication of which plan user is currently on

### Solution
- Highlight current plan with gold border and sparkle/bubble animation
- Show "Current Plan" badge instead of "Start Free Trial"
- Other plans show "Switch to [Plan]" or "Upgrade" / "Downgrade"

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
    const sparkleInterval = setInterval(() => {
      createSparkle(container)
    }, 150)

    return () => clearInterval(sparkleInterval)
  }, [active])

  const createSparkle = (container: HTMLElement) => {
    const sparkle = document.createElement('div')
    sparkle.className = 'sparkle'
    
    // Random position along the card edges and inside
    const x = Math.random() * container.offsetWidth
    const startY = container.offsetHeight + 10
    
    sparkle.style.cssText = `
      position: absolute;
      left: ${x}px;
      bottom: 0;
      width: ${4 + Math.random() * 4}px;
      height: ${4 + Math.random() * 4}px;
      background: radial-gradient(circle, #ffd700 0%, #ffec80 50%, transparent 70%);
      border-radius: 50%;
      pointer-events: none;
      animation: sparkle-float ${2 + Math.random() * 2}s ease-out forwards;
      box-shadow: 0 0 ${4 + Math.random() * 4}px #ffd700;
    `
    
    container.appendChild(sparkle)
    
    // Remove after animation
    setTimeout(() => sparkle.remove(), 4000)
  }

  return (
    <div
      ref={containerRef}
      className={`relative overflow-visible ${active ? 'ring-2 ring-yellow-400 shadow-[0_0_30px_rgba(255,215,0,0.3)]' : ''} ${className}`}
    >
      {children}
      
      <style jsx global>{`
        @keyframes sparkle-float {
          0% {
            transform: translateY(0) scale(1);
            opacity: 1;
          }
          100% {
            transform: translateY(-120px) scale(0);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  )
}
```

### Update Settings Page Plan Cards

```tsx
// In frontend/src/app/(app)/settings/page.tsx

import SparkleCard from '@/components/SparkleCard'

// In the pricing section:
{tiers.map((tier) => {
  const isCurrentPlan = user?.subscription_tier === tier.id
  const isDowngrade = getTierLevel(tier.id) < getTierLevel(user?.subscription_tier)
  const isUpgrade = getTierLevel(tier.id) > getTierLevel(user?.subscription_tier)
  
  return (
    <SparkleCard 
      key={tier.id} 
      active={isCurrentPlan}
      className="rounded-2xl"
    >
      <div className={`p-6 rounded-2xl border-2 transition-all ${
        isCurrentPlan 
          ? 'border-yellow-400 bg-gradient-to-b from-yellow-50 to-white' 
          : 'border-gray-200 bg-white hover:border-gray-300'
      }`}>
        {isCurrentPlan && (
          <div className="absolute -top-3 left-1/2 -translate-x-1/2">
            <span className="bg-gradient-to-r from-yellow-400 to-amber-500 text-white text-xs font-bold px-4 py-1 rounded-full shadow-lg">
              ✨ Current Plan
            </span>
          </div>
        )}
        
        <h3 className="text-xl font-bold">{tier.name}</h3>
        <p className="text-3xl font-bold mt-2">${tier.price}<span className="text-sm text-gray-500">/mo</span></p>
        
        {/* Features list */}
        <ul className="mt-4 space-y-2">
          {tier.features.map((feature, i) => (
            <li key={i} className="flex items-center gap-2 text-sm text-gray-600">
              <span className="text-green-500">✓</span> {feature}
            </li>
          ))}
        </ul>
        
        {/* Action button */}
        <button
          disabled={isCurrentPlan}
          onClick={() => handlePlanChange(tier.id)}
          className={`mt-6 w-full py-3 rounded-lg font-semibold transition-all ${
            isCurrentPlan
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : isUpgrade
                ? 'bg-primary-600 text-white hover:bg-primary-700'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          {isCurrentPlan 
            ? 'Current Plan' 
            : isUpgrade 
              ? `Upgrade to ${tier.name}` 
              : `Switch to ${tier.name}`
          }
        </button>
      </div>
    </SparkleCard>
  )
})}

// Helper function
function getTierLevel(tier: string | undefined): number {
  const levels: Record<string, number> = { FREE: 0, BASIC: 1, PREMIUM: 2, PRO: 3 }
  return levels[tier?.toUpperCase() || 'FREE'] || 0
}
```

---

## TASK 8: Trial Period Persists When Switching Plans

### Problem
User might try to game the system by switching plans to reset their trial.

### Solution
Track `trial_start_date` on the user, not per-subscription. Trial end date = trial_start + 7 days regardless of plan changes.

### Backend Changes

**In `app/api/routes/billing.py` - when creating checkout session:**

```python
async def create_checkout_session(...):
    # Check if user already used their trial
    user = await get_current_user(...)
    
    # If user has a trial_start_date, don't give another trial
    trial_days = 0
    if not user.trial_start_date:
        trial_days = 7
    elif user.trial_end_date and user.trial_end_date > datetime.utcnow():
        # Still in trial - calculate remaining days
        remaining = (user.trial_end_date - datetime.utcnow()).days
        trial_days = max(0, remaining)
    
    session = stripe.checkout.Session.create(
        # ... other params ...
        subscription_data={
            "trial_period_days": trial_days if trial_days > 0 else None,
        }
    )
```

**Update User model if needed:**

```python
class User(Base):
    # ... existing fields ...
    trial_start_date = Column(DateTime, nullable=True)  # Set once, never reset
    trial_end_date = Column(DateTime, nullable=True)    # trial_start + 7 days
```

**On first subscription (webhook):**

```python
# In checkout.session.completed handler:
if not user.trial_start_date:
    user.trial_start_date = datetime.utcnow()
    user.trial_end_date = datetime.utcnow() + timedelta(days=7)
```

---

## TASK 9: Sidebar Trial/Plan Banner

### Current
Sidebar shows "Start your 7 day free trial" for everyone.

### New Behavior

| User State | Banner Display |
|------------|----------------|
| Not subscribed | "Start your 7 day free trial" (current) |
| On trial (BASIC) | "⏳ 5 days left on trial" (countdown) |
| On trial (PREMIUM) | "⏳ 5 days left on trial" (countdown) |
| On trial (PRO) | "⏳ 5 days left on trial" (countdown) |
| Paid BASIC | Yellow ribbon: "BASIC" |
| Paid PREMIUM | Champagne sparkle ribbon: "PREMIUM" |
| Paid PRO | Gold with gold flakes: "PRO" |

### Create `frontend/src/components/TierBadge.tsx`

```tsx
'use client'

import { useEffect, useRef } from 'react'

interface TierBadgeProps {
  tier: 'BASIC' | 'PREMIUM' | 'PRO'
  daysLeft?: number // If on trial
}

export default function TierBadge({ tier, daysLeft }: TierBadgeProps) {
  const badgeRef = useRef<HTMLDivElement>(null)

  // Bubble/sparkle effect for PREMIUM and PRO
  useEffect(() => {
    if (!badgeRef.current || tier === 'BASIC') return
    
    const container = badgeRef.current
    const interval = setInterval(() => {
      createParticle(container, tier)
    }, tier === 'PRO' ? 100 : 200)

    return () => clearInterval(interval)
  }, [tier])

  const createParticle = (container: HTMLElement, tier: string) => {
    const particle = document.createElement('div')
    const x = Math.random() * container.offsetWidth
    const size = 2 + Math.random() * 3
    
    const colors = {
      PREMIUM: ['#d4af37', '#f5e6c8', '#c9b896'], // Champagne
      PRO: ['#ffd700', '#ffec80', '#fff4cc'],      // Gold
    }
    const color = colors[tier as keyof typeof colors]?.[Math.floor(Math.random() * 3)] || '#ffd700'
    
    particle.style.cssText = `
      position: absolute;
      left: ${x}px;
      bottom: 0;
      width: ${size}px;
      height: ${size}px;
      background: ${color};
      border-radius: 50%;
      pointer-events: none;
      animation: tier-bubble ${1.5 + Math.random()}s ease-out forwards;
      box-shadow: 0 0 ${size}px ${color};
    `
    
    container.appendChild(particle)
    setTimeout(() => particle.remove(), 2500)
  }

  // If on trial, show countdown
  if (daysLeft !== undefined && daysLeft > 0) {
    return (
      <div className="mx-3 mb-4 p-3 bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-xl">
        <div className="flex items-center gap-2">
          <span className="text-lg">⏳</span>
          <div>
            <p className="text-sm font-semibold text-amber-800">
              {daysLeft} day{daysLeft !== 1 ? 's' : ''} left on trial
            </p>
            <p className="text-xs text-amber-600">{tier} plan</p>
          </div>
        </div>
      </div>
    )
  }

  // Paid user badges
  const styles = {
    BASIC: {
      bg: 'bg-gradient-to-r from-yellow-400 to-amber-400',
      text: 'text-yellow-900',
      shadow: 'shadow-yellow-200',
    },
    PREMIUM: {
      bg: 'bg-gradient-to-r from-amber-200 via-yellow-100 to-amber-200',
      text: 'text-amber-800',
      shadow: 'shadow-amber-100',
    },
    PRO: {
      bg: 'bg-gradient-to-r from-yellow-400 via-amber-300 to-yellow-400',
      text: 'text-yellow-900',
      shadow: 'shadow-yellow-300',
    },
  }

  const style = styles[tier]

  return (
    <div className="mx-3 mb-4 relative overflow-visible">
      <div
        ref={badgeRef}
        className={`relative p-3 ${style.bg} rounded-xl shadow-lg ${style.shadow} overflow-visible`}
      >
        {/* Ribbon fold effect */}
        <div className="absolute -right-2 -top-2 w-4 h-4 bg-amber-600 rounded-sm transform rotate-45 opacity-30" />
        
        <div className="flex items-center justify-center gap-2">
          <span className="text-lg">
            {tier === 'BASIC' && '⭐'}
            {tier === 'PREMIUM' && '💎'}
            {tier === 'PRO' && '👑'}
          </span>
          <span className={`font-bold ${style.text}`}>{tier}</span>
        </div>
      </div>
      
      <style jsx global>{`
        @keyframes tier-bubble {
          0% {
            transform: translateY(0) scale(1);
            opacity: 0.8;
          }
          100% {
            transform: translateY(-40px) scale(0);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  )
}
```

### Update Sidebar Component

```tsx
// In frontend/src/components/Sidebar.tsx

import TierBadge from './TierBadge'

// Inside the sidebar, replace the "Start your 7 day free trial" section:

{/* Bottom section - Trial/Plan badge */}
<div className="mt-auto">
  {!user ? (
    // Not logged in - show nothing or login prompt
    null
  ) : user.subscription_status === 'trialing' && user.trial_end_date ? (
    // On trial - show countdown
    <TierBadge 
      tier={user.subscription_tier as 'BASIC' | 'PREMIUM' | 'PRO'} 
      daysLeft={Math.ceil((new Date(user.trial_end_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24))}
    />
  ) : user.subscription_tier && user.subscription_tier !== 'FREE' ? (
    // Paid user - show tier badge
    <TierBadge tier={user.subscription_tier as 'BASIC' | 'PREMIUM' | 'PRO'} />
  ) : (
    // Free user - show upgrade prompt
    <Link
      href="/settings"
      className="mx-3 mb-4 block p-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-xl text-center text-sm font-semibold hover:from-primary-600 hover:to-primary-700 transition-all"
    >
      🚀 Start your 7-day free trial
    </Link>
  )}
</div>
```

---

## TASK 10: Card Hover Animation - Shake + Green Wisps + Logo Watermark

### Requirements
- Cards shake slightly on hover
- Green wisps/particles float up on hover
- OddWons logo watermark in center of each card

### Create `frontend/src/components/GameCard.tsx`

```tsx
'use client'

import { useRef, useState } from 'react'
import Image from 'next/image'

interface GameCardProps {
  children: React.ReactNode
  className?: string
  showWatermark?: boolean
}

export default function GameCard({ children, className = '', showWatermark = true }: GameCardProps) {
  const cardRef = useRef<HTMLDivElement>(null)
  const [isHovered, setIsHovered] = useState(false)

  const handleMouseEnter = () => {
    setIsHovered(true)
    if (cardRef.current) {
      // Create green wisps
      for (let i = 0; i < 5; i++) {
        setTimeout(() => createWisp(cardRef.current!), i * 100)
      }
    }
  }

  const handleMouseLeave = () => {
    setIsHovered(false)
  }

  const createWisp = (container: HTMLElement) => {
    const wisp = document.createElement('div')
    const x = Math.random() * container.offsetWidth
    const size = 6 + Math.random() * 8
    
    wisp.style.cssText = `
      position: absolute;
      left: ${x}px;
      bottom: 20%;
      width: ${size}px;
      height: ${size * 1.5}px;
      background: radial-gradient(ellipse, rgba(34, 197, 94, 0.6) 0%, rgba(34, 197, 94, 0.2) 50%, transparent 70%);
      border-radius: 50%;
      pointer-events: none;
      animation: wisp-float ${1 + Math.random() * 0.5}s ease-out forwards;
      filter: blur(1px);
    `
    
    container.appendChild(wisp)
    setTimeout(() => wisp.remove(), 1500)
  }

  return (
    <div
      ref={cardRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`relative overflow-hidden transition-all duration-200 ${isHovered ? 'animate-card-shake' : ''} ${className}`}
    >
      {/* Logo watermark */}
      {showWatermark && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
          <Image
            src="/oddwons-logo.png"
            alt=""
            width={80}
            height={80}
            className="opacity-[0.04] select-none"
          />
        </div>
      )}
      
      {/* Card content */}
      <div className="relative z-10">
        {children}
      </div>
      
      <style jsx global>{`
        @keyframes wisp-float {
          0% {
            transform: translateY(0) scale(1);
            opacity: 0.8;
          }
          50% {
            transform: translateY(-30px) scale(1.2) translateX(${Math.random() > 0.5 ? '' : '-'}10px);
            opacity: 0.6;
          }
          100% {
            transform: translateY(-60px) scale(0.5);
            opacity: 0;
          }
        }
        
        @keyframes card-shake {
          0%, 100% { transform: translateX(0); }
          10% { transform: translateX(-2px) rotate(-0.5deg); }
          20% { transform: translateX(2px) rotate(0.5deg); }
          30% { transform: translateX(-2px) rotate(-0.5deg); }
          40% { transform: translateX(2px) rotate(0.5deg); }
          50% { transform: translateX(-1px); }
          60% { transform: translateX(1px); }
          70% { transform: translateX(-1px); }
          80% { transform: translateX(1px); }
          90% { transform: translateX(0); }
        }
        
        .animate-card-shake {
          animation: card-shake 0.5s ease-in-out;
        }
      `}</style>
    </div>
  )
}
```

### Usage in Dashboard, AI Highlights, Cross-Platform Pages

```tsx
import GameCard from '@/components/GameCard'

// Wrap market/insight cards with GameCard:
<GameCard className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-lg">
  <h3>{market.title}</h3>
  <p>{market.description}</p>
  {/* ... rest of card content */}
</GameCard>
```

### Add Global Animation Classes to `globals.css`

```css
/* Card shake animation */
@keyframes card-shake {
  0%, 100% { transform: translateX(0); }
  10% { transform: translateX(-2px) rotate(-0.5deg); }
  20% { transform: translateX(2px) rotate(0.5deg); }
  30% { transform: translateX(-2px) rotate(-0.5deg); }
  40% { transform: translateX(2px) rotate(0.5deg); }
  50% { transform: translateX(-1px); }
  60% { transform: translateX(1px); }
  70% { transform: translateX(0); }
}

.hover-shake:hover {
  animation: card-shake 0.4s ease-in-out;
}
```

---

## Summary - UI Enhancement Tasks

| Task | Component | Description |
|------|-----------|-------------|
| **7** | Settings Page | Highlight current plan with gold sparkles |
| **8** | Billing Logic | Trial persists across plan changes |
| **9** | Sidebar | Trial countdown OR tier ribbon badge |
| **10** | Cards | Shake + green wisps + logo watermark on hover |

## Files to Create/Modify

- [ ] CREATE `frontend/src/components/SparkleCard.tsx`
- [ ] CREATE `frontend/src/components/TierBadge.tsx`
- [ ] CREATE `frontend/src/components/GameCard.tsx`
- [ ] MODIFY `frontend/src/app/(app)/settings/page.tsx` - Use SparkleCard for current plan
- [ ] MODIFY `frontend/src/components/Sidebar.tsx` - Add TierBadge component
- [ ] MODIFY `frontend/src/app/(app)/dashboard/page.tsx` - Wrap cards with GameCard
- [ ] MODIFY `frontend/src/app/(app)/opportunities/page.tsx` - Wrap cards with GameCard
- [ ] MODIFY `frontend/src/app/(app)/cross-platform/page.tsx` - Wrap cards with GameCard
- [ ] MODIFY `frontend/src/app/globals.css` - Add animation keyframes
- [ ] MODIFY `app/api/routes/billing.py` - Trial persistence logic
- [ ] MODIFY `app/models/user.py` - Add trial_start_date field if missing
