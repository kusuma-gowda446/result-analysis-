import os
import pytest
from app import create_app
from app.database import get_db, init_db, build_student_report
from app.utils.security import validate_usn, validate_score

@pytest.fixture
def client():
    os.environ['FLASK_ENV'] = 'testing'
    app = create_app('testing')
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            init_db(app)
        yield client

def test_usn_validator():
    valid, res = validate_usn("1SG24AI001")
    assert valid is True
    assert res == "1SG24AI001"

    valid, err = validate_usn("invalid@usn#")
    assert valid is False

def test_score_validator():
    valid, val, err = validate_score("12.5", 15)
    assert valid is True
    assert val == 12.5

    valid, val, err = validate_score("-5", 15)
    assert valid is False
    assert err == "Score cannot be negative."

    valid, val, err = validate_score("20", 15)
    assert valid is False
    assert "cannot exceed maximum marks" in err

def test_login_success_and_logout(client):
    res = client.post('/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Admin Overview' in res.data or b'Faculty' in res.data

    logout_res = client.get('/logout', follow_redirects=True)
    assert logout_res.status_code == 200
    assert b'Sign In' in logout_res.data

def test_login_failure(client):
    res = client.post('/login', data={
        'username': 'admin',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert b'Invalid username or password' in res.data

def test_admin_route_protection_for_guest(client):
    res = client.get('/admin/students', follow_redirects=True)
    assert b'Please log in to access this page' in res.data or b'Sign In' in res.data

def test_add_student_and_build_report(client):
    # Log in as admin
    client.post('/login', data={'username': 'admin', 'password': 'admin123'})
    
    # Add a student
    add_res = client.post('/admin/add_student', data={
        'usn': '1SG24AI999',
        'name': 'Test Student',
        'semester': '3',
        'year': '2024-25',
        'department': 'AI & Data Science',
        'score_1': '12.0',
        'att_1': '95%',
        'remark_1': 'Excellent'
    }, follow_redirects=True)
    assert add_res.status_code == 200

    # Verify report in database helper
    with client.application.app_context():
        rpt = build_student_report('1SG24AI999')
        assert rpt is not None
        assert rpt['name'] == 'Test Student'
        assert rpt['total'] == 12.0

def test_pdf_download_route(client):
    client.post('/login', data={'username': 'admin', 'password': 'admin123'})
    client.post('/admin/add_student', data={
        'usn': '1SG24AI888',
        'name': 'PDF Test Student',
        'semester': '3',
        'year': '2024-25',
        'department': 'AI & Data Science'
    })

    pdf_res = client.get('/download_pdf/1SG24AI888')
    assert pdf_res.status_code == 200
    assert pdf_res.mimetype == 'application/pdf'
