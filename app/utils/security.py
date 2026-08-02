import re
from functools import wraps
from flask import session, flash, redirect, url_for, request

def login_required(f):
    @wraps(f)
    def deco(*a, **kw):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.student_login', next=request.url))
        return f(*a, **kw)
    return deco

def admin_required(f):
    @wraps(f)
    def deco(*a, **kw):
        if 'user_id' not in session or session.get('role') != 'admin':
            if session.get('role') == 'student':
                flash('Access Denied: Admin privileges required.', 'danger')
                return redirect(url_for('student.dashboard'))
            flash('Please log in as Admin to access this page.', 'warning')
            return redirect(url_for('auth.admin_login', next=request.url))
        return f(*a, **kw)
    return deco

def student_required(f):
    @wraps(f)
    def deco(*a, **kw):
        if 'user_id' not in session or session.get('role') not in ['student', 'admin']:
            flash('Please log in with your USN and name to access your dashboard.', 'warning')
            return redirect(url_for('auth.student_login', next=request.url))
        return f(*a, **kw)
    return deco

def validate_usn(usn):
    """Validate USN format (alphanumeric, 5-15 chars)."""
    if not usn or not isinstance(usn, str):
        return False, "USN cannot be empty."
    clean_usn = usn.strip().upper()
    if not re.match(r'^[A-Z0-9]{5,15}$', clean_usn):
        return False, "Invalid USN format. (Must be 5-15 alphanumeric characters)"
    return True, clean_usn

def validate_score(score, max_marks):
    """Ensure mark score is valid float between 0 and max_marks."""
    try:
        val = float(score)
        if val < 0:
            return False, 0.0, "Score cannot be negative."
        if val > float(max_marks):
            return False, float(max_marks), f"Score cannot exceed maximum marks ({max_marks})."
        return True, val, None
    except (ValueError, TypeError):
        return False, 0.0, "Score must be a valid number."

def validate_email(email):
    """Validate email address format if provided."""
    if not email:
        return True, ""
    clean_email = email.strip()
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', clean_email):
        return False, "Invalid email address format."
    return True, clean_email

def validate_phone(phone):
    """Validate 10-digit phone number if provided."""
    if not phone:
        return True, ""
    clean_phone = phone.strip()
    if not re.match(r'^\+?[0-9]{7,15}$', clean_phone):
        return False, "Invalid phone number format."
    return True, clean_phone

def validate_semester(semester):
    """Ensure semester is an integer between 1 and 8."""
    try:
        sem_num = int(semester)
        if sem_num < 1 or sem_num > 8:
            return False, 3, "Semester must be between 1 and 8."
        return True, str(sem_num), None
    except (ValueError, TypeError):
        return False, 3, "Semester must be a valid number."
