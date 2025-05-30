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
5. Copy `.env.example` to `.env` and fill in any credentials if integrating an external service.  

### Running the App

```bash
python main.py
```  
The server will start on http://localhost:5000. Open that in your browser to see the live stream and analysis feed.

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