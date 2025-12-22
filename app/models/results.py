from sqlalchemy import Integer, String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from .mixins.id_int_pk import IdIntPk
from .mixins.time_stamp_mixin import TimestampMixin
from .mixins.user_pr_ky import UserPrKy

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .quiz import Quiz


class Result(UserPrKy, IdIntPk, TimestampMixin, Base):
    __tablename__ = "results"
    
    back_populates_name = "results"
    
    quiz_id: Mapped[int] = mapped_column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)

    correct_answers: Mapped[int] = mapped_column(Integer, nullable=False)
    incorrect_answers: Mapped[int] = mapped_column(Integer, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    score_percentage: Mapped[float] = mapped_column(Float, nullable=False)  # use Float for percentages
    grade: Mapped[str] = mapped_column(String(5), nullable=False)  # e.g., "A+", "B"

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="results")