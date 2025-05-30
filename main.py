import os
import io
from flask import Flask, jsonify, send_file, request, send_from_directory
from reportlab.pdfgen import canvas
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static')

STUB_DATA = [
    {"title": "BUILDING", "description": "40% completed. Last floor progress updated 2h ago."},
    {"title": "FLOOR", "description": "4th floor under construction. Materials delivered this morning."}
]

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/analysis')
def analysis():
    return jsonify(STUB_DATA)

@app.route('/api/export-pdf')
def export_pdf():
    buf = io.BytesIO()
    p = canvas.Canvas(buf)
    width, height = 595, 842
    y = height - 40
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, y, "Construction Progress Report")
    y -= 40
    p.setFont("Helvetica", 12)
    for item in STUB_DATA:
        text = f"{item['title']}: {item['description']}"
        p.drawString(40, y, text)
        y -= 20
        if y < 40:
            p.showPage()
            y = height - 40
    p.showPage()
    p.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='report.pdf', mimetype='application/pdf')

@app.route('/api/call', methods=['POST'])
def call():
    data = request.get_json(force=True)
    number = data.get('number')
    print(f"Simulating call to {number}")
    return jsonify({"status": "success", "message": f"Simulated call to {number}"})

if __name__ == '__main__':
    # Internal container port
    port = int(os.getenv("PORT", 5000))
    # External host port (docker-compose HOST_PORT)
    external_port = os.getenv("HOST_PORT", port)
    print(f"* External access via http://localhost:{external_port}")
    app.run(host='0.0.0.0', port=port, debug=True)