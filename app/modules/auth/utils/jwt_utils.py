import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from typing import Dict, Any

from core.config import settings

def _create_token(data: dict, secret_key: str, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.jwt.algorithm)
    return encoded_jwt


def create_access_token(data: dict):
    delta = timedelta(minutes=settings.jwt.access_token_expires_minutes)
    return _create_token(
        data=data, secret_key=settings.jwt.access_token_secret, expires_delta=delta
    )


def create_refresh_token(data: dict):
    delta = timedelta(days=settings.jwt.refresh_token_expires_days)
    return _create_token(
        data=data, secret_key=settings.jwt.refresh_token_secret, expires_delta=delta
    )
    

def decode_refresh_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt.refresh_token_secret,
            algorithms=[settings.jwt.algorithm],
        )
        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )