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
            # Add initial test student
            StudentModel.save_student(
                usn='1SG24AI001',
                name='Rahul Kumar',
                dob='2004-05-15',
                department='AI & Data Science',
                semester='3',
                section='A',
                phone='9876543210',
                email='rahul@example.com',
                address='Bangalore, India'
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

def test_marks_management_crud_operations(client):
    # 1. Admin login
    client.post('/admin/login', data={'username': 'admin', 'password': 'admin123'})

    # 2. ADD MARKS (Internal = 35, External = 55 -> Total = 90, Result = PASS, Grade Point = 10.0)
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

    # Verify calculation in MongoDB and ReportService
    with client.application.app_context():
        rpt = build_student_report('1SG24AI001')
        assert rpt is not None
        assert rpt['total_internal'] == 35.0
        assert rpt['total_external'] == 55.0
        assert rpt['total'] == 90.0
        assert rpt['result'] == 'PASS'
        assert rpt['sgpa'] > 0.0
        assert rpt['cgpa'] > 0.0

    # 3. UPDATE MARKS
    update_res = client.post('/admin/marks/update', data={
        'usn': '1SG24AI001',
        'semester': '3',
        'subject_id': 1,
        'internal_marks': '40.0',
        'external_marks': '58.0',
        'attendance': '98%',
        'remark': 'Outstanding'
    }, follow_redirects=True)
    assert update_res.status_code == 200

    with client.application.app_context():
        rpt_updated = build_student_report('1SG24AI001')
        assert rpt_updated['total_internal'] == 40.0
        assert rpt_updated['total_external'] == 58.0
        assert rpt_updated['total'] == 98.0

    # 4. DELETE MARKS
    del_res = client.post('/admin/marks/delete/1SG24AI001/1', follow_redirects=True)
    assert del_res.status_code == 200

    with client.application.app_context():
        marks_left = MarkModel.get_by_student('1SG24AI001')
        assert len(marks_left) == 0

def test_rbac_marks_protection_for_students(client):
    # Student login
    client.post('/student/login', data={'usn': '1SG24AI001', 'password': '1SG24AI001'})

    # Attempting to add, update, or delete marks as student -> MUST BE BLOCKED
    add_res = client.post('/admin/marks/add', data={'usn': '1SG24AI001', 'subject_id': 1, 'internal_marks': 50, 'external_marks': 50}, follow_redirects=True)
    assert b'Access Denied' in add_res.data or b'Admin privileges required' in add_res.data

    del_res = client.post('/admin/marks/delete/1SG24AI001/1', follow_redirects=True)
    assert b'Access Denied' in del_res.data or b'Admin privileges required' in del_res.data
