import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Brand constants for email templates
BRAND = {
    "logo_url": "https://oddwons.ai/oddwons-logo.png",  # Must be publicly accessible
    "primary": "#0ea5e9",      # Sky blue
    "primary_dark": "#0284c7",
    "primary_gradient": "linear-gradient(135deg, #0ea5e9 0%, #0284c7 50%, #0369a1 100%)",
    "success": "#22c55e",
    "warning": "#eab308",
    "danger": "#ef4444",
    "dark": "#0f172a",
    "gray": "#64748b",
    "light_bg": "#f8fafc",
    "accent": "#06b6d4",  # Cyan accent
}

def get_email_base_template(content: str, title: str = "") -> str:
    """Wrap email content in branded base template."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: {BRAND["light_bg"]}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1e293b;">
    <!-- Outer container with pattern background -->
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: {BRAND["light_bg"]};">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <!-- Main email container -->
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width: 600px; width: 100%; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1);">
                    <!-- Header with logo and gradient -->
                    <tr>
                        <td style="background: {BRAND["primary_gradient"]}; padding: 32px 40px; text-align: center;">
                            <!-- Logo -->
                            <img src="{BRAND["logo_url"]}" alt="OddWons" width="150" style="max-width: 150px; height: auto; margin-bottom: 16px;">
                            <!-- Decorative dots pattern -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top: 8px;">
                                <tr>
                                    <td align="center">
                                        <span style="display: inline-block; width: 6px; height: 6px; background: rgba(255,255,255,0.3); border-radius: 50%; margin: 0 4px;"></span>
                                        <span style="display: inline-block; width: 6px; height: 6px; background: rgba(255,255,255,0.5); border-radius: 50%; margin: 0 4px;"></span>
                                        <span style="display: inline-block; width: 6px; height: 6px; background: rgba(255,255,255,0.7); border-radius: 50%; margin: 0 4px;"></span>
                                        <span style="display: inline-block; width: 6px; height: 6px; background: rgba(255,255,255,0.5); border-radius: 50%; margin: 0 4px;"></span>
                                        <span style="display: inline-block; width: 6px; height: 6px; background: rgba(255,255,255,0.3); border-radius: 50%; margin: 0 4px;"></span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Content area -->
                    <tr>
                        <td style="padding: 40px;">
                            {content}
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background: {BRAND["dark"]}; padding: 32px 40px; text-align: center;">
                            <p style="margin: 0 0 16px 0; color: #94a3b8; font-size: 14px;">
                                Your prediction market research companion
                            </p>
                            <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 0 auto 16px auto;">
                                <tr>
                                    <td style="padding: 0 8px;">
                                        <a href="https://oddwons.ai/dashboard" style="color: {BRAND["accent"]}; text-decoration: none; font-size: 13px;">Dashboard</a>
                                    </td>
                                    <td style="color: #475569;">|</td>
                                    <td style="padding: 0 8px;">
                                        <a href="https://oddwons.ai/settings" style="color: {BRAND["accent"]}; text-decoration: none; font-size: 13px;">Settings</a>
                                    </td>
                                    <td style="color: #475569;">|</td>
                                    <td style="padding: 0 8px;">
                                        <a href="mailto:support@oddwons.ai" style="color: {BRAND["accent"]}; text-decoration: none; font-size: 13px;">Support</a>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 0; color: #64748b; font-size: 12px;">
                                &copy; {datetime.utcnow().year} OddWons. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''


def get_button_html(text: str, url: str, color: str = None) -> str:
    """Generate a branded CTA button."""
    bg_color = color or BRAND["primary"]
    return f'''<table role="presentation" cellspacing="0" cellpadding="0" style="margin: 24px 0;">
        <tr>
            <td style="background: {bg_color}; border-radius: 8px; text-align: center;">
                <a href="{url}" style="display: inline-block; padding: 14px 32px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px;">{text}</a>
            </td>
        </tr>
    </table>'''


def get_highlight_box(content: str, border_color: str = None) -> str:
    """Generate a highlighted info box."""
    color = border_color or BRAND["primary"]
    return f'''<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin: 20px 0;">
        <tr>
            <td style="background: {BRAND["light_bg"]}; border-left: 4px solid {color}; padding: 16px 20px; border-radius: 0 8px 8px 0;">
                {content}
            </td>
        </tr>
    </table>'''


class NotificationService:
    """Service for sending notifications via email, SMS, etc."""

    def __init__(self):
        self.sendgrid_api_key = settings.sendgrid_api_key
        self.from_email = settings.from_email
        self._sg_client: Optional[SendGridAPIClient] = None

    @property
    def sg_client(self) -> Optional[SendGridAPIClient]:
        if self._sg_client is None and self.sendgrid_api_key:
            self._sg_client = SendGridAPIClient(self.sendgrid_api_key)
        return self._sg_client

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email notification."""
        if not self.sg_client:
            logger.warning("SendGrid not configured, skipping email")
            return False

        try:
            message = Mail(
                from_email=Email(self.from_email, "OddWons"),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content),
            )

            if text_content:
                message.add_content(Content("text/plain", text_content))

            response = self.sg_client.send(message)
            logger.info(f"Email sent to {to_email}, status: {response.status_code}")
            return response.status_code in (200, 201, 202)

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_alert_email(
        self,
        to_email: str,
        alert: Dict[str, Any],
        user_name: Optional[str] = None
    ) -> bool:
        """Send an alert notification email."""
        subject = f"OddWons Alert: {alert.get('title', 'New Opportunity')}"

        # Build HTML content
        html_content = self._build_alert_email_html(alert, user_name)
        text_content = self._build_alert_email_text(alert, user_name)

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_daily_digest(
        self,
        to_email: str,
        opportunities: List[Dict[str, Any]],
        user_name: Optional[str] = None
    ) -> bool:
        """Send daily digest email with top opportunities."""
        subject = f"OddWons Daily Digest - {datetime.utcnow().strftime('%B %d, %Y')}"

        html_content = self._build_digest_email_html(opportunities, user_name)
        text_content = self._build_digest_email_text(opportunities, user_name)

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_welcome_email(
        self,
        to_email: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send welcome email to new users."""
        subject = "Welcome to OddWons! 🎯"

        greeting = f"Hi {user_name}," if user_name else "Hey there,"

        content = f'''
            <h1 style="margin: 0 0 8px 0; font-size: 28px; font-weight: 700; color: {BRAND["dark"]};">Welcome aboard!</h1>
            <p style="margin: 0 0 24px 0; color: {BRAND["gray"]}; font-size: 16px;">You've just unlocked smarter prediction market research.</p>

            <p style="margin: 0 0 16px 0; font-size: 16px;">{greeting}</p>
            <p style="margin: 0 0 24px 0; font-size: 16px;">Thanks for joining OddWons! We're here to help you stay on top of prediction markets across Kalshi and Polymarket.</p>

            {get_highlight_box(f"""
                <p style="margin: 0 0 8px 0; font-weight: 600; color: {BRAND["dark"]};">🎉 Your 7-day free trial is now active!</p>
                <p style="margin: 0; color: {BRAND["gray"]}; font-size: 14px;">Full access to all features. No credit card required.</p>
            """, BRAND["success"])}

            <p style="margin: 24px 0 12px 0; font-size: 16px; font-weight: 600; color: {BRAND["dark"]};">What you get:</p>

            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                    <td style="padding: 12px 0; border-bottom: 1px solid #e2e8f0;">
                        <table role="presentation" cellspacing="0" cellpadding="0">
                            <tr>
                                <td style="width: 32px; vertical-align: top;">
                                    <span style="display: inline-block; width: 24px; height: 24px; background: {BRAND["light_bg"]}; border-radius: 6px; text-align: center; line-height: 24px;">🤖</span>
                                </td>
                                <td style="padding-left: 12px;">
                                    <strong style="color: {BRAND["dark"]};">AI Market Insights</strong><br>
                                    <span style="color: {BRAND["gray"]}; font-size: 14px;">Daily analysis of what's moving and why</span>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 12px 0; border-bottom: 1px solid #e2e8f0;">
                        <table role="presentation" cellspacing="0" cellpadding="0">
                            <tr>
                                <td style="width: 32px; vertical-align: top;">
                                    <span style="display: inline-block; width: 24px; height: 24px; background: {BRAND["light_bg"]}; border-radius: 6px; text-align: center; line-height: 24px;">⚡</span>
                                </td>
                                <td style="padding-left: 12px;">
                                    <strong style="color: {BRAND["dark"]};">Cross-Platform Comparison</strong><br>
                                    <span style="color: {BRAND["gray"]}; font-size: 14px;">See price differences between Kalshi & Polymarket</span>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 12px 0; border-bottom: 1px solid #e2e8f0;">
                        <table role="presentation" cellspacing="0" cellpadding="0">
                            <tr>
                                <td style="width: 32px; vertical-align: top;">
                                    <span style="display: inline-block; width: 24px; height: 24px; background: {BRAND["light_bg"]}; border-radius: 6px; text-align: center; line-height: 24px;">📊</span>
                                </td>
                                <td style="padding-left: 12px;">
                                    <strong style="color: {BRAND["dark"]};">Real-Time Alerts</strong><br>
                                    <span style="color: {BRAND["gray"]}; font-size: 14px;">Get notified when markets move significantly</span>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 12px 0;">
                        <table role="presentation" cellspacing="0" cellpadding="0">
                            <tr>
                                <td style="width: 32px; vertical-align: top;">
                                    <span style="display: inline-block; width: 24px; height: 24px; background: {BRAND["light_bg"]}; border-radius: 6px; text-align: center; line-height: 24px;">📰</span>
                                </td>
                                <td style="padding-left: 12px;">
                                    <strong style="color: {BRAND["dark"]};">Daily Briefings</strong><br>
                                    <span style="color: {BRAND["gray"]}; font-size: 14px;">Curated market summaries delivered to your inbox</span>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>

            {get_button_html("Explore Your Dashboard →", "https://oddwons.ai/dashboard")}

            <p style="margin: 24px 0 0 0; font-size: 14px; color: {BRAND["gray"]};">
                Questions? Just reply to this email - we're here to help!
            </p>
        '''

        html_content = get_email_base_template(content, "Welcome to OddWons!")

        text_content = f"""
{greeting}

Welcome to OddWons!

Thanks for joining! We're here to help you stay on top of prediction markets across Kalshi and Polymarket.

YOUR 7-DAY FREE TRIAL IS NOW ACTIVE
Full access to all features. No credit card required.

What you get:
- AI Market Insights: Daily analysis of what's moving and why
- Cross-Platform Comparison: See price differences between Kalshi & Polymarket
- Real-Time Alerts: Get notified when markets move significantly
- Daily Briefings: Curated market summaries delivered to your inbox

Visit https://oddwons.ai/dashboard to get started.

Questions? Just reply to this email - we're here to help!

Best,
The OddWons Team
        """

        return await self.send_email(to_email, subject, html_content, text_content)

    def _build_alert_email_html(self, alert: Dict[str, Any], user_name: Optional[str] = None) -> str:
        """Build HTML content for alert email."""
        greeting = f"Hi {user_name}," if user_name else "Hi,"
        score = alert.get('score', 0)
        score_color = '#22c55e' if score >= 70 else ('#f59e0b' if score >= 50 else '#ef4444')

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1f2937; color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
                .content {{ background: #fff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; }}
                .score {{ display: inline-block; background: {score_color}; color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold; }}
                .action-box {{ background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 15px; margin-top: 15px; }}
                .button {{ display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">{alert.get('title', 'New Opportunity Detected')}</h2>
                    <p style="margin: 10px 0 0 0; opacity: 0.8;">{alert.get('pattern_type', 'Pattern Alert')}</p>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>We detected a new opportunity that matches your criteria:</p>

                    <p><strong>Score:</strong> <span class="score">{score}/100</span></p>

                    <p>{alert.get('message', '')}</p>

                    {f'<div class="action-box"><strong>Suggested Action:</strong><br>{alert.get("action_suggestion", "")}</div>' if alert.get("action_suggestion") else ''}

                    <a href="https://oddwons.ai/opportunities" class="button">View Full Details</a>
                </div>
                <div class="footer">
                    <p>You're receiving this because you have alerts enabled for your OddWons account.</p>
                    <p><a href="https://oddwons.ai/settings">Manage notification preferences</a></p>
                </div>
            </div>
        </body>
        </html>
        """

    def _build_alert_email_text(self, alert: Dict[str, Any], user_name: Optional[str] = None) -> str:
        """Build plain text content for alert email."""
        greeting = f"Hi {user_name}," if user_name else "Hi,"

        text = f"""
{greeting}

New Opportunity Detected: {alert.get('title', 'Alert')}

Score: {alert.get('score', 0)}/100

{alert.get('message', '')}
"""

        if alert.get('action_suggestion'):
            text += f"\nSuggested Action: {alert.get('action_suggestion')}"

        text += "\n\nView full details: https://oddwons.ai/opportunities"

        return text

    def _build_digest_email_html(self, opportunities: List[Dict[str, Any]], user_name: Optional[str] = None) -> str:
        """Build HTML content for daily digest email."""
        greeting = f"Hi {user_name}," if user_name else "Hi,"

        opp_html = ""
        for i, opp in enumerate(opportunities[:5], 1):
            score = opp.get('score', 0)
            score_color = '#22c55e' if score >= 70 else ('#f59e0b' if score >= 50 else '#ef4444')
            opp_html += f"""
            <div style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>#{i} {opp.get('title', 'Opportunity')[:50]}...</strong>
                    <span style="background: {score_color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">{score}</span>
                </div>
                <p style="margin: 5px 0 0 0; font-size: 14px; color: #6b7280;">{opp.get('description', '')[:100]}...</p>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ background: #fff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; }}
                .button {{ display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Daily Digest</h1>
                    <p>{datetime.utcnow().strftime('%B %d, %Y')}</p>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>Here are today's top opportunities:</p>

                    <div style="border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; margin-top: 15px;">
                        {opp_html if opp_html else '<p style="padding: 20px; text-align: center; color: #6b7280;">No opportunities detected today. Check back tomorrow!</p>'}
                    </div>

                    <a href="https://oddwons.ai/opportunities" class="button">View All Opportunities</a>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.utcnow().year} OddWons. All rights reserved.</p>
                    <p><a href="https://oddwons.ai/settings">Manage notification preferences</a></p>
                </div>
            </div>
        </body>
        </html>
        """

    def _build_digest_email_text(self, opportunities: List[Dict[str, Any]], user_name: Optional[str] = None) -> str:
        """Build plain text content for daily digest email."""
        greeting = f"Hi {user_name}," if user_name else "Hi,"

        text = f"""
{greeting}

Your OddWons Daily Digest - {datetime.utcnow().strftime('%B %d, %Y')}

Top Opportunities:
"""

        for i, opp in enumerate(opportunities[:5], 1):
            text += f"\n{i}. {opp.get('title', 'Opportunity')} (Score: {opp.get('score', 0)})"
            if opp.get('description'):
                text += f"\n   {opp.get('description')[:80]}..."

        text += "\n\nView all opportunities: https://oddwons.ai/opportunities"

        return text


    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send password reset email."""
        subject = "Reset Your OddWons Password"
        reset_url = f"https://oddwons.ai/reset-password?token={reset_token}"

        greeting = f"Hi {user_name}," if user_name else "Hi,"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ background: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
                .button {{ display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
                .warning {{ background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px; padding: 12px; margin-top: 20px; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset</h1>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>
                    <div class="warning">
                        <strong>This link expires in 1 hour.</strong> If you didn't request this, you can safely ignore this email.
                    </div>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.utcnow().year} OddWons. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
{greeting}

We received a request to reset your password.

Click here to reset your password: {reset_url}

This link expires in 1 hour. If you didn't request this, you can safely ignore this email.

Best,
The OddWons Team
        """

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_trial_started_email(
        self,
        to_email: str,
        user_name: Optional[str] = None,
        tier: str = "BASIC",
        trial_end: Optional[datetime] = None
    ) -> bool:
        """Send trial started email."""
        subject = f"Your OddWons {tier.title()} Trial Has Started!"
        greeting = f"Hi {user_name}," if user_name else "Hi there,"
        trial_end_str = trial_end.strftime('%B %d, %Y') if trial_end else "7 days from now"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ background: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
                .button {{ display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
                .highlight {{ background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 15px; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Trial Has Started!</h1>
                    <p>{tier.title()} Plan</p>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>Welcome to OddWons {tier.title()}! Your 7-day free trial is now active.</p>
                    <div class="highlight">
                        <strong>Trial ends:</strong> {trial_end_str}<br>
                        <strong>Plan:</strong> {tier.title()}
                    </div>
                    <p>During your trial, you'll have full access to:</p>
                    <ul>
                        <li>AI-powered market analysis</li>
                        <li>Cross-platform price comparisons</li>
                        <li>Real-time alerts and notifications</li>
                        <li>Daily market briefings</li>
                    </ul>
                    <p>Explore everything OddWons has to offer!</p>
                    <a href="https://oddwons.ai/dashboard" class="button">Go to Dashboard</a>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.utcnow().year} OddWons. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
{greeting}

Your OddWons {tier.title()} trial has started!

Trial ends: {trial_end_str}
Plan: {tier.title()}

During your trial, you'll have full access to all features. Explore everything OddWons has to offer!

Visit https://oddwons.ai/dashboard to get started.

Best,
The OddWons Team
        """

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_subscription_confirmed_email(
        self,
        to_email: str,
        user_name: Optional[str] = None,
        tier: str = "BASIC"
    ) -> bool:
        """Send subscription confirmed email."""
        subject = f"Welcome to OddWons {tier.title()}!"
        greeting = f"Hi {user_name}," if user_name else "Hi there,"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #22c55e, #16a34a); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ background: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
                .button {{ display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Subscription Confirmed!</h1>
                    <p>{tier.title()} Plan</p>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>Thank you for subscribing to OddWons {tier.title()}! Your subscription is now active.</p>
                    <p>You now have full access to all {tier.title()} features. We're excited to help you stay informed on prediction markets!</p>
                    <a href="https://oddwons.ai/dashboard" class="button">Go to Dashboard</a>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.utcnow().year} OddWons. All rights reserved.</p>
                    <p><a href="https://oddwons.ai/settings">Manage your subscription</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
{greeting}

Thank you for subscribing to OddWons {tier.title()}!

Your subscription is now active. You have full access to all {tier.title()} features.

Visit https://oddwons.ai/dashboard to explore.

Best,
The OddWons Team
        """

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_subscription_cancelled_email(
        self,
        to_email: str,
        user_name: Optional[str] = None,
        tier: str = "BASIC"
    ) -> bool:
        """Send subscription cancelled email."""
        subject = "Your OddWons Subscription Has Been Cancelled"
        greeting = f"Hi {user_name}," if user_name else "Hi there,"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1f2937; color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ background: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
                .button {{ display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Subscription Cancelled</h1>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>Your OddWons {tier.title()} subscription has been cancelled.</p>
                    <p>We're sorry to see you go! If you change your mind, you can resubscribe anytime from your settings page.</p>
                    <p>You still have access to our free tier with limited features.</p>
                    <a href="https://oddwons.ai/settings" class="button">Resubscribe</a>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.utcnow().year} OddWons. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
{greeting}

Your OddWons {tier.title()} subscription has been cancelled.

We're sorry to see you go! If you change your mind, you can resubscribe anytime at https://oddwons.ai/settings

You still have access to our free tier with limited features.

Best,
The OddWons Team
        """

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_payment_failed_email(
        self,
        to_email: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send payment failed email."""
        subject = "Action Required: Payment Failed for OddWons"
        greeting = f"Hi {user_name}," if user_name else "Hi there,"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #ef4444; color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ background: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
                .button {{ display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
                .warning {{ background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 15px; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Payment Failed</h1>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>We were unable to process your payment for OddWons.</p>
                    <div class="warning">
                        <strong>Action Required:</strong> Please update your payment method to avoid service interruption.
                    </div>
                    <p>Common reasons for failed payments:</p>
                    <ul>
                        <li>Expired card</li>
                        <li>Insufficient funds</li>
                        <li>Card declined by bank</li>
                    </ul>
                    <a href="https://oddwons.ai/settings" class="button">Update Payment Method</a>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.utcnow().year} OddWons. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
{greeting}

We were unable to process your payment for OddWons.

Please update your payment method at https://oddwons.ai/settings to avoid service interruption.

Best,
The OddWons Team
        """

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_trial_ending_email(
        self,
        to_email: str,
        user_name: Optional[str] = None,
        days_remaining: int = 1,
        tier: str = "BASIC"
    ) -> bool:
        """Send trial ending reminder email."""
        subject = f"Your OddWons Trial Ends in {days_remaining} Day{'s' if days_remaining != 1 else ''}"
        greeting = f"Hi {user_name}," if user_name else "Hi there,"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ background: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
                .button {{ display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
                .highlight {{ background: #fffbeb; border: 1px solid #fcd34d; border-radius: 8px; padding: 15px; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Trial Ending Soon</h1>
                    <p>{days_remaining} day{'s' if days_remaining != 1 else ''} remaining</p>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>Your OddWons {tier.title()} trial ends in {days_remaining} day{'s' if days_remaining != 1 else ''}.</p>
                    <div class="highlight">
                        <strong>Don't lose access!</strong> Subscribe now to keep your {tier.title()} features.
                    </div>
                    <p>What you'll keep with {tier.title()}:</p>
                    <ul>
                        <li>AI-powered market insights</li>
                        <li>Cross-platform price comparisons</li>
                        <li>Real-time alerts</li>
                        <li>Daily market briefings</li>
                    </ul>
                    <a href="https://oddwons.ai/settings" class="button">Subscribe Now</a>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.utcnow().year} OddWons. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
{greeting}

Your OddWons {tier.title()} trial ends in {days_remaining} day{'s' if days_remaining != 1 else ''}.

Don't lose access! Subscribe now at https://oddwons.ai/settings to keep your {tier.title()} features.

Best,
The OddWons Team
        """

        return await self.send_email(to_email, subject, html_content, text_content)


# Singleton instance
notification_service = NotificationService()
