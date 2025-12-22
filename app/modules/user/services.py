from sqlalchemy import select, delete, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from .schemas import AssignUserRoleRequest, AssignUserRoleListRequest, UserResponse, UserUpdateUsername, UserListResponse, UserListItem
from models.association.user_role_association import UserRoleAssociation
from models.user import User
from models.role import Role
from core.mixins.crud import create, get, get_all, update, delete
from core.schemas.pagination import Pagination
from sqlalchemy.ext.asyncio import AsyncSession



class UserServices:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def assign_role(self, data: AssignUserRoleRequest):
        # Check user exists
        if not await get(session=self.session, model=User, id=data.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check role exists
        if not await get(model=Role, id=data.role_id, session=self.session):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
            
        

        try:
            await create(
                model=UserRoleAssociation,
                data=data,
                session=self.session
            )
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role already assigned to this user"
            )

        return {
            "message": "Role assigned successfully",
            "user_id": data.user_id,
            "role_id": data.role_id,
        }

    async def assign_role_list(self, data: AssignUserRoleListRequest):
            # Check user exists
            if not await get(model=User, id=data.user_id, session=self.session):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Check roles exist
            for role_id in data.role_ids:
                if not await get(model=Role, id=role_id, session=self.session):
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Role not found: {role_id}"
                    )

            try:
                for role_id in data.role_ids:
                    self.session.add(
                        UserRoleAssociation(
                            user_id=data.user_id,
                            role_id=role_id
                        )
                    )
                await self.session.commit()

            except IntegrityError:
                await self.session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more roles already assigned"
                )

            return {
                "message": "Roles assigned successfully",
                "user_id": data.user_id,
                "role_ids": data.role_ids,
            }
            
    async def get_user_with_roles(self, user_id: int) -> User:
        """
        Retrieve a user with their assigned roles.
        
        Args:
            user_id: The ID of the user to retrieve
            
        Returns:
            User object with roles loaded
            
        Raises:
            HTTPException: 404 if user not found
        """
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles))
        )
        
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        return UserResponse.model_validate(user)
    
    
    async def reassignment_user_to_role(self, data: AssignUserRoleRequest):
        
        if not await get(session=self.session, model=User, id=data.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {data.user_id} not found"
            )

        # Check role exists
        if not await get(model=Role, id=data.role_id, session=self.session):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id {data.role_id} not found"
            )
            
            
        stmt = (
            delete(UserRoleAssociation)
            .where(
                and_(
                    UserRoleAssociation.user_id == data.user_id,
                    UserRoleAssociation.role_id == data.role_id
                )
            )
        )
        
        result = await self.session.execute(stmt)  # Fixed: execute(), not call
        await self.session.commit() 
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role assignment not found for user {data.user_id} and role {data.role_id}"
            )
        
        return {
            "message": "Role successfully removed from user",
            "user_id": data.user_id,
            "role_id": data.role_id
        }
        
    async def get_all_users(self, pagination: Pagination):
        all_users = await get_all(model=User, pagination=pagination, search_columns="username", session=self.session)
        return UserListResponse(
            users=all_users["items"],
            limit=pagination.limit,
            page=pagination.page,
            total=all_users["total"],
            total_pages=all_users["total_pages"]
        )
    
    async def update_username(self, user_id: int ,data: UserUpdateUsername):
        user_data = await update(model=User, data=data, id=user_id, session=self.session)
        return UserListItem.model_validate(user_data)
    
    
    async def delete_user(self, user_id: int):
        delete_data = await delete(
            id=user_id, 
            model=User, 
            session=self.session
        )
        
        if not delete_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,  # Changed from 400 to 404
                detail=f"User with id {user_id} not found"
            )
        
        return {
            "message": "User deleted successfully",
            "user_id": user_id
        }