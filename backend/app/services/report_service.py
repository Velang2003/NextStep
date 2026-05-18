import os
from io import BytesIO
from datetime import datetime, timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# --- Design Tokens ---
PRIMARY      = colors.HexColor('#4f46e5') # Indigo 600
SECONDARY    = colors.HexColor('#7c3aed') # Violet 600
TEXT_MAIN    = colors.HexColor('#0f172a') # Slate 900
TEXT_MUTED   = colors.HexColor('#64748b') # Slate 500
BORDER       = colors.HexColor('#e2e8f0') # Slate 200
BG_SUBTLE    = colors.HexColor('#f8fafc') # Slate 50
SUCCESS      = colors.HexColor('#16a34a')
WARNING      = colors.HexColor('#ca8a04')
ERROR        = colors.HexColor('#dc2626')

def build_report(user, gap_data: dict, career_data: dict, trend_data: list, assessment_data: list = None, app_data: dict = None) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
        title=f"NextStep Career Report — {user.email}",
    )

    styles = getSampleStyleSheet()
    story  = []

    # --- Custom Styles ---
    title_style = ParagraphStyle('Title', fontSize=28, textColor=TEXT_MAIN, fontName='Helvetica-Bold', leading=32, spaceAfter=8)
    subtitle_style = ParagraphStyle('Subtitle', fontSize=10, textColor=PRIMARY, fontName='Helvetica-Bold', leading=14, tracking=1, textTransform='uppercase')
    meta_style = ParagraphStyle('Meta', fontSize=8, textColor=TEXT_MUTED, fontName='Helvetica', alignment=TA_RIGHT)
    h2_style = ParagraphStyle('H2', fontSize=18, textColor=TEXT_MAIN, fontName='Helvetica-Bold', spaceBefore=20, spaceAfter=12)
    body_style = ParagraphStyle('Body', fontSize=10, textColor=TEXT_MAIN, fontName='Helvetica', leading=14)
    label_style = ParagraphStyle('Label', fontSize=9, textColor=TEXT_MUTED, fontName='Helvetica-Bold', textTransform='uppercase', tracking=0.5)
    cell_style = ParagraphStyle('Cell', fontSize=9, textColor=TEXT_MAIN, fontName='Helvetica', leading=14)

    # --- Header Section (Two Columns) ---
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'logo.png')
    
    header_left = []
    if os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=1.5*cm, height=1.5*cm)
            img.hAlign = 'LEFT'
            header_left.append(img)
        except:
            pass
    header_left.extend([
        Paragraph("NextStep", title_style),
        Paragraph("Career Progress Report", subtitle_style)
    ])

    header_right = [
        Paragraph(f"GENERATED FOR: {user.email.upper()}", meta_style),
        Paragraph(f"DATE: {datetime.now(timezone.utc).strftime('%B %d, %Y').upper()}", meta_style),
        Paragraph(f"PROFESSIONAL CAREER DOCUMENT", meta_style),
    ]

    header_table = Table([[header_left, header_right]], colWidths=[11*cm, 7*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width='100%', thickness=2, color=PRIMARY, spaceAfter=20))

    # --- Profile Summary Grid ---
    story.append(Paragraph("Your Profile", h2_style))
    profile = user.profile
    p_data = [
        [Paragraph("TARGET ROLE", label_style), Paragraph(profile.target_role or "NOT SET", cell_style)],
        [Paragraph("SKILL MATCH", label_style), Paragraph(f"{gap_data.get('match_percentage', 0)}% COMPATIBLE", cell_style)],
        [Paragraph("LOCATION", label_style), Paragraph(profile.location or "REMOTE/GLOBAL", cell_style)],
        [Paragraph("EXPERIENCE", label_style), Paragraph(f"{profile.experience_years or 0} YEARS", cell_style)],
    ]
    p_table = Table(p_data, colWidths=[4.5*cm, 13.5*cm])
    p_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('BACKGROUND', (0,0), (0,-1), BG_SUBTLE),
        ('LEFTPADDING', (0,0), (-1,-1), 15),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(p_table)

    # --- Skill Gap Visualization ---
    if gap_data:
        story.append(Paragraph("Skills to Learn", h2_style))
        missing = gap_data.get('missing_skills', [])[:12]
        demand = gap_data.get('demand_frequencies', {})
        
        if missing:
            story.append(Paragraph("Must-Learn Skills", label_style))
            story.append(Spacer(1, 0.2*cm))
            
            gap_rows = [['SKILL NAME', 'EMPLOYER DEMAND', 'PRIORITY']]
            for s in missing:
                freq = demand.get(s, 0)
                priority = "HIGH" if freq > 5 else "MEDIUM" if freq > 2 else "LOW"
                p_color = ERROR if priority == "HIGH" else WARNING if priority == "MEDIUM" else PRIMARY
                
                gap_rows.append([
                    Paragraph(s, cell_style),
                    f"{freq}% of Market",
                    Paragraph(priority, ParagraphStyle('P', fontSize=8, textColor=p_color, fontName='Helvetica-Bold'))
                ])
            
            g_table = Table(gap_rows, colWidths=[9*cm, 4.5*cm, 4.5*cm])
            g_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), TEXT_MAIN),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 9),
                ('GRID', (0,0), (-1,-1), 0.5, BORDER),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_SUBTLE]),
                ('ALIGN', (1,0), (-1,-1), 'CENTER'),
                ('LEFTPADDING', (0,0), (-1,-1), 12),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(g_table)

    # --- Assessments ---
    if assessment_data:
        story.append(Paragraph("Your Test Results", h2_style))
        ass_rows = [['SKILL', 'SCORE', 'LEVEL']]
        for a in assessment_data[:8]:
            score = a.get('percentage', 0)
            status = "EXPERT" if score >= 80 else "ADVANCED" if score >= 60 else "BEGINNER"
            s_color = SUCCESS if score >= 60 else WARNING
            
            ass_rows.append([
                Paragraph(a.get('skill_name', ''), cell_style),
                f"{score}%",
                Paragraph(status, ParagraphStyle('S', fontSize=8, textColor=s_color, fontName='Helvetica-Bold'))
            ])
        
        a_table = Table(ass_rows, colWidths=[9*cm, 4.5*cm, 4.5*cm])
        a_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), PRIMARY),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_SUBTLE]),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(a_table)

    # --- Market Trends ---
    if trend_data:
        story.append(Paragraph("Job Market Trends", h2_style))
        trend_rows = [['SKILL', 'OPEN JOBS', 'INDUSTRY']]
        for t in trend_data[:10]:
            trend_rows.append([
                Paragraph(t['skill'], cell_style),
                str(t['count']),
                Paragraph(t.get('sector', 'GENERIC TECH'), cell_style)
            ])
        
        t_table = Table(trend_rows, colWidths=[8*cm, 5*cm, 5*cm])
        t_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), SECONDARY),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_SUBTLE]),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(t_table)

    story.append(Spacer(1, 2*cm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER))
    footer_text = "This report was created by NextStep using live data from top job boards. We help you find the shortest path to your next career move."
    story.append(Paragraph(footer_text, ParagraphStyle('Footer', fontSize=7, textColor=TEXT_MUTED, alignment=TA_CENTER, leading=10, spaceBefore=10)))
    story.append(Paragraph("NEXTSTEP.IO — YOUR NEXT MOVE, SIMPLIFIED", ParagraphStyle('FooterB', fontSize=7, textColor=TEXT_MUTED, alignment=TA_CENTER, fontName='Helvetica-Bold', spaceBefore=5)))

    doc.build(story)
    buf.seek(0)
    return buf
