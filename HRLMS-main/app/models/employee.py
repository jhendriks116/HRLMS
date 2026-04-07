from pydantic import BaseModel, Field
from datetime import date

from app.models.enums import PaymentType
from app.models.leave_balance import LeaveBalance

class Employee(BaseModel):
    id: int
    name: str
    email: str
    type: PaymentType
    date_hired: date