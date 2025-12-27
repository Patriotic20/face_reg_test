from pydantic import BaseModel, field_validator

from core.utils.normalize_str import normalize_str
from core.schemas.time_mixin import DateTimeMixin


class CreatePermissionRequest(BaseModel):
    resource: str
    action: str

    @field_validator("*", mode="before")
    @classmethod
    def normalize_and_validate(cls, value):
        if isinstance(value, str):
            value = normalize_str(text=value)

            if not value:
                raise ValueError("Value cannot be empty")

        return value


class CreatePermissionResponse(DateTimeMixin):
    id: int
    resource: str
    action: str