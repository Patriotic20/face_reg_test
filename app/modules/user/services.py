from sqlalchemy import select, delete, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import (
    AssignUserRoleRequest,
    AssignUserRoleListRequest,
    UserResponse,
    UserUpdateUsername,
    UserListResponse,
    UserListItem,
)

from models.association.user_role_association import UserRoleAssociation
from models.user import User
from models.role import Role
from core.utils.get_user_by_id import get_user_by_id
from core.mixins.crud import create, get, get_all, update, delete
from core.schemas.pagination import Pagination
from core.utils.save_file import save_file
from core.logging import logging

logger = logging.getLogger(__name__)


class UserServices:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def assign_role(self, data: AssignUserRoleRequest):
        """Assign a single role to a user."""
        logger.info(f"Assigning role {data.role_id} to user {data.user_id}")

        # Check user exists
        if not await get(session=self.session, model=User, id=data.user_id):
            logger.warning(f"User not found: {data.user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check role exists
        if not await get(model=Role, id=data.role_id, session=self.session):
            logger.warning(f"Role not found: {data.role_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )

        try:
            await create(
                model=UserRoleAssociation, data=data, session=self.session
            )
            logger.info(
                f"Role {data.role_id} assigned successfully to user {data.user_id}"
            )
        except IntegrityError:
            await self.session.rollback()
            logger.error(
                f"Role {data.role_id} already assigned to user {data.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role already assigned to this user",
            )

        return {
            "message": "Role assigned successfully",
            "user_id": data.user_id,
            "role_id": data.role_id,
        }

    async def assign_role_list(self, data: AssignUserRoleListRequest):
        """Assign multiple roles to a user."""
        logger.info(f"Assigning {len(data.role_ids)} roles to user {data.user_id}")

        # Check user exists
        if not await get(model=User, id=data.user_id, session=self.session):
            logger.warning(f"User not found: {data.user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check roles exist
        for role_id in data.role_ids:
            if not await get(model=Role, id=role_id, session=self.session):
                logger.warning(f"Role not found: {role_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Role not found: {role_id}",
                )

        try:
            for role_id in data.role_ids:
                self.session.add(
                    UserRoleAssociation(user_id=data.user_id, role_id=role_id)
                )
            await self.session.commit()
            logger.info(
                f"Roles {data.role_ids} assigned successfully to user {data.user_id}"
            )

        except IntegrityError:
            await self.session.rollback()
            logger.error(f"Some roles already assigned to user {data.user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more roles already assigned",
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
        logger.info(f"Fetching user {user_id} with roles")

        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles))
        )

        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )

        logger.info(f"User {user_id} retrieved successfully with roles")
        return UserResponse.model_validate(user)

    async def reassignment_user_to_role(self, data: AssignUserRoleRequest):
        """Remove a role assignment from a user."""
        logger.info(
            f"Removing role {data.role_id} assignment from user {data.user_id}"
        )

        if not await get(session=self.session, model=User, id=data.user_id):
            logger.warning(f"User not found: {data.user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {data.user_id} not found",
            )

        # Check role exists
        if not await get(model=Role, id=data.role_id, session=self.session):
            logger.warning(f"Role not found: {data.role_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id {data.role_id} not found",
            )

        stmt = delete(UserRoleAssociation).where(
            and_(
                UserRoleAssociation.user_id == data.user_id,
                UserRoleAssociation.role_id == data.role_id,
            )
        )

        result = await self.session.execute(stmt)
        await self.session.commit()

        if result.rowcount == 0:
            logger.warning(
                f"Role assignment not found for user {data.user_id} and role {data.role_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role assignment not found for user {data.user_id} and role {data.role_id}",
            )

        logger.info(
            f"Role {data.role_id} removed from user {data.user_id} successfully"
        )
        return {
            "message": "Role successfully removed from user",
            "user_id": data.user_id,
            "role_id": data.role_id,
        }

    async def get_all_users(self, pagination: Pagination):
        """Retrieve all users with pagination."""
        logger.info(
            f"Fetching all users - page: {pagination.page}, limit: {pagination.limit}"
        )

        all_users = await get_all(
            model=User,
            pagination=pagination,
            search_columns="username",
            session=self.session,
        )

        logger.info(
            f"Retrieved {len(all_users['items'])} users from {all_users['total']} total"
        )
        return UserListResponse(
            users=all_users["items"],
            limit=pagination.limit,
            page=pagination.page,
            total=all_users["total"],
            total_pages=all_users["total_pages"],
        )

    async def update_username(self, user_id: int, data: UserUpdateUsername):
        """Update a user's username."""
        logger.info(f"Updating username for user {user_id}")

        user_data = await update(
            model=User, data=data, id=user_id, session=self.session
        )

        logger.info(f"Username updated successfully for user {user_id}")
        return UserListItem.model_validate(user_data)

    async def delete_user(self, user_id: int):
        """Delete a user by ID."""
        logger.info(f"Deleting user {user_id}")

        delete_data = await delete(id=user_id, model=User, session=self.session)

        if not delete_data:
            logger.warning(f"User not found for deletion: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )

        logger.info(f"User {user_id} deleted successfully")
        return {"message": "User deleted successfully", "user_id": user_id}

    async def save_user_image(self, user_id: int, image_file: UploadFile):
        """Save an image file for a user."""
        logger.info(f"Saving image for user {user_id}, filename: {image_file.filename}")

        try:
            # Fetch the user
            user_data = await get_user_by_id(session=self.session, user_id=user_id)

            # Save the file
            image_path = save_file(file=image_file, subdir="user")
            logger.debug(f"Image saved to path: {image_path}")

            # Update the user object
            user_data.image = image_path

            # Commit changes
            await self.session.commit()

            logger.info(f"Image saved successfully for user {user_id}")
            return image_path

        except Exception as e:
            logger.error(f"Error saving image for user {user_id}: {str(e)}")
            await self.session.rollback()
            raise e