from app.database.connection import get_db

class StudentModel:
    @staticmethod
    def get_by_usn(usn):
        conn = get_db()
        return conn.execute("SELECT * FROM students WHERE usn=?", (usn,)).fetchone()

    @staticmethod
    def get_all(search_query=None):
        conn = get_db()
        if search_query:
            return conn.execute(
                "SELECT * FROM students WHERE usn LIKE ? OR name LIKE ? ORDER BY usn",
                (f'%{search_query}%', f'%{search_query}%')
            ).fetchall()
        return conn.execute("SELECT * FROM students ORDER BY usn").fetchall()

    @staticmethod
    def get_recent(limit=5):
        conn = get_db()
        return conn.execute("SELECT usn, name, semester, year FROM students ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    @staticmethod
    def save_student(usn, name, semester, year, department, email):
        conn = get_db()
        conn.execute("""
            INSERT INTO students (usn, name, semester, year, department, email)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(usn) DO UPDATE SET
                name=excluded.name,
                semester=excluded.semester,
                year=excluded.year,
                department=excluded.department,
                email=excluded.email
        """, (usn, name, semester, year, department, email))
        conn.commit()

    @staticmethod
    def delete(usn):
        conn = get_db()
        conn.execute("DELETE FROM students WHERE usn=?", (usn,))
        conn.commit()

    @staticmethod
    def count():
        conn = get_db()
        return conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]

    @staticmethod
    def get_marks(usn):
        conn = get_db()
        return conn.execute(
            "SELECT subject_id, score, attendance, remark FROM student_marks WHERE student_usn=?",
            (usn,)
        ).fetchall()

    @staticmethod
    def save_mark(usn, subject_id, score, attendance, remark):
        conn = get_db()
        conn.execute("""
            INSERT INTO student_marks (student_usn, subject_id, score, attendance, remark)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(student_usn, subject_id) DO UPDATE SET
                score=excluded.score,
                attendance=excluded.attendance,
                remark=excluded.remark
        """, (usn, subject_id, score, attendance, remark))
        conn.commit()
