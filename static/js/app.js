document.addEventListener('DOMContentLoaded', () => {
  const cardsContainer = document.getElementById('cards-container');
  const analyzeBtn = document.getElementById('analyze-btn');
  const exportBtn = document.getElementById('export-btn');
  const voiceBtn = document.getElementById('voice-btn');

  async function fetchAnalysis() {
    analyzeBtn.disabled = true;
    cardsContainer.innerHTML = '<div class="loading">Loading analysis...</div>';
    console.log('---- fetchAnalysis ----');
    try {
      console.log('Capturing video snapshot (downscaled)...');
      const video = document.getElementById('liveVideo');
      const maxDim = 512;
      const vw = video.videoWidth;
      const vh = video.videoHeight;
      const scale = Math.min(maxDim / vw, maxDim / vh, 1);
      const canvas = document.createElement('canvas');
      canvas.width = Math.floor(vw * scale);
      canvas.height = Math.floor(vh * scale);
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg'));
      console.log('Snapshot blob size:', blob.size, 'bytes');
      const form = new FormData();
      form.append('snapshot', blob, 'snapshot.jpg');
      console.log('Sending snapshot to /api/analysis');
      const resp = await fetch('/api/analysis', {
        method: 'POST',
        body: form
      });
      if (!resp.ok) throw new Error(`Status ${resp.status}`);
      const data = await resp.json();
      console.log('Received analysis data:', data);
      cardsContainer.innerHTML = '';
      if (Array.isArray(data) && data.length > 0) {
        data.forEach(item => {
          const card = document.createElement('div');
          card.className = 'card';
          const title = document.createElement('strong');
          title.textContent = item.title;
          const desc = document.createElement('p');
          desc.style.fontSize = '0.9em';
          desc.textContent = item.description;
          card.appendChild(title);
          card.appendChild(desc);
          cardsContainer.appendChild(card);
        });
      } else {
        cardsContainer.innerHTML = '<div class="no-results">No analysis available.</div>';
      }
    } catch (err) {
      console.error('Error fetching analysis:', err);
      cardsContainer.innerHTML = '<div class="error">Error fetching analysis.</div>';
    } finally {
      analyzeBtn.disabled = false;
    }
  }

  exportBtn.addEventListener('click', () => {
    window.location.href = '/api/export-pdf';
  });



  // Attach manual analysis trigger
  analyzeBtn.addEventListener('click', fetchAnalysis);
  // Voice interaction: WebRTC real-time speech-to-speech via OpenAI Realtime API
  voiceBtn.addEventListener('click', async () => {
    voiceBtn.disabled = true;
    try {
      // 1. Get an ephemeral key from our server
      const tokenRes = await fetch('/session');
      if (!tokenRes.ok) throw new Error(`Session error: ${tokenRes.status}`);
      const tokenData = await tokenRes.json();
      const EPHEMERAL_KEY = tokenData.client_secret?.value;
      const model = tokenData.model;
      if (!EPHEMERAL_KEY || !model) throw new Error('Invalid session data');
      // 2. Create peer connection
      const pc = new RTCPeerConnection();
      // 3. Play remote audio from model
      const audioEl = document.createElement('audio');
      audioEl.autoplay = true;
      document.body.appendChild(audioEl);
      pc.ontrack = e => { audioEl.srcObject = e.streams[0]; };
      // 4. Add local microphone track
      const ms = await navigator.mediaDevices.getUserMedia({ audio: true });
      pc.addTrack(ms.getTracks()[0], ms);
      // 5. Data channel for events
      const dc = pc.createDataChannel('oai-events');
      dc.addEventListener('message', e => {
        console.log('Realtime event:', e);
      });
      // 6. SDP offer/answer exchange
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      const baseUrl = 'https://api.openai.com/v1/realtime';
      const sdpRes = await fetch(`${baseUrl}?model=${model}`, {
        method: 'POST',
        body: offer.sdp,
        headers: {
          'Authorization': `Bearer ${EPHEMERAL_KEY}`,
          'Content-Type': 'application/sdp'
        }
      });
      if (!sdpRes.ok) throw new Error(`SDP exchange error: ${sdpRes.status}`);
      const answer = { type: 'answer', sdp: await sdpRes.text() };
      await pc.setRemoteDescription(answer);
      console.log('Voice session established');
    } catch (err) {
      console.error('Voice interaction failed:', err);
      alert('Voice session error: ' + err.message);
    } finally {
      voiceBtn.disabled = false;
    }
  });
});