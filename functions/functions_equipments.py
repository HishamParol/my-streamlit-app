import io
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from functions.theme import THEME_ORANGE, THEME_BLACK, THEME_GREY, THEME_LIGHT_GREY, THEME_WHITE

def generate_pdf_report(res_df, title_text, subtitle_text, group_by_category=False, summary_metrics=None):
    """Generates a styled landscape PDF from the comparison dataframe."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor(THEME_ORANGE),
        fontName='Helvetica-Bold',
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor(THEME_GREY),
        fontName='Helvetica',
        spaceAfter=10
    )

    cat_heading_style = ParagraphStyle(
        'CatHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(THEME_BLACK),
        spaceBefore=12,
        spaceAfter=6
    )
    
    cell_header_style = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(THEME_WHITE),
        alignment=1
    )
    
    cell_body_style = ParagraphStyle(
        'BodyCell',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor(THEME_BLACK)
    )

    cell_body_bold = ParagraphStyle(
        'BodyCellBold',
        parent=cell_body_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(THEME_ORANGE)
    )

    bullet_style = ParagraphStyle(
        'BulletItem',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor(THEME_BLACK),
        leftIndent=15,
        spaceAfter=4
    )

    summary_label_style = ParagraphStyle(
        'SummaryLabel',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(THEME_BLACK)
    )

    summary_val_style = ParagraphStyle(
        'SummaryVal',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(THEME_ORANGE)
    )

    # Document Header
    elements.append(Paragraph(title_text, title_style))
    elements.append(Paragraph(f"<b>{subtitle_text}</b> &nbsp;|&nbsp; Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    
    # Accent Bar
    divider_table = Table([['']], colWidths=['100%'], rowHeights=[2])
    divider_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(THEME_ORANGE)),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(divider_table)
    elements.append(Spacer(1, 12))

    if res_df.empty:
        elements.append(Paragraph("No equipment data available to report.", cell_body_style))
    else:
        df_pdf = res_df.copy()
        for col in df_pdf.columns:
            df_pdf[col] = df_pdf[col].astype(str).str.replace("₹", "Rs. ")

        def build_table(sub_df):
            table_data = []
            headers = list(sub_df.columns)
            header_row = [Paragraph(str(h), cell_header_style) for h in headers]
            table_data.append(header_row)

            for _, row in sub_df.iterrows():
                formatted_row = []
                for col in headers:
                    val_str = str(row[col])
                    if any(k in col for k in ["Lowest Unit Price", "Best Unit Price", "Unit Price", "Total Est. Cost", "Best Total Price", "Total Price", "Best Supplier", "Total (Rs. )", "Total (₹)", "Line Total"]):
                        formatted_row.append(Paragraph(val_str, cell_body_bold))
                    else:
                        formatted_row.append(Paragraph(val_str, cell_body_style))
                table_data.append(formatted_row)

            pdf_table = Table(table_data, repeatRows=1)
            pdf_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(THEME_BLACK)),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor(THEME_LIGHT_GREY), colors.HexColor(THEME_WHITE)]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(THEME_GREY)),
            ]))
            return pdf_table

        if group_by_category and "Category" in df_pdf.columns:
            categories = df_pdf["Category"].unique()
            for cat in categories:
                cat_df = df_pdf[df_pdf["Category"] == cat]
                elements.append(Paragraph(str(cat), cat_heading_style))
                for _, item in cat_df.iterrows():
                    eq_name = item.get("Equipment Name", item.get("Name", ""))
                    qty = item.get("Qty", 1)
                    req = item.get("Requirement", "")
                    bullet_text = f"• <b>{eq_name}</b> &nbsp;&nbsp;|&nbsp;&nbsp; <b>Qty:</b> {qty} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Requirement:</b> {req}"
                    elements.append(Paragraph(bullet_text, bullet_style))
                elements.append(Spacer(1, 6))
        else:
            elements.append(build_table(df_pdf))

        if summary_metrics:
            elements.append(Spacer(1, 14))
            sum_data = [
                [Paragraph("<b>Procurement Summary Metric</b>", summary_label_style), Paragraph("<b>Value</b>", summary_label_style)]
            ]
            for label, val in summary_metrics.items():
                val_clean = str(val).replace("₹", "Rs. ")
                sum_data.append([
                    Paragraph(str(label), cell_body_style),
                    Paragraph(str(val_clean), summary_val_style)
                ])
            sum_table = Table(sum_data, colWidths=[250, 200])
            sum_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(THEME_LIGHT_GREY)),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(THEME_ORANGE)),
            ]))
            elements.append(sum_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()