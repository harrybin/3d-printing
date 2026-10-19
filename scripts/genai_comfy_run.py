"""Run a ComfyUI image-to-3D workflow (API format) and download the mesh outputs.

Stdlib only. The server URL comes from --server or $COMFYUI_URL
(default http://127.0.0.1:8188, as written by genai_local_setup.py).

    .venv\\Scripts\\python.exe scripts\\genai_comfy_run.py ^
        --workflow %LOCALAPPDATA%\\3d-printing-genai\\workflows\\api\\pixal3d_trellis2_api.json ^
        --image build\\genai\\ref_cutout.png --seed 42 --out build\\genai\\run1

    --set 12.text=foo   sets input "text" of node id 12 (JSON-parsed value when possible)

Writes <out>/provenance.json with hashes, seed, settings and server version so a
generated seed mesh can be traced (lineage) in the model's docs/ provenance note.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

MESH_EXTS = {".glb", ".gltf", ".obj", ".ply", ".stl", ".fbx"}
SEED_INPUTS = ("seed", "noise_seed")


def is_api_format(wf: dict) -> bool:
    return bool(wf) and "nodes" not in wf and all(
        isinstance(v, dict) and "class_type" in v for v in wf.values())


def apply_inputs(wf: dict, image_name: str | None, image_nodes: list[str] | None,
                 seed: int | None, sets: list[str]) -> list[str]:
    """Mutate an API-format workflow in place; return a log of changes."""
    log: list[str] = []
    if image_name:
        targets = image_nodes or [k for k, v in wf.items() if v["class_type"] == "LoadImage"]
        if not targets:
            raise SystemExit("workflow has no LoadImage node; pass --image-node")
        for k in targets:
            wf[k]["inputs"]["image"] = image_name
            log.append(f"{k}.image={image_name}")
    if seed is not None:
        for k, v in wf.items():
            for name in SEED_INPUTS:
                if name in v.get("inputs", {}) and not isinstance(v["inputs"][name], list):
                    v["inputs"][name] = seed
                    log.append(f"{k}.{name}={seed}")
    for item in sets:
        target, _, raw = item.partition("=")
        node, _, name = target.partition(".")
        if node not in wf or not name:
            raise SystemExit(f"bad --set {item!r}: node {node!r} not in workflow")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw
        wf[node]["inputs"][name] = value
        log.append(f"{node}.{name}={value!r}")
    return log


def collect_files(outputs: dict, all_files: bool = False) -> list[dict]:
    """Find {filename, subfolder, type} entries anywhere in /history outputs."""
    found: list[dict] = []

    def walk(o):
        if isinstance(o, dict):
            if "filename" in o and isinstance(o["filename"], str):
                if all_files or Path(o["filename"]).suffix.lower() in MESH_EXTS:
                    found.append({"filename": o["filename"], "subfolder": o.get("subfolder", ""),
                                  "type": o.get("type", "output")})
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(outputs)
    return found


def _get(server: str, path: str, timeout: float = 60):
    with urllib.request.urlopen(server + path, timeout=timeout) as r:
        return r.read()


def upload_image(server: str, path: Path) -> str:
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{path.name}\"\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n").encode() + path.read_bytes() + \
        f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(server + "/upload/image", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        info = json.loads(r.read())
    return f"{info['subfolder']}/{info['name']}" if info.get("subfolder") else info["name"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workflow", type=Path, required=True, help="API-format JSON (File > Export (API))")
    ap.add_argument("--image", type=Path, help="input image (ideally background-removed RGBA)")
    ap.add_argument("--image-node", nargs="+", help="LoadImage node ids (default: all LoadImage nodes)")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--set", action="append", default=[], metavar="NODE.INPUT=VALUE")
    ap.add_argument("--server", default=os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--timeout", type=float, default=3600)
    ap.add_argument("--all-files", action="store_true", help="also download images/previews")
    args = ap.parse_args()
    server = args.server.rstrip("/")

    wf = json.loads(args.workflow.read_text(encoding="utf-8-sig"))
    if not is_api_format(wf):
        sys.exit("workflow is in UI format; open it in ComfyUI and use File > Export (API)")
    try:
        stats = json.loads(_get(server, "/system_stats", 10))
    except OSError as e:
        sys.exit(f"ComfyUI not reachable at {server} ({e}); start <GENAI_HOME>\\launch.ps1")

    image_name = upload_image(server, args.image) if args.image else None
    changes = apply_inputs(wf, image_name, args.image_node, args.seed, args.set)
    req = urllib.request.Request(server + "/prompt", data=json.dumps(
        {"prompt": wf, "client_id": uuid.uuid4().hex}).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            prompt_id = json.loads(r.read())["prompt_id"]
    except urllib.error.HTTPError as e:
        sys.exit(f"ComfyUI rejected the workflow: {e.read().decode(errors='replace')[:2000]}")
    print(f"queued {prompt_id}; " + "; ".join(changes))

    t0 = time.time()
    while True:
        hist = json.loads(_get(server, f"/history/{prompt_id}"))
        entry = hist.get(prompt_id)
        if entry:  # ComfyUI records history only after execution finished or failed
            break
        if time.time() - t0 > args.timeout:
            sys.exit(f"timeout after {args.timeout:.0f} s")
        time.sleep(3)
    status = entry.get("status", {})
    if status.get("status_str") == "error":
        msgs = [m for m in status.get("messages", []) if m and m[0] == "execution_error"]
        sys.exit(f"execution error: {json.dumps(msgs)[:2000]}")

    args.out.mkdir(parents=True, exist_ok=True)
    files = collect_files(entry.get("outputs", {}), args.all_files)
    if not files:
        sys.exit("no mesh output found in /history (does the workflow end in a Save3D/SaveGLB node?)")
    written = []
    for f in files:
        q = urllib.parse.urlencode(f)
        dest = args.out / Path(f["filename"]).name
        dest.write_bytes(_get(server, f"/view?{q}", 600))
        written.append({"file": dest.name, "sha256": sha256(dest)})
        print(f"wrote {dest}")
    prov = {
        "tool": "genai_comfy_run.py",
        "server_comfyui_version": stats.get("system", {}).get("comfyui_version"),
        "devices": [d.get("name") for d in stats.get("devices", [])],
        "workflow": args.workflow.name, "workflow_sha256": sha256(args.workflow),
        "image": args.image.name if args.image else None,
        "image_sha256": sha256(args.image) if args.image else None,
        "seed": args.seed, "overrides": changes, "prompt_id": prompt_id,
        "seconds": round(time.time() - t0, 1), "outputs": written,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    (args.out / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print(f"done in {prov['seconds']} s -> {args.out / 'provenance.json'}")


if __name__ == "__main__":
    main()
