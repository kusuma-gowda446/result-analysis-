# Student Result Management System — SIET Tumakuru

An institutional, enterprise-grade web application designed for student profile management, academic marks tracking, automated SGPA/CGPA calculations, PDF marks card generation, Excel/CSV bulk data ingestion, and interactive performance analytics for **Shridevi Institute of Engineering and Technology (SIET)**.

---

## 🌟 Key Features

- **Dual-Role Authentication System (RBAC)**: Secure role-based access for Administrators/Faculty and Students.
- **Student Profile Management**: Full CRUD operations for student registration, USN validation, contact information, and academic records.
- **Academic Marks & Grade Engine**: Automatic evaluation of internal and external marks, total scores, PASS/FAIL results (`>= 40%`), credit-weighted SGPA, and CGPA.
- **Student Academic Portal**: Personal student dashboard with profile summary, subject-wise marks breakdown, and single-click PDF marks card download.
- **Institutional PDF Marks Card**: Dynamic ReportLab PDF generation featuring college branding, academic summary tables, and official printing layout.
- **Spreadsheet Bulk Import Engine**: Ingest Excel (`.xlsx`) or CSV files to automatically update multiple student records and marks simultaneously.
- **Academic Performance Analytics**: Interactive Chart.js charts rendering class grade distributions, subject performance averages, and top performer leaderboards.
- **Modern Responsive UI**: Built with **Bootstrap 5.3**, custom SIET theme styling, and persistent Dark/Light mode toggle.
- **Containerized Orchestration**: Automated multi-container stack with **Flask Gunicorn**, **MongoDB**, and **Mongo Express**.

---

## 🏗 System Architecture & Technology Stack

```
[ Web Browser ]
      │
      ├── (HTTP / Bootstrap 5.3 / Chart.js)
      ▼
[ Gunicorn WSGI Server ] (Port 5000)
      │
      ▼
[ Flask Application Factory ]
   ├── Auth Blueprint      (/login, /student/login, /admin/login, /logout)
   ├── Admin Blueprint     (/admin/students, /admin/marks, /admin/bulk_upload, /admin/users)
   ├── Student Blueprint   (/student/dashboard, /download_pdf/<usn>)
   └── Analytics Blueprint (/analytics/api/stats)
      │
      ├── Service Layer   (ReportService, AnalyticsService, BulkService)
      └── Model Layer     (UserModel, StudentModel, MarkModel, SubjectModel)
      │
      ▼
[ MongoDB Database Engine ] (Port 27017)
   ├── admins
   ├── students
   ├── marks
   └── subjects
```

- **Backend**: Python 3.12, Flask, PyMongo, ReportLab, Pandas, OpenPyXL, PyTest.
- **Frontend**: HTML5, Jinja2, Bootstrap 5.3, Bootstrap Icons, Chart.js.
- **Database**: MongoDB 7.0 (with Mongo Express web UI on port 8081).
- **Containerization**: Docker & Docker Compose.

---

## 📁 Directory Structure

```
marks_analyser/
├── app/
│   ├── __init__.py                 # Application Factory & Blueprint registration
│   ├── database/
│   │   └── connection.py           # MongoDB lifecycle, schema indexes, & auto-seeding
│   ├── models/                     # Data Access Objects (User, Student, Mark, Subject)
│   ├── routes/                     # Blueprint controllers (admin, auth, student, analytics)
│   ├── services/                   # Business aggregators (ReportService, AnalyticsService, BulkService)
│   ├── static/                     # CSS, images, and JavaScript assets
│   ├── templates/                  # Jinja2 templates (admin, auth, student, errors)
│   └── utils/                      # Security decorators, PDF generator, Excel processor
├── tests/
│   └── test_app.py                 # PyTest test suite
├── .env.example                    # Sample environment file
├── config.py                       # Flask configuration classes
├── Dockerfile                      # Container build definition
├── docker-compose.yml              # Container stack specification
├── requirements.txt                # Python dependencies
└── run.py                          # Local execution entry point
```

---

## 🚀 Quick Start with Docker Compose

### Prerequisites
- Docker Engine `^24.0`
- Docker Compose `^2.20`

### Step 1: Clone Repository & Create Environment File
```bash
git clone https://github.com/kusuma-gowda446/result-analysis-.git
cd result-analysis-
cp .env.example .env
```

### Step 2: Build & Start Container Services
```bash
docker compose up --build -d
```

### Step 3: Access Application Services
- **SIET Result Portal**: [http://localhost:5000](http://localhost:5000)
- **Mongo Express Web UI**: [http://localhost:8081](http://localhost:8081)

---

## 🔑 Default Credentials

| Portal / Service | URL | Username / Identity | Password |
| :--- | :--- | :--- | :--- |
| **Student Portal** | `/student/login` | Student USN (e.g. `1SG24AI001`) | Same USN |
| **Faculty & Admin Portal** | `/admin/login` | `admin` | `admin123` |
| **Mongo Express UI** | `http://localhost:8081` | `admin` | `adminpass` |

---

## 🔒 Security & Environment Configuration

Configure custom secret keys and MongoDB connection strings in `.env`:

```ini
FLASK_ENV=production
SECRET_KEY=your-production-secure-secret-key
MONGO_URI=mongodb://mongodb:27017/marks_analyser
```

---

## 🧪 Running Automated Tests

Run the integration test suite inside the active Docker container:

```bash
docker compose exec -e PYTHONPATH=/app flask_app pytest -v
```

---

## 📄 License & Attribution

Developed for **Shridevi Institute of Engineering and Technology (SIET), Tumakuru**. Affiliated to VTU Belagavi, Approved by AICTE, Accredited with NAAC A Grade.
