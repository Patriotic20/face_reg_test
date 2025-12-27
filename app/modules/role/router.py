from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession



from core.schemas.pagination import Pagination
from core.utils.dependencies import require_permission
from core.db_helper import db_helper
from core.logging import logging
from models.user import User

from .services import RoleServices
from .schemas import (
    RoleCreateRequest,
    RoleCreateResponse,
    AssignPermissionRoleRequest,
    AssignPermissionRoleListRequest,
    RoleListResponse,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Role"],
    prefix="/roles",
)


def get_role_services(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> RoleServices:
    return RoleServices(session=session)


@router.post(
    "/",
    response_model=RoleCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
)
async def create_role(
    data: RoleCreateRequest,
    _: User = Depends(require_permission("roles:create")),
    role_services: RoleServices = Depends(get_role_services),
) -> RoleCreateResponse:
    """
    Create a new role.

    Parameters:
    - data: Role creation data (name, description, etc.)

    Returns:
    - Created role with ID and details
    """
    logger.info(f"POST /roles - Creating new role: {data.name}")
    result = await role_services.create_role(data)
    logger.info(f"Role created successfully: {result.id}")
    return result


@router.post(
    "/{role_id}/permissions",
    status_code=status.HTTP_200_OK,
    summary="Assign a single permission to a role",
)
async def assign_permission_to_role(
    role_id: int,
    data: AssignPermissionRoleRequest,
    _: User = Depends(require_permission("roles:assign")),
    role_services: RoleServices = Depends(get_role_services),
) -> dict:
    """
    Assign a single permission to a role.

    Parameters:
    - role_id: ID of the role
    - data: Permission assignment data (permission_id, role_id)

    Returns:
    - Confirmation of the assignment
    """
    logger.info(
        f"POST /roles/{role_id}/permissions - Assigning permission to role {role_id}"
    )
    result = await role_services.assign_permissions_to_role(data)
    logger.info(f"Permission assigned to role {role_id}")
    return result


@router.post(
    "/{role_id}/permissions/bulk",
    status_code=status.HTTP_200_OK,
    summary="Assign multiple permissions to a role",
)
async def assign_permissions_to_role_bulk(
    role_id: int,
    data: AssignPermissionRoleListRequest,
    _: User = Depends(require_permission("roles:bulk")),
    role_services: RoleServices = Depends(get_role_services),
) -> dict:
    """
    Assign multiple permissions to a role in bulk.

    Parameters:
    - role_id: ID of the role
    - data: List of permission assignment data

    Returns:
    - Confirmation with count of assigned permissions
    """
    logger.info(
        f"POST /roles/{role_id}/permissions/bulk - Bulk assigning permissions to role {role_id}"
    )
    result = await role_services.assign_permission_ids_to_role(data)
    logger.info(f"Bulk permissions assigned to role {role_id}")
    return result


@router.get(
    "/{role_id}",
    response_model=RoleCreateResponse,
    summary="Get role by ID",
)
async def get_role(
    role_id: int,
    _: User = Depends(require_permission("roles:retrieve")),
    role_services: RoleServices = Depends(get_role_services),
) -> RoleCreateResponse:
    """
    Get a role by its ID.

    Parameters:
    - role_id: ID of the role to retrieve

    Returns:
    - Role details with ID, name, and description
    """
    logger.info(f"GET /roles/{role_id} - Fetching role {role_id}")
    result = await role_services.get_role_by_id(role_id)
    logger.info(f"Role {role_id} retrieved successfully")
    return result


@router.get(
    "/",
    response_model=RoleListResponse,
    summary="Get all roles with pagination",
)
async def get_roles(
    pagination: Pagination = Depends(),
    _: User = Depends(require_permission("roles:all")),
    role_services: RoleServices = Depends(get_role_services),
) -> RoleListResponse:
    """
    Get all roles with pagination.

    Query parameters:
    - page: Page number (default: 1)
    - limit: Number of roles per page (default: 10)

    Returns:
    - Paginated list of roles
    """
    logger.info(
        f"GET /roles - Fetching all roles (page: {pagination.page}, limit: {pagination.limit})"
    )
    result = await role_services.get_all_roles(pagination)
    logger.info(
        f"Retrieved {len(result.roles)} roles (total: {result.total})"
    )
    return result


@router.get(
    "/{role_id}/permissions",
    summary="Get all permissions for a role",
)
async def get_permissions_by_role(
    role_id: int,
    _: User = Depends(require_permission("roles:permissions")),
    role_services: RoleServices = Depends(get_role_services),
) -> dict:
    """
    Get all permissions assigned to a role in 'resource:action' format.

    Parameters:
    - role_id: ID of the role

    Returns:
    - List of permissions in 'resource:action' format
    """
    logger.info(
        f"GET /roles/{role_id}/permissions - Fetching permissions for role {role_id}"
    )
    result = await role_services.get_permissions_by_role_id(role_id=role_id)
    logger.info(f"Permissions retrieved for role {role_id}")
    return result


@router.patch(
    "/{role_id}",
    response_model=RoleCreateResponse,
    summary="Update a role",
)
async def update_role(
    role_id: int,
    data: RoleCreateRequest,
    _: User = Depends(require_permission("roles:update")),
    role_services: RoleServices = Depends(get_role_services),
) -> RoleCreateResponse:
    """
    Update a role.

    Parameters:
    - role_id: ID of the role to update
    - data: Updated role data (name, description, etc.)

    Returns:
    - Updated role details
    """
    logger.info(f"PATCH /roles/{role_id} - Updating role {role_id}")
    result = await role_services.update_role(role_id, data)
    logger.info(f"Role {role_id} updated successfully")
    return result


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a role",
)
async def delete_role(
    role_id: int,
    _: User = Depends(require_permission("roles:delete")),
    role_services: RoleServices = Depends(get_role_services),
) -> None:
    """
    Delete a role.

    Parameters:
    - role_id: ID of the role to delete

    Returns:
    - No content (204 status code)
    """
    logger.info(f"DELETE /roles/{role_id} - Deleting role {role_id}")
    await role_services.delete_role(role_id)
    logger.info(f"Role {role_id} deleted successfully")