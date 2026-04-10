from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel
from datetime import date
import app.database as db

from app.models.enums import PaymentType
from app.services.employee_service import EmployeeService

employee_router = APIRouter()


class EmployeeDto(BaseModel):
    name: str
    email: str
    type: PaymentType
    date_hired: date

@employee_router.get("/leave-balances", status_code=200)
def list_leave_balances():
    return db.read_all_records("leave_balances")
@employee_router.post("/employees", status_code=status.HTTP_201_CREATED)
def add_employee(data: EmployeeDto):
    # Prevent duplicates
    if db.find_one("employees", email=data.email):
        raise HTTPException(400, "Employee with this email already exists")

    # Save ENUM correctly using .value
    employee = db.create_record("employees", {
        "name": data.name,
        "email": data.email,
        "type": data.type.value,
        "date_hired": data.date_hired
    })

    # Initialize leave balances for the current year
    EmployeeService.init_leave_balance(employee, date.today().year)

    return {
        "Message": "Employee added successfully",
        "employee_id": employee["id"]
    }


@employee_router.get("/employees/{employee_id}", status_code=status.HTTP_200_OK)
def get_employee(employee_id: int):
    employee = db.find_one("employees", id=employee_id)
    if not employee:
        raise HTTPException(404, "Employee not found")
    return employee


@employee_router.get("/employees", status_code=status.HTTP_200_OK)
def list_employees():
    return db.read_all_records("employees")

class AdjustBalanceDto(BaseModel):
    leave_type: str
    adjustment: int
    year: int = None

@employee_router.patch("/employees/{employee_id}/adjust-balance", status_code=200)
def adjust_balance(employee_id: int, data: AdjustBalanceDto):
    employee = db.find_one("employees", id=employee_id)
    if not employee:
        raise HTTPException(404, "Employee not found")
    try:
        year = data.year or date.today().year
        updated = EmployeeService.adjust_leave_balance(
            employee_id, data.leave_type, data.adjustment, year
        )
        return { "message": "Balance adjusted", "updated_balance": updated }
    except ValueError as e:
        raise HTTPException(400, str(e))

@employee_router.post("/employees/{employee_id}/recalculate-balance", status_code=200)
def recalculate_balance(employee_id: int):
    #Recalculates entitlement based on current years of service.
    employee = db.find_one("employees", id=employee_id)
    if not employee:
        raise HTTPException(404, "Employee not found")
    EmployeeService.init_leave_balance(employee, date.today().year)
    return { "message": "Balance recalculated successfully" }