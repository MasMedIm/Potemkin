# Potemkin

## Overview

Potemkin is a hackathon demo application that uses a drone’s live video stream to monitor construction site progress in real time. It displays a video feed alongside periodically updated analysis cards, allows on-demand export of a PDF report, voice-over narration, and simulates calling a responsible party.

## Problem Statement

Visiting a construction site in person can be time-consuming and may allow hidden issues to go unnoticed. Potemkin addresses three core challenges:

- Verify progress visually against RAG (Red-Amber-Green) documentation.
- Detect safety compliance, e.g. protective equipment on workers.
- Identify budgetary risks and outliers (weather delays, supply chain issues, etc.).

**Motto:** On time, on budget, and safe.

## Features

- Live HLS video stream from a drone  
- Periodically fetched analysis cards (e.g., building completion stats)  
- Export a PDF progress report  
- Text-to-speech voice-over of stats  
 - Simulated call endpoint (stub for Twilio integration)  
- Image snapshot analysis using HuggingFace image captioning + OpenAI Chat Completions API (on-demand via 'Get Analysis' button)
- Voice interaction: WebRTC-based real-time speech-to-speech via OpenAI Realtime API, using your latest analysis data and example Q&A for context; voice style configurable via REALTIME_VOICE (default: alloy)

## Getting Started

### Prerequisites

- Python 3.7+  
- pip  

### Installation

1. Clone this repository  
2. Navigate into the project directory  
3. (Optional) Create and activate a virtual environment:  
   ```bash
   python -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\\Scripts\\activate    # Windows
   ```  
4. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```  
5. Copy `.env.example` to `.env` and fill in any credentials for external services. For example:  
  ```ini
  TWILIO_ACCOUNT_SID=...          # (optional) Twilio SID for call simulation
  TWILIO_AUTH_TOKEN=...           # (optional) Twilio Auth Token
  TWILIO_PHONE_NUMBER=...         # (optional) Twilio phone number
  HOST_PORT=63000                 # Host port for Docker mapping (default 5000)
  OPENAI_API_KEY=...              # OpenAI API key for chat completion
  HUGGINGFACE_API_KEY=...         # HuggingFace Inference API key for image captioning
  HUGGINGFACE_MODEL=Salesforce/blip-image-captioning-base  # (optional) caption model, default shown
  ```  

### Running the App

```bash
python main.py   # or: docker-compose up --build
```  
The server will start on http://localhost:5000 (or http://localhost:${HOST_PORT} if using Docker). Open that in your browser to see:
  - Live FLV video stream with a "LIVE" indicator
  - Sidebar goals & dynamic analysis cards (on-demand via 'Get Analysis' button)
  - Export PDF, call simulation, and text-to-speech controls

### Debugging
To trace the snapshot → OpenAI flow:
1. Browser console (F12):
   - Snapshot capture and size logs
   - Sending snapshot to `/api/analysis`
   - Received analysis data
2. Server logs (`docker-compose logs -f potemkin` or host terminal):
   - `/api/analysis` call details (method, headers, form/files keys)
   - Snapshot size received
   - OpenAI API call status and raw content logged
   - Final card JSON returned
   - Final card JSON returned

## Project Structure

```
/  
├── main.py                # Flask backend
├── index.html             # Front-end HTML
├── requirements.txt       # Python dependencies
├── .env.example           # Sample environment variables
├── static
│   ├── css
│   │   └── styles.css
│   └── js
│       └── app.js
└── README.md
```  

## Future Improvements

- Integrate real-time data from drone analytics  
- Replace stubbed call with Twilio or another telephony API  
- User authentication and permissions  
- Persist historical reports  
 
## Docker Compose

To run Potemkin in Docker:

1. Ensure Docker & Docker Compose are installed.
2. Copy `.env.example` to `.env` and fill in credentials as needed.
   You can also set `HOST_PORT` in `.env` to change the host port (default is `5000`).
3. Build and start the service:

   ```bash
   docker-compose up --build
   ```

4. Open http://localhost:${HOST_PORT:-5000} in your browser.

**Note:** The Flask logs inside the container will show addresses like http://127.0.0.1:5000 or http://<container-ip>:5000. Those are internal to the container. To reach the app from your host machine, use http://localhost:${HOST_PORT:-5000} (or the host IP and port you configured via `HOST_PORT`).