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
