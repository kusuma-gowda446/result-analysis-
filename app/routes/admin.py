from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from app.models.student import StudentModel
from app.models.subject import SubjectModel
from app.models.mark import MarkModel
from app.models.user import UserModel
from app.services.bulk_service import BulkService
from app.services.report_service import ReportService
from app.utils.security import admin_required, validate_usn, validate_score

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_students = StudentModel.count()
    total_subjects = SubjectModel.count()
    total_users    = UserModel.count()
    recent_students = StudentModel.get_recent(5)
    
    return render_template('admin/dashboard.html',
                           total_students=total_students,
                           total_subjects=total_subjects,
                           total_users=total_users,
                           recent_students=recent_students)

@admin_bp.route('/students')
@admin_required
def all_students():
    query = request.args.get('q', '').strip()
    students = StudentModel.get_all(query)
    subjects = SubjectModel.get_all()
    return render_template('admin/students.html', students=students, query=query, subjects=subjects)

@admin_bp.route('/add_student', methods=['GET', 'POST'])
@admin_required
def add_student():
    subjects = SubjectModel.get_all()

    if request.method == 'POST':
        raw_usn = request.form.get('usn', '')
        valid, usn = validate_usn(raw_usn)
        if not valid:
            flash(usn, 'danger')
            return render_template('admin/add_student.html', student=None, subjects=subjects, existing_marks={})

        name  = request.form.get('name', '').strip()
        dob   = request.form.get('dob', '').strip()
        dept  = request.form.get('department', 'AI & Data Science').strip()
        sem   = request.form.get('semester', '3').strip()
        sec   = request.form.get('section', 'A').strip().upper()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        addr  = request.form.get('address', '').strip()

        if not name:
            flash('Student Name is required.', 'danger')
            return render_template('admin/add_student.html', student=None, subjects=subjects, existing_marks={})

        StudentModel.save_student(
            usn=usn,
            name=name,
            dob=dob,
            department=dept,
            semester=sem,
            section=sec,
            phone=phone,
            email=email,
            address=addr
        )
        _save_marks(usn, sem, subjects, request.form)
        
        if request.form.get('create_user_account'):
            if not UserModel.get_by_username(usn):
                UserModel.create(username=usn, password=usn, role='student', student_usn=usn)

        flash(f'Student {usn} ({name}) added successfully!', 'success')
        return redirect(url_for('admin.all_students'))

    return render_template('admin/add_student.html', student=None, subjects=subjects, existing_marks={})

@admin_bp.route('/edit_student/<usn>', methods=['GET', 'POST'])
@admin_required
def edit_student(usn):
    row = StudentModel.get_by_usn(usn)
    if not row:
        flash('Student record not found.', 'danger')
        return redirect(url_for('admin.all_students'))

    subjects = SubjectModel.get_all()

    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        dob   = request.form.get('dob', '').strip()
        dept  = request.form.get('department', 'AI & Data Science').strip()
        sem   = request.form.get('semester', '3').strip()
        sec   = request.form.get('section', 'A').strip().upper()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        addr  = request.form.get('address', '').strip()

        if not name:
            flash('Student Name cannot be empty.', 'danger')
            return redirect(url_for('admin.edit_student', usn=usn))

        StudentModel.save_student(
            usn=usn,
            name=name,
            dob=dob,
            department=dept,
            semester=sem,
            section=sec,
            phone=phone,
            email=email,
            address=addr
        )
        _save_marks(usn, sem, subjects, request.form)
        
        flash(f'Student {usn} updated successfully!', 'success')
        return redirect(url_for('admin.all_students'))

    marks_rows = StudentModel.get_marks(usn)
    existing_marks = {m['subject_id']: dict(m) for m in marks_rows}
    
    return render_template('admin/add_student.html',
                           student=dict(row),
                           subjects=subjects,
                           existing_marks=existing_marks)

@admin_bp.route('/delete_student/<usn>', methods=['POST'])
@admin_required
def delete_student(usn):
    StudentModel.delete(usn)
    flash(f'Student {usn} deleted successfully.', 'info')
    return redirect(url_for('admin.all_students'))

# ── Marks Management (Admin Only CRUD) ──

@admin_bp.route('/marks')
@admin_required
def manage_marks_overview():
    query = request.args.get('q', '').strip()
    students_raw = StudentModel.get_all(query)
    students_list = []
    
    for s in students_raw:
        rpt = ReportService.build_student_report(s['usn'])
        if rpt:
            students_list.append(rpt)
            
    return render_template('admin/marks_overview.html', students=students_list, query=query)

@admin_bp.route('/marks/<usn>')
@admin_required
def manage_student_marks(usn):
    report = ReportService.build_student_report(usn)
    if not report:
        flash('Student record not found.', 'danger')
        return redirect(url_for('admin.manage_marks_overview'))
        
    subjects = SubjectModel.get_all()
    return render_template('admin/manage_student_marks.html', student=report, subjects=subjects)

@admin_bp.route('/marks/add', methods=['POST'])
@admin_required
def add_marks():
    usn = request.form.get('usn', '').strip().upper()
    semester = request.form.get('semester', '3').strip()
    subject_id = int(request.form.get('subject_id', 0))
    internal_marks = float(request.form.get('internal_marks', 0))
    external_marks = float(request.form.get('external_marks', 0))
    attendance = request.form.get('attendance', '90%').strip()
    remark = request.form.get('remark', 'Good').strip()

    subject = SubjectModel.get_by_id(subject_id)
    if not subject:
        flash('Invalid subject selected.', 'danger')
        return redirect(url_for('admin.manage_student_marks', usn=usn))

    MarkModel.save_mark(
        usn=usn,
        semester=semester,
        subject_id=subject_id,
        subject_name=subject['name'],
        internal_marks=internal_marks,
        external_marks=external_marks,
        max_marks=subject['max_marks'],
        attendance=attendance,
        remark=remark
    )
    flash(f"Marks added successfully for subject '{subject['name']}'!", 'success')
    return redirect(url_for('admin.manage_student_marks', usn=usn))

@admin_bp.route('/marks/update', methods=['POST'])
@admin_required
def update_marks():
    return add_marks()

@admin_bp.route('/marks/delete/<usn>/<int:subject_id>', methods=['POST'])
@admin_required
def delete_marks(usn, subject_id):
    MarkModel.delete_mark(usn, subject_id)
    flash(f"Marks entry deleted for subject ID {subject_id}.", 'info')
    return redirect(url_for('admin.manage_student_marks', usn=usn))

def _save_marks(usn, semester, subjects, form):
    for sub in subjects:
        sid = sub['id']
        max_m = sub['max_marks']
        
        raw_internal = form.get(f'internal_{sid}', form.get(f'score_{sid}', 0))
        raw_external = form.get(f'external_{sid}', 0)
        
        try:
            internal = float(raw_internal)
        except (ValueError, TypeError):
            internal = 0.0
            
        try:
            external = float(raw_external)
        except (ValueError, TypeError):
            external = 0.0

        att    = form.get(f'att_{sid}', '-').strip() or '-'
        remark = form.get(f'remark_{sid}', '-').strip() or '-'
        
        MarkModel.save_mark(
            usn=usn,
            semester=semester,
            subject_id=sid,
            subject_name=sub['name'],
            internal_marks=internal,
            external_marks=external,
            max_marks=max_m,
            attendance=att,
            remark=remark
        )

# ── Subjects ──

@admin_bp.route('/subjects')
@admin_required
def manage_subjects():
    subjects = SubjectModel.get_all()
    return render_template('admin/subjects.html', subjects=subjects)

@admin_bp.route('/subjects/add', methods=['POST'])
@admin_required
def add_subject():
    name      = request.form.get('name', '').strip()
    max_marks = float(request.form.get('max_marks', 15) or 15)
    order     = int(request.form.get('display_order', 0) or 0)
    
    if not name:
        flash('Subject name is required.', 'danger')
        return redirect(url_for('admin.manage_subjects'))
        
    SubjectModel.create(name, max_marks, order)
    flash(f'Subject "{name}" added successfully!', 'success')
    return redirect(url_for('admin.manage_subjects'))

@admin_bp.route('/subjects/edit/<int:sid>', methods=['POST'])
@admin_required
def edit_subject(sid):
    name      = request.form.get('name', '').strip()
    max_marks = float(request.form.get('max_marks', 15) or 15)
    order     = int(request.form.get('display_order', 0) or 0)
    
    if not name:
        flash('Subject name cannot be empty.', 'danger')
        return redirect(url_for('admin.manage_subjects'))
        
    SubjectModel.update(sid, name, max_marks, order)
    flash('Subject updated successfully!', 'success')
    return redirect(url_for('admin.manage_subjects'))

@admin_bp.route('/subjects/delete/<int:sid>', methods=['POST'])
@admin_required
def delete_subject(sid):
    sub = SubjectModel.delete(sid)
    if sub:
        flash(f'Subject "{sub["name"]}" deleted.', 'info')
    return redirect(url_for('admin.manage_subjects'))

# ── User Accounts ──

@admin_bp.route('/users', methods=['GET', 'POST'])
@admin_required
def users():
    if request.method == 'POST':
        username    = request.form.get('username', '').strip()
        password    = request.form.get('password', '')
        role        = request.form.get('role', 'student')
        student_usn = request.form.get('student_usn', '').strip().upper() or None

        if not username or not password:
            flash('Username and password are required.', 'danger')
        else:
            UserModel.create(username, password, role, student_usn)
            flash(f'User "{username}" created successfully!', 'success')

    all_users = UserModel.get_all_with_student_info()
    all_students = StudentModel.get_all()
    return render_template('admin/users.html', users=all_users, students=all_students)

@admin_bp.route('/users/delete/<int:uid>', methods=['POST'])
@admin_required
def delete_user(uid):
    if uid == session.get('user_id'):
        flash('You cannot delete your own logged-in account!', 'danger')
        return redirect(url_for('admin.users'))
    UserModel.delete(uid)
    flash('User deleted.', 'info')
    return redirect(url_for('admin.users'))

# ── Bulk Excel/CSV Upload ──

@admin_bp.route('/bulk_upload', methods=['GET', 'POST'])
@admin_required
def bulk_upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Please select a file to upload.', 'warning')
            return redirect(url_for('admin.bulk_upload'))

        success, count, msg = BulkService.process_upload(file.stream, file.filename)
        if success:
            flash(f'Successfully imported/updated {count} student records!', 'success')
            return redirect(url_for('admin.all_students'))
        else:
            flash(msg or 'Failed to process file.', 'danger')
            return redirect(url_for('admin.bulk_upload'))

    return render_template('admin/bulk_upload.html')

@admin_bp.route('/download_template')
@admin_required
def download_template():
    csv_stream = BulkService.get_csv_template()
    return send_file(
        csv_stream,
        mimetype='text/csv',
        as_attachment=True,
        download_name='student_marks_template.csv'
    )
