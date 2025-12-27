from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status, UploadFile

from core.logging import logging
from core.mixins.crud import create
from core.config import settings
from core.schemas.pagination import Pagination

from models.results import Result
from models.quiz import Quiz
from models.user import User

from .schemas import (
    QuizUpdate,
    QuizCreateRequest,
    QuizCreate,
    QuizResponse,
    QuizListResponse,
    EndQuizCreate,
    QuizResultResponse,

)
from .utils.compare_faces import compare_faces



logger = logging.getLogger(__name__)


class QuizService:
    """Service for managing quiz operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_quiz(
        self, data: QuizCreateRequest, user_id: int
    ) -> QuizResponse:
        """Create a new quiz for a subject"""
        logger.info(
            f"Attempting to create quiz for user: {user_id}"
        )
        try:
            quiz_data = QuizCreate(
                user_id=user_id,
                **data.model_dump(),
            )
            new_quiz = await create(
                session=self.session, model=Quiz, data=quiz_data
            )
            logger.info(
                f"Quiz created successfully: {new_quiz.id} by user {user_id}"
            )
            return QuizResponse.model_validate(new_quiz)
        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(f"Quiz creation failed for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invalid quiz data - subject may not exist",
            )
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error during quiz creation for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create quiz",
            )

    async def get_quiz_by_id(
        self, user_id: int, user_role: str, quiz_id: int
    ) -> QuizResponse:
        """Get a quiz by ID with authorization check"""
        logger.info(
            f"Fetching quiz {quiz_id} for user {user_id} with role {user_role}"
        )
        try:
            stmt = select(Quiz).where(Quiz.id == quiz_id)

            # Only apply user_id filter if not admin
            if user_role != settings.admin.name:
                stmt = stmt.where(Quiz.user_id == user_id)

            result = await self.session.execute(stmt)
            quiz_data = result.scalars().first()

            if not quiz_data:
                logger.warning(
                    f"Quiz {quiz_id} not found for user {user_id} with role {user_role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Quiz with id {quiz_id} not found",
                )

            logger.info(f"Quiz {quiz_id} retrieved successfully")
            return QuizResponse.model_validate(quiz_data)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while fetching quiz {quiz_id} for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve quiz",
            )

    async def get_all_quiz(
        self, user_id: int, user_role: str, pagination: Pagination
    ) -> QuizListResponse:
        """Get all quizzes with pagination and authorization"""
        logger.info(
            f"Fetching quizzes for user {user_id} with role {user_role} "
            f"- page: {pagination.page}, limit: {pagination.limit}"
        )
        try:
            # Build count query
            count_stmt = select(func.count(Quiz.id))
            if user_role != settings.admin.name:
                count_stmt = count_stmt.where(Quiz.user_id == user_id)

            # Get total count
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar() or 0

            # Build data query
            stmt = select(Quiz)
            if user_role != settings.admin.name:
                stmt = stmt.where(Quiz.user_id == user_id)

            stmt = (
                stmt.order_by(Quiz.created_at.desc())
                .limit(pagination.limit)
                .offset(pagination.offset)
            )

            # Get paginated results
            result = await self.session.execute(stmt)
            quiz_data = result.scalars().all()

            # Calculate total pages
            total_pages = (total + pagination.limit - 1) // pagination.limit

            logger.info(
                f"Retrieved {len(quiz_data)} quizzes out of {total} total for user {user_id}"
            )

            return QuizListResponse(
                total=total,
                page=pagination.page,
                limit=pagination.limit,
                total_pages=total_pages,
                quizzes=[
                    QuizResponse.model_validate(quiz) for quiz in quiz_data
                ],
            )

        except Exception as e:
            logger.error(
                f"Unexpected error while fetching quizzes for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve quizzes",
            )

    async def update_quiz(
        self, quiz_id: int, user_id: int, user_role: str, data: QuizUpdate
    ) -> QuizResponse:
        """Update a quiz with authorization check"""
        logger.info(
            f"Attempting to update quiz {quiz_id} for user {user_id} with role {user_role}"
        )
        try:
            # Build query to find the quiz
            stmt = select(Quiz).where(Quiz.id == quiz_id)

            # Only apply user_id filter if not admin
            if user_role != settings.admin.name:
                stmt = stmt.where(Quiz.user_id == user_id)

            # Get the quiz
            result = await self.session.execute(stmt)
            quiz_data = result.scalars().first()

            # Check if quiz exists
            if not quiz_data:
                logger.warning(
                    f"Quiz {quiz_id} not found for user {user_id} with role {user_role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Quiz with id {quiz_id} not found",
                )

            # Update quiz fields
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(quiz_data, field, value)

            # Commit changes
            self.session.add(quiz_data)
            await self.session.flush()
            await self.session.commit()

            # Refresh to reload lazy-loaded attributes
            await self.session.refresh(quiz_data)

            logger.info(f"Quiz {quiz_id} updated successfully by user {user_id}")
            return QuizResponse.model_validate(quiz_data)

        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(
                f"Quiz update failed for quiz {quiz_id}, user {user_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invalid quiz data - subject may not exist or data conflict",
            )
        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while updating quiz {quiz_id} for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update quiz",
            )

    async def delete_quiz(
        self, quiz_id: int, user_id: int, user_role: str
    ) -> dict:
        """Delete a quiz with authorization check"""
        logger.info(
            f"Attempting to delete quiz {quiz_id} for user {user_id} with role {user_role}"
        )
        try:
            # Build query to find the quiz
            stmt = select(Quiz).where(Quiz.id == quiz_id)

            # Only apply user_id filter if not admin
            if user_role != settings.admin.name:
                stmt = stmt.where(Quiz.user_id == user_id)

            # Get the quiz
            result = await self.session.execute(stmt)
            quiz_data = result.scalars().first()

            # Check if quiz exists
            if not quiz_data:
                logger.warning(
                    f"Quiz {quiz_id} not found for user {user_id} with role {user_role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Quiz with id {quiz_id} not found",
                )

            # Delete the quiz
            await self.session.delete(quiz_data)
            await self.session.commit()

            logger.info(f"Quiz {quiz_id} deleted successfully by user {user_id}")
            return {
                "message": f"Quiz {quiz_id} deleted successfully",
                "quiz_id": quiz_id,
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Unexpected error while deleting quiz {quiz_id} for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete quiz",
            )
            
    async def start_quiz(
        self, 
        user_id: int,
        user_image: UploadFile,
        user_role: str, 
        quiz_id: int, 
        pin: str
    ):
        """
        Start a quiz for a user with proper validation.
        Args:
            user_id: User ID
            user_image: User's uploaded image for face verification
            user_role: User role (admin, student, guest)
            quiz_id: Quiz ID to start
            pin: Quiz PIN for validation
        Returns:
            dict: Quiz data with questions or error message
        Raises:
            HTTPException: If quiz not found, PIN incorrect, role invalid, or face doesn't match
        """
        # Validate user role
        valid_roles = {"admin", "student", "guest"}
        if user_role.lower() not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user role: {user_role}"
            )
        
        # Check user face match with uploaded image
        await self.get_user_and_check(user_id=user_id, img2_file=user_image)
        
        # Fetch quiz with questions in one query (more efficient)
        quiz_stmt = select(Quiz).where(Quiz.id == quiz_id).options(
            selectinload(Quiz.questions)
        )
        quiz_result = await self.session.execute(quiz_stmt)
        quiz_data = quiz_result.scalars().first()
        
        # Validate quiz exists
        if not quiz_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz with ID {quiz_id} not found"
            )
        
        # Validate PIN
        if quiz_data.pin != pin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid PIN for this quiz"
            )
        
        # Prepare response
        return {
            "quiz_id": quiz_data.id,
            "quiz_name": quiz_data.name,
            "quiz_number": quiz_data.quiz_number,
            "duration": quiz_data.during,
            "total_questions": len(quiz_data.questions),
            "questions": [
                q.to_dict(randomize_options=True)
                for q in quiz_data.questions
            ],
        }
            
    async def end_quiz(self, user_id: int ,user_role: str, data: EndQuizCreate) -> QuizResultResponse:
        """
        End quiz and calculate results.
        
        Args:
            user_role: User role (admin, student, guest)
            data: Quiz submission data with answers
            
        Returns:
            QuizResultResponse: Quiz results with score and grade
            
        Raises:
            ValueError: If user role is invalid or quiz not found
        """
        # Validate user role
        valid_roles = {"admin", "student", "guest"}
        if user_role.lower() not in valid_roles:
            raise ValueError(f"Invalid user role: {user_role}")
        
        # Fetch quiz and questions
        quiz_stmt = select(Quiz).where(Quiz.id == data.quiz_id).options(
            selectinload(Quiz.questions)
        )
        quiz_result = await self.session.execute(quiz_stmt)
        quiz_data = quiz_result.scalars().first()
        
        if not quiz_data:
            raise ValueError(f"Quiz with ID {data.quiz_id} not found")
        
        # Calculate correct answers
        correct_count = 0
        question_map = {q.id: q for q in quiz_data.questions}
        
        for answer in data.answers:
            question = question_map.get(answer.question_id)
            if question and question.option_a == answer.option:
                correct_count += 1
        
        # Calculate score and grade
        total_questions = len(quiz_data.questions)
        incorrect_count = total_questions - correct_count
        score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
        grade = self._calculate_grade(score_percentage)
        
        # Save result to database
        result = Result(
            user_id=user_id,  # Assuming you have user context
            quiz_id=data.quiz_id,
            correct_answers=correct_count,
            incorrect_answers=incorrect_count,
            total_questions=total_questions,
            score_percentage=score_percentage,
            grade=grade
        )
        self.session.add(result)
        await self.session.commit()
        
        # Return response
        return QuizResultResponse(
            quiz_id=data.quiz_id,
            total_questions=total_questions,
            correct_answers=correct_count,
            incorrect_answers=incorrect_count,
            score_percentage=round(score_percentage, 2),
            grade=grade
        )
    
    @staticmethod
    def _calculate_grade(score_percentage: float) -> str:
        """Calculate letter grade based on score percentage."""
        if score_percentage >= 90:
            return "A+"
        elif score_percentage >= 80:
            return "A"
        elif score_percentage >= 70:
            return "B"
        elif score_percentage >= 60:
            return "C"
        else:
            return "F"
            
    async def get_user_and_check(self, user_id: int, img2_file: UploadFile):
        """
        Retrieve user and verify face image matches stored user image.
        
        Args:
            user_id: User ID to fetch
            img2_file: Uploaded image file for face verification
            
        Raises:
            HTTPException: If user not found or face doesn't match
        """
        # Fetch user from database
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        user_data = result.scalars().first()
        
        # Check if user exists
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Check if user has stored image
        if not user_data.image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no stored image for verification"
            )
        
        # Compare faces
        is_match = await compare_faces(
            img1=user_data.image, 
            img2_file=img2_file
        )
        
        if not is_match:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User face does not match stored image"
            )
        
        
        
        
        
        
        