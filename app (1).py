from flask import Flask, render_template, request, send_file
import pandas as pd
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

app = Flask(__name__)

# Global storage for the current session's student data
current_report_data = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/view_report', methods=['POST'])
def view_report():
    global current_report_data
    usn_input = request.form.get('usn', '').strip().upper()
    file = request.files.get('csv_file')
    
    if not file: return "CSV missing", 400

    try:
        df = pd.read_csv(file, header=None)
        df[0] = df[0].astype(str).str.strip().str.upper()
        student_row = df[df[0] == usn_input]

        if student_row.empty: return "Student not found", 404

        row = student_row.iloc[0]
        subjects_config = [
            ("Mathematics-III", 2, 3, 5),
            ("Digital Design", 6, 7, 9),
            ("Operating System", 10, 11, 13),
            ("Data Structures", 14, 15, 17),
            ("Python for DS", 18, 19, 21)
        ]

        processed_subjects = []
        grand_total = 0

        for name, s_idx, a_idx, r_idx in subjects_config:
            score = float(row[s_idx]) if pd.notna(row[s_idx]) else 0.0
            grand_total += score
            processed_subjects.append({
                "name": name, "score": score, 
                "attendance": row[a_idx], "remark": row[r_idx], "max": 15
            })

        current_report_data = {
            "name": row[1], "usn": row[0],
            "subjects": processed_subjects,
            "total": grand_total
        }

        return render_template('report.html', student=current_report_data)
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/download_pdf')
def download_pdf():
    global current_report_data
    if not current_report_data:
        return "No report data found. Please search first.", 400

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # PDF Header
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.midnightblue)
    c.drawString(100, 750, "Shridevi Institute of Engineering and Technology")
    
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(100, 735, f"Name: {current_report_data['name']}")
    c.drawString(100, 720, f"USN: {current_report_data['usn']}")
    c.drawString(400, 720, "Semester: 3 | Year: 2024-25")

    # Table Data
    data = [["Subject", "Score", "Attendance", "Remark"]]
    for s in current_report_data['subjects']:
        data.append([s['name'], s['score'], s['attendance'], s['remark']])
    data.append(["GRAND TOTAL", current_report_data['total'], "", ""])

    # Table Styling
    table = Table(data, colWidths=[200, 80, 80, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.midnightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    table.wrapOn(c, 50, 400)
    table.drawOn(c, 50, 500)
    
    c.showPage()
    c.save()
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, 
                     download_name=f"Report_{current_report_data['usn']}.pdf",
                     mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)