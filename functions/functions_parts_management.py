import io
import sqlite3
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from functions.theme import THEME_ORANGE, THEME_BLACK, THEME_GREY, THEME_LIGHT_GREY, THEME_WHITE

def get_parts_overview(conn):
    """Fetches full parts inventory with fitments and source count."""
    query = """
        SELECT 
            p.id,
            p.part_number AS 'Part No',
            p.name AS 'Part Name',
            p.category AS 'Category',
            p.stock_qty AS 'In Stock',
            p.min_stock_level AS 'Min Stock',
            COUNT(DISTINCT pss.id) AS 'Available Brands/Sources'
        FROM parts p
        LEFT JOIN part_supplier_sources pss ON p.id = pss.part_id
        GROUP BY p.id
        ORDER BY p.part_number ASC
    """
    return pd.read_sql_query(query, conn)

def search_parts_sourcing_guide(conn, make_filter=None, model_filter=None, part_search=None):
    """Comprehensive lookup engine matching car models to parts, brands, suppliers, and prices."""
    query = """
        SELECT 
            p.part_number AS 'Part No',
            p.name AS 'Part Name',
            p.category AS 'Category',
            pf.car_make AS 'Make',
            pf.car_model AS 'Model',
            pf.year_range AS 'Year Fitment',
            pss.brand_name AS 'Part Brand',
            s.name AS 'Supplier',
            pss.unit_cost AS 'Unit Cost (₹)',
            pss.lead_time_days AS 'Lead Time (Days)',
            pss.is_preferred AS 'Preferred Source',
            p.stock_qty AS 'In Stock Qty'
        FROM parts p
        JOIN part_fitments pf ON p.id = pf.part_id
        LEFT JOIN part_supplier_sources pss ON p.id = pss.part_id
        LEFT JOIN suppliers s ON pss.supplier_id = s.id
        WHERE 1=1
    """
    params = []
    if make_filter and make_filter != "All":
        query += " AND pf.car_make = ?"
        params.append(make_filter)
    if model_filter and model_filter != "All":
        query += " AND pf.car_model = ?"
        params.append(model_filter)
    if part_search:
        query += " AND (p.name LIKE ? OR p.part_number LIKE ?)"
        params.append(f"%{part_search}%")
        params.append(f"%{part_search}%")

    query += " ORDER BY p.name ASC, pss.unit_cost ASC"
    return pd.read_sql_query(query, conn, params=params)

def generate_parts_sourcing_pdf(res_df, title_text, subtitle_text):
    """Generates a landscape PDF guide for parts inventory and supplier sources."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(letter),
        rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25
    )
    
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontSize=18, leading=22,
        textColor=colors.HexColor(THEME_ORANGE), fontName='Helvetica-Bold', spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle', parent=styles['Normal'], fontSize=10, leading=14,
        textColor=colors.HexColor(THEME_GREY), fontName='Helvetica', spaceAfter=10
    )
    cell_header_style = ParagraphStyle(
        'HeaderCell', parent=styles['Normal'], fontSize=8, leading=10,
        fontName='Helvetica-Bold', textColor=colors.HexColor(THEME_WHITE), alignment=1
    )
    cell_body_style = ParagraphStyle(
        'BodyCell', parent=styles['Normal'], fontSize=8, leading=10,
        textColor=colors.HexColor(THEME_BLACK)
    )

    elements.append(Paragraph(title_text, title_style))
    elements.append(Paragraph(f"<b>{subtitle_text}</b> &nbsp;|&nbsp; Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    
    divider = Table([['']], colWidths=['100%'], rowHeights=[2])
    divider.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(THEME_ORANGE))]))
    elements.append(divider)
    elements.append(Spacer(1, 12))

    if res_df.empty:
        elements.append(Paragraph("No parts sourcing data available.", cell_body_style))
    else:
        df_pdf = res_df.copy()
        for col in df_pdf.columns:
            df_pdf[col] = df_pdf[col].astype(str).str.replace("₹", "Rs. ")

        table_data = [[Paragraph(str(h), cell_header_style) for h in df_pdf.columns]]
        for _, row in df_pdf.iterrows():
            table_data.append([Paragraph(str(row[c]), cell_body_style) for c in df_pdf.columns])

        pdf_table = Table(table_data, repeatRows=1)
        pdf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(THEME_BLACK)),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor(THEME_LIGHT_GREY), colors.HexColor(THEME_WHITE)]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(THEME_GREY)),
        ]))
        elements.append(pdf_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()