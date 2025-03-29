from flask_cors import CORS
from flask import Flask, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from io import BytesIO
import re
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
@app.route("/", methods=["GET"])
def index():
    return "떨림 PDF API 서버가 작동 중입니다. /generate 로 POST 요청하세요."

FONT_PATH = "NanumGothic.ttf"
pdfmetrics.registerFont(TTFont("NanumGothic", FONT_PATH))

def split_lyrics(raw):
    pattern = r'\n?\s*(\d+)\.\s*(.+?)\s*\n'
    matches = list(re.finditer(pattern, raw))
    sections = []
    for i in range(len(matches)):
        start = matches[i].end()
        end = matches[i+1].start() if i+1 < len(matches) else len(raw)
        title = matches[i].group(2).strip()
        body = raw[start:end].strip()
        sections.append((title, body))
    return sections

@app.route("/generate", methods=["POST"])
def generate_pdf():
    data = request.get_json()
    lyrics = data.get("lyrics", "")
    print("🔥 수신한 lyrics 내용:", lyrics)    
    sections = split_lyrics(lyrics)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setFont("NanumGothic", 18)

    # 표지
    pdf.drawCentredString(A4[0]/2, A4[1]/2, "그렇게, 우주를 노래하다")
    pdf.setFont("NanumGothic", 12)
    pdf.drawCentredString(A4[0]/2, A4[1]/2 - 40, "AI와 사람이 함께 만든 노랫말")
    pdf.showPage()

    # 목차
    pdf.setFont("NanumGothic", 14)
    pdf.drawString(40, A4[1] - 50, "목차")
    y = A4[1] - 80
    for i, (title, _) in enumerate(sections, 1):
        pdf.drawString(50, y, f"{i}. {title}")
        y -= 25
        if y < 50:
            pdf.showPage()
            y = A4[1] - 50

    pdf.showPage()

    # 본문 (2단 구성)
    margin = 30 * mm
    col_width = (A4[0] - 2 * margin - 10 * mm) / 2
    line_height = 14
    for i, (title, body) in enumerate(sections, 1):
        text = f"{i}. {title}\n{body}"
        lines = text.split("\n")
        x = margin
        y = A4[1] - margin
        col = 0
        pdf.setFont("NanumGothic", 12)
        for line in lines:
            pdf.drawString(x + col * (col_width + 10 * mm), y, line.strip())
            y -= line_height
            if y < margin:
                col += 1
                y = A4[1] - margin
                if col > 1:
                    pdf.showPage()
                    col = 0
        pdf.showPage()

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="떨림.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
