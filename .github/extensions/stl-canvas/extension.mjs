import { createServer } from "node:http";
import { existsSync, readdirSync, readFileSync, writeFileSync, mkdirSync, statSync } from "node:fs";
import { resolve, join, dirname } from "node:path";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";
import { joinSession, createCanvas, CanvasError } from "@github/copilot-sdk/extension";

const extensionDir = dirname(fileURLToPath(import.meta.url));
const viewerAppPath = join(extensionDir, "viewer-app.mjs");
const viewerCssPath = join(extensionDir, "viewer.css");
const servers = new Map();
function selectDefaultModel() {
    const files = listWorkspaceStlFiles();
    const preferred = files.find((name) => /duschscharnier|duschtur|shower|hinge/i.test(name)) || files[0];
    return preferred ? `models/${preferred}` : "models/cone_30mm_ascii.stl";
}
const defaultStlPath = selectDefaultModel();
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

function renderHtml(title, defaultFile) {
    const config = JSON.stringify({
        dataSource: "extension",
        defaultModelFile: defaultFile,
        viewApiUrl: "/api/view",
        modelsApiUrl: "/api/models",
        modelApiUrl: "/api/model",
    }).replace(/<\//g, "<\\/");
    return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>${title}</title>
    <link rel="stylesheet" href="/viewer.css" />
  </head>
  <body>
    <div id="app"></div>
    <script type="module">
      import { initStlCanvas } from '/viewer-app.mjs';
      initStlCanvas(${config});
    </script>
  </body>
</html>`;
}

async function startServer(modelPath) {
    const server = createServer((req, res) => {
        const url = new URL(req.url || '/', 'http://127.0.0.1');
        if (url.pathname === '/viewer-app.mjs') {
            try {
                res.setHeader('Content-Type', 'text/javascript; charset=utf-8');
                res.end(readFileSync(viewerAppPath, 'utf8'));
            } catch {
                res.statusCode = 404;
                res.end('viewer-app.mjs not found');
            }
            return;
        }
        if (url.pathname === '/viewer.css') {
            try {
                res.setHeader('Content-Type', 'text/css; charset=utf-8');
                res.end(readFileSync(viewerCssPath, 'utf8'));
            } catch {
                res.statusCode = 404;
                res.end('viewer.css not found');
            }
            return;
        }
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
        res.end(renderHtml("STL Canvas", defaultModelFile));
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
