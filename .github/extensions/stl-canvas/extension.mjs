import { createServer } from "node:http";
import { existsSync, readdirSync, readFileSync, writeFileSync, mkdirSync, statSync } from "node:fs";
import { resolve, join, dirname } from "node:path";
import { homedir } from "node:os";
import { joinSession, createCanvas, CanvasError } from "@github/copilot-sdk/extension";

const servers = new Map();
const defaultStlPath = "models\\cone_30mm_ascii.stl";
const defaultModelFile = defaultStlPath.split(/[\\/]/).pop();

const shadingModes = ["basic", "lambert", "normal", "phong"];
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
    shading: "lambert",
};
const viewStatePath = join(
    process.env.COPILOT_HOME || join(homedir(), ".copilot"),
    "extensions",
    "stl-canvas",
    "artifacts",
    "view-defaults.json",
);

function readViewDefaults() {
    try {
        if (!existsSync(viewStatePath)) return { ...fallbackView };
        const saved = JSON.parse(readFileSync(viewStatePath, "utf8"));
        return { ...fallbackView, ...sanitizeView(saved) };
    } catch {
        return { ...fallbackView };
    }
}

function sanitizeView(input) {
    const out = {};
    for (const key of ["rotX", "rotY", "rotZ", "panX", "panY", "zoom"]) {
        const raw = input?.[key];
        if (raw === null || raw === undefined || raw === "") continue;
        const value = Number(raw);
        if (!Number.isFinite(value)) continue;
        // Zoom must stay inside the slider's usable range or the viewer renders nothing.
        out[key] = key === "zoom" ? Math.min(5, Math.max(0.1, value)) : value;
    }
    for (const key of ["showGrid", "showAxes", "showBoundingBox", "showInfo", "wireframe"]) {
        const raw = input?.[key];
        if (typeof raw === "boolean") out[key] = raw;
    }
    if (shadingModes.includes(input?.shading)) out.shading = input.shading;
    return out;
}

function writeViewDefaults(view) {
    const merged = { ...readViewDefaults(), ...sanitizeView(view) };
    mkdirSync(dirname(viewStatePath), { recursive: true });
    writeFileSync(viewStatePath, JSON.stringify(merged, null, 2), "utf8");
    return merged;
}

function resolveWorkspaceModelPath(stlPath) {
    const normalized = (stlPath || defaultStlPath).replace(/\\/g, "/");
    if (/^[A-Za-z]:\//.test(normalized) || normalized.startsWith("/")) {
        return resolve(normalized);
    }
    const relative = normalized.includes("/") ? normalized : `models/${normalized}`;
    return resolve(process.cwd(), relative);
}

function resolveRequestedModelPath(inputStlPath) {
    const requested = inputStlPath || defaultStlPath;
    const candidate = resolveWorkspaceModelPath(requested);
    if (existsSync(candidate)) return { requested, modelPath: candidate };
    const fallback = listWorkspaceStlFiles()[0];
    if (fallback) return { requested: fallback, modelPath: resolveWorkspaceModelPath(`models/${fallback}`) };
    return { requested, modelPath: candidate };
}

function listWorkspaceStlFiles() {
    const modelsDir = resolve(process.cwd(), "models");
    if (!existsSync(modelsDir)) return [];
    return readdirSync(modelsDir)
        .filter((name) => name.toLowerCase().endsWith(".stl"))
        .sort((a, b) => a.localeCompare(b));
}

function fileMtime(name) {
    try {
        return statSync(modelLabelToPath(name)).mtimeMs;
    } catch {
        return 0;
    }
}

function listWorkspaceStlMtimes() {
    const out = {};
    for (const name of listWorkspaceStlFiles()) out[name] = fileMtime(name);
    return out;
}

function modelLabelToPath(label) {
    return resolve(process.cwd(), "models", label);
}

function parseAsciiStl(content) {
    if (!content) {
        return { facets: 0, vertices: 0, uniqueVertices: 0, bounds: null, format: "ascii" };
    }
    const vertexMatches = [...content.matchAll(/vertex\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)/g)];
    const facets = (content.match(/\bfacet normal\b/g) || []).length;
    const vertices = vertexMatches.map((m) => [Number(m[1]), Number(m[2]), Number(m[3])]);
    const unique = new Set(vertices.map((v) => `${v[0]},${v[1]},${v[2]}`)).size;
    let min = [Infinity, Infinity, Infinity];
    let max = [-Infinity, -Infinity, -Infinity];
    for (const v of vertices) {
        min = [Math.min(min[0], v[0]), Math.min(min[1], v[1]), Math.min(min[2], v[2])];
        max = [Math.max(max[0], v[0]), Math.max(max[1], v[1]), Math.max(max[2], v[2])];
    }
    return {
        facets,
        vertices: vertices.length,
        uniqueVertices: unique,
        bounds: vertices.length
            ? {
                  min: { x: min[0], y: min[1], z: min[2] },
                  max: { x: max[0], y: max[1], z: max[2] },
                  size: { x: max[0] - min[0], y: max[1] - min[1], z: max[2] - min[2] },
              }
            : null,
        format: "ascii",
    };
}

function parseBinaryStl(buffer) {
    if (!buffer || buffer.length < 84) {
        return { facets: 0, vertices: 0, uniqueVertices: 0, bounds: null, format: "binary" };
    }
    const facetCount = buffer.readUInt32LE(80);
    const triangles = [];
    let min = [Infinity, Infinity, Infinity];
    let max = [-Infinity, -Infinity, -Infinity];
    for (let i = 0; i < facetCount; i += 1) {
        const offset = 84 + i * 50;
        if (offset + 48 > buffer.length) break;
        const v1 = [buffer.readFloatLE(offset + 12), buffer.readFloatLE(offset + 16), buffer.readFloatLE(offset + 20)];
        const v2 = [buffer.readFloatLE(offset + 24), buffer.readFloatLE(offset + 28), buffer.readFloatLE(offset + 32)];
        const v3 = [buffer.readFloatLE(offset + 36), buffer.readFloatLE(offset + 40), buffer.readFloatLE(offset + 44)];
        const tri = [v1, v2, v3];
        triangles.push(tri);
        for (const v of tri) {
            min = [Math.min(min[0], v[0]), Math.min(min[1], v[1]), Math.min(min[2], v[2])];
            max = [Math.max(max[0], v[0]), Math.max(max[1], v[1]), Math.max(max[2], v[2])];
        }
    }
    const unique = new Set(triangles.flat().map((v) => `${v[0]},${v[1]},${v[2]}`)).size;
    return {
        facets: triangles.length,
        vertices: triangles.length * 3,
        uniqueVertices: unique,
        bounds: triangles.length
            ? {
                  min: { x: min[0], y: min[1], z: min[2] },
                  max: { x: max[0], y: max[1], z: max[2] },
                  size: { x: max[0] - min[0], y: max[1] - min[1], z: max[2] - min[2] },
              }
            : null,
        format: "binary",
    };
}

function detectStlFormat(buffer) {
    if (!buffer || buffer.length < 6) return "binary";
    const head = buffer.subarray(0, 256).toString("ascii", 0, 256).trimStart();
    return /^solid\b/i.test(head) ? "ascii" : "binary";
}

function parseStlBuffer(buffer) {
    const format = detectStlFormat(buffer);
    if (format === "ascii") {
        const text = buffer.toString("utf8");
        const parsed = parseAsciiStl(text);
        return { ...parsed, triangles: (text.match(/vertex\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)/g) || []).length ? (() => {
            const verts = [...text.matchAll(/vertex\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)/g)].map((m) => [+m[1], +m[2], +m[3]]);
            const tris = [];
            for (let i = 0; i < verts.length; i += 3) {
                if (i + 2 < verts.length) tris.push([verts[i], verts[i + 1], verts[i + 2]]);
            }
            return tris;
        })() : [] };
    }
    const parsed = parseBinaryStl(buffer);
    const triangles = [];
    const facetCount = buffer.readUInt32LE(80);
    for (let i = 0; i < facetCount; i += 1) {
        const offset = 84 + i * 50;
        if (offset + 48 > buffer.length) break;
        triangles.push([
            [buffer.readFloatLE(offset + 12), buffer.readFloatLE(offset + 16), buffer.readFloatLE(offset + 20)],
            [buffer.readFloatLE(offset + 24), buffer.readFloatLE(offset + 28), buffer.readFloatLE(offset + 32)],
            [buffer.readFloatLE(offset + 36), buffer.readFloatLE(offset + 40), buffer.readFloatLE(offset + 44)],
        ]);
    }
    return { ...parsed, triangles };
}

function readStlFile(modelPath) {
    const raw = readFileSync(modelPath);
    const format = detectStlFormat(raw);
    const parsed = parseStlBuffer(raw);
    return {
        path: modelPath.split(/[\\/]/).pop(),
        format,
        stats: { ...parsed, triangles: undefined },
        content: format === "ascii" ? raw.toString("utf8") : "",
        triangles: parsed.triangles || [],
        mtime: statSync(modelPath).mtimeMs,
    };
}

function renderHtml(title) {
    return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>${title}</title>
    <style>
      body { margin: 0; background: var(--background-color-default, #ffffff); color: var(--text-color-default, #1f2328); font-family: var(--font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif); font-size: var(--text-body-medium, 13px); display: flex; flex-direction: column; height: 100vh; }
      .toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 12px; padding: 10px 12px; border-bottom: 1px solid var(--border-color-default, #d1d9e0); }
      .field { display: flex; align-items: center; gap: 6px; font-size: 12px; white-space: nowrap; }
      .field.grow { flex: 1 1 180px; min-width: 140px; }
      select { font: inherit; flex: 1 1 auto; min-width: 0; padding: 5px 8px; border: 1px solid var(--border-color-default, #d1d9e0); border-radius: 6px; background: var(--background-color-default, #ffffff); color: var(--text-color-default, #1f2328); }
      option { background: var(--background-color-default, #ffffff); color: var(--text-color-default, #1f2328); }
      input[type="range"] { flex: 1 1 80px; min-width: 70px; }
      .toolbar.secondary { gap: 6px 16px; }
      .group { display: flex; align-items: center; gap: 4px; }
      .group > .group-label { font-size: 11px; text-transform: uppercase; letter-spacing: .04em; color: var(--text-color-muted, #57606a); margin-right: 2px; }
      button { font: inherit; font-size: 12px; padding: 4px 8px; border: 1px solid var(--border-color-default, #d1d9e0); border-radius: 6px; background: var(--background-color-default, #ffffff); color: var(--text-color-default, #1f2328); cursor: pointer; }
      button:hover { border-color: var(--border-color-emphasis, #8c959f); }
      button:active { transform: translateY(1px); }
      .viewer-container { flex: 1; min-height: 0; padding: 10px 12px; position: relative; }
      #info { position: absolute; top: 18px; left: 20px; padding: 8px 10px; border-radius: 6px; background: rgba(13, 17, 23, 0.78); color: #e6edf3; font-family: var(--font-mono, ui-monospace, SFMono-Regular, Consolas, monospace); font-size: 11px; line-height: 1.5; pointer-events: none; white-space: pre; }
      #info[hidden] { display: none; }
      #view { display: block; width: 100%; height: 100%; border: 1px solid var(--border-color-default, #d1d9e0); border-radius: 6px; background: #0d1117; cursor: grab; }
      #view:active { cursor: grabbing; }
      #meta { padding: 8px 12px; border-top: 1px solid var(--border-color-default, #d1d9e0); font-size: 12px; color: var(--text-color-muted, #57606a); display: flex; flex-wrap: wrap; gap: 4px 14px; }
    </style>
  </head>
  <body>
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
    </div>
    <div class="viewer-container">
      <canvas id="view"></canvas>
      <div id="info" hidden></div>
    </div>
    <div id="meta">Loading model…</div>
    <script>
      const baseView = ${JSON.stringify(fallbackView)};
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
      let isDragging = false, isShiftDrag = false, isRightDrag = false, lastX = 0, lastY = 0;
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
      showGridInput.checked = baseView.showGrid;
      showAxesInput.checked = baseView.showAxes;
      showBoxInput.checked = baseView.showBoundingBox;
      showInfoInput.checked = baseView.showInfo;
      wireframeInput.checked = baseView.wireframe;
      shadingInput.value = baseView.shading;
      let rawTriangles = [];
      let triangles = [];
      let modelBounds = null;
      let currentFile = ${JSON.stringify(defaultModelFile)};
      // Anycubic Kobra S1 build plate: 250 x 250 mm.
      const BED_SIZE_MM = 250;
      const MM_TO_PX = 1.8;
      let currentMtime = 0;
      let knownFiles = [];
      let savedZoom = Number.isFinite(baseView.zoom) ? baseView.zoom : null;
      let saveTimer = null;
      function saveView() {
        clearTimeout(saveTimer);
        saveTimer = setTimeout(() => {
          fetch('/api/view', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              rotX: rotX, rotY: rotY, rotZ: rotZ, panX: panX, panY: panY, zoom: parseFloat(zoomInput.value),
              wireframe: wireframeInput.checked, shading: shadingInput.value,
              showGrid: showGridInput.checked, showAxes: showAxesInput.checked,
              showBoundingBox: showBoxInput.checked, showInfo: showInfoInput.checked
            })
          }).catch(() => {});
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
      }
      function applyViewPreset(name) {
        const preset = VIEW_PRESETS[name] || VIEW_PRESETS.isometric;
        rotX = preset.rotX; rotY = preset.rotY; rotZ = preset.rotZ;
        panX = 0; panY = 0;
        fitView();
        draw();
        saveView();
      }
      function loadModel(file, preserveView) {
        const meta = document.getElementById('meta');
        return fetch('/api/model?file=' + encodeURIComponent(file) + '&t=' + Date.now()).then(r => r.json()).then(data => {
          if (data.error) { meta.textContent = data.error; return; }
          const s = data.stats || {};
          const b = s.bounds;
          const trianglesData = Array.isArray(data.triangles) ? data.triangles : [];
          if (!s.facets || s.facets <= 0 || !trianglesData.length) {
            const msg = 'Failed to load STL: no facet data found. Check that the file is a valid STL export.';
            meta.textContent = msg;
            triangles = [];
            rawTriangles = [];
            modelBounds = null;
            currentFile = file;
            currentMtime = data.mtime || 0;
            return;
          }
          meta.innerHTML = '<span><strong>File:</strong> ' + data.path + '</span>' +
            '<span><strong>Format:</strong> ' + (s.format === 'binary' ? 'Binary' : 'ASCII') + '</span>' +
            '<span><strong>Facets:</strong> ' + s.facets + '</span>' +
            '<span><strong>Vertices:</strong> ' + s.vertices + '</span>' +
            (b ? '<span><strong>Size (mm):</strong> ' + b.size.x.toFixed(1) + ' x ' + b.size.y.toFixed(1) + ' x ' + b.size.z.toFixed(1) + '</span>' : '');
          triangles = [];
          rawTriangles = [];
          for (const tri of trianglesData) {
            if (Array.isArray(tri) && tri.length === 3) rawTriangles.push(tri);
          }
          modelBounds = b;
          applyModelRotation();
          currentFile = file;
          currentMtime = data.mtime || 0;
          if (!preserveView) applySavedOrFit();
          draw();
        }).catch((err) => { meta.textContent = 'Failed to load model: ' + err; });
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
        fetch('/api/models?t=' + Date.now()).then(r => r.json()).then(data => {
          const files = Array.isArray(data.files) ? data.files : [];
          if (!files.length) return;
          refreshFileChooser(files);
          const selected = fileChooser.value;
          if (!selected) return;
          if (!autoReloadInput.checked) return;
          const mtime = (data.mtimes || {})[selected] || 0;
          if (selected !== currentFile) { loadModel(selected, false); return; }
          if (mtime && mtime !== currentMtime) loadModel(selected, true);
        }).catch(() => {});
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
      function faceColor(light, nx, ny, nz, len) {
        const mode = shadingInput.value;
        if (mode === 'basic') return 'rgb(31,111,235)';
        if (mode === 'normal') {
          return 'rgb(' + Math.round(127 + 128 * (nx / len)) + ',' + Math.round(127 + 128 * (ny / len)) + ',' + Math.round(127 + 128 * (nz / len)) + ')';
        }
        if (mode === 'phong') {
          const spec = Math.pow(light, 12) * 160;
          return 'rgb(' + Math.round(Math.min(255, 31 + 120 * light + spec)) + ',' + Math.round(Math.min(255, 111 + 90 * light + spec)) + ',' + Math.round(Math.min(255, 235 * light + 20 + spec)) + ')';
        }
        return 'rgb(' + Math.round(31 + 120 * light) + ',' + Math.round(111 + 90 * light) + ',' + Math.round(235 * light + 20) + ')';
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
        ].filter(Boolean).join('\\n');
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
        ctx.fillStyle = '#eceef1';
        ctx.fillRect(0, 0, w, h);
        const rx = rotX * Math.PI / 180, ry = rotY * Math.PI / 180, rz = rotZ * Math.PI / 180, zoom = parseFloat(zoomInput.value);
        drawBuildPlate(w, h, rx, ry, rz, zoom);
        if (showGridInput.checked) drawGrid(w, h, rx, ry, rz, zoom);
        const centerX = modelBounds ? (modelBounds.min.x + modelBounds.max.x) / 2 : 0;
        const centerY = modelBounds ? (modelBounds.min.y + modelBounds.max.y) / 2 : 0;
        const baseZ = modelBounds ? modelBounds.min.z : 0;
        if (showAxesInput.checked) drawAxes(w, h, rx, ry, rz, zoom);
        const projected = triangles.map((t) => t.map((v) => projectPoint([v[0] - centerX + objectX, v[1] - centerY + objectY, v[2] - baseZ], rx, ry, rz, w, h, zoom)));
        if (wireframeInput.checked) {
          ctx.strokeStyle = '#58a6ff';
          ctx.lineWidth = 1;
          for (const tri of projected) { ctx.beginPath(); ctx.moveTo(tri[0][0], tri[0][1]); ctx.lineTo(tri[1][0], tri[1][1]); ctx.lineTo(tri[2][0], tri[2][1]); ctx.closePath(); ctx.stroke(); }
        } else {
          const faces = [];
          for (const tri of projected) {
            // Screen-space winding: negative area means the face points away from us.
            const area = (tri[1][0] - tri[0][0]) * (tri[2][1] - tri[0][1]) - (tri[2][0] - tri[0][0]) * (tri[1][1] - tri[0][1]);
            if (area >= 0) continue;
            faces.push({ tri, depth: (tri[0][2] + tri[1][2] + tri[2][2]) / 3, area });
          }
          faces.sort((a, b) => a.depth - b.depth);
          for (const face of faces) {
            const tri = face.tri;
            // Fake lighting from face size vs. its screen footprint so curvature reads as shading.
            const e1 = [tri[1][0] - tri[0][0], tri[1][1] - tri[0][1], tri[1][2] - tri[0][2]];
            const e2 = [tri[2][0] - tri[0][0], tri[2][1] - tri[0][1], tri[2][2] - tri[0][2]];
            const nx = e1[1] * e2[2] - e1[2] * e2[1];
            const ny = e1[2] * e2[0] - e1[0] * e2[2];
            const nz = e1[0] * e2[1] - e1[1] * e2[0];
            const len = Math.hypot(nx, ny, nz) || 1;
            const light = Math.min(1, Math.max(0.25, 0.35 + 0.75 * Math.abs((nx * -0.4 + ny * -0.5 + nz * -0.75) / len)));
            ctx.fillStyle = faceColor(light, nx, ny, nz, len);
            ctx.beginPath();
            ctx.moveTo(tri[0][0], tri[0][1]);
            ctx.lineTo(tri[1][0], tri[1][1]);
            ctx.lineTo(tri[2][0], tri[2][1]);
            ctx.closePath();
            ctx.fill();
          }
        }
        if (showBoxInput.checked) drawBoundingBox(w, h, rx, ry, rz, zoom, objectX - centerX, objectY - centerY);
        updateInfo();
      }
      resizeCanvas();
      window.addEventListener('resize', () => { resizeCanvas(); draw(); });
      canvas.addEventListener('contextmenu', (e) => e.preventDefault());
      canvas.addEventListener('mousedown', (e) => { isDragging = true; isShiftDrag = e.shiftKey; isRightDrag = e.button === 2; lastX = e.clientX; lastY = e.clientY; });
      document.addEventListener('mousemove', (e) => { if (!isDragging) return; const dx = e.clientX - lastX; const dy = e.clientY - lastY; if (isRightDrag) { objectX += dx * 0.05; objectY -= dy * 0.05; } else if (isShiftDrag) { panX += dx * 0.5; panY += dy * 0.5; } else { rotY += dx * 0.5; rotX += dy * 0.5; } lastX = e.clientX; lastY = e.clientY; draw(); });
      document.addEventListener('mouseup', () => { if (isDragging) { isDragging = false; saveView(); } });
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
      fetch('/api/view').then(r => r.json()).then(view => {
        if (Number.isFinite(view.rotX)) rotX = view.rotX;
        if (Number.isFinite(view.rotY)) rotY = view.rotY;
        if (Number.isFinite(view.rotZ)) rotZ = view.rotZ;
        if (Number.isFinite(view.panX)) panX = view.panX;
        if (Number.isFinite(view.panY)) panY = view.panY;
        if (Number.isFinite(view.zoom)) { savedZoom = view.zoom; zoomInput.value = view.zoom; }
        if (typeof view.wireframe === 'boolean') wireframeInput.checked = view.wireframe;
        if (typeof view.shading === 'string') shadingInput.value = view.shading;
        showGridInput.checked = typeof view.showGrid === 'boolean' ? view.showGrid : baseView.showGrid;
        showAxesInput.checked = typeof view.showAxes === 'boolean' ? view.showAxes : baseView.showAxes;
        showBoxInput.checked = typeof view.showBoundingBox === 'boolean' ? view.showBoundingBox : baseView.showBoundingBox;
        showInfoInput.checked = typeof view.showInfo === 'boolean' ? view.showInfo : baseView.showInfo;
      }).catch(() => {}).then(() => {
        return fetch('/api/models').then(r => r.json()).then(data => {
          const files = Array.isArray(data.files) ? data.files : [];
          if (!files.length) {
            fileChooser.innerHTML = '<option value="">No STL files in models/</option>';
            document.getElementById('meta').textContent = 'No STL files found in models/.';
            return;
          }
          fileChooser.innerHTML = files.map((name) => '<option value="' + name + '">' + name + '</option>').join('');
          fileChooser.value = files.indexOf(currentFile) >= 0 ? currentFile : files[0];
          knownFiles = files;
          loadModel(fileChooser.value);
        }).catch((err) => {
          fileChooser.innerHTML = '<option value="">Failed to list files</option>';
          document.getElementById('meta').textContent = 'Failed to list files: ' + err;
        });
      }).then(() => { setInterval(pollForChanges, 1500); });
      fileChooser.addEventListener('change', () => { if (fileChooser.value) loadModel(fileChooser.value); });
      reloadBtn.addEventListener('click', () => {
        const selected = fileChooser.value || currentFile;
        if (selected) loadModel(selected, false);
      });
      autoReloadInput.addEventListener('change', () => {
        if (autoReloadInput.checked) {
          const selected = fileChooser.value || currentFile;
          if (selected) loadModel(selected, false);
        }
      });
      draw();
    </script>
  </body>
</html>`;
}

async function startServer(modelPath) {
    const server = createServer((req, res) => {
        if (req.url && req.url.startsWith("/api/view")) {
            if (req.method === "POST") {
                let body = "";
                req.on("data", (chunk) => {
                    body += chunk;
                    if (body.length > 10000) req.destroy();
                });
                req.on("end", () => {
                    try {
                        const saved = writeViewDefaults(JSON.parse(body));
                        res.setHeader("Content-Type", "application/json; charset=utf-8");
                        res.end(JSON.stringify(saved));
                    } catch (err) {
                        res.statusCode = 400;
                        res.setHeader("Content-Type", "application/json; charset=utf-8");
                        res.end(JSON.stringify({ error: String(err) }));
                    }
                });
                return;
            }
            res.setHeader("Content-Type", "application/json; charset=utf-8");
            res.end(JSON.stringify(readViewDefaults()));
            return;
        }
        if (req.url && req.url.startsWith("/api/models")) {
            res.setHeader("Content-Type", "application/json; charset=utf-8");
            res.setHeader("Cache-Control", "no-store");
            res.end(JSON.stringify({ files: listWorkspaceStlFiles(), mtimes: listWorkspaceStlMtimes() }));
            return;
        }
        if (req.url && req.url.startsWith("/api/model")) {
            try {
                const url = new URL(req.url, "http://127.0.0.1");
                const requested = (url.searchParams.get("file") || defaultModelFile).split(/[\\/]/).pop();
                const resolved = modelLabelToPath(requested);
                if (!existsSync(resolved)) throw new Error(`Model file not found: models/${requested}`);
                const raw = readFileSync(resolved);
                const parsed = parseStlBuffer(raw);
                const content = detectStlFormat(raw) === "ascii" ? raw.toString("utf8") : "";
                res.setHeader("Content-Type", "application/json; charset=utf-8");
                res.setHeader("Cache-Control", "no-store");
                res.end(JSON.stringify({
                    path: requested,
                    stats: { ...parsed, triangles: undefined },
                    triangles: parsed.triangles || [],
                    content,
                    mtime: fileMtime(requested),
                }));
                return;
            } catch (err) {
                res.statusCode = 500;
                res.setHeader("Content-Type", "application/json; charset=utf-8");
                res.end(JSON.stringify({ error: String(err) }));
                return;
            }
        }
        res.setHeader("Content-Type", "text/html; charset=utf-8");
        res.end(renderHtml("STL Canvas"));
    });
    await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
    const address = server.address();
    const port = typeof address === "object" && address ? address.port : 0;
    return { server, url: `http://127.0.0.1:${port}/` };
}

await joinSession({
    canvases: [
        createCanvas({
            id: "stl-canvas",
            displayName: "STL Canvas",
            description: "Renders and inspects ASCII or binary STL files from the workspace",
            inputSchema: {
                type: "object",
                properties: { stlPath: { type: "string", default: defaultStlPath } },
                additionalProperties: false,
            },
            actions: [
                {
                    name: "get_view_defaults",
                    description: "Returns the saved default camera angles, pan and zoom for the viewer",
                    handler: async () => readViewDefaults(),
                },
                {
                    name: "set_view_defaults",
                    description: "Saves default camera angles, pan and zoom for the viewer",
                    inputSchema: {
                        type: "object",
                        properties: {
                            rotX: { type: "number" },
                            rotY: { type: "number" },
                            rotZ: { type: "number" },
                            panX: { type: "number" },
                            panY: { type: "number" },
                            zoom: { type: "number" },
                            wireframe: { type: "boolean" },
                            shading: { type: "string", enum: shadingModes },
                            showGrid: { type: "boolean" },
                            showAxes: { type: "boolean" },
                            showBoundingBox: { type: "boolean" },
                            showInfo: { type: "boolean" },
                        },
                        additionalProperties: false,
                    },
                    handler: async (ctx) => writeViewDefaults(ctx.input || {}),
                },
                {
                    name: "read_stats",
                    description: "Reads STL metadata such as facets and bounds",
                    inputSchema: {
                        type: "object",
                        properties: { stlPath: { type: "string", default: defaultStlPath } },
                        additionalProperties: false,
                    },
                    handler: async (ctx) => {
                        const { requested, modelPath } = resolveRequestedModelPath(ctx.input?.stlPath);
                        if (!existsSync(modelPath)) throw new CanvasError("stl_not_found", `Model file not found: ${requested}`);
                        const raw = readFileSync(modelPath);
                        const parsed = parseStlBuffer(raw);
                        return { ...parsed, triangles: undefined };
                    },
                },
            ],
            open: async (ctx) => {
                const { requested, modelPath } = resolveRequestedModelPath(ctx.input?.stlPath);
                if (!existsSync(modelPath)) throw new CanvasError("stl_not_found", `Model file not found: ${requested}`);
                let entry = servers.get(ctx.instanceId);
                if (!entry) {
                    entry = await startServer(modelPath);
                    servers.set(ctx.instanceId, entry);
                }
                return { title: `STL: ${requested}`, url: entry.url };
            },
            onClose: async (ctx) => {
                const entry = servers.get(ctx.instanceId);
                if (entry) {
                    servers.delete(ctx.instanceId);
                    await new Promise((resolve) => entry.server.close(() => resolve()));
                }
            },
        }),
    ],
});
