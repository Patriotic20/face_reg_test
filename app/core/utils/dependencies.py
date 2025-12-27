import jwt
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from typing import Callable

from models.user import User
from models.role import Role
from models.permission import Permission

from core.config import settings
from core.db_helper import db_helper
from core.logging import logging

logger = logging.getLogger(__name__)

oauth2_scheme = APIKeyHeader(name="Authorization")

REGISTERED_PERMISSIONS: set[tuple[str, str]] = set()

# Create a callable dependency for the database session
async def get_db_session():
    """Database session dependency."""
    logger.debug("Creating new database session")
    async with db_helper.session_factory() as session:
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Validate JWT token and retrieve user with roles and permissions.
    
    Args:
        token: JWT access token from Authorization header
        session: Async database session
        
    Returns:
        User object if valid
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    logger.debug("Attempting to validate JWT token")
    
    # Strip "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
        logger.debug("Bearer prefix removed from token")
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt.access_token_secret,
            algorithms=[settings.jwt.algorithm]            
        )
        user_id = int(payload.get("sub"))
        
        if not user_id:
            logger.warning("JWT token valid but missing user_id in payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        logger.debug(f"JWT decoded successfully, user_id: {user_id}")
        
        stmt = (
            select(User)
            .options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
            .where(User.id == user_id)
        )
        result = await session.execute(stmt)
        user_data = result.scalars().first()
        
        if not user_data:
            logger.warning(f"User not found in database, user_id: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        logger.info(f"User authenticated successfully, user_id: {user_id}")
        return user_data
        
    except InvalidTokenError as e:
        logger.warning(f"Invalid or expired JWT token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )


def require_permission(*permissions: str, any_of: bool = True) -> Callable:
    """
    Dependency to protect routes by permissions.
    Automatically registers permissions for database seeding.
    """
    logger.debug(f"Setting up permission requirement: {permissions}, any_of={any_of}")
    
    # Register permissions for startup
    for perm_str in permissions:
        if ":" in perm_str:
            resource, action = perm_str.split(":", 1)
            REGISTERED_PERMISSIONS.add((resource, action))
            logger.debug(f"Registered permission: {resource}:{action}")
        else:
            logger.warning(f"Invalid permission format: {perm_str}. Expected 'resource:action'")
    
    async def checker(user: User = Depends(get_current_user)) -> User:
        if not user:
            logger.error("Authentication required but no user provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Extract all permissions from user's roles as "resource:action" strings
        user_perms = set()
        if user.roles:
            for role in user.roles:
                if role.permissions:
                    for perm in role.permissions:
                        user_perms.add(f"{perm.resource}:{perm.action}")
        
        logger.debug(f"User {user.id} permissions: {user_perms}")
        
        # Parse required permissions
        required_perms = set(permissions)
        
        if any_of:
            if not any(p in user_perms for p in required_perms):
                logger.warning(f"User {user.id} lacks required permissions. Required any of: {required_perms}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required: any of {list(required_perms)}",
                )
        else:
            missing = required_perms - user_perms
            if missing:
                logger.warning(f"User {user.id} missing required permissions: {missing}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Missing: {list(missing)}",
                )
        
        logger.info(f"User {user.id} authorized for permissions: {required_perms}")
        return user
    
    return checker


def has_permission(user: User, resource: str, action: str) -> bool:
    """
    Helper function to check if a user has a specific permission.
    
    Args:
        user: User object with loaded roles and permissions
        resource: Resource name (e.g., "user", "admin", "post")
        action: Action name (e.g., "read", "write", "delete", "create")
        
    Returns:
        True if user has the permission, False otherwise
        
    Example:
        if has_permission(user, "user", "delete"):
            # User can delete users
    """
    logger.debug(f"Checking permission for user {user.id}: {resource}:{action}")
    
    if not user.roles:
        logger.debug(f"User {user.id} has no roles")
        return False
    
    for role in user.roles:
        if role.permissions:
            for perm in role.permissions:
                if perm.resource == resource and perm.action == action:
                    logger.debug(f"User {user.id} has permission: {resource}:{action}")
                    return True
    
    logger.debug(f"User {user.id} lacks permission: {resource}:{action}")
    return False


def get_user_permissions(user: User) -> set[str]:
    """
    Get all permissions for a user as a set of "resource:action" strings.
    
    Args:
        user: User object with loaded roles and permissions
        
    Returns:
        Set of permission strings in format "resource:action"
        
    Example:
        perms = get_user_permissions(user)
        # Returns: {"user:read", "user:create", "admin:read", ...}
    """
    user_perms = set()
    if user.roles:
        for role in user.roles:
            if role.permissions:
                for perm in role.permissions:
                    user_perms.add(f"{perm.resource}:{perm.action}")
    
    logger.debug(f"Retrieved permissions for user {user.id}: {user_perms}")
    return user_perms


async def sync_permissions_to_db():
    """Sync collected permissions to database at startup."""
    logger.info(f"Starting permission sync with {len(REGISTERED_PERMISSIONS)} permissions")
    
    if not REGISTERED_PERMISSIONS:
        logger.info("No permissions to sync")
        return
    
    try:
        async with db_helper.session_factory() as session:
            created_count = 0
            existing_count = 0
            
            for resource, action in sorted(REGISTERED_PERMISSIONS):
                logger.debug(f"Processing permission: {resource}:{action}")
                
                # Check if permission exists
                stmt = select(Permission).where(
                    Permission.resource == resource,
                    Permission.action == action
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    # Create new permission
                    new_permission = Permission(
                        resource=resource,
                        action=action
                    )
                    session.add(new_permission)
                    logger.info(f"Created permission: {resource}:{action}")
                    created_count += 1
                else:
                    existing_count += 1
            
            await session.commit()
            logger.info(f"Permission sync committed to database")
            
            logger.info(
                f"Permission sync complete: {created_count} created, "
                f"{existing_count} already exist, "
                f"{len(REGISTERED_PERMISSIONS)} total"
            )
            
    except Exception as e:
        logger.error(f"Failed to sync permissions: {e}", exc_info=True)
        raise