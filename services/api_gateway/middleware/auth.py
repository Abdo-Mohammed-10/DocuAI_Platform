import hashlib
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import settings
from shared.db.models.user import User
from shared.db.session import get_db

# Config 
ALGORITHM = "HS256"
ACCESS_EXPIRE = 60  # minutes
REFRESH_EXPIRE = 60 * 24 * 7  # 7 days
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

# FIX: use sha256_crypt instead of bcrypt (avoids 72-byte issue)
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Schemas 
class TokenPayload(BaseModel):
    sub: str
    exp: datetime


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def _normalize_password(password: str) -> str:
    # bcrypt limit workaround
    if len(password.encode("utf-8")) > 72:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()
    return password


def hash_password(password: str) -> str:
    password = _normalize_password(password)
    return pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    plain = _normalize_password(plain)
    return pwd_ctx.verify(plain, hashed)


def create_token(user_id: str, expire_minutes: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def create_token_pair(user_id: str) -> TokenPair:
    return TokenPair(
        access_token=create_token(user_id, ACCESS_EXPIRE),
        refresh_token=create_token(user_id, REFRESH_EXPIRE),
    )

# FastAPI Dependency
async def get_current_user(
    token: Annotated[str, Depends(oauth2)],
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
        )

        user_id = UUID(payload.get("sub"))

        if user_id is None:
            raise credentials_exc

    except JWTError:
        raise credentials_exc

    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exc

    return user