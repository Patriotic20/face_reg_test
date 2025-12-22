from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import User

class UserPrKy:
    """
    Mixin to add user_id column and a user relationship.
    The child model must define the class attribute `back_populates_name` 
    to specify the back_populates in the User model.
    """

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    @declared_attr
    def user(cls) -> Mapped["User"]:
        if not hasattr(cls, "back_populates_name") or cls.back_populates_name is None:
            raise ValueError(f"{cls.__name__} must define class attribute 'back_populates_name'")
        return relationship("User", back_populates=cls.back_populates_name)
