"""
Professional Print-Ready Book Generator for Vedāṅga-Jyotiṣa
CRINE (All Religious Texts - ART Ecosystem)
"""

import os
import json
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable, KeepTogether, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib import colors

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute total pages and render print headers/footers.
    Follows press book standards: suppress headers/footers on title page, TOC, half-title.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # Skip headers and footers on cover/title/preface pages (pages 1-3)
        if self._pageNumber <= 3:
            return

        self.saveState()
        
        # Color Palette
        primary_gold = colors.HexColor('#8B5A2B')
        text_dark = colors.HexColor('#2C2C2C')
        border_gold = colors.HexColor('#D4AF37')
        
        width, height = A5
        margin = 36 # 0.5 in

        # Header Text
        self.setFont('NotoSerifDevanagari', 8)
        self.setFillColor(primary_gold)
        
        if self._pageNumber % 2 == 0:
            # Even page (Left)
            self.drawString(margin, height - 28, "वेदाङ्गज्योतिषम्")
            self.setFont('LatinSerif-Bold', 8)
            self.drawRightString(width - margin, height - 28, "CRINE CRITICAL EDITION")
        else:
            # Odd page (Right)
            self.setFont('LatinSerif-Bold', 8)
            self.drawString(margin, height - 28, "RIGVEDA RECENSION - LAGADHA")
            self.drawRightString(width - margin, height - 28, "ALL RELIGIOUS TEXTS (ART)")

        # Header Rule
        self.setStrokeColor(border_gold)
        self.setLineWidth(0.5)
        self.line(margin, height - 32, width - margin, height - 32)

        # Footer Rule
        self.line(margin, 36, width - margin, 36)

        # Footer Text & Page Numbering
        self.setFont('LatinSerif', 8.5)
        self.setFillColor(text_dark)
        page_str = f"Page {self._pageNumber} of {page_count}"
        
        if self._pageNumber % 2 == 0:
            self.drawString(margin, 22, page_str)
            self.drawRightString(width - margin, 22, "www.crine.in")
        else:
            self.drawString(margin, 22, "CRINE Dataset Repository")
            self.drawRightString(width - margin, 22, page_str)

        self.restoreState()


def clean_verse_lines(text):
    """
    Cleans raw XML danda artifacts into elegant verse lines for print layout.
    """
    text = text.replace("//", "॥").replace("/", "|")
    parts = [p.strip() for p in text.split("|")]
    return " | ".join(parts)


def build_pdf():
    base_dir = "data/vedic-canon/vedanga-jyotisa"
    orig_path = os.path.join(base_dir, "original.json")
    deva_path = os.path.join(base_dir, "translations/devanagari/indic-transliteration.json")
    meta_path = os.path.join(base_dir, "metadata.json")
    output_pdf = os.path.join(base_dir, "vedanga_jyotisa_edition.pdf")

    with open(orig_path, 'r', encoding='utf-8') as f:
        orig_data = json.load(f)

    with open(deva_path, 'r', encoding='utf-8') as f:
        deva_data = json.load(f)

    with open(meta_path, 'r', encoding='utf-8') as f:
        meta_data = json.load(f)

    # Register TTF Fonts
    font_deva_reg = "/usr/share/fonts/truetype/noto/NotoSerifDevanagari-Regular.ttf"
    font_deva_bold = "/usr/share/fonts/truetype/noto/NotoSerifDevanagari-Bold.ttf"
    
    font_lat_reg = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
    font_lat_bold = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
    font_lat_italic = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
    
    pdfmetrics.registerFont(TTFont('NotoSerifDevanagari', font_deva_reg))
    pdfmetrics.registerFont(TTFont('NotoSerifDevanagari-Bold', font_deva_bold))

    pdfmetrics.registerFont(TTFont('LatinSerif', font_lat_reg))
    pdfmetrics.registerFont(TTFont('LatinSerif-Bold', font_lat_bold))
    pdfmetrics.registerFont(TTFont('LatinSerif-Italic', font_lat_italic))

    # Page Setup (A5 Press Standard)
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A5,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=45
    )

    # Styling Palette
    c_primary = colors.HexColor('#4A2E16')    # Deep Saffron/Saddle Bronze
    c_secondary = colors.HexColor('#8B5A2B')  # Muted Gold/Amber
    c_text = colors.HexColor('#1A1A1A')       # Charcoal Body Text
    c_iast = colors.HexColor('#2E4053')       # Slate Navy IAST Text
    c_card_bg = colors.HexColor('#FDFBF7')   # Warm Cream Card Background
    c_card_border = colors.HexColor('#E5D3B3') # Light Gold Border

    # Custom Paragraph Styles
    style_cover_title_deva = ParagraphStyle(
        'CoverTitleDeva',
        fontName='NotoSerifDevanagari-Bold',
        fontSize=24,
        leading=32,
        alignment=TA_CENTER,
        textColor=c_primary,
        spaceAfter=10
    )

    style_cover_title_iast = ParagraphStyle(
        'CoverTitleIAST',
        fontName='LatinSerif-Bold',
        fontSize=18,
        leading=24,
        alignment=TA_CENTER,
        textColor=c_secondary,
        spaceAfter=15
    )

    style_cover_sub = ParagraphStyle(
        'CoverSub',
        fontName='LatinSerif',
        fontSize=10.5,
        leading=15,
        alignment=TA_CENTER,
        textColor=c_text,
        spaceAfter=25
    )

    style_section_heading_lat = ParagraphStyle(
        'SectionHeadingLat',
        fontName='LatinSerif-Bold',
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=c_primary,
        spaceBefore=15,
        spaceAfter=10
    )

    style_section_heading_deva = ParagraphStyle(
        'SectionHeadingDeva',
        fontName='NotoSerifDevanagari-Bold',
        fontSize=15,
        leading=20,
        alignment=TA_CENTER,
        textColor=c_primary,
        spaceBefore=15,
        spaceAfter=10
    )

    style_meta_label = ParagraphStyle(
        'MetaLabel',
        fontName='LatinSerif-Bold',
        fontSize=9,
        leading=13,
        textColor=c_secondary
    )

    style_meta_val_lat = ParagraphStyle(
        'MetaValLat',
        fontName='LatinSerif',
        fontSize=9,
        leading=13,
        textColor=c_text
    )

    style_meta_val_deva = ParagraphStyle(
        'MetaValDeva',
        fontName='NotoSerifDevanagari',
        fontSize=9,
        leading=13,
        textColor=c_text
    )

    style_body_lat = ParagraphStyle(
        'BodyLat',
        fontName='LatinSerif',
        fontSize=9.5,
        leading=15,
        alignment=TA_JUSTIFY,
        textColor=c_text,
        spaceAfter=8
    )

    style_verse_deva = ParagraphStyle(
        'VerseDeva',
        fontName='NotoSerifDevanagari-Bold',
        fontSize=11,
        leading=17,
        alignment=TA_CENTER,
        textColor=c_primary,
        spaceAfter=4
    )

    style_verse_iast = ParagraphStyle(
        'VerseIAST',
        fontName='LatinSerif',
        fontSize=9.5,
        leading=14,
        alignment=TA_CENTER,
        textColor=c_iast,
        spaceAfter=4
    )

    style_verse_num = ParagraphStyle(
        'VerseNum',
        fontName='LatinSerif-Bold',
        fontSize=8.5,
        leading=11,
        alignment=TA_RIGHT,
        textColor=c_secondary
    )

    story = []

    # ==========================================
    # 1. FRONT COVER / TITLE PAGE
    # ==========================================
    story.append(Spacer(1, 15))
    story.append(Paragraph("॥ श्रीमद्लगधप्रणीतं वेदाङ्गज्योतिषम् ॥", style_cover_title_deva))
    story.append(Paragraph("VEDĀṄGA-JYOTIṢA", style_cover_title_iast))
    story.append(HRFlowable(width="65%", thickness=1.5, color=c_secondary, spaceBefore=5, spaceAfter=15))
    story.append(Paragraph("The Canonical Astronomical Auxiliary of the Veda<br/><i>Ṛgveda Recension Assembled by Sage Lagadha</i>", style_cover_sub))
    
    story.append(Spacer(1, 15))

    # Decorative Ornament
    story.append(Paragraph("☸   𑁍   ☸", ParagraphStyle('Symbol', fontName='NotoSerifDevanagari', fontSize=14, alignment=TA_CENTER, textColor=c_secondary)))
    story.append(Spacer(1, 20))

    # Publication Metadata Box
    meta_table_data = [
        [Paragraph("Author / Rishi:", style_meta_label), Paragraph("Mahātma Lagadha (<font name='NotoSerifDevanagari'>लगधः</font>)", style_meta_val_lat)],
        [Paragraph("Recension / Veda:", style_meta_label), Paragraph("Ṛgveda Recension (35 Verses)", style_meta_val_lat)],
        [Paragraph("Collection:", style_meta_label), Paragraph("Vedic Canon (Vedāṅga)", style_meta_val_lat)],
        [Paragraph("Textual Source:", style_meta_label), Paragraph("GRETIL Critical Edition (sa_lagadha-RgvedavedAGgajyotiSa.xml)", style_meta_val_lat)],
        [Paragraph("Ecosystem Standard:", style_meta_label), Paragraph("CRINE All Religious Texts (ART) Platform", style_meta_val_lat)],
        [Paragraph("Publisher & Year:", style_meta_label), Paragraph("CRINE Publishing House, 2026", style_meta_val_lat)],
    ]
    meta_table = Table(meta_table_data, colWidths=[110, 180])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
        ('BOX', (0,0), (-1,-1), 1, c_card_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#F0E6D2')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(meta_table)

    story.append(PageBreak())

    # ==========================================
    # 2. PREFACE & INTRODUCTORY ESSAY
    # ==========================================
    story.append(Paragraph("PREFACE & INTRODUCTION", style_section_heading_lat))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceBefore=4, spaceAfter=12))

    intro_text = (
        "<b>The Vedāṅga-Jyotiṣa</b> is historically recognized as the oldest extant Indian astronomical text, "
        "formulating the fundamental calendar, timekeeping metrics, and celestial mechanics required for "
        "the precise scheduling of Vedic Yajñas (sacrifices) and rituals. Attributed to the ancient sage "
        "<b>Lagadha</b>, it represents the astronomical branch (<i>Jyotiṣa</i>) among the six traditional "
        "auxiliary disciplines (<i>Vedāṅgas</i>) of Vedic literature.<br/><br/>"
        "As verse 35 famously proclaims:<br/>"
        "<i>“Yathā śikhā mayūrāṇāṃ nāgānāṃ maṇayo yathā | Tadvad vedāṅgaśāstrāṇāṃ jyotiṣaṃ mūrdhani sthitam ॥”</i><br/>"
        "<i>(Just as the crest stands at the head of peacocks and gems crown the serpents, so does Jyotiṣa stand at the apex of all Vedāṅga sciences.)</i><br/><br/>"
        "<b>Textual Structure & Metrics:</b><br/>"
        "This critical bilingual edition contains the complete 35 verses of the Ṛgveda recension in dual layout: "
        "original Sanskrit in Devanagari script paired with standardized International Alphabet of Sanskrit Transliteration (IAST)."
    )
    story.append(Paragraph(intro_text, style_body_lat))

    story.append(Spacer(1, 15))

    # Table of Contents Summary
    story.append(Paragraph("CANONICAL CONTENTS", style_section_heading_lat))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceBefore=4, spaceAfter=12))

    toc_data = [
        [Paragraph("<b>Section / Chapter</b>", style_meta_label), Paragraph("<b>Verses</b>", style_meta_label), Paragraph("<b>Page</b>", style_meta_label)],
        [Paragraph("Preface & Introduction", style_meta_val_lat), Paragraph("—", style_meta_val_lat), Paragraph("Page 2", style_meta_val_lat)],
        [Paragraph("Vedāṅga-Jyotiṣa (<font name='NotoSerifDevanagari'>वेदाङ्गज्योतिषम्</font>)", style_meta_val_lat), Paragraph("Verses 1 – 35", style_meta_val_lat), Paragraph("Page 3", style_meta_val_lat)],
    ]
    toc_table = Table(toc_data, colWidths=[180, 60, 50])
    toc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F5EBDC')),
        ('BOX', (0,0), (-1,-1), 0.8, c_card_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5D3B3')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(toc_table)

    story.append(PageBreak())

    # ==========================================
    # 3. CANONICAL VERSES (CRITICAL BILINGUAL EDITION)
    # ==========================================
    story.append(Paragraph("वेदाङ्गज्योतिषम् — मूलपाठः", style_section_heading_deva))
    story.append(Paragraph("VEDĀṄGA-JYOTIṢA (CANONICAL TEXT)", style_cover_title_iast))
    story.append(HRFlowable(width="100%", thickness=1, color=c_primary, spaceBefore=2, spaceAfter=15))

    orig_verses = orig_data['chapters'][0]['verses']
    deva_verses = deva_data['chapters'][0]['verses']

    for v_orig, v_deva in zip(orig_verses, deva_verses):
        citation = v_orig['citation']
        
        t_deva = clean_verse_lines(v_deva['text'])
        t_iast = clean_verse_lines(v_orig['text'])

        # Card container for each verse block
        card_content = []
        card_content.append(Paragraph(f"<b>Verse {citation}</b>", style_verse_num))
        card_content.append(Spacer(1, 2))
        card_content.append(Paragraph(t_deva, style_verse_deva))
        card_content.append(Spacer(1, 3))
        card_content.append(Paragraph(t_iast, style_verse_iast))

        card_table = Table([[card_content]], colWidths=[290])
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
            ('BOX', (0,0), (-1,-1), 0.8, c_card_border),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ]))

        # Prevent mid-verse orphan breaks across page boundaries
        story.append(KeepTogether([card_table, Spacer(1, 10)]))

    # Build Document with Custom Canvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print("Successfully built press-ready PDF:", output_pdf)

if __name__ == "__main__":
    build_pdf()
