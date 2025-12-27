from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, UniqueConstraint
from models.base import Base
from models.mixins.id_int_pk import IdIntPk
from models.mixins.time_stamp_mixin import TimestampMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .role import Role

class Permission(IdIntPk, TimestampMixin, Base):
    __tablename__ = "permissions"

    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_resource_action"),
    )

    # Back reference to roles
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="role_permission_association",
        back_populates="permissions"
    )
