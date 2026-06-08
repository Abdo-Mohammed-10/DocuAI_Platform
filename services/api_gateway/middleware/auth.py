from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.config import settings
from shared.db.session import get_db
from shared.db.models.user import User
from dataclasses import dataclass

@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    
# ── Config 
ALGORITHM      = "HS256"
ACCESS_EXPIRE  = 60        # minutes
REFRESH_EXPIRE = 60 * 24 * 1  # 1 days

pwd_ctx    = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2     = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Schemas 
class TokenPayload(BaseModel):
    sub: str       # user id
    exp: datetime


class TokenPair(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


# ── Helpers 
def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def create_token(
    user_id: str,
    token_type: str = "access",
    expire_minutes: int = 60,
):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expire_minutes
    )

    payload = {
        "sub": user_id,
        "type": token_type,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def create_token_pair(user_id: str) -> TokenPair:
    return TokenPair(
        access_token=create_token(
            user_id=user_id,
            token_type="access",
            expire_minutes=60,
        ),
        refresh_token=create_token(
            user_id=user_id,
            token_type="refresh",
            expire_minutes=60 * 24 * 7,
        ),
    )


# ── FastAPI Dependency 
async def get_current_user(
    token: Annotated[str, Depends(oauth2)],
    db:    AsyncSession = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise credentials_exc

    return user