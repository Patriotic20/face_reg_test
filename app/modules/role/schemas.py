from pydantic import BaseModel, field_validator, Field
from typing import List

from core.utils.normalize_str import normalize_str
from core.schemas.time_mixin import DateTimeMixin
from core.schemas.pagination import PaginatedResponse

class RoleCreateRequest(BaseModel):
    name: str
    
    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return normalize_str(value)
    

    
class RoleCreateResponse(DateTimeMixin):
    id: int
    name: str
    
    
    
class AssignPermissionRoleRequest(BaseModel):
    role_id: int = Field(..., gt=0, description="ID of the role, must be greater than 0")
    permission_id: int = Field(..., gt=0, description="ID of the permission, must be greater than 0")
    
    
class AssignPermissionRoleListRequest(BaseModel):
    role_id: int = Field(..., gt=0, description="Role ID must be greater than 0")
    permission_ids: List[int] = Field(
        ...,
        min_items=1,
        description="List of permission IDs, must not be empty"
    )
    
    @field_validator("permission_ids")
    @classmethod
    def validate_permission_ids(cls, value: List[int]):
        if any(permission_id <= 0 for permission_id in value):
            raise ValueError("All permission_ids must be greater than 0")
        return value
    
    
class RoleListResponse(PaginatedResponse):
    roles: list[RoleCreateResponse]
    

    
    
