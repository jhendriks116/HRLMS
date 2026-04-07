# HRLMS - HR Leave Management System
**Island Concrete | COMP2171 Group 6 Project**

This project is a web-based HR Leave Managements System built with FastAPI and JSON file storage. The aim of this build is to replace the existing paper-based leave management process for Island Concrete.

## Group Members

| Name | ID Number |
|---|---|
| Jordan Hendriks | 620086686 |
| Andre Wright | 620153778 |
| Cliff Holmes | 620153431 |
| Jordon Stewart | 620163114 |

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Storage | JSON files |
| Reports | pandas, openpyxl |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Notifications | Console/log stub |

## Project Stucture

HRLMS/
├── app
│   ├── controllers
│   │   ├── employee_controller.py
│   │   ├── leave_requests_controller.py
│   │   └── reports_controller.py
│   ├── database
│   │   ├── employees.json
│   │   ├── leave_balances.json
│   │   ├── leave_requests.json
│   │   └── sick_documents.json
│   ├── database.py
│   ├── frontend
│   │   ├── app.js
│   │   ├── index.html
│   │   └── styles.css
│   ├── main.py
│   ├── models
│   │   ├── employee.py
│   │   ├── enums.py
│   │   ├── leave_balance.py
│   │   ├── leave_request.py
│   │   ├── sick_document.py
│   │   └── user.py
│   ├── reports
│   │   └── combined_leave_report.xlsx
│   └── services
│       ├── employee_service.py
│       ├── leave_service.py
│       ├── notification_service.py
│       └── report_service.py
├── LICENSE
├── README.md
└── requirements.txt


## Setup & Running

### 1. Clone the Repository
```bash
git clone https://github.com/jhendriks116/HRLMS.git
cd HRLMS
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt --break-system-packages
```

### 3. Run the Server
```bash
python3 main.py
```

### 4. Open the Frontend
Open `frontend/index.html` in your browser

## API Endpoints

### Employees
| Method | Endpoint | Description |
|---|---|---|
| POST | `/employees` | Add new employee |
| GET | `/employees` | List all employees |
| GET | `/employees/{id}` | Get employee by ID |
| GET | `/leave-balances` | List all leave balances |

### Leave Requests
| Method | Endpoint | Description |
|---|---|---|
| POST | `/leave-requests` | Submit leave request |
| PATCH | `/leave-requests/{id}/status` | Approve or reject |
| POST | `/leave-requests/{id}/upload-sick-note` | Upload sick note |

### Reports
| Method | Endpoint | Description |
|---|---|---|
| GET | `/reports/leave-report` | Download Excel report

## Business Rules
- **Vacation Leave** - weekdays only
- **Sick Leave** - calendar days
- Sick Note required for Sick Leave longer than 2 days
- Entitlement by years of service:

| Payment Type | Years | Vacation Days |
|---|---|---|
| Fortnightly | Less than 7 | 10 days |
| Fortnightly | 7 or more | 15 days |
| Monthly | Less than 5 | 10 days |
| Monthly | 5 -10 | 15 days |
| Monthly | 10 or more | 20 days |

- Sick days: 10 if employed for 1 year or more, 0 otherwise