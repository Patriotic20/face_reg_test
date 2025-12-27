from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship


from .base import Base
from .mixins.id_int_pk import IdIntPk
from .mixins.time_stamp_mixin import TimestampMixin
from .mixins.user_pr_ky import UserPrKy

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .questions import Question
    from .results import Result



class Quiz(UserPrKy, IdIntPk, TimestampMixin, Base):
    __tablename__ = "quizzes"
    
    back_populates_name = "quizzes"
    
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    quiz_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    during: Mapped[int] = mapped_column(Integer, nullable=False)
    pin: Mapped[str] = mapped_column(String, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )
    
    
    results: Mapped[list["Result"]] = relationship(
        "Result",
        back_populates="quiz",
        cascade="all, delete-orphan",
        lazy="select"  # Lazy load results to avoid N+1 queries
    )