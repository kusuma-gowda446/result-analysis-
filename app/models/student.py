import re
from app.database.connection import get_db

class StudentModel:
    @staticmethod
    def get_by_usn(usn):
        db = get_db()
        return db.students.find_one({'usn': usn})

    @staticmethod
    def get_all(search_query=None):
        db = get_db()
        if search_query:
            regex = re.compile(search_query, re.IGNORECASE)
            return list(db.students.find({'$or': [{'usn': regex}, {'name': regex}]}).sort('usn', 1))
        return list(db.students.find().sort('usn', 1))

    @staticmethod
    def get_recent(limit=5):
        db = get_db()
        return list(db.students.find().sort('_id', -1).limit(limit))

    @staticmethod
    def save_student(usn, name, semester, year, department, email):
        db = get_db()
        doc = {
            'usn': usn,
            'name': name,
            'semester': semester,
            'year': year,
            'department': department,
            'email': email
        }
        db.students.update_one({'usn': usn}, {'$set': doc}, upsert=True)

    @staticmethod
    def delete(usn):
        db = get_db()
        db.students.delete_one({'usn': usn})
        db.marks.delete_many({'student_usn': usn})
        db.admins.delete_many({'student_usn': usn})

    @staticmethod
    def count():
        db = get_db()
        return db.students.count_documents({})

    @staticmethod
    def get_marks(usn):
        db = get_db()
        return list(db.marks.find({'student_usn': usn}))

    @staticmethod
    def save_mark(usn, subject_id, score, attendance, remark):
        db = get_db()
        doc = {
            'student_usn': usn,
            'subject_id': int(subject_id),
            'score': float(score),
            'attendance': attendance,
            'remark': remark
        }
        db.marks.update_one(
            {'student_usn': usn, 'subject_id': int(subject_id)},
            {'$set': doc},
            upsert=True
        )
