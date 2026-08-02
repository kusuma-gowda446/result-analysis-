import os
import pytest
from app import create_app
from app.database import get_db, init_db, build_student_report
from app.models.student import StudentModel
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

def test_student_crud_operations(client):
    # 1. Admin login
    client.post('/admin/login', data={'username': 'admin', 'password': 'admin123'})

    # 2. CREATE student with all 9 fields
    add_res = client.post('/admin/add_student', data={
        'usn': '1SG24AI005',
        'name': 'Anita Roy',
        'dob': '2004-08-20',
        'department': 'AI & Data Science',
        'semester': '3',
        'section': 'B',
        'phone': '9123456789',
        'email': 'anita@example.com',
        'address': 'Tumkur, Karnataka',
        'score_1': '14.0',
        'att_1': '95%',
        'remark_1': 'Excellent'
    }, follow_redirects=True)
    assert add_res.status_code == 200

    # Verify student record created in MongoDB with all 9 fields
    with client.application.app_context():
        st = StudentModel.get_by_usn('1SG24AI005')
        assert st is not None
        assert st['name'] == 'Anita Roy'
        assert st['dob'] == '2004-08-20'
        assert st['department'] == 'AI & Data Science'
        assert st['semester'] == '3'
        assert st['section'] == 'B'
        assert st['phone'] == '9123456789'
        assert st['email'] == 'anita@example.com'
        assert st['address'] == 'Tumkur, Karnataka'

    # 3. READ student list
    list_res = client.get('/admin/students')
    assert b'Anita Roy' in list_res.data
    assert b'1SG24AI005' in list_res.data

    # 4. UPDATE student
    edit_res = client.post('/admin/edit_student/1SG24AI005', data={
        'name': 'Anita Roy Updated',
        'dob': '2004-08-20',
        'department': 'AI & Data Science',
        'semester': '4',
        'section': 'A',
        'phone': '9999988888',
        'email': 'anita.updated@example.com',
        'address': 'Bangalore, Karnataka'
    }, follow_redirects=True)
    assert edit_res.status_code == 200

    with client.application.app_context():
        st_updated = StudentModel.get_by_usn('1SG24AI005')
        assert st_updated['name'] == 'Anita Roy Updated'
        assert st_updated['semester'] == '4'
        assert st_updated['section'] == 'A'

    # 5. DELETE student
    del_res = client.post('/admin/delete_student/1SG24AI005', follow_redirects=True)
    assert del_res.status_code == 200

    with client.application.app_context():
        st_deleted = StudentModel.get_by_usn('1SG24AI005')
        assert st_deleted is None

def test_rbac_student_management_protection(client):
    # Non-admin / student attempting to create student -> MUST BE BLOCKED
    client.post('/student/login', data={'usn': '1SG24AI001', 'password': '1SG24AI001'})

    add_res = client.post('/admin/add_student', data={'usn': 'HACK001', 'name': 'Hacker'}, follow_redirects=True)
    assert b'Access Denied' in add_res.data or b'Admin privileges required' in add_res.data

    edit_res = client.post('/admin/edit_student/1SG24AI001', data={'name': 'Hacked'}, follow_redirects=True)
    assert b'Access Denied' in edit_res.data or b'Admin privileges required' in edit_res.data

    del_res = client.post('/admin/delete_student/1SG24AI001', follow_redirects=True)
    assert b'Access Denied' in del_res.data or b'Admin privileges required' in del_res.data
