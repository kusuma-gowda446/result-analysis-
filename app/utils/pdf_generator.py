import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def generate_pdf_report(student):
    """Generates a professional PDF byte stream for a student report dict."""
    buffer = io.BytesIO()
    navy  = colors.HexColor('#0e2245')
    cream = colors.HexColor('#f0f3f8')
    light = colors.HexColor('#f7f9fc')

    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=14*mm, bottomMargin=14*mm
    )
    styles = getSampleStyleSheet()
    story  = []
    W, H   = letter

    def draw_border(cv, d):
        cv.saveState()
        cv.setStrokeColor(navy)
        cv.setLineWidth(3)
        cv.rect(10*mm, 10*mm, W-20*mm, H-20*mm)
        cv.setLineWidth(1)
        cv.rect(13*mm, 13*mm, W-26*mm, H-26*mm)
        cv.restoreState()

    def ps(name, **kw):
        return ParagraphStyle(name, parent=styles[kw.pop('parent', 'Normal')], **kw)

    affil_s = ps('affil', fontSize=9, textColor=colors.HexColor('#555555'), alignment=TA_CENTER, fontName='Helvetica-Oblique')
    title_s = ps('title', fontSize=18, textColor=navy, alignment=TA_CENTER, fontName='Helvetica-Bold', leading=22)
    addr_s  = ps('addr',  fontSize=9, textColor=colors.HexColor('#333333'), alignment=TA_CENTER, leading=13)
    dept_s  = ps('dept',  fontSize=11, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold')
    rpt_s   = ps('rpt',   fontSize=13, textColor=navy, alignment=TA_CENTER, fontName='Helvetica-Bold')
    sub_s   = ps('sub',   fontSize=9, textColor=colors.HexColor('#555555'), alignment=TA_CENTER, fontName='Helvetica-Oblique')
    lbl_s   = ps('lbl',   fontSize=9, textColor=navy, fontName='Helvetica-Bold')
    val_s   = ps('val',   fontSize=10, textColor=colors.HexColor('#111111'))
    note_s  = ps('note',  fontSize=8, textColor=colors.HexColor('#666666'), alignment=TA_CENTER, fontName='Helvetica-Oblique')
    sig_s   = ps('sig',   fontSize=9, textColor=navy, alignment=TA_CENTER, fontName='Helvetica-Bold')
    foot_s  = ps('foot',  fontSize=8, textColor=colors.HexColor('#777777'), alignment=TA_CENTER)
    pct_s   = ps('pct',   fontSize=8, textColor=colors.HexColor('#555555'), alignment=TA_CENTER)

    dept_name = student.get('department', 'DEPARTMENT OF ARTIFICIAL INTELLIGENCE & DATA SCIENCE').upper()
    if not dept_name.startswith('DEPARTMENT OF'):
        dept_name = f"DEPARTMENT OF {dept_name}"

    story += [
        Paragraph('Affiliated to Visvesvaraya Technological University (VTU), Belagavi | Approved by AICTE', affil_s),
        Spacer(1, 4),
        Paragraph('Shridevi Institute of Engineering and Technology', title_s),
        Paragraph('Sira Road, Tumakuru – 572 106, Karnataka, India', addr_s),
        Paragraph('Phone: 0816-225800  |  Email: info@shrideviiet.ac.in  |  www.shrideviiet.ac.in', addr_s),
        Spacer(1, 6),
        HRFlowable(width='100%', thickness=2, color=navy),
    ]

    dept_tbl = Table([[Paragraph(dept_name, dept_s)]], colWidths=[doc.width])
    dept_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), navy),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story += [
        dept_tbl, Spacer(1, 10),
        Paragraph('INTERNAL ASSESSMENT PROGRESS REPORT', rpt_s), Spacer(1, 3),
        Paragraph(f"Academic Year: {student['year']}  |  Semester: {student['semester']}  |  Grade: {student['grade']}", sub_s),
        Spacer(1, 10), HRFlowable(width='100%', thickness=1, color=navy), Spacer(1, 6)
    ]

    half = doc.width / 2
    det = Table([
        [Paragraph('Student Name', lbl_s), Paragraph(student['name'], val_s),
         Paragraph('USN', lbl_s),          Paragraph(student['usn'], val_s)],
        [Paragraph('Programme', lbl_s),    Paragraph(f"B.E. – {student.get('department', 'AI & Data Science')}", val_s),
         Paragraph('Semester', lbl_s),     Paragraph(f"{student['semester']} Semester", val_s)],
        [Paragraph('Academic Year', lbl_s),Paragraph(student['year'], val_s),
         Paragraph('Status / Grade', lbl_s), Paragraph(student['grade'], val_s)],
    ], colWidths=[half*0.32, half*0.68, half*0.32, half*0.68])
    det.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), cream), ('BACKGROUND', (2,0), (2,-1), cream),
        ('BOX', (0,0), (-1,-1), 1.2, navy), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#aaaaaa')),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story += [det, Spacer(1, 10)]

    hdr_s = ps('thdr', fontSize=9, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold')
    td_c  = ps('tdc',  fontSize=10, alignment=TA_CENTER)
    td_l  = ps('tdl',  fontSize=10, alignment=TA_LEFT)
    td_g  = ps('tdg',  fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor('#166534'), fontName='Helvetica-Bold')
    td_b  = ps('tdb',  fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor('#854d0e'), fontName='Helvetica-Bold')
    td_r  = ps('tdr',  fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor('#991b1b'), fontName='Helvetica-Bold')

    def score_para(score, max_m):
        ratio = score / max_m if max_m else 0
        if ratio >= 0.8:   return Paragraph(str(score), td_g)
        elif ratio >= 0.6: return Paragraph(str(score), td_b)
        else:              return Paragraph(str(score), td_r)

    marks_data = [[Paragraph(h, hdr_s) for h in
                   ['Sl.', 'Subject / Course Title', 'Max Marks', 'Marks Obtained', 'Attendance', 'Remarks']]]
    for i, s in enumerate(student['subjects'], 1):
        marks_data.append([
            Paragraph(str(i), td_c),
            Paragraph(s['name'], td_l),
            Paragraph(str(s['max']), td_c),
            score_para(s['score'], s['max']),
            Paragraph(str(s['attendance']), td_c),
            Paragraph(str(s['remark']), td_c),
        ])

    tot_s = ps('tot', fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=navy)
    gtl_s = ps('gtl', fontSize=10, alignment=TA_RIGHT,  fontName='Helvetica-Bold', textColor=navy)
    marks_data.append([
        Paragraph('', tot_s),
        Paragraph('GRAND TOTAL', gtl_s),
        Paragraph(str(student['max_total']), tot_s),
        Paragraph(str(student['total']), tot_s),
        Paragraph(f"{student['percentage']}%", pct_s),
        Paragraph('', tot_s),
    ])

    cw = [20, doc.width - 20 - 65 - 80 - 65 - 75, 65, 80, 65, 75]
    marks_tbl = Table(marks_data, colWidths=cw, repeatRows=1)
    marks_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), navy),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, light]),
        ('BACKGROUND', (0,-1), (-1,-1), cream),
        ('LINEABOVE', (0,-1), (-1,-1), 1.5, navy),
        ('BOX', (0,0), (-1,-1), 1.2, navy),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,1), (1,-1), 8), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story += [marks_tbl, Spacer(1, 10)]

    note_tbl = Table([[Paragraph(
        '★  This is an official computer-generated internal assessment report. Results are subject to final approval by the examination committee.', note_s
    )]], colWidths=[doc.width])
    note_tbl.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.7, colors.HexColor('#aaaaaa')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fffde7')),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story += [note_tbl, Spacer(1, 24)]

    sig_tbl = Table([
        [Paragraph('___________________________', sig_s)]*3,
        [Paragraph(x, sig_s) for x in ['Class Teacher', 'Head of Department', 'Principal']],
        [Paragraph(x, note_s) for x in ['Signature &amp; Date', f"Dept. of {student.get('department', 'AI & DS')}", 'Shridevi Inst. of Engg. &amp; Tech.']],
    ], colWidths=[doc.width/3]*3)
    sig_tbl.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story += [
        sig_tbl, Spacer(1, 14),
        HRFlowable(width='100%', thickness=1.5, color=navy), Spacer(1, 4),
        Paragraph('Shridevi Institute of Engineering and Technology, Tumakuru  |  Approved by AICTE  |  Affiliated to VTU, Belagavi', foot_s)
    ]

    doc.build(story, onFirstPage=draw_border, onLaterPages=draw_border)
    buffer.seek(0)
    return buffer
