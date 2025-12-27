from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from .services import QuestionsService
from .schemas import QuestionUpdateRequest, QuestionRequest

from core.schemas.pagination import Pagination
from core.db_helper import db_helper
from core.logging import logging
from core.utils.dependencies import require_permission
from models.user import User
from core.utils.save_file import save_file


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/questions",
    tags=["Questions"],
)


def get_question_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> QuestionsService:
    return QuestionsService(session=session)


@router.post("", summary="Create a single question")
async def create_question(
    quiz_id: int,
    data: QuestionRequest,
    current_user: User = Depends(require_permission("questions:create")),
    service: QuestionsService = Depends(get_question_service),
):
    """
    Create a single question.

    Parameters:
    - user_id: ID of the user creating the question
    - data: Question data (text, option_a, option_b, option_c, option_d)
    """
    logger.info(f"POST /questions - User {current_user.id} creating a question")
    return await service.create_question(
        user_id=current_user.id, 
        quiz_id=quiz_id, 
        data=data
    )

@router.post("/upload")
async def upload_file(
    upload_file: UploadFile = File(),
    _: User = Depends(require_permission("questions:upload")),
):
    url = save_file(file=upload_file, subdir="question")
    return {"file_url": url}

@router.post(
    "/bulk-upload",
    summary="Bulk create questions from Excel file",
)
async def create_questions_bulk(
    quiz_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("questions:batch")),
    service: QuestionsService = Depends(get_question_service),
):
    """
    Bulk create questions from an Excel file.

    Expected file type: .xlsx

    Excel file should contain the following columns:
    - text: Question text (required)
    - option_a: Option A (required)
    - option_b: Option B (required)
    - option_c: Option C (required)
    - option_d: Option D (required)

    Parameters:
    - user_id: ID of the user uploading the file
    - file: Excel file (.xlsx)
    """
    logger.info(f"POST /questions/bulk-upload - User {current_user.id} uploading Excel file")
    file_content = await file.read()
    return await service.create_questions_bulk_excel(
        user_id=current_user.id,
        quiz_id=quiz_id,
        file_content=file_content,
    )


@router.get("/{question_id}", summary="Get question by ID")
async def get_question_by_id(
    question_id: int,
    current_user: User = Depends(require_permission("questions:retrieve")),
    service: QuestionsService = Depends(get_question_service),
):
    """
    Get a question by its ID.

    Parameters:
    - user_id: ID of the user making the request
    - user_role: Role of the user (admin or regular)
    - question_id: ID of the question to retrieve

    Access control:
    - Admin users can view any question
    - Regular users can only view their own questions
    """
    logger.info(
        f"GET /questions/{question_id} - User {current_user.id} fetching question"
    )
    return await service.get_question_by_id(
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
        question_id=question_id,
    )


@router.get("", summary="Get all questions")
async def get_all_questions(
    pagination: Pagination = Depends(),
    current_user: User = Depends(require_permission("questions:all")),
    service: QuestionsService = Depends(get_question_service),
):
    """
    Get all questions with pagination.

    Parameters:
    - user_id: ID of the user making the request
    - user_role: Role of the user (admin or regular)
    - pagination: Pagination object (page, limit)

    Access control:
    - Admin users see all questions
    - Regular users see only their own questions
    """
    logger.info(
        f"GET /questions - User {current_user.id} fetching questions (page: {pagination.page}, limit: {pagination.limit})"
    )
    return await service.get_all_questions(
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
        pagination=pagination,
    )


@router.put("/{question_id}", summary="Update question")
async def update_question(
    question_id: int,
    data: QuestionUpdateRequest,
    current_user: User = Depends(require_permission("questions:update")),
    service: QuestionsService = Depends(get_question_service),
):
    """
    Update a question.

    Parameters:
    - user_id: ID of the user making the request
    - user_role: Role of the user (admin or regular)
    - question_id: ID of the question to update
    - data: Updated question data (optional fields)

    Access control:
    - Admin users can update any question
    - Regular users can only update their own questions
    """
    logger.info(
        f"PUT /questions/{question_id} - User {current_user.id} updating question"
    )
    return await service.update_question(
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
        question_id=question_id,
        data=data,
    )


@router.delete("/{question_id}", summary="Delete question")
async def delete_question(
    question_id: int,
    current_user: User = Depends(require_permission("questions:delete")),
    service: QuestionsService = Depends(get_question_service),
):
    """
    Delete a question.

    Parameters:
    - user_id: ID of the user making the request
    - user_role: Role of the user (admin or regular)
    - question_id: ID of the question to delete

    Access control:
    - Admin users can delete any question
    - Regular users can only delete their own questions
    """
    logger.info(
        f"DELETE /questions/{question_id} - User {current_user.id} deleting question"
    )
    return await service.delete_question(
        user_id=current_user.id,
        user_role=current_user.roles[0].name,
        question_id=question_id,
    )