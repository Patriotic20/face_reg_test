from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from .services import PermissionService
from .schemas import CreatePermissionRequest, CreatePermissionResponse

from core.logging import logging
from core.schemas.pagination import Pagination
from core.db_helper import db_helper
from core.utils.dependencies import require_permission
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Permission"],
    prefix="/permission",
)


async def get_permission_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> PermissionService:
    return PermissionService(session=session)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CreatePermissionResponse,
    summary="Create a new permission",
)
async def create_permission(
    data: CreatePermissionRequest,
    _: User = Depends(require_permission("permission:create")),
    service: PermissionService = Depends(get_permission_service),
) -> CreatePermissionResponse:
    """
    Create a new permission.

    Parameters:
    - data: Permission creation data (name, resource, action, description)

    Returns:
    - Created permission with ID and details
    """
    logger.info(f"POST /permission - Creating new permission: {data.name}")
    result = await service.create_permission(data)
    logger.info(f"Permission created successfully: {result.id}")
    return result


@router.get(
    "/{permission_id}",
    summary="Get permission by ID",
)
async def get_permission_by_id(
    permission_id: int,
    _: User = Depends(require_permission("permission:retrieve")),
    service: PermissionService = Depends(get_permission_service),
) -> CreatePermissionResponse:
    """
    Get a permission by its ID.

    Parameters:
    - permission_id: ID of the permission to retrieve

    Returns:
    - Permission details with ID, name, resource, and action
    """
    logger.info(f"GET /permission/{permission_id} - Fetching permission {permission_id}")
    result = await service.get_permission_by_id(permission_id)
    logger.info(f"Permission {permission_id} retrieved successfully")
    return result


@router.get(
    "",
    summary="Get all permissions with pagination",
)
async def get_all_permissions(
    pagination: Pagination = Depends(),
     _: User = Depends(require_permission("permission:all")),
    service: PermissionService = Depends(get_permission_service),
):
    """
    Get all permissions with pagination.

    Query parameters:
    - page: Page number (default: 1)
    - limit: Number of permissions per page (default: 10)

    Returns:
    - Paginated list of permissions
    """
    logger.info(
        f"GET /permission - Fetching all permissions (page: {pagination.page}, limit: {pagination.limit})"
    )
    result = await service.get_all_permissions(pagination)
    logger.info(
        f"Retrieved {len(result.get('permissions', []))} permissions (total: {result.get('total', 0)})"
    )
    return result


@router.delete(
    "/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a permission",
)
async def delete_permission(
    permission_id: int,
    _: User = Depends(require_permission("permission:delete")),
    service: PermissionService = Depends(get_permission_service),
) -> None:
    """
    Delete a permission by ID.

    Parameters:
    - permission_id: ID of the permission to delete

    Returns:
    - No content (204 status code)
    """
    logger.info(f"DELETE /permission/{permission_id} - Deleting permission {permission_id}")
    await service.delete_permission(permission_id)
    logger.info(f"Permission {permission_id} deleted successfully")


@router.get(
    "/resource/{resource}",
    summary="Get permissions by resource",
)
async def get_permission_by_resource(
    resource: str,
    _: User = Depends(require_permission("permission:resource")),
    service: PermissionService = Depends(get_permission_service),
) -> dict:
    """
    Get all permissions for a specific resource.

    Parameters:
    - resource: Resource name (e.g., 'questions', 'users', 'roles')

    Returns:
    - List of permissions for the resource in 'resource:action' format
    """
    logger.info(
        f"GET /permission/resource/{resource} - Fetching permissions for resource: {resource}"
    )
    result = await service.get_permission_by_resource(resource)
    logger.info(f"Permissions retrieved for resource: {resource}")
    return result