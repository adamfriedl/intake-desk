const submit = document.getElementById('submit');
const message = document.getElementById('message');
const results = document.getElementById('results');
const statusEl = document.getElementById('status');

submit.addEventListener('click', runIntake);

async function runIntake() {
  statusEl.textContent = 'Submitting intake…';
  submit.disabled = true;
  results.classList.add('hidden');
  try {
    const response = await fetch('/api/intake', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: message.value, include_draft: true }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(formatDetail(data.detail) || 'Request failed');
    renderClient(data);
    results.classList.remove('hidden');
    statusEl.textContent = '';
  } catch (error) {
    statusEl.textContent = String(error);
  } finally {
    submit.disabled = false;
  }
}

function formatDetail(detail) {
  if (!detail) return '';
  if (typeof detail === 'string') return detail;
  return JSON.stringify(detail);
}

function renderClient(record) {
  const client = record.client_response;
  const banner = document.getElementById('outcome-banner');
  const pill = document.getElementById('outcome-pill');

  banner.className = 'banner';
  pill.className = 'pill';
  if (client.outcome === 'refuse') {
    banner.classList.add('danger');
    pill.classList.add('bad');
  } else if (client.outcome === 'self_help') {
    banner.classList.add('ok');
    pill.classList.add('ok');
  } else {
    banner.classList.add('warn');
    pill.classList.add('warn');
  }

  const label = client.outcome.replace('_', ' ');
  banner.innerHTML = `<strong>${escapeHtml(client.headline)}</strong>${escapeHtml(client.message)}`;
  pill.textContent = label;

  document.getElementById('headline').textContent = client.headline;
  document.getElementById('message-out').textContent = client.message;

  const selfHelp = document.getElementById('self-help');
  if (client.outcome === 'self_help' && client.answer) {
    selfHelp.classList.remove('hidden');
    document.getElementById('answer').textContent = client.answer;
  } else {
    selfHelp.classList.add('hidden');
  }

  document.getElementById('next-steps').innerHTML = (client.next_steps || [])
    .map((step) => `<li>${escapeHtml(step)}</li>`)
    .join('');

  const staffLink = document.getElementById('staff-link');
  const advocateLink = document.getElementById('advocate-link');
  staffLink.classList.remove('hidden');
  advocateLink.href = `/advocate?session=${record.session_id}`;
  advocateLink.textContent = record.session_id;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}
