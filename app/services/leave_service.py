from datetime import date, timedelta
from typing import Optional
import app.database as db
from app.models.enums import LeaveType, LeaveStatus
from app.services.notification_service import NotificationService


class LeaveService:
    """Centralized leave processing: calculating days, approving, rejecting, updating balances"""

  
    # CALCULATE LEAVE DAYS
   
    def calc_leave_days(self, start_date: date, end_date: date, leave_type: LeaveType) -> int:
        if end_date < start_date:
            raise ValueError("End date cannot be before start date.")

        # Vacation counts weekdays only
        if leave_type == LeaveType.VACATION:
            return self._working_days(start_date, end_date)

        # Sick counts full calendar days
        if leave_type == LeaveType.SICK:
            return (end_date - start_date).days + 1

        # Default inclusive
        return (end_date - start_date).days + 1

    def _working_days(self, start: date, end: date) -> int:
        days = 0
        current = start
        while current <= end:
            if current.weekday() < 5:
                days += 1
            current += timedelta(days=1)
        return days

   
    # APPROVE REQUEST

    def approve_request(self, request_id: int) -> dict:
        request = db.read_record("leave_requests", request_id)
        if not request:
            raise ValueError("Leave request not found")

        if request["status"] == LeaveStatus.APPROVED.value:
            return {"message": "Already approved", "leave_request": request, "updated_balance": None}

        # Parse stored dates
        start = date.fromisoformat(request["start_date"])
        end = date.fromisoformat(request["end_date"])
        leave_type = LeaveType(request["leave_type"])

        # Calculate leave days
        days_requested = request.get("days_requested")
        if days_requested is None:
            days_requested = self.calc_leave_days(start, end, leave_type)

        # Get leave balance
        balance = db.find_one(
            "leave_balances",
            employee_id=request["employee_id"],
            year=start.year,
            leave_type=leave_type.value
        )
        if not balance:
            raise ValueError("Leave balance not found")

        if balance["remaining_days"] < days_requested:
            raise ValueError("Not enough leave days")

        # Deduct days
        updated_balance = self._deduct_days(balance, days_requested)

        # Update request status
        db.update_record("leave_requests", request_id, {
            "status": LeaveStatus.APPROVED.value,
            "last_updated": date.today().isoformat()
        })
        updated_request = db.read_record("leave_requests", request_id)

        # Notify employee
        employee = db.find_one("employees", id=request["employee_id"])
        NotificationService.notify_leave_status(employee, "APPROVED")

        return {"leave_request": updated_request, "updated_balance": updated_balance}

  
    # REJECT REQUEST
    
    def reject_request(self, request_id: int) -> dict:
        request = db.read_record("leave_requests", request_id)
        if not request:
            raise ValueError("Leave request not found")

        old_status = request["status"]

        # Always update status
        db.update_record("leave_requests", request_id, {
            "status": LeaveStatus.REJECTED.value,
            "last_updated": date.today().isoformat()
        })
        updated_request = db.read_record("leave_requests", request_id)

        # If previously approved, restore days
        updated_balance = None

        if old_status == LeaveStatus.APPROVED.value:
            start = date.fromisoformat(request["start_date"])
            end = date.fromisoformat(request["end_date"])
            leave_type = LeaveType(request["leave_type"])
            days_requested = request["days_requested"]

            balance = db.find_one(
                "leave_balances",
                employee_id=request["employee_id"],
                year=start.year,
                leave_type=leave_type.value
            )

            updated_balance = self._restore_days(balance, days_requested)

        # Notify employee
        employee = db.find_one("employees", id=request["employee_id"])
        NotificationService.notify_leave_status(employee, "REJECTED")

        return {"leave_request": updated_request, "updated_balance": updated_balance}

  
    # BALANCE UTILITIES

    def _deduct_days(self, balance: dict, days: int) -> dict:
        new_used = balance["used_days"] + days
        new_remaining = balance["remaining_days"] - days

        db.update_record("leave_balances", balance["id"], {
            "used_days": new_used,
            "remaining_days": new_remaining,
            "last_updated": date.today().isoformat()
        })
        return db.read_record("leave_balances", balance["id"])

    def _restore_days(self, balance: dict, days: int) -> dict:
        new_used = max(0, balance["used_days"] - days)
        new_remaining = balance["remaining_days"] + days

        db.update_record("leave_balances", balance["id"], {
            "used_days": new_used,
            "remaining_days": new_remaining,
            "last_updated": date.today().isoformat()
        })
        return db.read_record("leave_balances", balance["id"])
