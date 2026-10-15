import { existsSync, realpathSync } from "node:fs";
import { win32, posix } from "node:path";
import { spawn } from "node:child_process";

export function defaultOpenCommand(modelPath, {
    platform = process.platform,
    env = process.env,
} = {}) {
    if (platform === "win32") {
        const windir = env.SystemRoot || env.windir || String.raw`C:\Windows`;
        return { command: win32.join(windir, "explorer.exe"), args: [modelPath] };
    }
    if (platform === "darwin") return { command: "open", args: [modelPath] };
    return { command: "xdg-open", args: [modelPath] };
}

export function validateOrcaModelPath(modelPath, workspaceRoot, {
    exists = existsSync,
    canonicalize = realpathSync,
    path = (String(modelPath || "").includes("\\") || String(workspaceRoot || "").includes("\\") || /^[a-zA-Z]:/.test(String(modelPath || ""))) ? win32 : (process.platform === "win32" ? win32 : posix),
} = {}) {
    const resolved = path.resolve(String(modelPath || ""));
    if (!resolved.toLowerCase().endsWith(".3mf")) {
        throw new Error("Only 3MF projects can be opened.");
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

export async function launchDefault3mfApp(modelPath, {
    resolveCommand = defaultOpenCommand,
    spawnProcess = spawn,
} = {}) {
    const { command, args } = resolveCommand(modelPath);
    const child = spawnProcess(command, args, {
        detached: true,
        stdio: "ignore",
        windowsHide: false,
    });
    await new Promise((resolveSpawn, reject) => {
        child.once("error", reject);
        child.once("spawn", resolveSpawn);
    });
    child.unref();
    return command;
}
