import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.core.database import get_db
from app.config import get_settings
from app.schemas.user import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    UserProfile,
    UserUpdate,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services.auth import (
    get_user_by_email,
    create_user,
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
)
from app.services.notifications import notification_service
from app.models.user import User

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    # Check if user exists
    existing = await get_user_by_email(db, user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = await create_user(db, user_data)

    # Create token
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email}
    )

    return Token(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password."""
    user = await authenticate_user(db, credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Create token
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email}
    )

    return Token(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserProfile)
async def get_me(user: User = Depends(get_current_user)):
    """Get current user profile."""
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    updates: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile."""
    if updates.name is not None:
        user.name = updates.name

    if updates.email is not None:
        # Check if email is taken
        existing = await get_user_by_email(db, updates.email)
        if existing and existing.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use",
            )
        user.email = updates.email

    await db.commit()
    await db.refresh(user)

    return user


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change user password."""
    from app.services.auth import verify_password

    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    user.hashed_password = hash_password(new_password)
    await db.commit()

    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout():
    """Logout (client should discard token)."""
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request password reset email."""
    user = await get_user_by_email(db, request.email)

    # Always return success to prevent email enumeration
    if user:
        # Generate reset token
        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        await db.commit()

        # Send email
        await notification_service.send_password_reset_email(
            to_email=user.email,
            reset_token=token,
            user_name=user.name
        )

    return {"message": "If an account exists, a reset email has been sent"}


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password with token."""
    # Find user by reset token
    result = await db.execute(
        select(User).where(User.password_reset_token == request.token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Check if token expired
    if user.password_reset_expires < datetime.utcnow():
        # Clear the expired token
        user.password_reset_token = None
        user.password_reset_expires = None
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )

    # Update password
    user.hashed_password = hash_password(request.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    await db.commit()

    return {"message": "Password reset successfully"}
