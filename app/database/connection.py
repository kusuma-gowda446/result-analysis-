from flask import current_app, g
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

DEFAULT_SUBJECTS = [
    {"id": 1, "name": "Mathematics-III", "max_marks": 15.0, "display_order": 1},
    {"id": 2, "name": "Digital Design",  "max_marks": 15.0, "display_order": 2},
    {"id": 3, "name": "Operating System", "max_marks": 15.0, "display_order": 3},
    {"id": 4, "name": "Data Structures", "max_marks": 15.0, "display_order": 4},
    {"id": 5, "name": "Python for DS",   "max_marks": 15.0, "display_order": 5},
]

def get_db():
    if 'db' not in g:
        mongo_uri = current_app.config.get('MONGO_URI') or 'mongodb://localhost:27017/marks_analyser'
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        
        # Determine target database name (e.g. marks_analyser or marks_analyser_test)
        db_name = 'marks_analyser_test' if current_app.config.get('TESTING') else 'marks_analyser'
        g.mongo_client = client
        g.db = client[db_name]
    return g.db

def close_db(e=None):
    client = g.pop('mongo_client', None)
    if client is not None:
        client.close()

def init_db(app=None):
    mongo_uri = (app.config.get('MONGO_URI') if app else current_app.config.get('MONGO_URI')) or 'mongodb://localhost:27017/marks_analyser'
    is_testing = app.config.get('TESTING') if app else current_app.config.get('TESTING', False)
    db_name = 'marks_analyser_test' if is_testing else 'marks_analyser'
    
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        db = client[db_name]

        # 1. Collection 'admins'
        db.admins.create_index('username', unique=True)

        # 2. Collection 'students'
        db.students.create_index('usn', unique=True)

        # 3. Collection 'marks'
        db.marks.create_index([('student_usn', 1), ('subject_id', 1)], unique=True)

        # 4. Collection 'subjects'
        db.subjects.create_index('id', unique=True)

        # Seed default admin user in 'admins' collection
        if not db.admins.find_one({'username': 'admin'}):
            db.admins.insert_one({
                'id': 1,
                'username': 'admin',
                'password': generate_password_hash('admin123'),
                'role': 'admin',
                'student_usn': None
            })

        # Seed default subjects
        if db.subjects.count_documents({}) == 0:
            db.subjects.insert_many(DEFAULT_SUBJECTS)

        client.close()
    except Exception as err:
        print(f"MongoDB connection/initialization info: {err}")
