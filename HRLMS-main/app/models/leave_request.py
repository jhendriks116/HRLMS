from pydantic import BaseModel
from datetime import date
from typing import Optional

from app.models.enums import LeaveType, LeaveStatus


class LeaveRequest(BaseModel):
    """
    Domain model representing a single leave request.
    Mirrors the structure stored in leave_requests.json.
    """
    id: int
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    status: LeaveStatus = LeaveStatus.PENDING
    days_requested: int
    date_requested: date
    sick_document_id: Optional[int] = None  # ID of SickDocument if uploaded

    def validate_dates(self) -> None:
        if self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date.")

    def duration_days(self) -> int:
        """Total calendar days of the leave (inclusive)."""
        return (self.end_date - self.start_date).days + 1

    def requires_sick_document(self) -> bool:
        """
        Business rule for Option 2:
        Sick document is required for SICK leave longer than 2 days.
        """
        return self.leave_type == LeaveType.SICK and self.duration_days() > 2

    def approve(self) -> None:
        if self.status is not LeaveStatus.PENDING:
            raise ValueError("Only pending requests can be approved.")
        self.status = LeaveStatus.APPROVED

    def deny(self) -> None:
        if self.status is not LeaveStatus.PENDING:
            raise ValueError("Only pending requests can be rejected.")
        self.status = LeaveStatus.REJECTED
