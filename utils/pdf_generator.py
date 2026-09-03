"""
Generates a colorful, boxed Joint Measurement Sheet (JMS) PDF:

  [==== VISIONTECH INFRA SOLUTIONS — JMS  (colored bar) ====]

  +----------------------------------------------------------+
  | Circle: ...                                               |
  | TSP Partner :- ...          Site ID :- ...                |
  | Site Name :- ...            Project ID :- ...              |
  +----------------------------------------------------------+

  [ colored header row: S.No | Line Item | Unit | Qty | Remarks ]
  [ zebra striped item rows, bordered                          ]

  +---------------+ +---------------+ +---------------+ +---------------+
  | Partner Sup.  | | Audit Eng.    | | TSP Partner   | | Agency Name   |
  | <name>        | | <name>        | | <name>        | | <name>        |
  | [ signature ] | | [ signature ] | | [ signature ] | | [ signature ] |
  +---------------+ +---------------+ +---------------+ +---------------+
"""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

BRAND = colors.HexColor("#4f46e5")       # indigo
BRAND_LIGHT = colors.HexColor("#eef2ff")  # very light indigo fill
BRAND_DARK = colors.HexColor("#3730a3")
ACCENT = colors.HexColor("#8b5cf6")       # purple
ZEBRA = colors.HexColor("#f5f3ff")
BORDER = colors.HexColor("#c7d2fe")
TEXT_MUTED = colors.HexColor("#64748b")


def generate_jms_pdf(header: dict, items_df) -> bytes:
    """
    header keys: circle, tsp_partner, site_id, site_name, project_id,
                 partner_supervisor_name, audit_engineer_name, agency_name
    items_df columns: item_description, unit, qty, remarks (optional)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=10 * mm,
        bottomMargin=12 * mm,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Title"], fontSize=16, textColor=colors.white,
        alignment=1, spaceAfter=0,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle", parent=styles["Normal"], fontSize=9, textColor=colors.white,
        alignment=1, spaceAfter=0,
    )
    label_style = ParagraphStyle("LabelStyle", parent=styles["Normal"], fontSize=9.5, fontName="Helvetica-Bold", textColor=BRAND_DARK)
    value_style = ParagraphStyle("ValueStyle", parent=styles["Normal"], fontSize=9.5, fontName="Helvetica", textColor=colors.HexColor("#1e293b"))
    cell_style = ParagraphStyle("CellStyle", parent=styles["Normal"], fontSize=8, leading=10)
    header_cell_style = ParagraphStyle(
        "HeaderCellStyle", parent=styles["Normal"], fontSize=8.5, leading=10,
        fontName="Helvetica-Bold", textColor=colors.white,
    )
    sig_label_style = ParagraphStyle("SigLabelStyle", parent=styles["Normal"], fontSize=8, fontName="Helvetica-Bold", textColor=colors.white)
    sig_value_style = ParagraphStyle("SigValueStyle", parent=styles["Normal"], fontSize=8, leading=9.5, fontName="Helvetica-Bold", textColor=colors.HexColor("#1e293b"))
    sig_caption_style = ParagraphStyle("SigCaptionStyle", parent=styles["Normal"], fontSize=7, textColor=TEXT_MUTED)

    def lbl(text):
        return Paragraph(text, label_style)

    def val(text):
        return Paragraph(str(text) if text not in (None, "") else "&nbsp;", value_style)

    elements = []

    # ---- 1. Colored title bar -------------------------------------------
    title_table = Table(
        [[Paragraph("VISIONTECH INFRA SOLUTIONS", title_style)],
         [Paragraph("JOINT MEASUREMENT SHEET (JMS)", subtitle_style)]],
        colWidths=[186 * mm],
    )
    title_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BRAND),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                ("TOPPADDING", (0, 1), (-1, 1), 0),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
            ]
        )
    )
    elements.append(title_table)
    elements.append(Spacer(1, 5 * mm))

    # ---- 2. Site info box (bordered, light-filled) -----------------------
    site_rows = [
        [lbl("Circle:"), val(header.get("circle", "")), "", ""],
        [lbl("TSP Partner :-"), val(header.get("tsp_partner", "")), lbl("Site ID :-"), val(header.get("site_id", ""))],
        [lbl("Site Name :-"), val(header.get("site_name", "")), lbl("Project ID :-"), val(header.get("project_id", ""))],
    ]
    site_table = Table(site_rows, colWidths=[88, 172, 72, 163])
    site_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BRAND_LIGHT),
                ("BOX", (0, 0), (-1, -1), 1, BRAND),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(site_table)
    elements.append(Spacer(1, 6 * mm))

    # ---- 3. Line items table (colored header, zebra body) ----------------
    table_header = [Paragraph(h, header_cell_style) for h in ["S.No.", "Line Item", "Unit", "Qty as per site", "Remarks"]]
    table_data = [table_header]
    for i, row in enumerate(items_df.itertuples(index=False), start=1):
        table_data.append(
            [
                str(i),
                Paragraph(str(getattr(row, "item_description", "")), cell_style),
                getattr(row, "unit", ""),
                f"{getattr(row, 'qty', 0):g}",
                getattr(row, "remarks", "") or "",
            ]
        )

    col_widths = [35, 250, 45, 80, 85]
    items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 1, BRAND),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (2, 0), (3, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ZEBRA]),
            ]
        )
    )
    elements.append(items_table)
    elements.append(Spacer(1, 8 * mm))

    # ---- 4. Signature section (4 colored boxes with a blank sign area) --
    def sig_cell(role_label, name_value):
        return [
            Paragraph(role_label, sig_label_style),
            Paragraph(str(name_value) if name_value else "&nbsp;", sig_value_style),
        ]

    sig_top = [
        sig_cell("Partner Supervisor", header.get("partner_supervisor_name", "")),
        sig_cell("Audit Engineer", header.get("audit_engineer_name", "")),
        sig_cell("TSP Partner Name", header.get("tsp_partner", "")),
        sig_cell("Agency Name", header.get("agency_name", "")),
    ]
    sig_row_top = [Table([[c[0]], [c[1]]], colWidths=[105], rowHeights=[7 * mm, 11 * mm]) for c in sig_top]
    for t in sig_row_top:
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), BRAND),
                    ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (0, 0), 2),
                    ("BOTTOMPADDING", (0, 0), (0, 0), 2),
                    ("LEFTPADDING", (0, 0), (0, 0), 6),
                    ("VALIGN", (0, 1), (0, 1), "TOP"),
                    ("TOPPADDING", (0, 1), (0, 1), 4),
                    ("BOTTOMPADDING", (0, 1), (0, 1), 2),
                    ("LEFTPADDING", (0, 1), (0, 1), 6),
                    ("BACKGROUND", (0, 1), (0, 1), colors.white),
                ]
            )
        )

    sig_box_row = [Paragraph("Signature", sig_caption_style) for _ in range(4)]

    signature_table = Table(
        [sig_row_top, sig_box_row],
        colWidths=[47 * mm] * 4,
        rowHeights=[18 * mm, 20 * mm],
    )
    signature_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, BRAND),
                ("GRID", (0, 0), (-1, -1), 1, BRAND),
                ("VALIGN", (0, 0), (-1, 0), "TOP"),
                ("VALIGN", (0, 1), (-1, 1), "TOP"),
                ("LEFTPADDING", (0, 1), (-1, 1), 6),
                ("TOPPADDING", (0, 1), (-1, 1), 4),
            ]
        )
    )
    elements.append(signature_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
