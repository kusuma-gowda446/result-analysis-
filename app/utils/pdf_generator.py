import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def generate_pdf_report(student):
    """Generates an official, print-ready PDF Marks Card for a student."""
    buffer = io.BytesIO()
    navy  = colors.HexColor('#0e2245')
    gold  = colors.HexColor('#d97706')
    cream = colors.HexColor('#f8fafc')
    light = colors.HexColor('#f1f5f9')
    dark_gray = colors.HexColor('#1e293b')

    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=14*mm, rightMargin=14*mm,
        topMargin=12*mm, bottomMargin=12*mm
    )
    styles = getSampleStyleSheet()
    story  = []
    W, H   = letter

    def draw_official_border(cv, d):
        cv.saveState()
        # Outer thick border
        cv.setStrokeColor(navy)
        cv.setLineWidth(2.5)
        cv.rect(8*mm, 8*mm, W-16*mm, H-16*mm)
        # Inner fine gold border
        cv.setStrokeColor(gold)
        cv.setLineWidth(0.75)
        cv.rect(10.5*mm, 10.5*mm, W-21*mm, H-21*mm)
        cv.restoreState()

    def ps(name, **kw):
        return ParagraphStyle(name, parent=styles[kw.pop('parent', 'Normal')], **kw)

    affil_s = ps('affil', fontSize=8, textColor=colors.HexColor('#475569'), alignment=TA_CENTER, fontName='Helvetica-Bold')
    title_s = ps('title', fontSize=15, textColor=navy, alignment=TA_CENTER, fontName='Helvetica-Bold', leading=18)
    addr_s  = ps('addr',  fontSize=8, textColor=colors.HexColor('#334155'), alignment=TA_CENTER, leading=11)
    dept_s  = ps('dept',  fontSize=10, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold')
    rpt_s   = ps('rpt',   fontSize=12, textColor=navy, alignment=TA_CENTER, fontName='Helvetica-Bold')
    sub_s   = ps('sub',   fontSize=8.5, textColor=colors.HexColor('#475569'), alignment=TA_CENTER, fontName='Helvetica-Oblique')
    lbl_s   = ps('lbl',   fontSize=8.5, textColor=navy, fontName='Helvetica-Bold')
    val_s   = ps('val',   fontSize=9, textColor=dark_gray, fontName='Helvetica')
    note_s  = ps('note',  fontSize=7.5, textColor=colors.HexColor('#64748b'), alignment=TA_CENTER, fontName='Helvetica-Oblique')
    sig_s   = ps('sig',   fontSize=8.5, textColor=navy, alignment=TA_CENTER, fontName='Helvetica-Bold')
    foot_s  = ps('foot',  fontSize=7.5, textColor=colors.HexColor('#64748b'), alignment=TA_CENTER)

    # 1. Header with Logo & College Info
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'logo.png')
    logo_img = None
    if os.path.exists(logo_path):
        try:
            logo_img = Image(logo_path, width=28*mm, height=28*mm)
        except Exception:
            logo_img = None

    header_text_nodes = [
        Paragraph('AFFILIATED TO VTU, BELAGAVI | APPROVED BY AICTE, NEW DELHI | RECOGNIZED BY GOVT. OF KARNATAKA', affil_s),
        Spacer(1, 2),
        Paragraph('SHRIDEVI INSTITUTE OF ENGINEERING AND TECHNOLOGY', title_s),
        Paragraph('Sira Road, Tumakuru – 572 106, Karnataka, India', addr_s),
        Paragraph('Phone: 0816-2258000 | Email: principal@shrideviiet.ac.in | Web: www.shrideviiet.ac.in', addr_s),
    ]

    if logo_img:
        header_table = Table([[logo_img, header_text_nodes]], colWidths=[32*mm, doc.width - 32*mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (0,0), 'CENTER'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(header_table)
    else:
        for node in header_text_nodes:
            story.append(node)

    story += [
        Spacer(1, 6),
        HRFlowable(width='100%', thickness=1.5, color=navy),
        Spacer(1, 4),
    ]

    # Department Banner
    dept_name = student.get('department', 'DEPARTMENT OF ARTIFICIAL INTELLIGENCE & DATA SCIENCE').upper()
    if not dept_name.startswith('DEPARTMENT OF'):
        dept_name = f"DEPARTMENT OF {dept_name}"

    dept_tbl = Table([[Paragraph(dept_name, dept_s)]], colWidths=[doc.width])
    dept_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), navy),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story += [
        dept_tbl, Spacer(1, 6),
        Paragraph('OFFICIAL STATEMENT OF MARKS (MARKS CARD)', rpt_s), Spacer(1, 2),
        Paragraph(f"Academic Year: {student.get('year', '2024-25')}  |  Semester: Sem {student.get('semester', '3')} (Sec {student.get('section', 'A')})", sub_s),
        Spacer(1, 6), HRFlowable(width='100%', thickness=0.75, color=gold), Spacer(1, 6)
    ]

    # 2. Student Details Table (USN, Name, DOB, Dept, Sem, Sec, Phone, Email)
    half = doc.width / 2
    det = Table([
        [Paragraph('Student Name', lbl_s), Paragraph(student.get('name', '-'), val_s),
         Paragraph('USN', lbl_s),          Paragraph(student.get('usn', '-'), val_s)],
        [Paragraph('Date of Birth', lbl_s),Paragraph(student.get('dob', '-'), val_s),
         Paragraph('Department', lbl_s),   Paragraph(student.get('department', 'AI & DS'), val_s)],
        [Paragraph('Semester & Sec', lbl_s),Paragraph(f"Sem {student.get('semester', '3')} - Sec {student.get('section', 'A')}", val_s),
         Paragraph('Academic Year', lbl_s),Paragraph(student.get('year', '2024-25'), val_s)],
        [Paragraph('Phone Number', lbl_s), Paragraph(student.get('phone', '-'), val_s),
         Paragraph('Email Address', lbl_s),Paragraph(student.get('email', '-'), val_s)],
    ], colWidths=[half*0.32, half*0.68, half*0.32, half*0.68])
    det.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), cream), ('BACKGROUND', (2,0), (2,-1), cream),
        ('BOX', (0,0), (-1,-1), 1, navy), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story += [det, Spacer(1, 8)]

    # 3. Subject-wise Marks Table
    hdr_s = ps('thdr', fontSize=8.5, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold')
    td_c  = ps('tdc',  fontSize=9, alignment=TA_CENTER)
    td_l  = ps('tdl',  fontSize=9, alignment=TA_LEFT)
    td_g  = ps('tdg',  fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor('#166534'), fontName='Helvetica-Bold')
    td_r  = ps('tdr',  fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor('#991b1b'), fontName='Helvetica-Bold')

    marks_data = [[Paragraph(h, hdr_s) for h in
                   ['Sl.', 'Subject / Course Title', 'Internal', 'External', 'Total', 'Max', 'Result', 'Grade Pt']]]
    
    for i, s in enumerate(student.get('subjects', []), 1):
        res_para = Paragraph(s['result'], td_g if s['result'] == 'PASS' else td_r)
        marks_data.append([
            Paragraph(str(i), td_c),
            Paragraph(s['name'], td_l),
            Paragraph(str(s.get('internal_marks', s.get('score', 0))), td_c),
            Paragraph(str(s.get('external_marks', 0)), td_c),
            Paragraph(str(s.get('total', s.get('score', 0))), td_c),
            Paragraph(str(s.get('max', 100)), td_c),
            res_para,
            Paragraph(str(s.get('grade_point', 0.0)), td_c),
        ])

    cw = [22, doc.width - 22 - 50 - 50 - 50 - 45 - 55 - 50, 50, 50, 50, 45, 55, 50]
    marks_tbl = Table(marks_data, colWidths=cw, repeatRows=1)
    marks_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), navy),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light]),
        ('BOX', (0,0), (-1,-1), 1, navy),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,1), (1,-1), 6), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story += [marks_tbl, Spacer(1, 8)]

    # 4. Academic Performance Summary Table (Total, SGPA, CGPA, Result)
    tot_lbl = ps('tlbl', fontSize=9, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=navy)
    tot_val = ps('tval', fontSize=9, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=dark_gray)
    res_val = ps('rval', fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Bold',
                 textColor=colors.HexColor('#166534') if student.get('result') == 'PASS' else colors.HexColor('#991b1b'))

    summary_data = [
        [Paragraph('Total Internal', tot_lbl), Paragraph('Total External', tot_lbl), Paragraph('Grand Total', tot_lbl),
         Paragraph('Result', tot_lbl), Paragraph('SGPA', tot_lbl), Paragraph('CGPA', tot_lbl)],
        [Paragraph(str(student.get('total_internal', 0.0)), tot_val),
         Paragraph(str(student.get('total_external', 0.0)), tot_val),
         Paragraph(f"{student.get('total', 0.0)} / {student.get('max_total', 0.0)}", tot_val),
         Paragraph(student.get('result', 'PASS'), res_val),
         Paragraph(str(student.get('sgpa', 0.0)), tot_val),
         Paragraph(str(student.get('cgpa', 0.0)), tot_val)]
    ]
    summary_tbl = Table(summary_data, colWidths=[doc.width/6]*6)
    summary_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), cream),
        ('BACKGROUND', (0,1), (-1,1), colors.white),
        ('BOX', (0,0), (-1,-1), 1, navy),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story += [summary_tbl, Spacer(1, 10)]

    # 5. Note / Disclaimer Box
    note_tbl = Table([[Paragraph(
        '★  OFFICIAL MARKS STATEMENT — Computer Generated Academic Transcript. Issued under authority of the Controller of Examinations, Shridevi Institute of Engineering & Technology.', note_s
    )]], colWidths=[doc.width])
    note_tbl.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story += [note_tbl, Spacer(1, 18)]

    # 6. Signatures Section & Official Stamp Box
    sig_tbl = Table([
        [Paragraph('___________________________', sig_s), Paragraph('___________________________', sig_s), Paragraph('___________________________', sig_s)],
        [Paragraph('Class Coordinator', sig_s), Paragraph('Head of Department', sig_s), Paragraph('Principal / Controller', sig_s)],
        [Paragraph('Signature &amp; Date', note_s), Paragraph(f"Dept. of {student.get('department', 'AI & DS')}", note_s), Paragraph('SIET, Tumakuru', note_s)],
    ], colWidths=[doc.width/3]*3)
    sig_tbl.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story += [
        sig_tbl, Spacer(1, 10),
        HRFlowable(width='100%', thickness=1, color=navy), Spacer(1, 3),
        Paragraph('Shridevi Institute of Engineering and Technology, Tumakuru | Approved by AICTE | Affiliated to VTU, Belagavi', foot_s)
    ]

    doc.build(story, onFirstPage=draw_official_border, onLaterPages=draw_official_border)
    buffer.seek(0)
    return buffer
