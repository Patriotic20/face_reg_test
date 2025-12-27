from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class Pagination(BaseModel):
    """Model for handling pagination parameters"""
    
    page: int = Field(default=1, ge=1, description="Page number (starting from 1)")
    limit: int = Field(default=10, ge=1, le=100, description="Number of items per page")
    search: Optional[str] = Field(default=None, description="Search query string")
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "limit": 20,
                "search": "example query"
            }
        }
    
    @property
    def offset(self) -> int:
        """Calculate the offset for database queries"""
        return (self.page - 1) * self.limit
    
    
class PaginatedResponse(BaseModel):
    """Response model for paginated results"""
    total: int
    page: int
    limit: int
    total_pages: int
    
    model_config = ConfigDict(from_attributes=True)