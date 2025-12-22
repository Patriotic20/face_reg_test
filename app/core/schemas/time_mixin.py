from pydantic import BaseModel, ConfigDict
from datetime import datetime

class DateTimeMixin(BaseModel):
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)