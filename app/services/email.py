"""
SendGrid Email Service for OddWons.

Handles all transactional emails with branded templates.
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
                            <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px;">Your Prediction Market Companion</p>
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
                                            Compare markets | AI insights | Real-time alerts
                                        </p>
                                        <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                                            © {datetime.now().year} OddWons. All rights reserved.
                                        </p>
                                        <p style="margin: 8px 0 0 0; font-size: 12px; color: #9ca3af;">
                                            <a href="https://oddwons.ai/settings" style="color: {BRAND_PRIMARY}; text-decoration: none;">Manage preferences</a>
                                            &nbsp;|&nbsp;
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


def info_box(content: str, emoji: str = "") -> str:
    """Generate an info box."""
    prefix = f"{emoji} " if emoji else ""
    return f"""
    <div style="background-color: {BRAND_LIGHT}; border-left: 4px solid {BRAND_PRIMARY}; padding: 16px; border-radius: 0 8px 8px 0; margin: 20px 0;">
        <p style="margin: 0; color: #0c4a6e; font-size: 14px;">
            {prefix}{content}
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
            Welcome aboard, {display_name}!
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            You just joined the smartest prediction market community. We're pumped to have you here!
        </p>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            OddWons gives you the edge by aggregating data from Kalshi and Polymarket, then serving you AI-powered insights so you can make smarter decisions.
        </p>

        {info_box("Your 7-day free trial just started. Explore everything!")}

        <p style="color: #111827; font-weight: 600; margin: 24px 0 12px 0;">Here's what you can do:</p>

        {feature_list([
            "Browse 2,000+ markets from Kalshi & Polymarket",
            "Get AI-generated market highlights daily",
            "Compare prices across platforms instantly",
            "Set alerts for markets you care about",
        ])}

        {button("Go to Dashboard", "https://oddwons.ai/dashboard")}

        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            Questions? Just reply to this email - we actually read them!
        </p>
    """

    return await send_email(
        to_email=to_email,
        subject="Welcome to OddWons! Your prediction market journey starts now",
        html_content=get_base_template(content, f"Hey {display_name}! Welcome to OddWons - your prediction market companion.")
    )


async def send_password_reset_email(to_email: str, reset_token: str, name: str = None) -> bool:
    """Password reset request email."""
    display_name = name or "there"
    reset_url = f"https://oddwons.ai/reset-password?token={reset_token}"

    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            Reset your password
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, we got a request to reset your OddWons password. No worries - it happens to the best of us!
        </p>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Click the button below to set a new password:
        </p>

        {button("Reset Password", reset_url)}

        {info_box("This link expires in 1 hour for security reasons.")}

        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            Didn't request this? No worries - just ignore this email and your password stays the same.
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
            Password changed successfully
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, just confirming that your OddWons password was just changed.
        </p>

        {info_box("If you didn't make this change, please contact us immediately by replying to this email.")}

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
            Your free trial is active!
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
            Make the most of your trial - we'll remind you before it ends!
        </p>
    """

    return await send_email(
        to_email=to_email,
        subject=f"Your {tier} trial is now active - 7 days free!",
        html_content=get_base_template(content, f"Your 7-day free trial of OddWons {tier} is now active!")
    )


async def send_trial_ending_soon_email(to_email: str, days_left: int, name: str = None, tier: str = "BASIC") -> bool:
    """Trial ending reminder (3 days or 1 day)."""
    display_name = name or "there"
    urgency = "tomorrow" if days_left == 1 else f"in {days_left} days"

    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            Your trial ends {urgency}
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, just a heads up - your OddWons {tier_badge(tier)} trial wraps up {urgency}.
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
            Not ready? No pressure - you can always come back later. We'll keep your account safe.
        </p>
    """

    return await send_email(
        to_email=to_email,
        subject=f"Your OddWons trial ends {urgency}",
        html_content=get_base_template(content, f"Your free trial ends {urgency} - upgrade to keep access")
    )


async def send_trial_ended_email(to_email: str, name: str = None) -> bool:
    """Trial has ended."""
    display_name = name or "there"

    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            Your trial has ended
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, your 7-day OddWons trial is now over.
        </p>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            You've been downgraded to the free tier, which means limited access to insights and features.
        </p>

        {info_box("Upgrade anytime to get full access back - your data is still here!")}

        <p style="color: #111827; font-weight: 600; margin: 24px 0 12px 0;">What you're missing:</p>

        {feature_list([
            "Full AI-powered market analysis",
            "Unlimited market highlights",
            "Real-time alerts",
            "Cross-platform arbitrage detection",
        ])}

        {button("Upgrade to Premium", "https://oddwons.ai/settings", BRAND_PRIMARY)}

        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            We hope to see you back soon!
        </p>
    """

    return await send_email(
        to_email=to_email,
        subject="Your OddWons trial has ended - we miss you already!",
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
            "Cross-platform comparison",
            "SMS notifications",
            "Movement analysis",
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
            You're officially {tier_badge(tier)}!
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, welcome to OddWons {tier}! Your payment of <strong>${amount:.2f}</strong> was successful.
        </p>

        <p style="color: #111827; font-weight: 600; margin: 24px 0 12px 0;">Here's what you now have access to:</p>

        {feature_list(features)}

        {button("Go to Dashboard", "https://oddwons.ai/dashboard")}

        {info_box("Your subscription renews automatically each month. Manage it anytime in Settings.")}

        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            Thanks for supporting OddWons! You're gonna love it.
        </p>
    """

    return await send_email(
        to_email=to_email,
        subject=f"You're now OddWons {tier}!",
        html_content=get_base_template(content, f"Welcome to OddWons {tier} - your subscription is active!")
    )


async def send_subscription_cancelled_email(to_email: str, tier: str, end_date: str, name: str = None) -> bool:
    """Subscription cancelled."""
    display_name = name or "there"

    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            We're sad to see you go
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, your {tier_badge(tier)} subscription has been cancelled.
        </p>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            You'll still have access to your current features until <strong>{end_date}</strong>, then you'll be moved to the free tier.
        </p>

        {info_box("Changed your mind? You can resubscribe anytime before your access ends.")}

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
            Payment failed
        </h2>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            Hey {display_name}, we couldn't process your payment of <strong>${amount:.2f}</strong>.
        </p>
        <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
            This could happen if your card expired, has insufficient funds, or was declined by your bank.
        </p>

        {info_box("Please update your payment method to avoid losing access to your subscription.")}

        {button("Update Payment Method", "https://oddwons.ai/settings", BRAND_ERROR)}

        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">
            We'll retry the payment in a few days. If you need help, just reply to this email.
        </p>
    """

    return await send_email(
        to_email=to_email,
        subject="Your OddWons payment failed",
        html_content=get_base_template(content, "Your payment couldn't be processed - please update your payment method")
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
            Payment received
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
    direction_color = BRAND_SUCCESS if price_change > 0 else BRAND_ERROR

    content = f"""
        <h2 style="color: #111827; margin: 0 0 16px 0; font-size: 24px;">
            Market Alert
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
        subject=f"{market_title} moved {direction} {abs(price_change):.0%}",
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
            Your Daily Digest
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

        <h3 style="color: #111827; margin: 0 0 16px 0; font-size: 18px;">Today's Top Insights</h3>

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
        subject=f"Your OddWons Daily Digest - {date}",
        html_content=get_base_template(content, f"Your daily prediction market insights for {date}")
    )


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
    from app.models.market import Alert
    from app.models.user import User

    results = {"processed": 0, "sent": 0, "failed": 0}

    async with AsyncSessionLocal() as session:
        # Get all unsent alerts with user info
        query = select(Alert, User).join(User, Alert.user_id == User.id).where(
            and_(
                Alert.email_sent == False,
                User.email_alerts_enabled == True
            )
        ).order_by(Alert.created_at.desc()).limit(100)

        result = await session.execute(query)
        alerts_with_users = result.all()

        for alert, user in alerts_with_users:
            results["processed"] += 1

            try:
                success = await send_market_alert_email(
                    to_email=user.email,
                    market_title=alert.title,
                    alert_type=alert.alert_type,
                    old_price=alert.old_price or 0,
                    new_price=alert.new_price or 0,
                    platform=alert.platform or "unknown",
                    name=user.name
                )

                if success:
                    alert.email_sent = True
                    alert.email_sent_at = datetime.utcnow()
                    results["sent"] += 1
                else:
                    results["failed"] += 1

            except Exception as e:
                logger.error(f"Failed to send alert email for alert {alert.id}: {e}")
                results["failed"] += 1

        await session.commit()

    logger.info(f"Alert email batch complete: {results}")
    return results
