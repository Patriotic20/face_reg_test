from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from .schemas import (
    CreatePermissionRequest, 
    CreatePermissionResponse
)

from core.mixins.crud import (
    create, 
    get, 
    get_all, 
    delete
)
from core.logging import logging
from core.schemas.pagination import Pagination
from models.permission import Permission

logger = logging.getLogger(__name__)

class PermissionService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_permission(self, data: CreatePermissionRequest):
        logger.info(f"Attempting to create permission: {data.resource}.{data.action}")
        
        try:
            permission: Permission = await create(
                session=self.session,
                model=Permission,
                data=data,
            )
            logger.info(f"Permission created successfully: {permission.id} ({permission.resource}.{permission.action})")
            return CreatePermissionResponse(
                id=permission.id,
                resource=permission.resource,
                action=permission.action,
                created_at=permission.created_at,
                updated_at=permission.updated_at,
            )
        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(
                f"Permission creation failed - permission already exists: {data.resource}.{data.action}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Permission for resource '{data.resource}' and action '{data.action}' already exists",
            )
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error during permission creation for {data.resource}.{data.action}: {str(e)}",
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create permission",
            )
    
    async def get_permission_by_id(self, permission_id: int):
        logger.info(f"Fetching permission by ID: {permission_id}")
        
        try:
            permission_data = await get(
                session=self.session, 
                model=Permission, 
                id=permission_id
            )
            
            if not permission_data:
                logger.warning(f"Permission not found with ID: {permission_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Permission not found"
                )
            
            logger.info(f"Permission retrieved successfully: {permission_data.id}")
            return permission_data
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching permission by ID {permission_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch permission",
            )
    
    async def get_permission_by_resource(self, resource: str):
        logger.info(f"Fetching permissions by resource: {resource}")
        
        try:
            stmt = select(Permission).where(Permission.resource == resource)
            result = await self.session.execute(stmt)
            permissions = result.scalars().all()
            
            if not permissions:
                logger.warning(f"No permissions found for resource: {resource}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No permissions found for resource '{resource}'",
                )
            
            logger.info(f"Retrieved {len(permissions)} permissions for resource: {resource}")
            return permissions
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching permissions by resource '{resource}': {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch permissions",
            )
    
    async def get_all_permissions(self, pagination: Pagination):
        logger.info(f"Fetching all permissions with pagination: offset={pagination.offset}, limit={pagination.limit}")
        
        try:
            permissions = await get_all(
                session=self.session,
                model=Permission,
                pagination=pagination,
                search_columns=["resource", "action"]
            )
            
            if not permissions:
                logger.info("No permissions found in database")
                return []
            
            logger.info(f"Retrieved {len(permissions)} permissions")
            return permissions
        except Exception as e:
            logger.error(f"Error fetching all permissions: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch permissions",
            )

    async def delete_permission(self, permission_id: int):
        logger.info(f"Attempting to delete permission: {permission_id}")
        
        try:
            is_deleted = await delete(
                session=self.session,
                model=Permission,
                id=permission_id
            )
            
            if not is_deleted:
                logger.warning(f"Permission not found for deletion with ID: {permission_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Permission not deleted successfully",
                )
            
            logger.info(f"Permission deleted successfully: {permission_id}")
            return {
                "message": "Permission deleted successfully",
                "id": permission_id,
            }
        except HTTPException:
            raise
        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(
                f"Permission deletion failed - permission may be in use: {permission_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete permission - it is currently in use by roles",
            )
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error during permission deletion for ID {permission_id}: {str(e)}",
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete permission",
            )
