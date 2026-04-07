from datetime import datetime

class NotificationService:

    @staticmethod
    def send_email(to_email: str, subject: str, message: str):
        print(f"Email sent to {to_email}: {subject}")

    @staticmethod
    def log_notification(employee_id: int, status: str):
        with open("notification_log.txt", "a") as file:
            file.write(f"{datetime.now()} - Employee:{employee_id} - {status}\n")

    @staticmethod
    def notify_leave_status(employee: dict, status: str):
        """
        Works with your JSON database employees,
        which are stored as dictionaries.
        """

        subject = f"Your Leave Request Status: {status}"

        # Access dict-style
        name = employee.get("name", "Employee")
        email = employee.get("email", None)
        emp_id = employee.get("id", None)

        message = f"Hello {name}, your leave request is now: {status}"

        # Send "email"
        if email:
            NotificationService.send_email(email, subject, message)

        # Log notification
        if emp_id:
            NotificationService.log_notification(emp_id, status)
