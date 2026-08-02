import os
import sqlite3
from flask import current_app, g
import pymongo
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

DEFAULT_SUBJECTS = [
    {"id": 1, "name": "Mathematics-III", "max_marks": 15.0, "display_order": 1},
    {"id": 2, "name": "Digital Design",  "max_marks": 15.0, "display_order": 2},
    {"id": 3, "name": "Operating System", "max_marks": 15.0, "display_order": 3},
    {"id": 4, "name": "Data Structures", "max_marks": 15.0, "display_order": 4},
    {"id": 5, "name": "Python for DS",   "max_marks": 15.0, "display_order": 5},
]

def is_mongo(db):
    return isinstance(db, pymongo.database.Database)

def get_db():
    if 'db' not in g:
        is_testing = current_app.config.get('TESTING', False)
        mongo_uri = current_app.config.get('MONGO_URI') or 'mongodb://mongodb:27017/marks_analyser'
        
        if not (is_testing and 'mongodb://' in mongo_uri):
            try:
                timeout = 100 if is_testing else 1000
                client = MongoClient(mongo_uri, serverSelectionTimeoutMS=timeout)
                client.admin.command('ping')
                db_name = mongo_uri.rstrip('/').split('/')[-1] or 'marks_analyser'
                g.mongo_client = client
                g.db = client[db_name]
                return g.db
            except Exception:
                pass

        db_path = current_app.config['DATABASE_PATH']
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None and isinstance(db, sqlite3.Connection):
        db.close()
    client = g.pop('mongo_client', None)
    if client is not None:
        client.close()

def init_db(app=None):
    db_path = app.config['DATABASE_PATH'] if app else current_app.config['DATABASE_PATH']
    mongo_uri = (app.config.get('MONGO_URI') if app else current_app.config.get('MONGO_URI')) or 'mongodb://mongodb:27017/marks_analyser'
    is_testing = app.config.get('TESTING') if app else current_app.config.get('TESTING', False)

    if not is_testing:
        try:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=1000)
            client.admin.command('ping')
            db_name = mongo_uri.rstrip('/').split('/')[-1] or 'marks_analyser'
            mdb = client[db_name]
            
            mdb.users.create_index('username', unique=True)
            mdb.students.create_index('usn', unique=True)
            mdb.subjects.create_index('id', unique=True)
            mdb.student_marks.create_index([('student_usn', 1), ('subject_id', 1)], unique=True)
            
            if not mdb.users.find_one({'username': 'admin'}):
                mdb.users.insert_one({
                    'id': 1,
                    'username': 'admin',
                    'password': generate_password_hash('admin123'),
                    'role': 'admin',
                    'student_usn': None
                })
                
            if mdb.subjects.count_documents({}) == 0:
                mdb.subjects.insert_many(DEFAULT_SUBJECTS)
                
            client.close()
            return
        except Exception:
            pass

    # Fallback to SQLite initialization
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        username    TEXT UNIQUE NOT NULL,
        password    TEXT NOT NULL,
        role        TEXT NOT NULL DEFAULT "student",
        student_usn TEXT DEFAULT NULL,
        created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_usn) REFERENCES students(usn) ON DELETE SET NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        usn        TEXT UNIQUE NOT NULL,
        name       TEXT NOT NULL,
        semester   TEXT DEFAULT "3",
        year       TEXT DEFAULT "2024-25",
        department TEXT DEFAULT "AI & Data Science",
        email      TEXT DEFAULT "-"
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS subjects (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT NOT NULL,
        max_marks     REAL DEFAULT 15,
        display_order INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS student_marks (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        student_usn TEXT NOT NULL,
        subject_id  INTEGER NOT NULL,
        score       REAL DEFAULT 0,
        attendance  TEXT DEFAULT "-",
        remark      TEXT DEFAULT "-",
        FOREIGN KEY (student_usn) REFERENCES students(usn) ON DELETE CASCADE,
        FOREIGN KEY (subject_id)  REFERENCES subjects(id)  ON DELETE CASCADE,
        UNIQUE (student_usn, subject_id)
    )''')

    if not c.execute("SELECT 1 FROM users WHERE username='admin'").fetchone():
        c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                  ('admin', generate_password_hash('admin123'), 'admin'))

    if not c.execute("SELECT 1 FROM subjects").fetchone():
        c.executemany("INSERT INTO subjects (name,max_marks,display_order) VALUES (?,?,?)",
                      [(s['name'], s['max_marks'], s['display_order']) for s in DEFAULT_SUBJECTS])

    conn.commit()
    conn.close()
