from app.database.connection import get_db, close_db, init_db

def build_student_report(usn):
    from app.services.report_service import ReportService
    return ReportService.build_student_report(usn)
