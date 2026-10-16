export const APP_HTML = `
<div class="toolbar">
  <div class="field grow">
    <label for="fileChooser">File</label>
    <select id="fileChooser"><option value="">Loading…</option></select>
  </div>
  <div class="field" id="plateField" hidden>
    <label for="plateChooser">Plate</label>
    <select id="plateChooser"><option value="all">All plates</option></select>
  </div>
  <div class="field image-actions" id="imageActions" hidden>
    <button type="button" id="projectPreviewBtn" hidden>Project preview</button>
    <div class="plate-support-actions" id="plateSupportActions" role="group" aria-label="Support previews by plate" hidden></div>
  </div>
  <div class="field" id="orcaField" hidden>
    <button type="button" id="openInOrcaBtn" title="Open the current 3MF project with the default 3MF application">3mf öffnen</button>
    <span id="orcaStatus" class="action-status" role="status" aria-live="polite" hidden></span>
  </div>
  <details class="tool-drawer">
    <summary title="Show view, model and reload controls">View &amp; model controls</summary>
    <div class="tool-drawer-panel">
      <div class="group">
        <span class="group-label">File</span>
        <button type="button" id="reloadBtn" title="Reload current model">Reload</button>
        <label class="field"><input id="autoReload" type="checkbox"> Auto reload</label>
      </div>
      <div class="group grow-controls">
        <span class="group-label">Display</span>
        <label class="field zoom-field" for="zoom">Zoom
          <input id="zoom" type="range" min="0.1" max="30" step="0.1" value="1.7">
        </label>
        <label class="field"><input id="wireframe" type="checkbox"> Wireframe</label>
        <label class="field" for="shading">Shading
          <select id="shading">
            <option value="lambert">Lambert</option>
            <option value="phong">Phong</option>
            <option value="normal">Normal</option>
            <option value="basic">Basic</option>
            <option value="material">Material</option>
          </select>
        </label>
      </div>
      <div class="group">
        <span class="group-label">View</span>
        <button type="button" data-view="isometric" title="Isometric view">Iso</button>
        <button type="button" data-view="top" title="Top view">Top</button>
        <button type="button" data-view="bottom" title="Bottom view">Bottom</button>
        <button type="button" data-view="front" title="Front view">Front</button>
        <button type="button" data-view="back" title="Back view">Back</button>
        <button type="button" data-view="left" title="Left view">Left</button>
        <button type="button" data-view="right" title="Right view">Right</button>
        <button type="button" id="fitBtn" title="Fit model to view">Fit</button>
      </div>
      <div class="group">
        <span class="group-label">Rotate model</span>
        <button type="button" data-rotate="x" title="Rotate model 90° around X">X 90°</button>
        <button type="button" data-rotate="y" title="Rotate model 90° around Y">Y 90°</button>
        <button type="button" data-rotate="z" title="Rotate model 90° around Z">Z 90°</button>
        <button type="button" id="resetRotation" title="Clear model rotation">Reset</button>
      </div>
      <div class="group">
        <span class="group-label">Show</span>
        <label class="field"><input id="showGrid" type="checkbox"> Grid</label>
        <label class="field"><input id="showAxes" type="checkbox"> Axes</label>
        <label class="field"><input id="showBoundingBox" type="checkbox"> Box</label>
        <label class="field"><input id="showInfo" type="checkbox"> Info</label>
      </div>
      <div class="group">
        <span class="group-label">Measure</span>
        <label class="field"><input id="measureMode" type="checkbox"> On</label>
        <button type="button" id="measureClear" title="Clear selected features (Esc)">Clear</button>
      </div>
    </div>
  </details>
</div>
<section id="printSummary" class="print-summary" aria-label="Print project summary" hidden>
  <div class="print-card print-scope"><strong>All plates · project total</strong></div>
  <div class="print-card"><span>Print time</span><strong id="summaryPrintTime">—</strong></div>
  <div class="print-card"><span>Material usage</span><strong id="summaryMaterial">—</strong></div>
  <div class="print-card"><span>Support material</span><strong id="summarySupport">—</strong></div>
  <div class="print-card"><span>Filament length</span><strong id="summaryLength">—</strong></div>
  <div class="print-card"><span>Validation</span><strong id="summaryStatus">—</strong></div>
  <div class="print-card"><span>Plates</span><strong id="summaryPlates">—</strong></div>
</section>
<div class="viewer-container">
  <canvas id="view"></canvas>
  <div id="loadingSpinner" class="loading-spinner" hidden role="status" aria-live="polite">
    <div class="spinner"></div>
    <span class="spinner-text">Loading plates…</span>
  </div>
  <div id="info" hidden></div>
  <div id="measurePanel" hidden></div>
  <details id="metaPanel" class="meta-panel">
    <summary>Model &amp; print details</summary>
    <div id="meta">Loading model…</div>
  </details>
</div>
<dialog id="projectImageDialog" class="project-image-dialog" aria-labelledby="projectImageCaption">
  <div class="project-image-dialog-header">
    <strong id="projectImageCaption"></strong>
    <button type="button" id="closeProjectImageBtn" aria-label="Close image preview">Close</button>
  </div>
  <img id="projectImage" alt="">
</dialog>

`

export function create3mfOpenUrl(file, accessibleUrl, baseUrl = globalThis.location?.href) {
  if (!/\.3mf$/i.test(String(file || '').trim()) || !accessibleUrl || !baseUrl) return ''
  try {
    const url = new URL(accessibleUrl, baseUrl)
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return ''
    return url.href
  } catch {
    return ''
  }
}

export function formatPrintMetadataSummary(projectMetadata = {}) {
  const metadataValue = (key, fallback = 'not available') => {
    const value = projectMetadata[key]
    return value !== undefined && value !== null && value !== '' && value !== 'unknown' ? value : fallback
  }
  const metadataWithUnit = (key, unit) => {
    const value = metadataValue(key)
    return value === 'not available' ? value : `${value} ${unit}`
  }
  const seconds = Number(projectMetadata.estimatedPrintTimeSeconds)
  let printTime = 'not available'
  if (Number.isFinite(seconds) && seconds >= 0) {
    const totalMinutes = Math.round(seconds / 60)
    const hours = Math.floor(totalMinutes / 60)
    const minutes = totalMinutes % 60
    printTime = hours ? `${hours} h ${minutes} min` : `${minutes} min`
  }
  const grams = metadataWithUnit('filamentUsageGrams', 'g')
  const material = metadataValue('materialType', '')
  const supportGrams = Number(projectMetadata.supportFilamentGrams)
  const supportUsage = metadataValue('supportFilamentGrams') === 'not available'
    || !Number.isFinite(supportGrams) || supportGrams < 0
    ? 'not available'
    : supportGrams === 0 ? 'none' : `${supportGrams.toFixed(2)} g`
  return {
    visible: Object.keys(projectMetadata).length > 0,
    printTime,
    materialUsage: grams === 'not available' ? grams : `${grams}${material ? ` ${material}` : ''}`,
    supportUsage,
    filamentLength: metadataWithUnit('filamentUsageMillimeters', 'mm'),
    status: metadataValue('status'),
  }
}

function modelBasename(file) {
  return String(file || '').split(/[\\/]/).pop() || ''
}

export function projectPreviewImagePath(file) {
  const name = modelBasename(file)
  if (!/\.3mf$/i.test(name)) return ''
  return `docs/images/${name.replace(/\.3mf$/i, '')}-preview.png`
}

export function plateSupportImagePath(file, plateNumber) {
  const previewPath = projectPreviewImagePath(file)
  if (!previewPath || !Number.isInteger(Number(plateNumber)) || Number(plateNumber) < 1) return ''
  const stem = modelBasename(file).replace(/\.3mf$/i, '')
  return `docs/images/${stem}-plate-${Number(plateNumber)}-supports.png`
}

export function renderPlateSupportPreviewActions(file, plates = []) {
  if (!Array.isArray(plates)) return ''
  return plates.map((plate) => {
    const plateNumber = Number(plate?.id)
    const imagePath = plateSupportImagePath(file, plateNumber)
    if (!imagePath) return ''
    const label = `Plate ${plateNumber}`
    return `<button type="button" class="plate-support-preview" data-project-image="${escapeHtml(imagePath)}" data-project-image-caption="${escapeHtml(`${label} support preview`)}" disabled title="Checking screenshot availability">${label}: supports</button>`
  }).join('')
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

export function renderPlatePrintDetails(projectMetadata = {}, { file = '' } = {}) {
  if (!Object.keys(projectMetadata).length) return ''
  let plates
  try {
    plates = typeof projectMetadata.plateDetails === 'string'
      ? JSON.parse(projectMetadata.plateDetails)
      : projectMetadata.plateDetails
  } catch {
    return '<p class="plate-data-notice">Per-plate print data could not be read: invalid plateDetails metadata.</p>'
  }
  if (plates === undefined) {
    return '<p class="plate-data-notice">Per-plate print data is not available in this file.</p>'
  }
  if (!Array.isArray(plates) || plates.some((plate) => !plate || typeof plate !== 'object' || Array.isArray(plate))) {
    return '<p class="plate-data-notice">Per-plate print data could not be read: expected plate records.</p>'
  }
  if (!plates.length) return '<p class="plate-data-notice">No per-plate print data is stored in this file.</p>'
  const rows = plates.map((plate, index) => {
    const summary = formatPrintMetadataSummary(plate)
    const rawSupportLength = plate.supportFilamentMillimeters
    const supportLength = rawSupportLength !== undefined && rawSupportLength !== null &&
      String(rawSupportLength).trim() !== '' && Number.isFinite(Number(rawSupportLength)) &&
      Number(rawSupportLength) >= 0
      ? `${Number(rawSupportLength).toFixed(2)} mm` : 'not available'
    const name = typeof plate.name === 'string' && plate.name.trim() ? plate.name : `Plate ${index + 1}`
    const supportImagePath = plateSupportImagePath(file, index + 1)
    const supportPreview = supportImagePath
      ? `<button type="button" class="plate-support-preview" data-project-image="${escapeHtml(supportImagePath)}" data-project-image-caption="${escapeHtml(`${name} support preview`)}" disabled title="Checking screenshot availability">View supports</button>`
      : ''
    return `<tr><th scope="row">${escapeHtml(name)}</th>` +
      [summary.printTime, summary.materialUsage, summary.supportUsage, summary.filamentLength, supportLength, summary.status]
        .map((value) => `<td>${escapeHtml(value)}</td>`).join('') +
      `<td>${supportPreview}</td></tr>`
  }).join('')
  return '<details class="plate-print-details"><summary>Print data by plate (' + plates.length + ')</summary>' +
    '<div class="plate-table-scroll" tabindex="0" role="region" aria-label="Print data by plate">' +
    '<table class="plate-print-table"><caption>Per-plate slice results; the top bar always shows all-plate totals.</caption>' +
    '<thead><tr><th scope="col">Plate</th><th scope="col">Print time</th><th scope="col">Material</th>' +
    '<th scope="col">Support</th><th scope="col">Filament length</th><th scope="col">Support length</th><th scope="col">Validation</th>' +
    '<th scope="col">Support preview</th></tr></thead>' +
    `<tbody>${rows}</tbody></table></div></details>`
}

export function createOrcaLaunchRequest(url, modelPath, nonce) {
  return {
    url,
    options: {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ modelPath, nonce }),
    },
  }
}

export function transform3mfPoint(point, transform) {
  if (!transform) return point
  const [x, y, z] = point
  return [
    transform[0] * x + transform[3] * y + transform[6] * z + transform[9],
    transform[1] * x + transform[4] * y + transform[7] * z + transform[10],
    transform[2] * x + transform[5] * y + transform[8] * z + transform[11],
  ]
}

function scaleTransformTranslation(transform, unitScale = 1) {
  if (!transform || unitScale === 1) return transform
  const scaled = transform.slice()
  scaled[9] *= unitScale
  scaled[10] *= unitScale
  scaled[11] *= unitScale
  return scaled
}

export function compose3mfTransforms(parent, child, childUnitScale = 1) {
  const normalizedChild = scaleTransformTranslation(child, childUnitScale)
  if (!parent) return normalizedChild
  if (!normalizedChild) return parent
  const toMatrix = (transform) => [
    [transform[0], transform[1], transform[2], 0],
    [transform[3], transform[4], transform[5], 0],
    [transform[6], transform[7], transform[8], 0],
    [transform[9], transform[10], transform[11], 1],
  ]
  const childMatrix = toMatrix(normalizedChild)
  const parentMatrix = toMatrix(parent)
  const combined = Array.from({ length: 4 }, (_, row) => (
    Array.from({ length: 4 }, (_, column) => (
      childMatrix[row].reduce(
        (sum, value, index) => sum + value * parentMatrix[index][column],
        0,
      )
    ))
  ))
  return [
    combined[0][0], combined[0][1], combined[0][2],
    combined[1][0], combined[1][1], combined[1][2],
    combined[2][0], combined[2][1], combined[2][2],
    combined[3][0], combined[3][1], combined[3][2],
  ]
}

export function selectDefaultPlate(file, previousFile, previousSelection, plates) {
  return plates.length > 1 && file === previousFile && plates.some((plate) => String(plate.id) === previousSelection)
    ? previousSelection
    : 'all'
}

export function selectDefaultModelFile(files = [], requested = '') {
  if (requested && files.includes(requested)) return requested
  const printCandidate = files.find((name) => /ghouls[_-]?grip.*print/i.test(name))
  if (printCandidate) return printCandidate
  const anyGhoul = files.find((name) => /ghouls[_-]?grip/i.test(name))
  if (anyGhoul) return anyGhoul
  const first3mf = files.find((name) => /\.3mf$/i.test(name))
  if (first3mf) return first3mf
  return files[0] || 'ghouls-grip-print.3mf'
}

export function calculateTouchPinchZoom(currentZoom, currentDistance, initialDistance, minZoom = 0.1, maxZoom = 30) {
  if (!initialDistance || initialDistance <= 0 || !currentDistance || currentDistance <= 0) return currentZoom
  const factor = currentDistance / initialDistance
  const updated = currentZoom * factor
  return Math.max(minZoom, Math.min(maxZoom, Math.round(updated * 100) / 100))
}

export function calculateTouchPan(dx, dy, scale = 0.5) {
  return {
    deltaPanX: dx * scale,
    deltaPanY: dy * scale,
  }
}

export function calculateTouchRotation(dx, dy, scale = 0.5) {
  return {
    deltaRotX: dy * scale,
    deltaRotY: dx * scale,
  }
}

function computeBounds(tris) {
  if (!tris.length) return null;
  let min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (const tri of tris) for (const v of tri) for (let i = 0; i < 3; i++) { if (v[i] < min[i]) min[i] = v[i]; if (v[i] > max[i]) max[i] = v[i]; }
  return { min: { x: min[0], y: min[1], z: min[2] }, max: { x: max[0], y: max[1], z: max[2] }, size: { x: max[0] - min[0], y: max[1] - min[1], z: max[2] - min[2] } };
}

export function layoutPlateOverview(plates, bedSize = 250, spacing = 50) {
  if (plates.length <= 1) return plates
  const envelopes = plates.map((plate) => {
    const bounds = computeBounds(plate.triangles)
    return {
      x: (bounds.min.x + bounds.max.x) / 2,
      y: (bounds.min.y + bounds.max.y) / 2,
      width: Math.max(bedSize, bounds.size.x),
      height: Math.max(bedSize, bounds.size.y),
    }
  })
  // Reposition only the overview; individual plate geometry retains its transforms.
  const overlaps = envelopes.some((left, index) => envelopes.slice(index + 1).some((right) => (
    Math.abs(left.x - right.x) < (left.width + right.width) / 2 &&
    Math.abs(left.y - right.y) < (left.height + right.height) / 2
  )))
  if (!overlaps && plates.length <= 2) return plates

  const columns = Math.ceil(Math.sqrt(plates.length))
  const cellWidth = Math.max(...envelopes.map((envelope) => envelope.width)) + spacing
  const cellHeight = Math.max(...envelopes.map((envelope) => envelope.height)) + spacing
  return plates.map((plate, index) => {
    const envelope = envelopes[index]
    const dx = envelopes[0].x + (index % columns) * cellWidth - envelope.x
    const dy = envelopes[0].y - Math.floor(index / columns) * cellHeight - envelope.y
    const triangles = plate.triangles.map((triangle) => triangle.map(([x, y, z]) => [x + dx, y + dy, z]))
    return {
      ...plate,
      triangles,
      stats: { ...plate.stats, bounds: computeBounds(triangles) },
    }
  })
}

function childrenByLocalName(node, name) {
  return [...(node?.children || [])].filter((child) => child.localName === name)
}

function normalizeColor(value) {
  if (typeof value !== 'string') return null
  const match = value.trim().match(/^#([0-9a-f]{6}|[0-9a-f]{8})$/i)
  if (!match) return null
  return `#${match[1].slice(0, 6)}`.toLowerCase()
}

export function orcaMaterialAssignments(settingsDoc, projectSettings) {
  const palette = projectSettings.filament_colour || projectSettings.filament_color || []
  const assignments = new Map()
  const extruder = (node) => childrenByLocalName(node, 'metadata')
    .find((entry) => entry.getAttribute('key') === 'extruder')?.getAttribute('value')
  const colorFor = (slot) => {
    const index = Number(slot) - 1
    return Number.isInteger(index) && index >= 0 ? normalizeColor(palette[index]) : null
  }
  for (const object of childrenByLocalName(settingsDoc.documentElement, 'object')) {
    const objectSlot = extruder(object)
    const objectColor = colorFor(objectSlot)
    const partColors = new Map()
    for (const part of childrenByLocalName(object, 'part')) {
      const partSlot = extruder(part)
      const color = colorFor(Number(partSlot) > 0 ? partSlot : objectSlot)
      if (color) partColors.set(part.getAttribute('id'), color)
    }
    assignments.set(object.getAttribute('id'), { color: objectColor, parts: partColors })
  }
  return assignments
}

export function initStlCanvas(options = {}) {
const root = options.root || document.querySelector('#app') || document.body
root.innerHTML = APP_HTML
const VIEW_STORAGE_KEY = options.viewStorageKey || 'stl-canvas-view-defaults'
const searchParams = new URLSearchParams(window.location.search)
const defaultModelFile = searchParams.get('model') || options.defaultModelFile || 'ghouls-grip-print.3mf'
const runtimeMode = options.dataSource === 'extension' ? 'extension' : 'static'
const modelsBasePath = options.modelsBasePath || './models'
const modelsIndexUrl = options.modelsIndexUrl || `${modelsBasePath}/models.json`
const viewApiUrl = options.viewApiUrl || '/api/view'
const modelsApiUrl = options.modelsApiUrl || '/api/models'
const modelApiUrl = options.modelApiUrl || '/api/model'
const modelDownloadApiUrl = options.modelDownloadApiUrl || '/api/model-file'
const projectImageApiUrl = options.projectImageApiUrl || '/api/project-image'
const openInOrcaApiUrl = options.openInOrcaApiUrl || ''
const openInOrcaNonce = options.openInOrcaNonce || ''
const pollIntervalMs = Number.isFinite(options.pollIntervalMs) ? options.pollIntervalMs : 1500
const maxPixelRatio = Number.isFinite(options.maxPixelRatio) ? Math.max(0.5, options.maxPixelRatio) : Number.POSITIVE_INFINITY
const repository = options.repository && typeof options.repository === 'object' ? options.repository : {}
const storageShadingModes = ['basic', 'lambert', 'normal', 'phong', 'material']
const fallbackView = {
  rotX: -64.5,
  rotY: 8,
  rotZ: 0,
  panX: 0,
  panY: 0,
  zoom: 1.0,
  showGrid: true,
  showAxes: false,
  showBoundingBox: false,
  showInfo: false,
  wireframe: false,
  shading: 'lambert',
}
const VIEW_BACKGROUND = '#0d1117'
const CIRCLE_MIN_RADIUS_MM = 0.2
const CIRCLE_RADIUS_VARIANCE_RATIO = 0.02
const CIRCLE_PLANAR_TOLERANCE_MM = 0.02
const remoteModelUrlParam = searchParams.get('url') || ''
const remoteRepoParam = searchParams.get('repo') || ''
const remoteRefParam = searchParams.get('ref') || ''
const remoteLabelParam = searchParams.get('label') || ''
let remoteRequestedFile = ''

function sanitizeView(input) {
  const out = {}
  for (const key of ['rotX', 'rotY', 'rotZ', 'panX', 'panY', 'zoom']) {
    const raw = input?.[key]
    if (raw === null || raw === undefined || raw === '') continue
    const value = Number(raw)
    if (!Number.isFinite(value)) continue
    out[key] = key === 'zoom' ? Math.min(30, Math.max(0.1, value)) : value
  }
  for (const key of ['showGrid', 'showAxes', 'showBoundingBox', 'showInfo', 'wireframe']) {
    if (typeof input?.[key] === 'boolean') out[key] = input[key]
  }
  if (storageShadingModes.includes(input?.shading)) out.shading = input.shading
  return out
}

const configuredFallbackView = { ...fallbackView, ...sanitizeView(options.fallbackView || {}) }

async function readViewDefaults() {
  if (runtimeMode === 'extension') {
    try {
      const res = await fetch(viewApiUrl, { cache: 'no-store' })
      if (!res.ok) return { ...configuredFallbackView }
      return { ...configuredFallbackView, ...sanitizeView(await res.json()) }
    } catch {
      return { ...configuredFallbackView }
    }
  }
  try {
    const raw = localStorage.getItem(VIEW_STORAGE_KEY)
    if (!raw) return { ...configuredFallbackView }
    return { ...configuredFallbackView, ...sanitizeView(JSON.parse(raw)) }
  } catch {
    return { ...configuredFallbackView }
  }
}

async function writeViewDefaults(view) {
  if (runtimeMode === 'extension') {
    const payload = { ...configuredFallbackView, ...sanitizeView(view) }
    try {
      const res = await fetch(viewApiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (res.ok) {
        baseView = { ...configuredFallbackView, ...sanitizeView(await res.json()) }
        return baseView
      }
    } catch {}
    baseView = { ...configuredFallbackView, ...sanitizeView(payload) }
    return baseView
  }
  const merged = { ...baseView, ...sanitizeView(view) }
  baseView = { ...configuredFallbackView, ...sanitizeView(merged) }
  try {
    localStorage.setItem(VIEW_STORAGE_KEY, JSON.stringify(baseView))
  } catch {}
  return baseView
}

function detectStlFormat(buffer) {
  if (!buffer || buffer.byteLength < 6) return 'binary'
  if (buffer.byteLength >= 84) {
    const facetCount = new DataView(buffer).getUint32(80, true)
    if (84 + facetCount * 50 === buffer.byteLength) return 'binary'
  }
  const head = new TextDecoder().decode(new Uint8Array(buffer, 0, Math.min(buffer.byteLength, 256))).trimStart()
  return /^solid\b/i.test(head) ? 'ascii' : 'binary'
}

function parseAsciiStl(text) {
  if (!text) return { facets: 0, vertices: 0, uniqueVertices: 0, bounds: null, format: 'ascii', triangles: [] }
  const matches = [...text.matchAll(/vertex\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)/g)]
  const vertices = matches.map((m) => [Number(m[1]), Number(m[2]), Number(m[3])])
  const triangles = []
  let min = [Infinity, Infinity, Infinity]
  let max = [-Infinity, -Infinity, -Infinity]
  for (let i = 0; i < vertices.length; i += 3) {
    if (i + 2 < vertices.length) triangles.push([vertices[i], vertices[i + 1], vertices[i + 2]])
  }
  for (const v of vertices) {
    min = [Math.min(min[0], v[0]), Math.min(min[1], v[1]), Math.min(min[2], v[2])]
    max = [Math.max(max[0], v[0]), Math.max(max[1], v[1]), Math.max(max[2], v[2])]
  }
  return {
    facets: (text.match(/\bfacet normal\b/g) || []).length,
    vertices: vertices.length,
    uniqueVertices: new Set(vertices.map((v) => `${v[0]},${v[1]},${v[2]}`)).size,
    bounds: vertices.length ? {
      min: { x: min[0], y: min[1], z: min[2] },
      max: { x: max[0], y: max[1], z: max[2] },
      size: { x: max[0] - min[0], y: max[1] - min[1], z: max[2] - min[2] },
    } : null,
    format: 'ascii',
    triangles,
  }
}

function parseBinaryStl(buffer) {
  if (!buffer || buffer.byteLength < 84) {
    return { facets: 0, vertices: 0, uniqueVertices: 0, bounds: null, format: 'binary', triangles: [] }
  }
  const dv = new DataView(buffer)
  const facetCount = dv.getUint32(80, true)
  const triangles = []
  let min = [Infinity, Infinity, Infinity]
  let max = [-Infinity, -Infinity, -Infinity]
  for (let i = 0; i < facetCount; i += 1) {
    const offset = 84 + i * 50
    if (offset + 48 > buffer.byteLength) break
    const tri = [
      [dv.getFloat32(offset + 12, true), dv.getFloat32(offset + 16, true), dv.getFloat32(offset + 20, true)],
      [dv.getFloat32(offset + 24, true), dv.getFloat32(offset + 28, true), dv.getFloat32(offset + 32, true)],
      [dv.getFloat32(offset + 36, true), dv.getFloat32(offset + 40, true), dv.getFloat32(offset + 44, true)],
    ]
    triangles.push(tri)
    for (const v of tri) {
      min = [Math.min(min[0], v[0]), Math.min(min[1], v[1]), Math.min(min[2], v[2])]
      max = [Math.max(max[0], v[0]), Math.max(max[1], v[1]), Math.max(max[2], v[2])]
    }
  }
  return {
    facets: triangles.length,
    vertices: triangles.length * 3,
    uniqueVertices: new Set(triangles.flat().map((v) => `${v[0]},${v[1]},${v[2]}`)).size,
    bounds: triangles.length ? {
      min: { x: min[0], y: min[1], z: min[2] },
      max: { x: max[0], y: max[1], z: max[2] },
      size: { x: max[0] - min[0], y: max[1] - min[1], z: max[2] - min[2] },
    } : null,
    format: 'binary',
    triangles,
  }
}

function parseStlBuffer(buffer) {
  return detectStlFormat(buffer) === 'ascii'
    ? parseAsciiStl(new TextDecoder().decode(new Uint8Array(buffer)))
    : parseBinaryStl(buffer)
}

async function inflateDeflateRaw(bytes) {
  if (typeof DecompressionStream !== 'function') {
    throw new Error('3MF decompression is not supported in this browser.')
  }
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw'))
  const buffer = await new Response(stream).arrayBuffer()
  return new Uint8Array(buffer)
}

function firstChildByLocalName(node, name) {
  return childrenByLocalName(node, name)[0] || null
}

function descendantsByLocalName(node, name) {
  return [...(node?.getElementsByTagName('*') || [])].filter((child) => child.localName === name)
}

function averageHexColors(colors) {
  const entries = colors.map(normalizeColor).filter(Boolean)
  if (!entries.length) return null
  const total = entries.reduce((acc, color) => {
    acc[0] += Number.parseInt(color.slice(1, 3), 16)
    acc[1] += Number.parseInt(color.slice(3, 5), 16)
    acc[2] += Number.parseInt(color.slice(5, 7), 16)
    return acc
  }, [0, 0, 0])
  const scale = entries.length
  return `#${total.map((value) => Math.round(value / scale).toString(16).padStart(2, '0')).join('')}`
}

function normalizeZipPath(basePath, target) {
  const rawTarget = String(target || '').replaceAll('\\', '/').trim()
  if (!rawTarget) return String(basePath || '').replace(/^\/+/, '')
  const combined = rawTarget.startsWith('/')
    ? rawTarget.replace(/^\/+/, '')
    : `${String(basePath || '').replace(/^\/+/, '').split('/').slice(0, -1).join('/')}/${rawTarget}`
  const normalized = []
  for (const segment of combined.split('/').filter(Boolean)) {
    if (segment === '.') continue
    if (segment === '..') normalized.pop()
    else normalized.push(segment)
  }
  return normalized.join('/')
}

const MODEL_UNIT_TO_MM = Object.freeze({
  micron: 0.001,
  millimeter: 1,
  centimeter: 10,
  inch: 25.4,
  foot: 304.8,
  meter: 1000,
})

function documentUnitScale(modelDoc, documentPath) {
  const unit = String(modelDoc?.documentElement?.getAttribute('unit') || 'millimeter').trim().toLowerCase()
  const scale = MODEL_UNIT_TO_MM[unit]
  if (!scale) throw new Error(`Unsupported 3MF unit "${unit}" in ${documentPath}`)
  return scale
}

function parseTransformString(transform, context) {
  if (transform == null) return null
  const raw = String(transform).trim()
  if (!raw) return null
  const values = raw.split(/[,\s]+/).map(Number)
  if (values.length !== 12 || values.some((value) => !Number.isFinite(value))) {
    throw new Error(`Invalid 3MF transform${context ? ` in ${context}` : ''}`)
  }
  return values
}

function composeTransforms(parent, child, childUnitScale = 1) {
  return compose3mfTransforms(parent, child, childUnitScale)
}

async function readZipEntry(buffer, entryName) {
  const bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer)
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
  const decoder = new TextDecoder()

  for (let offset = bytes.length - 22; offset >= Math.max(0, bytes.length - 65557); offset -= 1) {
    if (view.getUint32(offset, true) !== 0x06054b50) continue
    let cursor = view.getUint32(offset + 16, true)
    const entries = view.getUint16(offset + 10, true)
    if (cursor === 0xffffffff || entries === 0xffff) throw new Error('ZIP64 3MF archives are not supported in this browser viewer.')
    for (let index = 0; index < entries; index += 1) {
      if (view.getUint32(cursor, true) !== 0x02014b50) throw new Error('Invalid 3MF central directory')
      const compression = view.getUint16(cursor + 10, true)
      const compressedSize = view.getUint32(cursor + 20, true)
      const nameLength = view.getUint16(cursor + 28, true)
      const extraLength = view.getUint16(cursor + 30, true)
      const commentLength = view.getUint16(cursor + 32, true)
      const localOffset = view.getUint32(cursor + 42, true)
      if (compressedSize === 0xffffffff || localOffset === 0xffffffff) throw new Error('ZIP64 3MF archives are not supported in this browser viewer.')
      const name = decoder.decode(bytes.slice(cursor + 46, cursor + 46 + nameLength))
      if (name === entryName) {
        if (view.getUint32(localOffset, true) !== 0x04034b50) throw new Error('Invalid 3MF local header')
        const localNameLength = view.getUint16(localOffset + 26, true)
        const localExtraLength = view.getUint16(localOffset + 28, true)
        const start = localOffset + 30 + localNameLength + localExtraLength
        const data = bytes.slice(start, start + compressedSize)
        if (compression === 0) return data
        if (compression === 8) return inflateDeflateRaw(data)
        throw new Error(`Unsupported 3MF compression method: ${compression}`)
      }
      cursor += 46 + nameLength + extraLength + commentLength
    }
    break
  }
  throw new Error(`3MF entry not found: ${entryName}`)
}

function parseXmlDocument(xml, documentPath) {
  const doc = new DOMParser().parseFromString(xml, 'application/xml')
  if (doc.documentElement?.localName === 'parsererror' || descendantsByLocalName(doc, 'parsererror').length) {
    throw new Error(`Invalid 3MF XML document: ${documentPath}`)
  }
  return doc
}

async function load3mfDocument(buffer, entryName, cache) {
  const normalized = String(entryName || '').replace(/^\/+/, '')
  if (!cache.has(normalized)) {
    const xml = new TextDecoder().decode(await readZipEntry(buffer, normalized))
    cache.set(normalized, parseXmlDocument(xml, normalized))
  }
  return cache.get(normalized)
}

async function read3mfStartPath(buffer) {
  const xml = new TextDecoder().decode(await readZipEntry(buffer, '_rels/.rels'))
  const doc = parseXmlDocument(xml, '_rels/.rels')
  const relationship = childrenByLocalName(doc.documentElement, 'Relationship')
    .find((entry) => (entry.getAttribute('Type') || '').includes('/3dmodel'))
  const target = relationship?.getAttribute('Target')
  if (!target) throw new Error('3MF start part not found in _rels/.rels')
  return normalizeZipPath('', target)
}

function resourceColorLookup(modelDoc) {
  const resources = firstChildByLocalName(modelDoc.documentElement, 'resources')
  const lookup = new Map()
  if (!resources) return lookup

  for (const group of childrenByLocalName(resources, 'basematerials')) {
    lookup.set(group.getAttribute('id'), childrenByLocalName(group, 'base').map((entry) => normalizeColor(entry.getAttribute('displaycolor'))))
  }
  for (const group of childrenByLocalName(resources, 'colorgroup')) {
    lookup.set(group.getAttribute('id'), childrenByLocalName(group, 'color').map((entry) => normalizeColor(entry.getAttribute('color')) || normalizeColor(entry.getAttribute('displaycolor'))))
  }
  return lookup
}

function resourceObjectLookup(modelDoc) {
  const resources = firstChildByLocalName(modelDoc.documentElement, 'resources')
  const lookup = new Map()
  if (!resources) return lookup
  for (const object of childrenByLocalName(resources, 'object')) {
    lookup.set(object.getAttribute('id'), object)
  }
  return lookup
}

function resolveColor(resourceLookup, pid, ...indices) {
  if (!pid) return null
  const palette = resourceLookup.get(pid)
  if (!palette?.length) return null
  const colors = indices
    .filter((index) => index != null && String(index).trim() !== '')
    .map((index) => Number(index))
    .filter((index) => Number.isInteger(index) && index >= 0 && index < palette.length)
    .map((index) => palette[index])
    .filter(Boolean)
  return averageHexColors(colors)
}

function parseRequiredFiniteAttributes(node, attributes, message, integer = false) {
  return attributes.map((attribute) => {
    const raw = node.getAttribute(attribute)
    if (raw == null || !String(raw).trim()) throw new Error(message)
    const value = Number(raw)
    if (!Number.isFinite(value) || (integer && !Number.isInteger(value))) throw new Error(message)
    return value
  })
}

function parse3mfVertex(vertex, documentPath, objectId, unitScale) {
  const coords = parseRequiredFiniteAttributes(
    vertex,
    ['x', 'y', 'z'],
    `Invalid 3MF vertex in ${documentPath} object ${objectId}`,
  )
  return coords.map((value) => value * unitScale)
}

function parse3mfTriangleIndices(triangle, documentPath, objectId, vertexCount) {
  const indices = parseRequiredFiniteAttributes(
    triangle,
    ['v1', 'v2', 'v3'],
    `Invalid 3MF triangle in ${documentPath} object ${objectId}`,
    true,
  )
  if (!indices.every((index) => index >= 0 && index < vertexCount)) {
    throw new Error(`Invalid 3MF triangle in ${documentPath} object ${objectId}`)
  }
  return indices
}

function create3mfStats() {
  return {
    facets: 0,
    vertices: 0,
    uniqueVertices: new Set(),
    min: [Infinity, Infinity, Infinity],
    max: [-Infinity, -Infinity, -Infinity],
  }
}

function add3mfTriangle(stats, triangle) {
  stats.facets += 1
  stats.vertices += 3
  for (const vertex of triangle) {
    stats.uniqueVertices.add(`${vertex[0]},${vertex[1]},${vertex[2]}`)
    stats.min[0] = Math.min(stats.min[0], vertex[0])
    stats.min[1] = Math.min(stats.min[1], vertex[1])
    stats.min[2] = Math.min(stats.min[2], vertex[2])
    stats.max[0] = Math.max(stats.max[0], vertex[0])
    stats.max[1] = Math.max(stats.max[1], vertex[1])
    stats.max[2] = Math.max(stats.max[2], vertex[2])
  }
}

function parse3mfComponentTarget(documentPath, objectId, explicitPath) {
  const rawObjectId = String(objectId || '')
  const rawExplicitPath = String(explicitPath || '')
  if (rawObjectId.includes('#')) {
    const [pathPart, objectPart] = rawObjectId.split('#', 2)
    return {
      documentPath: normalizeZipPath(documentPath, pathPart),
      objectId: objectPart,
    }
  }
  if (rawExplicitPath.includes('#')) {
    const [pathPart, objectPart] = rawExplicitPath.split('#', 2)
    return {
      documentPath: normalizeZipPath(documentPath, pathPart),
      objectId: objectPart || rawObjectId,
    }
  }
  return {
    documentPath: rawExplicitPath ? normalizeZipPath(documentPath, rawExplicitPath) : documentPath,
    objectId: rawObjectId,
  }
}

async function collect3mfObject(buffer, documents, documentPath, objectId, parentTransform, inheritedColor, triangles, triangleColors, resourceCache, objectCache, unitCache, stats, activeObjects, orcaAssignment) {
  const activeKey = `${documentPath}#${objectId}`
  if (activeObjects.has(activeKey)) throw new Error(`3MF component cycle detected at ${activeKey}`)
  activeObjects.add(activeKey)
  try {
    const modelDoc = await load3mfDocument(buffer, documentPath, documents)
    const resourceLookup = resourceCache.get(documentPath) || resourceColorLookup(modelDoc)
    const objects = objectCache.get(documentPath) || resourceObjectLookup(modelDoc)
    const unitScale = unitCache.get(documentPath) || documentUnitScale(modelDoc, documentPath)
    resourceCache.set(documentPath, resourceLookup)
    objectCache.set(documentPath, objects)
    unitCache.set(documentPath, unitScale)
    const object = objects.get(String(objectId))
    if (!object) throw new Error(`3MF object not found: ${documentPath}#${objectId}`)

    const orcaColor = orcaAssignment?.parts.get(String(objectId)) || orcaAssignment?.color
    const objectColor = orcaColor || resolveColor(resourceLookup, object.getAttribute('pid'), object.getAttribute('pindex')) || inheritedColor
    const components = firstChildByLocalName(object, 'components')
    if (components) {
      for (const component of childrenByLocalName(components, 'component')) {
        const target = parse3mfComponentTarget(
          documentPath,
          component.getAttribute('objectid'),
          component.getAttribute('p:path') || component.getAttribute('path') || '',
        )
        const transform = composeTransforms(
          parentTransform,
          parseTransformString(component.getAttribute('transform'), `${documentPath}#${objectId}`),
          unitScale,
        )
        await collect3mfObject(
          buffer,
          documents,
          target.documentPath,
          target.objectId,
          transform,
          objectColor,
          triangles,
          triangleColors,
          resourceCache,
          objectCache,
          unitCache,
          stats,
          activeObjects,
          orcaAssignment ? { ...orcaAssignment, color: orcaColor } : undefined,
        )
      }
      return
    }

    const mesh = firstChildByLocalName(object, 'mesh')
    if (!mesh) return
    const vertices = childrenByLocalName(firstChildByLocalName(mesh, 'vertices'), 'vertex').map((vertex) => (
      transform3mfPoint(parse3mfVertex(vertex, documentPath, objectId, unitScale), parentTransform)
    ))

    for (const triangle of childrenByLocalName(firstChildByLocalName(mesh, 'triangles'), 'triangle')) {
      const indices = parse3mfTriangleIndices(triangle, documentPath, objectId, vertices.length)
      const triangleVertices = indices.map((index) => vertices[index])
      triangles.push(triangleVertices)
      add3mfTriangle(stats, triangleVertices)
      triangleColors.push(
        orcaColor || resolveColor(
          resourceLookup,
          triangle.getAttribute('pid') || object.getAttribute('pid'),
          triangle.getAttribute('p1'),
          triangle.getAttribute('p2'),
          triangle.getAttribute('p3'),
          triangle.getAttribute('pindex'),
        ) || objectColor || '#d6d9de',
      )
    }
  } finally {
    activeObjects.delete(activeKey)
  }
}

function finalize3mfStats(stats) {
  return {
    facets: stats.facets,
    vertices: stats.vertices,
    uniqueVertices: stats.uniqueVertices.size,
    bounds: stats.facets
      ? {
        min: { x: stats.min[0], y: stats.min[1], z: stats.min[2] },
        max: { x: stats.max[0], y: stats.max[1], z: stats.max[2] },
        size: { x: stats.max[0] - stats.min[0], y: stats.max[1] - stats.min[1], z: stats.max[2] - stats.min[2] },
      }
      : null,
    format: '3mf',
  }
}

async function read3mfPlateAssignments(buffer) {
  let xml
  try {
    xml = new TextDecoder().decode(await readZipEntry(buffer, 'Metadata/model_settings.config'))
  } catch {
    return new Map()
  }
  const doc = parseXmlDocument(xml, 'Metadata/model_settings.config')
  const assignments = new Map()
  for (const plate of Array.from(doc.getElementsByTagName('plate'))) {
    const plateId = childrenByLocalName(plate, 'metadata')
      .find((entry) => entry.getAttribute('key') === 'plater_id')
      ?.getAttribute('value')
    if (!plateId) continue
    for (const instance of childrenByLocalName(plate, 'model_instance')) {
      const objectId = childrenByLocalName(instance, 'metadata')
        .find((entry) => entry.getAttribute('key') === 'object_id')
        ?.getAttribute('value')
      if (objectId) assignments.set(objectId, plateId)
    }
  }
  return assignments
}

async function read3mfProjectMetadata(buffer) {
  let xml
  try {
    xml = new TextDecoder().decode(await readZipEntry(buffer, 'Metadata/ghouls_grip_print_metadata.xml'))
  } catch {
    return {}
  }
  const doc = parseXmlDocument(xml, 'Metadata/ghouls_grip_print_metadata.xml')
  const metadata = {}
  for (const entry of Array.from(doc.getElementsByTagName('metadata'))) {
    const name = entry.getAttribute('name')
    if (name) metadata[name] = entry.getAttribute('value') || ''
  }
  return metadata
}

async function parse3mfBuffer(buffer) {
  const documents = new Map()
  const resourceCache = new Map()
  const objectCache = new Map()
  const unitCache = new Map()
  const rootPath = await read3mfStartPath(buffer)
  const rootDoc = await load3mfDocument(buffer, rootPath, documents)
  const rootUnitScale = documentUnitScale(rootDoc, rootPath)
  const triangles = []
  const triangleColors = []
  const stats = create3mfStats()
  const plateAssignments = await read3mfPlateAssignments(buffer)
  const projectMetadata = await read3mfProjectMetadata(buffer)
  const readOptionalEntry = async (path) => {
    try {
      return new TextDecoder().decode(await readZipEntry(buffer, path))
    } catch (error) {
      if (error.message === `3MF entry not found: ${path}`) return null
      throw error
    }
  }
  const settingsXml = await readOptionalEntry('Metadata/model_settings.config')
  const projectJson = await readOptionalEntry('Metadata/project_settings.config')
  const orcaAssignments = settingsXml && projectJson
    ? orcaMaterialAssignments(
      parseXmlDocument(settingsXml, 'Metadata/model_settings.config'),
      JSON.parse(projectJson),
    )
    : new Map()
  const plateGroups = new Map()
  const build = firstChildByLocalName(rootDoc.documentElement, 'build')
  if (!build) throw new Error(`3MF start model document is missing <build>: ${rootPath}`)

  for (const item of childrenByLocalName(build, 'item')) {
    const objectId = item.getAttribute('objectid')
    const itemTriangles = []
    const itemColors = []
    const itemStats = create3mfStats()
    await collect3mfObject(
      buffer,
      documents,
      rootPath,
      objectId,
      composeTransforms(null, parseTransformString(item.getAttribute('transform'), `${rootPath} build`), rootUnitScale),
      null,
      itemTriangles,
      itemColors,
      resourceCache,
      objectCache,
      unitCache,
      itemStats,
      new Set(),
      orcaAssignments.get(objectId),
    )
    triangles.push(...itemTriangles)
    triangleColors.push(...itemColors)
    for (const triangle of itemTriangles) add3mfTriangle(stats, triangle)
    const plateId = plateAssignments.get(objectId) || '1'
    const plate = plateGroups.get(plateId) || {
      id: plateId,
      triangles: [],
      triangleColors: [],
      stats: create3mfStats(),
    }
    plate.triangles.push(...itemTriangles)
    plate.triangleColors.push(...itemColors)
    for (const triangle of itemTriangles) add3mfTriangle(plate.stats, triangle)
    plateGroups.set(plateId, plate)
  }

  const projectColor = normalizeColor(projectMetadata.materialColorHex)
  if (projectColor) {
    for (let index = 0; index < triangleColors.length; index += 1) {
      if (triangleColors[index] === '#d6d9de') triangleColors[index] = projectColor
    }
    for (const plate of plateGroups.values()) {
      for (let index = 0; index < plate.triangleColors.length; index += 1) {
        if (plate.triangleColors[index] === '#d6d9de') {
          plate.triangleColors[index] = projectColor
        }
      }
    }
  }

  return {
    ...finalize3mfStats(stats),
    triangles,
    triangleColors,
    plates: [...plateGroups.values()]
      .sort((left, right) => Number(left.id) - Number(right.id))
      .map((plate) => ({
        id: plate.id,
        triangles: plate.triangles,
        triangleColors: plate.triangleColors,
        stats: finalize3mfStats(plate.stats),
      })),
    projectMetadata,
  }
}

async function parseModelBuffer(modelPath, buffer) {
  return modelPath.toLowerCase().endsWith('.3mf') ? parse3mfBuffer(buffer) : parseStlBuffer(buffer)
}

let baseView = { ...configuredFallbackView };
let reloadInFlight = false;
const VIEW_PRESETS = {
  isometric: { rotX: -60, rotY: 45, rotZ: 0 },
  top: { rotX: 0, rotY: 0, rotZ: 0 },
  bottom: { rotX: 180, rotY: 0, rotZ: 0 },
  front: { rotX: -90, rotY: 0, rotZ: 0 },
  back: { rotX: -90, rotY: 180, rotZ: 0 },
  left: { rotX: -90, rotY: 90, rotZ: 0 },
  right: { rotX: -90, rotY: -90, rotZ: 0 }
};
let rotX = baseView.rotX, rotY = baseView.rotY, rotZ = baseView.rotZ || 0, panX = baseView.panX, panY = baseView.panY, objectX = 0, objectY = 0;
let modelRotX = 0, modelRotY = 0, modelRotZ = 0;
let isDragging = false, isShiftDrag = false, isRightDrag = false, lastX = 0, lastY = 0, dragMoved = 0;
const canvas = document.getElementById('view');
const ctx = canvas.getContext('2d');
const fileChooser = document.getElementById('fileChooser');
const plateField = document.getElementById('plateField');
const plateChooser = document.getElementById('plateChooser');
const imageActions = document.getElementById('imageActions')
const projectPreviewBtn = document.getElementById('projectPreviewBtn')
const plateSupportActions = document.getElementById('plateSupportActions')
const projectImageDialog = document.getElementById('projectImageDialog')
const projectImage = document.getElementById('projectImage')
const projectImageCaption = document.getElementById('projectImageCaption')
const reloadBtn = document.getElementById('reloadBtn');
const orcaField = document.getElementById('orcaField');
const openInOrcaBtn = document.getElementById('openInOrcaBtn');
const orcaStatus = document.getElementById('orcaStatus');
let orcaStatusTimer = null;
const loadingSpinner = document.getElementById('loadingSpinner');
const spinnerText = loadingSpinner?.querySelector('.spinner-text');

function setSpinner(visible, text = 'Loading plates…') {
  if (!loadingSpinner) return;
  if (visible) {
    if (spinnerText) spinnerText.textContent = text;
    loadingSpinner.hidden = false;
  } else {
    loadingSpinner.hidden = true;
  }
}
const projectImageAvailability = new Map()

function resolveProjectImageUrl(imagePath) {
  if (!/^docs\/images\/[^/\\\u0000-\u001f]+\.png$/i.test(String(imagePath || ''))) return ''
  if (runtimeMode === 'extension') {
    return `${projectImageApiUrl}?path=${encodeURIComponent(imagePath)}`
  }
  return `./${imagePath.split('/').map(encodeURIComponent).join('/')}`
}

async function verifyProjectImageButton(button) {
  const imageUrl = resolveProjectImageUrl(button.dataset.projectImage)
  if (!imageUrl) {
    button.disabled = true
    button.title = 'Invalid project image path'
    return
  }
  let availability = projectImageAvailability.get(imageUrl)
  if (!availability) {
    availability = fetch(imageUrl, { method: 'HEAD', cache: 'no-store' })
      .then((response) => ({ available: response.ok }))
      .catch((error) => ({ error: error instanceof Error ? error.message : String(error) }))
    projectImageAvailability.set(imageUrl, availability)
  }
  const result = await availability
  if (result.available) {
    button.disabled = false
    button.title = ''
  } else if (!result.error) {
    button.disabled = true
    button.title = `Screenshot not found: ${button.dataset.projectImage}`
  } else {
    button.disabled = true
    button.title = `Preview unavailable: ${result.error}`
  }
  if (![...imageActions.querySelectorAll('button')].some((item) => !item.hidden)) {
    imageActions.hidden = true
  }
}

function updateProjectImageActions(file = loadedModelInfo?.path || '') {
  const previewPath = projectPreviewImagePath(file)
  projectPreviewBtn.hidden = !previewPath
  projectPreviewBtn.disabled = Boolean(previewPath)
  if (previewPath) {
    projectPreviewBtn.dataset.projectImage = previewPath
    projectPreviewBtn.dataset.projectImageCaption = `${modelBasename(file)} full-project preview`
    void verifyProjectImageButton(projectPreviewBtn)
  }

  plateSupportActions.innerHTML = renderPlateSupportPreviewActions(file, loadedPlates)
  plateSupportActions.hidden = !plateSupportActions.childElementCount
  plateSupportActions.querySelectorAll('button[data-project-image]').forEach((button) => {
    void verifyProjectImageButton(button)
  })
  imageActions.hidden = !previewPath && plateSupportActions.hidden
}

root.addEventListener('click', (event) => {
  const button = event.target.closest?.('button[data-project-image]')
  if (!button || button.disabled) return
  const imageUrl = resolveProjectImageUrl(button.dataset.projectImage)
  if (!imageUrl) return
  projectImageCaption.textContent = button.dataset.projectImageCaption || 'Project image'
  projectImage.alt = projectImageCaption.textContent
  projectImage.onerror = () => {
    button.disabled = true
    button.title = `Preview unavailable: ${button.dataset.projectImage}`
    projectImageCaption.textContent = button.title
    projectImageDialog.close()
  }
  projectImage.src = imageUrl
  projectImageDialog.showModal()
})
document.getElementById('closeProjectImageBtn').addEventListener('click', () => projectImageDialog.close())
projectImageDialog.addEventListener('click', (event) => {
  if (event.target === projectImageDialog) projectImageDialog.close()
})
projectImageDialog.addEventListener('close', () => {
  projectImage.removeAttribute('src')
  projectImage.onerror = null
})

function updateOrcaAction(file = '', modelPath = '') {
  const source = file ? modelSource(file) : null
  const openUrl = create3mfOpenUrl(file, source?.downloadUrl || '', window.location.href)
  const canOpenLocally = runtimeMode === 'extension' && /\.3mf$/i.test(String(file || '').trim()) &&
    Boolean(openInOrcaApiUrl) && Boolean(openInOrcaNonce)
  orcaField.hidden = !openUrl && !canOpenLocally
  openInOrcaBtn.disabled = !openUrl && !canOpenLocally
  openInOrcaBtn.dataset.openUrl = openUrl
  openInOrcaBtn.dataset.file = file
  openInOrcaBtn.dataset.modelPath = modelPath
  clearTimeout(orcaStatusTimer)
  orcaStatus.hidden = true
  orcaStatus.textContent = ''
}
function emitModelChange(file = fileChooser.value || currentFile || '') {
  const source = file ? modelSource(file) : null
  root.dispatchEvent(new CustomEvent('stl-canvas:model-change', { detail: { file, url: source?.downloadUrl || '' } }))
}
const autoReloadInput = document.getElementById('autoReload');
const autoReloadField = autoReloadInput.closest('.field');
const zoomInput = document.getElementById('zoom');
const wireframeInput = document.getElementById('wireframe');
const shadingInput = document.getElementById('shading');
const showGridInput = document.getElementById('showGrid');
const showAxesInput = document.getElementById('showAxes');
const showBoxInput = document.getElementById('showBoundingBox');
const showInfoInput = document.getElementById('showInfo');
const infoBox = document.getElementById('info');
const measureModeInput = document.getElementById('measureMode');
const measurePanel = document.getElementById('measurePanel');
const measureClearBtn = document.getElementById('measureClear');
showGridInput.checked = baseView.showGrid;
if (pollIntervalMs <= 0 && autoReloadField) autoReloadField.hidden = true
showAxesInput.checked = baseView.showAxes;
showBoxInput.checked = baseView.showBoundingBox;
showInfoInput.checked = baseView.showInfo;
wireframeInput.checked = baseView.wireframe;
shadingInput.value = baseView.shading;
let rawTriangles = [];
let triangles = [];
let rawTriangleColors = [];
let triangleColors = [];
let loadedTriangles = [];
let loadedTriangleColors = [];
let loadedPlates = [];
let overviewPlates = [];
let loadedModelInfo = null;
// Crease-aware per-corner normals, rebuilt whenever the geometry changes.
let cornerNormals = null, faceNormals = null;
// Measure gizmo state: welded points, crease edges, fitted circles.
let measurePoints = [], measureEdges = [], measureCircles = [], triVerts = null, vertexEdges = null;
let creaseIndex = null, vertexCircle = null;
let hoverFeature = null, pickedFeatures = [], lastPointer = null;
// Software z-buffer target so walls can never show through each other.
let rasterCanvas = null, rasterCtx = null, rasterImage = null, depthBuffer = null, pickBuffer = null;
let lastProjection = null;
let modelBounds = null;
let currentFile = defaultModelFile;
// Anycubic Kobra S1 build plate: 250 x 250 mm.
const BED_SIZE_MM = 250;
const MM_TO_PX = 1.8;
let currentMtime = '';
let knownFiles = [];
let savedZoom = Number.isFinite(baseView.zoom) ? baseView.zoom : null;
let saveTimer = null;
let pollTimer = null;
function saveView() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    writeViewDefaults({
      rotX: rotX, rotY: rotY, rotZ: rotZ, panX: panX, panY: panY, zoom: parseFloat(zoomInput.value),
      wireframe: wireframeInput.checked, shading: shadingInput.value,
      showGrid: showGridInput.checked, showAxes: showAxesInput.checked,
      showBoundingBox: showBoxInput.checked, showInfo: showInfoInput.checked
    });
  }, 400);
}

// Model rotation is baked into the geometry so the part still sits flat on the plate.
function applyModelRotation() {
  const rx = modelRotX * Math.PI / 180, ry = modelRotY * Math.PI / 180, rz = modelRotZ * Math.PI / 180;
  const cx = Math.cos(rx), sx = Math.sin(rx), cy = Math.cos(ry), sy = Math.sin(ry), cz = Math.cos(rz), sz = Math.sin(rz);
  triangles = rawTriangles.map((tri) => tri.map((v) => {
    let x = v[0], y = v[1], z = v[2];
    let t = y * cx - z * sx; z = y * sx + z * cx; y = t;
    t = x * cy + z * sy; z = -x * sy + z * cy; x = t;
    t = x * cz - y * sz; y = x * sz + y * cz; x = t;
    return [x, y, z];
  }));
  triangleColors = [...rawTriangleColors];
  modelBounds = computeBounds(triangles) || modelBounds;
  computeCornerNormals();
}

function applyPlateSelection() {
  const selected = plateChooser.value
  const plate = selected === 'all'
    ? null
    : loadedPlates.find((candidate) => String(candidate.id) === selected)
  const overview = !plate && overviewPlates.length > 1
  const sourceTriangles = plate?.triangles || (overview ? overviewPlates.flatMap((entry) => entry.triangles) : loadedTriangles)
  const sourceColors = plate?.triangleColors || (overview ? overviewPlates.flatMap((entry) => entry.triangleColors) : loadedTriangleColors)
  rawTriangles = []
  rawTriangleColors = []
  for (let index = 0; index < sourceTriangles.length; index += 1) {
    const tri = sourceTriangles[index]
    if (!Array.isArray(tri) || tri.length !== 3) continue
    rawTriangles.push(tri)
    rawTriangleColors.push(
      typeof sourceColors[index] === 'string'
        ? sourceColors[index]
        : '#d6d9de',
    )
  }
  modelBounds = plate?.stats?.bounds || computeBounds(rawTriangles)
  applyModelRotation()
  renderModelMeta()
}

function renderModelMeta() {
  if (!loadedModelInfo) return
  const selected = plateChooser.value
  const plate = selected === 'all'
    ? null
    : loadedPlates.find((candidate) => String(candidate.id) === selected)
  const stats = plate?.stats || loadedModelInfo.stats
  const bounds = plate?.stats?.bounds || computeBounds(rawTriangles)
  const projectMetadata = loadedModelInfo.projectMetadata || {}
  const printSummaryValues = formatPrintMetadataSummary(projectMetadata)
  const metadataValue = (key, fallback = 'not available') => {
    const value = projectMetadata[key]
    return value && value !== 'unknown' ? value : fallback
  }
  const metadataWithUnit = (key, unit) => {
    const value = metadataValue(key)
    return value === 'not available' ? value : `${value} ${unit}`
  }
  const plateCount = metadataValue('plateCount', loadedPlates.length ? String(loadedPlates.length) : 'not available')
  const printFields = [
    ['Status', metadataValue('status')],
    ['Total print time', printSummaryValues.printTime],
    ['Total filament', metadataWithUnit('filamentUsageGrams', 'g')],
    ['Total filament length', metadataWithUnit('filamentUsageMillimeters', 'mm')],
    ['Total filament volume', metadataWithUnit('filamentUsageCubicMillimeters', 'mm³')],
    ['Total support material', printSummaryValues.supportUsage],
    ['Total support length', metadataWithUnit('supportFilamentMillimeters', 'mm')],
    ['Printer', metadataValue('printerProfile')],
    ['Nozzle', metadataWithUnit('nozzleDiameterMm', 'mm')],
    ['Process', metadataValue('processProfile')],
    ['Layer', metadataWithUnit('layerHeightMm', 'mm')],
    ['Filament profile', metadataValue('filamentProfile')],
    ['Material', metadataValue('materialType')],
    ['Color', metadataValue('materialColorName', metadataValue('materialColorHex'))],
    ['Bed', metadataValue('bedType')],
    ['Walls', metadataValue('wallLoops')],
    ['Infill', metadataValue('infillDensity')],
    ['Supports', metadataValue('supportPolicy')],
    ['Plates', plateCount],
  ]
  const printSummary = document.getElementById('printSummary')
  printSummary.hidden = !printSummaryValues.visible
  if (printSummaryValues.visible) {
    document.getElementById('summaryPrintTime').textContent = printSummaryValues.printTime
    document.getElementById('summaryMaterial').textContent = printSummaryValues.materialUsage
    document.getElementById('summarySupport').textContent = printSummaryValues.supportUsage
    document.getElementById('summaryLength').textContent = printSummaryValues.filamentLength
    document.getElementById('summaryStatus').textContent = printSummaryValues.status
    document.getElementById('summaryPlates').textContent = plateCount
  }
  const meta = document.getElementById('meta')
  const plateDetailsOpen = meta.querySelector('.plate-print-details')?.open || false
  meta.innerHTML = '<span><strong>File:</strong> ' + escapeHtml(loadedModelInfo.path) + '</span>' +
    (loadedModelInfo.source ? '<span><strong>Source:</strong> ' + escapeHtml(loadedModelInfo.source) + '</span>' : '') +
    '<span><strong>Format:</strong> ' + (stats.format === 'binary' ? 'Binary STL' : stats.format === 'ascii' ? 'ASCII STL' : '3MF') + '</span>' +
    (loadedPlates.length > 1 ? '<span><strong>Plate:</strong> ' + (plate ? escapeHtml(String(plate.id)) : 'All') + '</span>' : '') +
    '<span><strong>Facets:</strong> ' + stats.facets + '</span>' +
    '<span><strong>Vertices:</strong> ' + stats.vertices + '</span>' +
    (bounds ? '<span><strong>Size (mm):</strong> ' + bounds.size.x.toFixed(1) + ' x ' + bounds.size.y.toFixed(1) + ' x ' + bounds.size.z.toFixed(1) + '</span>' : '') +
    renderPlatePrintDetails(projectMetadata, { file: loadedModelInfo.path }) +
    printFields.map(([label, value]) => `<span><strong>${escapeHtml(label)}:</strong> ${escapeHtml(value)}</span>`).join('')
  const plateDetails = meta.querySelector('.plate-print-details')
  if (plateDetails) plateDetails.open = plateDetailsOpen
  updateProjectImageActions(loadedModelInfo.path)
  meta.querySelectorAll('button[data-project-image]').forEach((button) => {
    void verifyProjectImageButton(button)
  })
}
// Average face normals per welded vertex, but fall back to the face
// normal across creases so 90-degree corners stay crisp.
function computeCornerNormals() {
  const n = triangles.length;
  const faceN = new Float32Array(n * 3);
  const acc = new Map();
  const key = (v) => Math.round(v[0] * 1000) + '|' + Math.round(v[1] * 1000) + '|' + Math.round(v[2] * 1000);
  for (let i = 0; i < n; i++) {
    const t = triangles[i];
    const ax = t[1][0] - t[0][0], ay = t[1][1] - t[0][1], az = t[1][2] - t[0][2];
    const bx = t[2][0] - t[0][0], by = t[2][1] - t[0][1], bz = t[2][2] - t[0][2];
    let nx = ay * bz - az * by, ny = az * bx - ax * bz, nz = ax * by - ay * bx;
    const len = Math.hypot(nx, ny, nz) || 1;
    nx /= len; ny /= len; nz /= len;
    faceN[i * 3] = nx; faceN[i * 3 + 1] = ny; faceN[i * 3 + 2] = nz;
    for (let j = 0; j < 3; j++) {
      const k = key(t[j]);
      let a = acc.get(k);
      if (!a) { a = [0, 0, 0]; acc.set(k, a); }
      a[0] += nx; a[1] += ny; a[2] += nz;
    }
  }
  const out = new Float32Array(n * 9);
  const creaseCos = Math.cos(40 * Math.PI / 180);
  for (let i = 0; i < n; i++) {
    const t = triangles[i];
    const fx = faceN[i * 3], fy = faceN[i * 3 + 1], fz = faceN[i * 3 + 2];
    for (let j = 0; j < 3; j++) {
      const a = acc.get(key(t[j]));
      let nx = a[0], ny = a[1], nz = a[2];
      const l = Math.hypot(nx, ny, nz) || 1;
      nx /= l; ny /= l; nz /= l;
      if (nx * fx + ny * fy + nz * fz < creaseCos) { nx = fx; ny = fy; nz = fz; }
      out[i * 9 + j * 3] = nx; out[i * 9 + j * 3 + 1] = ny; out[i * 9 + j * 3 + 2] = nz;
    }
  }
  cornerNormals = out;
  faceNormals = faceN;
  buildMeasureFeatures();
}
// Weld vertices, collect the crease edges that a human would call an
// "edge", and fit circles to closed crease loops (bores, bosses, arcs).
// This mirrors the feature set of the OrcaSlicer measure gizmo:
// point, edge, circle and plane.
function buildMeasureFeatures() {
  measurePoints = [];
  measureEdges = [];
  measureCircles = [];
  triVerts = new Int32Array(triangles.length * 3);
  vertexEdges = null;
  if (!triangles.length) return;
  const index = new Map();
  const key = (v) => Math.round(v[0] * 1000) + '|' + Math.round(v[1] * 1000) + '|' + Math.round(v[2] * 1000);
  for (let i = 0; i < triangles.length; i++) {
    for (let j = 0; j < 3; j++) {
      const v = triangles[i][j];
      const k = key(v);
      let id = index.get(k);
      if (id === undefined) { id = measurePoints.length; index.set(k, id); measurePoints.push([v[0], v[1], v[2]]); }
      triVerts[i * 3 + j] = id;
    }
  }
  // Edge -> adjacent faces
  const edgeMap = new Map();
  for (let i = 0; i < triangles.length; i++) {
    for (let j = 0; j < 3; j++) {
      const a = triVerts[i * 3 + j], b = triVerts[i * 3 + (j + 1) % 3];
      const k = a < b ? a + '_' + b : b + '_' + a;
      let e = edgeMap.get(k);
      if (!e) { e = { a: Math.min(a, b), b: Math.max(a, b), f: [] }; edgeMap.set(k, e); }
      e.f.push(i);
    }
  }
  const creaseCos = Math.cos(18 * Math.PI / 180);
  for (const e of edgeMap.values()) {
    let crease = e.f.length !== 2;
    if (!crease) {
      const p = e.f[0] * 3, q = e.f[1] * 3;
      const d = faceNormals[p] * faceNormals[q] + faceNormals[p + 1] * faceNormals[q + 1] + faceNormals[p + 2] * faceNormals[q + 2];
      crease = d < creaseCos;
    }
    if (crease) measureEdges.push({ a: e.a, b: e.b });
  }
  // Adjacency over crease edges only, used for hover lookup and loops.
  vertexEdges = new Map();
  for (let i = 0; i < measureEdges.length; i++) {
    for (const v of [measureEdges[i].a, measureEdges[i].b]) {
      let list = vertexEdges.get(v);
      if (!list) { list = []; vertexEdges.set(v, list); }
      list.push(i);
    }
  }
  // Closed loops where every vertex has exactly two crease edges are
  // candidates for circles; accept them when the points are coplanar and
  // equidistant from their centroid.
  const seen = new Uint8Array(measureEdges.length);
  for (let start = 0; start < measureEdges.length; start++) {
    if (seen[start]) continue;
    const loop = [];
    let edgeIdx = start, vert = measureEdges[start].a;
    const first = vert;
    let ok = true;
    for (let guard = 0; guard < 4096; guard++) {
      seen[edgeIdx] = 1;
      loop.push(vert);
      const e = measureEdges[edgeIdx];
      const next = e.a === vert ? e.b : e.a;
      const around = vertexEdges.get(next);
      if (!around || around.length !== 2) { ok = false; break; }
      const nextEdge = around[0] === edgeIdx ? around[1] : around[0];
      if (next === first) break;
      if (seen[nextEdge]) { ok = false; break; }
      edgeIdx = nextEdge; vert = next;
    }
    if (!ok || loop.length < 8) continue;
    const circle = fitCircle(loop);
    if (circle) measureCircles.push(circle);
  }
  const creaseKey = (a, b) => (a < b ? a + '_' + b : b + '_' + a);
  creaseIndex = new Map();
  for (let i = 0; i < measureEdges.length; i++) creaseIndex.set(creaseKey(measureEdges[i].a, measureEdges[i].b), i);
  vertexCircle = new Map();
  for (let i = 0; i < measureCircles.length; i++) {
    for (const v of measureCircles[i].loop) if (!vertexCircle.has(v)) vertexCircle.set(v, i);
  }
}
function fitCircle(loop) {
  let cx = 0, cy = 0, cz = 0;
  for (const i of loop) { const p = measurePoints[i]; cx += p[0]; cy += p[1]; cz += p[2]; }
  const n = loop.length;
  cx /= n; cy /= n; cz /= n;
  let rSum = 0, rMin = Infinity, rMax = 0;
  for (const i of loop) {
    const p = measurePoints[i];
    const r = Math.hypot(p[0] - cx, p[1] - cy, p[2] - cz);
    rSum += r; if (r < rMin) rMin = r; if (r > rMax) rMax = r;
  }
  const r = rSum / n;
  if (r < CIRCLE_MIN_RADIUS_MM || rMax - rMin > Math.max(CIRCLE_PLANAR_TOLERANCE_MM, r * CIRCLE_RADIUS_VARIANCE_RATIO)) return null;
  // Plane fit: normal from the two widest spokes.
  const p0 = measurePoints[loop[0]], p1 = measurePoints[loop[Math.floor(n / 3)]], p2 = measurePoints[loop[Math.floor(2 * n / 3)]];
  const ax = p1[0] - p0[0], ay = p1[1] - p0[1], az = p1[2] - p0[2];
  const bx = p2[0] - p0[0], by = p2[1] - p0[1], bz = p2[2] - p0[2];
  let nx = ay * bz - az * by, ny = az * bx - ax * bz, nz = ax * by - ay * bx;
  const nl = Math.hypot(nx, ny, nz);
  if (nl < 1e-9) return null;
  nx /= nl; ny /= nl; nz /= nl;
  for (const i of loop) {
    const p = measurePoints[i];
    if (Math.abs((p[0] - cx) * nx + (p[1] - cy) * ny + (p[2] - cz) * nz) > CIRCLE_PLANAR_TOLERANCE_MM) return null;
  }
  return { center: [cx, cy, cz], normal: [nx, ny, nz], radius: r, loop };
}
function applyViewPreset(name) {
  const preset = VIEW_PRESETS[name] || VIEW_PRESETS.isometric;
  rotX = preset.rotX; rotY = preset.rotY; rotZ = preset.rotZ;
  panX = 0; panY = 0;
  fitView();
  draw();
  saveView();
}

function normalizeText(input) {
  return typeof input === 'string' ? input.trim() : ''
}

function normalizeRepoSlug(value) {
  const slug = normalizeText(value).replace(/^\/+|\/+$/g, '')
  return /^[^/]+\/[^/]+$/.test(slug) ? slug : ''
}

function encodePathSegments(path) {
  return String(path || '').split('/').filter(Boolean).map((segment) => encodeURIComponent(segment)).join('/')
}

function normalizeRemoteUrl(value) {
  const raw = normalizeText(value)
  if (!raw) return ''
  try {
    const url = new URL(raw, window.location.href)
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.toString() : ''
  } catch {
    return ''
  }
}

function buildRawGithubModelUrl(repoSlug, ref, file) {
  const [owner, repo] = repoSlug.split('/')
  return `https://raw.githubusercontent.com/${owner}/${repo}/${encodePathSegments(ref)}/models/${encodePathSegments(file)}`
}

function appendCacheBust(url) {
  return `${url}${url.includes('?') ? '&' : '?'}t=${Date.now()}`
}

function fileNameFromUrl(url) {
  try {
    const pathname = new URL(url).pathname
    const base = pathname.split('/').filter(Boolean).pop() || ''
    return decodeURIComponent(base)
  } catch {
    return ''
  }
}

function requestedRemoteEntry() {
  const directUrl = normalizeRemoteUrl(remoteModelUrlParam)
  if (directUrl) {
    const file = normalizeText(defaultModelFile) || normalizeText(remoteLabelParam) || fileNameFromUrl(directUrl) || 'remote-model'
    remoteRequestedFile = file
    return {
      file,
      fetchUrl: directUrl,
      downloadUrl: directUrl,
      cacheBust: false,
      sourceLabel: 'remote URL',
    }
  }
  const ref = normalizeText(remoteRefParam)
  const file = normalizeText(defaultModelFile)
  const repoSlug = normalizeRepoSlug(remoteRepoParam) || normalizeRepoSlug(`${repository.owner || ''}/${repository.repo || ''}`)
  if (!ref || !file || !repoSlug) return null
  remoteRequestedFile = file
  return {
    file,
    fetchUrl: buildRawGithubModelUrl(repoSlug, ref, file),
    downloadUrl: buildRawGithubModelUrl(repoSlug, ref, file),
    cacheBust: false,
    sourceLabel: `${repoSlug}@${ref}`,
  }
}

const remoteEntry = requestedRemoteEntry()

function modelUrl(file) {
  return `${modelsBasePath}/${encodePathSegments(file)}`;
}

function modelSource(file) {
  if (remoteEntry && file === remoteRequestedFile) return remoteEntry
  if (runtimeMode === 'extension') {
    const localUrl = `${modelDownloadApiUrl}?file=${encodeURIComponent(file)}`
    return { file, fetchUrl: localUrl, downloadUrl: localUrl, cacheBust: false, sourceLabel: '' }
  }
  const localUrl = modelUrl(file)
  return { file, fetchUrl: localUrl, downloadUrl: localUrl, cacheBust: true, sourceLabel: '' }
}

function manifestFilesWithRemote(files) {
  if (!remoteEntry?.file) return files
  if (files.includes(remoteEntry.file)) return files
  return [remoteEntry.file, ...files]
}

async function readModelManifest() {
  if (runtimeMode === 'extension') {
    const res = await fetch(`${modelsApiUrl}?t=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) throw new Error('model list not found');
    const data = await res.json();
    return {
      files: Array.isArray(data.files) ? data.files : [],
      mtimes: data.mtimes && typeof data.mtimes === 'object' ? data.mtimes : {},
    };
  }
  const res = await fetch(appendCacheBust(modelsIndexUrl), { cache: 'no-store' });
  if (!res.ok) {
    if (remoteEntry) return { files: [remoteEntry.file], mtimes: null };
    throw new Error('models.json not found');
  }
  const data = await res.json();
  return { files: manifestFilesWithRemote(Array.isArray(data.files) ? data.files : []), mtimes: null };
}

async function readModelVersion(file) {
  if (runtimeMode === 'extension') return currentMtime || '';
  try {
    const source = modelSource(file)
    const res = await fetch(source.cacheBust ? appendCacheBust(source.downloadUrl) : source.downloadUrl, { method: 'HEAD', cache: 'no-store' });
    if (!res.ok) return '';
    return res.headers.get('etag') || res.headers.get('last-modified') || res.headers.get('content-length') || '';
  } catch {
    return '';
  }
}

async function fetchModelData(file) {
  if (runtimeMode === 'extension') {
    const res = await fetch(`${modelApiUrl}?file=${encodeURIComponent(file)}&t=${Date.now()}`, { cache: 'no-store' })
    if (!res.ok) throw new Error(`Model file not found: models/${file}`)
    return res.json()
  }
  const source = modelSource(file)
  const response = await fetch(source.cacheBust ? appendCacheBust(source.fetchUrl) : source.fetchUrl, { cache: 'no-store' })
  if (!response.ok) throw new Error(`Model file not found: ${source.sourceLabel ? `${source.sourceLabel} ${file}` : `models/${file}`}`)
  const buffer = await response.arrayBuffer()
  const parsed = await parseModelBuffer(file, buffer)
  return {
    path: file,
    source: source.sourceLabel,
    downloadUrl: source.downloadUrl,
    stats: {
      ...parsed,
      triangles: undefined,
      triangleColors: undefined,
      plates: undefined,
    },
    triangles: parsed.triangles || [],
    triangleColors: parsed.triangleColors || [],
    plates: parsed.plates || [],
    projectMetadata: parsed.projectMetadata || {},
    mtime: await readModelVersion(file),
  }
}

function loadModel(file, preserveView) {
  const meta = document.getElementById('meta')
  const previousFile = loadedModelInfo ? currentFile : ''
  const previousSelection = plateChooser.value
  updateOrcaAction()
  setSpinner(true, 'Loading plates…')
  return fetchModelData(file)
    .then((data) => {
      if (data.error) { meta.textContent = data.error; setSpinner(false); return false }
      const s = data.stats || {}
      const b = s.bounds
      const trianglesData = Array.isArray(data.triangles) ? data.triangles : []
      const colorsData = Array.isArray(data.triangleColors) ? data.triangleColors : []
      const platesData = Array.isArray(data.plates) ? data.plates : []
      if (s.format === '3mf') shadingInput.value = 'material'
      if (!s.facets || s.facets <= 0 || !trianglesData.length) {
        const msg = 'Failed to load model: no triangle data found. Check that the file is a valid STL or 3MF export.'
        meta.textContent = msg
        triangles = []
        rawTriangles = []
        rawTriangleColors = []
        loadedTriangles = []
        loadedTriangleColors = []
        loadedPlates = []
        overviewPlates = []
        loadedModelInfo = null
        triangleColors = []
        modelBounds = null
        plateField.hidden = true
        currentFile = file
        currentMtime = runtimeMode === 'extension' ? '' : ''
        emitModelChange(file)
        setSpinner(false)
        return false
      }
      loadedModelInfo = {
        path: data.path || file,
        source: data.source || '',
        stats: s,
        projectMetadata: data.projectMetadata || {},
        modelPath: data.modelPath || '',
      }
      triangles = []
      loadedTriangles = []
      loadedTriangleColors = []
      for (const tri of trianglesData) {
        if (Array.isArray(tri) && tri.length === 3) {
          loadedTriangles.push(tri)
          loadedTriangleColors.push(typeof colorsData[loadedTriangles.length - 1] === 'string' ? colorsData[loadedTriangles.length - 1] : '#d6d9de')
        }
      }
      loadedPlates = platesData.filter((plate) => Array.isArray(plate?.triangles) && plate.triangles.length)
      overviewPlates = layoutPlateOverview(loadedPlates)
      plateChooser.innerHTML = '<option value="all">All plates</option>' +
        loadedPlates.map((plate) => '<option value="' + escapeHtml(String(plate.id)) + '">Plate ' + escapeHtml(String(plate.id)) + '</option>').join('')
      plateField.hidden = loadedPlates.length <= 1
      plateChooser.value = selectDefaultPlate(file, previousFile, previousSelection, loadedPlates)
      applyPlateSelection()
      if (!modelBounds) modelBounds = b || computeBounds(rawTriangles)
      currentFile = file
      currentMtime = data.mtime || ''
      if (!preserveView) {
        if (plateChooser.value === 'all' && loadedPlates.length > 1) fitView()
        else applySavedOrFit()
      }
      draw()
      setSpinner(false)
      updateOrcaAction(file, loadedModelInfo.modelPath)
      emitModelChange(file)
      return true
    })
    .catch((err) => {
      meta.textContent = 'Failed to load model: ' + err
      setSpinner(false)
      emitModelChange(file)
      return false
    })
}

function refreshFileChooser(files) {
  if (files.join('|') === knownFiles.join('|')) return;
  knownFiles = files;
  const keep = fileChooser.value;
  fileChooser.innerHTML = files.map((name) => '<option value="' + name + '">' + name + '</option>').join('');
  fileChooser.value = files.indexOf(keep) >= 0 ? keep : files[0];
}
// Poll models/ so externally rewritten model files refresh the viewer automatically.
function pollForChanges() {
  if (reloadInFlight) return
  reloadInFlight = true
  readModelManifest().then(({ files, mtimes }) => {
    if (!files.length) return
    refreshFileChooser(files)
    const selected = fileChooser.value
    if (!selected || !autoReloadInput.checked) return
    if (runtimeMode === 'extension') {
      const version = (mtimes || {})[selected] || ''
      if (selected !== currentFile) return loadModel(selected, false)
      if (version && version !== currentMtime) return loadModel(selected, true)
      return
    }
    return readModelVersion(selected).then((version) => {
      if (!version) return
      if (selected !== currentFile) return loadModel(selected, false)
      if (currentMtime && version !== currentMtime) return loadModel(selected, true)
    }).catch(() => {})
  }).catch(() => {}).finally(() => { reloadInFlight = false })
}

function canvasPixelRatio() { return Math.min(window.devicePixelRatio || 1, maxPixelRatio); }
function resizeCanvas() { const rect = canvas.getBoundingClientRect(); const pixelRatio = canvasPixelRatio(); canvas.width = rect.width * pixelRatio; canvas.height = rect.height * pixelRatio; ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.scale(pixelRatio, pixelRatio); }
// Turntable camera: yaw around the model's Z (up) axis, then pitch, then screen roll.
function rot(v, rx, ry, rz) { let [x, y, z] = v; const cy = Math.cos(ry), sy = Math.sin(ry), cx = Math.cos(rx), sx = Math.sin(rx), cz = Math.cos(rz), sz = Math.sin(rz); let t = x * cy - y * sy; y = x * sy + y * cy; x = t; t = y * cx - z * sx; z = y * sx + z * cx; y = t; t = x * cz - y * sz; y = x * sz + y * cz; x = t; return [x, y, z]; }
function projectPoint(v, rx, ry, rz, w, h, zoom) { const r = rot(v, rx, ry, rz); const x = r[0] + panX; const y = r[1] + panY; const z = r[2]; const f = 420 / (420 - z); return [w / 2 + x * f * MM_TO_PX * zoom, h / 2 - y * f * MM_TO_PX * zoom, z]; }
function drawBuildPlate(w, h, rx, ry, rz, zoom, offsetX = 0, offsetY = 0, label = '') {
  const half = BED_SIZE_MM / 2;
  const bedY = 0;
  const thickness = 6;
  const project = ([x, y, z]) => projectPoint([x + offsetX, y + offsetY, z], rx, ry, rz, w, h, zoom)
  const top = [
    [-half, -half, bedY],
    [half, -half, bedY],
    [half, half, bedY],
    [-half, half, bedY],
  ].map(project);
  const low = [
    [-half, -half, bedY - thickness],
    [half, -half, bedY - thickness],
    [half, half, bedY - thickness],
    [-half, half, bedY - thickness],
  ].map(project);
  ctx.fillStyle = '#1a1e22';
  ctx.beginPath();
  ctx.moveTo(low[0][0], low[0][1]);
  ctx.lineTo(low[1][0], low[1][1]);
  ctx.lineTo(low[2][0], low[2][1]);
  ctx.lineTo(low[3][0], low[3][1]);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = '#343a40';
  ctx.beginPath();
  ctx.moveTo(top[0][0], top[0][1]);
  ctx.lineTo(top[1][0], top[1][1]);
  ctx.lineTo(top[2][0], top[2][1]);
  ctx.lineTo(top[3][0], top[3][1]);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = '#5f6670';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(top[0][0], top[0][1]);
  ctx.lineTo(top[1][0], top[1][1]);
  ctx.lineTo(top[2][0], top[2][1]);
  ctx.lineTo(top[3][0], top[3][1]);
  ctx.closePath();
  ctx.stroke();
  if (label) {
    const labelPoint = project([-half + 8, -half + 8, 0.5])
    ctx.fillStyle = '#d0d7de'
    ctx.font = '600 12px system-ui, sans-serif'
    ctx.fillText(label, labelPoint[0], labelPoint[1])
  }
}
function drawGrid(w, h, rx, ry, rz, zoom) {
  const half = BED_SIZE_MM / 2;
  const step = 10;
  ctx.lineWidth = 1;
  for (let i = -half; i <= half; i += step) {
    const major = i % 50 === 0;
    ctx.strokeStyle = major ? 'rgba(160,170,182,0.55)' : 'rgba(120,130,142,0.28)';
    const a = projectPoint([i, -half, 0], rx, ry, rz, w, h, zoom);
    const b = projectPoint([i, half, 0], rx, ry, rz, w, h, zoom);
    const c = projectPoint([-half, i, 0], rx, ry, rz, w, h, zoom);
    const d = projectPoint([half, i, 0], rx, ry, rz, w, h, zoom);
    ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(c[0], c[1]); ctx.lineTo(d[0], d[1]); ctx.stroke();
  }
}
function drawAxes(w, h, rx, ry, rz, zoom) {
  const len = modelBounds ? Math.max(20, Math.max(modelBounds.size.x, modelBounds.size.y, modelBounds.size.z) * 0.8) : 50;
  const origin = projectPoint([0, 0, 0], rx, ry, rz, w, h, zoom);
  const axes = [[[len, 0, 0], '#f85149', 'X'], [[0, len, 0], '#3fb950', 'Y'], [[0, 0, len], '#58a6ff', 'Z']];
  ctx.lineWidth = 2;
  for (const [vec, color, label] of axes) {
    const end = projectPoint(vec, rx, ry, rz, w, h, zoom);
    ctx.strokeStyle = color;
    ctx.beginPath(); ctx.moveTo(origin[0], origin[1]); ctx.lineTo(end[0], end[1]); ctx.stroke();
    ctx.fillStyle = color;
    ctx.font = '11px sans-serif';
    ctx.fillText(label, end[0] + 4, end[1] - 4);
  }
}
function drawBoundingBox(w, h, rx, ry, rz, zoom, offX, offY) {
  if (!modelBounds) return;
  const x0 = modelBounds.min.x + offX, x1 = modelBounds.max.x + offX;
  const y0 = modelBounds.min.y + offY, y1 = modelBounds.max.y + offY;
  const z0 = 0, z1 = modelBounds.size.z;
  const corners = [
    [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
    [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]
  ].map((p) => projectPoint(p, rx, ry, rz, w, h, zoom));
  const edges = [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]];
  ctx.strokeStyle = '#d29922';
  ctx.lineWidth = 1.5;
  for (const [a, b] of edges) { ctx.beginPath(); ctx.moveTo(corners[a][0], corners[a][1]); ctx.lineTo(corners[b][0], corners[b][1]); ctx.stroke(); }
}
// Studio light in view space: upper left, slightly towards the camera.
const LIGHT = (() => { const v = [-0.35, 0.45, 0.82]; const l = Math.hypot(v[0], v[1], v[2]); return [v[0] / l, v[1] / l, v[2] / l]; })();
const HALFWAY = (() => { const v = [LIGHT[0], LIGHT[1], LIGHT[2] + 1]; const l = Math.hypot(v[0], v[1], v[2]); return [v[0] / l, v[1] / l, v[2] / l]; })();
const SURFACE = [214, 217, 222];
function shadeNormal(nx, ny, nz, mode, out, material = SURFACE) {
  if (mode === 'basic') { out[0] = 31; out[1] = 111; out[2] = 235; return; }
  if (mode === 'normal') {
    out[0] = 127 + 128 * nx; out[1] = 127 + 128 * ny; out[2] = 127 + 128 * nz; return;
  }
  const d = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2];
  // Ambient plus a weak fill from behind keeps cavities readable.
  const intensity = 0.30 + 0.78 * Math.max(0, d) + 0.10 * Math.max(0, -d);
  const base = mode === 'material' ? material : SURFACE;
  let r = base[0] * intensity, g = base[1] * intensity, b = base[2] * intensity;
  if (mode === 'phong') {
    const s = Math.max(0, nx * HALFWAY[0] + ny * HALFWAY[1] + nz * HALFWAY[2]);
    const spec = Math.pow(s, 30) * 190;
    r += spec; g += spec; b += spec;
  }
  out[0] = r < 255 ? r : 255; out[1] = g < 255 ? g : 255; out[2] = b < 255 ? b : 255;
}
// Scanline rasterizer with a depth buffer. The old painter's algorithm
// sorted whole triangles by their centroid, which let long thin facets
// punch through walls and made solid geometry look transparent.
function rasterizeMesh(rx, ry, rz, zoom, w, h, centerX, centerY, baseZ) {
  const dpr = canvasPixelRatio();
  const W = Math.max(1, canvas.width), H = Math.max(1, canvas.height);
  if (!rasterCanvas) { rasterCanvas = document.createElement('canvas'); rasterCtx = rasterCanvas.getContext('2d'); }
  if (rasterCanvas.width !== W || rasterCanvas.height !== H || !rasterImage) {
    rasterCanvas.width = W; rasterCanvas.height = H;
    rasterImage = rasterCtx.createImageData(W, H);
    depthBuffer = new Float32Array(W * H);
    pickBuffer = new Int32Array(W * H);
  }
  const pix = rasterImage.data;
  pix.fill(0);
  depthBuffer.fill(-1e30);
  pickBuffer.fill(-1);
  lastProjection = { rx, ry, rz, zoom, w, h, centerX, centerY, baseZ, dpr };
  const mode = shadingInput.value;
  const c0 = [0, 0, 0], c1 = [0, 0, 0], c2 = [0, 0, 0];
  const sx = [0, 0, 0], sy = [0, 0, 0], sz = [0, 0, 0];
  for (let i = 0; i < triangles.length; i++) {
    const tri = triangles[i];
    for (let j = 0; j < 3; j++) {
      const v = tri[j];
      const p = projectPoint([v[0] - centerX + objectX, v[1] - centerY + objectY, v[2] - baseZ], rx, ry, rz, w, h, zoom);
      sx[j] = p[0] * dpr; sy[j] = p[1] * dpr; sz[j] = p[2];
    }
    // Screen-space winding: positive area means the facet faces away.
    const area = (sx[1] - sx[0]) * (sy[2] - sy[0]) - (sx[2] - sx[0]) * (sy[1] - sy[0]);
    if (area >= 0) continue;
    const cols = [c0, c1, c2];
    for (let j = 0; j < 3; j++) {
      const b = i * 9 + j * 3;
      const n = rot([cornerNormals[b], cornerNormals[b + 1], cornerNormals[b + 2]], rx, ry, rz);
      const color = triangleColors[i] || '#d6d9de';
      const material = [parseInt(color.slice(1, 3), 16), parseInt(color.slice(3, 5), 16), parseInt(color.slice(5, 7), 16)];
      shadeNormal(n[0], n[1], n[2], mode, cols[j], material);
    }
    let minX = Math.max(0, Math.floor(Math.min(sx[0], sx[1], sx[2])));
    let maxX = Math.min(W - 1, Math.ceil(Math.max(sx[0], sx[1], sx[2])));
    let minY = Math.max(0, Math.floor(Math.min(sy[0], sy[1], sy[2])));
    let maxY = Math.min(H - 1, Math.ceil(Math.max(sy[0], sy[1], sy[2])));
    if (minX > maxX || minY > maxY) continue;
    const inv = 1 / area;
    for (let py = minY; py <= maxY; py++) {
      const fy = py + 0.5;
      for (let px = minX; px <= maxX; px++) {
        const fx = px + 0.5;
        const w0 = ((sx[1] - fx) * (sy[2] - fy) - (sx[2] - fx) * (sy[1] - fy)) * inv;
        if (w0 < 0) continue;
        const w1 = ((sx[2] - fx) * (sy[0] - fy) - (sx[0] - fx) * (sy[2] - fy)) * inv;
        if (w1 < 0) continue;
        const w2 = 1 - w0 - w1;
        if (w2 < 0) continue;
        const z = w0 * sz[0] + w1 * sz[1] + w2 * sz[2];
        const idx = py * W + px;
        if (z <= depthBuffer[idx]) continue;
        depthBuffer[idx] = z;
        pickBuffer[idx] = i;
        const o = idx * 4;
        pix[o] = w0 * c0[0] + w1 * c1[0] + w2 * c2[0];
        pix[o + 1] = w0 * c0[1] + w1 * c1[1] + w2 * c2[1];
        pix[o + 2] = w0 * c0[2] + w1 * c1[2] + w2 * c2[2];
        pix[o + 3] = 255;
      }
    }
  }
  rasterCtx.putImageData(rasterImage, 0, 0);
  ctx.drawImage(rasterCanvas, 0, 0, W / dpr, H / dpr);
}

// ---- Measure gizmo -------------------------------------------------
const SNAP_PX = 9;
function projectModel(p) {
  const L = lastProjection;
  if (!L) return null;
  return projectPoint([p[0] - L.centerX + objectX, p[1] - L.centerY + objectY, p[2] - L.baseZ], L.rx, L.ry, L.rz, L.w, L.h, L.zoom);
}
function segmentPixelDistance(px, py, a, b) {
  const ax = a[0], ay = a[1], bx = b[0], by = b[1];
  const dx = bx - ax, dy = by - ay;
  const len2 = dx * dx + dy * dy;
  let t = len2 > 0 ? ((px - ax) * dx + (py - ay) * dy) / len2 : 0;
  t = Math.max(0, Math.min(1, t));
  return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
}
function pickFeature(cssX, cssY) {
  if (!lastProjection || !pickBuffer || !triVerts) return null;
  const dpr = lastProjection.dpr;
  const W = rasterCanvas.width, H = rasterCanvas.height;
  const cx = Math.round(cssX * dpr), cy = Math.round(cssY * dpr);
  let tri = -1;
  const reach = Math.max(2, Math.round(3 * dpr));
  outer:
  for (let r = 0; r <= reach; r++) {
    for (let oy = -r; oy <= r; oy++) {
      for (let ox = -r; ox <= r; ox++) {
        if (Math.max(Math.abs(ox), Math.abs(oy)) !== r) continue;
        const x = cx + ox, y = cy + oy;
        if (x < 0 || y < 0 || x >= W || y >= H) continue;
        const v = pickBuffer[y * W + x];
        if (v >= 0) { tri = v; break outer; }
      }
    }
  }
  if (tri < 0) return null;
  const ids = [triVerts[tri * 3], triVerts[tri * 3 + 1], triVerts[tri * 3 + 2]];
  const world = ids.map((i) => measurePoints[i]);
  const screen = world.map((p) => projectModel(p));
  // Barycentric hit point on the triangle, used for plane picks.
  const area = (screen[1][0] - screen[0][0]) * (screen[2][1] - screen[0][1]) - (screen[2][0] - screen[0][0]) * (screen[1][1] - screen[0][1]);
  let hit = world[0];
  if (Math.abs(area) > 1e-9) {
    const w0 = ((screen[1][0] - cssX) * (screen[2][1] - cssY) - (screen[2][0] - cssX) * (screen[1][1] - cssY)) / area;
    const w1 = ((screen[2][0] - cssX) * (screen[0][1] - cssY) - (screen[0][0] - cssX) * (screen[2][1] - cssY)) / area;
    const w2 = 1 - w0 - w1;
    hit = [
      w0 * world[0][0] + w1 * world[1][0] + w2 * world[2][0],
      w0 * world[0][1] + w1 * world[1][1] + w2 * world[2][1],
      w0 * world[0][2] + w1 * world[1][2] + w2 * world[2][2]
    ];
  }
  // 1) snap to a corner
  let bestVert = -1, bestVertDist = SNAP_PX;
  for (let j = 0; j < 3; j++) {
    const d = Math.hypot(screen[j][0] - cssX, screen[j][1] - cssY);
    if (d < bestVertDist) { bestVertDist = d; bestVert = j; }
  }
  // 2) snap to a crease edge, and prefer a fitted circle through it
  let bestEdge = -1, bestEdgeDist = SNAP_PX;
  for (let j = 0; j < 3; j++) {
    const a = ids[j], b = ids[(j + 1) % 3];
    const idx = creaseIndex ? creaseIndex.get(a < b ? a + '_' + b : b + '_' + a) : undefined;
    if (idx === undefined) continue;
    const d = segmentPixelDistance(cssX, cssY, screen[j], screen[(j + 1) % 3]);
    if (d < bestEdgeDist) { bestEdgeDist = d; bestEdge = j; }
  }
  if (bestEdge >= 0 && vertexCircle) {
    const a = ids[bestEdge], b = ids[(bestEdge + 1) % 3];
    const ci = vertexCircle.has(a) ? vertexCircle.get(a) : vertexCircle.get(b);
    if (ci !== undefined) {
      const c = measureCircles[ci];
      return { kind: 'circle', center: c.center, normal: c.normal, radius: c.radius, loop: c.loop, tri };
    }
  }
  if (bestVert >= 0 && bestVertDist <= bestEdgeDist) {
    return { kind: 'point', p: world[bestVert], id: ids[bestVert], tri };
  }
  if (bestEdge >= 0) {
    return { kind: 'edge', a: world[bestEdge], b: world[(bestEdge + 1) % 3], tri };
  }
  const n = [faceNormals[tri * 3], faceNormals[tri * 3 + 1], faceNormals[tri * 3 + 2]];
  return { kind: 'plane', p: hit, normal: n, tri };
}
function featureAnchor(f) {
  if (f.kind === 'point') return f.p;
  if (f.kind === 'circle') return f.center;
  if (f.kind === 'edge') return [(f.a[0] + f.b[0]) / 2, (f.a[1] + f.b[1]) / 2, (f.a[2] + f.b[2]) / 2];
  return f.p;
}
function featureLabel(f) {
  const r3 = (n) => n.toFixed(2);
  if (f.kind === 'point') return 'Point  ' + f.p.map(r3).join(', ');
  if (f.kind === 'circle') return 'Circle  d ' + r3(f.radius * 2) + '  center ' + f.center.map(r3).join(', ');
  if (f.kind === 'edge') return 'Edge  len ' + r3(Math.hypot(f.b[0] - f.a[0], f.b[1] - f.a[1], f.b[2] - f.a[2]));
  return 'Plane  n ' + f.normal.map((v) => v.toFixed(2)).join(', ');
}
function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
function norm(a) { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; }
function featureDirection(f) {
  if (f.kind === 'edge') return norm(sub(f.b, f.a));
  if (f.kind === 'circle') return f.normal;
  if (f.kind === 'plane') return f.normal;
  return null;
}
function measureBetween(a, b) {
  const pa = featureAnchor(a), pb = featureAnchor(b);
  const d = sub(pb, pa);
  const lines = [];
  const r3 = (n) => n.toFixed(3);
  let headline = 'Distance  ' + r3(Math.hypot(d[0], d[1], d[2])) + ' mm';
  const kinds = [a.kind, b.kind].sort().join('-');
  if (kinds === 'plane-point' || kinds === 'circle-plane') {
    const pl = a.kind === 'plane' ? a : b, other = a.kind === 'plane' ? b : a;
    lines.push('Perpendicular  ' + r3(Math.abs(dot(sub(featureAnchor(other), pl.p), pl.normal))) + ' mm');
  } else if (kinds === 'edge-point' || kinds === 'circle-edge') {
    const e = a.kind === 'edge' ? a : b, other = a.kind === 'edge' ? b : a;
    const dir = norm(sub(e.b, e.a));
    const v = sub(featureAnchor(other), e.a);
    const perp = sub(v, [dir[0] * dot(v, dir), dir[1] * dot(v, dir), dir[2] * dot(v, dir)]);
    lines.push('Perpendicular  ' + r3(Math.hypot(perp[0], perp[1], perp[2])) + ' mm');
  } else if (kinds === 'plane-plane') {
    const ang = Math.acos(Math.min(1, Math.max(-1, Math.abs(dot(a.normal, b.normal))))) * 180 / Math.PI;
    lines.push('Angle  ' + ang.toFixed(2) + ' deg');
    if (ang < 0.5) lines.push('Parallel gap  ' + r3(Math.abs(dot(sub(b.p, a.p), a.normal))) + ' mm');
  } else if (kinds === 'edge-edge') {
    const da = norm(sub(a.b, a.a)), db = norm(sub(b.b, b.a));
    const ang = Math.acos(Math.min(1, Math.max(-1, Math.abs(dot(da, db))))) * 180 / Math.PI;
    lines.push('Angle  ' + ang.toFixed(2) + ' deg');
    const n = cross(da, db);
    const nl = Math.hypot(n[0], n[1], n[2]);
    if (nl > 1e-6) lines.push('Line gap  ' + r3(Math.abs(dot(sub(b.a, a.a), [n[0] / nl, n[1] / nl, n[2] / nl]))) + ' mm');
  } else if (kinds === 'circle-circle') {
    headline = 'Center distance  ' + r3(Math.hypot(d[0], d[1], d[2])) + ' mm';
    lines.push('Diameters  ' + (a.radius * 2).toFixed(3) + ' / ' + (b.radius * 2).toFixed(3) + ' mm');
  }
  lines.push('dX ' + r3(d[0]) + '   dY ' + r3(d[1]) + '   dZ ' + r3(d[2]));
  return { headline, lines, pa, pb };
}
function clearMeasurement() { pickedFeatures = []; hoverFeature = null; }
function drawFeature(f, color, width) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = width;
  if (f.kind === 'point') {
    const s = projectModel(f.p);
    ctx.beginPath(); ctx.arc(s[0], s[1], 4.5, 0, Math.PI * 2); ctx.fill();
  } else if (f.kind === 'edge') {
    const a = projectModel(f.a), b = projectModel(f.b);
    ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
  } else if (f.kind === 'circle') {
    ctx.beginPath();
    for (let i = 0; i < f.loop.length; i++) {
      const s = projectModel(measurePoints[f.loop[i]]);
      if (i === 0) ctx.moveTo(s[0], s[1]); else ctx.lineTo(s[0], s[1]);
    }
    ctx.closePath(); ctx.stroke();
    const c = projectModel(f.center);
    ctx.beginPath(); ctx.moveTo(c[0] - 5, c[1]); ctx.lineTo(c[0] + 5, c[1]); ctx.moveTo(c[0], c[1] - 5); ctx.lineTo(c[0], c[1] + 5); ctx.stroke();
  } else if (f.kind === 'plane') {
    const tri = triangles[f.tri].map((v) => projectModel(v));
    ctx.globalAlpha = 0.45;
    ctx.beginPath(); ctx.moveTo(tri[0][0], tri[0][1]); ctx.lineTo(tri[1][0], tri[1][1]); ctx.lineTo(tri[2][0], tri[2][1]); ctx.closePath(); ctx.fill();
    ctx.globalAlpha = 1;
    const s = projectModel(f.p);
    ctx.beginPath(); ctx.arc(s[0], s[1], 3, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}
function drawMeasureOverlay() {
  if (!measureModeInput.checked || !lastProjection) { measurePanel.hidden = true; return; }
  if (hoverFeature) drawFeature(hoverFeature, '#2dd4bf', 2.5);
  if (pickedFeatures[0]) drawFeature(pickedFeatures[0], '#f0883e', 3);
  if (pickedFeatures[1]) drawFeature(pickedFeatures[1], '#7ee787', 3);
  const text = ['Measure: click a point, edge, circle or face'];
  if (pickedFeatures.length === 2) {
    const m = measureBetween(pickedFeatures[0], pickedFeatures[1]);
    const a = projectModel(m.pa), b = projectModel(m.pb);
    ctx.save();
    ctx.strokeStyle = '#e6edf3';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([5, 4]);
    ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
    ctx.setLineDash([]);
    const label = m.headline.replace(/^[^ ]+ +/, '');
    ctx.font = '12px ui-monospace, Consolas, monospace';
    const mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    const wLabel = ctx.measureText(label).width + 10;
    ctx.fillStyle = 'rgba(13,17,23,0.85)';
    ctx.fillRect(mid[0] - wLabel / 2, mid[1] - 18, wLabel, 18);
    ctx.fillStyle = '#e6edf3';
    ctx.textAlign = 'center';
    ctx.fillText(label, mid[0], mid[1] - 5);
    ctx.restore();
    text.length = 0;
    text.push('A  ' + featureLabel(pickedFeatures[0]));
    text.push('B  ' + featureLabel(pickedFeatures[1]));
    text.push('');
    text.push(m.headline);
    for (const l of m.lines) text.push(l);
  } else if (pickedFeatures.length === 1) {
    text.length = 0;
    text.push('A  ' + featureLabel(pickedFeatures[0]));
    text.push('Pick the second feature');
  }
  if (hoverFeature) text.push('', 'Hover  ' + featureLabel(hoverFeature));
  measurePanel.hidden = false;
  measurePanel.textContent = text.join('\n');
}
function updateInfo() {
  if (!showInfoInput.checked) { infoBox.hidden = true; return; }
  infoBox.hidden = false;
  const r = (n) => Math.round(n * 100) / 100;
  const b = modelBounds;
  infoBox.textContent = [
    'camera_rot_x: ' + r(rotX),
    'camera_rot_y: ' + r(rotY),
    'camera_rot_z: ' + r(rotZ),
    'pan: ' + r(panX) + ', ' + r(panY),
    'zoom: ' + r(parseFloat(zoomInput.value)),
    'model_rot: ' + modelRotX + ', ' + modelRotY + ', ' + modelRotZ,
    'triangles: ' + triangles.length,
    b ? 'size_mm: ' + r(b.size.x) + ' x ' + r(b.size.y) + ' x ' + r(b.size.z) : 'size_mm: n/a',
    b ? 'min: ' + r(b.min.x) + ', ' + r(b.min.y) + ', ' + r(b.min.z) : '',
    b ? 'max: ' + r(b.max.x) + ', ' + r(b.max.y) + ', ' + r(b.max.z) : ''
  ].filter(Boolean).join('\n');
}
function fitView() {
  if (!modelBounds) return;
  const sizeX = Math.max(1, modelBounds.size.x);
  const sizeY = Math.max(1, modelBounds.size.y);
  const sizeZ = Math.max(1, modelBounds.size.z);
  let maxSize = Math.max(sizeX, sizeY, sizeZ);
  const plateOverview = plateChooser.value === 'all' && loadedPlates.length > 1
  if (plateOverview) {
    const centers = overviewPlates
      .map((plate) => plate.stats?.bounds)
      .filter(Boolean)
      .map((bounds) => ({
        x: (bounds.min.x + bounds.max.x) / 2,
        y: (bounds.min.y + bounds.max.y) / 2,
      }))
    if (centers.length) {
      const xs = centers.map((center) => center.x)
      const ys = centers.map((center) => center.y)
      maxSize = Math.max(
        maxSize,
        Math.max(...xs) - Math.min(...xs) + BED_SIZE_MM,
        Math.max(...ys) - Math.min(...ys) + BED_SIZE_MM,
      )
    }
  }
  // Zoom 1.0 shows the whole 250 mm plate; smaller models get zoomed in.
  zoomInput.value = Math.max(plateOverview ? 0.18 : 0.6, Math.min(3, 110 / maxSize));
  panX = 0;
  panY = 0;
  objectX = 0;
  objectY = 0;
}
function applySavedOrFit() {
  // A saved zoom means the user already framed the scene; don't override it.
  if (savedZoom !== null) {
    zoomInput.value = savedZoom;
    objectX = 0;
    objectY = 0;
    return;
  }
  fitView();
}
function draw() {
  const pixelRatio = canvasPixelRatio()
  const w = canvas.width / pixelRatio, h = canvas.height / pixelRatio;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = VIEW_BACKGROUND;
  ctx.fillRect(0, 0, w, h);
  const rx = rotX * Math.PI / 180, ry = rotY * Math.PI / 180, rz = rotZ * Math.PI / 180, zoom = parseFloat(zoomInput.value);
  const centerX = modelBounds ? (modelBounds.min.x + modelBounds.max.x) / 2 : 0;
  const centerY = modelBounds ? (modelBounds.min.y + modelBounds.max.y) / 2 : 0;
  const baseZ = modelBounds ? modelBounds.min.z : 0;
  const plateOverview = plateChooser.value === 'all' && loadedPlates.length > 1
  if (plateOverview) {
    for (const plate of overviewPlates) {
      const bounds = plate.stats?.bounds
      if (!bounds) continue
      drawBuildPlate(
        w,
        h,
        rx,
        ry,
        rz,
        zoom,
        (bounds.min.x + bounds.max.x) / 2 - centerX,
        (bounds.min.y + bounds.max.y) / 2 - centerY,
        `Plate ${plate.id}`,
      )
    }
  } else {
    drawBuildPlate(w, h, rx, ry, rz, zoom)
    if (showGridInput.checked) drawGrid(w, h, rx, ry, rz, zoom)
  }
  if (showAxesInput.checked) drawAxes(w, h, rx, ry, rz, zoom);
  if (wireframeInput.checked) {
    const projected = triangles.map((t) => t.map((v) => projectPoint([v[0] - centerX + objectX, v[1] - centerY + objectY, v[2] - baseZ], rx, ry, rz, w, h, zoom)));
    ctx.strokeStyle = '#58a6ff';
    ctx.lineWidth = 1;
    for (const tri of projected) { ctx.beginPath(); ctx.moveTo(tri[0][0], tri[0][1]); ctx.lineTo(tri[1][0], tri[1][1]); ctx.lineTo(tri[2][0], tri[2][1]); ctx.closePath(); ctx.stroke(); }
  } else if (triangles.length && cornerNormals) {
    rasterizeMesh(rx, ry, rz, zoom, w, h, centerX, centerY, baseZ);
  }
  if (showBoxInput.checked) drawBoundingBox(w, h, rx, ry, rz, zoom, objectX - centerX, objectY - centerY);
  drawMeasureOverlay();
  updateInfo();
}
resizeCanvas();
window.addEventListener('resize', () => { resizeCanvas(); draw(); });
canvas.addEventListener('contextmenu', (e) => e.preventDefault());
canvas.addEventListener('mousedown', (e) => { isDragging = true; dragMoved = 0; isShiftDrag = e.shiftKey; isRightDrag = e.button === 2; lastX = e.clientX; lastY = e.clientY; });
document.addEventListener('mousemove', (e) => {
  if (!isDragging) {
    if (measureModeInput.checked) {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left, y = e.clientY - rect.top;
      if (x >= 0 && y >= 0 && x <= rect.width && y <= rect.height) {
        lastPointer = [x, y];
        const f = pickFeature(x, y);
        const changed = JSON.stringify(f && [f.kind, f.tri, f.id]) !== JSON.stringify(hoverFeature && [hoverFeature.kind, hoverFeature.tri, hoverFeature.id]);
        hoverFeature = f;
        if (changed) draw();
      }
    }
    return;
  }
  const dx = e.clientX - lastX; const dy = e.clientY - lastY;
  dragMoved += Math.abs(dx) + Math.abs(dy);
  if (isRightDrag) {
    // Pan the whole view (plates, grid, axes and model) so it follows the cursor.
    const pxPerMm = MM_TO_PX * (parseFloat(zoomInput.value) || 1);
    panX += dx / pxPerMm; panY -= dy / pxPerMm;
  } else if (isShiftDrag) { panX += dx * 0.5; panY += dy * 0.5; } else { rotY += dx * 0.5; rotX += dy * 0.5; }
  lastX = e.clientX; lastY = e.clientY; draw();
});
document.addEventListener('mouseup', () => { if (isDragging) { isDragging = false; saveView(); } });
// A click without dragging selects the snapped feature under the cursor.
canvas.addEventListener('click', (e) => {
  if (!measureModeInput.checked || dragMoved > 3) return;
  const rect = canvas.getBoundingClientRect();
  const f = pickFeature(e.clientX - rect.left, e.clientY - rect.top);
  if (!f) { clearMeasurement(); draw(); return; }
  if (pickedFeatures.length >= 2) pickedFeatures = [];
  pickedFeatures.push(f);
  draw();
});
measureModeInput.addEventListener('change', () => {
  canvas.classList.toggle('measuring', measureModeInput.checked);
  if (!measureModeInput.checked) clearMeasurement();
  draw();
});
measureClearBtn.addEventListener('click', () => { clearMeasurement(); draw(); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { clearMeasurement(); draw(); } });
canvas.addEventListener('wheel', (e) => { e.preventDefault(); const delta = e.deltaY > 0 ? -0.1 : 0.1; zoomInput.value = Math.max(0.1, Math.min(30, parseFloat(zoomInput.value) + delta)); draw(); saveView(); });
canvas.addEventListener('dblclick', () => { rotX = baseView.rotX; rotY = baseView.rotY; rotZ = baseView.rotZ || 0; panX = baseView.panX; panY = baseView.panY; savedZoom = Number.isFinite(baseView.zoom) ? baseView.zoom : null; applySavedOrFit(); draw(); saveView(); });

let initialPinchDist = 0;
let initialPinchZoom = 1;
let lastTouchPanMid = null;
let lastTouchX = 0;
let lastTouchY = 0;
let lastTapTime = 0;

canvas.addEventListener('touchstart', (e) => {
  e.preventDefault();
  const t = e.touches;
  if (t.length === 1) {
    const now = Date.now();
    if (now - lastTapTime < 300) {
      rotX = baseView.rotX; rotY = baseView.rotY; rotZ = baseView.rotZ || 0;
      panX = baseView.panX; panY = baseView.panY;
      savedZoom = Number.isFinite(baseView.zoom) ? baseView.zoom : null;
      applySavedOrFit();
      draw();
      saveView();
      lastTapTime = 0;
      return;
    }
    lastTapTime = now;
    lastTouchX = t[0].clientX;
    lastTouchY = t[0].clientY;
  } else if (t.length === 2) {
    const dx = t[0].clientX - t[1].clientX;
    const dy = t[0].clientY - t[1].clientY;
    initialPinchDist = Math.hypot(dx, dy);
    initialPinchZoom = parseFloat(zoomInput.value) || 1;
    lastTouchPanMid = {
      x: (t[0].clientX + t[1].clientX) / 2,
      y: (t[0].clientY + t[1].clientY) / 2
    };
  }
}, { passive: false });

canvas.addEventListener('touchmove', (e) => {
  e.preventDefault();
  const t = e.touches;
  if (t.length === 1) {
    const curX = t[0].clientX;
    const curY = t[0].clientY;
    const dx = curX - lastTouchX;
    const dy = curY - lastTouchY;
    const rot = calculateTouchRotation(dx, dy);
    rotY += rot.deltaRotY;
    rotX += rot.deltaRotX;
    lastTouchX = curX;
    lastTouchY = curY;
    draw();
  } else if (t.length === 2) {
    const dx = t[0].clientX - t[1].clientX;
    const dy = t[0].clientY - t[1].clientY;
    const currentDist = Math.hypot(dx, dy);
    if (initialPinchDist > 0 && currentDist > 0) {
      const newZoom = calculateTouchPinchZoom(initialPinchZoom, currentDist, initialPinchDist);
      zoomInput.value = newZoom;
    }
    const midX = (t[0].clientX + t[1].clientX) / 2;
    const midY = (t[0].clientY + t[1].clientY) / 2;
    if (lastTouchPanMid) {
      const panDelta = calculateTouchPan(midX - lastTouchPanMid.x, midY - lastTouchPanMid.y);
      panX += panDelta.deltaPanX;
      panY += panDelta.deltaPanY;
    }
    lastTouchPanMid = { x: midX, y: midY };
    draw();
  }
}, { passive: false });

canvas.addEventListener('touchend', (e) => {
  if (e.touches.length === 0) {
    initialPinchDist = 0;
    lastTouchPanMid = null;
    saveView();
  } else if (e.touches.length === 1) {
    initialPinchDist = 0;
    lastTouchPanMid = null;
    lastTouchX = e.touches[0].clientX;
    lastTouchY = e.touches[0].clientY;
  }
}, { passive: false });

canvas.addEventListener('touchcancel', () => {
  initialPinchDist = 0;
  lastTouchPanMid = null;
  saveView();
});
zoomInput.addEventListener('input', () => { draw(); saveView(); });
wireframeInput.addEventListener('change', () => { draw(); saveView(); });
shadingInput.addEventListener('change', () => { draw(); saveView(); });
for (const input of [showGridInput, showAxesInput, showBoxInput, showInfoInput]) {
  input.addEventListener('change', () => { draw(); saveView(); });
}
for (const button of document.querySelectorAll('[data-view]')) {
  button.addEventListener('click', () => applyViewPreset(button.getAttribute('data-view')));
}
for (const button of document.querySelectorAll('[data-rotate]')) {
  button.addEventListener('click', () => {
    const axis = button.getAttribute('data-rotate');
    if (axis === 'x') modelRotX = (modelRotX + 90) % 360;
    else if (axis === 'y') modelRotY = (modelRotY + 90) % 360;
    else modelRotZ = (modelRotZ + 90) % 360;
    applyModelRotation();
    draw();
  });
}
document.getElementById('resetRotation').addEventListener('click', () => { modelRotX = 0; modelRotY = 0; modelRotZ = 0; applyModelRotation(); draw(); });
document.getElementById('fitBtn').addEventListener('click', () => { fitView(); draw(); saveView(); });
function applyBaseView(view) {
  baseView = { ...configuredFallbackView, ...sanitizeView(view) }
  if (Number.isFinite(baseView.rotX)) rotX = baseView.rotX
  if (Number.isFinite(baseView.rotY)) rotY = baseView.rotY
  if (Number.isFinite(baseView.rotZ)) rotZ = baseView.rotZ
  if (Number.isFinite(baseView.panX)) panX = baseView.panX
  if (Number.isFinite(baseView.panY)) panY = baseView.panY
  if (Number.isFinite(baseView.zoom)) { savedZoom = baseView.zoom; zoomInput.value = baseView.zoom }
  if (typeof baseView.wireframe === 'boolean') wireframeInput.checked = baseView.wireframe
  if (typeof baseView.shading === 'string') shadingInput.value = baseView.shading
  showGridInput.checked = typeof baseView.showGrid === 'boolean' ? baseView.showGrid : true
  showAxesInput.checked = typeof baseView.showAxes === 'boolean' ? baseView.showAxes : false
  showBoxInput.checked = typeof baseView.showBoundingBox === 'boolean' ? baseView.showBoundingBox : false
  showInfoInput.checked = typeof baseView.showInfo === 'boolean' ? baseView.showInfo : false
}

readViewDefaults().then((view) => {
  applyBaseView(view)
  return readModelManifest().then(({ files }) => {
    if (!files.length) {
      fileChooser.innerHTML = '<option value="">No STL or 3MF files in models/</option>'
      document.getElementById('meta').textContent = 'No STL or 3MF files found in models/.'
      emitModelChange('')
      return false
    }
    fileChooser.innerHTML = files.map((name) => '<option value="' + name + '">' + name + '</option>').join('')
    fileChooser.value = files.indexOf(currentFile) >= 0 ? currentFile : files[0]
    knownFiles = files
    return loadModel(fileChooser.value)
  }).catch((err) => {
    fileChooser.innerHTML = '<option value="">Failed to list files</option>'
    document.getElementById('meta').textContent = 'Failed to list files: ' + err
    return false
  })
}).catch(() => {
  applyBaseView(configuredFallbackView)
  return false
}).then((loaded) => {
  if (loaded !== false && pollTimer === null && pollIntervalMs > 0) pollTimer = setInterval(pollForChanges, pollIntervalMs)
})
fileChooser.addEventListener('change', () => { if (fileChooser.value) loadModel(fileChooser.value) })
plateChooser.addEventListener('change', () => {
  pickedFeatures = []
  hoverFeature = null
  setSpinner(true, 'Rendering plate…')
  setTimeout(() => {
    applyPlateSelection()
    fitView()
    draw()
    setSpinner(false)
  }, 20)
})
reloadBtn.addEventListener('click', () => {
  const selected = fileChooser.value || currentFile
  if (selected) loadModel(selected, false)
})
openInOrcaBtn.addEventListener('click', async () => {
  const openUrl = openInOrcaBtn.dataset.openUrl || ''
  const file = openInOrcaBtn.dataset.file || ''
  const modelPath = openInOrcaBtn.dataset.modelPath || ''
  if (!openUrl && !modelPath) return
  openInOrcaBtn.disabled = true
  orcaStatus.textContent = 'Opening 3MF…'
  orcaStatus.hidden = false
  clearTimeout(orcaStatusTimer)
  if (runtimeMode === 'extension' && openInOrcaApiUrl && openInOrcaNonce && modelPath) {
    try {
      const request = createOrcaLaunchRequest(openInOrcaApiUrl, modelPath, openInOrcaNonce)
      const response = await fetch(request.url, request.options)
      const result = await response.json()
      if (!response.ok || !result.ok) throw new Error(result.error || '3MF launch failed')
      orcaStatus.textContent = 'Opened with the default 3MF application.'
    } catch (error) {
      orcaStatus.textContent = `Could not open 3MF: ${error}`
    } finally {
      openInOrcaBtn.disabled = false
    }
    return
  }
  // Browsers cannot launch local applications directly; hand the 3MF to the
  // browser download flow so the OS opens it with the registered 3MF handler.
  try {
    const link = document.createElement('a')
    link.href = openUrl
    link.download = file.split('/').pop() || 'model.3mf'
    link.rel = 'noopener'
    document.body.appendChild(link)
    link.click()
    link.remove()
    orcaStatus.textContent = 'Downloaded. Open the file from your downloads to use the default 3MF application.'
  } catch {
    orcaStatus.textContent = 'Could not download the 3MF. Use the download button instead.'
  }
  orcaStatusTimer = setTimeout(() => {
    openInOrcaBtn.disabled = false
  }, 1500)
})
autoReloadInput.addEventListener('change', () => {
  if (autoReloadInput.checked) {
    const selected = fileChooser.value || currentFile
    if (selected) loadModel(selected, false)
  }
})
draw()
return { root }
}
