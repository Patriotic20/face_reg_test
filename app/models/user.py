from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from .base import Base
from .mixins.id_int_pk import IdIntPk
from .mixins.time_stamp_mixin import TimestampMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .role import Role
    from .quiz import Quiz
    from .results import Result
    from .questions import Question
    from .user_answer import UserAnswer

class User(IdIntPk, TimestampMixin ,Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    image: Mapped[str] = mapped_column(
        String, 
        nullable=True
    )
    
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="user_role_association",
        back_populates="users"
    )
    
    
    quizzes: Mapped[list["Quiz"]] = relationship(
        "Quiz",
        back_populates="user",   
    )
    
    
    results: Mapped[list["Result"]] = relationship(
        "Result", 
        back_populates="user"
    )
    
    user_answers: Mapped[list["UserAnswer"]] = relationship(
        "UserAnswer",
        back_populates="user"
    )

    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="user"
    )
    
