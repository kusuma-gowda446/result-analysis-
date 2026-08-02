from app.database.connection import get_db, is_mongo
from werkzeug.security import generate_password_hash

class UserModel:
    @staticmethod
    def get_by_username(username):
        db = get_db()
        if is_mongo(db):
            doc = db.users.find_one({'username': username})
            if doc:
                doc['id'] = doc.get('id', str(doc['_id']))
            return doc
        return db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()

    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        if is_mongo(db):
            try:
                user_id = int(user_id)
            except ValueError:
                pass
            doc = db.users.find_one({'$or': [{'id': user_id}, {'_id': user_id}]})
            if doc:
                doc['id'] = doc.get('id', str(doc['_id']))
            return doc
        return db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    @staticmethod
    def get_all_with_student_info():
        db = get_db()
        if is_mongo(db):
            users = list(db.users.find())
            out = []
            for u in users:
                u['id'] = u.get('id', str(u['_id']))
                sname = None
                if u.get('student_usn'):
                    st = db.students.find_one({'usn': u['student_usn']})
                    if st:
                        sname = st.get('name')
                u['student_name'] = sname
                out.append(u)
            return out
        return db.execute(
            "SELECT u.*, s.name as student_name FROM users u LEFT JOIN students s ON u.student_usn = s.usn ORDER BY u.id"
        ).fetchall()

    @staticmethod
    def create(username, password, role='student', student_usn=None):
        db = get_db()
        hashed = generate_password_hash(password)
        if is_mongo(db):
            next_id = db.users.count_documents({}) + 1
            db.users.insert_one({
                'id': next_id,
                'username': username,
                'password': hashed,
                'role': role,
                'student_usn': student_usn
            })
            return
        db.execute(
            "INSERT INTO users (username, password, role, student_usn) VALUES (?,?,?,?)",
            (username, hashed, role, student_usn)
        )
        db.commit()

    @staticmethod
    def update_password(user_id, new_password):
        db = get_db()
        hashed = generate_password_hash(new_password)
        if is_mongo(db):
            try:
                user_id = int(user_id)
            except ValueError:
                pass
            db.users.update_one({'$or': [{'id': user_id}, {'_id': user_id}]}, {'$set': {'password': hashed}})
            return
        db.execute("UPDATE users SET password=? WHERE id=?", (hashed, user_id))
        db.commit()

    @staticmethod
    def delete(user_id):
        db = get_db()
        if is_mongo(db):
            try:
                user_id = int(user_id)
            except ValueError:
                pass
            db.users.delete_one({'$or': [{'id': user_id}, {'_id': user_id}]})
            return
        db.execute("DELETE FROM users WHERE id=?", (user_id,))
        db.commit()

    @staticmethod
    def count():
        db = get_db()
        if is_mongo(db):
            return db.users.count_documents({})
        return db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
