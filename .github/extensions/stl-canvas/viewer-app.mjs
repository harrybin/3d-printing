export const APP_HTML = `
<div class="toolbar">
  <div class="field grow">
    <label for="fileChooser">File</label>
    <select id="fileChooser"><option value="">Loading…</option></select>
  </div>
  <div class="field">
  <button type="button" id="reloadBtn" title="Reload current STL">Reload</button>
</div>
<label class="field"><input id="autoReload" type="checkbox"> Auto reload</label>
<div class="field">
  <label for="zoom">Zoom</label>
    <input id="zoom" type="range" min="0.1" max="5" step="0.1" value="1.7">
  </div>
  <div class="field">
    <label><input id="wireframe" type="checkbox"> Wireframe</label>
  </div>
  <div class="field">
    <label for="shading">Shading</label>
    <select id="shading">
      <option value="lambert">Lambert</option>
      <option value="phong">Phong</option>
      <option value="normal">Normal</option>
      <option value="basic">Basic</option>
    </select>
  </div>
</div>
<div class="toolbar secondary">
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
<div class="viewer-container">
  <canvas id="view"></canvas>
  <div id="info" hidden></div>
  <div id="measurePanel" hidden></div>
</div>
<div id="meta">Loading model…</div>

`

export function initStlCanvas(options = {}) {
const root = options.root || document.querySelector('#app') || document.body
root.innerHTML = APP_HTML
const VIEW_STORAGE_KEY = options.viewStorageKey || 'stl-canvas-view-defaults'
const defaultModelFile = new URLSearchParams(window.location.search).get('model') || options.defaultModelFile || ''
const runtimeMode = options.dataSource === 'extension' ? 'extension' : 'static'
const modelsBasePath = options.modelsBasePath || './models'
const modelsIndexUrl = options.modelsIndexUrl || `${modelsBasePath}/models.json`
const viewApiUrl = options.viewApiUrl || '/api/view'
const modelsApiUrl = options.modelsApiUrl || '/api/models'
const modelApiUrl = options.modelApiUrl || '/api/model'
const pollIntervalMs = Number.isFinite(options.pollIntervalMs) ? options.pollIntervalMs : 1500
const storageShadingModes = ['basic', 'lambert', 'normal', 'phong']
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

function sanitizeView(input) {
  const out = {}
  for (const key of ['rotX', 'rotY', 'rotZ', 'panX', 'panY', 'zoom']) {
    const raw = input?.[key]
    if (raw === null || raw === undefined || raw === '') continue
    const value = Number(raw)
    if (!Number.isFinite(value)) continue
    out[key] = key === 'zoom' ? Math.min(5, Math.max(0.1, value)) : value
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

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

let baseView = { ...configuredFallbackView };
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
const reloadBtn = document.getElementById('reloadBtn');
const autoReloadInput = document.getElementById('autoReload');
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
showAxesInput.checked = baseView.showAxes;
showBoxInput.checked = baseView.showBoundingBox;
showInfoInput.checked = baseView.showInfo;
wireframeInput.checked = baseView.wireframe;
shadingInput.value = baseView.shading;
let rawTriangles = [];
let triangles = [];
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
let currentMtime = 0;
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

function computeBounds(tris) {
  if (!tris.length) return null;
  let min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (const tri of tris) for (const v of tri) for (let i = 0; i < 3; i++) { if (v[i] < min[i]) min[i] = v[i]; if (v[i] > max[i]) max[i] = v[i]; }
  return { min: { x: min[0], y: min[1], z: min[2] }, max: { x: max[0], y: max[1], z: max[2] }, size: { x: max[0] - min[0], y: max[1] - min[1], z: max[2] - min[2] } };
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
  modelBounds = computeBounds(triangles) || modelBounds;
  computeCornerNormals();
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

function modelUrl(file) {
  return `${modelsBasePath}/${encodeURIComponent(file)}`;
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
  const res = await fetch(`${modelsIndexUrl}?t=${Date.now()}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('models.json not found');
  const data = await res.json();
  return { files: Array.isArray(data.files) ? data.files : [], mtimes: null };
}

async function readModelVersion(file) {
  if (runtimeMode === 'extension') return currentMtime || 0;
  try {
    const res = await fetch(`${modelUrl(file)}?t=${Date.now()}`, { method: 'HEAD', cache: 'no-store' });
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
  const response = await fetch(`${modelUrl(file)}?t=${Date.now()}`, { cache: 'no-store' })
  if (!response.ok) throw new Error(`Model file not found: models/${file}`)
  const buffer = await response.arrayBuffer()
  const parsed = parseStlBuffer(buffer)
  return {
    path: file,
    stats: { ...parsed, triangles: undefined },
    triangles: parsed.triangles || [],
    mtime: await readModelVersion(file),
  }
}

function loadModel(file, preserveView) {
  const meta = document.getElementById('meta')
  return fetchModelData(file)
    .then((data) => {
      if (data.error) { meta.textContent = data.error; return false }
      const s = data.stats || {}
      const b = s.bounds
      const trianglesData = Array.isArray(data.triangles) ? data.triangles : []
      if (!s.facets || s.facets <= 0 || !trianglesData.length) {
        const msg = 'Failed to load STL: no facet data found. Check that the file is a valid STL export.'
        meta.textContent = msg
        triangles = []
        rawTriangles = []
        modelBounds = null
        currentFile = file
        currentMtime = runtimeMode === 'extension' ? 0 : ''
        return false
      }
      const safeFile = escapeHtml(data.path || file)
      meta.innerHTML = '<span><strong>File:</strong> ' + safeFile + '</span>' +
        '<span><strong>Format:</strong> ' + (s.format === 'binary' ? 'Binary' : 'ASCII') + '</span>' +
        '<span><strong>Facets:</strong> ' + s.facets + '</span>' +
        '<span><strong>Vertices:</strong> ' + s.vertices + '</span>' +
        (b ? '<span><strong>Size (mm):</strong> ' + b.size.x.toFixed(1) + ' x ' + b.size.y.toFixed(1) + ' x ' + b.size.z.toFixed(1) + '</span>' : '')
      triangles = []
      rawTriangles = []
      for (const tri of trianglesData) {
        if (Array.isArray(tri) && tri.length === 3) rawTriangles.push(tri)
      }
      modelBounds = b || computeBounds(rawTriangles)
      applyModelRotation()
      currentFile = file
      currentMtime = data.mtime || (runtimeMode === 'extension' ? 0 : '')
      if (!preserveView) applySavedOrFit()
      draw()
      return true
    })
    .catch((err) => {
      meta.textContent = 'Failed to load model: ' + err
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
// Poll models/ so externally rewritten STL files refresh the viewer automatically.
function pollForChanges() {
  readModelManifest().then(({ files, mtimes }) => {
    if (!files.length) return
    refreshFileChooser(files)
    const selected = fileChooser.value
    if (!selected || !autoReloadInput.checked) return
    if (runtimeMode === 'extension') {
      const version = (mtimes || {})[selected] || 0
      if (selected !== currentFile) { loadModel(selected, false); return }
      if (version && version !== currentMtime) loadModel(selected, true)
      return
    }
    readModelVersion(selected).then((version) => {
      if (!version) return
      if (selected !== currentFile) { loadModel(selected, false); return }
      if (currentMtime && version !== currentMtime) loadModel(selected, true)
    }).catch(() => {})
  }).catch(() => {})
}

function resizeCanvas() { const rect = canvas.getBoundingClientRect(); canvas.width = rect.width * window.devicePixelRatio; canvas.height = rect.height * window.devicePixelRatio; ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.scale(window.devicePixelRatio, window.devicePixelRatio); }
// Turntable camera: yaw around the model's Z (up) axis, then pitch, then screen roll.
function rot(v, rx, ry, rz) { let [x, y, z] = v; const cy = Math.cos(ry), sy = Math.sin(ry), cx = Math.cos(rx), sx = Math.sin(rx), cz = Math.cos(rz), sz = Math.sin(rz); let t = x * cy - y * sy; y = x * sy + y * cy; x = t; t = y * cx - z * sx; z = y * sx + z * cx; y = t; t = x * cz - y * sz; y = x * sz + y * cz; x = t; return [x, y, z]; }
function projectPoint(v, rx, ry, rz, w, h, zoom) { const r = rot(v, rx, ry, rz); const x = r[0] + panX; const y = r[1] + panY; const z = r[2]; const f = 420 / (420 - z); return [w / 2 + x * f * MM_TO_PX * zoom, h / 2 - y * f * MM_TO_PX * zoom, z]; }
function drawBuildPlate(w, h, rx, ry, rz, zoom) {
  const half = BED_SIZE_MM / 2;
  const bedY = 0;
  const thickness = 6;
  const top = [
    [-half, -half, bedY],
    [half, -half, bedY],
    [half, half, bedY],
    [-half, half, bedY],
  ].map((p) => projectPoint(p, rx, ry, rz, w, h, zoom));
  const low = [
    [-half, -half, bedY - thickness],
    [half, -half, bedY - thickness],
    [half, half, bedY - thickness],
    [-half, half, bedY - thickness],
  ].map((p) => projectPoint(p, rx, ry, rz, w, h, zoom));
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
function shadeNormal(nx, ny, nz, mode, out) {
  if (mode === 'basic') { out[0] = 31; out[1] = 111; out[2] = 235; return; }
  if (mode === 'normal') {
    out[0] = 127 + 128 * nx; out[1] = 127 + 128 * ny; out[2] = 127 + 128 * nz; return;
  }
  const d = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2];
  // Ambient plus a weak fill from behind keeps cavities readable.
  const intensity = 0.30 + 0.78 * Math.max(0, d) + 0.10 * Math.max(0, -d);
  let r = SURFACE[0] * intensity, g = SURFACE[1] * intensity, b = SURFACE[2] * intensity;
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
  const dpr = window.devicePixelRatio || 1;
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
      shadeNormal(n[0], n[1], n[2], mode, cols[j]);
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
  const maxSize = Math.max(sizeX, sizeY, sizeZ);
  // Zoom 1.0 shows the whole 250 mm plate; smaller models get zoomed in.
  zoomInput.value = Math.max(0.6, Math.min(3, 110 / maxSize));
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
  const w = canvas.width / window.devicePixelRatio, h = canvas.height / window.devicePixelRatio;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = VIEW_BACKGROUND;
  ctx.fillRect(0, 0, w, h);
  const rx = rotX * Math.PI / 180, ry = rotY * Math.PI / 180, rz = rotZ * Math.PI / 180, zoom = parseFloat(zoomInput.value);
  drawBuildPlate(w, h, rx, ry, rz, zoom);
  if (showGridInput.checked) drawGrid(w, h, rx, ry, rz, zoom);
  const centerX = modelBounds ? (modelBounds.min.x + modelBounds.max.x) / 2 : 0;
  const centerY = modelBounds ? (modelBounds.min.y + modelBounds.max.y) / 2 : 0;
  const baseZ = modelBounds ? modelBounds.min.z : 0;
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
  if (isRightDrag) { objectX += dx * 0.05; objectY -= dy * 0.05; } else if (isShiftDrag) { panX += dx * 0.5; panY += dy * 0.5; } else { rotY += dx * 0.5; rotX += dy * 0.5; }
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
canvas.addEventListener('wheel', (e) => { e.preventDefault(); const delta = e.deltaY > 0 ? -0.1 : 0.1; zoomInput.value = Math.max(0.1, Math.min(5, parseFloat(zoomInput.value) + delta)); draw(); saveView(); });
canvas.addEventListener('dblclick', () => { rotX = baseView.rotX; rotY = baseView.rotY; rotZ = baseView.rotZ || 0; panX = baseView.panX; panY = baseView.panY; savedZoom = Number.isFinite(baseView.zoom) ? baseView.zoom : null; applySavedOrFit(); draw(); saveView(); });
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
      fileChooser.innerHTML = '<option value="">No STL files in models/</option>'
      document.getElementById('meta').textContent = 'No STL files found in models/.'
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
  if (loaded !== false && pollTimer === null) pollTimer = setInterval(pollForChanges, pollIntervalMs)
})
fileChooser.addEventListener('change', () => { if (fileChooser.value) loadModel(fileChooser.value) })
reloadBtn.addEventListener('click', () => {
  const selected = fileChooser.value || currentFile
  if (selected) loadModel(selected, false)
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
