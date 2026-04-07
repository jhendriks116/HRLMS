from fastapi import APIRouter, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from datetime import date
from pathlib import Path
import shutil

import app.database as db
from app.models.enums import LeaveType, LeaveStatus
from app.services.leave_service import LeaveService
from app.services.notification_service import NotificationService   # ✅ FIXED IMPORT

leave_request_router = APIRouter()
leave_service = LeaveService()

UPLOAD_DIR = Path("./app/uploads/sick_documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class LeaveRequestDto(BaseModel):
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date


class StatusUpdateDto(BaseModel):
    status: LeaveStatus


# CREATE LEAVE REQUEST

@leave_request_router.get("/leave-requests", status_code=200)
def list_leave_request():
    return db.read_all_records("leave_requests")

@leave_request_router.post("/leave-requests", status_code=201)
def create_leave_request(data: LeaveRequestDto):

    employee = db.find_one("employees", id=data.employee_id)
    if not employee:
        raise HTTPException(404, "Employee not found")

    # calculate days using LeaveService
    try:
        days_requested = leave_service.calc_leave_days(
            data.start_date, data.end_date, data.leave_type
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    # find balance
    balance = db.find_one(
        "leave_balances",
        employee_id=data.employee_id,
        leave_type=data.leave_type.value,
        year=date.today().year
    )
    if not balance:
        raise HTTPException(400, "Leave balance not found")

    if balance["remaining_days"] < days_requested:
        raise HTTPException(400, "Not enough leave days")

    leave_request = db.create_record("leave_requests", {
        "employee_id": data.employee_id,
        "leave_type": data.leave_type.value,
        "start_date": data.start_date.isoformat(),
        "end_date": data.end_date.isoformat(),
        "days_requested": days_requested,
        "status": LeaveStatus.PENDING.value,
        "date_requested": date.today().isoformat(),
        "sick_document_id": None
    })

    return {
        "message": "Leave request submitted",
        "leave_request_id": leave_request["id"],
        "days_requested": days_requested
    }


# ---------------------------------------------------------
# APPROVE / REJECT REQUEST + NOTIFICATIONS
# ---------------------------------------------------------
@leave_request_router.patch("/leave-requests/{request_id}/status")
def update_status(request_id: int, data: StatusUpdateDto):

    request = db.read_record("leave_requests", request_id)
    if not request:
        raise HTTPException(404, "Leave request not found")

    employee = db.read_record("employees", request["employee_id"])
    if not employee:
        raise HTTPException(404, "Employee not found")

    # APPROVE
    if data.status == LeaveStatus.APPROVED:
        try:
            result = leave_service.approve_request(request_id)

            # 🔔 Send APPROVAL notification
            NotificationService.notify_leave_status(employee, "Approved")

            return {
                "message": "Leave request approved",
                "data": result
            }
        except ValueError as e:
            raise HTTPException(400, str(e))

    # REJECT
    elif data.status == LeaveStatus.REJECTED:
        try:
            result = leave_service.reject_request(request_id)

            # 🔔 Send REJECTION notification
            NotificationService.notify_leave_status(employee, "Rejected")

            return {
                "message": "Leave request rejected",
                "data": result
            }
        except ValueError as e:
            raise HTTPException(400, str(e))

    raise HTTPException(400, "Invalid status")



# UPLOAD SICK DOCUMENT (only allowed when >2 days)

@leave_request_router.post("/leave-requests/{leave_request_id}/upload-sick-note")
async def upload_sick_note(leave_request_id: int, file: UploadFile = File(...)):

    req = db.find_one("leave_requests", id=leave_request_id)
    if not req:
        raise HTTPException(404, "Request not found")

    if req["leave_type"] != LeaveType.SICK.value:
        raise HTTPException(400, "Document allowed only for sick leave")

    start = date.fromisoformat(req["start_date"])
    end = date.fromisoformat(req["end_date"])
    total_days = (end - start).days + 1

    if total_days <= 2:
        raise HTTPException(400, "Sick note required only for >2 days")

    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc = db.create_record("sick_documents", {
        "leave_request_id": leave_request_id,
        "file_path": str(file_path),
        "file_name": file.filename,
        "uploaded_at": date.today().isoformat()
    })

    db.update_record("leave_requests", leave_request_id, {
        "sick_document_id": doc["id"]
    })

    return {"message": "Sick note uploaded", "document": doc}
