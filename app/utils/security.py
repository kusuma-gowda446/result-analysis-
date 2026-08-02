import re
from functools import wraps
from flask import session, flash, redirect, url_for, request

def login_required(f):
    @wraps(f)
    def deco(*a, **kw):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*a, **kw)
    return deco

def admin_required(f):
    @wraps(f)
    def deco(*a, **kw):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash('Admin privilege required.', 'danger')
            return redirect(url_for('student.dashboard'))
        return f(*a, **kw)
    return deco

def validate_usn(usn):
    """Validate USN format (alphanumeric, 5-12 chars)."""
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
        if val > max_marks:
            return False, max_marks, f"Score cannot exceed maximum marks ({max_marks})."
        return True, val, None
    except (ValueError, TypeError):
        return False, 0.0, "Score must be a valid number."
