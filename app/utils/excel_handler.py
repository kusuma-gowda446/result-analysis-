import io
import pandas as pd
from app.database import get_db

def generate_csv_template():
    """Generate sample CSV template file for bulk student marks upload."""
    conn = get_db()
    subjects = conn.execute("SELECT id, name FROM subjects ORDER BY display_order, id").fetchall()
    
    headers = ['USN', 'Name', 'Semester', 'Year', 'Department', 'Email']
    for sub in subjects:
        headers.extend([f"{sub['name']}_Score", f"{sub['name']}_Attendance", f"{sub['name']}_Remark"])

    sample_row = ['1SG24AI001', 'Rahul Kumar', '3', '2024-25', 'AI & Data Science', 'rahul@example.com']
    for _ in subjects:
        sample_row.extend(['12.5', '90%', 'Good'])

    df = pd.DataFrame([sample_row], columns=headers)
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return output

def process_bulk_upload(file_stream, file_filename):
    """Process uploaded CSV or Excel file and import students & marks."""
    conn = get_db()
    subjects = conn.execute("SELECT id, name FROM subjects ORDER BY display_order, id").fetchall()
    
    try:
        if file_filename.endswith('.csv'):
            df = pd.read_csv(file_stream)
        elif file_filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_stream)
        else:
            return False, 0, "Invalid file format. Please upload a .csv or .xlsx file."
    except Exception as e:
        return False, 0, f"Error parsing spreadsheet: {str(e)}"

    df.columns = [str(col).strip() for col in df.columns]
    
    if 'USN' not in df.columns or 'Name' not in df.columns:
        return False, 0, "Spreadsheet missing required 'USN' or 'Name' columns."

    imported_count = 0
    for _, row in df.iterrows():
        usn = str(row.get('USN', '')).strip().upper()
        name = str(row.get('Name', '')).strip()
        if not usn or not name or usn == 'NAN' or name == 'NAN':
            continue

        sem = str(row.get('Semester', '3')).strip()
        year = str(row.get('Year', '2024-25')).strip()
        dept = str(row.get('Department', 'AI & Data Science')).strip()
        email = str(row.get('Email', '-')).strip()

        # Insert or update student
        conn.execute("""
            INSERT INTO students (usn, name, semester, year, department, email)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(usn) DO UPDATE SET
                name=excluded.name,
                semester=excluded.semester,
                year=excluded.year,
                department=excluded.department,
                email=excluded.email
        """, (usn, name, sem, year, dept, email))

        # Insert or update marks for subjects
        for sub in subjects:
            sid = sub['id']
            s_name = sub['name']
            
            score_col = f"{s_name}_Score"
            att_col   = f"{s_name}_Attendance"
            rem_col   = f"{s_name}_Remark"

            raw_score = row.get(score_col, 0) if score_col in df.columns else 0
            try:
                score = float(raw_score) if pd.notna(raw_score) else 0.0
            except (ValueError, TypeError):
                score = 0.0

            att = str(row.get(att_col, '-')).strip() if att_col in df.columns else '-'
            rem = str(row.get(rem_col, '-')).strip() if rem_col in df.columns else '-'

            conn.execute("""
                INSERT INTO student_marks (student_usn, subject_id, score, attendance, remark)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(student_usn, subject_id) DO UPDATE SET
                    score=excluded.score,
                    attendance=excluded.attendance,
                    remark=excluded.remark
            """, (usn, sid, score, att, rem))

        imported_count += 1

    conn.commit()
    return True, imported_count, None
