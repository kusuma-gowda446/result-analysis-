from app.database.connection import get_db

class SubjectModel:
    @staticmethod
    def get_all():
        conn = get_db()
        return conn.execute("SELECT * FROM subjects ORDER BY display_order, id").fetchall()

    @staticmethod
    def get_by_id(subject_id):
        conn = get_db()
        return conn.execute("SELECT * FROM subjects WHERE id=?", (subject_id,)).fetchone()

    @staticmethod
    def create(name, max_marks=15, display_order=0):
        conn = get_db()
        conn.execute("INSERT INTO subjects (name, max_marks, display_order) VALUES (?,?,?)",
                     (name, max_marks, display_order))
        conn.commit()

    @staticmethod
    def update(subject_id, name, max_marks, display_order):
        conn = get_db()
        conn.execute("UPDATE subjects SET name=?, max_marks=?, display_order=? WHERE id=?",
                     (name, max_marks, display_order, subject_id))
        conn.commit()

    @staticmethod
    def delete(subject_id):
        conn = get_db()
        sub = conn.execute("SELECT name FROM subjects WHERE id=?", (subject_id,)).fetchone()
        if sub:
            conn.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
            conn.commit()
        return sub

    @staticmethod
    def count():
        conn = get_db()
        return conn.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
