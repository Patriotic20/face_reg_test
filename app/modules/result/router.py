from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db_helper import db_helper
from core.logging import logging
from core.schemas.pagination import Pagination
from core.utils.dependencies import require_permission
from models.user import User

from .services import ResultService

router = APIRouter(tags=["Result"], prefix="/results")


def get_result_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> ResultService:
    return ResultService(session=session)


@router.get("/{result_id}")
async def get_by_id_result(
    result_id: int,
    service: ResultService = Depends(get_result_service),
    _: User = Depends(require_permission("results:retrieve")),
):
    try:
        logging.info(f"Fetching result with ID: {result_id}")
        result = await service.get_by_id_result(result_id=result_id)
        logging.info(f"Successfully retrieved result with ID: {result_id}")
        return result
    except Exception as e:
        logging.error(f"Error fetching result with ID {result_id}: {str(e)}")
        raise


@router.get("")
async def get_all_result_by_quiz(
    quiz_id: int,
    pagination: Pagination = Depends(),
    service: ResultService = Depends(get_result_service),
    _: User = Depends(require_permission("results:all")),
):
    try:
        logging.info(
            f"Fetching results for quiz ID: {quiz_id} with pagination: {pagination}"
        )
        results = await service.get_all_result_by_quiz(
            quiz_id=quiz_id, pagination=pagination
        )
        logging.info(f"Successfully retrieved results for quiz ID: {quiz_id}")
        return results
    except Exception as e:
        logging.error(f"Error fetching results for quiz ID {quiz_id}: {str(e)}")
        raise