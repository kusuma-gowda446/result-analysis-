from app.models.student import StudentModel
from app.models.subject import SubjectModel
from app.models.mark import MarkModel
from app.database.connection import get_db
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
        grand_total = 0.0
        max_total   = 0.0
        total_internal = 0.0
        total_external = 0.0
        total_credits = 0.0
        weighted_gp = 0.0
        all_passed = True
        
        for sub in subjects_db:
            sid = sub['id']
            mark = db.marks.find_one({'student_usn': row['usn'], 'subject_id': int(sid)})
            
            if mark:
                internal = float(mark.get('internal_marks', mark.get('score', 0.0)))
                external = float(mark.get('external_marks', 0.0))
                score = mark.get('total', internal + external)
                res = mark.get('result', MarkModel.calculate_result(internal, external, score, sub['max_marks']))
                gp = mark.get('grade_point', MarkModel.calculate_grade_point(score, sub['max_marks']))
                att = mark.get('attendance', '90%')
                rem = mark.get('remark', 'Good')
            else:
                internal = 0.0
                external = 0.0
                score = 0.0
                res = 'FAIL'
                gp = 0.0
                att = '-'
                rem = '-'
                
            credits = float(sub.get('credits', 3.0))
            if res != 'PASS':
                all_passed = False
                
            grand_total += score
            max_total += sub['max_marks']
            total_internal += internal
            total_external += external
            total_credits += credits
            weighted_gp += (gp * credits)
            
            subjects_out.append({
                'id':             sid,
                'name':           sub['name'],
                'internal_marks': internal,
                'external_marks': external,
                'score':          score,
                'total':          score,
                'result':         res,
                'grade_point':    gp,
                'attendance':     att,
                'remark':         rem,
                'max':            sub['max_marks'],
            })
        
        percentage = round((grand_total / max_total * 100), 2) if max_total > 0 else 0.0
        sgpa = round(weighted_gp / total_credits, 2) if total_credits > 0 else 0.0
        cgpa = sgpa
        overall_result = 'PASS' if (all_passed and len(subjects_db) > 0) else ('PASS' if grand_total >= (max_total * 0.4) else 'FAIL')

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
            'name':           row['name'],
            'usn':            row['usn'],
            'dob':            row.get('dob', '-'),
            'semester':       row.get('semester', '3'),
            'section':        row.get('section', 'A'),
            'year':           row.get('year', '2024-25'),
            'department':     row.get('department', 'AI & Data Science'),
            'phone':          row.get('phone', '-'),
            'email':          row.get('email', '-'),
            'address':        row.get('address', '-'),
            'subjects':       subjects_out,
            'total_internal': round(total_internal, 2),
            'total_external': round(total_external, 2),
            'total':          round(grand_total, 2),
            'grand_total':    round(grand_total, 2),
            'max_total':      round(max_total, 2),
            'percentage':     percentage,
            'result':         overall_result,
            'sgpa':           sgpa,
            'cgpa':           cgpa,
            'grade':          grade
        }

    @staticmethod
    def generate_pdf(student_data):
        return generate_pdf_report(student_data)
