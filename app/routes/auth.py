from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from app.models.user import UserModel
from app.utils.security import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
        
    if request.method == 'POST':
        u = request.form.get('username', '').strip()
        p = request.form.get('password', '')
        user = UserModel.get_by_username(u)
        
        if user and check_password_hash(user['password'], p):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['student_usn'] = user['student_usn']
            
            flash(f"Welcome back, {user['username']}!", 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('student.dashboard'))
            
        flash('Invalid username or password.', 'danger')
        
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_p = request.form.get('current_password', '')
    new_p     = request.form.get('new_password', '')
    confirm_p = request.form.get('confirm_password', '')

    if new_p != confirm_p:
        flash('New passwords do not match.', 'danger')
        return redirect(request.referrer or url_for('auth.index'))
    if len(new_p) < 6:
        flash('Password must be at least 6 characters long.', 'danger')
        return redirect(request.referrer or url_for('auth.index'))

    user = UserModel.get_by_id(session['user_id'])
    if not user or not check_password_hash(user['password'], current_p):
        flash('Incorrect current password.', 'danger')
        return redirect(request.referrer or url_for('auth.index'))

    UserModel.update_password(session['user_id'], new_p)
    flash('Password updated successfully!', 'success')
    return redirect(request.referrer or url_for('auth.index'))
