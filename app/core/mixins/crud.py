from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, func, or_
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from core.schemas.pagination import Pagination , PaginatedResponse

# CREATE
async def create(session: AsyncSession, model, data: BaseModel):
    """Create a new record in the database"""
    try:
        obj = model(**data.model_dump(exclude_unset=True))
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj
    except SQLAlchemyError as e:
        await session.rollback()
        raise e


# GET DETAIL
async def get(session: AsyncSession, model, id: int):
    """Get a single record by ID"""
    try:
        result = await session.execute(select(model).where(model.id == id))
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        raise e


# GET ALL WITH PAGINATION
async def get_all(
    session: AsyncSession,
    model,
    pagination: Pagination,
    search_columns: Optional[List[str]] = None
) -> PaginatedResponse:
    """
    Get all records with pagination and optional search
    
    Args:
        session: AsyncSession instance
        model: SQLAlchemy model class
        pagination: Pagination parameters
        search_columns: List of column names to search in (e.g., ['name', 'email'])
    """
    try:
        # Base query
        query = select(model)
        
        # Apply search filter if search term and columns are provided
        if pagination.search and search_columns:
            search_filters = []
            for col_name in search_columns:
                if hasattr(model, col_name):
                    column = getattr(model, col_name)
                    search_filters.append(column.ilike(f"%{pagination.search}%"))
            
            if search_filters:
                query = query.where(or_(*search_filters))
        
        # Get total countrowcount
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.offset(pagination.offset).limit(pagination.limit)
        
        # Execute query
        result = await session.execute(query)
        items = result.scalars().all()
        
        # Calculate total pages
        total_pages = (total + pagination.limit - 1) // pagination.limit if total > 0 else 0
        
        return {
            "items": items,
            "total": total,
            "page": pagination.page,
            "limit": pagination.limit,
            "total_pages": total_pages
        }
    except SQLAlchemyError as e:
        raise e


# UPDATE
async def update(
    session: AsyncSession,
    model,
    id: int,
    data: BaseModel,
    exclude_unset: bool = True
):
    """
    Update a record by ID
    
    Args:
        exclude_unset: If True, only update fields that were explicitly set
    
    Returns:
        Updated object or None if not found
    """
    try:
        # First check if the record exists
        existing = await get(session, model, id)
        if not existing:
            return None
        
        # Get update data
        update_data = data.model_dump(exclude_unset=exclude_unset)
        
        if not update_data:
            return existing  # Nothing to update
        
        # Perform update
        await session.execute(
            sqlalchemy_update(model)
            .where(model.id == id)
            .values(**update_data)
        )
        await session.commit()
        
        # Refresh and return updated object
        await session.refresh(existing)
        return existing
    except SQLAlchemyError as e:
        await session.rollback()
        raise e


# PARTIAL UPDATE (PATCH)
async def partial_update(
    session: AsyncSession,
    model,
    id: int,
    data: Dict[str, Any]
):
    """Update specific fields of a record"""
    try:
        existing = await get(session, model, id)
        if not existing:
            return None
        
        if not data:
            return existing
        
        await session.execute(
            sqlalchemy_update(model)
            .where(model.id == id)
            .values(**data)
        )
        await session.commit()
        await session.refresh(existing)
        return existing
    except SQLAlchemyError as e:
        await session.rollback()
        raise e


# DELETE
async def delete(session: AsyncSession, model, id: int) -> bool:
    """Delete a record by ID. Returns True if deleted, False if not found"""
    try:
        # First check if the record exists
        existing = await get(session, model, id)
        if not existing:
            return False
        
        await session.execute(sqlalchemy_delete(model).where(model.id == id))
        await session.commit()
        return True
    except SQLAlchemyError as e:
        await session.rollback()
        raise e


# BULK DELETE
async def bulk_delete(session: AsyncSession, model, ids: List[int]) -> int:
    """Delete multiple records by IDs. Returns count of deleted records"""
    try:
        result = await session.execute(
            sqlalchemy_delete(model).where(model.id.in_(ids))
        )
        await session.commit()
        return result.rowcount
    except SQLAlchemyError as e:
        await session.rollback()
        raise e


# EXISTS CHECK
async def exists(session: AsyncSession, model, id: int) -> bool:
    """Check if a record exists by ID"""
    try:
        query = select(func.count()).select_from(model).where(model.id == id)
        result = await session.execute(query)
        count = result.scalar()
        return count > 0
    except SQLAlchemyError as e:
        raise e