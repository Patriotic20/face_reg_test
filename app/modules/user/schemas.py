from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List
from datetime import datetime

from core.utils.normalize_str import normalize_str


class AssignUserRoleRequest(BaseModel):
    user_id: int = Field(..., gt=0, description="ID of the user, must be greater than 0")
    role_id: int = Field(..., gt=0, description="ID of the role, must be greater than 0")

class AssignUserRoleListRequest(BaseModel):
    user_id: int = Field(..., gt=0, description="User ID must be greater than 0")
    role_ids: List[int] = Field(
        ...,
        min_items=1,
        description="List of role IDs, must not be empty"
    )

    @field_validator("role_ids")
    @classmethod
    def validate_role_ids(cls, value: List[int]):
        if any(role_id <= 0 for role_id in value):
            raise ValueError("All role_ids must be greater than 0")
        return value


class RoleBase(BaseModel):
    name: str


class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    
class UserBase(BaseModel):
    username: str
    
    
class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    roles: List[RoleResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
    

class UserListItem(BaseModel):
    id: int
    username: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

    
    
class UserListResponse(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    users: List[UserListItem]
    
    model_config = ConfigDict(from_attributes=True)
    
class UserUpdateUsername(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=30,
        examples=["john_doe"]
    )

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        value = normalize_str(text=value)
        if " " in value:
            raise ValueError("Username must not contain spaces")
        return value