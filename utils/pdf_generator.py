"""
Generates a plain, minimal Joint Measurement Sheet (JMS) PDF matching the
company's standard format:

  VISIONTECH INFRA SOLUTIONS - JMS

  Circle: ...
  TSP Partner :- ...          Site ID :- ...
  Site Name :- ...            Project ID :- ...

  S.No | Item Code | Item Description | Qty as per site | Remarks

  Partner Supervisor Name :- ...      Audit Engineer Name :- ...
  [ signature box ]                   [ signature box ]
  TSP Partner Name : ...              Agency Name : ...
  [ signature box ]                   [ signature box ]
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


def generate_jms_pdf(header: dict, items_df) -> bytes:
    """
    header keys: circle, tsp_partner, site_id, site_name, project_id,
                 partner_supervisor_name, audit_engineer_name, agency_name
    items_df columns: item_code, item_description, qty, remarks (optional)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=15, spaceAfter=0, alignment=1)
    label_style = ParagraphStyle("LabelStyle", parent=styles["Normal"], fontSize=9.5, fontName="Helvetica-Bold")
    value_style = ParagraphStyle("ValueStyle", parent=styles["Normal"], fontSize=9.5, fontName="Helvetica")
    cell_style = ParagraphStyle("CellStyle", parent=styles["Normal"], fontSize=8, leading=10)
    header_cell_style = ParagraphStyle("HeaderCellStyle", parent=styles["Normal"], fontSize=8.5, leading=10, fontName="Helvetica-Bold")
    sig_caption_style = ParagraphStyle("SigCaptionStyle", parent=styles["Normal"], fontSize=7, textColor=colors.grey)

    def lbl(text):
        return Paragraph(text, label_style)

    def val(text):
        return Paragraph(str(text) if text not in (None, "") else "&nbsp;", value_style)

    elements = []

    # ---- Title -------------------------------------------------------------
    elements.append(Paragraph("VISIONTECH INFRA SOLUTIONS - JMS", title_style))
    elements.append(Spacer(1, 1 * mm))
    line_table = Table([[""]], colWidths=[182 * mm], rowHeights=[0.6])
    line_table.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 1, colors.black)]))
    elements.append(line_table)
    elements.append(Spacer(1, 5 * mm))

    # ---- Site info (plain 2-column grid, no borders — like the original) ---
    site_rows = [
        [lbl("Circle:"), val(header.get("circle", "")), "", ""],
        [lbl("TSP Partner :-"), val(header.get("tsp_partner", "")), lbl("Site ID :-"), val(header.get("site_id", ""))],
        [lbl("Site Name :-"), val(header.get("site_name", "")), lbl("Project ID :-"), val(header.get("project_id", ""))],
    ]
    site_table = Table(site_rows, colWidths=[85, 175, 72, 165])
    site_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    elements.append(site_table)
    elements.append(Spacer(1, 6 * mm))

    # ---- Line items table (plain black/white, grey header) -----------------
    table_header = [Paragraph(h, header_cell_style) for h in ["S.No.", "Item Code", "Item Description", "Qty as per site", "Remarks"]]
    table_data = [table_header]
    for i, row in enumerate(items_df.itertuples(index=False), start=1):
        table_data.append(
            [
                str(i),
                Paragraph(str(getattr(row, "item_code", "")), cell_style),
                Paragraph(str(getattr(row, "item_description", "")), cell_style),
                f"{getattr(row, 'qty', 0):g}",
                getattr(row, "remarks", "") or "",
            ]
        )

    col_widths = [38, 88, 231, 65, 61]
    items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (3, 0), (3, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(items_table)
    elements.append(Spacer(1, 8 * mm))

    # ---- Signature section (plain, bordered boxes) --------------------------
    sig_rows = [
        [lbl("Partner Supervisor Name :-"), val(header.get("partner_supervisor_name", "")),
         lbl("Audit Engineer Name :-"), val(header.get("audit_engineer_name", ""))],
        [Paragraph("Signature", sig_caption_style), "", Paragraph("Signature", sig_caption_style), ""],
        [lbl("TSP Partner Name :"), val(header.get("tsp_partner", "")),
         lbl("Agency Name :"), val(header.get("agency_name", ""))],
        [Paragraph("Signature", sig_caption_style), "", Paragraph("Signature", sig_caption_style), ""],
    ]
    sig_table = Table(sig_rows, colWidths=[95, 130, 90, 140], rowHeights=[9 * mm, 16 * mm, 9 * mm, 16 * mm])
    sig_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("BOX", (0, 1), (1, 1), 0.75, colors.black),
                ("BOX", (2, 1), (3, 1), 0.75, colors.black),
                ("BOX", (0, 3), (1, 3), 0.75, colors.black),
                ("BOX", (2, 3), (3, 3), 0.75, colors.black),
                ("LEFTPADDING", (0, 1), (0, 1), 4),
                ("LEFTPADDING", (2, 1), (2, 1), 4),
                ("LEFTPADDING", (0, 3), (0, 3), 4),
                ("LEFTPADDING", (2, 3), (2, 3), 4),
                ("TOPPADDING", (0, 1), (-1, 1), 3),
                ("TOPPADDING", (0, 3), (-1, 3), 3),
            ]
        )
    )
    elements.append(sig_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
