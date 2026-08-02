from app.models.student import StudentModel
from app.models.subject import SubjectModel
from app.services.report_service import ReportService
from app.database.connection import get_db

class AnalyticsService:
    @staticmethod
    def get_class_analytics():
        students = StudentModel.get_all()
        
        grade_counts = {
            'Distinction': 0,
            'First Class': 0,
            'Second Class': 0,
            'Pass': 0,
            'Fail': 0
        }
        
        all_reports = []
        for s in students:
            rpt = ReportService.build_student_report(s['usn'])
            if rpt:
                all_reports.append(rpt)
                grade = rpt['grade']
                if grade in grade_counts:
                    grade_counts[grade] += 1

        subjects = SubjectModel.get_all()
        conn = get_db()
        subject_stats = []
        for sub in subjects:
            scores = conn.execute(
                "SELECT score FROM student_marks WHERE subject_id=?", (sub['id'],)
            ).fetchall()
            val_list = [r['score'] for r in scores]
            avg_score = round(sum(val_list) / len(val_list), 2) if val_list else 0.0
            max_score = max(val_list) if val_list else 0.0
            min_score = min(val_list) if val_list else 0.0
            
            subject_stats.append({
                'name': sub['name'],
                'max_marks': sub['max_marks'],
                'avg_score': avg_score,
                'max_score': max_score,
                'min_score': min_score
            })

        all_reports.sort(key=lambda x: x['percentage'], reverse=True)
        top_5 = [{
            'usn': r['usn'],
            'name': r['name'],
            'total': r['total'],
            'percentage': r['percentage'],
            'grade': r['grade']
        } for r in all_reports[:5]]

        return {
            'total_students': len(students),
            'grade_counts': grade_counts,
            'subject_stats': subject_stats,
            'top_performers': top_5
        }
