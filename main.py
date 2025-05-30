import os
import io
import json
import base64
import logging
from flask import Flask, jsonify, send_file, request, send_from_directory
from reportlab.pdfgen import canvas
from dotenv import load_dotenv
import re
import requests
from openai import OpenAI

# Load environment and configure
load_dotenv()
# Debug directory for snapshots and API payloads
DEBUG_DIR = os.getenv('DEBUG_DIR', 'debug')
os.makedirs(DEBUG_DIR, exist_ok=True)
# Data directory for storing analysis results
DATA_DIR = os.getenv('DATA_DIR', 'data')
os.makedirs(DATA_DIR, exist_ok=True)
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
    Analyze an image using OpenAI's multimodal ChatCompletion API.
    """
    client = OpenAI()
    b64 = base64.b64encode(image_bytes).decode('utf-8')
    data_url = f"data:image/jpeg;base64,{b64}"
    system_prompt = (
        "You are an image analysis assistant specialized in construction site monitoring. "
        "Respond with exactly three cards in a JSON array—each an object with 'title' and 'description' only: "
        "'Progress', 'Safety detection (PPE compliance)', and 'Budgetary risk & outlier detection'. "
        "Do not include any extra text or markdown. "
        "For 'Progress', describe only what you see in the image."
    )
    user_message = {
        "role": "user",
        "content": [
            {"type": "text", "text": "Analyze the following image and produce analysis cards:"},
            {"type": "image_url", "image_url": {"url": data_url}}
        ]
    }
    try:
        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
            messages=[{"role": "system", "content": system_prompt}, user_message],
        )
        content = completion.choices[0].message.content
        app.logger.debug("analyze_image_openai: raw content: %s", content)
        text = content if isinstance(content, str) else ""
        json_text = re.sub(r"```json", "", text)
        json_text = re.sub(r"```", "", json_text).strip()
        cards = json.loads(json_text)
        return cards
    except Exception as e:
        app.logger.error("analyze_image_openai error: %s", e, exc_info=True)
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
            # Persist latest analysis to data directory by appending to run list
            try:
                path = os.path.join(DATA_DIR, 'last_analysis.json')
                runs = []
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        existing = json.load(f)
                    # Determine if existing is a single run or list of runs
                    if isinstance(existing, list):
                        if existing and isinstance(existing[0], list):
                            runs = existing
                        else:
                            runs = [existing]
                runs.append(cards)
                with open(path, 'w') as f:
                    json.dump(runs, f)
                app.logger.debug("Appended analysis. Total runs: %d, saved to %s", len(runs), path)
            except Exception as e:
                app.logger.error("Failed to save analysis data: %s", e)
            return jsonify(cards)
        else:
            app.logger.warning(
                "/api/analysis POST missing 'snapshot' in files"
            )
    # Fallback or GET: return stub data
    return jsonify(STUB_DATA)

@app.route('/api/export-pdf')
def export_pdf():
    # Load latest analysis data (last run) or fallback to stub
    try:
        path = os.path.join(DATA_DIR, 'last_analysis.json')
        with open(path, 'r') as f:
            data = json.load(f)
        # Determine if data is list of runs or single run
        if isinstance(data, list):
            if data and isinstance(data[0], list):
                cards = data[-1]
            elif data and isinstance(data[0], dict):
                cards = data
            else:
                cards = STUB_DATA
        else:
            cards = STUB_DATA
    except Exception:
        cards = STUB_DATA
    # Generate PDF report from cards
    buf = io.BytesIO()
    p = canvas.Canvas(buf)
    width, height = 595, 842
    y = height - 40
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, y, "Construction Progress Report")
    y -= 40
    p.setFont("Helvetica", 12)
    for item in cards:
        text = f"{item.get('title', '')}: {item.get('description', '')}"
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
 
 

@app.route('/api/voice', methods=['POST'])
def voice():
    """
    Handle text-based voice interactions: receive user transcript, include analysis context, and return AI reply.
    """
    data = request.get_json(force=True) or {}
    user_input = data.get('input', '').strip()
    if not user_input:
        return jsonify({'error': 'No input provided'}), 400
    # Load last analysis run as context
    path = os.path.join(DATA_DIR, 'last_analysis.json')
    context = []
    try:
        if os.path.exists(path):
            raw = json.load(open(path, 'r'))
            # pick last run if list of runs
            if isinstance(raw, list):
                if raw and isinstance(raw[0], list):
                    context = raw[-1]
                elif raw and isinstance(raw[0], dict):
                    context = raw
    except Exception:
        context = []
    # Build system prompt
    sys_prompt = (
        "You are an AI assistant specialized in construction site monitoring. "
        f"Here is the latest analysis data: {json.dumps(context)}. "
        "Answer user questions based on this context."
    )
    # Prepare messages
    client = OpenAI()
    messages = [
        {'role': 'system', 'content': sys_prompt},
        {'role': 'user', 'content': user_input}
    ]
    try:
        completion = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o'),
            messages=messages
        )
        reply = completion.choices[0].message.content
        return jsonify({'reply': reply})
    except Exception as e:
        app.logger.error("Voice completion error: %s", e, exc_info=True)
        return jsonify({'error': 'AI completion failed'}), 502

@app.route('/session', methods=['GET'])
def session():
    """
    Mint an ephemeral API key for OpenAI Realtime (WebRTC) sessions.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return jsonify({"error": "Server misconfiguration: OPENAI_API_KEY not set"}), 500
    model = os.getenv('MODEL')
    voice = os.getenv('VOICE')
    if not model or not voice:
        return jsonify({"error": "Server misconfiguration: MODEL or VOICE not set"}), 500
    url = 'https://api.openai.com/v1/realtime/sessions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    payload = { 'model': model, 'voice': voice }
    # Load custom instructions from instructions.txt, if provided
    instr_file = os.getenv('INSTRUCTIONS_FILE', 'instructions.txt')
    try:
        with open(instr_file, 'r', encoding='utf-8') as f:
            instr = f.read().strip()
        if instr:
            payload['instructions'] = instr
    except FileNotFoundError:
        pass
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        return jsonify(resp.json())
    except Exception as e:
        app.logger.error("Failed to create realtime session: %s", e, exc_info=True)
        return jsonify({"error": "Failed to create realtime session"}), 502

if __name__ == '__main__':
    # Internal container port
    port = int(os.getenv("PORT", 5000))
    # External host port (docker-compose HOST_PORT)
    external_port = os.getenv("HOST_PORT", port)
    print(f"* External access via http://localhost:{external_port}")
    app.run(host='0.0.0.0', port=port, debug=True)