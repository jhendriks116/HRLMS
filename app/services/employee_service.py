from datetime import date
import app.database as db
from app.models.enums import PaymentType, LeaveType


def parse_date(d) -> date:
    """Ensures dates from JSON are converted back to date objects."""
    return date.fromisoformat(d) if isinstance(d, str) else d


class EmployeeService:
    """Handles calculations and initialization of employee leave balances."""


    @staticmethod
    def calc_years_of_service(date_hired: date) -> int:
        today = date.today()
        years = today.year - date_hired.year

        if (today.month, today.day) < (date_hired.month, date_hired.day):
            years -= 1

        return years

 
    @staticmethod
    def calc_vacation_days(date_hired: date, pay_type: PaymentType) -> int:
        years = EmployeeService.calc_years_of_service(date_hired)

        if pay_type == PaymentType.FORTNIGHTLY:
            return 10 if years < 7 else 15

        # Monthly employees
        if years < 5:
            return 10
        elif years < 10:
            return 15
        return 20

   
    @staticmethod
    def calc_sick_days(date_hired: date) -> int:
        years = EmployeeService.calc_years_of_service(date_hired)
        return 10 if years >= 1 else 0

   
    
    @staticmethod
    def init_leave_balance(employee: dict, year: int) -> None:
        """
        Ensures the employee has correct leave balances for the given year.
        If record exists → update.
        If record does not exist → create.
        """

        date_hired = parse_date(employee["date_hired"])

        vacation_entitled = EmployeeService.calc_vacation_days(date_hired, employee["type"])
        sick_entitled = EmployeeService.calc_sick_days(date_hired)

        employee_id = employee["id"]

        
        vacation_balance = db.find_one(
            "leave_balances",
            employee_id=employee_id,
            year=year,
            leave_type=LeaveType.VACATION.value  # ALWAYS string in JSON
        )

        if vacation_balance:
            # Update existing record
            db.update_record("leave_balances", vacation_balance["id"], {
                "entitled_days": vacation_entitled,
                "remaining_days": vacation_entitled - vacation_balance.get("used_days", 0),
                "last_updated": date.today()
            })
        else:
            # Create new record
            db.create_record("leave_balances", {
                "employee_id": employee_id,
                "year": year,
                "leave_type": LeaveType.VACATION.value,
                "entitled_days": vacation_entitled,
                "used_days": 0,
                "remaining_days": vacation_entitled,
                "last_updated": date.today()
            })

       
        sick_balance = db.find_one(
            "leave_balances",
            employee_id=employee_id,
            year=year,
            leave_type=LeaveType.SICK.value
        )

        if sick_balance:
            db.update_record("leave_balances", sick_balance["id"], {
                "entitled_days": sick_entitled,
                "remaining_days": sick_entitled - sick_balance.get("used_days", 0),
                "last_updated": date.today()
            })
        else:
            db.create_record("leave_balances", {
                "employee_id": employee_id,
                "year": year,
                "leave_type": LeaveType.SICK.value,
                "entitled_days": sick_entitled,
                "used_days": 0,
                "remaining_days": sick_entitled,
                "last_updated": date.today()
            })

    @staticmethod
    def adjust_leave_balance(employee_id: int, leave_type: str, adjustment: int, year: int) -> dict:
        #Manually adjust entitled_days for an employee
        balance = db.find_one(
            "leave_balances",
            employee_id=employee_id,
            leave_type=leave_type,
            year=year
        )
        if not balance:
            raise ValueError("Leave balance not found")

        new_entitled = balance["entitled_days"] + adjustment
        if new_entitled < 0:
            raise ValueError("Entitled days cannot be negative")

        new_remaining = max(0, new_entitled - balance["used_days"])

        db.update_record("leave_balances", balance["id"], {
            "entitled_days": new_entitled,
            "remaining_days": new_remaining,
            "last_updated": date.today().isoformat()
        })
        return db.read_record("leave_balances", balance["id"])