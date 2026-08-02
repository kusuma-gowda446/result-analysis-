import os
import pytest
from app import create_app
from app.database import get_db, init_db, build_student_report
from app.models.student import StudentModel
from app.models.mark import MarkModel
from app.utils.security import validate_usn, validate_score

@pytest.fixture
def client():
    os.environ['FLASK_ENV'] = 'testing'
    app = create_app('testing')
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            init_db(app)
            # Add test students
            StudentModel.save_student(
                usn='1SG24AI001',
                name='Rahul Kumar',
                dob='2004-05-15',
                department='Computer Science & Engineering',
                semester='3',
                section='A',
                phone='9876543210',
                email='rahul@example.com',
                address='Bangalore, India'
            )
            StudentModel.save_student(
                usn='1SG24AI002',
                name='Priya Sharma',
                dob='2004-09-10',
                department='Computer Science & Engineering',
                semester='3',
                section='B',
                phone='9123456789',
                email='priya@example.com',
                address='Mysore, India'
            )
        yield client
        with app.app_context():
            db = get_db()
            db.admins.drop()
            db.students.drop()
            db.marks.drop()
            db.subjects.drop()

def test_usn_validator():
    valid, res = validate_usn("1SG24AI001")
    assert valid is True
    assert res == "1SG24AI001"

    valid, err = validate_usn("invalid@usn#")
    assert valid is False

def test_student_dashboard_profile_and_isolation(client):
    # 1. Login as student 1SG24AI001
    login_res = client.post('/student/login', data={'usn': '1SG24AI001', 'password': '1SG24AI001'}, follow_redirects=True)
    assert login_res.status_code == 200
    assert b'Rahul Kumar' in login_res.data
    assert b'1SG24AI001' in login_res.data
    assert b'2004-05-15' in login_res.data
    assert b'Bangalore, India' in login_res.data
    assert b'SGPA' in login_res.data
    assert b'CGPA' in login_res.data
    assert b'Logout' in login_res.data

    # 2. PDF Download for own report
    pdf_res = client.get('/download_pdf/1SG24AI001')
    assert pdf_res.status_code == 200
    assert pdf_res.mimetype == 'application/pdf'

    # 3. Attempt to download ANOTHER student's PDF report -> MUST BE RESTRICTED
    other_pdf = client.get('/download_pdf/1SG24AI002', follow_redirects=True)
    assert b'Access Restricted' in other_pdf.data or b'only download your own' in other_pdf.data

    # 4. Logout
    logout_res = client.get('/logout', follow_redirects=True)
    assert logout_res.status_code == 200

def test_marks_management_crud_operations(client):
    # 1. Admin login
    client.post('/admin/login', data={'username': 'admin', 'password': 'admin123'})

    # 2. ADD MARKS
    add_res = client.post('/admin/marks/add', data={
        'usn': '1SG24AI001',
        'semester': '3',
        'subject_id': 1,
        'internal_marks': '35.0',
        'external_marks': '55.0',
        'attendance': '95%',
        'remark': 'Excellent'
    }, follow_redirects=True)
    assert add_res.status_code == 200

    with client.application.app_context():
        rpt = build_student_report('1SG24AI001')
        assert rpt is not None
        assert rpt['total_internal'] == 35.0
        assert rpt['total_external'] == 55.0
        assert rpt['total'] == 90.0
        assert rpt['result'] == 'PASS'
        assert rpt['sgpa'] > 0.0
        assert rpt['cgpa'] > 0.0

    # 3. DELETE MARKS
    del_res = client.post('/admin/marks/delete/1SG24AI001/1', follow_redirects=True)
    assert del_res.status_code == 200

def test_rbac_marks_protection_for_students(client):
    client.post('/student/login', data={'usn': '1SG24AI001', 'password': '1SG24AI001'})
    add_res = client.post('/admin/marks/add', data={'usn': '1SG24AI001', 'subject_id': 1, 'internal_marks': 50, 'external_marks': 50}, follow_redirects=True)
    assert b'Access Denied' in add_res.data or b'Admin privileges required' in add_res.data
