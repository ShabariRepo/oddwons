import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


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
        subject = "Welcome to OddWons!"

        greeting = f"Hi {user_name}," if user_name else "Hi there,"

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
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to OddWons!</h1>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>Thank you for joining OddWons! We're excited to help you find profitable prediction market opportunities.</p>
                    <p><strong>What to expect:</strong></p>
                    <ul>
                        <li>AI-powered market analysis for Kalshi and Polymarket</li>
                        <li>Real-time pattern detection and alerts</li>
                        <li>Cross-platform arbitrage opportunities</li>
                        <li>Personalized opportunity scoring</li>
                    </ul>
                    <p>Your 7-day free trial starts now. Explore the dashboard to see today's top opportunities!</p>
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

Thank you for joining OddWons! We're excited to help you find profitable prediction market opportunities.

What to expect:
- AI-powered market analysis for Kalshi and Polymarket
- Real-time pattern detection and alerts
- Cross-platform arbitrage opportunities
- Personalized opportunity scoring

Your 7-day free trial starts now. Visit https://oddwons.ai/dashboard to see today's top opportunities!

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


# Singleton instance
notification_service = NotificationService()
