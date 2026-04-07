from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.controllers.employee_controller import employee_router
# from app.controllers.hr_controller import hr_router
from app.controllers.leave_requests_controller import leave_request_router
from app.controllers.reports_controller import reports_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_headers = ["*"],
)

app.include_router(employee_router)
# app.include_router(hr_router)
app.include_router(leave_request_router)
app.include_router(reports_router)

app.mount("/", StaticFiles(directory="app/frontend", html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)