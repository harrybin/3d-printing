import { existsSync, realpathSync } from "node:fs";
import { isAbsolute, join, relative, resolve, win32, posix } from "node:path";
import { spawn } from "node:child_process";

export function findOrcaSlicer({
    platform = process.platform,
    env = process.env,
    exists = existsSync,
} = {}) {
    const candidates = [
        env.ORCA_SLICER_BIN,
        platform === "win32" && env.ProgramW6432 ? join(env.ProgramW6432, "OrcaSlicer", "orca-slicer.exe") : "",
        platform === "win32" && env.ProgramFiles ? join(env.ProgramFiles, "OrcaSlicer", "orca-slicer.exe") : "",
        platform === "win32" && env.LOCALAPPDATA
            ? join(env.LOCALAPPDATA, "Programs", "OrcaSlicer", "orca-slicer.exe")
            : "",
        platform === "win32" ? String.raw`C:\Program Files\OrcaSlicer\orca-slicer.exe` : "",
        platform === "darwin" ? "/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer" : "",
        platform === "linux" ? "/usr/bin/orca-slicer" : "",
        platform === "linux" ? "/usr/local/bin/orca-slicer" : "",
    ].filter(Boolean);
    return candidates.find((candidate) => exists(candidate)) || "";
}

export function validateOrcaModelPath(modelPath, workspaceRoot, {
    exists = existsSync,
    canonicalize = realpathSync,
    path = (String(modelPath || "").includes("\\") || String(workspaceRoot || "").includes("\\") || /^[a-zA-Z]:/.test(String(modelPath || ""))) ? win32 : (process.platform === "win32" ? win32 : posix),
} = {}) {
    const resolved = path.resolve(String(modelPath || ""));
    if (!resolved.toLowerCase().endsWith(".3mf")) {
        throw new Error("Only 3MF projects can be opened in OrcaSlicer.");
    }
    if (!exists(resolved)) throw new Error(`Model file not found: ${resolved}`);
    const canonicalModelPath = canonicalize(resolved);
    const canonicalWorkspaceRoot = canonicalize(path.resolve(workspaceRoot));
    const relativePath = path.relative(canonicalWorkspaceRoot, canonicalModelPath);
    if (relativePath.startsWith("..") || path.isAbsolute(relativePath)) {
        throw new Error(`Model path is outside the current workspace: ${canonicalModelPath}`);
    }
    return canonicalModelPath;
}

export async function launchOrcaSlicer(modelPath, {
    findExecutable = findOrcaSlicer,
    spawnProcess = spawn,
} = {}) {
    const executable = findExecutable();
    if (!executable) {
        throw new Error("OrcaSlicer executable not found. Set ORCA_SLICER_BIN or install OrcaSlicer.");
    }
    const child = spawnProcess(executable, [modelPath], {
        detached: true,
        stdio: "ignore",
        windowsHide: false,
    });
    await new Promise((resolveSpawn, reject) => {
        child.once("error", reject);
        child.once("spawn", resolveSpawn);
    });
    child.unref();
    return executable;
}
