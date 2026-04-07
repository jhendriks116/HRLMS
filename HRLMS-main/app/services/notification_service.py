import app.database as db
from datetime import datetime
import smtplib
from email.message import EmailMessage


class NotificationService:

    @staticmethod
    def send_email(to_email: str, subject: str, message: str):
        EMAIL_ADDRESS = "jordanstewart294@gmail.com"
        EMAIL_PASSWORD = "hctahhxdcjspqreh"

        print("🔥 Trying to send email...")

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg.set_content(message)

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(msg)
                print("✅ Email sent successfully")
        except Exception as e:
            print("❌ Email failed:", e)

    @staticmethod
    def create_notification(employee_id: int, message: str):
        return db.create_record("notifications", {
            "employee_id": employee_id,
            "message": message,
            "read": False,
            "created_at": datetime.now().isoformat()
        })

    @staticmethod
    def get_notifications_for_employee(employee_id: int):
        return db.find("notifications", employee_id=employee_id)

    @staticmethod
    def notify_leave_status(employee: dict, status: str):
        name = employee.get("name", "Employee")
        email = employee.get("email")
        emp_id = employee.get("id")

        message = f"Hello {name}, your leave request is {status}"

        # Save notification
        if emp_id:
            NotificationService.create_notification(emp_id, message)

        # Send email
        if email:
            NotificationService.send_email(email, f"Leave {status}", message)