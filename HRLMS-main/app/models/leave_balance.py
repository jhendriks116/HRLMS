from pydantic import BaseModel, Field

from datetime import date
from app.models.enums import LeaveType


class LeaveBalance(BaseModel):
    id: int
    employee_id: int
    year: int
    leave_type: LeaveType
    entitled_days: int
    used_days:int = 0
    remaining_days: int
    last_updated: date = Field(default_factory=date.today)

    def leave_balance(self):
        self.remaining_days = max(0, self.entitled_days - self.used_days)
        return self.remaining_days