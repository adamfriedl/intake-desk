const loadBtn = document.getElementById('load-session');
const sessionInput = document.getElementById('session-id');
const results = document.getElementById('results');
const statusEl = document.getElementById('status');
let session = null;

loadBtn.addEventListener('click', loadSession);
document.getElementById('approve-all').addEventListener('click', approveAll);

const params = new URLSearchParams(window.location.search);
if (params.get('session')) {
  sessionInput.value = params.get('session');
  loadSession();
}

async function loadSession() {
  const id = sessionInput.value.trim();
  if (!id) return;
  statusEl.textContent = 'Loading case file...';
  try {
    const response = await fetch(`/api/sessions/${encodeURIComponent(id)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Session not found');
    session = data;
    renderSession(session);
    results.classList.remove('hidden');
    statusEl.textContent = '';
  } catch (error) {
    statusEl.textContent = String(error);
  }
}

function renderSession(record) {
  const cf = record.case_file;
  document.getElementById('case-file').innerHTML = `
    <div><strong>Session:</strong> ${escapeHtml(cf.session_id)}</div>
    <div><span class="pill">${escapeHtml(cf.matter_type)}</span>
         <span class="pill">${escapeHtml(cf.triage)}</span>
         <span class="pill">urgency ${escapeHtml(cf.urgency)}</span>
         ${cf.human_review_required ? '<span class="pill warn">human review</span>' : ''}
         ${cf.jurisdiction_missing ? '<span class="pill warn">jurisdiction missing</span>' : ''}
    </div>
    <div><strong>Routing:</strong> ${escapeHtml(cf.routing)}</div>
    <div><strong>Jurisdiction:</strong> ${escapeHtml(cf.jurisdiction || 'unknown')}</div>
    <div><strong>Parties:</strong> ${escapeHtml((cf.parties || []).join(', ') || '—')}</div>
    <div><strong>Facts:</strong></div>
    <ul>${(cf.facts || []).map((f) => `<li>${escapeHtml(f)}</li>`).join('') || '<li class="muted">—</li>'}</ul>
    <p class="muted">${escapeHtml(cf.classification_rationale || '')}</p>
  `;

  const answer = cf.grounded_answer;
  document.getElementById('answer').innerHTML = answer
    ? `<div>${linkifyCitations(answer)}</div>`
    : '<p class="muted">No grounded answer (refused or escalated before client delivery).</p>';

  renderCitations(cf.citations || []);
  renderSections(record.reviewed_sections || []);
  document.getElementById('audit').textContent = JSON.stringify(
    record.pipeline.audit_log,
    null,
    2,
  );
  document.getElementById('chunk-panel').classList.add('hidden');
}

function linkifyCitations(text) {
  return escapeHtml(text).replace(
    /\[([a-z0-9._:-]+)\]/gi,
    (_, id) =>
      `<button type="button" class="citation inline" data-chunk="${id}">[${id}]</button>`,
  );
}

function renderCitations(citations) {
  const container = document.getElementById('citations');
  container.innerHTML = citations.length
    ? citations
        .map(
          (c) => `
        <button type="button" class="citation" data-chunk="${escapeHtml(c.chunk_id)}">
          <strong>${escapeHtml(c.chunk_id)}</strong> — ${escapeHtml(c.source)}
          <div class="muted">${escapeHtml(c.quoted_span)}</div>
        </button>`,
        )
        .join('')
    : '<p class="muted">No citations.</p>';

  container.querySelectorAll('[data-chunk]').forEach((el) => {
    el.addEventListener('click', () => loadChunk(el.dataset.chunk));
  });
  document
    .getElementById('answer')
    .querySelectorAll('[data-chunk]')
    .forEach((el) => el.addEventListener('click', () => loadChunk(el.dataset.chunk)));
}

async function loadChunk(chunkId) {
  const panel = document.getElementById('chunk-panel');
  panel.classList.remove('hidden');
  panel.textContent = 'Loading...';
  try {
    const response = await fetch(`/api/chunks/${encodeURIComponent(chunkId)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Not found');
    panel.innerHTML = `
      <strong>${escapeHtml(data.chunk_id)}</strong> — ${escapeHtml(data.source)}
      ${data.source_url ? `<div><a href="${escapeHtml(data.source_url)}" target="_blank" rel="noopener">Primary source</a></div>` : ''}
      <pre class="raw">${escapeHtml(data.text)}</pre>`;
  } catch (error) {
    panel.textContent = String(error);
  }
}

function renderSections(sections) {
  const container = document.getElementById('sections');
  if (!sections.length) {
    container.innerHTML = '<p class="muted">No draft sections.</p>';
    return;
  }
  container.innerHTML = sections
    .map(
      (section) => `
    <div class="card" data-index="${section.index}">
      <div class="section-status pill ${statusClass(section.review_status)}">${escapeHtml(section.review_status)}</div>
      <h3>${escapeHtml(section.title)}</h3>
      <textarea class="section-content">${escapeHtml(section.content)}</textarea>
      <div class="section-actions">
        <button type="button" data-action="approve">Approve</button>
        <button type="button" data-action="save">Save edit</button>
        <button type="button" data-action="reject">Reject</button>
      </div>
    </div>`,
    )
    .join('');

  container.querySelectorAll('.card').forEach((card) => {
    const index = Number(card.dataset.index);
    card.querySelector('[data-action="approve"]').addEventListener('click', () =>
      patchSection(index, { review_status: 'approved' }),
    );
    card.querySelector('[data-action="reject"]').addEventListener('click', () =>
      patchSection(index, { review_status: 'rejected' }),
    );
    card.querySelector('[data-action="save"]').addEventListener('click', () => {
      const content = card.querySelector('.section-content').value;
      patchSection(index, { content, review_status: 'edited' });
    });
  });
}

function statusClass(status) {
  if (status === 'approved') return 'ok';
  if (status === 'rejected') return 'bad';
  if (status === 'edited') return 'warn';
  return '';
}

async function patchSection(index, body) {
  if (!session) return;
  const response = await fetch(`/api/review/${session.session_id}/sections/${index}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) {
    statusEl.textContent = data.detail || 'Update failed';
    return;
  }
  session = data;
  renderSession(session);
}

async function approveAll() {
  if (!session) return;
  const response = await fetch(`/api/review/${session.session_id}/approve-all`, {
    method: 'POST',
  });
  const data = await response.json();
  if (!response.ok) {
    statusEl.textContent = data.detail || 'Approve failed';
    return;
  }
  session = data;
  renderSession(session);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}
