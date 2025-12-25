from fastapi import APIRouter, Depends, Query, status, UploadFile , File
from sqlalchemy.ext.asyncio import AsyncSession

from core.db_helper import db_helper
from core.schemas.pagination import Pagination
from core.utils.dependencies import require_permission
from models.user import User

from .schemas import (
    EndQuizCreate,
    QuizCreateRequest,
    QuizListResponse,
    QuizResponse,
    QuizUpdate,
    QuizResultResponse,
)
from .services import QuizService

router = APIRouter(
    prefix="/quizzes",
    tags=["Quiz"],
)


def get_quiz_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> QuizService:
    return QuizService(session=session)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=QuizResponse,
)
async def create_quiz(
    user_id: int = Query(...),
    data: QuizCreateRequest = None,
    current_user: User = Depends(require_permission("quizzes:create")),
    service: QuizService = Depends(get_quiz_service),
) -> QuizResponse:
    """Create a new quiz for a subject"""
    return await service.create_quiz(
        data=data,
        user_id=user_id,
    )


@router.post(
    "/start",
    response_model=dict,
)
async def start_quiz(
    quiz_id: int,
    pin: str,
    user_image: UploadFile = File(),
    current_user: User = Depends(require_permission("quizzes:start")),
    service: QuizService = Depends(get_quiz_service),
) -> QuizResultResponse:
    """Start a quiz"""
    return await service.start_quiz(
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
        quiz_id=quiz_id,
        user_image=user_image,
        pin=pin,
    )


@router.post(
    "/end",
)
async def end_quiz(
    current_user: User = Depends(require_permission("quizzes:end")),
    data: EndQuizCreate = None,
    service: QuizService = Depends(get_quiz_service),
):
    """End a quiz"""
    return await service.end_quiz(
        data=data,
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
    )


@router.get(
    "",
    response_model=QuizListResponse,
)
async def get_all_quiz(
    pagination: Pagination = Depends(),
    current_user: User = Depends(require_permission("quizzes:all")),
    service: QuizService = Depends(get_quiz_service),
) -> QuizListResponse:
    """Get all quizzes with pagination"""
    return await service.get_all_quiz(
        pagination=pagination,
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
    )


@router.get(
    "/{quiz_id}",
    response_model=QuizResponse,
)
async def get_quiz_by_id(
    quiz_id: int,
    current_user: User = Depends(require_permission("quizzes:retrieve")),
    service: QuizService = Depends(get_quiz_service),
) -> QuizResponse:
    """Get a quiz by ID"""
    return await service.get_quiz_by_id(
        quiz_id=quiz_id,
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
    )


@router.put(
    "/{quiz_id}",
    response_model=QuizResponse,
)
async def update_quiz(
    quiz_id: int,
    current_user: User = Depends(require_permission("quizzes:update")),
    data: QuizUpdate = None,
    service: QuizService = Depends(get_quiz_service),
) -> QuizResponse:
    """Update a quiz"""
    return await service.update_quiz(
        quiz_id=quiz_id,
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
        data=data,
    )


@router.delete(
    "/{quiz_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_quiz(
    quiz_id: int,
    current_user: User = Depends(require_permission("quizzes:delete")),
    service: QuizService = Depends(get_quiz_service),
) -> None:
    """Delete a quiz"""
    await service.delete_quiz(
        quiz_id=quiz_id,
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
    )