import './style.css'
import { initStlCanvas } from '../../.github/extensions/stl-canvas/viewer-app.mjs'

const TOKEN_STORAGE_KEY = 'stl-canvas-github-token'
const USER_STORAGE_KEY = 'stl-canvas-github-user'
const MODEL_STORAGE_KEY = 'stl-canvas-saved-models'
const WORKSPACE_STORAGE_KEY = 'stl-canvas-image-workspace'
const MAX_STORED_MODEL_JSON_CHARS = 4_000_000
const API_HEADERS = {
  Accept: 'application/vnd.github+json',
  'X-GitHub-Api-Version': '2022-11-28',
}

const app = document.querySelector('#app')
let storedModelsCache = getStoredModels()

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function safeGithubUrl(value, prefix = 'https://github.com/') {
  return typeof value === 'string' && value.startsWith(prefix) ? value : '#'
}

function loadStoredJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function saveStoredJson(key, value) {
  localStorage.setItem(key, JSON.stringify(value))
}

function getStoredModels() {
  const raw = loadStoredJson(MODEL_STORAGE_KEY, [])
  return Array.isArray(raw) ? raw : []
}

function refreshStoredModelsCache() {
  storedModelsCache = getStoredModels()
  return storedModelsCache
}

function decodeBase64(base64) {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i)
  return bytes
}

function encodeBase64(bytes) {
  let out = ''
  const chunkSize = 0x8000
  for (let i = 0; i < bytes.length; i += chunkSize) {
    out += String.fromCharCode(...bytes.subarray(i, i + chunkSize))
  }
  return btoa(out)
}

function fileExtension(name) {
  const match = /\.[^.]+$/.exec(name || '')
  return match ? match[0].toLowerCase() : ''
}

function isModelFile(name) {
  return ['.stl', '.3mf'].includes(fileExtension(name))
}

function isViewerEligibleModel(name) {
  return fileExtension(name) === '.stl'
}

function contentTypeFor(name) {
  switch (fileExtension(name)) {
    case '.stl':
      return 'model/stl'
    case '.3mf':
      return 'application/vnd.ms-package.3dmanufacturing-3dmodel+xml'
    default:
      return 'application/octet-stream'
  }
}

function formatBytes(size) {
  const value = Number(size) || 0
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / (1024 * 1024)).toFixed(2)} MB`
}

function persistStoredModels(models) {
  const next = [...models]
  while (next.length && JSON.stringify(next).length > MAX_STORED_MODEL_JSON_CHARS) next.pop()
  if (models.length && !next.find((entry) => entry.key === models[0].key)) {
    throw new Error('Lokaler Speicher voll. Ältere Modelle löschen oder kleinere Artefakte verwenden.')
  }
  saveStoredJson(MODEL_STORAGE_KEY, next)
  storedModelsCache = next
  return next
}

function upsertStoredModel(record) {
  const current = getStoredModels()
  const next = [record, ...current.filter((entry) => entry.key !== record.key)]
  return persistStoredModels(next)
}

let modelFetchShimInstalled = false
function installModelFetchShim() {
  if (modelFetchShimInstalled) return
  modelFetchShimInstalled = true
  const originalFetch = window.fetch.bind(window)
  window.fetch = async (input, init) => {
    const request = input instanceof Request ? input : new Request(input, init)
    const url = new URL(request.url, window.location.href)
    const method = (request.method || 'GET').toUpperCase()
    const savedModels = storedModelsCache
    const viewerModels = savedModels.filter((entry) => entry.viewerEligible)

    if (url.pathname.endsWith('/models/models.json')) {
      try {
        const response = await originalFetch(input, init)
        const data = response.ok ? await response.clone().json() : { files: [] }
        const files = Array.from(new Set([...(Array.isArray(data.files) ? data.files : []), ...viewerModels.map((entry) => entry.key)])).sort((a, b) => a.localeCompare(b))
        return new Response(JSON.stringify({ ...data, files }), {
          status: response.status,
          headers: { 'Content-Type': 'application/json' },
        })
      } catch {
        return new Response(JSON.stringify({ files: viewerModels.map((entry) => entry.key) }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
    }

    const marker = '/models/'
    const markerIndex = url.pathname.lastIndexOf(marker)
    if (markerIndex >= 0) {
      const requestedFile = decodeURIComponent(url.pathname.slice(markerIndex + marker.length))
      const saved = viewerModels.find((entry) => entry.key === requestedFile)
      if (saved) {
        if (method === 'HEAD') {
          return new Response(null, {
            status: 200,
            headers: {
              'Content-Type': saved.contentType,
              ETag: saved.version,
              'Content-Length': String(saved.size),
            },
          })
        }
        if (method === 'GET') {
          return new Response(decodeBase64(saved.base64), {
            status: 200,
            headers: {
              'Content-Type': saved.contentType,
              ETag: saved.version,
              'Content-Length': String(saved.size),
            },
          })
        }
      }
    }

    return originalFetch(input, init)
  }
}

installModelFetchShim()

app.innerHTML = `
  <div class="page-shell">
    <header class="hero card">
      <div>
        <p class="eyebrow">GitHub Pages + GitHub Actions</p>
        <h1>STL Canvas + Repo Skill Runner</h1>
        <p class="lede">
          Die App rendert STL-Dateien lokal im Browser und startet serverseitige, workflow-gestützte
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
            <p>Bestehende Modelle aus <code>models/</code> und lokal gespeicherte STL-Dateien bleiben direkt im Browser sichtbar.</p>
          </div>
        </div>
        <div id="viewerRoot" class="viewer-root"></div>
      </section>

      <section class="card runner-card">
        <div class="section-header">
          <div>
            <h2>Repo Skill Runner</h2>
            <p>
              Zeigt zugehörige Repo-Skills als Referenz an und führt unterstützte Aufgaben über
              <code>workflow_dispatch</code> in GitHub Actions aus.
            </p>
          </div>
        </div>

        <section class="stack auth-box">
          <div>
            <h3>GitHub verbinden</h3>
            <p class="muted">
              Dieses Setup bleibt backendfrei. Der PAT bleibt nur im <code>sessionStorage</code> des aktuellen Tabs;
              lokal gesicherte Modelldateien und der zuletzt verifizierte Benutzer bleiben im
              <code>localStorage</code>, damit Sessions sicherer fortgesetzt werden können.
            </p>
          </div>
          <div id="storageNotice" class="status-panel" data-tone="warning">
            Beim Verbinden wird der zugehörige GitHub-Benutzer angezeigt; der PAT bleibt nur in dieser Tabsitzung.
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
            <code>Contents: Read and write</code> für dieses Repository.
          </p>
          <div id="authStatus" class="status-panel">Nicht verbunden.</div>
        </section>

        <section class="stack upload-box">
          <div class="section-header compact">
            <div>
              <h3>Bild-Workspace</h3>
              <p class="muted">
                In privaten Repositories kann die App Referenzbilder ohne Backend in einen
                benutzereigenen GitHub-Branch hochladen, damit das Image-Workflow-Profil sie verwenden kann.
              </p>
            </div>
          </div>
          <div id="workspaceStatus" class="status-panel">Noch kein Bild-Workspace initialisiert.</div>
          <label class="stack field-block">
            <span>Referenzbilder hochladen</span>
            <input id="imageUploadInput" type="file" accept="image/*" multiple />
          </label>
          <div class="button-row">
            <button type="button" id="uploadImagesBtn">Bilder nach GitHub hochladen</button>
            <button type="button" id="useWorkspaceDirBtn" class="secondary">Ordner für Bild-Workflow verwenden</button>
          </div>
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
            <textarea id="promptInput" rows="5" placeholder="Optional: zusätzliche Hinweise; werden mit dem Run gespeichert, steuern das MVP aber nicht direkt"></textarea>
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

        <section class="stack saved-box">
          <div class="section-header compact">
            <div>
              <h3>Lokale Modellablage</h3>
              <p class="muted">Gespeicherte STL/3MF-Dateien aus Workflow-Artefakten zum Fortsetzen späterer Sessions.</p>
            </div>
            <button type="button" id="clearSavedModelsBtn" class="secondary">Modelle löschen</button>
          </div>
          <div id="savedModelsList" class="runs-list empty">Noch keine lokal gespeicherten Modelldateien.</div>
        </section>
      </section>
    </main>
  </div>
`

const state = {
  config: null,
  buildInfo: null,
  manifest: null,
  token: sessionStorage.getItem(TOKEN_STORAGE_KEY) || '',
  user: loadStoredJson(USER_STORAGE_KEY, null),
  runs: [],
  runDetails: new Map(),
  savedModels: getStoredModels(),
  workspace: loadStoredJson(WORKSPACE_STORAGE_KEY, null),
  pollHandle: null,
}

const repoBadge = document.querySelector('#repoBadge')
const tokenInput = document.querySelector('#tokenInput')
const connectBtn = document.querySelector('#connectBtn')
const clearTokenBtn = document.querySelector('#clearTokenBtn')
const clearSavedModelsBtn = document.querySelector('#clearSavedModelsBtn')
const imageUploadInput = document.querySelector('#imageUploadInput')
const uploadImagesBtn = document.querySelector('#uploadImagesBtn')
const useWorkspaceDirBtn = document.querySelector('#useWorkspaceDirBtn')
const storageNotice = document.querySelector('#storageNotice')
const workspaceStatus = document.querySelector('#workspaceStatus')
const authStatus = document.querySelector('#authStatus')
const skillSelect = document.querySelector('#skillSelect')
const skillMeta = document.querySelector('#skillMeta')
const dynamicFields = document.querySelector('#dynamicFields')
const promptInput = document.querySelector('#promptInput')
const dispatchBtn = document.querySelector('#dispatchBtn')
const refreshBtn = document.querySelector('#refreshBtn')
const dispatchStatus = document.querySelector('#dispatchStatus')
const runsList = document.querySelector('#runsList')
const savedModelsList = document.querySelector('#savedModelsList')
const manifestSummary = document.querySelector('#manifestSummary')

tokenInput.value = state.token

initStlCanvas({
  root: document.querySelector('#viewerRoot'),
  viewStorageKey: 'stl-canvas-pages-view-defaults',
})

function setStatus(node, message, tone = 'neutral') {
  node.textContent = message
  node.dataset.tone = tone
}

function updateStorageNotice() {
  const savedCount = state.savedModels.length
  const userLabel = state.user?.login ? ` Benutzer: ${state.user.login}.` : ''
  const tokenLabel = state.token ? ' PAT nur für diese Tabsitzung gespeichert.' : ' Kein PAT gespeichert.'
  const workspaceLabel = state.workspace?.imageDir ? ` Bild-Workspace: ${state.workspace.imageDir}.` : ' Kein Bild-Workspace gespeichert.'
  setStatus(storageNotice, `Lokale Session:${userLabel}${tokenLabel}${workspaceLabel} Gespeicherte Modelldateien: ${savedCount}.`, state.token ? 'success' : 'warning')
}

function renderWorkspaceStatus() {
  if (!imageUploadsAllowed()) {
    setStatus(
      workspaceStatus,
      'Bild-Uploads sind in diesem öffentlichen Repository deaktiviert, damit Benutzerfotos nicht öffentlich im Git-Verlauf landen.',
      'warning',
    )
    return
  }
  if (!state.workspace?.imageDir) {
    setStatus(workspaceStatus, 'Noch kein Bild-Workspace initialisiert.', 'warning')
    return
  }
  const fileCount = Array.isArray(state.workspace.files) ? state.workspace.files.length : 0
  setStatus(
    workspaceStatus,
    `Branch: ${state.workspace.branch} · Ordner: ${state.workspace.imageDir} · Dateien: ${fileCount}`,
    'success',
  )
}

function applyWorkspaceFieldDefaults() {
  if (!state.workspace?.imageDir) return
  const skill = selectedSkill()
  if (!skill || skill.id !== 'stl-from-image-measurements') return
  const node = [...dynamicFields.querySelectorAll('[data-field]')].find((element) => element.dataset.field === 'image_dir')
  if (node) node.value = state.workspace.imageDir
}

function repoSlug() {
  const { owner, repo } = state.config.repository
  return `${owner}/${repo}`
}

function workflowFile() {
  return state.config.workflow.file
}

function currentWorkflowRef() {
  return state.buildInfo?.workflowRef || state.config.repository.defaultBranch
}

function currentWorkspaceBranch() {
  if (!state.manifest) return null
  const skill = selectedSkill()
  const imageDirNode = dynamicFields
    ? [...dynamicFields.querySelectorAll('[data-field]')].find((element) => element.dataset.field === 'image_dir')
    : null
  const usesWorkspace =
    skill?.id === 'stl-from-image-measurements' &&
    state.workspace?.userLogin === state.user?.login &&
    typeof imageDirNode?.value === 'string' &&
    imageDirNode.value.trim().startsWith(state.config.workspace.imageRoot + '/')
  return usesWorkspace ? state.workspace.branch : null
}

function workspaceBranchName(login) {
  return `${state.config.workspace.branchPrefix}/${login}`
}

function workspaceImageDir(login, sessionId) {
  return `${state.config.workspace.imageRoot}/${login}/${sessionId}`
}

function sanitizePathSegment(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80) || 'upload'
}

function imageUploadsAllowed() {
  return state.config?.repository?.visibility === 'private'
}

function githubBlobUrl(path) {
  return `https://github.com/${repoSlug()}/blob/${state.config.repository.defaultBranch}/${path}`
}

function selectedSkill() {
  if (!state.manifest?.skills?.length) return null
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
  applyWorkspaceFieldDefaults()
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
  if (!skill) throw new Error('App wird noch initialisiert. Bitte kurz erneut versuchen.')
  const inputs = { skill: skill.id, prompt: promptInput.value.trim() }
  for (const field of skill.fields) {
    const node = [...dynamicFields.querySelectorAll('[data-field]')].find((element) => element.dataset.field === field.name)
    const value = (node?.value || '').trim()
    if (field.required && !value) throw new Error(`Feld „${field.label}“ fehlt.`)
    if (value) inputs[field.name] = value
  }
  return inputs
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
    const error = new Error(message)
    error.status = res.status
    throw error
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

async function githubRequestOptional(path, options = {}) {
  try {
    return await githubRequest(path, options)
  } catch (error) {
    if (String(error.message).includes('(404)')) return null
    throw error
  }
}

async function readFileAsBase64(file) {
  const buffer = await file.arrayBuffer()
  return encodeBase64(new Uint8Array(buffer))
}

async function ensureWorkspaceBranch(login) {
  const branch = workspaceBranchName(login)
  const existing = await githubRequestOptional(`/repos/${repoSlug()}/git/ref/heads/${encodeURIComponent(branch)}`)
  if (existing) return branch
  const base = await githubRequest(`/repos/${repoSlug()}/git/ref/heads/${state.config.repository.defaultBranch}`)
  await githubRequest(`/repos/${repoSlug()}/git/refs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ref: `refs/heads/${branch}`,
      sha: base.object.sha,
    }),
  })
  return branch
}

async function uploadImagesToWorkspace() {
  if (!imageUploadsAllowed()) {
    throw new Error('Bild-Uploads sind für dieses öffentliche Repository deaktiviert.')
  }
  if (!state.user?.login || !state.token) throw new Error('Bitte zuerst einen GitHub-Token verbinden.')
  const files = [...(imageUploadInput.files || [])]
  if (!files.length) throw new Error('Bitte mindestens ein Bild auswählen.')

  const branch = await ensureWorkspaceBranch(state.user.login)
  const sessionId = new Date().toISOString().replace(/[:.]/g, '-')
  const imageDir = workspaceImageDir(state.user.login, sessionId)
  const uploaded = []

  for (const [index, file] of files.entries()) {
    const safeName = `${String(index + 1).padStart(2, '0')}-${sanitizePathSegment(file.name.replace(/\.[^.]+$/, ''))}${fileExtension(file.name) || '.bin'}`
    await githubRequest(`/repos/${repoSlug()}/contents/${imageDir}/${safeName}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: `Upload reference image ${safeName}`,
        content: await readFileAsBase64(file),
        branch,
      }),
    })
    uploaded.push({
      name: safeName,
      size: file.size,
      uploadedAt: new Date().toISOString(),
    })
  }

  state.workspace = {
    branch,
    imageDir,
    files: uploaded,
    userLogin: state.user.login,
    updatedAt: new Date().toISOString(),
  }
  saveStoredJson(WORKSPACE_STORAGE_KEY, state.workspace)
  imageUploadInput.value = ''
  renderWorkspaceStatus()
  updateStorageNotice()
  renderSkillDetails()
  setStatus(dispatchStatus, `${uploaded.length} Bilddatei(en) nach ${imageDir} auf ${branch} hochgeladen.`, 'success')
}

async function connectToken() {
  state.token = tokenInput.value.trim()
  if (!state.token) {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY)
    localStorage.removeItem(USER_STORAGE_KEY)
    state.user = null
    setStatus(authStatus, 'Token fehlt.', 'warning')
    renderRuns([])
    updateStorageNotice()
    return
  }
  setStatus(authStatus, 'Prüfe GitHub Token…')
  try {
    const user = await githubRequest('/user')
    state.user = { login: user.login, id: user.id }
    if (state.workspace?.userLogin && state.workspace.userLogin !== user.login) {
      state.workspace = null
      localStorage.removeItem(WORKSPACE_STORAGE_KEY)
      renderSkillDetails()
    }
    sessionStorage.setItem(TOKEN_STORAGE_KEY, state.token)
    saveStoredJson(USER_STORAGE_KEY, state.user)
    setStatus(authStatus, `Verbunden als ${user.login}. PAT bleibt nur in dieser Tabsitzung; lokale Modelle bleiben im Browser gespeichert.`, 'success')
    renderWorkspaceStatus()
    updateStorageNotice()
    await refreshRuns()
    ensurePolling()
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      sessionStorage.removeItem(TOKEN_STORAGE_KEY)
      localStorage.removeItem(USER_STORAGE_KEY)
      state.user = null
      state.token = ''
      tokenInput.value = ''
    }
    updateStorageNotice()
    setStatus(authStatus, `Verbindung fehlgeschlagen: ${error.message}`, 'danger')
    throw error
  }
}

function clearToken() {
  state.token = ''
  state.user = null
  tokenInput.value = ''
  sessionStorage.removeItem(TOKEN_STORAGE_KEY)
  localStorage.removeItem(USER_STORAGE_KEY)
  if (state.pollHandle) {
    window.clearInterval(state.pollHandle)
    state.pollHandle = null
  }
  updateStorageNotice()
  setStatus(authStatus, 'Token gelöscht. Gespeicherte Modelldateien bleiben erhalten.', 'neutral')
  renderRuns([])
}

async function dispatchWorkflow() {
  const inputs = collectInputs()
  const workspaceBranch = currentWorkspaceBranch()
  if (workspaceBranch) inputs.workspace_branch = workspaceBranch
  setStatus(dispatchStatus, 'Starte Workflow…')
  await githubRequest(`/repos/${repoSlug()}/actions/workflows/${workflowFile()}/dispatches`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ref: currentWorkflowRef(),
      inputs,
    }),
  })
  const sourceNote = workspaceBranch ? ` Bildquelle: ${workspaceBranch}.` : ''
  setStatus(dispatchStatus, `Workflow auf ${currentWorkflowRef()} angefordert.${sourceNote} Aktualisiere Run-Liste…`, 'success')
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
      const cached = state.runDetails.get(run.id)
      if (cached?.updatedAt && cached.updatedAt !== run.updated_at) state.runDetails.delete(run.id)
      const details = state.runDetails.get(run.id) || { artifacts: null, jobs: null }
      const runUrl = safeGithubUrl(run.html_url)
      const artifacts = Array.isArray(details.artifacts)
        ? details.artifacts.map((artifact) => `
        <li>
          <span>${escapeHtml(artifact.name)}</span>
          <button type="button" data-download="${escapeHtml(safeGithubUrl(artifact.archive_download_url, 'https://api.github.com/'))}" data-artifact-name="${escapeHtml(artifact.name)}" data-run-id="${escapeHtml(run.id)}">Download</button>
        </li>
      `).join('') || '<li>Keine Artefakte.</li>'
        : '<li>Zum Laden öffnen.</li>'
      const jobs = Array.isArray(details.jobs)
        ? details.jobs.map((job) => `<li>${escapeHtml(job.name)}: ${escapeHtml(job.status)}${job.conclusion ? ` / ${escapeHtml(job.conclusion)}` : ''}</li>`).join('') || '<li>Keine Jobs gefunden.</li>'
        : '<li>Zum Laden öffnen.</li>'
      return `
        <article class="run-card" data-tone="${runTone(run)}">
          <div class="run-card-header">
            <div>
              <h4>#${escapeHtml(run.run_number)} · ${escapeHtml(run.display_title || run.name)}</h4>
              <p>${escapeHtml(new Date(run.created_at).toLocaleString('de-DE'))} · ${escapeHtml(formatRunStatus(run))}</p>
            </div>
            <a href="${escapeHtml(runUrl)}" target="_blank" rel="noreferrer">In GitHub öffnen</a>
          </div>
          <p class="run-body"><strong>Skill:</strong> ${escapeHtml(run.display_skill || 'unbekannt')}${run.head_branch ? ` · <strong>Ref:</strong> ${escapeHtml(run.head_branch)}` : ''}</p>
          <details data-run-id="${escapeHtml(run.id)}" data-detail-kind="jobs">
            <summary>Jobs</summary>
            <ul class="artifact-list" id="run-jobs-${escapeHtml(run.id)}">${jobs}</ul>
          </details>
          <details data-run-id="${escapeHtml(run.id)}" data-detail-kind="artifacts">
            <summary>Artefakte</summary>
            <ul class="artifact-list" id="run-artifacts-${escapeHtml(run.id)}">${artifacts}</ul>
          </details>
        </article>
      `
    })
    .join('')
}

function renderSavedModels() {
  state.savedModels = refreshStoredModelsCache()
  updateStorageNotice()
  if (!state.savedModels.length) {
    savedModelsList.className = 'runs-list empty'
    savedModelsList.textContent = 'Noch keine lokal gespeicherten Modelldateien.'
    return
  }
  savedModelsList.className = 'runs-list'
  savedModelsList.innerHTML = state.savedModels.map((model) => `
    <article class="run-card">
      <div class="run-card-header">
        <div>
          <h4>${escapeHtml(model.displayName)}</h4>
          <p>${escapeHtml(model.userLogin || 'unbekannt')} · ${escapeHtml(model.sourceArtifact || 'Artefakt')} · ${escapeHtml(new Date(model.savedAt).toLocaleString('de-DE'))}</p>
        </div>
        <span>${escapeHtml(formatBytes(model.size))}</span>
      </div>
      <p class="run-body"><strong>Datei:</strong> ${escapeHtml(model.key)}</p>
      <div class="button-row compact-row">
        ${model.viewerEligible ? `<button type="button" data-open-model="${escapeHtml(model.key)}">Im Viewer öffnen</button>` : ''}
        <button type="button" data-download-model="${escapeHtml(model.key)}">Herunterladen</button>
        <button type="button" class="secondary" data-delete-model="${escapeHtml(model.key)}">Löschen</button>
      </div>
    </article>
  `).join('')
}

async function fetchWorkflowRuns() {
  const actorQuery = state.user ? `&actor=${encodeURIComponent(state.user.login)}` : ''
  const branchQuery = `&branch=${encodeURIComponent(currentWorkflowRef())}`
  const data = await githubRequest(`/repos/${repoSlug()}/actions/workflows/${workflowFile()}/runs?event=workflow_dispatch&per_page=50${actorQuery}${branchQuery}`)
  const workflowRuns = data.workflow_runs || []
  const filtered = state.user
    ? workflowRuns.filter((run) => (run.triggering_actor?.login || run.actor?.login) === state.user.login)
    : workflowRuns
  return filtered.filter((run) => run.head_branch === currentWorkflowRef()).slice(0, 5).map((run) => ({
    ...run,
    display_skill: run.name === state.config.workflow.name ? inferSkillFromTitle(run.display_title) : run.name,
  }))
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

async function loadRunDetails(runId) {
  const run = state.runs.find((entry) => String(entry.id) === String(runId))
  if (!run) return
  const cached = state.runDetails.get(run.id)
  if (cached?.updatedAt === run.updated_at && Array.isArray(cached.jobs) && Array.isArray(cached.artifacts)) return
  const jobsNode = document.querySelector(`#run-jobs-${CSS.escape(String(run.id))}`)
  const artifactsNode = document.querySelector(`#run-artifacts-${CSS.escape(String(run.id))}`)
  if (jobsNode) jobsNode.innerHTML = '<li>Lade…</li>'
  if (artifactsNode) artifactsNode.innerHTML = '<li>Lade…</li>'
  try {
    const [artifactsData, jobsData] = await Promise.all([
      githubRequest(`/repos/${repoSlug()}/actions/runs/${run.id}/artifacts`).catch(() => ({ artifacts: [] })),
      githubRequest(`/repos/${repoSlug()}/actions/runs/${run.id}/jobs`).catch(() => ({ jobs: [] })),
    ])
    state.runDetails.set(run.id, {
      updatedAt: run.updated_at,
      artifacts: artifactsData.artifacts || [],
      jobs: jobsData.jobs || [],
    })
    renderRuns(state.runs)
  } catch (error) {
    if (jobsNode) jobsNode.innerHTML = `<li>${escapeHtml(error.message)}</li>`
    if (artifactsNode) artifactsNode.innerHTML = `<li>${escapeHtml(error.message)}</li>`
  }
}

function findZipEndOfCentralDirectory(bytes) {
  for (let index = bytes.length - 22; index >= Math.max(0, bytes.length - 0xffff - 22); index -= 1) {
    if (bytes[index] === 0x50 && bytes[index + 1] === 0x4b && bytes[index + 2] === 0x05 && bytes[index + 3] === 0x06) return index
  }
  throw new Error('ZIP-Ende nicht gefunden.')
}

async function inflateDeflateRaw(bytes) {
  if (typeof DecompressionStream === 'undefined') throw new Error('Browser unterstützt kein lokales ZIP-Entpacken.')
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw'))
  return new Uint8Array(await new Response(stream).arrayBuffer())
}

async function extractModelFilesFromZip(blob) {
  const buffer = await blob.arrayBuffer()
  const bytes = new Uint8Array(buffer)
  const view = new DataView(buffer)
  const eocd = findZipEndOfCentralDirectory(bytes)
  const totalEntries = view.getUint16(eocd + 10, true)
  const centralDirectoryOffset = view.getUint32(eocd + 16, true)
  const decoder = new TextDecoder('utf-8')
  const entries = []
  let pointer = centralDirectoryOffset

  for (let i = 0; i < totalEntries; i += 1) {
    if (view.getUint32(pointer, true) !== 0x02014b50) throw new Error('Ungültiger ZIP-Central-Directory-Eintrag.')
    const compressionMethod = view.getUint16(pointer + 10, true)
    const compressedSize = view.getUint32(pointer + 20, true)
    const uncompressedSize = view.getUint32(pointer + 24, true)
    const fileNameLength = view.getUint16(pointer + 28, true)
    const extraLength = view.getUint16(pointer + 30, true)
    const commentLength = view.getUint16(pointer + 32, true)
    const localHeaderOffset = view.getUint32(pointer + 42, true)
    const fileNameBytes = bytes.slice(pointer + 46, pointer + 46 + fileNameLength)
    const name = decoder.decode(fileNameBytes)
    entries.push({ name, compressionMethod, compressedSize, uncompressedSize, localHeaderOffset })
    pointer += 46 + fileNameLength + extraLength + commentLength
  }

  const models = []
  for (const entry of entries) {
    if (!isModelFile(entry.name) || entry.name.endsWith('/')) continue
    if (view.getUint32(entry.localHeaderOffset, true) !== 0x04034b50) throw new Error('Ungültiger ZIP-Local-Header.')
    const fileNameLength = view.getUint16(entry.localHeaderOffset + 26, true)
    const extraLength = view.getUint16(entry.localHeaderOffset + 28, true)
    const dataStart = entry.localHeaderOffset + 30 + fileNameLength + extraLength
    const compressed = bytes.slice(dataStart, dataStart + entry.compressedSize)
    let content
    if (entry.compressionMethod === 0) content = compressed
    else if (entry.compressionMethod === 8) content = await inflateDeflateRaw(compressed)
    else throw new Error(`ZIP-Komprimierung ${entry.compressionMethod} wird nicht unterstützt.`)
    models.push({ name: entry.name, content, size: entry.uncompressedSize || content.length })
  }
  return models
}

async function cacheModelsFromArtifact(blob, artifactName, runId) {
  const run = state.runs.find((entry) => String(entry.id) === String(runId))
  const extracted = await extractModelFilesFromZip(blob)
  if (!extracted.length) return 0
  let storedCount = 0
  for (const file of extracted) {
    const leafName = file.name.split('/').pop()
    const namespacedKey = `saved/${run?.run_number || 'run'}-${leafName}`
    state.savedModels = upsertStoredModel({
      key: namespacedKey,
      displayName: leafName,
      base64: encodeBase64(file.content),
      contentType: contentTypeFor(leafName),
      size: file.size,
      savedAt: new Date().toISOString(),
      sourceArtifact: artifactName,
      runId: String(runId || ''),
      runNumber: run?.run_number || null,
      userLogin: state.user?.login || '',
      version: `${run?.updated_at || Date.now()}-${file.size}`,
      viewerEligible: isViewerEligibleModel(leafName),
    })
    storedCount += 1
  }
  renderSavedModels()
  return storedCount
}

async function downloadArtifact(url, name, runId) {
  try {
    const blob = await githubRequest(url.replace('https://api.github.com', ''))
    let cacheMessage = ''
    try {
      const storedCount = await cacheModelsFromArtifact(blob, name, runId)
      if (storedCount) cacheMessage = ` ${storedCount} Modelldatei(en) lokal gespeichert.`
    } catch (error) {
      cacheMessage = ` Lokales Sichern übersprungen: ${error.message}`
    }
    const href = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = href
    link.download = `${name}.zip`
    link.click()
    URL.revokeObjectURL(href)
    setStatus(dispatchStatus, `Artefakt ${name} heruntergeladen.${cacheMessage}`.trim(), 'success')
  } catch (error) {
    setStatus(dispatchStatus, `Artefakt-Download fehlgeschlagen: ${error.message}`, 'danger')
  }
}

function downloadSavedModel(key) {
  const model = state.savedModels.find((entry) => entry.key === key)
  if (!model) return
  const blob = new Blob([decodeBase64(model.base64)], { type: model.contentType })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = model.displayName
  link.click()
  URL.revokeObjectURL(link.href)
}

function openSavedModelInViewer(key) {
  const chooser = document.querySelector('#viewerRoot #fileChooser')
  if (!chooser) {
    setStatus(dispatchStatus, 'Viewer-Dateiauswahl nicht gefunden. Bitte Seite neu laden und erneut versuchen.', 'warning')
    return
  }
  if (![...chooser.options].some((option) => option.value === key)) {
    chooser.add(new Option(key, key))
  }
  chooser.value = key
  chooser.dispatchEvent(new Event('change', { bubbles: true }))
  setStatus(dispatchStatus, `Lokales Modell ${key} im Viewer geöffnet.`, 'success')
}

function deleteSavedModel(key) {
  state.savedModels = refreshStoredModelsCache().filter((entry) => entry.key !== key)
  saveStoredJson(MODEL_STORAGE_KEY, state.savedModels)
  storedModelsCache = state.savedModels
  renderSavedModels()
}

function clearSavedModels() {
  state.savedModels = []
  localStorage.removeItem(MODEL_STORAGE_KEY)
  storedModelsCache = []
  renderSavedModels()
}

function useWorkspaceDirForImageSkill() {
  if (!state.manifest?.skills) {
    setStatus(dispatchStatus, 'App wird noch initialisiert. Bitte kurz erneut versuchen.', 'warning')
    return
  }
  if (!state.workspace?.imageDir) {
    setStatus(dispatchStatus, 'Noch kein Bild-Workspace vorhanden.', 'warning')
    return
  }
  skillSelect.value = 'stl-from-image-measurements'
  renderSkillDetails()
  const node = [...dynamicFields.querySelectorAll('[data-field]')].find((element) => element.dataset.field === 'image_dir')
  if (node) node.value = state.workspace.imageDir
  setStatus(dispatchStatus, `Bild-Workflow auf ${state.workspace.imageDir} vorbereitet.`, 'success')
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
  downloadArtifact(button.dataset.download, button.dataset.artifactName, button.dataset.runId)
})

runsList.addEventListener('toggle', (event) => {
  const details = event.target
  if (!(details instanceof HTMLDetailsElement) || !details.open || !details.dataset.runId) return
  loadRunDetails(details.dataset.runId).catch(() => {})
}, true)

savedModelsList.addEventListener('click', (event) => {
  const openButton = event.target.closest('[data-open-model]')
  if (openButton) {
    openSavedModelInViewer(openButton.dataset.openModel)
    return
  }
  const downloadButton = event.target.closest('[data-download-model]')
  if (downloadButton) {
    downloadSavedModel(downloadButton.dataset.downloadModel)
    return
  }
  const deleteButton = event.target.closest('[data-delete-model]')
  if (deleteButton) deleteSavedModel(deleteButton.dataset.deleteModel)
})

skillSelect.addEventListener('change', renderSkillDetails)
connectBtn.addEventListener('click', () => connectToken().catch(() => {}))
clearTokenBtn.addEventListener('click', clearToken)
clearSavedModelsBtn.addEventListener('click', clearSavedModels)
uploadImagesBtn.addEventListener('click', () => uploadImagesToWorkspace().catch((error) => setStatus(dispatchStatus, error.message, 'danger')))
useWorkspaceDirBtn.addEventListener('click', useWorkspaceDirForImageSkill)
dispatchBtn.addEventListener('click', () => dispatchWorkflow().catch((error) => setStatus(dispatchStatus, error.message, 'danger')))
refreshBtn.addEventListener('click', () => refreshRuns())

async function bootstrap() {
  try {
    const [config, buildInfo, manifest] = await Promise.all([
      loadJson('./app-config.json'),
      loadJson('./build-info.json').catch(() => null),
      loadJson('./skills-manifest.json'),
    ])
    state.config = config
    state.buildInfo = buildInfo
    state.manifest = manifest
    if (!imageUploadsAllowed()) {
      state.workspace = null
      localStorage.removeItem(WORKSPACE_STORAGE_KEY)
      imageUploadInput.disabled = true
      uploadImagesBtn.disabled = true
      useWorkspaceDirBtn.disabled = true
    }
    repoBadge.textContent = `${repoSlug()} · ${state.config.workflow.name} · ref ${currentWorkflowRef()}`
    manifestSummary.textContent = manifest.description
    renderSkillOptions()
    renderSavedModels()
    renderWorkspaceStatus()
    if (state.user?.login && state.token) {
      setStatus(authStatus, `PAT in dieser Tabsitzung gefunden. Letzter Benutzer: ${state.user.login}.`, 'warning')
      try {
        await connectToken()
      } catch {
        updateStorageNotice()
        renderRuns([])
      }
    } else {
      updateStorageNotice()
      renderRuns([])
    }
  } catch (error) {
    repoBadge.textContent = 'Konfiguration konnte nicht geladen werden'
    setStatus(authStatus, `Initialisierung fehlgeschlagen: ${error.message}`, 'danger')
    setStatus(dispatchStatus, 'App konnte nicht vollständig initialisiert werden.', 'danger')
  }
}

bootstrap()
