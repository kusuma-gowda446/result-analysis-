from app.models.student import StudentModel
from app.models.subject import SubjectModel
from app.database.connection import get_db, is_mongo
from app.utils.pdf_generator import generate_pdf_report

class ReportService:
    @staticmethod
    def build_student_report(usn):
        row = StudentModel.get_by_usn(usn)
        if not row:
            return None
        row = dict(row)
            
        subjects_db = SubjectModel.get_all()
        db = get_db()
        
        subjects_out = []
        grand_total = 0
        max_total   = 0
        
        for sub in subjects_db:
            sid = sub['id']
            if is_mongo(db):
                mark = db.student_marks.find_one({'student_usn': usn, 'subject_id': int(sid)})
            else:
                mark = db.execute(
                    "SELECT * FROM student_marks WHERE student_usn=? AND subject_id=?",
                    (usn, sid)
                ).fetchone()
                
            score = mark['score'] if mark else 0
            grand_total += score
            max_total   += sub['max_marks']
            subjects_out.append({
                'id':         sid,
                'name':       sub['name'],
                'score':      score,
                'attendance': mark['attendance'] if mark else '-',
                'remark':     mark['remark']     if mark else '-',
                'max':        sub['max_marks'],
            })
        
        percentage = round((grand_total / max_total * 100), 1) if max_total > 0 else 0
        
        if percentage >= 85:
            grade = 'Distinction'
        elif percentage >= 70:
            grade = 'First Class'
        elif percentage >= 50:
            grade = 'Second Class'
        elif percentage >= 40:
            grade = 'Pass'
        else:
            grade = 'Fail'

        return {
            'name':       row['name'],
            'usn':        row['usn'],
            'semester':   row['semester'],
            'year':       row['year'],
            'department': row.get('department', 'AI & Data Science'),
            'email':      row.get('email', '-'),
            'subjects':   subjects_out,
            'total':      grand_total,
            'max_total':  max_total,
            'percentage': percentage,
            'grade':      grade
        }

    @staticmethod
    def generate_pdf(student_data):
        return generate_pdf_report(student_data)
