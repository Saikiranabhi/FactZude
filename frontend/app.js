const verifyBtn      = document.getElementById('verifyBtn');
const claimInput     = document.getElementById('claimInput');
const charHint       = document.getElementById('charHint');

const emptyState     = document.getElementById('emptyState');
const loadingState   = document.getElementById('loadingState');
const errorState     = document.getElementById('errorState');
const resultState    = document.getElementById('resultState');

const verdictCard    = document.getElementById('verdictCard');
const verdictIcon    = document.getElementById('verdictIcon');
const verdictWord    = document.getElementById('verdictWord');
const confNumber     = document.getElementById('confNumber');
const confFill       = document.getElementById('confFill');
const claimDisplay   = document.getElementById('claimDisplay');
const explanationDiv = document.getElementById('explanationDiv');
const sourcesList    = document.getElementById('sourcesList');

const ICONS  = { TRUE: '✓', FALSE: '✕', UNCERTAIN: '~' };
const LABELS = { TRUE: 'True', FALSE: 'False', UNCERTAIN: 'Uncertain' };

/* Character counter */
claimInput.addEventListener('input', () => {
  charHint.textContent = claimInput.value.length + ' characters';
});

/* Show only one right-panel state at a time */
function showOnly(id) {
  [emptyState, loadingState, resultState].forEach(el => {
    el.style.display = 'none';
  });
  if (id) {
    document.getElementById(id).style.display = 'flex';
  }
}

/* Verify button click */
verifyBtn.addEventListener('click', async () => {
  const claim = claimInput.value.trim();

  if (!claim) {
    errorState.textContent = 'Please enter a claim first.';
    errorState.style.display = 'block';
    return;
  }

  errorState.style.display = 'none';
  showOnly('loadingState');
  verifyBtn.disabled = true;

  try {
    const res = await fetch('https://factzude-2.onrender.com/fact-check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ claim })
    });

    if (!res.ok) {
      const e = await res.json();
      throw new Error(e.detail || 'Server error');
    }

    const data = await res.json();
    renderResult(claim, data);

  } catch (err) {
    showOnly(null);
    emptyState.style.display = 'flex';
    errorState.textContent = 'Error: ' + err.message;
    errorState.style.display = 'block';

  } finally {
    verifyBtn.disabled = false;
  }
});

/* Render result into the right panel */
function renderResult(claim, data) {
  const v   = (data.verdict || 'Uncertain').toUpperCase();
  const cls = v === 'TRUE' ? 'v-true' : v === 'FALSE' ? 'v-false' : 'v-uncertain';
  const pct = Math.round((data.confidence || 0) * 100);

  // Verdict card
  verdictCard.className   = 'verdict-card ' + cls;
  verdictIcon.textContent = ICONS[v]  || '?';
  verdictWord.textContent = LABELS[v] || 'Uncertain';
  confNumber.textContent  = pct + '%';

  // Animate confidence bar
  confFill.style.width = '0%';
  setTimeout(() => { confFill.style.width = pct + '%'; }, 80);

  // Text content
  claimDisplay.textContent   = claim;
  explanationDiv.textContent = data.explanation || 'No explanation provided.';

  // Sources list
  sourcesList.innerHTML = '';
  const srcs = (data.sources && data.sources.length) ? data.sources : [];

  if (srcs.length) {
    srcs.forEach(s => {
      const li = document.createElement('li');
      li.innerHTML = `
        <a href="${s.url || '#'}" target="_blank" rel="noopener">
          <span class="src-dot"></span>
          <span class="src-title">${s.title || s.url || 'Source'}</span>
          <span class="src-arr">↗</span>
        </a>`;
      sourcesList.appendChild(li);
    });
  } else {
    sourcesList.innerHTML = '<li style="font-size:13px;color:rgba(255,255,255,0.3);padding:4px 0;">No sources available.</li>';
  }

  showOnly('resultState');
}
