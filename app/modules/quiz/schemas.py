from pydantic import BaseModel, Field, field_validator
from typing import Optional

from core.schemas.time_mixin import DateTimeMixin
from core.schemas.pagination import PaginatedResponse


class QuizCreateRequest(BaseModel):
    """Request model for creating a quiz"""
    name: str = Field(..., min_length=1, max_length=100)
    during: int = Field(..., gt=0, description="Quiz duration in minutes")
    quiz_number: int = Field(default=0, ge=0, description="Quiz number starting from 0")
    pin: str
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate name is not empty"""
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class QuizCreate(QuizCreateRequest):
    """Model for creating quiz with internal fields"""
    user_id: int = Field(..., gt=0)


    

class QuizResponse(DateTimeMixin):
    id: int
    name: str
    quiz_number: int
    during: int
    pin: str
    

class QuizUpdate(BaseModel):
    """Model for updating a quiz - all fields are optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    during: Optional[int] = Field(None, gt=0, description="Quiz duration in minutes")
    quiz_number: Optional[int] = Field(None, ge=0, description="Quiz number starting from 0")
    pin: str
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate name is not empty if provided"""
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip() if v else None
    
    
    
class QuizListResponse(PaginatedResponse):
    quizzes: list[QuizResponse]
    
class AnswerItem(BaseModel):
    """Model for a single answer submission."""
    question_id: int = Field(..., description="ID of the question")
    option: str = Field(..., description="Selected answer option")


class EndQuizCreate(BaseModel):
    """Model for submitting a completed quiz."""
    quiz_id: int = Field(..., description="ID of the quiz being submitted")
    answers: list[AnswerItem] = Field(..., description="List of answers provided")


class QuizResultResponse(BaseModel):
    """Response model after quiz submission."""
    quiz_id: int
    total_questions: int
    correct_answers: int
    incorrect_answers: int
    score_percentage: float
    grade: str