from flask import Flask, render_template, request, send_file, session, redirect, url_for, flash
import sqlite3, io, os
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from functools import wraps

app = Flask(__name__)
app.secret_key = 'shridevi-secret-key-2024'
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

DEFAULT_SUBJECTS = [
    ("Mathematics-III", 15, 1),
    ("Digital Design",  15, 2),
    ("Operating System",15, 3),
    ("Data Structures", 15, 4),
    ("Python for DS",   15, 5),
]

# ─────────────────────────────────────────
#  DB Helpers
# ─────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def col_names(conn, table):
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]

def init_db():
    conn = get_db()
    c = conn.cursor()

    # ── users ──
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role     TEXT NOT NULL DEFAULT "student"
    )''')

    # ── students (lean — no per-subject columns) ──
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        usn      TEXT UNIQUE NOT NULL,
        name     TEXT NOT NULL,
        semester TEXT DEFAULT "3",
        year     TEXT DEFAULT "2024-25"
    )''')

    # ── subjects (fully editable) ──
    c.execute('''CREATE TABLE IF NOT EXISTS subjects (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT NOT NULL,
        max_marks     REAL DEFAULT 15,
        display_order INTEGER DEFAULT 0
    )''')

    # ── student marks (one row per student × subject) ──
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

    # ── seed admin ──
    if not c.execute("SELECT 1 FROM users WHERE username='admin'").fetchone():
        c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                  ('admin', generate_password_hash('admin123'), 'admin'))

    # ── seed default subjects ──
    if not c.execute("SELECT 1 FROM subjects").fetchone():
        c.executemany("INSERT INTO subjects (name,max_marks,display_order) VALUES (?,?,?)",
                      DEFAULT_SUBJECTS)

    # ── migrate old per-column marks if they exist ──
    _migrate_old_data(conn)

    conn.commit()
    conn.close()

def _migrate_old_data(conn):
    """Move data from the old math_score/dd_score/… columns into student_marks."""
    old_cols = col_names(conn, 'students')
    if 'math_score' not in old_cols:
        return  # nothing to migrate

    subj_rows = conn.execute("SELECT id, name FROM subjects ORDER BY display_order").fetchall()
    name_to_id = {r['name']: r['id'] for r in subj_rows}

    mapping = {
        "Mathematics-III": ("math_score","math_att","math_remark"),
        "Digital Design":  ("dd_score",  "dd_att",  "dd_remark"),
        "Operating System":("os_score",  "os_att",  "os_remark"),
        "Data Structures": ("ds_score",  "ds_att",  "ds_remark"),
        "Python for DS":   ("py_score",  "py_att",  "py_remark"),
    }

    for student in conn.execute("SELECT * FROM students").fetchall():
        d = dict(student)
        for subj_name, (sc, at, rm) in mapping.items():
            sid = name_to_id.get(subj_name)
            if sid is None:
                continue
            conn.execute("""
                INSERT OR IGNORE INTO student_marks (student_usn,subject_id,score,attendance,remark)
                VALUES (?,?,?,?,?)
            """, (d['usn'], sid, d.get(sc, 0), d.get(at, '-'), d.get(rm, '-')))
    conn.commit()

# ─────────────────────────────────────────
#  Report builder
# ─────────────────────────────────────────

def build_student_report(usn):
    conn = get_db()
    row = conn.execute("SELECT * FROM students WHERE usn=?", (usn,)).fetchone()
    if not row:
        conn.close()
        return None
    subjects_db = conn.execute(
        "SELECT * FROM subjects ORDER BY display_order, id").fetchall()
    subjects_out = []
    grand_total = 0
    max_total   = 0
    for sub in subjects_db:
        mark = conn.execute(
            "SELECT * FROM student_marks WHERE student_usn=? AND subject_id=?",
            (usn, sub['id'])
        ).fetchone()
        score = mark['score'] if mark else 0
        grand_total += score
        max_total   += sub['max_marks']
        subjects_out.append({
            'name':       sub['name'],
            'score':      score,
            'attendance': mark['attendance'] if mark else '-',
            'remark':     mark['remark']     if mark else '-',
            'max':        sub['max_marks'],
        })
    conn.close()
    return {
        'name':      row['name'],
        'usn':       row['usn'],
        'semester':  row['semester'],
        'year':      row['year'],
        'subjects':  subjects_out,
        'total':     grand_total,
        'max_total': max_total,
    }

# ─────────────────────────────────────────
#  Decorators
# ─────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def deco(*a, **kw):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*a, **kw)
    return deco

def admin_required(f):
    @wraps(f)
    def deco(*a, **kw):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*a, **kw)
    return deco

# ─────────────────────────────────────────
#  Auth
# ─────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        u = request.form.get('username','').strip()
        p = request.form.get('password','')
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], p):
            session.update({'user_id': user['id'], 'username': user['username'], 'role': user['role']})
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─────────────────────────────────────────
#  Dashboard & Search
# ─────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html',
                           username=session.get('username'),
                           role=session.get('role'))

@app.route('/search', methods=['POST'])
@login_required
def search():
    usn = request.form.get('usn','').strip().upper()
    if not usn:
        flash('Please enter a USN.', 'warning')
        return redirect(url_for('dashboard'))
    student = build_student_report(usn)
    if not student:
        flash(f'No student found with USN: {usn}', 'danger')
        return redirect(url_for('dashboard'))
    session['report_data'] = student
    return render_template('report.html', student=student)

# ─────────────────────────────────────────
#  PDF
# ─────────────────────────────────────────

@app.route('/download_pdf')
@login_required
def download_pdf():
    student = session.get('report_data')
    if not student:
        flash('No report found. Please search first.', 'warning')
        return redirect(url_for('dashboard'))

    buffer = io.BytesIO()
    navy  = colors.HexColor('#0e2245')
    cream = colors.HexColor('#f0f3f8')
    light = colors.HexColor('#f7f9fc')

    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=14*mm, bottomMargin=14*mm)
    styles = getSampleStyleSheet()
    story  = []
    W, H   = letter

    def draw_border(cv, d):
        cv.saveState()
        cv.setStrokeColor(navy)
        cv.setLineWidth(3)
        cv.rect(10*mm, 10*mm, W-20*mm, H-20*mm)
        cv.setLineWidth(1)
        cv.rect(13*mm, 13*mm, W-26*mm, H-26*mm)
        cv.restoreState()

    def ps(name, **kw):
        return ParagraphStyle(name, parent=styles[kw.pop('parent','Normal')], **kw)

    affil_s = ps('affil', fontSize=9,  textColor=colors.HexColor('#555555'), alignment=TA_CENTER, fontName='Helvetica-Oblique')
    title_s = ps('title', fontSize=18, textColor=navy, alignment=TA_CENTER, fontName='Helvetica-Bold', leading=22)
    addr_s  = ps('addr',  fontSize=9,  textColor=colors.HexColor('#333333'), alignment=TA_CENTER, leading=13)
    dept_s  = ps('dept',  fontSize=11, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold')
    rpt_s   = ps('rpt',   fontSize=13, textColor=navy, alignment=TA_CENTER, fontName='Helvetica-Bold')
    sub_s   = ps('sub',   fontSize=9,  textColor=colors.HexColor('#555555'), alignment=TA_CENTER, fontName='Helvetica-Oblique')
    lbl_s   = ps('lbl',   fontSize=9,  textColor=navy, fontName='Helvetica-Bold')
    val_s   = ps('val',   fontSize=10, textColor=colors.HexColor('#111111'))
    note_s  = ps('note',  fontSize=8,  textColor=colors.HexColor('#666666'), alignment=TA_CENTER, fontName='Helvetica-Oblique')
    sig_s   = ps('sig',   fontSize=9,  textColor=navy, alignment=TA_CENTER, fontName='Helvetica-Bold')
    foot_s  = ps('foot',  fontSize=8,  textColor=colors.HexColor('#777777'), alignment=TA_CENTER)
    pct_s   = ps('pct',   fontSize=8,  textColor=colors.HexColor('#555555'), alignment=TA_CENTER)

    story += [
        Paragraph('Affiliated to Visvesvaraya Technological University (VTU), Belagavi | Approved by AICTE', affil_s),
        Spacer(1,4),
        Paragraph('Shridevi Institute of Engineering and Technology', title_s),
        Paragraph('Sira Road, Tumakuru – 572 106, Karnataka, India', addr_s),
        Paragraph('Phone: 0816-225800  |  Email: info@shrideviiet.ac.in  |  www.shrideviiet.ac.in', addr_s),
        Spacer(1,6),
        HRFlowable(width='100%', thickness=2, color=navy),
    ]

    dept_tbl = Table([[Paragraph('DEPARTMENT OF ARTIFICIAL INTELLIGENCE &amp; DATA SCIENCE', dept_s)]],
                     colWidths=[doc.width])
    dept_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), navy),
        ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    story += [dept_tbl, Spacer(1,10),
              Paragraph('INTERNAL ASSESSMENT PROGRESS REPORT', rpt_s), Spacer(1,3),
              Paragraph(f"Academic Year: {student['year']}  |  Semester: {student['semester']}  |  Batch: 2024–2028", sub_s),
              Spacer(1,10), HRFlowable(width='100%', thickness=1, color=navy), Spacer(1,6)]

    half = doc.width / 2
    det = Table([
        [Paragraph('Student Name',lbl_s), Paragraph(student['name'],val_s),
         Paragraph('USN',lbl_s),          Paragraph(student['usn'], val_s)],
        [Paragraph('Programme',lbl_s),    Paragraph('B.E. – AI &amp; Data Science',val_s),
         Paragraph('Semester',lbl_s),     Paragraph(f"{student['semester']}rd Semester",val_s)],
        [Paragraph('Academic Year',lbl_s),Paragraph(student['year'],val_s),
         Paragraph('Assessment',lbl_s),   Paragraph('IA – 1 &amp; IA – 2 (Combined)',val_s)],
    ], colWidths=[half*0.32, half*0.68, half*0.32, half*0.68])
    det.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,-1),cream), ('BACKGROUND',(2,0),(2,-1),cream),
        ('BOX',(0,0),(-1,-1),1.2,navy), ('INNERGRID',(0,0),(-1,-1),0.5,colors.HexColor('#aaaaaa')),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
    ]))
    story += [det, Spacer(1,10)]

    hdr_s = ps('thdr', fontSize=9, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold')
    td_c  = ps('tdc',  fontSize=10, alignment=TA_CENTER)
    td_l  = ps('tdl',  fontSize=10, alignment=TA_LEFT)
    td_g  = ps('tdg',  fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor('#166534'), fontName='Helvetica-Bold')
    td_b  = ps('tdb',  fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor('#854d0e'), fontName='Helvetica-Bold')
    td_r  = ps('tdr',  fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor('#991b1b'), fontName='Helvetica-Bold')

    def score_para(score, max_m):
        ratio = score / max_m if max_m else 0
        if ratio >= 0.8:   return Paragraph(str(score), td_g)
        elif ratio >= 0.6: return Paragraph(str(score), td_b)
        else:              return Paragraph(str(score), td_r)

    marks_data = [[Paragraph(h, hdr_s) for h in
                   ['Sl.','Subject / Course Title','Max Marks','Marks Obtained','Attendance','Remarks']]]
    for i, s in enumerate(student['subjects'], 1):
        marks_data.append([
            Paragraph(str(i), td_c),
            Paragraph(s['name'], td_l),
            Paragraph(str(s['max']), td_c),
            score_para(s['score'], s['max']),
            Paragraph(str(s['attendance']), td_c),
            Paragraph(str(s['remark']), td_c),
        ])

    pct   = round(student['total'] / student['max_total'] * 100, 1) if student['max_total'] else 0
    tot_s = ps('tot', fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=navy)
    gtl_s = ps('gtl', fontSize=10, alignment=TA_RIGHT,  fontName='Helvetica-Bold', textColor=navy)
    marks_data.append([
        Paragraph('',tot_s),
        Paragraph('GRAND TOTAL', gtl_s),
        Paragraph(str(student['max_total']), tot_s),
        Paragraph(str(student['total']), tot_s),
        Paragraph(f'{pct}%', pct_s),
        Paragraph('', tot_s),
    ])

    cw = [20, doc.width - 20 - 65 - 80 - 65 - 75, 65, 80, 65, 75]
    marks_tbl = Table(marks_data, colWidths=cw, repeatRows=1)
    marks_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),navy),
        ('ROWBACKGROUNDS',(0,1),(-1,-2),[colors.white, light]),
        ('BACKGROUND',(0,-1),(-1,-1),cream),
        ('LINEABOVE',(0,-1),(-1,-1),1.5,navy),
        ('BOX',(0,0),(-1,-1),1.2,navy),
        ('INNERGRID',(0,0),(-1,-1),0.5,colors.HexColor('#cccccc')),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LEFTPADDING',(0,1),(1,-1),8),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]))
    story += [marks_tbl, Spacer(1,10)]

    note_tbl = Table([[Paragraph(
        '★  This is a computer-generated internal assessment report. Results are subject to approval by the examination committee.', note_s
    )]], colWidths=[doc.width])
    note_tbl.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.7,colors.HexColor('#aaaaaa')),
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#fffde7')),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    story += [note_tbl, Spacer(1,24)]

    sig_tbl = Table([
        [Paragraph('___________________________',sig_s)]*3,
        [Paragraph(x,sig_s) for x in ['Class Teacher','Head of Department','Principal']],
        [Paragraph(x,note_s) for x in ['Signature &amp; Date','Dept. of AI &amp; DS','Shridevi Inst. of Engg. &amp; Tech.']],
    ], colWidths=[doc.width/3]*3)
    sig_tbl.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
    ]))
    story += [sig_tbl, Spacer(1,14),
              HRFlowable(width='100%', thickness=1.5, color=navy), Spacer(1,4),
              Paragraph('Shridevi Institute of Engineering and Technology, Tumakuru  |  Approved by AICTE  |  Affiliated to VTU, Belagavi', foot_s)]

    doc.build(story, onFirstPage=draw_border, onLaterPages=draw_border)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f"Report_{student['usn']}.pdf",
                     mimetype='application/pdf')

# ─────────────────────────────────────────
#  Admin — Students
# ─────────────────────────────────────────

@app.route('/admin/students')
@admin_required
def all_students():
    conn = get_db()
    students = conn.execute("SELECT usn, name, semester, year FROM students ORDER BY usn").fetchall()
    conn.close()
    return render_template('all_students.html', students=students)

@app.route('/admin/add_student', methods=['GET','POST'])
@admin_required
def add_student():
    conn = get_db()
    subjects = conn.execute("SELECT * FROM subjects ORDER BY display_order, id").fetchall()

    if request.method == 'POST':
        usn  = request.form.get('usn','').strip().upper()
        name = request.form.get('name','').strip()
        sem  = request.form.get('semester','3').strip()
        year = request.form.get('year','2024-25').strip()

        try:
            conn.execute("INSERT INTO students (usn,name,semester,year) VALUES (?,?,?,?)",
                         (usn, name, sem, year))
            conn.commit()
            _save_marks(conn, usn, subjects, request.form)
            conn.commit()
            flash(f'Student {usn} added successfully!', 'success')
            conn.close()
            return redirect(url_for('all_students'))
        except sqlite3.IntegrityError:
            flash(f'USN {usn} already exists. Use Edit to update.', 'danger')
            conn.close()
            return render_template('add_student.html', student=None, subjects=subjects)

    conn.close()
    return render_template('add_student.html', student=None, subjects=subjects, existing_marks={})

@app.route('/admin/edit_student/<usn>', methods=['GET','POST'])
@admin_required
def edit_student(usn):
    conn = get_db()
    row = conn.execute("SELECT * FROM students WHERE usn=?", (usn,)).fetchone()
    if not row:
        conn.close()
        flash('Student not found.', 'danger')
        return redirect(url_for('all_students'))

    subjects = conn.execute("SELECT * FROM subjects ORDER BY display_order, id").fetchall()

    if request.method == 'POST':
        name = request.form.get('name','').strip()
        sem  = request.form.get('semester','3').strip()
        year = request.form.get('year','2024-25').strip()
        conn.execute("UPDATE students SET name=?,semester=?,year=? WHERE usn=?",
                     (name, sem, year, usn))
        conn.commit()
        _save_marks(conn, usn, subjects, request.form)
        conn.commit()
        conn.close()
        flash(f'Student {usn} updated successfully!', 'success')
        return redirect(url_for('all_students'))

    marks_rows = conn.execute(
        "SELECT subject_id, score, attendance, remark FROM student_marks WHERE student_usn=?",
        (usn,)
    ).fetchall()
    existing_marks = {m['subject_id']: dict(m) for m in marks_rows}
    conn.close()
    return render_template('add_student.html',
                           student=dict(row),
                           subjects=subjects,
                           existing_marks=existing_marks)

def _save_marks(conn, usn, subjects, form):
    for sub in subjects:
        sid   = sub['id']
        score = float(form.get(f'score_{sid}', 0) or 0)
        att   = form.get(f'att_{sid}', '-').strip() or '-'
        remark= form.get(f'remark_{sid}', '-').strip() or '-'
        conn.execute("""
            INSERT INTO student_marks (student_usn, subject_id, score, attendance, remark)
            VALUES (?,?,?,?,?)
            ON CONFLICT(student_usn, subject_id) DO UPDATE SET
                score=excluded.score,
                attendance=excluded.attendance,
                remark=excluded.remark
        """, (usn, sid, score, att, remark))

# ─────────────────────────────────────────
#  Admin — Subjects
# ─────────────────────────────────────────

@app.route('/admin/subjects')
@admin_required
def manage_subjects():
    conn = get_db()
    subjects = conn.execute("SELECT * FROM subjects ORDER BY display_order, id").fetchall()
    conn.close()
    return render_template('manage_subjects.html', subjects=subjects)

@app.route('/admin/subjects/add', methods=['POST'])
@admin_required
def add_subject():
    name      = request.form.get('name','').strip()
    max_marks = float(request.form.get('max_marks', 15) or 15)
    order     = int(request.form.get('display_order', 0) or 0)
    if not name:
        flash('Subject name is required.', 'danger')
        return redirect(url_for('manage_subjects'))
    conn = get_db()
    conn.execute("INSERT INTO subjects (name,max_marks,display_order) VALUES (?,?,?)",
                 (name, max_marks, order))
    conn.commit()
    conn.close()
    flash(f'Subject "{name}" added!', 'success')
    return redirect(url_for('manage_subjects'))

@app.route('/admin/subjects/edit/<int:sid>', methods=['POST'])
@admin_required
def edit_subject(sid):
    name      = request.form.get('name','').strip()
    max_marks = float(request.form.get('max_marks', 15) or 15)
    order     = int(request.form.get('display_order', 0) or 0)
    if not name:
        flash('Subject name cannot be empty.', 'danger')
        return redirect(url_for('manage_subjects'))
    conn = get_db()
    conn.execute("UPDATE subjects SET name=?,max_marks=?,display_order=? WHERE id=?",
                 (name, max_marks, order, sid))
    conn.commit()
    conn.close()
    flash(f'Subject updated!', 'success')
    return redirect(url_for('manage_subjects'))

@app.route('/admin/subjects/delete/<int:sid>', methods=['POST'])
@admin_required
def delete_subject(sid):
    conn = get_db()
    sub = conn.execute("SELECT name FROM subjects WHERE id=?", (sid,)).fetchone()
    if sub:
        conn.execute("DELETE FROM subjects WHERE id=?", (sid,))
        conn.commit()
        flash(f'Subject "{sub["name"]}" deleted.', 'success')
    conn.close()
    return redirect(url_for('manage_subjects'))

# ─────────────────────────────────────────
#  Admin — Users
# ─────────────────────────────────────────

@app.route('/admin/add_user', methods=['GET','POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        role     = request.form.get('role','student')
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('add_user.html')
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                         (username, generate_password_hash(password), role))
            conn.commit()
            flash(f'User "{username}" created!', 'success')
        except sqlite3.IntegrityError:
            flash(f'Username "{username}" already exists.', 'danger')
        finally:
            conn.close()
        return redirect(url_for('all_students'))
    return render_template('add_user.html')

# ─────────────────────────────────────────
#  Run
# ─────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
