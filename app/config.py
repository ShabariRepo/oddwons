from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://oddwons:oddwons_dev@localhost:5432/oddwons"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # API Keys (optional - for direct API fallback)
    kalshi_api_key: str = ""
    kalshi_api_secret: str = ""
    polymarket_api_key: str = ""

    # App Settings
    debug: bool = True
    log_level: str = "INFO"
    frontend_url: str = "http://localhost:3000"

    # Data Collection
    collection_interval_minutes: int = 15

    # API Base URLs
    kalshi_base_url: str = "https://api.elections.kalshi.com/trade-api/v2"
    polymarket_gamma_url: str = "https://gamma-api.polymarket.com"
    polymarket_clob_url: str = "https://clob.polymarket.com"

    # Authentication
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""

    # Stripe Price IDs (configure in Stripe dashboard)
    stripe_price_basic: str = ""
    stripe_price_premium: str = ""
    stripe_price_pro: str = ""

    # SendGrid (Email)
    sendgrid_api_key: str = ""
    from_email: str = "alerts@oddwons.ai"

    # AI Analysis (Groq)
    groq_api_key: str = ""
    ai_analysis_enabled: bool = True
    ai_model: str = "gpt-oss-20b-128k"

    # Gemini (Google AI) - for web search grounding
    gemini_api_key: str = ""

    # Worker/Scheduler settings
    run_scheduler: bool = True  # Set to false when using separate worker service

    def model_post_init(self, __context):
        """Fix Railway's DATABASE_URL format for asyncpg."""
        if self.database_url.startswith("postgresql://") and "+asyncpg" not in self.database_url:
            object.__setattr__(
                self,
                'database_url',
                self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
