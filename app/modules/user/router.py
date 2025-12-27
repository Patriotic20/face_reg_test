from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from core.db_helper import db_helper
from core.schemas.pagination import Pagination
from core.utils.dependencies import require_permission
from core.logging import logging

from models.user import User


from .services import UserServices
from .schemas import (
    AssignUserRoleRequest,
    AssignUserRoleListRequest,
    UserUpdateUsername,
)



logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["User Roles"],
    prefix="/users",
)


def get_user_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> UserServices:
    return UserServices(session)


@router.post("/{user_id}/roles", summary="Assign a role to a user")
async def assign_role(
    user_id: int,
    data: AssignUserRoleRequest,
    _: User = Depends(require_permission("users:assign")),
    service: UserServices = Depends(get_user_service),
):
    """
    Assign a role to a user.

    Parameters:
    - user_id: ID of the user
    - data: Role assignment data (role_id, etc.)
    """
    logger.info(f"POST /users/{user_id}/roles - Assigning role to user {user_id}")
    return await service.assign_role(data=data)


@router.post("/{user_id}/roles/bulk", summary="Bulk assign roles to a user")
async def assign_role_bulk(
    user_id: int,
    data: AssignUserRoleListRequest,
    _: User = Depends(require_permission("users:bulk")),
    service: UserServices = Depends(get_user_service),
):
    """
    Bulk assign multiple roles to a user.

    Parameters:
    - user_id: ID of the user
    - data: List of role assignment data
    """
    logger.info(
        f"POST /users/{user_id}/roles/bulk - Bulk assigning roles to user {user_id}"
    )
    return await service.assign_role_list(data=data)


@router.get("", summary="Get all users")
async def get_all_users(
    pagination: Pagination = Depends(),
    _: User = Depends(require_permission("users:all")),
    service: UserServices = Depends(get_user_service),
):
    """
    Get all users with pagination.

    Query parameters:
    - page: Page number (default: 1)
    - limit: Number of users per page (default: 10)
    """
    logger.info(
        f"GET /users - Fetching all users (page: {pagination.page}, limit: {pagination.limit})"
    )
    return await service.get_all_users(pagination=pagination)


@router.get("/{user_id}/roles", summary="Get user roles")
async def get_user_roles(
    user_id: int,
    _: User = Depends(require_permission("users:roles")),
    service: UserServices = Depends(get_user_service),
):
    """
    Get all roles assigned to a user.

    Parameters:
    - user_id: ID of the user
    """
    logger.info(f"GET /users/{user_id}/roles - Fetching roles for user {user_id}")
    return await service.get_user_with_roles(user_id=user_id)


@router.patch("/{user_id}/username", summary="Update user username")
async def update_username(
    user_id: int,
    data: UserUpdateUsername,
    _: User = Depends(require_permission("users:username")),
    service: UserServices = Depends(get_user_service),
):
    """
    Update a user's username.

    Parameters:
    - user_id: ID of the user
    - data: New username data
    """
    logger.info(f"PATCH /users/{user_id}/username - Updating username for user {user_id}")
    return await service.update_username(user_id=user_id, data=data)


@router.delete("/{user_id}/roles/{role_id}", summary="Remove role from user")
async def remove_user_role(
    user_id: int,
    role_id: int,
    _: User = Depends(require_permission("users:reassign")),
    service: UserServices = Depends(get_user_service),
):
    """
    Remove a role from a user (reassign user to role).

    Parameters:
    - user_id: ID of the user
    - role_id: ID of the role to remove
    """
    logger.info(
        f"DELETE /users/{user_id}/roles/{role_id} - Removing role {role_id} from user {user_id}"
    )
    data = AssignUserRoleRequest(user_id=user_id, role_id=role_id)
    return await service.reassignment_user_to_role(data=data)


@router.delete("/{user_id}", summary="Delete user")
async def delete_user(
    user_id: int,
    _: User = Depends(require_permission("users:delete")),
    service: UserServices = Depends(get_user_service),
):
    """
    Delete a user.

    Parameters:
    - user_id: ID of the user to delete
    """
    logger.info(f"DELETE /users/{user_id} - Deleting user {user_id}")
    return await service.delete_user(user_id=user_id)


@router.post("/upload/face")
async def upload_face(
    image_face: UploadFile = File(),
    service: UserServices = Depends(get_user_service),
    current_user: User = Depends(require_permission("users:upload")),
):
    return await service.save_user_image(user_id=current_user.id, image_file=image_face)