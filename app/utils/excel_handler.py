import io
import pandas as pd
from app.models.subject import SubjectModel
from app.models.student import StudentModel

def generate_csv_template():
    """Generate sample CSV template file for bulk student management upload."""
    subjects = SubjectModel.get_all()
    
    headers = ['USN', 'Name', 'DOB', 'Department', 'Semester', 'Section', 'Phone', 'Email', 'Address']
    for sub in subjects:
        headers.extend([f"{sub['name']}_Score", f"{sub['name']}_Attendance", f"{sub['name']}_Remark"])

    sample_row = ['1SG24AI001', 'Rahul Kumar', '2004-05-15', 'AI & Data Science', '3', 'A', '9876543210', 'rahul@example.com', 'Bangalore, India']
    for _ in subjects:
        sample_row.extend(['12.5', '90%', 'Good'])

    df = pd.DataFrame([sample_row], columns=headers)
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return output

def process_bulk_upload(file_stream, file_filename):
    """Process uploaded CSV or Excel file and import students & marks into MongoDB."""
    subjects = SubjectModel.get_all()
    
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

        dob = str(row.get('DOB', '')).strip()
        dept = str(row.get('Department', 'AI & Data Science')).strip()
        sem = str(row.get('Semester', '3')).strip()
        sec = str(row.get('Section', 'A')).strip().upper()
        phone = str(row.get('Phone', '')).strip()
        email = str(row.get('Email', '')).strip()
        addr = str(row.get('Address', '')).strip()

        # Save student document with all 9 fields in 'students' collection
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

        # Save marks documents in 'marks' collection
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

            StudentModel.save_mark(usn, sid, score, att, rem)

        imported_count += 1

    return True, imported_count, None
