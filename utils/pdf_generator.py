"""
Generates a Joint Measurement Sheet (JMS) PDF matching the company's
standard format (see uploaded JMS_Format.pdf):

  Circle: ...                              Date: ...
  TSP Partner :- ...                       Site ID :- ...
  Site Name :- ...                         RL ID :- ...

  S.No | Line Item | Unit | Qty as per site | Remarks

  Partner Supervisor Name :- ...           Audit Engineer Name :- ...
  TSP Partner Name : ...                   Agency Name : ...
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
    header keys: circle, date, tsp_partner, site_id, site_name, rl_id,
                 partner_supervisor_name, audit_engineer_name, agency_name
    items_df columns: item_code (optional, not printed), item_description,
                       unit, qty, remarks (optional)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=14, spaceAfter=2)
    label_style = ParagraphStyle("LabelStyle", parent=styles["Normal"], fontSize=9.5, fontName="Helvetica-Bold")
    value_style = ParagraphStyle("ValueStyle", parent=styles["Normal"], fontSize=9.5, fontName="Helvetica")

    def lbl(text):
        return Paragraph(text, label_style)

    def val(text):
        return Paragraph(str(text) if text not in (None, "") else "&nbsp;", value_style)

    elements = [Paragraph("VISIONTECH INFRA SOLUTIONS - JMS", title_style), Spacer(1, 4 * mm)]

    # --- Header block (2-column key:value grid, like the original) --------
    header_rows = [
        [lbl("Circle:"), val(header.get("circle", "")), lbl("Date:"), val(header.get("date", ""))],
        [lbl("TSP Partner :-"), val(header.get("tsp_partner", "")), lbl("Site ID :-"), val(header.get("site_id", ""))],
        [lbl("Site Name :-"), val(header.get("site_name", "")), lbl("RL ID :-"), val(header.get("rl_id", ""))],
    ]
    header_table = Table(header_rows, colWidths=[90, 180, 75, 135])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(header_table)
    elements.append(Spacer(1, 6 * mm))

    # --- Line items table ---------------------------------------------------
    cell_style = ParagraphStyle("CellStyle", parent=styles["Normal"], fontSize=8, leading=10)
    header_cell_style = ParagraphStyle(
        "HeaderCellStyle", parent=styles["Normal"], fontSize=8, leading=10,
        fontName="Helvetica-Bold", textColor=colors.white,
    )

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

    col_widths = [35, 250, 45, 80, 70]
    items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (2, 0), (3, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f7")]),
            ]
        )
    )
    elements.append(items_table)
    elements.append(Spacer(1, 10 * mm))

    # --- Footer / signature block -------------------------------------------
    footer_rows = [
        [lbl("Partner Supervisor Name :-"), val(header.get("partner_supervisor_name", "")),
         lbl("Audit Engineer Name :-"), val(header.get("audit_engineer_name", ""))],
        [lbl("TSP Partner Name :"), val(header.get("tsp_partner", "")),
         lbl("Agency Name :"), val(header.get("agency_name", ""))],
    ]
    footer_table = Table(footer_rows, colWidths=[150, 110, 105, 115])
    footer_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(footer_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
