document.addEventListener('DOMContentLoaded', () => {
  const cardsContainer = document.getElementById('cards-container');
  const exportBtn = document.getElementById('export-btn');
  const callBtn = document.getElementById('call-btn');
  const speakBtn = document.getElementById('speak-btn');
  const analyzeBtn = document.getElementById('analyze-btn');

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

  callBtn.addEventListener('click', async () => {
    const number = prompt('Enter number to call:', '');
    if (!number) return;
    try {
      const resp = await fetch('/api/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ number })
      });
      const result = await resp.json();
      alert(result.message || 'Call simulated');
    } catch (err) {
      console.error('Error calling:', err);
      alert('Error simulating call');
    }
  });

  speakBtn.addEventListener('click', async () => {
    if (!window.speechSynthesis) {
      alert('Speech Synthesis not supported');
      return;
    }
    try {
      console.log('---- speakStats ----');
      console.log('Capturing video snapshot for speech (downscaled)...');
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
      console.log('Snapshot blob size for speech:', blob.size, 'bytes');
      const form = new FormData();
      form.append('snapshot', blob, 'snapshot.jpg');
      console.log('Sending snapshot to /api/analysis for speech');
      const resp = await fetch('/api/analysis', { method: 'POST', body: form });
      if (!resp.ok) throw new Error(`Status ${resp.status}`);
      const data = await resp.json();
      console.log('Received analysis data for speech:', data);
      const utter = new SpeechSynthesisUtterance(
        data.map(item => `${item.title}: ${item.description}`).join('. ')
      );
      speechSynthesis.speak(utter);
    } catch (err) {
      console.error('Error speaking stats', err);
      alert('Error performing speech synthesis');
    }
  });

  // Attach manual analysis trigger
  analyzeBtn.addEventListener('click', fetchAnalysis);
});