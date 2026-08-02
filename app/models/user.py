from app.database.connection import get_db
from werkzeug.security import generate_password_hash

class UserModel:
    @staticmethod
    def get_by_username(username):
        db = get_db()
        doc = db.admins.find_one({'username': username})
        if doc:
            doc['id'] = doc.get('id', str(doc['_id']))
        return doc

    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        try:
            int_id = int(user_id)
        except (ValueError, TypeError):
            int_id = user_id
        doc = db.admins.find_one({'$or': [{'id': int_id}, {'_id': user_id}]})
        if doc:
            doc['id'] = doc.get('id', str(doc['_id']))
        return doc

    @staticmethod
    def get_all_with_student_info():
        db = get_db()
        users = list(db.admins.find())
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

    @staticmethod
    def create(username, password, role='student', student_usn=None):
        db = get_db()
        hashed = generate_password_hash(password)
        next_id = db.admins.count_documents({}) + 1
        db.admins.insert_one({
            'id': next_id,
            'username': username,
            'password': hashed,
            'role': role,
            'student_usn': student_usn
        })

    @staticmethod
    def update_password(user_id, new_password):
        db = get_db()
        hashed = generate_password_hash(new_password)
        try:
            int_id = int(user_id)
        except (ValueError, TypeError):
            int_id = user_id
        db.admins.update_one({'$or': [{'id': int_id}, {'_id': user_id}]}, {'$set': {'password': hashed}})

    @staticmethod
    def delete(user_id):
        db = get_db()
        try:
            int_id = int(user_id)
        except (ValueError, TypeError):
            int_id = user_id
        db.admins.delete_one({'$or': [{'id': int_id}, {'_id': user_id}]})

    @staticmethod
    def count():
        db = get_db()
        return db.admins.count_documents({})
