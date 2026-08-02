from app.database.connection import get_db
from werkzeug.security import generate_password_hash, check_password_hash

class UserModel:
    @staticmethod
    def get_by_username(username):
        conn = get_db()
        return conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()

    @staticmethod
    def get_by_id(user_id):
        conn = get_db()
        return conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    @staticmethod
    def get_all_with_student_info():
        conn = get_db()
        return conn.execute(
            "SELECT u.*, s.name as student_name FROM users u LEFT JOIN students s ON u.student_usn = s.usn ORDER BY u.id"
        ).fetchall()

    @staticmethod
    def create(username, password, role='student', student_usn=None):
        conn = get_db()
        hashed = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (username, password, role, student_usn) VALUES (?,?,?,?)",
            (username, hashed, role, student_usn)
        )
        conn.commit()

    @staticmethod
    def update_password(user_id, new_password):
        conn = get_db()
        hashed = generate_password_hash(new_password)
        conn.execute("UPDATE users SET password=? WHERE id=?", (hashed, user_id))
        conn.commit()

    @staticmethod
    def delete(user_id):
        conn = get_db()
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()

    @staticmethod
    def count():
        conn = get_db()
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
