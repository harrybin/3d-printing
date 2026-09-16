import './style.css'
import { initStlCanvas } from '../../.github/extensions/stl-canvas/viewer-app.mjs'

const app = document.querySelector('#app')
const MOBILE_BREAKPOINT = '(max-width: 720px)'
const state = {
  config: null,
  currentModel: '',
  currentModelUrl: '',
}

async function loadJson(url) {
  const res = await fetch(url, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Failed to load ${url}: ${res.status}`)
  return res.json()
}

function repoSlug() {
  const { owner = 'harrybin', repo = '3d-printing' } = state.config?.repository || {}
  return `${owner}/${repo}`
}

function currentModelUrl() {
  return state.currentModelUrl || (state.currentModel
    ? `./models/${state.currentModel.split('/').map((segment) => encodeURIComponent(segment)).join('/')}`
    : '#')
}

function updateDownloadButton() {
  const button = document.querySelector('#downloadModelBtn')
  if (!button) return
  const enabled = Boolean(state.currentModel)
  button.href = enabled ? currentModelUrl() : '#'
  button.toggleAttribute('aria-disabled', !enabled)
  button.tabIndex = enabled ? 0 : -1
  button.setAttribute('download', enabled ? state.currentModel : '')
  button.querySelector('.button-label').textContent = enabled
    ? `Download ${state.currentModel}`
    : 'Download model'
}

function bindViewerEvents() {
  const viewerRoot = document.querySelector('#viewerRoot')
  if (!viewerRoot) return
  viewerRoot.addEventListener('stl-canvas:model-change', (event) => {
    state.currentModel = event.detail?.file || ''
    state.currentModelUrl = event.detail?.url || ''
    updateDownloadButton()
  })
}

function renderShell() {
  app.innerHTML = `
    <div class="page-shell">
      <header class="hero card">
        <div class="hero-copy">
          <p class="eyebrow">GitHub Pages · STL / 3MF</p>
          <h1 id="appTitle">3d-printing model viewer</h1>
          <p class="lede" id="appTagline">Browse printable models from this repository, preview them in 3D, download them, or open a new model request on GitHub.</p>
        </div>
        <div class="hero-actions" id="heroActions">
          <a id="repoLink" class="icon-link" href="https://github.com/harrybin/3d-printing" target="_blank" rel="noreferrer" aria-label="Open GitHub repository">
            <svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">
              <path fill="currentColor" d="M8 0C3.58 0 0 3.67 0 8.2c0 3.63 2.29 6.7 5.47 7.78.4.08.55-.18.55-.39 0-.19-.01-.82-.01-1.49-2.01.38-2.53-.51-2.69-.97-.09-.24-.48-.97-.81-1.16-.27-.15-.66-.54-.01-.55.61-.01 1.05.58 1.2.82.69 1.18 1.79.85 2.23.64.07-.51.27-.85.49-1.05-1.78-.21-3.64-.92-3.64-4.08 0-.9.31-1.64.82-2.22-.08-.21-.36-1.06.08-2.2 0 0 .67-.22 2.2.85.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.07 2.2-.85 2.2-.85.44 1.14.16 1.99.08 2.2.51.58.82 1.31.82 2.22 0 3.17-1.87 3.87-3.65 4.08.29.25.53.73.53 1.49 0 1.07-.01 1.94-.01 2.21 0 .21.15.47.55.39A8.23 8.23 0 0 0 16 8.2C16 3.67 12.42 0 8 0Z"></path>
            </svg>
            <span>Repository</span>
          </a>
          <a id="downloadModelBtn" class="action-link" href="#" aria-disabled="true" tabindex="-1">
            <span class="button-label">Download model</span>
          </a>
          <a id="newIssueLink" class="action-link primary" href="https://github.com/harrybin/3d-printing/issues/new?template=model-request.yml" target="_blank" rel="noreferrer">Work on new model</a>
        </div>
      </header>

      <main>
        <section class="card viewer-card">
          <div class="section-header">
            <div>
              <h2>3D Model Viewer</h2>
              <p class="muted">Open STL and 3MF files from <code>models/</code>. On phones and tablets the canvas uses a lower pixel ratio so large meshes render faster.</p>
            </div>
          </div>
          <div id="viewerRoot" class="viewer-root"></div>
        </section>
      </main>
    </div>
  `
}

async function bootstrap() {
  renderShell()
  bindViewerEvents()

  try {
    state.config = await loadJson('./app-config.json')
  } catch {
    state.config = {
      app: {
        title: '3d-printing model viewer',
        tagline: 'Browse printable STL and 3MF files from this repository.',
      },
      repository: {
        owner: 'harrybin',
        repo: '3d-printing',
      },
    }
  }

  const appTitle = document.querySelector('#appTitle')
  const appTagline = document.querySelector('#appTagline')
  const repoLink = document.querySelector('#repoLink')
  const newIssueLink = document.querySelector('#newIssueLink')

  if (state.config.app?.title) {
    appTitle.textContent = state.config.app.title
    document.title = state.config.app.title
  }
  if (state.config.app?.tagline) appTagline.textContent = state.config.app.tagline

  const repoUrl = `https://github.com/${repoSlug()}`
  repoLink.href = repoUrl
  newIssueLink.href = `${repoUrl}/issues/new?template=model-request.yml`

  initStlCanvas({
    root: document.querySelector('#viewerRoot'),
    repository: state.config.repository,
    viewStorageKey: 'stl-canvas-pages-view-defaults',
    pollIntervalMs: 0,
    maxPixelRatio: window.matchMedia(MOBILE_BREAKPOINT).matches ? 1.1 : 1.75,
  })
  updateDownloadButton()
}

bootstrap()
