document.addEventListener('DOMContentLoaded', () => {
  const cardsContainer = document.getElementById('cards-container');
  const exportBtn = document.getElementById('export-btn');
  const callBtn = document.getElementById('call-btn');
  const speakBtn = document.getElementById('speak-btn');

  async function fetchAnalysis() {
    try {
      const resp = await fetch('/api/analysis');
      if (!resp.ok) throw new Error(`Status ${resp.status}`);
      const data = await resp.json();
      cardsContainer.innerHTML = '';
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
    } catch (err) {
      console.error('Error fetching analysis:', err);
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
      const resp = await fetch('/api/analysis');
      if (!resp.ok) throw new Error();
      const data = await resp.json();
      const utter = new SpeechSynthesisUtterance(
        data.map(item => `${item.title}: ${item.description}`).join('. ')
      );
      speechSynthesis.speak(utter);
    } catch (err) {
      console.error('Error speaking stats', err);
    }
  });

  fetchAnalysis();
  setInterval(fetchAnalysis, 5000);
});