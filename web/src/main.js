import './style.css'
import { initStlCanvas } from '../../.github/extensions/stl-canvas/viewer-app.mjs'

const SESSION_TOKEN_KEY = 'stl-canvas-github-token'
const API_HEADERS = {
  Accept: 'application/vnd.github+json',
  'X-GitHub-Api-Version': '2022-11-28',
}

const app = document.querySelector('#app')

app.innerHTML = `
  <div class="page-shell">
    <header class="hero card">
      <div>
        <p class="eyebrow">GitHub Pages + GitHub Actions</p>
        <h1>STL Canvas + Repo Skill Runner</h1>
        <p class="lede">
          Die App rendert STL-Dateien lokal im Browser und startet serverseitige, skill-gestützte
          Repo-Workflows auf GitHub Actions – ohne lokalen Checkout beim Benutzer.
        </p>
      </div>
      <div class="repo-badge" id="repoBadge">Lade Repository-Konfiguration…</div>
    </header>

    <main class="layout">
      <section class="card viewer-card">
        <div class="section-header">
          <div>
            <h2>STL Viewer</h2>
            <p>Bestehende Modelle aus <code>models/</code> bleiben direkt in GitHub Pages sichtbar.</p>
          </div>
        </div>
        <div id="viewerRoot" class="viewer-root"></div>
      </section>

      <section class="card runner-card">
        <div class="section-header">
          <div>
            <h2>Repo Skill Runner</h2>
            <p>
              Nutzt Repo-Skills als Policy-Kontext und führt unterstützte Aufgaben über
              <code>workflow_dispatch</code> in GitHub Actions aus.
            </p>
          </div>
        </div>

        <section class="stack auth-box">
          <div>
            <h3>GitHub verbinden</h3>
            <p class="muted">
              GitHub Pages kann keine Secrets halten. Dieses MVP nutzt deshalb einen GitHub Token im Browser
              (nur <code>sessionStorage</code>), um Workflow Runs im eigenen Account zu starten.
            </p>
          </div>
          <label class="stack field-block">
            <span>GitHub Token</span>
            <input id="tokenInput" type="password" placeholder="github_pat_…" autocomplete="off" spellcheck="false" />
          </label>
          <div class="button-row">
            <button type="button" id="connectBtn">Verbinden</button>
            <button type="button" id="clearTokenBtn" class="secondary">Token löschen</button>
          </div>
          <p class="hint" id="tokenHint">
            Empfohlen: Fine-grained PAT mit mindestens <code>Actions: Read and write</code> und
            <code>Contents: Read-only</code> für dieses Repository.
          </p>
          <div id="authStatus" class="status-panel">Nicht verbunden.</div>
        </section>

        <section class="stack request-box">
          <div>
            <h3>Skill-gestützten Run starten</h3>
            <p class="muted" id="manifestSummary">Lade Skill-Metadaten…</p>
          </div>

          <label class="stack field-block">
            <span>Skill</span>
            <select id="skillSelect"></select>
          </label>

          <div id="skillMeta" class="skill-meta"></div>
          <div id="dynamicFields" class="stack"></div>

          <label class="stack field-block">
            <span>Prompt / Notizen</span>
            <textarea id="promptInput" rows="5" placeholder="Optional: zusätzliche Hinweise für den Workflow-Lauf"></textarea>
          </label>

          <div class="button-row">
            <button type="button" id="dispatchBtn">Workflow starten</button>
            <button type="button" id="refreshBtn" class="secondary">Status aktualisieren</button>
          </div>
          <div id="dispatchStatus" class="status-panel">Noch kein Workflow gestartet.</div>
        </section>

        <section class="stack runs-box">
          <div class="section-header compact">
            <div>
              <h3>Letzte Runs</h3>
              <p class="muted">Es werden bevorzugt die eigenen <code>workflow_dispatch</code>-Runs angezeigt.</p>
            </div>
          </div>
          <div id="runsList" class="runs-list empty">Noch keine Daten geladen.</div>
        </section>
      </section>
    </main>
  </div>
`

initStlCanvas({
  root: document.querySelector('#viewerRoot'),
  viewStorageKey: 'stl-canvas-pages-view-defaults',
})

const state = {
  config: null,
  manifest: null,
  token: sessionStorage.getItem(SESSION_TOKEN_KEY) || '',
  user: null,
  runs: [],
  pollHandle: null,
}

const repoBadge = document.querySelector('#repoBadge')
const tokenInput = document.querySelector('#tokenInput')
const connectBtn = document.querySelector('#connectBtn')
const clearTokenBtn = document.querySelector('#clearTokenBtn')
const authStatus = document.querySelector('#authStatus')
const skillSelect = document.querySelector('#skillSelect')
const skillMeta = document.querySelector('#skillMeta')
const dynamicFields = document.querySelector('#dynamicFields')
const promptInput = document.querySelector('#promptInput')
const dispatchBtn = document.querySelector('#dispatchBtn')
const refreshBtn = document.querySelector('#refreshBtn')
const dispatchStatus = document.querySelector('#dispatchStatus')
const runsList = document.querySelector('#runsList')
const manifestSummary = document.querySelector('#manifestSummary')

tokenInput.value = state.token

function setStatus(node, message, tone = 'neutral') {
  node.textContent = message
  node.dataset.tone = tone
}

function repoSlug() {
  const { owner, repo } = state.config.repository
  return `${owner}/${repo}`
}

function workflowFile() {
  return state.config.workflow.file
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function githubBlobUrl(path) {
  return `https://github.com/${repoSlug()}/blob/${state.config.repository.defaultBranch}/${path}`
}

async function loadJson(url) {
  const res = await fetch(url, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Failed to load ${url}: ${res.status}`)
  return res.json()
}

async function githubRequest(path, options = {}) {
  if (!state.token) throw new Error('GitHub token fehlt.')
  const headers = {
    ...API_HEADERS,
    Authorization: 'Bearer ' + state.token,
    ...(options.headers || {}),
  }
  const res = await fetch(`https://api.github.com${path}`, {
    ...options,
    headers,
  })
  if (res.status === 204) return null
  if (!res.ok) {
    const message = await safeErrorMessage(res)
    throw new Error(message)
  }
  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) return res.json()
  return res.blob()
}

async function safeErrorMessage(res) {
  try {
    const data = await res.json()
    return data.message ? `${data.message} (${res.status})` : `GitHub API error (${res.status})`
  } catch {
    return `GitHub API error (${res.status})`
  }
}

function selectedSkill() {
  return state.manifest.skills.find((skill) => skill.id === skillSelect.value) || state.manifest.skills[0]
}

function renderSkillOptions() {
  skillSelect.innerHTML = state.manifest.skills
    .map((skill) => `<option value="${escapeHtml(skill.id)}">${escapeHtml(skill.name)}</option>`)
    .join('')
  if (!skillSelect.value && state.manifest.skills[0]) skillSelect.value = state.manifest.skills[0].id
  renderSkillDetails()
}

function renderSkillDetails() {
  const skill = selectedSkill()
  if (!skill) return
  skillMeta.innerHTML = `
    <div class="skill-card">
      <p>${escapeHtml(skill.description)}</p>
      <ul>
        <li><strong>Skill-Datei:</strong> <a href="${escapeHtml(githubBlobUrl(skill.source))}" target="_blank" rel="noreferrer">${escapeHtml(skill.source)}</a></li>
        <li><strong>Workflow-Ausgabe:</strong> ${escapeHtml(skill.outputs.join(', '))}</li>
        <li><strong>Hinweis:</strong> ${escapeHtml(skill.limitations)}</li>
      </ul>
    </div>
  `
  dynamicFields.innerHTML = skill.fields
    .map(
      (field) => `
        <label class="stack field-block">
          <span>${escapeHtml(field.label)}${field.required ? ' *' : ''}</span>
          ${renderFieldInput(field)}
          <span class="hint">${escapeHtml(field.help)}</span>
        </label>
      `,
    )
    .join('')
}

function renderFieldInput(field) {
  const value = field.default || ''
  if (field.type === 'number') {
    return `<input data-field="${escapeHtml(field.name)}" type="number" value="${escapeHtml(value)}" placeholder="${escapeHtml(field.placeholder || '')}" ${field.required ? 'required' : ''} />`
  }
  return `<input data-field="${escapeHtml(field.name)}" type="text" value="${escapeHtml(value)}" placeholder="${escapeHtml(field.placeholder || '')}" ${field.required ? 'required' : ''} spellcheck="false" />`
}

function collectInputs() {
  const skill = selectedSkill()
  const inputs = { skill: skill.id, prompt: promptInput.value.trim() }
  for (const field of skill.fields) {
    const node = dynamicFields.querySelector(`[data-field="${field.name}"]`)
    const value = (node?.value || '').trim()
    if (field.required && !value) throw new Error(`Feld „${field.label}“ fehlt.`)
    if (value) inputs[field.name] = value
  }
  return inputs
}

async function connectToken() {
  state.token = tokenInput.value.trim()
  if (!state.token) {
    sessionStorage.removeItem(SESSION_TOKEN_KEY)
    state.user = null
    setStatus(authStatus, 'Token fehlt.', 'warning')
    renderRuns([])
    return
  }
  setStatus(authStatus, 'Prüfe GitHub Token…')
  try {
    const user = await githubRequest('/user')
    state.user = user
    sessionStorage.setItem(SESSION_TOKEN_KEY, state.token)
    setStatus(authStatus, `Verbunden als ${user.login}.`, 'success')
    await refreshRuns()
    ensurePolling()
  } catch (error) {
    sessionStorage.removeItem(SESSION_TOKEN_KEY)
    state.user = null
    state.token = ''
    setStatus(authStatus, `Verbindung fehlgeschlagen: ${error.message}`, 'danger')
    throw error
  }
}

function clearToken() {
  state.token = ''
  state.user = null
  tokenInput.value = ''
  sessionStorage.removeItem(SESSION_TOKEN_KEY)
  if (state.pollHandle) {
    window.clearInterval(state.pollHandle)
    state.pollHandle = null
  }
  setStatus(authStatus, 'Token gelöscht.', 'neutral')
  renderRuns([])
}

async function dispatchWorkflow() {
  const inputs = collectInputs()
  setStatus(dispatchStatus, 'Starte Workflow…')
  await githubRequest(`/repos/${repoSlug()}/actions/workflows/${workflowFile()}/dispatches`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ref: state.config.repository.defaultBranch,
      inputs,
    }),
  })
  setStatus(dispatchStatus, 'Workflow angefordert. Aktualisiere Run-Liste…', 'success')
  await refreshRuns()
}

function formatRunStatus(run) {
  const status = run.status || 'unknown'
  const conclusion = run.conclusion ? ` / ${run.conclusion}` : ''
  return `${status}${conclusion}`
}

function runTone(run) {
  if (run.conclusion === 'success') return 'success'
  if (run.conclusion === 'failure' || run.conclusion === 'cancelled' || run.conclusion === 'timed_out') return 'danger'
  if (run.status === 'in_progress' || run.status === 'queued' || run.status === 'waiting') return 'warning'
  return 'neutral'
}

function renderRuns(runs) {
  if (!runs.length) {
    runsList.className = 'runs-list empty'
    runsList.textContent = state.token ? 'Keine passenden Workflow-Runs gefunden.' : 'Verbinde zuerst GitHub, um Runs zu sehen.'
    return
  }
  runsList.className = 'runs-list'
  runsList.innerHTML = runs
    .map((run) => {
      const artifacts = (run.artifacts || []).map((artifact) => `
        <li>
          <span>${artifact.name}</span>
          <button type="button" data-download="${artifact.archive_download_url}" data-artifact-name="${artifact.name}">Download</button>
        </li>
      `).join('') || '<li>Keine Artefakte.</li>'
      const jobs = (run.jobs || []).map((job) => `<li>${job.name}: ${job.status}${job.conclusion ? ` / ${job.conclusion}` : ''}</li>`).join('') || '<li>Jobdetails noch nicht geladen.</li>'
      return `
        <article class="run-card" data-tone="${runTone(run)}">
          <div class="run-card-header">
            <div>
              <h4>#${run.run_number} · ${run.display_title || run.name}</h4>
              <p>${new Date(run.created_at).toLocaleString('de-DE')} · ${formatRunStatus(run)}</p>
            </div>
            <a href="${run.html_url}" target="_blank" rel="noreferrer">In GitHub öffnen</a>
          </div>
          <p class="run-body"><strong>Skill:</strong> ${run.display_skill || 'unbekannt'}${run.head_branch ? ` · <strong>Ref:</strong> ${run.head_branch}` : ''}</p>
          <details>
            <summary>Jobs</summary>
            <ul class="artifact-list">${jobs}</ul>
          </details>
          <details>
            <summary>Artefakte</summary>
            <ul class="artifact-list">${artifacts}</ul>
          </details>
        </article>
      `
    })
    .join('')
}

async function fetchWorkflowRuns() {
  const actorQuery = state.user ? `&actor=${encodeURIComponent(state.user.login)}` : ''
  const data = await githubRequest(`/repos/${repoSlug()}/actions/workflows/${workflowFile()}/runs?event=workflow_dispatch&per_page=50${actorQuery}`)
  const workflowRuns = data.workflow_runs || []
  const filtered = state.user
    ? workflowRuns.filter((run) => (run.triggering_actor?.login || run.actor?.login) === state.user.login)
    : workflowRuns
  const detailedRuns = await Promise.all(
    filtered.slice(0, 5).map(async (run) => {
      const [artifactsData, jobsData] = await Promise.all([
        githubRequest(`/repos/${repoSlug()}/actions/runs/${run.id}/artifacts`).catch(() => ({ artifacts: [] })),
        githubRequest(`/repos/${repoSlug()}/actions/runs/${run.id}/jobs`).catch(() => ({ jobs: [] })),
      ])
      return {
        ...run,
        display_skill: run.name === state.config.workflow.name ? inferSkillFromTitle(run.display_title) : run.name,
        artifacts: artifactsData.artifacts || [],
        jobs: jobsData.jobs || [],
      }
    }),
  )
  return detailedRuns
}

function inferSkillFromTitle(title = '') {
  const lower = title.toLowerCase()
  const match = state.manifest.skills.find((skill) => lower.includes(skill.id.toLowerCase()))
  return match ? match.name : title || state.config.workflow.name
}

async function refreshRuns() {
  if (!state.token) {
    renderRuns([])
    return
  }
  setStatus(dispatchStatus, 'Lade Workflow-Status…')
  try {
    const runs = await fetchWorkflowRuns()
    state.runs = runs
    renderRuns(runs)
    setStatus(dispatchStatus, runs.length ? 'Workflow-Status aktualisiert.' : 'Noch keine passenden Workflow-Runs gefunden.', 'neutral')
  } catch (error) {
    setStatus(dispatchStatus, `Status konnte nicht geladen werden: ${error.message}`, 'danger')
    renderRuns([])
  }
}

async function downloadArtifact(url, name) {
  try {
    const blob = await githubRequest(url.replace('https://api.github.com', ''))
    const href = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = href
    link.download = `${name}.zip`
    link.click()
    URL.revokeObjectURL(href)
  } catch (error) {
    setStatus(dispatchStatus, `Artefakt-Download fehlgeschlagen: ${error.message}`, 'danger')
  }
}

function ensurePolling() {
  if (state.pollHandle || !state.token) return
  state.pollHandle = window.setInterval(() => {
    refreshRuns().catch(() => {})
  }, 20000)
}

runsList.addEventListener('click', (event) => {
  const button = event.target.closest('[data-download]')
  if (!button) return
  downloadArtifact(button.dataset.download, button.dataset.artifactName)
})

skillSelect.addEventListener('change', renderSkillDetails)
connectBtn.addEventListener('click', () => connectToken().catch(() => {}))
clearTokenBtn.addEventListener('click', clearToken)
dispatchBtn.addEventListener('click', () => dispatchWorkflow().catch((error) => setStatus(dispatchStatus, error.message, 'danger')))
refreshBtn.addEventListener('click', () => refreshRuns())

async function bootstrap() {
  try {
    const [config, manifest] = await Promise.all([
      loadJson('./app-config.json'),
      loadJson('./skills-manifest.json'),
    ])
    state.config = config
    state.manifest = manifest
    repoBadge.textContent = `${repoSlug()} · ${state.config.workflow.name}`
    manifestSummary.textContent = manifest.description
    renderSkillOptions()
    if (state.token) {
      await connectToken()
    } else {
      renderRuns([])
    }
  } catch (error) {
    repoBadge.textContent = 'Konfiguration konnte nicht geladen werden'
    setStatus(authStatus, `Initialisierung fehlgeschlagen: ${error.message}`, 'danger')
    setStatus(dispatchStatus, 'App konnte nicht vollständig initialisiert werden.', 'danger')
  }
}

bootstrap()
