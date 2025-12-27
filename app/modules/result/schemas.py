from core.schemas.time_mixin import DateTimeMixin
from core.schemas.pagination import PaginatedResponse


class ResultResponse(DateTimeMixin):
    correct_answers: int
    incorrect_answers: int
    total_questions: int
    score_percentage: float
    grade: str


class ResultListResponse(PaginatedResponse):
    results: list[ResultResponse]
