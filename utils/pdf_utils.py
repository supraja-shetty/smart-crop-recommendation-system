from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime
import random
import os


def generate_pdf(user, crop, image_path, n, p, k, temp, humidity, ph, rainfall, top3):

    # ---------------- FILE ----------------
    report_id = f"AGR-{random.randint(10000,99999)}"
    filename = f"static/reports/{report_id}.pdf"

    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    elements = []

    # ---------------- TITLE ----------------
    title = Paragraph("CROP RECOMMENDATION REPORT", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 15))

    # ---------------- USER INFO ----------------
    info = f"""
    <b>Report ID:</b> {report_id}<br/>
    <b>User ID:</b> {user}<br/>
    <b>Date:</b> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}
    """
    elements.append(Paragraph(info, styles['Normal']))
    elements.append(Spacer(1, 15))

    # ---------------- INPUT TABLE ----------------
    data = [
        ["Parameter", "Value"],
        ["Nitrogen", n],
        ["Phosphorus", p],
        ["Potassium", k],
        ["Temperature", temp],
        ["Humidity", humidity],
        ["pH", ph],
        ["Rainfall", rainfall]
    ]

    table = Table(data, colWidths=[200, 200])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.darkgreen),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,0), 10),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # ---------------- RESULT ----------------
    result = Paragraph(
        f"<b>RECOMMENDED CROP:</b><br/><font size=20 color='darkgreen'>{crop.upper()}</font>",
        styles['Heading2']
    )
    elements.append(result)
    elements.append(Spacer(1, 15))

    # ---------------- MAIN IMAGE ----------------
    try:
        img = Image(image_path)
        img.drawHeight = 300
        img.drawWidth = 400
        elements.append(img)
    except:
        elements.append(Paragraph("Image not available", styles['Normal']))

    elements.append(Spacer(1, 25))

    # ================= TOP 3 CROPS =================
    elements.append(Paragraph("<b>TOP 3 RECOMMENDED CROPS:</b>", styles['Heading3']))
    elements.append(Spacer(1, 15))

    for i, c in enumerate(top3, start=1):

        elements.append(Paragraph(f"{i}. {c.upper()}", styles['Normal']))
        elements.append(Spacer(1, 5))

        # 👉 image path for each crop
        img_path = f"static/crops/{c.lower()}.jpg"

        if os.path.exists(img_path):
            try:
                crop_img = Image(img_path)
                crop_img.drawHeight = 120
                crop_img.drawWidth = 160
                elements.append(crop_img)
            except:
                elements.append(Paragraph("Image not available", styles['Normal']))
        else:
            elements.append(Paragraph("Image not available", styles['Normal']))

        elements.append(Spacer(1, 15))

    # ---------------- BUILD PDF ----------------
    doc.build(elements)

    return filename