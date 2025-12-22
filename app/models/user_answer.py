from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
from .mixins.id_int_pk import IdIntPk
from .mixins.time_stamp_mixin import TimestampMixin
from .mixins.user_pr_ky import UserPrKy

class UserAnswer(UserPrKy, IdIntPk, TimestampMixin, Base):
    __tablename__ = "user_answers"
    
    back_populates_name = "user_answers"

    selected_option: Mapped[str] = mapped_column(String(1), nullable=False)  # 'A', 'B', 'C', 'D'
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
