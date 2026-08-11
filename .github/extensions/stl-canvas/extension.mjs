import { createServer } from "node:http";
import { existsSync, readdirSync, readFileSync, writeFileSync, mkdirSync, statSync } from "node:fs";
import { resolve, join, dirname } from "node:path";
import { homedir } from "node:os";
import { joinSession, createCanvas, CanvasError } from "@github/copilot-sdk/extension";

const servers = new Map();
const defaultStlPath = "models\\cone_30mm_ascii.stl";
const defaultModelFile = defaultStlPath.split(/[\\/]/).pop();

const fallbackView = { rotX: -64.5, rotY: 8, panX: 0, panY: 0, zoom: 1.0 };
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
    for (const key of ["rotX", "rotY", "panX", "panY", "zoom"]) {
        const raw = input?.[key];
        if (raw === null || raw === undefined || raw === "") continue;
        const value = Number(raw);
        if (!Number.isFinite(value)) continue;
        // Zoom must stay inside the slider's usable range or the viewer renders nothing.
        out[key] = key === "zoom" ? Math.min(5, Math.max(0.1, value)) : value;
    }
    return out;
}

function writeViewDefaults(view) {
    const merged = { ...readViewDefaults(), ...sanitizeView(view) };
    mkdirSync(dirname(viewStatePath), { recursive: true });
    writeFileSync(viewStatePath, JSON.stringify(merged, null, 2), "utf8");
    return merged;
}

function resolveWorkspaceModelPath(stlPath) {
    return resolve(process.cwd(), stlPath);
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
        return { facets: 0, vertices: 0, uniqueVertices: 0, bounds: null };
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
      .viewer-container { flex: 1; min-height: 0; padding: 10px 12px; }
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
        <label for="zoom">Zoom</label>
        <input id="zoom" type="range" min="0.1" max="5" step="0.1" value="1.7">
      </div>
      <div class="field">
        <label><input id="wireframe" type="checkbox"> Wireframe</label>
      </div>
    </div>
    <div class="viewer-container">
      <canvas id="view"></canvas>
    </div>
    <div id="meta">Loading model…</div>
    <script>
      const baseView = ${JSON.stringify(fallbackView)};
      let rotX = baseView.rotX, rotY = baseView.rotY, panX = baseView.panX, panY = baseView.panY, objectX = 0, objectY = 0;
      let isDragging = false, isShiftDrag = false, isRightDrag = false, lastX = 0, lastY = 0;
      const canvas = document.getElementById('view');
      const ctx = canvas.getContext('2d');
      const fileChooser = document.getElementById('fileChooser');
      const zoomInput = document.getElementById('zoom');
      const wireframeInput = document.getElementById('wireframe');
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
            body: JSON.stringify({ rotX: rotX, rotY: rotY, panX: panX, panY: panY, zoom: parseFloat(zoomInput.value) })
          }).catch(() => {});
        }, 400);
      }
      function loadModel(file, preserveView) {
        const meta = document.getElementById('meta');
        return fetch('/api/model?file=' + encodeURIComponent(file) + '&t=' + Date.now()).then(r => r.json()).then(data => {
          if (data.error) { meta.textContent = data.error; return; }
          const s = data.stats;
          const b = s.bounds;
          meta.innerHTML = '<span><strong>File:</strong> ' + data.path + '</span>' +
            '<span><strong>Facets:</strong> ' + s.facets + '</span>' +
            '<span><strong>Vertices:</strong> ' + s.vertices + '</span>' +
            (b ? '<span><strong>Size (mm):</strong> ' + b.size.x.toFixed(1) + ' x ' + b.size.y.toFixed(1) + ' x ' + b.size.z.toFixed(1) + '</span>' : '');
          const re = /vertex\\s+([-\\d.eE+]+)\\s+([-\\d.eE+]+)\\s+([-\\d.eE+]+)/g;
          const verts = [];
          let m;
          while ((m = re.exec(data.content)) !== null) verts.push([+m[1], +m[2], +m[3]]);
          triangles = [];
          for (let i = 0; i < verts.length; i += 3) triangles.push([verts[i], verts[i + 1], verts[i + 2]]);
          modelBounds = b;
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
          const mtime = (data.mtimes || {})[selected] || 0;
          if (selected !== currentFile) { loadModel(selected, false); return; }
          if (mtime && mtime !== currentMtime) loadModel(selected, true);
        }).catch(() => {});
      }
      function resizeCanvas() { const rect = canvas.getBoundingClientRect(); canvas.width = rect.width * window.devicePixelRatio; canvas.height = rect.height * window.devicePixelRatio; ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.scale(window.devicePixelRatio, window.devicePixelRatio); }
      function rot(v, rx, ry, rz) { let [x, y, z] = v; const cy = Math.cos(ry), sy = Math.sin(ry), cx = Math.cos(rx), sx = Math.sin(rx), cz = Math.cos(rz), sz = Math.sin(rz); [x, z] = [x * cy + z * sy, -x * sy + z * cy]; [y, z] = [y * cx - z * sx, y * sx + z * cx]; [x, y] = [x * cz - y * sz, x * sz + y * cz]; return [x, y, z]; }
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
        const rx = rotX * Math.PI / 180, ry = rotY * Math.PI / 180, rz = 0, zoom = parseFloat(zoomInput.value);
        drawBuildPlate(w, h, rx, ry, rz, zoom);
        const centerX = modelBounds ? (modelBounds.min.x + modelBounds.max.x) / 2 : 0;
        const centerY = modelBounds ? (modelBounds.min.y + modelBounds.max.y) / 2 : 0;
        const baseZ = modelBounds ? modelBounds.min.z : 0;
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
            const r = Math.round(31 + 120 * light), g = Math.round(111 + 90 * light), b = Math.round(235 * light + 20);
            ctx.fillStyle = 'rgb(' + r + ',' + g + ',' + b + ')';
            ctx.beginPath();
            ctx.moveTo(tri[0][0], tri[0][1]);
            ctx.lineTo(tri[1][0], tri[1][1]);
            ctx.lineTo(tri[2][0], tri[2][1]);
            ctx.closePath();
            ctx.fill();
          }
        }
      }
      resizeCanvas();
      window.addEventListener('resize', () => { resizeCanvas(); draw(); });
      canvas.addEventListener('contextmenu', (e) => e.preventDefault());
      canvas.addEventListener('mousedown', (e) => { isDragging = true; isShiftDrag = e.shiftKey; isRightDrag = e.button === 2; lastX = e.clientX; lastY = e.clientY; });
      document.addEventListener('mousemove', (e) => { if (!isDragging) return; const dx = e.clientX - lastX; const dy = e.clientY - lastY; if (isRightDrag) { objectX += dx * 0.05; objectY -= dy * 0.05; } else if (isShiftDrag) { panX += dx * 0.5; panY += dy * 0.5; } else { rotY += dx * 0.5; rotX += dy * 0.5; } lastX = e.clientX; lastY = e.clientY; draw(); });
      document.addEventListener('mouseup', () => { if (isDragging) { isDragging = false; saveView(); } });
      canvas.addEventListener('wheel', (e) => { e.preventDefault(); const delta = e.deltaY > 0 ? -0.1 : 0.1; zoomInput.value = Math.max(0.1, Math.min(5, parseFloat(zoomInput.value) + delta)); draw(); saveView(); });
      canvas.addEventListener('dblclick', () => { rotX = baseView.rotX; rotY = baseView.rotY; panX = baseView.panX; panY = baseView.panY; savedZoom = Number.isFinite(baseView.zoom) ? baseView.zoom : null; applySavedOrFit(); draw(); saveView(); });
      zoomInput.addEventListener('input', () => { draw(); saveView(); });
      wireframeInput.addEventListener('change', draw);
      fetch('/api/view').then(r => r.json()).then(view => {
        if (Number.isFinite(view.rotX)) rotX = view.rotX;
        if (Number.isFinite(view.rotY)) rotY = view.rotY;
        if (Number.isFinite(view.panX)) panX = view.panX;
        if (Number.isFinite(view.panY)) panY = view.panY;
        if (Number.isFinite(view.zoom)) { savedZoom = view.zoom; zoomInput.value = view.zoom; }
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
                const content = readFileSync(resolved, "utf8");
                const stats = parseAsciiStl(content);
                res.setHeader("Content-Type", "application/json; charset=utf-8");
                res.setHeader("Cache-Control", "no-store");
                res.end(JSON.stringify({ path: requested, stats, content, mtime: fileMtime(requested) }));
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
            description: "Renders and inspects an ASCII STL file from the workspace",
            inputSchema: {
                type: "object",
                properties: { stlPath: { type: "string", default: defaultStlPath } },
                required: ["stlPath"],
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
                            panX: { type: "number" },
                            panY: { type: "number" },
                            zoom: { type: "number" },
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
                        required: ["stlPath"],
                        additionalProperties: false,
                    },
                    handler: async (ctx) => {
                        const modelPath = resolveWorkspaceModelPath(ctx.input.stlPath);
                        if (!existsSync(modelPath)) throw new CanvasError("stl_not_found", `Model file not found: ${ctx.input.stlPath}`);
                        return parseAsciiStl(readFileSync(modelPath, "utf8"));
                    },
                },
            ],
            open: async (ctx) => {
                const modelPath = resolveWorkspaceModelPath(ctx.input.stlPath);
                if (!existsSync(modelPath)) throw new CanvasError("stl_not_found", `Model file not found: ${ctx.input.stlPath}`);
                let entry = servers.get(ctx.instanceId);
                if (!entry) {
                    entry = await startServer(modelPath);
                    servers.set(ctx.instanceId, entry);
                }
                return { title: `STL: ${ctx.input.stlPath}`, url: entry.url };
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
