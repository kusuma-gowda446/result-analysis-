from app.database.connection import get_db

class MarkModel:
    @staticmethod
    def calculate_grade_point(total, max_marks=100.0):
        if max_marks <= 0:
            return 0.0
        percentage = (total / max_marks) * 100.0
        if percentage >= 90:
            return 10.0
        elif percentage >= 80:
            return 9.0
        elif percentage >= 70:
            return 8.0
        elif percentage >= 60:
            return 7.0
        elif percentage >= 50:
            return 6.0
        elif percentage >= 40:
            return 5.0
        return 0.0

    @staticmethod
    def calculate_result(internal, external, total, max_marks=100.0):
        if not max_marks or float(max_marks) <= 0:
            max_marks = 100.0
        pass_mark = float(max_marks) * 0.40
        if float(total) >= pass_mark:
            return 'PASS'
        return 'FAIL'

    @staticmethod
    def save_mark(usn, semester, subject_id, subject_name, internal_marks, external_marks, max_marks=100.0, credits=3.0, attendance='90%', remark='Good'):
        db = get_db()
        clean_usn = str(usn).strip().upper()
        
        internal = float(internal_marks) if internal_marks is not None else 0.0
        external = float(external_marks) if external_marks is not None else 0.0
        max_m = float(max_marks) if max_marks else 100.0
        total = internal + external
        
        result = MarkModel.calculate_result(internal, external, total, max_m)
        grade_point = MarkModel.calculate_grade_point(total, max_m)

        doc = {
            'student_usn': clean_usn,
            'semester': str(semester).strip(),
            'subject_id': int(subject_id),
            'subject_name': str(subject_name).strip(),
            'internal_marks': internal,
            'external_marks': external,
            'total': total,
            'max_marks': max_m,
            'credits': float(credits),
            'grade_point': grade_point,
            'result': result,
            'attendance': attendance,
            'remark': remark
        }

        db.marks.update_one(
            {'student_usn': clean_usn, 'subject_id': int(subject_id)},
            {'$set': doc},
            upsert=True
        )
        return doc

    @staticmethod
    def get_by_student(usn):
        db = get_db()
        clean_usn = str(usn).strip().upper()
        return list(db.marks.find({'student_usn': clean_usn}).sort('subject_id', 1))

    @staticmethod
    def delete_mark(usn, subject_id):
        db = get_db()
        clean_usn = str(usn).strip().upper()
        db.marks.delete_one({'student_usn': clean_usn, 'subject_id': int(subject_id)})

    @staticmethod
    def delete_all_for_student(usn):
        db = get_db()
        clean_usn = str(usn).strip().upper()
        db.marks.delete_many({'student_usn': clean_usn})

    @staticmethod
    def calculate_summary(usn):
        marks = MarkModel.get_by_student(usn)
        if not marks:
            return {
                'total_internal': 0.0,
                'total_external': 0.0,
                'total_score': 0.0,
                'max_score': 0.0,
                'percentage': 0.0,
                'result': 'N/A',
                'sgpa': 0.0,
                'cgpa': 0.0,
                'marks': []
            }

        total_internal = sum(m.get('internal_marks', 0.0) for m in marks)
        total_external = sum(m.get('external_marks', 0.0) for m in marks)
        total_score = sum(m.get('total', 0.0) for m in marks)
        max_score = sum(m.get('max_marks', 100.0) for m in marks)

        total_credits = sum(m.get('credits', 3.0) for m in marks)
        weighted_gp = sum(m.get('grade_point', 0.0) * m.get('credits', 3.0) for m in marks)

        sgpa = round(weighted_gp / total_credits, 2) if total_credits > 0 else 0.0
        cgpa = sgpa  # For single semester view or overall cumulative average

        overall_result = 'PASS' if all(m.get('result') == 'PASS' for m in marks) else 'FAIL'
        percentage = round((total_score / max_score) * 100.0, 2) if max_score > 0 else 0.0

        return {
            'total_internal': round(total_internal, 2),
            'total_external': round(total_external, 2),
            'total_score': round(total_score, 2),
            'max_score': round(max_score, 2),
            'percentage': percentage,
            'result': overall_result,
            'sgpa': sgpa,
            'cgpa': cgpa,
            'marks': marks
        }
