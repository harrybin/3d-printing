import { createServer } from "node:http";
import { existsSync, readdirSync, readFileSync, writeFileSync, mkdirSync, statSync } from "node:fs";
import { resolve, join, dirname } from "node:path";
import { homedir } from "node:os";
import { randomBytes } from "node:crypto";
import { fileURLToPath } from "node:url";
import { inflateRawSync } from "node:zlib";
import { joinSession, createCanvas, CanvasError } from "@github/copilot-sdk/extension";
import { compose3mfTransforms, transform3mfPoint as apply3mfTransform, orcaMaterialAssignments } from "./viewer-app.mjs";
import { launchOrcaSlicer, validateOrcaModelPath } from "./orca-launcher.mjs";
import { createModelApiPayload, handleOrcaOpenRequest } from "./canvas-server-helpers.mjs";

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

const shadingModes = ["basic", "lambert", "normal", "phong", "material"];
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
        out[key] = key === "zoom" ? Math.min(30, Math.max(0.1, value)) : value;
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
        .filter((name) => /\.(stl|3mf)$/i.test(name))
        .sort((a, b) => a.localeCompare(b));
}

function fileVersion(name) {
    try {
        const stat = statSync(modelLabelToPath(name));
        // ZIP-based 3MF exports can be rewritten within one filesystem timestamp
        // tick. Including size makes auto-reload detect those replacements too.
        return `${stat.mtimeMs}:${stat.size}`;
    } catch {
        return "";
    }
}

function listWorkspaceModelVersions() {
    const out = {};
    for (const name of listWorkspaceStlFiles()) out[name] = fileVersion(name);
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

function meshStats(triangles, format) {
    let min = [Infinity, Infinity, Infinity];
    let max = [-Infinity, -Infinity, -Infinity];
    for (const triangle of triangles) {
        for (const vertex of triangle) {
            min = [Math.min(min[0], vertex[0]), Math.min(min[1], vertex[1]), Math.min(min[2], vertex[2])];
            max = [Math.max(max[0], vertex[0]), Math.max(max[1], vertex[1]), Math.max(max[2], vertex[2])];
        }
    }
    return {
        facets: triangles.length,
        vertices: triangles.length * 3,
        uniqueVertices: new Set(triangles.flat().map((vertex) => `${vertex[0]},${vertex[1]},${vertex[2]}`)).size,
        bounds: triangles.length
            ? {
                  min: { x: min[0], y: min[1], z: min[2] },
                  max: { x: max[0], y: max[1], z: max[2] },
                  size: { x: max[0] - min[0], y: max[1] - min[1], z: max[2] - min[2] },
              }
            : null,
        format,
    };
}

function readZipEntry(buffer, entryName) {
    for (let offset = buffer.length - 22; offset >= Math.max(0, buffer.length - 65557); offset -= 1) {
        if (buffer.readUInt32LE(offset) !== 0x06054b50) continue;
        let cursor = buffer.readUInt32LE(offset + 16);
        const entries = buffer.readUInt16LE(offset + 10);
        for (let index = 0; index < entries; index += 1) {
            if (buffer.readUInt32LE(cursor) !== 0x02014b50) throw new Error("Invalid 3MF central directory");
            const compression = buffer.readUInt16LE(cursor + 10);
            const compressedSize = buffer.readUInt32LE(cursor + 20);
            const nameLength = buffer.readUInt16LE(cursor + 28);
            const extraLength = buffer.readUInt16LE(cursor + 30);
            const commentLength = buffer.readUInt16LE(cursor + 32);
            const localOffset = buffer.readUInt32LE(cursor + 42);
            const name = buffer.subarray(cursor + 46, cursor + 46 + nameLength).toString("utf8");
            if (name === entryName) {
                if (buffer.readUInt32LE(localOffset) !== 0x04034b50) throw new Error("Invalid 3MF local header");
                const localNameLength = buffer.readUInt16LE(localOffset + 26);
                const localExtraLength = buffer.readUInt16LE(localOffset + 28);
                const start = localOffset + 30 + localNameLength + localExtraLength;
                const data = buffer.subarray(start, start + compressedSize);
                if (compression === 0) return data;
                if (compression === 8) return inflateRawSync(data);
                throw new Error(`Unsupported 3MF compression method: ${compression}`);
            }
            cursor += 46 + nameLength + extraLength + commentLength;
        }
        break;
    }
    throw new Error(`3MF entry not found: ${entryName}`);
}

function transform3mfPoint(point, transform) {
    if (!transform) return point;
    return apply3mfTransform(point, transform);
}

function parse3mfTransform(raw) {
    if (!raw) return null;
    const values = raw.trim().split(/[,\s]+/).map(Number);
    return values.length === 12 && values.every(Number.isFinite) ? values : null;
}

function xmlAttribute(tag, name) {
    return tag.match(new RegExp(`(?:^|\\s)(?:[\\w.-]+:)?${name}="([^"]*)"`))?.[1] || "";
}

function parse3mfDocument(xml, transform, triangles, triangleColors, assignment) {
    const materials = [...xml.matchAll(/<base\b[^>]*\bdisplaycolor="(#[0-9A-Fa-f]{6})(?:[0-9A-Fa-f]{2})?"[^>]*\/>/g)]
        .map((match) => match[1]);
    for (const object of xml.matchAll(/<object\b[\s\S]*?<\/object>/g)) {
        const verticesBlock = object[0].match(/<vertices>([\s\S]*?)<\/vertices>/);
        if (!verticesBlock) continue;
        const materialIndex = Number(object[0].match(/<object\b[^>]*\bpindex="(\d+)"/)?.[1]);
        const objectId = xmlAttribute(object[0].match(/<object\b[^>]*>/)[0], "id");
        const color = assignment?.parts.get(objectId) || assignment?.color || materials[materialIndex] || "#d6d9de";
        const vertices = [...verticesBlock[1].matchAll(/<vertex\b[^>]*\bx="([^"]+)"[^>]*\by="([^"]+)"[^>]*\bz="([^"]+)"[^>]*\/>/g)]
            .map((match) => transform3mfPoint([Number(match[1]), Number(match[2]), Number(match[3])], transform));
        for (const triangle of object[0].matchAll(/<triangle\b[^>]*\bv1="(\d+)"[^>]*\bv2="(\d+)"[^>]*\bv3="(\d+)"[^>]*\/>/g)) {
            const indices = [Number(triangle[1]), Number(triangle[2]), Number(triangle[3])];
            if (indices.every((index) => vertices[index])) {
                triangles.push(indices.map((index) => vertices[index]));
                triangleColors.push(color);
            }
        }
    }
}

function parse3mfPlateAssignments(buffer) {
    let xml;
    try {
        xml = readZipEntry(buffer, "Metadata/model_settings.config").toString("utf8");
    } catch {
        return new Map();
    }
    const assignments = new Map();
    for (const plateMatch of xml.matchAll(/<plate>([\s\S]*?)<\/plate>/g)) {
        const plateXml = plateMatch[1];
        const plateId = [...plateXml.matchAll(/<metadata\b[^>]*\/?>/g)]
            .map((match) => match[0])
            .find((tag) => xmlAttribute(tag, "key") === "plater_id");
        const id = plateId ? xmlAttribute(plateId, "value") : "";
        if (!id) continue;
        for (const instanceMatch of plateXml.matchAll(/<model_instance>([\s\S]*?)<\/model_instance>/g)) {
            const objectTag = [...instanceMatch[1].matchAll(/<metadata\b[^>]*\/?>/g)]
                .map((match) => match[0])
                .find((tag) => xmlAttribute(tag, "key") === "object_id");
            const objectId = objectTag ? xmlAttribute(objectTag, "value") : "";
            if (objectId) assignments.set(objectId, id);
        }
    }
    return assignments;
}

function parse3mfProjectMetadata(buffer) {
    let xml;
    try {
        xml = readZipEntry(buffer, "Metadata/ghouls_grip_print_metadata.xml").toString("utf8");
    } catch {
        return {};
    }
    const metadata = {};
    for (const match of xml.matchAll(
        /<metadata\b[^>]*\bname=(["'])(.*?)\1[^>]*\bvalue=(["'])(.*?)\3[^>]*\/?>/g,
    )) {
        metadata[match[2]] = match[4];
    }
    return metadata;
}

function parse3mfBuffer(buffer) {
    const rootXml = readZipEntry(buffer, "3D/3dmodel.model").toString("utf8");
    const triangles = [];
    const triangleColors = [];
    parse3mfDocument(rootXml, null, triangles, triangleColors);
    const projectMetadata = parse3mfProjectMetadata(buffer);
    const plateAssignments = parse3mfPlateAssignments(buffer);
    const optionalEntry = (path) => {
        try {
            return readZipEntry(buffer, path).toString("utf8");
        } catch (error) {
            if (error.message === `3MF entry not found: ${path}`) return null;
            throw error;
        }
    };
    const settingsXml = optionalEntry("Metadata/model_settings.config");
    const projectJson = optionalEntry("Metadata/project_settings.config");
    const node = (localName, tag, children = []) => ({
        localName, children, getAttribute: (name) => xmlAttribute(tag, name),
    });
    const metadataNodes = (xml) => [...xml.matchAll(/<metadata\b[^>]*\/?>/g)]
        .map((match) => node("metadata", match[0]));
    const objects = [...(settingsXml || "").matchAll(/<object\b([^>]*)>([\s\S]*?)<\/object>/g)]
        .map((match) => node("object", match[1], [
            ...metadataNodes(match[2].replace(/<part\b[\s\S]*?<\/part>/g, "")),
            ...[...match[2].matchAll(/<part\b([^>]*)>([\s\S]*?)<\/part>/g)]
                .map((part) => node("part", part[1], metadataNodes(part[2]))),
        ]));
    const assignments = projectJson
        ? orcaMaterialAssignments({ documentElement: { children: objects } }, JSON.parse(projectJson))
        : new Map();
    const plateGroups = new Map();

    const componentsByObject = new Map();
    for (const objectMatch of rootXml.matchAll(/<object\b([^>]*)>([\s\S]*?)<\/object>/g)) {
        const objectId = xmlAttribute(objectMatch[1], "id");
        const componentTag = objectMatch[2].match(/<component\b[^>]*\/?>/)?.[0];
        if (!objectId || !componentTag) continue;
        const path = xmlAttribute(componentTag, "path").replace(/^\/+/, "");
        if (!path) continue;
        componentsByObject.set(objectId, {
            path,
            transform: parse3mfTransform(xmlAttribute(componentTag, "transform")),
        });
    }
    for (const itemMatch of rootXml.matchAll(/<item\b[^>]*\/?>/g)) {
        const itemTag = itemMatch[0];
        const objectId = xmlAttribute(itemTag, "objectid");
        const component = componentsByObject.get(objectId);
        if (!component) continue;
        const transform = compose3mfTransforms(
            parse3mfTransform(xmlAttribute(itemTag, "transform")),
            component.transform,
        );
        const xml = readZipEntry(buffer, component.path).toString("utf8");
        const itemTriangles = [];
        const itemColors = [];
        parse3mfDocument(xml, transform, itemTriangles, itemColors, assignments.get(objectId));
        triangles.push(...itemTriangles);
        triangleColors.push(...itemColors);
        const plateId = plateAssignments.get(objectId) || "1";
        const plate = plateGroups.get(plateId) || {
            id: plateId,
            triangles: [],
            triangleColors: [],
        };
        plate.triangles.push(...itemTriangles);
        plate.triangleColors.push(...itemColors);
        plateGroups.set(plateId, plate);
    }
    const plates = [...plateGroups.values()]
        .sort((left, right) => Number(left.id) - Number(right.id))
        .map((plate) => ({
            ...plate,
            stats: meshStats(plate.triangles, "3mf"),
        }));
    return {
        ...meshStats(triangles, "3mf"),
        triangles,
        triangleColors,
        plates,
        projectMetadata,
    };
}

function parseModelBuffer(modelPath, buffer) {
    return modelPath.toLowerCase().endsWith(".3mf") ? parse3mfBuffer(buffer) : parseStlBuffer(buffer);
}

function readStlFile(modelPath) {
    const raw = readFileSync(modelPath);
    const parsed = parseModelBuffer(modelPath, raw);
    return {
        path: modelPath.split(/[\\/]/).pop(),
        format: parsed.format,
        stats: { ...parsed, triangles: undefined, triangleColors: undefined },
        projectMetadata: parsed.projectMetadata || {},
        content: parsed.format === "ascii" ? raw.toString("utf8") : "",
        triangles: parsed.triangles || [],
        triangleColors: parsed.triangleColors || [],
        mtime: fileVersion(modelPath.split(/[\\/]/).pop()),
    };
}

// JSON embedded in a <script> block: escape the characters that could close the
// tag. Entity escaping is wrong here because script content is raw text.
function escapeJsonForScript(json) {
    return json.replace(/</g, "\\u003c").replace(/>/g, "\\u003e").replace(/&/g, "\\u0026");
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function renderHtml(title, defaultFile, openInOrcaNonce) {
    const config = escapeJsonForScript(JSON.stringify({
        dataSource: "extension",
        defaultModelFile: defaultFile,
        viewApiUrl: "/api/view",
        modelsApiUrl: "/api/models",
        modelApiUrl: "/api/model",
        modelDownloadApiUrl: "/api/model-file",
        projectImageApiUrl: "/api/project-image",
        openInOrcaApiUrl: "/api/open-in-orca",
        openInOrcaNonce,
    }));
    return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>${escapeHtml(title)}</title>
    <link rel="stylesheet" href="/viewer.css" />
  </head>
  <body>
    <div id="app"></div>
    <script id="stl-canvas-config" type="application/json">${config}</script>
    <script type="module">
      import { initStlCanvas } from '/viewer-app.mjs';
      initStlCanvas(JSON.parse(document.getElementById('stl-canvas-config').textContent));
    </script>
  </body>
</html>`;
}

async function startServer(modelPath) {
    const instanceDefaultFile = modelPath.split(/[\\/]/).pop();
    const openInOrcaNonce = randomBytes(32).toString("hex");
    const server = createServer(async (req, res) => {
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
            res.end(JSON.stringify({ files: listWorkspaceStlFiles(), mtimes: listWorkspaceModelVersions() }));
            return;
        }
        if (url.pathname === "/api/model-file") {
            try {
                const requested = (url.searchParams.get("file") || instanceDefaultFile).split(/[\\/]/).pop();
                const resolved = modelLabelToPath(requested);
                if (!existsSync(resolved)) throw new Error(`Model file not found: models/${requested}`);
                const extension = requested.toLowerCase().endsWith(".3mf") ? "model/3mf" : "model/stl";
                res.setHeader("Content-Type", extension);
                res.setHeader("Content-Disposition", `attachment; filename*=UTF-8''${encodeURIComponent(requested)}`);
                res.setHeader("Cache-Control", "no-store");
                res.end(readFileSync(resolved));
            } catch (err) {
                res.statusCode = 404;
                res.setHeader("Content-Type", "text/plain; charset=utf-8");
                res.end(String(err));
            }
            return;
        }
        if (url.pathname === "/api/project-image") {
            if (req.method !== "GET" && req.method !== "HEAD") {
                res.statusCode = 405;
                res.setHeader("Allow", "GET, HEAD");
                res.end("Method not allowed");
                return;
            }
            const imagePath = url.searchParams.get("path") || "";
            const prefix = "docs/images/";
            const filename = imagePath.startsWith(prefix) ? imagePath.slice(prefix.length) : "";
            if (!filename || filename.includes("/") || filename.includes("\\") ||
                /[\u0000-\u001f]/.test(filename) || !/\.png$/i.test(filename)) {
                res.statusCode = 400;
                res.setHeader("Content-Type", "text/plain; charset=utf-8");
                res.end("Invalid project image path");
                return;
            }
            const resolved = resolve(process.cwd(), "docs", "images", filename);
            let imageSize;
            try {
                const stat = statSync(resolved);
                if (stat.isFile()) imageSize = stat.size;
            } catch {
                imageSize = undefined;
            }
            if (imageSize === undefined) {
                res.statusCode = 404;
                res.setHeader("Content-Type", "text/plain; charset=utf-8");
                res.end("Project image not found");
                return;
            }
            res.setHeader("Content-Type", "image/png");
            res.setHeader("Cache-Control", "no-store");
            res.setHeader("Content-Length", String(imageSize));
            if (req.method === "HEAD") res.end();
            else res.end(readFileSync(resolved));
            return;
        }
        if (url.pathname === "/api/open-in-orca") {
            if (req.method !== "POST") {
                res.statusCode = 405;
                res.setHeader("Allow", "POST");
                res.end("Method not allowed");
                return;
            }
            await handleOrcaOpenRequest(req, res, {
                defaultModelPath: modelPath,
                expectedNonce: openInOrcaNonce,
                validate: (requestedPath) => validateOrcaModelPath(requestedPath, process.cwd()),
                launch: launchOrcaSlicer,
            });
            return;
        }
        if (req.url && req.url.startsWith("/api/model")) {
            try {
                const url = new URL(req.url, "http://127.0.0.1");
                const requested = (url.searchParams.get("file") || instanceDefaultFile).split(/[\\/]/).pop();
                const resolved = modelLabelToPath(requested);
                if (!existsSync(resolved)) throw new Error(`Model file not found: models/${requested}`);
                const raw = readFileSync(resolved);
                const parsed = parseModelBuffer(resolved, raw);
                const content = parsed.format === "ascii" ? raw.toString("utf8") : "";
                res.setHeader("Content-Type", "application/json; charset=utf-8");
                res.setHeader("Cache-Control", "no-store");
                res.end(JSON.stringify(createModelApiPayload({
                    requested,
                    resolved,
                    parsed,
                    content,
                    mtime: fileVersion(requested),
                })));
                return;
            } catch (err) {
                res.statusCode = 500;
                res.setHeader("Content-Type", "application/json; charset=utf-8");
                res.end(JSON.stringify({ error: String(err) }));
                return;
            }
        }
        res.setHeader("Content-Type", "text/html; charset=utf-8");
        res.end(renderHtml("STL Canvas", instanceDefaultFile, openInOrcaNonce));
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
            description: "Renders and inspects STL and 3MF model files from the workspace",
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
                        const parsed = parseModelBuffer(modelPath, raw);
                        return {
                            ...parsed,
                            triangles: undefined,
                            triangleColors: undefined,
                            plates: (parsed.plates || []).map((plate) => ({
                                id: plate.id,
                                stats: plate.stats,
                            })),
                        };
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
