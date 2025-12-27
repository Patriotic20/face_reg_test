from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from fastapi import HTTPException, status

from .schemas import (
    UserCreate,
    UserCreateResponse,
    UserLogin,
    UserLoginResponse,
    RefreshRequest,
    UpdatePassword
)
from .utils.jwt_utils import create_access_token, create_refresh_token, decode_refresh_token
from .utils.password_hash import verify_password

from core.logging import logging
from models.user import User
from core.mixins.crud import create, partial_update

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        logger.debug("AuthService initialized with database session")

    async def register_user(self, credentials: UserCreate) -> UserCreateResponse:
        logger.info(f"Attempting to register user: {credentials.username}")
        
        try:
            user: User = await create(
                session=self.session,
                model=User,
                data=credentials,
            )
            
            logger.info(f"User registered successfully: {user.id} ({user.username})")

            return UserCreateResponse(
                id=user.id,
                username=user.username,
            )

        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(f"Registration failed - username already exists: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Unexpected error during user registration for {credentials.username}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            )

    async def login_user(self, credentials: UserLogin) -> UserLoginResponse:
        logger.info(f"Attempting login for user: {credentials.username}")
        
        user = await self.get_by_username(credentials.username)

        if not user:
            logger.warning(f"Login failed - user not found: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        
        if not verify_password(
            plain_password=credentials.password,
            hashed_password=user.password,
        ):
            logger.warning(f"Login failed - invalid password for user: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        logger.info(f"User logged in successfully: {user.id} ({user.username})")
        payload = {"sub": str(user.id)}

        return UserLoginResponse(
            token_type="Bearer",
            access_token=create_access_token(payload),
            refresh_token=create_refresh_token(payload),
        )

    async def get_by_username(self, username: str) -> User | None:
        logger.debug(f"Fetching user by username: {username}")
        
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        user = result.scalars().first()
        
        if user:
            logger.debug(f"User found: {user.id} ({username})")
        else:
            logger.debug(f"User not found: {username}")
        
        return user

        
    
    async def refresh_token(
        self,
        credentials: RefreshRequest,
    ) -> UserLoginResponse:
        logger.debug("Attempting to refresh access token")
        
        try:
            payload = decode_refresh_token(credentials.refresh_token)
            logger.debug("Refresh token decoded successfully")

        except Exception as e:
            logger.warning(f"Token refresh failed - invalid or expired refresh token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token refresh failed - missing user_id in token payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        logger.debug(f"Refreshing token for user_id: {user_id}")
        
        # Optional but recommended: verify user still exists
        user = await self.session.get(User, int(user_id))
        if not user:
            logger.warning(f"Token refresh failed - user no longer exists: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists",
            )

        logger.info(f"Token refreshed successfully for user: {user_id}")
        new_payload = {"sub": str(user.id)}

        return UserLoginResponse(
            token_type="Bearer",
            access_token=create_access_token(new_payload),
            refresh_token=create_refresh_token(new_payload),
        )
    

    async def change_password(self, credentials: UpdatePassword, current_user: User):
        """Change user password."""
        logger.info(f"Attempting password change for user: {current_user.id} ({current_user.username})")
        
        user_data = await self.get_by_username(username=current_user.username)
        
        # Verify old password
        if not verify_password(
            plain_password=credentials.old_password, 
            hashed_password=user_data.password
        ):
            logger.warning(f"Password change failed - incorrect old password for user: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password"
            )
        
        logger.debug(f"Old password verified for user: {current_user.id}")
        
        # Update password using the computed hashed field
        await partial_update(
            model=User, 
            id=user_data.id, 
            session=self.session, 
            data={"password": credentials.password}  # Already hashed!
        )
        
        logger.info(f"Password changed successfully for user: {current_user.id} ({current_user.username})")
        
        return {"message": "Password updated successfully"}