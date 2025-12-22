from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from .base import Base
from .mixins.id_int_pk import IdIntPk
from .mixins.time_stamp_mixin import TimestampMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .permission import Permission

class Role(IdIntPk, TimestampMixin, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    
    # Many-to-many relationship with users
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_role_association",
        back_populates="roles"
    )
    
    # Many-to-many relationship with permissions
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary="role_permission_association",
        back_populates="roles"
    )
