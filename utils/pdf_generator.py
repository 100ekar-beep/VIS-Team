"""
Generates the JMS PDF:

  +==========================================================+
  |            VISIONTECH INFRA SOLUTIONS (letterhead)        |
  |               Joint Measurement Sheet                     |
  |------------------------------------------------------------|
  |  Circle:- ...              | Site ID :- ...                 |
  |  Site Name :- ...         | Project ID :- ...               |
  |------------------------------------------------------------|
  |  S.No | Item Code | Item Description | Qty as per site | Remarks |
  |  ... rows ...                                               |
  |                                                              |
  |  +-------------------------+  +-------------------------+   |
  |  | TSP Partner Name :      |  | Auditor Name :-          |  |
  |  | Visiontech Infra Sol.   |  | Audit Agency :-          |  |
  |  +-------------------------+  +-------------------------+   |
  +==========================================================+

The whole page has a thin border. Signature boxes are always anchored to
the bottom of the page — leftover space above them is left blank so an
auditor can write in missed items by hand.
"""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import Table, TableStyle, Paragraph

PAGE_W, PAGE_H = A4

PAGE_BORDER = 7 * mm                     # thin border around the whole page
MARGIN = 14 * mm                         # content margin (text/tables)
CONTENT_W = PAGE_W - 2 * MARGIN

LETTERHEAD_H = 24 * mm
BOX_AREA_HEIGHT = 45 * mm                # signature boxes (~30% shorter than before)
BOX_GAP = 8 * mm

BRAND = colors.HexColor("#3730a3")       # deep indigo
ACCENT = colors.HexColor("#f59e0b")      # gold accent stripe


def generate_jms_pdf(header: dict, items_df) -> bytes:
    """
    header keys: circle, tsp_partner, site_id, site_name, project_id
    items_df columns: item_code, item_description, qty, remarks (optional)
    """
    buffer = io.BytesIO()
    c = pdfcanvas.Canvas(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    label_style = ParagraphStyle("LabelStyle", parent=styles["Normal"], fontSize=9.5, fontName="Helvetica-Bold")
    value_style = ParagraphStyle("ValueStyle", parent=styles["Normal"], fontSize=9.5, fontName="Helvetica")
    cell_style = ParagraphStyle("CellStyle", parent=styles["Normal"], fontSize=8, leading=10)
    header_cell_style = ParagraphStyle("HeaderCellStyle", parent=styles["Normal"], fontSize=8.5, leading=10, fontName="Helvetica-Bold")

    def lbl(text):
        return Paragraph(text, label_style)

    def val(text):
        return Paragraph(str(text) if text not in (None, "") else "&nbsp;", value_style)

    def draw_page_border():
        c.setLineWidth(1.2)
        c.setStrokeColor(colors.black)
        c.rect(PAGE_BORDER, PAGE_BORDER, PAGE_W - 2 * PAGE_BORDER, PAGE_H - 2 * PAGE_BORDER)

    def draw_letterhead():
        """Lavish colored letterhead band with the company name + subtitle."""
        band_x = PAGE_BORDER
        band_w = PAGE_W - 2 * PAGE_BORDER
        band_top = PAGE_H - PAGE_BORDER
        band_bottom = band_top - LETTERHEAD_H

        c.setFillColor(BRAND)
        c.rect(band_x, band_bottom, band_w, LETTERHEAD_H, stroke=0, fill=1)
        # gold accent stripe under the band
        c.setFillColor(ACCENT)
        c.rect(band_x, band_bottom, band_w, 1.6 * mm, stroke=0, fill=1)

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 19)
        c.drawCentredString(PAGE_W / 2, band_top - 11 * mm, "VISIONTECH INFRA SOLUTIONS")
        c.setFont("Helvetica", 11)
        c.drawCentredString(PAGE_W / 2, band_top - 18 * mm, "Joint Measurement Sheet")

        c.setFillColor(colors.black)
        return band_bottom - 7 * mm

    def draw_site_box(y):
        """Bordered box, full content width, 2x2 grid: Circle/Site ID, Site Name/Project ID."""
        rows = [
            [lbl("Circle:"), val(header.get("circle", "")), lbl("Site ID :-"), val(header.get("site_id", ""))],
            [lbl("Site Name :-"), val(header.get("site_name", "")), lbl("Project ID :-"), val(header.get("project_id", ""))],
        ]
        col_w = [78, CONTENT_W / 2 - 78, 80, CONTENT_W / 2 - 80]
        t = Table(rows, colWidths=col_w)
        t.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("LINEAFTER", (1, 0), (1, -1), 0.5, colors.black),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        tw, th = t.wrapOn(c, CONTENT_W, y)
        t.drawOn(c, MARGIN, y - th)
        return y - th - 7 * mm

    def draw_items_table(y):
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
        col_widths = [38, 88, CONTENT_W - 38 - 88 - 65 - 61, 65, 61]
        t = Table(table_data, colWidths=col_widths)
        t.setStyle(
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
        tw, th = t.wrapOn(c, CONTENT_W, y)
        t.drawOn(c, MARGIN, y - th)
        return y - th

    def draw_signature_boxes():
        """2 boxes, side by side, anchored to the bottom margin of the page."""
        box_w = (CONTENT_W - BOX_GAP) / 2
        box_bottom = MARGIN
        box_top = MARGIN + BOX_AREA_HEIGHT

        left_x = MARGIN
        right_x = MARGIN + box_w + BOX_GAP

        c.setLineWidth(1)
        c.setStrokeColor(colors.black)
        c.rect(left_x, box_bottom, box_w, BOX_AREA_HEIGHT)
        c.rect(right_x, box_bottom, box_w, BOX_AREA_HEIGHT)

        text_pad = 6 * mm
        line1_y = box_bottom + 13 * mm
        line2_y = box_bottom + 6 * mm
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(left_x + text_pad, line1_y, "TSP Partner Name :")
        c.setFont("Helvetica", 9.5)
        c.drawString(left_x + text_pad, line2_y, header.get("tsp_partner", "Visiontech Infra Solutions"))

        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(right_x + text_pad, line1_y, "Auditor Name :-")
        c.drawString(right_x + text_pad, line2_y, "Audit Agency :-")

        return box_top

    # ---- Page 1: border, letterhead, site box, items table -----------------
    draw_page_border()
    y = draw_letterhead()
    y = draw_site_box(y)
    y_after_table = draw_items_table(y)

    box_top_needed = MARGIN + BOX_AREA_HEIGHT + 6 * mm

    if y_after_table < box_top_needed:
        # Items table ran into the reserved bottom-box area — put the
        # signature boxes on a fresh page instead of overlapping them.
        c.showPage()
        draw_page_border()

    draw_signature_boxes()

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
