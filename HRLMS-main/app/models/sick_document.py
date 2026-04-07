from pydantic import BaseModel, Field
from datetime import date

class SickDocument(BaseModel):
    id: int
    leave_request_id: int
    file_path: str
    file_name: str
    uploaded_at: date = Field(default_factory=date.today)