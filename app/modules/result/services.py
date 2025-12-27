from sqlalchemy import select, func
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.schemas.pagination import Pagination
from core.logging import logging
from core.mixins.crud import get
from models.results import Result

from .schemas import ResultListResponse, ResultResponse

logger = logging.getLogger(__name__)


class ResultService:
    def __init__(self, session: AsyncSession):
        self.session = session
        logger.debug("ResultService initialized with AsyncSession")

    async def get_all_result_by_quiz(
        self,
        quiz_id: int,
        pagination: Pagination,
    ) -> ResultListResponse:
        """
        Get paginated results for a quiz with full pagination metadata.
        
        Args:
            quiz_id: The ID of the quiz to fetch results for
            pagination: Pagination parameters (page, limit)
            
        Returns:
            ResultListResponse containing paginated results and metadata
            
        Raises:
            HTTPException: If database query fails
        """
        try:
            logger.info(f"Fetching results for quiz_id={quiz_id}, page={pagination.page}, limit={pagination.limit}")

            # Count total items
            count_stmt = (
                select(func.count())
                .select_from(Result)
                .where(Result.quiz_id == quiz_id)
            )
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar_one()
            logger.debug(f"Total results found for quiz_id={quiz_id}: {total}")

    
            total_pages = (total + pagination.limit - 1) // pagination.limit if total > 0 else 0
            
            logger.debug(f"Pagination calculated: total_pages={total_pages}, offset={pagination.offset}")

            # Fetch paginated data
            stmt = (
                select(Result)
                .where(Result.quiz_id == quiz_id)
                .order_by(Result.id.desc())
                .limit(pagination.limit)
                .offset(pagination.offset)
            )
            result = await self.session.execute(stmt)
            items = result.scalars().all()
            logger.debug(f"Retrieved {len(items)} items for quiz_id={quiz_id}")

            response = ResultListResponse(
                limit=pagination.limit,
                page=pagination.page,
                total=total,
                total_pages=total_pages,
                results=items,
            )
            logger.info(f"Successfully fetched results for quiz_id={quiz_id}")
            return response

        except Exception as e:
            logger.error(f"Error fetching results for quiz_id={quiz_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch results"
            )

    async def get_by_id_result(self, result_id: int) -> ResultResponse:
        """
        Get a single result by ID.
        
        Args:
            result_id: The ID of the result to fetch
            
        Returns:
            ResultResponse containing the result data
            
        Raises:
            HTTPException: If result not found or database query fails
        """
        try:
            logger.info(f"Fetching result with result_id={result_id}")
            
            result_data = await get(
                session=self.session,
                model=Result,
                id=result_id,
            )
            
            if not result_data:
                logger.warning(f"Result not found for result_id={result_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Result not found"
                )
            
            logger.debug(f"Successfully retrieved result_id={result_id}")
            return ResultResponse.model_validate(result_data)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching result_id={result_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch result"
            )