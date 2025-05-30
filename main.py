import os
import io
import json
import base64
import logging
import requests
from flask import Flask, jsonify, send_file, request, send_from_directory
from reportlab.pdfgen import canvas
from dotenv import load_dotenv
import re
from openai import OpenAI

# Load environment and configure
load_dotenv()
# Debug directory for snapshots and API payloads
DEBUG_DIR = os.getenv('DEBUG_DIR', 'debug')
os.makedirs(DEBUG_DIR, exist_ok=True)
# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, static_folder='static')
app.logger.setLevel(logging.DEBUG)

STUB_DATA = [
    {"title": "BUILDING", "description": "40% completed. Last floor progress updated 2h ago."},
    {"title": "FLOOR", "description": "4th floor under construction. Materials delivered this morning."}
]

def analyze_image_openai(image_bytes):
    """
    Alternative image analysis using OpenAI Chat Completions.
    """
    # Prepare base64-encoded image for multimodal input
    client = OpenAI()
    b64 = base64.b64encode(image_bytes).decode('utf-8')
    data_url = f"data:image/jpeg;base64,{b64}"
    # Instruct model to output only JSON array of cards
    system_prompt = (
        "You are an image analysis assistant. Given an image and instructions, "
        "output ONLY a JSON array of analysis cards. Each card must be an object with 'title' and 'description'. "
        "Do not include any additional text, markdown, or explanation."
    )
    user_prompt = (
        "Provide analysis cards covering progress vs RAG documentation, "
        "safety detection (PPE compliance), and budgetary risk & outlier detection."
    )
    # Call ChatCompletion with system and user messages
    completion = client.chat.completions.create(
        model=os.getenv('OPENAI_MODEL', 'gpt-4'),
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': [
                {'type': 'text', 'text': user_prompt},
                {'type': 'image_url', 'image_url': {'url': data_url}}
            ]}
        ],
    )
    content = completion.choices[0].message.content
    app.logger.debug('analyze_image_openai: raw content: %s', content)
    # Clean output from possible code fences
    text = content if isinstance(content, str) else ''
    json_text = re.sub(r'```json', '', text)
    json_text = re.sub(r'```', '', json_text).strip()
    # Parse JSON
    try:
        cards = json.loads(json_text)
        return cards
    except Exception as e:
        app.logger.error('JSON parse error: %s', e, exc_info=True)
        app.logger.debug('analyze_image_openai: cleaned text: %s', json_text)
        # Fallback: wrap raw analysis text in one card
        return [{'title': 'Analysis', 'description': text.strip()}]
    # Prepare base64-encoded image data URL and OpenAI payload
    b64 = base64.b64encode(image_bytes).decode('utf-8')
    data_url = f"data:image/jpeg;base64,{b64}"
    model = os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')
    user_prompt = (
        "Provide a JSON array of analysis cards. Each card must have 'title' and 'description'. "
        "Cover progress vs RAG documentation, safety/PPE detection, and budgetary risk outliers."
    )
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }
        ],
        "max_tokens": 300
    }
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    # Save incoming snapshot for inspection
    try:
        snapshot_path = os.path.join(DEBUG_DIR, 'snapshot.jpg')
        with open(snapshot_path, 'wb') as f:
            f.write(image_bytes)
        app.logger.debug("analyze_image: snapshot saved to %s", snapshot_path)
        # Save the Gemini payload
        payload_path = os.path.join(DEBUG_DIR, 'payload.json')
        with open(payload_path, 'w') as f:
            json.dump(payload, f)
        app.logger.debug("analyze_image: payload saved to %s", payload_path)
    except Exception:
        app.logger.warning("analyze_image: failed to write debug files", exc_info=True)
    # Call Gemini API
    try:
        app.logger.debug("analyze_image: calling Gemini API at %s", url)
        app.logger.debug(
            "analyze_image: image_bytes size=%d bytes, mime_type=%s",
            len(image_bytes), mime_type
        )
        resp = requests.post(url, json=payload)
        # Save raw response
        try:
            resp_path = os.path.join(DEBUG_DIR, 'response_raw.json')
            with open(resp_path, 'w') as f:
                f.write(resp.text)
            app.logger.debug("analyze_image: raw response saved to %s", resp_path)
        except Exception:
            app.logger.warning("analyze_image: failed to write raw response", exc_info=True)
        app.logger.debug("analyze_image: Gemini API status=%s", resp.status_code)
        text = resp.text
        app.logger.debug(
            "analyze_image: Gemini raw response (truncated to 500 chars): %s",
            text[:500]
        )
        resp.raise_for_status()
        result = resp.json()
        parts = result['candidates'][0]['content']['parts']
        text = parts[-1]['text']
        cards = json.loads(text)
        return cards
    except Exception as e:
        app.logger.error("Gemini analysis error: %s", e, exc_info=True)
        return STUB_DATA

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/analysis', methods=['GET', 'POST'])
def analysis():
    # Debug incoming request
    app.logger.debug("/api/analysis called; method=%s", request.method)
    app.logger.debug("Headers: %s", dict(request.headers))
    app.logger.debug("Content-Type: %s", request.content_type)
    app.logger.debug("Form keys: %s", list(request.form.keys()))
    app.logger.debug("Files keys: %s", list(request.files.keys()))
    # Accept an image snapshot for analysis
    if request.method == 'POST':
        if 'snapshot' in request.files:
            file = request.files['snapshot']
            img_bytes = file.read()
            app.logger.debug(
                "/api/analysis POST received: snapshot size=%d bytes",
                len(img_bytes)
            )
            cards = analyze_image_openai(img_bytes)
            app.logger.debug(
                "/api/analysis responding with %d cards: %s",
                len(cards), cards
            )
            return jsonify(cards)
        else:
            app.logger.warning(
                "/api/analysis POST missing 'snapshot' in files"
            )
    # Fallback or GET: return stub data
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