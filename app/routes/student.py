from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from app.services.report_service import ReportService
from app.utils.security import login_required

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
def dashboard():
    usn = session.get('student_usn')
    student = None
    if usn:
        student = ReportService.build_student_report(usn)
        
    return render_template('student/dashboard.html',
                           username=session.get('username'),
                           role=session.get('role'),
                           student=student)

@student_bp.route('/search', methods=['POST'])
@login_required
def search():
    target_usn = request.form.get('usn', '').strip().upper()
    if not target_usn:
        flash('Please enter a valid USN.', 'warning')
        return redirect(url_for('student.dashboard'))

    if session.get('role') == 'student' and session.get('student_usn'):
        if target_usn != session.get('student_usn'):
            flash('Access Restricted: You may only view your own academic report.', 'danger')
            return redirect(url_for('student.dashboard'))

    student = ReportService.build_student_report(target_usn)
    if not student:
        flash(f'No student found with USN: {target_usn}', 'danger')
        return redirect(url_for('student.dashboard'))

    return render_template('student/report.html', student=student)

@student_bp.route('/download_pdf/<usn>')
@login_required
def download_pdf(usn):
    clean_usn = usn.strip().upper()
    
    if session.get('role') == 'student' and session.get('student_usn'):
        if clean_usn != session.get('student_usn'):
            flash('Unauthorized to download PDF for another student.', 'danger')
            return redirect(url_for('student.dashboard'))

    student = ReportService.build_student_report(clean_usn)
    if not student:
        flash('Student record not found.', 'danger')
        return redirect(url_for('student.dashboard'))

    pdf_buffer = ReportService.generate_pdf(student)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Report_{student['usn']}.pdf",
        mimetype='application/pdf'
    )
