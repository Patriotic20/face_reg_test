from pydantic import BaseModel
from core.schemas.time_mixin import DateTimeMixin
from core.schemas.pagination import PaginatedResponse

class QuestionRequest(BaseModel):
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str


class CreateQuestionRequest(QuestionRequest):
    quiz_id: int
    user_id: int

class QuestionResponse(DateTimeMixin):
    id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    
class QuestionListResponse(PaginatedResponse):
    questions: list[QuestionResponse]
    
    
class QuestionUpdateRequest(BaseModel):
    text: str | None = None
    option_a: str | None = None
    option_b: str | None = None
    option_c: str | None = None
    option_d: str | None = None


class QuestionUpdateResponse(QuestionResponse):
    pass
    
    