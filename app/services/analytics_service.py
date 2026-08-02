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
                grade = rpt.get('grade', 'Fail')
                if grade in grade_counts:
                    grade_counts[grade] += 1
                else:
                    grade_counts['Pass'] += 1

        subjects = SubjectModel.get_all()
        db = get_db()
        subject_stats = []
        for sub in subjects:
            sid = sub['id']
            # Match either integer or string subject_id
            cursor = db.marks.find({'$or': [{'subject_id': sid}, {'subject_id': str(sid)}]})
            scores = []
            for doc in cursor:
                val = doc.get('total', doc.get('score', doc.get('internal_marks', 0)))
                scores.append(float(val) if val is not None else 0.0)

            avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
            max_score = max(scores) if scores else 0.0
            min_score = min(scores) if scores else 0.0
            
            subject_stats.append({
                'name': sub['name'],
                'max_marks': sub['max_marks'],
                'avg_score': avg_score,
                'max_score': max_score,
                'min_score': min_score
            })

        all_reports.sort(key=lambda x: x.get('percentage', 0), reverse=True)
        top_5 = [{
            'usn': r['usn'],
            'name': r['name'],
            'total': r.get('total', 0),
            'percentage': r.get('percentage', 0),
            'grade': r.get('grade', 'Pass')
        } for r in all_reports[:5]]

        return {
            'total_students': len(students),
            'grade_counts': grade_counts,
            'subject_stats': subject_stats,
            'top_performers': top_5
        }
