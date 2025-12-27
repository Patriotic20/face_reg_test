from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from .schemas import (
    RoleCreateRequest, 
    RoleCreateResponse, 
    AssignPermissionRoleRequest, 
    AssignPermissionRoleListRequest, 
    RoleListResponse,
)

from core.mixins.crud import (
    create, 
    get, 
    get_all, 
    update, 
    delete
)

from models.role import Role
from models.permission import Permission
from models.association.role_permissions_association import RolePermissionAssociation

from core.logging import logging
from core.schemas.pagination import Pagination


logger = logging.getLogger(__name__)


class RoleServices:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_role(self, data: RoleCreateRequest):
        logger.info(f"Attempting to create role: {data.name}")
        
        try:
            role: Role = await create(
                session=self.session,
                model=Role,
                data=data,
            )
            logger.info(f"Role created successfully: {role.id} ({role.name})")
            return RoleCreateResponse(
                id=role.id,
                name=role.name,
                created_at=role.created_at,
                updated_at=role.updated_at,
            )
        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(f"Role creation failed - role name already exists: {data.name}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role name already exists",
            )
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error during role creation for {data.name}: {str(e)}",
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create role",
            )
    
    async def assign_permissions_to_role(self, data: AssignPermissionRoleRequest):
        logger.info(f"Attempting to assign permission {data.permission_id} to role: {data.role_id}")
        
        try:
            role_permission = await create(
                session=self.session,
                model=RolePermissionAssociation,
                data=data
            )
            logger.info(f"Permission {data.permission_id} assigned successfully to role {data.role_id}")
            
            return {
                "message": "Permission assigned successfully to role",
                "role_id": data.role_id,
                "permission_id": data.permission_id,
            }
        except IntegrityError as e:
            await self.session.rollback()
            error_msg = str(e.orig).lower()
            
            logger.warning(
                f"Integrity error while assigning permission "
                f"{data.permission_id} to role {data.role_id}: {error_msg}"
            )
            
            if "foreign key constraint" in error_msg or "violates foreign key" in error_msg:
                if "role" in error_msg:
                    logger.warning(f"Role not found: {data.role_id}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Role not found: {data.role_id}"
                    )
                elif "permission" in error_msg:
                    logger.warning(f"Permission not found: {data.permission_id}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Permission not found: {data.permission_id}"
                    )
            elif "unique constraint" in error_msg or "duplicate" in error_msg:
                logger.warning(
                    f"Permission {data.permission_id} already assigned to role {data.role_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Permission already assigned to this role"
                )
            else:
                logger.error(
                    f"IntegrityError during permission assignment: {str(e)}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to assign permission to role"
                )
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error during permission assignment: {str(e)}",
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign permission to role"
            )
        
    async def assign_permission_ids_to_role(self, data: AssignPermissionRoleListRequest):
        logger.info(f"Attempting to assign permissions {data.permission_ids} to role: {data.role_id}")
        
        try:
            for permission_id in data.permission_ids:
                logger.debug(
                    f"Assigning permission {permission_id} to role {data.role_id}"
                )
                self.session.add(
                    RolePermissionAssociation(
                        role_id=data.role_id,
                        permission_id=permission_id
                    )
                )
            await self.session.commit()
            logger.info(f"Permissions assigned successfully to role {data.role_id}")
            
            return {
                "message": "Permissions assigned successfully to role",
                "role_id": data.role_id,
                "permission_ids": data.permission_ids,
            }
        except IntegrityError as e:
            await self.session.rollback()
            error_msg = str(e.orig).lower()
            
            logger.warning(
                f"Integrity error while assigning permissions "
                f"to role {data.role_id}: {error_msg}"
            )
            
            if "foreign key constraint" in error_msg or "violates foreign key" in error_msg:
                if "role" in error_msg:
                    logger.warning(f"Role not found: {data.role_id}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Role not found: {data.role_id}"
                    )
                else:
                    logger.warning(
                        f"One or more permissions not found in {data.permission_ids}"
                    )
                    missing_permissions = []
                    for permission_id in data.permission_ids:
                        if not await get(model=Permission, id=permission_id, session=self.session):
                            missing_permissions.append(permission_id)
                    
                    if missing_permissions:
                        logger.warning(
                            f"Missing permissions detected: {missing_permissions}"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Permission(s) not found: {missing_permissions}"
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="One or more permissions not found"
                        )
            elif "unique constraint" in error_msg or "duplicate" in error_msg:
                logger.warning(
                    f"Duplicate permission assignment attempt for role {data.role_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="One or more permissions already assigned to this role"
                )
            else:
                logger.error(
                    f"IntegrityError during permission assignment: {str(e)}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to assign permissions to role"
                )
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error during permission assignment: {str(e)}",
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign permissions to role"
            )
    
    async def get_role_by_id(self, role_id: int):
        logger.info(f"Fetching role by id: {role_id}")
        
        role_data = await get(session=self.session, model=Role, id=role_id)
        
        if not role_data:
            logger.warning(f"Role not found: {role_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )

        
        else:
            logger.info(f"Role fetched successfully: {role_id}")
        
        return RoleCreateResponse.model_validate(role_data)
    
    async def get_all_roles(self, pagination: Pagination):
        logger.info(
            f"Fetching roles | page={pagination.page}, limit={pagination.limit}"
        )
        
        roles_data = await get_all(
            session=self.session, 
            model=Role, 
            pagination=pagination, 
            search_columns="name"
        )
        
        logger.info(
            f"Roles fetched successfully | total={roles_data['total']}"
        )
        
        return RoleListResponse(
            total_pages=roles_data["total_pages"],
            page=pagination.page,
            limit=pagination.limit,
            total=roles_data["total"],
            roles=roles_data["items"]
        )
        
    async def get_permissions_by_role_id(self, role_id: int):
        logger.info(f"Fetching permissions for role_id: {role_id}")
        
        try:
            stmt = (
                select(Role)
                .where(Role.id == role_id)
                .options(selectinload(Role.permissions))
            )
            
            result = await self.session.execute(stmt)
            role_data = result.scalars().one_or_none()
            
            if not role_data:
                logger.warning(f"Role not found when fetching permissions: {role_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Role not found"
                )
            
            # Format permissions as "resource:action"
            formatted_permissions = [
                f"{perm.resource}:{perm.action}" for perm in role_data.permissions
            ]
            
            logger.info(
                f"Successfully fetched {len(formatted_permissions)} permissions "
                f"for role: {role_id} ({role_data.name})"
            )
            
            return formatted_permissions
        
        except HTTPException:
            raise  # Let HTTP exceptions pass through (already logged)
        except Exception as e:
            logger.error(
                f"Unexpected error while fetching permissions for role {role_id}: {str(e)}",
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch permissions for role"
            )
    
    async def update_role(self, role_id: int, data: RoleCreateRequest):
        logger.info(f"Attempting to update role: {role_id}")
        
        role_data = await update(session=self.session, model=Role, id=role_id, data=data)
        
        if not role_data:
            logger.warning(f"Role not found for update: {role_id}")
        else:
            logger.info(f"Role updated successfully: {role_id}")
        
        return RoleCreateResponse.model_validate(role_data)
    
    async def delete_role(self, role_id: int):
        logger.info(f"Attempting to delete role: {role_id}")
        
        role_deleted = await delete(session=self.session, model=Role, id=role_id)
        
        if not role_deleted:
            logger.warning(f"Role not found for deletion: {role_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role not found: {role_id}"
            )
        
        logger.info(f"Role deleted successfully: {role_id}")
        return {"message": "Role deleted successfully", "role_id": role_id}
