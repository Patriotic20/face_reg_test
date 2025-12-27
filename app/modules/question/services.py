from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import pandas as pd

from .schemas import (
    CreateQuestionRequest,
    QuestionRequest,
    QuestionResponse,
    QuestionListResponse,
    QuestionUpdateRequest,
)

from models.questions import Question
from core.logging import logging
from core.mixins.crud import create
from core.schemas.pagination import Pagination
from core.config import settings

logger = logging.getLogger(__name__)


class QuestionsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_question(
        self,
        user_id: int,
        quiz_id: int,
        data: QuestionRequest,
    ) -> QuestionResponse:
        logger.info(f"Attempting to create question for user: {user_id}")

        try:
            question_data = CreateQuestionRequest(
                user_id=user_id,
                quiz_id=quiz_id,
                **data.model_dump(),
            )
            new_question = await create(
                session=self.session,
                model=Question,
                data=question_data,
            )
            logger.info(
                f"Question created successfully: {new_question.id} by user {user_id}"
            )
            return QuestionResponse.model_validate(new_question)
        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(
                f"Question creation failed for user {user_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invalid question data - user may not exist",
            )
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error during question creation for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create question",
            )

    async def create_questions_bulk_excel(
        self, user_id: int, quiz_id: int, file_content: bytes
    ) -> dict:
        logger.info(
            f"Attempting to create bulk questions from Excel for user: {user_id}"
        )

        try:
            # Read Excel file
            df = pd.read_excel(file_content)
            logger.info(f"Excel file parsed successfully with {len(df)} rows")

            # Validate required columns
            required_columns = [
                "text",
                "option_a",
                "option_b",
                "option_c",
                "option_d",
            ]
            missing_columns = [
                col for col in required_columns if col not in df.columns
            ]

            if missing_columns:
                logger.warning(f"Missing required columns: {missing_columns}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required columns: {', '.join(missing_columns)}. Required: {', '.join(required_columns)}",
                )

            # Filter out rows with NaN values in required columns
            df = df.dropna(subset=required_columns)

            if df.empty:
                logger.warning("No valid rows found in Excel file")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid questions found in the Excel file",
                )

            created_questions = []
            failed_questions = []

            # Create questions row by row
            for idx, row in df.iterrows():
                try:
                    question_data = CreateQuestionRequest(
                        user_id=user_id,
                        quiz_id=quiz_id,
                        text=str(row["text"]).strip(),
                        option_a=str(row["option_a"]).strip(),
                        option_b=str(row["option_b"]).strip(),
                        option_c=str(row["option_c"]).strip(),
                        option_d=str(row["option_d"]).strip(),
                    )

                    new_question = await create(
                        session=self.session,
                        model=Question,
                        data=question_data,
                    )

                    created_questions.append(
                        {
                            "id": new_question.id,
                            "text": new_question.text,
                        }
                    )
                    logger.info(f"Question created from bulk import: {new_question.id}")

                except IntegrityError as e:
                    await self.session.rollback()
                    failed_questions.append(
                        {
                            "row": idx + 2,
                            "text": row["text"],
                            "error": "Duplicate or invalid data",
                        }
                    )
                    logger.warning(
                        f"Failed to create question at row {idx + 2}: {str(e)}"
                    )
                except Exception as e:
                    await self.session.rollback()
                    failed_questions.append(
                        {
                            "row": idx + 2,
                            "text": row["text"],
                            "error": str(e),
                        }
                    )
                    logger.warning(
                        f"Failed to create question at row {idx + 2}: {str(e)}"
                    )

            if not created_questions:
                logger.error("No questions were created from bulk import")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create any questions from the Excel file",
                )

            logger.info(
                f"Bulk question creation completed: {len(created_questions)} created, {len(failed_questions)} failed"
            )

            return {
                "message": "Bulk questions created successfully",
                "created_count": len(created_questions),
                "failed_count": len(failed_questions),
                "created_questions": created_questions,
                "failed_questions": failed_questions if failed_questions else None,
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error during bulk question creation for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process Excel file",
            )

    async def get_question_by_id(
        self,
        user_id: int,
        user_role: str,
        question_id: int,
    ) -> QuestionResponse:
        logger.info(
            f"Fetching question {question_id} for user {user_id} with role {user_role}"
        )

        try:
            # Base query: always filter by question ID
            stmt = select(Question).where(Question.id == question_id)

            # Apply ownership restriction for non-admin users
            if user_role != settings.admin.name:
                stmt = stmt.where(Question.user_id == user_id)

            # Execute query
            result = await self.session.execute(stmt)
            question_data = result.scalar_one_or_none()

            # Handle not found or unauthorized access
            if not question_data:
                logger.warning(
                    f"Question {question_id} not found or access denied for user {user_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Question not found",
                )

            logger.info(
                f"Question {question_id} retrieved successfully for user {user_id}"
            )
            # Convert ORM model to Pydantic response
            return QuestionResponse.model_validate(question_data)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error fetching question {question_id} for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve question",
            )

    async def get_all_questions(
        self,
        user_id: int,
        user_role: str,
        pagination: Pagination,
    ) -> QuestionListResponse:
        logger.info(
            f"Fetching all questions for user {user_id} with role {user_role}, page: {pagination.page}, limit: {pagination.limit}"
        )

        try:
            # Base query
            stmt = select(Question)

            # Apply access control (non-admin sees only own questions)
            if user_role != settings.admin.name:
                logger.debug(f"Applying access control filter for user {user_id}")
                stmt = stmt.where(Question.user_id == user_id)

            # Count query (before limit/offset)
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_result = await self.session.execute(count_stmt)
            total = total_result.scalar_one()
            logger.debug(f"Total questions found: {total}")

            # Pagination
            stmt = stmt.order_by(Question.created_at.desc()).limit(pagination.limit).offset(pagination.offset)

            # Execute paginated query
            result = await self.session.execute(stmt)
            questions = result.scalars().all()

            total_pages = (
                (total + pagination.limit - 1) // pagination.limit
                if total > 0
                else 0
            )

            logger.info(
                f"Retrieved {len(questions)} questions for user {user_id}, total pages: {total_pages}"
            )

            # Serialize response
            return QuestionListResponse(
                total=total,
                total_pages=total_pages,
                limit=pagination.limit,
                page=pagination.page,
                questions=questions,
            )

        except Exception as e:
            logger.error(
                f"Unexpected error fetching questions for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve questions",
            )

    async def update_question(
        self,
        user_id: int,
        user_role: str,
        question_id: int,
        data: QuestionUpdateRequest,
    ) -> QuestionResponse:
        logger.info(
            f"Attempting to update question {question_id} for user {user_id}"
        )

        try:
            # Ensure question exists and user has access
            await self.get_question_by_id(
                user_id=user_id,
                user_role=user_role,
                question_id=question_id,
            )

            # Base update statement
            stmt = (
                update(Question)
                .where(Question.id == question_id)
                .values(**data.model_dump(exclude_unset=True))
                .returning(Question)
            )

            # Non-admin users can update only their own questions
            if user_role != settings.admin.name:
                stmt = stmt.where(Question.user_id == user_id)

            # Execute update
            result = await self.session.execute(stmt)
            updated_question = result.scalar_one_or_none()

            if not updated_question:
                logger.warning(
                    f"Question {question_id} not found for user {user_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Question not found",
                )

            await self.session.commit()
            logger.info(
                f"Question {question_id} updated successfully for user {user_id}"
            )

            return QuestionResponse.model_validate(updated_question)

        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error updating question {question_id} for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update question",
            )

    async def delete_question(
        self,
        user_id: int,
        user_role: str,
        question_id: int,
    ) -> None:
        logger.info(
            f"Attempting to delete question {question_id} for user {user_id}"
        )

        try:
            # Ensure question exists and access is valid
            await self.get_question_by_id(
                user_id=user_id,
                user_role=user_role,
                question_id=question_id,
            )

            # Base delete statement
            stmt = delete(Question).where(Question.id == question_id)

            # Non-admin users can delete only their own questions
            if user_role != settings.admin.name:
                stmt = stmt.where(Question.user_id == user_id)

            # Execute delete
            result = await self.session.execute(stmt)

            if result.rowcount == 0:
                logger.warning(
                    f"Question {question_id} not found for deletion for user {user_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Question not found",
                )

            await self.session.commit()
            logger.info(
                f"Question {question_id} deleted successfully for user {user_id}"
            )

        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error deleting question {question_id} for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete question",
            )           