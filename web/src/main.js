import './style.css'
import { initStlCanvas } from '../../.github/extensions/stl-canvas/viewer-app.mjs'
import {
  STORE_FILES,
  STORE_IMAGES,
  STORE_MODELS,
  clearStore,
  deleteRecord,
  estimateUsage,
  getRecord,
  listRecords,
  migrateLegacyModels,
  putRecord,
} from './storage.mjs'
import { buildContactSheet, buildImageContextBlock, describeImage } from './images.mjs'

const TOKEN_STORAGE_KEY = 'stl-canvas-github-token'
const USER_STORAGE_KEY = 'stl-canvas-github-user'
const JOURNAL_STORAGE_KEY = 'stl-canvas-run-journal'
const LEGACY_MODEL_STORAGE_KEY = 'stl-canvas-saved-models'
const LEGACY_WORKSPACE_STORAGE_KEY = 'stl-canvas-image-workspace'
const JOURNAL_LIMIT = 40
const API_HEADERS = {
  Accept: 'application/vnd.github+json',
  'X-GitHub-Api-Version': '2022-11-28',
}

const app = document.querySelector('#app')

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
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // The journal is a convenience cache; losing it must never break a run.
  }
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
    case '.png':
      return 'image/png'
    case '.json':
      return 'application/json'
    case '.md':
    case '.txt':
    case '.patch':
      return 'text/plain'
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

function sanitizePathSegment(value) {
  return (
    String(value || '')
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9._-]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 80) || 'datei'
  )
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
    const viewerModels = state.models.filter((entry) => entry.viewerEligible)

    if (url.pathname.endsWith('/models/models.json')) {
      try {
        const response = await originalFetch(input, init)
        const data = response.ok ? await response.clone().json() : { files: [] }
        const files = Array.from(
          new Set([...(Array.isArray(data.files) ? data.files : []), ...viewerModels.map((entry) => entry.key)]),
        ).sort((a, b) => a.localeCompare(b))
        return new Response(JSON.stringify({ ...data, files }), {
          status: 200,
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
      if (saved && (method === 'GET' || method === 'HEAD')) {
        const headers = {
          'Content-Type': saved.contentType,
          ETag: saved.version,
          'Content-Length': String(saved.size),
        }
        if (method === 'HEAD') return new Response(null, { status: 200, headers })
        const record = await getRecord(STORE_MODELS, requestedFile)
        if (record?.blob) return new Response(record.blob, { status: 200, headers })
      }
    }

    return originalFetch(input, init)
  }
}

const state = {
  config: null,
  buildInfo: null,
  manifest: null,
  token: sessionStorage.getItem(TOKEN_STORAGE_KEY) || '',
  user: loadStoredJson(USER_STORAGE_KEY, null),
  runs: [],
  runDetails: new Map(),
  models: [],
  files: [],
  images: [],
  journal: loadStoredJson(JOURNAL_STORAGE_KEY, {}),
  openDetails: new Set(),
  targetOwner: null,
  setupReady: false,
  pollHandle: null,
}

installModelFetchShim()

app.innerHTML = `
  <div class="page-shell">
    <header class="hero card">
      <div>
        <p class="eyebrow">GitHub Pages + GitHub Actions + Copilot</p>
        <h1 id="appTitle">3d-printing - create and adjust models with GH-Copilot</h1>
        <p class="lede" id="appTagline">
          Modelle im Browser ansehen und per GitHub Copilot in einer GitHub-Action erzeugen oder anpassen –
          ohne lokalen Checkout und ohne Schreibrechte auf das Repository.
        </p>
      </div>
      <div class="repo-badge" id="repoBadge">Lade Repository-Konfiguration…</div>
    </header>

    <main class="layout">
      <section class="card viewer-card">
        <div class="section-header">
          <div>
            <h2>STL Viewer</h2>
            <p>Modelle aus <code>models/</code> und lokal gespeicherte Ergebnisse aus Copilot-Runs.</p>
          </div>
        </div>
        <div id="viewerRoot" class="viewer-root"></div>
      </section>

      <section class="card runner-card">
        <div class="section-header">
          <div>
            <h2>Copilot-Run</h2>
            <p>
              Beschreibe in normaler Sprache, was Copilot tun soll. Der Auftrag läuft als GitHub-Action im
              vollständigen Repository – mit allen Skripten und allen Repo-Skills.
            </p>
          </div>
        </div>

        <section class="stack auth-box">
          <div>
            <h3>GitHub verbinden</h3>
            <p class="muted">
              Backendfrei: der PAT bleibt nur im <code>sessionStorage</code> dieses Tabs. Bilder und Modelle liegen
              in der IndexedDB des Browsers und verlassen den Rechner nicht.
            </p>
          </div>
          <div id="storageNotice" class="status-panel" data-tone="warning">Noch nicht verbunden.</div>
          <label class="stack field-block">
            <span>GitHub Token</span>
            <input id="tokenInput" type="password" placeholder="github_pat_…" autocomplete="off" spellcheck="false" />
          </label>
          <div class="button-row">
            <button type="button" id="connectBtn">Verbinden</button>
            <button type="button" id="clearTokenBtn" class="secondary">Token löschen</button>
          </div>
          <p class="hint" id="tokenHint">Lade Token-Anforderungen…</p>
          <div id="setupHint" class="status-panel" hidden></div>
          <div id="authStatus" class="status-panel">Nicht verbunden.</div>
        </section>

        <section class="stack request-box">
          <div class="section-header compact">
            <div>
              <h3>Auftrag an Copilot</h3>
              <p class="muted" id="manifestSummary">Lade Skill-Metadaten…</p>
            </div>
          </div>

          <div class="button-row" id="promptExamples"></div>

          <label class="stack field-block">
            <span>Prompt</span>
            <textarea id="promptInput" rows="10" placeholder="z. B. Validiere models/lineal-clip-kappe.stl und melde Überhänge über 45°, oder: Erzeuge einen neuen Generator für eine Kabelklemme mit 12 mm Innendurchmesser und 3 mm Wandstärke."></textarea>
          </label>
          <p class="hint" id="promptCounter"></p>

          <label class="stack field-block">
            <span>Modell (optional)</span>
            <input id="modelInput" type="text" placeholder="leer lassen für Standardmodell" spellcheck="false" />
            <span class="hint">Wird als <code>--model</code> an die Copilot CLI weitergereicht.</span>
          </label>

          <div class="button-row">
            <button type="button" id="dispatchBtn">Copilot starten</button>
            <button type="button" id="refreshBtn" class="secondary">Status aktualisieren</button>
          </div>
          <div id="dispatchStatus" class="status-panel">Noch kein Run gestartet.</div>
        </section>

        <section class="stack upload-box">
          <div class="section-header compact">
            <div>
              <h3>Referenzbilder</h3>
              <p class="muted">
                Bilder bleiben im Browser (IndexedDB) und werden nie ins Repository geschrieben. Das Kontaktblatt
                nummeriert sie, damit du im Prompt auf Kacheln verweisen kannst.
              </p>
            </div>
            <button type="button" id="clearImagesBtn" class="secondary">Bilder löschen</button>
          </div>
          <div id="imageStatus" class="status-panel">Noch keine Bilder gespeichert.</div>
          <label class="stack field-block">
            <span>Bilder hinzufügen</span>
            <input id="imageUploadInput" type="file" accept="image/*" multiple />
          </label>
          <div class="button-row">
            <button type="button" id="contactSheetBtn" class="secondary">Kontaktblatt erzeugen</button>
            <button type="button" id="appendImageContextBtn" class="secondary">Bildkontext an Prompt anhängen</button>
          </div>
          <div id="imageList" class="runs-list empty">Noch keine Bilder gespeichert.</div>
        </section>

        <section class="stack runs-box">
          <div class="section-header compact">
            <div>
              <h3>Letzte Runs</h3>
              <p class="muted">Eigene <code>workflow_dispatch</code>-Runs inklusive Artefakten.</p>
            </div>
          </div>
          <div id="runsList" class="runs-list empty">Noch keine Daten geladen.</div>
        </section>

        <section class="stack saved-box">
          <div class="section-header compact">
            <div>
              <h3>Lokale Ergebnisse</h3>
              <p class="muted">Modelle und Berichte aus heruntergeladenen Artefakten.</p>
            </div>
            <button type="button" id="clearSavedModelsBtn" class="secondary">Ergebnisse löschen</button>
          </div>
          <div id="savedModelsList" class="runs-list empty">Noch keine lokal gespeicherten Dateien.</div>
        </section>

        <section class="stack skills-box">
          <div class="section-header compact">
            <div>
              <h3>Immer aktive Skills</h3>
              <p class="muted">Copilot wählt selbst aus – eine Auswahl im UI ist nicht nötig.</p>
            </div>
          </div>
          <div id="skillList" class="skill-card">Lade Skills…</div>
        </section>
      </section>
    </main>
  </div>
`

const repoBadge = document.querySelector('#repoBadge')
const appTitle = document.querySelector('#appTitle')
const appTagline = document.querySelector('#appTagline')
const tokenInput = document.querySelector('#tokenInput')
const tokenHint = document.querySelector('#tokenHint')
const connectBtn = document.querySelector('#connectBtn')
const clearTokenBtn = document.querySelector('#clearTokenBtn')
const clearSavedModelsBtn = document.querySelector('#clearSavedModelsBtn')
const clearImagesBtn = document.querySelector('#clearImagesBtn')
const imageUploadInput = document.querySelector('#imageUploadInput')
const contactSheetBtn = document.querySelector('#contactSheetBtn')
const appendImageContextBtn = document.querySelector('#appendImageContextBtn')
const imageStatus = document.querySelector('#imageStatus')
const imageList = document.querySelector('#imageList')
const storageNotice = document.querySelector('#storageNotice')
const authStatus = document.querySelector('#authStatus')
const setupHint = document.querySelector('#setupHint')
const promptExamples = document.querySelector('#promptExamples')
const promptInput = document.querySelector('#promptInput')
const promptCounter = document.querySelector('#promptCounter')
const modelInput = document.querySelector('#modelInput')
const dispatchBtn = document.querySelector('#dispatchBtn')
const refreshBtn = document.querySelector('#refreshBtn')
const dispatchStatus = document.querySelector('#dispatchStatus')
const runsList = document.querySelector('#runsList')
const savedModelsList = document.querySelector('#savedModelsList')
const manifestSummary = document.querySelector('#manifestSummary')
const skillList = document.querySelector('#skillList')

tokenInput.value = state.token

initStlCanvas({
  root: document.querySelector('#viewerRoot'),
  viewStorageKey: 'stl-canvas-pages-view-defaults',
})

const PROMPT_EXAMPLES = [
  {
    label: 'Modell prüfen',
    prompt:
      'Validiere models/lineal-clip-kappe.stl: Wasserdichtheit, Normalen, degenerierte Facetten und Überhänge über 45°. Fasse die Ergebnisse zusammen und nenne konkrete Druckempfehlungen.',
  },
  {
    label: 'Für Druck optimieren',
    prompt:
      'Analysiere models/duschscharnier_ersatz.stl für den Anycubic Kobra S1 und schlage die beste Druckorientierung vor. Ermittle Materialbedarf bei 20 % Infill. Ändere die Generator-Ausgabe nicht, sondern liefere nur Berichte.',
  },
  {
    label: 'Neues Teil erzeugen',
    prompt:
      'Erzeuge einen neuen parametrischen Generator unter scripts/ für <Teil beschreiben> mit folgenden gemessenen Maßen: <Maße in mm>. Exportiere das Ergebnis als ASCII-STL nach models/ und validiere es anschließend.',
  },
  {
    label: 'Bestehendes Teil ändern',
    prompt:
      'Passe scripts/lineal_clip_kappe.py so an, dass <Änderung beschreiben>. Regeneriere das STL, validiere es und erkläre, welche Parameter du geändert hast.',
  },
]

function setStatus(node, message, tone = 'neutral') {
  node.textContent = message
  node.dataset.tone = tone
}

function promptLimit() {
  const { chunkSize = 1024, maxChunks = 12 } = state.config?.prompt || {}
  return chunkSize * maxChunks
}

function chunkPrompt(text) {
  const { chunkSize = 1024, maxChunks = 12 } = state.config?.prompt || {}
  const chunks = []
  for (let index = 0; index < text.length; index += chunkSize) {
    chunks.push(text.slice(index, index + chunkSize))
  }
  if (chunks.length > maxChunks) {
    throw new Error(`Prompt ist zu lang: ${text.length} von maximal ${chunkSize * maxChunks} Zeichen.`)
  }
  return chunks
}

function updatePromptCounter() {
  const length = promptInput.value.length
  const limit = promptLimit()
  promptCounter.textContent = `${length} / ${limit} Zeichen`
  promptCounter.dataset.tone = length > limit ? 'danger' : 'neutral'
}

async function updateStorageNotice() {
  const userLabel = state.user?.login ? ` Benutzer: ${state.user.login}.` : ''
  const tokenLabel = state.token ? ' PAT nur in dieser Tabsitzung.' : ' Kein PAT gespeichert.'
  const usage = await estimateUsage()
  const usageLabel = usage?.quota
    ? ` Browser-Speicher: ${formatBytes(usage.usage)} von ${formatBytes(usage.quota)}.`
    : ''
  setStatus(
    storageNotice,
    `Lokale Session:${userLabel}${tokenLabel} Bilder: ${state.images.length}. Ergebnisdateien: ${
      state.models.length + state.files.length
    }.${usageLabel}`,
    state.token ? 'success' : 'warning',
  )
}

function forkMode() {
  return state.config?.execution?.mode === 'fork'
}

function upstreamSlug() {
  const { owner, repo } = state.config.repository
  return `${owner}/${repo}`
}

function repoSlug() {
  const { owner, repo } = state.config.repository
  if (forkMode()) return `${state.targetOwner || owner}/${repo}`
  return `${owner}/${repo}`
}

function workflowFile() {
  return state.config.workflow.file
}

function currentWorkflowRef() {
  return state.buildInfo?.workflowRef || state.config.repository.defaultBranch
}

function dispatchRef() {
  // In fork mode the upstream build SHA does not exist in the user's fork.
  if (forkMode()) return state.config.repository.defaultBranch
  return currentWorkflowRef()
}

function githubBlobUrl(path) {
  return `https://github.com/${upstreamSlug()}/blob/${state.buildInfo?.commit || currentWorkflowRef()}/${path}`
}

function renderSkillList() {
  const skills = state.manifest?.skills || []
  if (!skills.length) {
    skillList.textContent = 'Keine Skills gefunden.'
    return
  }
  skillList.innerHTML = `
    <ul>
      ${skills
        .map(
          (skill) => `
        <li>
          <a href="${escapeHtml(githubBlobUrl(skill.source))}" target="_blank" rel="noreferrer"><strong>${escapeHtml(skill.name)}</strong></a>
          <br />${escapeHtml(skill.description)}
        </li>
      `,
        )
        .join('')}
    </ul>
  `
}

function renderPromptExamples() {
  promptExamples.innerHTML = PROMPT_EXAMPLES.map(
    (example, index) => `<button type="button" class="secondary" data-example="${index}">${escapeHtml(example.label)}</button>`,
  ).join('')
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
    Authorization: `Bearer ${state.token}`,
    ...(options.headers || {}),
  }
  const res = await fetch(`https://api.github.com${path}`, { ...options, headers })
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

async function connectToken() {
  state.token = tokenInput.value.trim()
  if (!state.token) {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY)
    localStorage.removeItem(USER_STORAGE_KEY)
    state.user = null
    state.targetOwner = null
    state.setupReady = false
    setStatus(authStatus, 'Token fehlt.', 'warning')
    renderRuns([])
    await updateStorageNotice()
    return
  }
  setStatus(authStatus, 'Prüfe GitHub Token…')
  try {
    const user = await githubRequest('/user')
    state.user = { login: user.login, id: user.id }
    if (forkMode()) state.targetOwner = user.login
    sessionStorage.setItem(TOKEN_STORAGE_KEY, state.token)
    saveStoredJson(USER_STORAGE_KEY, state.user)
    updateRepoBadge()
    updateTokenHint()
    setStatus(authStatus, `Verbunden als ${user.login}.`, 'success')
    await updateStorageNotice()
    await verifyTargetRepository()
    if (forkMode() && !state.setupReady) {
      renderRuns([])
      return
    }
    await refreshRuns()
    ensurePolling()
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      sessionStorage.removeItem(TOKEN_STORAGE_KEY)
      localStorage.removeItem(USER_STORAGE_KEY)
      state.user = null
      state.token = ''
      state.targetOwner = null
      tokenInput.value = ''
    }
    state.setupReady = false
    await updateStorageNotice()
    setStatus(authStatus, `Verbindung fehlgeschlagen: ${error.message}`, 'danger')
    throw error
  }
}

function renderSetupHint(tone, html) {
  if (!html) {
    setupHint.hidden = true
    setupHint.innerHTML = ''
    return
  }
  setupHint.hidden = false
  setupHint.dataset.tone = tone
  setupHint.innerHTML = html
}

function forkSetupInstructions(missingStep) {
  const upstream = upstreamSlug()
  const secret = state.config?.execution?.secretName || 'COPILOT_GITHUB_TOKEN'
  const known = Boolean(state.targetOwner)
  const target = known ? repoSlug() : `<dein-account>/${state.config.repository.repo}`
  const link = (path, label) =>
    known
      ? `<a href="https://github.com/${escapeHtml(repoSlug())}${path}" target="_blank" rel="noreferrer">${escapeHtml(label)}</a>`
      : escapeHtml(label)
  return `
    <strong>Einrichtung deines Forks nötig.</strong>
    <p>${escapeHtml(missingStep)}</p>
    <ol>
      <li><a href="https://github.com/${escapeHtml(upstream)}/fork" target="_blank" rel="noreferrer">${escapeHtml(upstream)} forken</a></li>
      <li>${link('/actions', 'Actions im Fork aktivieren')} (einmaliger Bestätigungsklick)</li>
      <li>Secret <code>${escapeHtml(secret)}</code> anlegen (${link(
        '/settings/secrets/actions/new',
        'Secret hinzufügen',
      )}) – Wert ist ein fine-grained PAT mit der Berechtigung <code>Copilot Requests</code>.</li>
      <li>Diese App mit einem PAT für <code>${escapeHtml(target)}</code> verbinden (${escapeHtml(
        (state.config?.auth?.requiredPermissions || []).join(' + '),
      )}).</li>
    </ol>
    <p class="muted">Copilot-Nutzung, Actions-Minuten und Ergebnisse bleiben damit vollständig in deinem eigenen Account.</p>
  `
}

async function verifyTargetRepository() {
  state.setupReady = false
  if (!forkMode()) {
    state.setupReady = true
    renderSetupHint('neutral', '')
    return
  }
  try {
    await githubRequest(`/repos/${repoSlug()}`)
  } catch (error) {
    if (error.status === 404) {
      renderSetupHint('warning', forkSetupInstructions(`${repoSlug()} wurde nicht gefunden oder der Token hat keinen Zugriff darauf.`))
      return
    }
    throw error
  }
  try {
    await githubRequest(`/repos/${repoSlug()}/actions/workflows/${workflowFile()}`)
  } catch (error) {
    if (error.status === 404) {
      renderSetupHint(
        'warning',
        forkSetupInstructions(
          `Der Workflow ${workflowFile()} fehlt im Fork oder Actions sind dort noch deaktiviert. Fork mit dem Upstream synchronisieren und Actions aktivieren.`,
        ),
      )
      return
    }
    throw error
  }
  state.setupReady = true
  const secret = state.config?.execution?.secretName || 'COPILOT_GITHUB_TOKEN'
  try {
    await githubRequest(`/repos/${repoSlug()}/actions/secrets/${secret}`)
    renderSetupHint('success', `Fork <code>${escapeHtml(repoSlug())}</code> ist einsatzbereit.`)
  } catch (error) {
    if (error.status === 404) {
      renderSetupHint(
        'warning',
        `Secret <code>${escapeHtml(secret)}</code> fehlt in <code>${escapeHtml(repoSlug())}</code>.
         <a href="https://github.com/${escapeHtml(repoSlug())}/settings/secrets/actions/new" target="_blank" rel="noreferrer">Jetzt anlegen</a>
         – fine-grained PAT mit <code>Copilot Requests</code>. Ohne dieses Secret bricht jeder Run sofort ab.`,
      )
    } else {
      renderSetupHint('success', `Fork <code>${escapeHtml(repoSlug())}</code> ist erreichbar.`)
    }
  }
}

function updateRepoBadge() {
  const suffix = forkMode() && state.targetOwner ? ' · dein Fork' : forkMode() ? ' · Fork erforderlich' : ''
  repoBadge.textContent = `${repoSlug()} · ${state.config.workflow.name} · ref ${dispatchRef()}${suffix}`
}

function updateTokenHint() {
  const permissions = (state.config?.auth?.requiredPermissions || []).join(' + ')
  tokenHint.innerHTML = forkMode()
    ? `Fine-grained PAT für deinen eigenen Fork <code>${escapeHtml(repoSlug())}</code> mit ${escapeHtml(permissions)}.
       Kein <code>Contents</code>-Recht nötig – die App schreibt nie in ein Repository.`
    : `Fine-grained PAT für <code>${escapeHtml(repoSlug())}</code> mit ${escapeHtml(permissions)}.
       Kein <code>Contents</code>-Recht nötig – die App schreibt nie in das Repository.`
}

async function clearToken() {
  state.token = ''
  state.user = null
  state.targetOwner = null
  state.setupReady = false
  tokenInput.value = ''
  sessionStorage.removeItem(TOKEN_STORAGE_KEY)
  localStorage.removeItem(USER_STORAGE_KEY)
  if (state.pollHandle) {
    window.clearInterval(state.pollHandle)
    state.pollHandle = null
  }
  renderSetupHint('neutral', '')
  updateRepoBadge()
  updateTokenHint()
  await updateStorageNotice()
  setStatus(authStatus, 'Token gelöscht. Lokale Dateien bleiben erhalten.', 'neutral')
  renderRuns([])
}

function rememberRun(correlationId, entry) {
  const journal = { ...state.journal, [correlationId]: entry }
  const keys = Object.keys(journal).sort((a, b) => String(journal[b].createdAt).localeCompare(String(journal[a].createdAt)))
  const trimmed = {}
  for (const key of keys.slice(0, JOURNAL_LIMIT)) trimmed[key] = journal[key]
  state.journal = trimmed
  saveStoredJson(JOURNAL_STORAGE_KEY, trimmed)
}

function correlationIdFromRun(run) {
  const match = /Copilot run ([0-9a-zA-Z-]{6,})/.exec(run.display_title || run.name || '')
  return match ? match[1] : null
}

async function dispatchWorkflow() {
  if (!state.token) throw new Error('Bitte zuerst einen GitHub-Token verbinden.')
  if (forkMode() && !state.setupReady) {
    throw new Error(`Fork ${repoSlug()} ist noch nicht einsatzbereit – siehe Einrichtungshinweis oben.`)
  }
  const prompt = promptInput.value.trim()
  if (!prompt) throw new Error('Bitte einen Prompt eingeben.')
  const chunks = chunkPrompt(prompt)
  const correlationId = crypto.randomUUID()
  const inputs = { correlation_id: correlationId }
  chunks.forEach((chunk, index) => {
    inputs[index === 0 ? 'prompt' : `prompt_${index + 1}`] = chunk
  })
  const model = modelInput.value.trim()
  if (model) inputs.model = model

  setStatus(dispatchStatus, 'Starte Copilot-Run…')
  const path = `/repos/${repoSlug()}/actions/workflows/${workflowFile()}/dispatches`
  const post = (body) =>
    githubRequest(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

  let response = null
  try {
    response = await post({ ref: dispatchRef(), inputs, return_run_details: true })
  } catch (error) {
    // Older GitHub deployments reject the run-details flag; fall back to a plain dispatch.
    if (error.status !== 422) throw error
    response = await post({ ref: dispatchRef(), inputs })
  }

  rememberRun(correlationId, {
    prompt,
    model,
    createdAt: new Date().toISOString(),
    runId: response?.workflow_run_id ? String(response.workflow_run_id) : '',
  })

  const runNote = response?.workflow_run_id ? ` Run-ID ${response.workflow_run_id}.` : ''
  setStatus(dispatchStatus, `Copilot-Run auf ${currentWorkflowRef()} angefordert.${runNote}`, 'success')
  ensurePolling()
  await refreshRuns()
}

function formatRunStatus(run) {
  const status = run.status || 'unknown'
  const conclusion = run.conclusion ? ` / ${run.conclusion}` : ''
  return `${status}${conclusion}`
}

function runTone(run) {
  if (run.conclusion === 'success') return 'success'
  if (['failure', 'cancelled', 'timed_out'].includes(run.conclusion)) return 'danger'
  if (['in_progress', 'queued', 'waiting'].includes(run.status)) return 'warning'
  return 'neutral'
}

function renderRuns(runs) {
  if (!runs.length) {
    runsList.className = 'runs-list empty'
    runsList.textContent = state.token ? 'Keine passenden Runs gefunden.' : 'Verbinde zuerst GitHub, um Runs zu sehen.'
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
        ? details.artifacts
            .map(
              (artifact) => `
        <li>
          <span>${escapeHtml(artifact.name)} · ${escapeHtml(formatBytes(artifact.size_in_bytes))}</span>
          <button type="button" data-download="${escapeHtml(safeGithubUrl(artifact.archive_download_url, 'https://api.github.com/'))}" data-artifact-name="${escapeHtml(artifact.name)}" data-run-id="${escapeHtml(run.id)}">Übernehmen</button>
        </li>
      `,
            )
            .join('') || '<li>Keine Artefakte.</li>'
        : '<li>Zum Laden öffnen.</li>'
      const jobs = Array.isArray(details.jobs)
        ? details.jobs
            .map(
              (job) =>
                `<li>${escapeHtml(job.name)}: ${escapeHtml(job.status)}${job.conclusion ? ` / ${escapeHtml(job.conclusion)}` : ''}</li>`,
            )
            .join('') || '<li>Keine Jobs gefunden.</li>'
        : '<li>Zum Laden öffnen.</li>'
      const journalEntry = run.correlationId ? state.journal[run.correlationId] : null
      const promptExcerpt = journalEntry?.prompt
        ? `${journalEntry.prompt.slice(0, 220)}${journalEntry.prompt.length > 220 ? '…' : ''}`
        : 'Prompt nicht in diesem Browser gespeichert.'
      return `
        <article class="run-card" data-tone="${runTone(run)}">
          <div class="run-card-header">
            <div>
              <h4>#${escapeHtml(run.run_number)}</h4>
              <p>${escapeHtml(new Date(run.created_at).toLocaleString('de-DE'))} · ${escapeHtml(formatRunStatus(run))}</p>
            </div>
            <a href="${escapeHtml(runUrl)}" target="_blank" rel="noreferrer">In GitHub öffnen</a>
          </div>
          <p class="run-body"><strong>Prompt:</strong> ${escapeHtml(promptExcerpt)}</p>
          <details data-run-id="${escapeHtml(run.id)}" data-detail-kind="jobs"${state.openDetails.has(`${run.id}:jobs`) ? ' open' : ''}>
            <summary>Jobs</summary>
            <ul class="artifact-list" id="run-jobs-${escapeHtml(run.id)}">${jobs}</ul>
          </details>
          <details data-run-id="${escapeHtml(run.id)}" data-detail-kind="artifacts"${state.openDetails.has(`${run.id}:artifacts`) ? ' open' : ''}>
            <summary>Artefakte</summary>
            <ul class="artifact-list" id="run-artifacts-${escapeHtml(run.id)}">${artifacts}</ul>
          </details>
        </article>
      `
    })
    .join('')
}

async function renderSavedFiles() {
  const entries = [...state.models, ...state.files]
  await updateStorageNotice()
  if (!entries.length) {
    savedModelsList.className = 'runs-list empty'
    savedModelsList.textContent = 'Noch keine lokal gespeicherten Dateien.'
    return
  }
  savedModelsList.className = 'runs-list'
  savedModelsList.innerHTML = entries
    .map(
      (entry) => `
    <article class="run-card">
      <div class="run-card-header">
        <div>
          <h4>${escapeHtml(entry.displayName)}</h4>
          <p>${escapeHtml(entry.sourceArtifact || 'Artefakt')} · ${escapeHtml(new Date(entry.savedAt).toLocaleString('de-DE'))}</p>
        </div>
        <span>${escapeHtml(formatBytes(entry.size))}</span>
      </div>
      <p class="run-body"><strong>Datei:</strong> ${escapeHtml(entry.key)}</p>
      <div class="button-row compact-row">
        ${entry.viewerEligible ? `<button type="button" data-open-model="${escapeHtml(entry.key)}">Im Viewer öffnen</button>` : ''}
        ${entry.previewable ? `<button type="button" class="secondary" data-preview-file="${escapeHtml(entry.key)}">Anzeigen</button>` : ''}
        <button type="button" data-download-file="${escapeHtml(entry.key)}" data-store="${escapeHtml(entry.store)}">Herunterladen</button>
        <button type="button" class="secondary" data-delete-file="${escapeHtml(entry.key)}" data-store="${escapeHtml(entry.store)}">Löschen</button>
      </div>
      <pre class="file-preview" id="preview-${escapeHtml(entry.key.replace(/[^a-zA-Z0-9_-]/g, '_'))}" hidden></pre>
    </article>
  `,
    )
    .join('')
}

async function fetchWorkflowRuns() {
  const actorQuery = state.user ? `&actor=${encodeURIComponent(state.user.login)}` : ''
  const data = await githubRequest(
    `/repos/${repoSlug()}/actions/workflows/${workflowFile()}/runs?event=workflow_dispatch&per_page=20${actorQuery}`,
  )
  const workflowRuns = data?.workflow_runs || []
  const filtered = state.user
    ? workflowRuns.filter((run) => (run.triggering_actor?.login || run.actor?.login) === state.user.login)
    : workflowRuns
  return filtered.slice(0, 8).map((run) => ({ ...run, correlationId: correlationIdFromRun(run) }))
}

async function refreshRuns() {
  if (!state.token) {
    renderRuns([])
    return
  }
  try {
    const runs = await fetchWorkflowRuns()
    state.runs = runs
    renderRuns(runs)
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
  try {
    const [artifactsData, jobsData] = await Promise.all([
      githubRequest(`/repos/${repoSlug()}/actions/runs/${run.id}/artifacts`).catch(() => ({ artifacts: [] })),
      githubRequest(`/repos/${repoSlug()}/actions/runs/${run.id}/jobs`).catch(() => ({ jobs: [] })),
    ])
    state.runDetails.set(run.id, {
      updatedAt: run.updated_at,
      artifacts: artifactsData?.artifacts || [],
      jobs: jobsData?.jobs || [],
    })
    renderRuns(state.runs)
  } catch (error) {
    setStatus(dispatchStatus, `Run-Details konnten nicht geladen werden: ${error.message}`, 'danger')
  }
}

function findZipEndOfCentralDirectory(bytes) {
  for (let index = bytes.length - 22; index >= Math.max(0, bytes.length - 0xffff - 22); index -= 1) {
    if (bytes[index] === 0x50 && bytes[index + 1] === 0x4b && bytes[index + 2] === 0x05 && bytes[index + 3] === 0x06) {
      return index
    }
  }
  throw new Error('ZIP-Ende nicht gefunden.')
}

async function inflateDeflateRaw(bytes) {
  if (typeof DecompressionStream === 'undefined') throw new Error('Browser unterstützt kein lokales ZIP-Entpacken.')
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw'))
  return new Uint8Array(await new Response(stream).arrayBuffer())
}

const STORABLE_EXTENSIONS = ['.stl', '.3mf', '.md', '.txt', '.patch', '.json', '.png']

async function extractArtifactFiles(blob) {
  const buffer = await blob.arrayBuffer()
  const bytes = new Uint8Array(buffer)
  const view = new DataView(buffer)
  const eocd = findZipEndOfCentralDirectory(bytes)
  const totalEntries = view.getUint16(eocd + 10, true)
  const centralDirectoryOffset = view.getUint32(eocd + 16, true)
  const decoder = new TextDecoder('utf-8')
  const entries = []
  let pointer = centralDirectoryOffset

  for (let index = 0; index < totalEntries; index += 1) {
    if (view.getUint32(pointer, true) !== 0x02014b50) throw new Error('Ungültiger ZIP-Central-Directory-Eintrag.')
    const compressionMethod = view.getUint16(pointer + 10, true)
    const compressedSize = view.getUint32(pointer + 20, true)
    const uncompressedSize = view.getUint32(pointer + 24, true)
    const fileNameLength = view.getUint16(pointer + 28, true)
    const extraLength = view.getUint16(pointer + 30, true)
    const commentLength = view.getUint16(pointer + 32, true)
    const localHeaderOffset = view.getUint32(pointer + 42, true)
    const name = decoder.decode(bytes.slice(pointer + 46, pointer + 46 + fileNameLength))
    entries.push({ name, compressionMethod, compressedSize, uncompressedSize, localHeaderOffset })
    pointer += 46 + fileNameLength + extraLength + commentLength
  }

  const files = []
  for (const entry of entries) {
    if (entry.name.endsWith('/')) continue
    if (!STORABLE_EXTENSIONS.includes(fileExtension(entry.name))) continue
    if (view.getUint32(entry.localHeaderOffset, true) !== 0x04034b50) throw new Error('Ungültiger ZIP-Local-Header.')
    const fileNameLength = view.getUint16(entry.localHeaderOffset + 26, true)
    const extraLength = view.getUint16(entry.localHeaderOffset + 28, true)
    const dataStart = entry.localHeaderOffset + 30 + fileNameLength + extraLength
    const compressed = bytes.slice(dataStart, dataStart + entry.compressedSize)
    let content
    if (entry.compressionMethod === 0) content = compressed
    else if (entry.compressionMethod === 8) content = await inflateDeflateRaw(compressed)
    else continue
    files.push({ name: entry.name, content, size: entry.uncompressedSize || content.length })
  }
  return files
}

async function storeArtifactFiles(blob, artifactName, runId) {
  const run = state.runs.find((entry) => String(entry.id) === String(runId))
  const runLabel = run?.run_number || 'run'
  const extracted = await extractArtifactFiles(blob)
  let stored = 0
  for (const file of extracted) {
    const leafName = file.name.split('/').pop()
    const model = isModelFile(leafName)
    const key = model ? `run${runLabel}-${leafName}` : `run${runLabel}/${file.name}`
    await putRecord(model ? STORE_MODELS : STORE_FILES, {
      key,
      displayName: leafName,
      blob: new Blob([file.content], { type: contentTypeFor(leafName) }),
      contentType: contentTypeFor(leafName),
      size: file.size,
      sourceArtifact: artifactName,
      runId: String(runId || ''),
      runNumber: run?.run_number || null,
      userLogin: state.user?.login || '',
      version: `${run?.updated_at || Date.now()}-${file.size}`,
      viewerEligible: isViewerEligibleModel(leafName),
      previewable: ['.md', '.txt', '.patch', '.json'].includes(fileExtension(leafName)),
    })
    stored += 1
  }
  await reloadStoredFiles()
  return stored
}

async function downloadArtifact(url, name, runId) {
  try {
    setStatus(dispatchStatus, `Lade Artefakt ${name}…`)
    const blob = await githubRequest(url.replace('https://api.github.com', ''))
    let message = ''
    try {
      const stored = await storeArtifactFiles(blob, name, runId)
      message = stored ? ` ${stored} Datei(en) lokal gespeichert.` : ' Keine übernehmbaren Dateien im Artefakt.'
    } catch (error) {
      message = ` Lokales Sichern übersprungen: ${error.message}`
    }
    const href = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = href
    link.download = `${name}.zip`
    link.click()
    URL.revokeObjectURL(href)
    setStatus(dispatchStatus, `Artefakt ${name} übernommen.${message}`, 'success')
  } catch (error) {
    setStatus(dispatchStatus, `Artefakt-Download fehlgeschlagen: ${error.message}`, 'danger')
  }
}

async function reloadStoredFiles() {
  const [models, files] = await Promise.all([listRecords(STORE_MODELS), listRecords(STORE_FILES)])
  state.models = models.map((entry) => ({ ...entry, store: STORE_MODELS, blob: undefined }))
  state.files = files.map((entry) => ({ ...entry, store: STORE_FILES, blob: undefined }))
  await renderSavedFiles()
}

async function downloadStoredFile(storeName, key) {
  const record = await getRecord(storeName, key)
  if (!record?.blob) return
  const link = document.createElement('a')
  link.href = URL.createObjectURL(record.blob)
  link.download = record.displayName || key
  link.click()
  URL.revokeObjectURL(link.href)
}

async function previewStoredFile(key) {
  const record = await getRecord(STORE_FILES, key)
  const node = document.querySelector(`#preview-${CSS.escape(key.replace(/[^a-zA-Z0-9_-]/g, '_'))}`)
  if (!record?.blob || !node) return
  node.hidden = !node.hidden
  if (!node.hidden) node.textContent = await record.blob.text()
}

function openSavedModelInViewer(key) {
  const chooser = document.querySelector('#viewerRoot #fileChooser')
  if (!chooser) {
    setStatus(dispatchStatus, 'Viewer-Dateiauswahl nicht gefunden. Bitte Seite neu laden.', 'warning')
    return
  }
  if (![...chooser.options].some((option) => option.value === key)) chooser.add(new Option(key, key))
  chooser.value = key
  chooser.dispatchEvent(new Event('change', { bubbles: true }))
  setStatus(dispatchStatus, `Lokales Modell ${key} im Viewer geöffnet.`, 'success')
}

const thumbnailUrls = new Set()

function releaseThumbnailUrls() {
  for (const url of thumbnailUrls) URL.revokeObjectURL(url)
  thumbnailUrls.clear()
}

async function reloadImages() {
  const records = await listRecords(STORE_IMAGES)
  state.images = records.slice().reverse()
  renderImages()
  await updateStorageNotice()
}

function renderImages() {
  releaseThumbnailUrls()
  if (!state.images.length) {
    imageList.className = 'runs-list empty'
    imageList.textContent = 'Noch keine Bilder gespeichert.'
    setStatus(imageStatus, 'Noch keine Bilder gespeichert.', 'warning')
    return
  }
  setStatus(
    imageStatus,
    `${state.images.length} Bild(er) im Browser gespeichert. Sie werden nicht an die Action übertragen – Maße bitte im Prompt angeben.`,
    'success',
  )
  imageList.className = 'runs-list'
  imageList.innerHTML = state.images
    .map((record, index) => {
      let thumbUrl = ''
      if (record.thumbnail) {
        thumbUrl = URL.createObjectURL(record.thumbnail)
        thumbnailUrls.add(thumbUrl)
      }
      return `
      <article class="run-card image-card">
        <div class="run-card-header">
          <div>
            <h4>Kachel ${escapeHtml(String(index + 1).padStart(2, '0'))} · ${escapeHtml(record.displayName)}</h4>
            <p>${escapeHtml(record.width)}×${escapeHtml(record.height)} px · ${escapeHtml(formatBytes(record.size))}</p>
          </div>
          <button type="button" class="secondary" data-delete-image="${escapeHtml(record.key)}">Löschen</button>
        </div>
        ${thumbUrl ? `<img class="image-thumb" src="${escapeHtml(thumbUrl)}" alt="${escapeHtml(record.displayName)}" />` : ''}
        <label class="stack field-block">
          <span>Notiz / gemessene Maße</span>
          <input type="text" data-image-note="${escapeHtml(record.key)}" value="${escapeHtml(record.note || '')}" placeholder="z. B. Außendurchmesser 24,5 mm" />
        </label>
      </article>
    `
    })
    .join('')
}

async function addImages(files) {
  const maxFiles = state.config?.images?.maxFiles || 24
  if (state.images.length + files.length > maxFiles) {
    throw new Error(`Maximal ${maxFiles} Bilder. Bitte zuerst einige löschen.`)
  }
  for (const file of files) {
    const meta = await describeImage(file)
    await putRecord(STORE_IMAGES, {
      key: `img-${Date.now()}-${Math.random().toString(36).slice(2, 8)}-${sanitizePathSegment(file.name)}`,
      displayName: file.name,
      blob: file,
      thumbnail: meta.thumbnail,
      width: meta.width,
      height: meta.height,
      size: file.size,
      contentType: file.type || 'image/*',
      note: '',
    })
  }
  await reloadImages()
}

async function updateImageNote(key, note) {
  const record = await getRecord(STORE_IMAGES, key)
  if (!record) return
  await putRecord(STORE_IMAGES, { ...record, note, savedAt: record.savedAt })
  state.images = state.images.map((entry) => (entry.key === key ? { ...entry, note } : entry))
}

async function createContactSheet() {
  if (!state.images.length) throw new Error('Bitte zuerst Bilder hinzufügen.')
  const records = []
  for (const meta of state.images) {
    const full = await getRecord(STORE_IMAGES, meta.key)
    if (full) records.push(full)
  }
  const sheet = await buildContactSheet(records)
  await putRecord(STORE_FILES, {
    key: 'contact-sheet/_index.png',
    displayName: '_index.png',
    blob: sheet,
    contentType: 'image/png',
    size: sheet.size,
    sourceArtifact: 'Lokales Kontaktblatt',
    viewerEligible: false,
    previewable: false,
    version: String(Date.now()),
  })
  await reloadStoredFiles()
  const href = URL.createObjectURL(sheet)
  const link = document.createElement('a')
  link.href = href
  link.download = '_index.png'
  link.click()
  URL.revokeObjectURL(href)
  setStatus(imageStatus, 'Kontaktblatt erzeugt, heruntergeladen und lokal gespeichert.', 'success')
}

function appendImageContext() {
  if (!state.images.length) throw new Error('Bitte zuerst Bilder hinzufügen.')
  const block = buildImageContextBlock(state.images)
  promptInput.value = `${promptInput.value.trimEnd()}\n\n${block}\n`
  updatePromptCounter()
  setStatus(imageStatus, 'Bildkontext an den Prompt angehängt.', 'success')
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

runsList.addEventListener(
  'toggle',
  (event) => {
    const details = event.target
    if (!(details instanceof HTMLDetailsElement) || !details.dataset.runId) return
    const stateKey = `${details.dataset.runId}:${details.dataset.detailKind}`
    if (details.open) state.openDetails.add(stateKey)
    else state.openDetails.delete(stateKey)
    if (!details.open) return
    loadRunDetails(details.dataset.runId).catch(() => {})
  },
  true,
)

savedModelsList.addEventListener('click', (event) => {
  const openButton = event.target.closest('[data-open-model]')
  if (openButton) {
    openSavedModelInViewer(openButton.dataset.openModel)
    return
  }
  const previewButton = event.target.closest('[data-preview-file]')
  if (previewButton) {
    previewStoredFile(previewButton.dataset.previewFile).catch(() => {})
    return
  }
  const downloadButton = event.target.closest('[data-download-file]')
  if (downloadButton) {
    downloadStoredFile(downloadButton.dataset.store, downloadButton.dataset.downloadFile).catch(() => {})
    return
  }
  const deleteButton = event.target.closest('[data-delete-file]')
  if (deleteButton) {
    deleteRecord(deleteButton.dataset.store, deleteButton.dataset.deleteFile)
      .then(reloadStoredFiles)
      .catch(() => {})
  }
})

imageList.addEventListener('click', (event) => {
  const deleteButton = event.target.closest('[data-delete-image]')
  if (!deleteButton) return
  deleteRecord(STORE_IMAGES, deleteButton.dataset.deleteImage)
    .then(reloadImages)
    .catch(() => {})
})

imageList.addEventListener('change', (event) => {
  const noteInput = event.target.closest('[data-image-note]')
  if (!noteInput) return
  updateImageNote(noteInput.dataset.imageNote, noteInput.value).catch(() => {})
})

promptExamples.addEventListener('click', (event) => {
  const button = event.target.closest('[data-example]')
  if (!button) return
  promptInput.value = PROMPT_EXAMPLES[Number(button.dataset.example)].prompt
  updatePromptCounter()
  promptInput.focus()
})

promptInput.addEventListener('input', updatePromptCounter)
connectBtn.addEventListener('click', () => connectToken().catch(() => {}))
clearTokenBtn.addEventListener('click', () => clearToken().catch(() => {}))
clearSavedModelsBtn.addEventListener('click', () => {
  Promise.all([clearStore(STORE_MODELS), clearStore(STORE_FILES)])
    .then(reloadStoredFiles)
    .catch(() => {})
})
clearImagesBtn.addEventListener('click', () => {
  clearStore(STORE_IMAGES).then(reloadImages).catch(() => {})
})
imageUploadInput.addEventListener('change', () => {
  const files = [...(imageUploadInput.files || [])]
  if (!files.length) return
  addImages(files)
    .then(() => {
      imageUploadInput.value = ''
    })
    .catch((error) => setStatus(imageStatus, error.message, 'danger'))
})
contactSheetBtn.addEventListener('click', () => {
  createContactSheet().catch((error) => setStatus(imageStatus, error.message, 'danger'))
})
appendImageContextBtn.addEventListener('click', () => {
  try {
    appendImageContext()
  } catch (error) {
    setStatus(imageStatus, error.message, 'danger')
  }
})
dispatchBtn.addEventListener('click', () => {
  dispatchWorkflow().catch((error) => setStatus(dispatchStatus, error.message, 'danger'))
})
refreshBtn.addEventListener('click', () => refreshRuns().catch(() => {}))
window.addEventListener('beforeunload', releaseThumbnailUrls)

async function bootstrap() {
  try {
    const [config, buildInfo, manifest] = await Promise.all([
      loadJson('./app-config.json'),
      loadJson('./build-info.json').catch(() => null),
      loadJson('./skills-manifest.json').catch(() => ({ skills: [] })),
    ])
    state.config = config
    state.buildInfo = buildInfo
    state.manifest = manifest

    if (config.app?.title) {
      appTitle.textContent = config.app.title
      document.title = config.app.title
    }
    if (config.app?.tagline) appTagline.textContent = config.app.tagline
    updateRepoBadge()
    manifestSummary.textContent = manifest.description || ''
    updateTokenHint()

    localStorage.removeItem(LEGACY_WORKSPACE_STORAGE_KEY)
    renderPromptExamples()
    renderSkillList()
    updatePromptCounter()

    try {
      const migrated = await migrateLegacyModels(LEGACY_MODEL_STORAGE_KEY)
      if (migrated) setStatus(dispatchStatus, `${migrated} Modell(e) aus dem alten Speicher übernommen.`, 'success')
    } catch {
      // Migration is best effort.
    }

    await reloadStoredFiles()
    await reloadImages()

    if (state.user?.login && state.token) {
      setStatus(authStatus, `PAT in dieser Tabsitzung gefunden. Letzter Benutzer: ${state.user.login}.`, 'warning')
      try {
        await connectToken()
      } catch {
        renderRuns([])
      }
    } else {
      if (forkMode()) {
        renderSetupHint(
          'warning',
          forkSetupInstructions('Der Auftrag läuft in deinem eigenen Fork – dort brauchst du einmalig folgende Einrichtung:'),
        )
      }
      await updateStorageNotice()
      renderRuns([])
    }
  } catch (error) {
    repoBadge.textContent = 'Konfiguration konnte nicht geladen werden'
    setStatus(authStatus, `Initialisierung fehlgeschlagen: ${error.message}`, 'danger')
    setStatus(dispatchStatus, 'App konnte nicht vollständig initialisiert werden.', 'danger')
  }
}

bootstrap()
