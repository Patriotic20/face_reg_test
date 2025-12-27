from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.logging import logging
from core.config import settings
from core.db_helper import db_helper

from models.user import User
from models.role import Role
from models.permission import Permission
from models.association.user_role_association import UserRoleAssociation
from models.association.role_permissions_association import RolePermissionAssociation

from modules.auth.services import AuthService
from modules.user.services import UserServices
from modules.role.services import RoleServices

from modules.auth.schemas import UserCreate
from modules.user.schemas import AssignUserRoleRequest
from modules.role.schemas import AssignPermissionRoleListRequest

logger = logging.getLogger(__name__)


async def create_admin(session: AsyncSession) -> User:
    """
    Create admin user if it does not exist.
    Returns existing or newly created admin user.
    """
    try:
        stmt = select(User).where(User.username == settings.admin.username)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if user:
            logger.info("Admin user already exists")
            return user

        auth_service = AuthService(session=session)

        user_data = UserCreate(
            username=settings.admin.username,
            password=settings.admin.password,
        )

        user = await auth_service.register_user(credentials=user_data)
        logger.info("Admin user created successfully")
        return user

    except Exception:
        logger.exception("Failed to create admin user")
        raise


async def assign_user_role(session: AsyncSession, user_id: int) -> int:
    """
    Assign admin role to user if not assigned.
    Returns admin role ID.
    """
    try:
        stmt = select(Role).where(Role.name == settings.admin.name)
        result = await session.execute(stmt)
        role = result.scalars().first()

        if role is None:
            raise ValueError("Admin role not found")

        stmt = select(UserRoleAssociation).where(
            UserRoleAssociation.user_id == user_id,
            UserRoleAssociation.role_id == role.id,
        )
        result = await session.execute(stmt)
        existing = result.scalars().first()

        if existing:
            logger.info("Admin role already assigned to user")
            return role.id

        user_service = UserServices(session=session)
        assign_data = AssignUserRoleRequest(
            user_id=user_id,
            role_id=role.id,
        )

        await user_service.assign_role(data=assign_data)
        logger.info("Admin role assigned to user")

        return role.id

    except Exception:
        logger.exception("Failed to assign admin role to user")
        raise


async def assign_role_permissions(session: AsyncSession, role_id: int) -> None:
    """
    Assign all missing permissions to admin role.
    """
    try:
        # All permissions
        stmt = select(Permission)
        result = await session.execute(stmt)
        permissions = result.scalars().all()

        if not permissions:
            raise ValueError("No permissions found")

        # Existing role-permission mappings
        stmt = select(RolePermissionAssociation.permission_id).where(
            RolePermissionAssociation.role_id == role_id
        )
        result = await session.execute(stmt)
        existing_permission_ids = set(result.scalars().all())

        permission_ids = [
            p.id for p in permissions if p.id not in existing_permission_ids
        ]

        if not permission_ids:
            logger.info("All permissions already assigned to admin role")
            return

        role_service = RoleServices(session=session)
        data = AssignPermissionRoleListRequest(
            role_id=role_id,
            permission_ids=permission_ids,
        )

        await role_service.assign_permission_ids_to_role(data=data)
        logger.info(
            "Assigned %d permissions to admin role",
            len(permission_ids),
        )

    except Exception:
        logger.exception("Failed to assign permissions to admin role")
        raise


async def setup_admin_user() -> User:
    """
    Bootstrap admin user safely.
    """
    try:
        async with db_helper.session_factory() as session:
            logger.info("Starting admin bootstrap process")

            admin_user = await create_admin(session)
            role_id = await assign_user_role(session, admin_user.id)
            await assign_role_permissions(session, role_id)

            logger.info("Admin bootstrap completed successfully")
            return admin_user

    except Exception:
        logger.exception("Admin bootstrap failed")
        raise

