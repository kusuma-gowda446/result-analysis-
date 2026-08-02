import sqlite3
import os
from flask import current_app, g

DEFAULT_SUBJECTS = [
    ("Mathematics-III", 15, 1),
    ("Digital Design",  15, 2),
    ("Operating System", 15, 3),
    ("Data Structures", 15, 4),
    ("Python for DS",   15, 5),
]

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app=None):
    db_path = app.config['DATABASE_PATH'] if app else current_app.config['DATABASE_PATH']
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

    # Seed admin user if not exists
    from werkzeug.security import generate_password_hash
    if not c.execute("SELECT 1 FROM users WHERE username='admin'").fetchone():
        c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                  ('admin', generate_password_hash('admin123'), 'admin'))

    # Seed default subjects
    if not c.execute("SELECT 1 FROM subjects").fetchone():
        c.executemany("INSERT INTO subjects (name,max_marks,display_order) VALUES (?,?,?)",
                      DEFAULT_SUBJECTS)

    conn.commit()
    conn.close()
