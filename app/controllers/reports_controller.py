from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.report_service import fetch_report_data, generate_excel_report

reports_router = APIRouter(prefix="/reports", tags=["Reports"])

@reports_router.get("/leave-report")
def download_leave_report():
    try:
        employees, leave_records = fetch_report_data()
        file_path = generate_excel_report(employees, leave_records)

        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="combined_leave_report.xlsx"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
