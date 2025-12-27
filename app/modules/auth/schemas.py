from pydantic import BaseModel, field_validator, Field, computed_field
from core.utils.normalize_str import normalize_str
from .utils.password_hash import hash_password


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=3)
    
    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        """Normalize username before validation"""
        if not value or not value.strip():
            raise ValueError("Username is required")
        return normalize_str(value)
    
    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Validate password before hashing"""
        if not value or not value.strip():
            raise ValueError("Password is required")
        return hash_password(value.strip())


class UserCreateResponse(BaseModel):
    """Response model after user creation"""
    id: int
    username: str
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "john_doe"
            }
        }


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=3)
    
    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        """Normalize username before validation"""
        if not value or not value.strip():
            raise ValueError("Username is required")
        return normalize_str(value)
    
    @field_validator("password", mode="before")
    @classmethod
    def clean_password(cls, value: str) -> str:
        """Remove whitespace and validate password"""
        if not value or not value.strip():
            raise ValueError("Password is required")
        return value.strip()


class UserLoginResponse(BaseModel):
    """Response model for successful login"""
    token_type: str = Field(default="Bearer", description="Token type")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token_type": "Bearer",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
        
class RefreshRequest(BaseModel):
    refresh_token: str

    @field_validator("refresh_token", mode="before")
    @classmethod
    def normalize(cls, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError("refresh_token must be a string")
        return value.strip()
    
class UpdatePassword(BaseModel):
    old_password: str
    new_password: str
    
    @field_validator("old_password", "new_password", mode="before")
    @classmethod
    def clean_password(cls, value: str) -> str:
        return value.strip()
    
    @computed_field
    @property
    def password(self) -> str:
        """Returns the hashed new password."""
        return hash_password(password=self.new_password)