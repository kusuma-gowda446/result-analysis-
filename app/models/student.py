import re
from app.database.connection import get_db, is_mongo

class StudentModel:
    @staticmethod
    def get_by_usn(usn):
        db = get_db()
        if is_mongo(db):
            return db.students.find_one({'usn': usn})
        return db.execute("SELECT * FROM students WHERE usn=?", (usn,)).fetchone()

    @staticmethod
    def get_all(search_query=None):
        db = get_db()
        if is_mongo(db):
            if search_query:
                regex = re.compile(search_query, re.IGNORECASE)
                return list(db.students.find({'$or': [{'usn': regex}, {'name': regex}]}).sort('usn', 1))
            return list(db.students.find().sort('usn', 1))
        if search_query:
            return db.execute(
                "SELECT * FROM students WHERE usn LIKE ? OR name LIKE ? ORDER BY usn",
                (f'%{search_query}%', f'%{search_query}%')
            ).fetchall()
        return db.execute("SELECT * FROM students ORDER BY usn").fetchall()

    @staticmethod
    def get_recent(limit=5):
        db = get_db()
        if is_mongo(db):
            return list(db.students.find().sort('_id', -1).limit(limit))
        return db.execute("SELECT usn, name, semester, year FROM students ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

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
        if is_mongo(db):
            db.students.update_one({'usn': usn}, {'$set': doc}, upsert=True)
            return
        db.execute("""
            INSERT INTO students (usn, name, semester, year, department, email)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(usn) DO UPDATE SET
                name=excluded.name,
                semester=excluded.semester,
                year=excluded.year,
                department=excluded.department,
                email=excluded.email
        """, (usn, name, semester, year, department, email))
        db.commit()

    @staticmethod
    def delete(usn):
        db = get_db()
        if is_mongo(db):
            db.students.delete_one({'usn': usn})
            db.student_marks.delete_many({'student_usn': usn})
            return
        db.execute("DELETE FROM students WHERE usn=?", (usn,))
        db.commit()

    @staticmethod
    def count():
        db = get_db()
        if is_mongo(db):
            return db.students.count_documents({})
        return db.execute("SELECT COUNT(*) FROM students").fetchone()[0]

    @staticmethod
    def get_marks(usn):
        db = get_db()
        if is_mongo(db):
            return list(db.student_marks.find({'student_usn': usn}))
        return db.execute(
            "SELECT subject_id, score, attendance, remark FROM student_marks WHERE student_usn=?",
            (usn,)
        ).fetchall()

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
        if is_mongo(db):
            db.student_marks.update_one(
                {'student_usn': usn, 'subject_id': int(subject_id)},
                {'$set': doc},
                upsert=True
            )
            return
        db.execute("""
            INSERT INTO student_marks (student_usn, subject_id, score, attendance, remark)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(student_usn, subject_id) DO UPDATE SET
                score=excluded.score,
                attendance=excluded.attendance,
                remark=excluded.remark
        """, (usn, subject_id, score, attendance, remark))
        db.commit()
