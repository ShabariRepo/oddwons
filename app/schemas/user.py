from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum


class SubscriptionTier(str, Enum):
    FREE = "FREE"
    BASIC = "BASIC"
    PREMIUM = "PREMIUM"
    PRO = "PRO"


class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CANCELED = "CANCELED"
    PAST_DUE = "PAST_DUE"
    TRIALING = "TRIALING"
    INACTIVE = "INACTIVE"


# Auth schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    user_id: str
    email: str


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    id: str
    is_active: bool
    is_verified: bool
    is_admin: bool = False
    subscription_tier: Optional[SubscriptionTier] = None
    subscription_status: SubscriptionStatus
    subscription_end: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfile(UserResponse):
    stripe_customer_id: Optional[str] = None
    trial_end: Optional[datetime] = None
    last_login: Optional[datetime] = None


# Subscription schemas
class SubscriptionInfo(BaseModel):
    tier: Optional[SubscriptionTier] = None
    status: SubscriptionStatus
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    trial_end: Optional[datetime] = None


class SubscriptionCreate(BaseModel):
    price_id: str  # Stripe price ID


class CheckoutSession(BaseModel):
    checkout_url: str
    session_id: str


class BillingPortal(BaseModel):
    portal_url: str
