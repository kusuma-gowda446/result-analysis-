import re
from app.database.connection import get_db

class StudentModel:
    @staticmethod
    def get_by_usn(usn):
        db = get_db()
        if not usn:
            return None
        return db.students.find_one({'usn': str(usn).strip().upper()})

    @staticmethod
    def authenticate(usn, password):
        db = get_db()
        if not usn or not password:
            return None
            
        clean_usn = str(usn).strip().upper()
        clean_pass = str(password).strip().upper()
        
        # Student logs in using USN as password
        if clean_usn != clean_pass:
            return None

        return db.students.find_one({'usn': clean_usn})

    @staticmethod
    def get_all(search_query=None):
        db = get_db()
        if search_query:
            regex = re.compile(search_query, re.IGNORECASE)
            return list(db.students.find({'$or': [
                {'usn': regex},
                {'name': regex},
                {'department': regex},
                {'section': regex},
                {'email': regex},
                {'phone': regex}
            ]}).sort('usn', 1))
        return list(db.students.find().sort('usn', 1))

    @staticmethod
    def get_recent(limit=5):
        db = get_db()
        return list(db.students.find().sort('_id', -1).limit(limit))

    @staticmethod
    def save_student(usn, name, dob='', department='AI & Data Science', semester='3', section='A', phone='', email='', address='', year='2024-25'):
        db = get_db()
        clean_usn = str(usn).strip().upper()
        doc = {
            'usn': clean_usn,
            'name': str(name).strip(),
            'dob': str(dob).strip() if dob else '',
            'department': str(department).strip() if department else 'AI & Data Science',
            'semester': str(semester).strip() if semester else '3',
            'section': str(section).strip().upper() if section else 'A',
            'phone': str(phone).strip() if phone else '',
            'email': str(email).strip() if email else '',
            'address': str(address).strip() if address else '',
            'year': str(year).strip() if year else '2024-25'
        }
        db.students.update_one({'usn': clean_usn}, {'$set': doc}, upsert=True)

    @staticmethod
    def update_student(usn, name, dob, department, semester, section, phone, email, address, year='2024-25'):
        StudentModel.save_student(usn, name, dob, department, semester, section, phone, email, address, year)

    @staticmethod
    def delete(usn):
        db = get_db()
        clean_usn = str(usn).strip().upper()
        db.students.delete_one({'usn': clean_usn})
        db.marks.delete_many({'student_usn': clean_usn})
        db.admins.delete_many({'student_usn': clean_usn})

    @staticmethod
    def count():
        db = get_db()
        return db.students.count_documents({})

    @staticmethod
    def get_marks(usn):
        db = get_db()
        clean_usn = str(usn).strip().upper() if isinstance(usn, str) else usn
        return list(db.marks.find({'student_usn': clean_usn}))

    @staticmethod
    def save_mark(usn, subject_id, score, attendance, remark):
        db = get_db()
        clean_usn = str(usn).strip().upper()
        doc = {
            'student_usn': clean_usn,
            'subject_id': int(subject_id),
            'score': float(score),
            'attendance': attendance,
            'remark': remark
        }
        db.marks.update_one(
            {'student_usn': clean_usn, 'subject_id': int(subject_id)},
            {'$set': doc},
            upsert=True
        )
