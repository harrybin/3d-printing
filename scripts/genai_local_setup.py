"""Install the optional local ComfyUI + 3D mesh-generation models (dry run by default).

Installs outside the git checkout (default %LOCALAPPDATA%\\3d-printing-genai or
$GENAI_HOME):
    <root>/ComfyUI   pinned ComfyUI code (git tag)       - reinstallable
    <root>/venv      isolated Python env with CUDA torch  - reinstallable
    <root>/data      --base-directory: models, input, output (kept on reinstall)
    <root>/workflows official MIT Comfy-Org templates (UI format)
    <root>/launch.ps1 / launch.sh

    .venv\\Scripts\\python.exe scripts\\genai_local_setup.py            # plan only
    .venv\\Scripts\\python.exe scripts\\genai_local_setup.py --yes      # execute
    .venv\\Scripts\\python.exe scripts\\genai_local_setup.py --yes --only models --packs multi-view

ComfyUI-Manager is deliberately not installed: it can upgrade packages and break
the pinned environment. Only official Comfy-Org Hugging Face files are downloaded.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import genai_catalog as cat  # noqa: E402
import genai_hw_probe as hw  # noqa: E402

STEPS = ("comfy", "venv", "torch", "deps", "models", "templates", "launcher")


def free_port(start: int = cat.COMFYUI_DEFAULT_PORT, span: int = 50) -> int:
    for port in range(start, start + span):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise SystemExit(f"no free port in {start}..{start + span - 1}")


def find_python(explicit: str | None) -> list[str]:
    if explicit:
        return [explicit]
    if sys.platform == "win32" and shutil.which("py"):
        for ver in ("3.13", "3.12"):
            if subprocess.run(["py", f"-{ver}", "-c", "pass"], capture_output=True).returncode == 0:
                return ["py", f"-{ver}"]
    for exe in ("python3.13", "python3.12"):
        if shutil.which(exe):
            return [exe]
    return [sys.executable]


def venv_python(root: Path) -> Path:
    return root / "venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def run(cmd: list, execute: bool, cwd: Path | None = None) -> None:
    print("  $ " + " ".join(str(c) for c in cmd))
    if execute:
        subprocess.run([str(c) for c in cmd], check=True, cwd=cwd)


def download(url: str, dest: Path, execute: bool) -> None:
    if not url.startswith(cat.ALLOWED_DOWNLOAD_PREFIXES):
        raise SystemExit(f"refusing non-allowlisted download: {url}")
    print(f"  GET {url}\n      -> {dest}")
    if not execute:
        return
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        total = int(r.headers.get("Content-Length") or 0)
    if dest.exists() and total and dest.stat().st_size == total:
        print("      already complete")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    have = part.stat().st_size if part.exists() else 0
    req = urllib.request.Request(url, headers={"Range": f"bytes={have}-"} if have else {})
    with urllib.request.urlopen(req, timeout=60) as r, open(part, "ab" if have else "wb") as f:
        if have and r.status != 206:
            f.truncate(0)
            have = 0
        done, last = have, time.time()
        while chunk := r.read(8 << 20):
            f.write(chunk)
            done += len(chunk)
            if time.time() - last > 10:
                print(f"      {done / 1024 ** 3:.2f} / {total / 1024 ** 3:.2f} GB", flush=True)
                last = time.time()
    if total and part.stat().st_size != total:
        raise SystemExit(f"size mismatch for {dest.name}: {part.stat().st_size} != {total}; rerun to resume")
    part.replace(dest)


def template_models(template_json: dict) -> list[tuple[str, str, str]]:
    """(name, directory, url) entries declared by an official UI-format template."""
    nodes = list(template_json.get("nodes", []))
    for sg in template_json.get("definitions", {}).get("subgraphs", []):
        nodes += sg.get("nodes", [])
    seen, out = set(), []
    for n in nodes:
        for m in (n.get("properties") or {}).get("models") or []:
            key = (m.get("name"), m.get("directory"), m.get("url"))
            if all(key) and key not in seen:
                seen.add(key)
                out.append(key)
    return out


def write_launchers(root: Path, port: int, launch_args: list[str], execute: bool) -> None:
    args = ["--base-directory", str(root / "data"), "--listen", "127.0.0.1", "--port", str(port), *launch_args]
    ps1 = f'& "{venv_python(root)}" "{root / "ComfyUI" / "main.py"}" ' + " ".join(f'"{a}"' for a in args) + "\n"
    sh = "#!/usr/bin/env sh\n" + f'exec "{venv_python(root)}" "{root / "ComfyUI" / "main.py"}" ' + \
        " ".join(f'"{a}"' for a in args) + "\n"
    print(f"  write {root / 'launch.ps1'} / launch.sh  (http://127.0.0.1:{port})")
    if execute:
        (root / "launch.ps1").write_text(ps1, encoding="utf-8")
        (root / "launch.sh").write_text(sh, encoding="utf-8")
        (root / "genai-install.json").write_text(json.dumps(
            {"comfyui_tag": cat.COMFYUI_TAG, "url": f"http://127.0.0.1:{port}", "launch_args": args}, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--yes", action="store_true", help="execute; without it only the plan is printed")
    ap.add_argument("--root", type=Path, default=cat.default_home())
    ap.add_argument("--packs", nargs="+", choices=sorted(cat.PACKS), help="override tier packs")
    ap.add_argument("--precision", choices=("int8", "bf16"), help="override tier precision")
    ap.add_argument("--torch-index", help="override, e.g. cu128 or cpu (cpu is not usable for generation)")
    ap.add_argument("--python", help="interpreter for the ComfyUI venv (default: py 3.13/3.12)")
    ap.add_argument("--only", nargs="+", choices=STEPS, help="run only these steps")
    ap.add_argument("--force", action="store_true", help="install even if the probe recommends Gemini")
    args = ap.parse_args()

    p = hw.probe()
    if p["route"] != "local" and not args.force:
        print("Probe recommends the Gemini route:")
        for r in p["reasons_against_local"]:
            print(f"  - {r}")
        raise SystemExit("not installing (pass --force to override against the recommendation)")
    tier = next((t for t in cat.TIERS if t["id"] == p["tier"]), cat.TIERS[-1])
    packs = args.packs or tier["packs"]
    precision = args.precision or tier["precision"]
    torch_index = args.torch_index or p["torch_index"]
    if not torch_index:
        raise SystemExit("no matching CUDA torch build; update the NVIDIA driver or pass --torch-index")
    keys = cat.pack_models(packs, precision)
    root: Path = args.root.resolve()
    repo_root = Path(__file__).resolve().parents[1]
    if root == repo_root or repo_root in root.parents:
        raise SystemExit("install root must be outside the git checkout")
    steps = set(args.only or STEPS)
    ex = args.yes

    print(f"{'EXECUTE' if ex else 'DRY RUN (add --yes to execute)'}: tier {p['tier']} on "
          f"{(p['gpu'] or {}).get('name')}, packs {packs}, precision {precision}, torch {torch_index}")
    print(f"root {root}; downloads ~{cat.download_gb(keys)} GB models + ~{cat.ENV_OVERHEAD_GB:.0f} GB env")
    print("licenses: " + ", ".join(sorted({f'{cat.MODELS[k][0]} ({cat.MODELS[k][4]})' for k in keys})))
    py = venv_python(root)
    comfy = root / "ComfyUI"

    if "comfy" in steps:
        print(f"[comfy] ComfyUI {cat.COMFYUI_TAG}")
        if (comfy / ".git").exists():
            run(["git", "-C", comfy, "fetch", "--depth", "1", "origin", "tag", cat.COMFYUI_TAG], ex)
            run(["git", "-C", comfy, "checkout", "--force", cat.COMFYUI_TAG], ex)
        else:
            if ex:
                root.mkdir(parents=True, exist_ok=True)
            run(["git", "clone", "--depth", "1", "--branch", cat.COMFYUI_TAG, cat.COMFYUI_REPO, comfy], ex)
    if "venv" in steps:
        print("[venv]")
        if not py.exists():
            run([*find_python(args.python), "-m", "venv", root / "venv"], ex)
        run([py, "-m", "pip", "install", "-q", "--upgrade", "pip"], ex)
    if "torch" in steps:
        print(f"[torch] {torch_index}")
        run([py, "-m", "pip", "install", "-q", "torch", "torchvision", "torchaudio",
             "--index-url", f"https://download.pytorch.org/whl/{torch_index}"], ex)
    if "deps" in steps:
        print("[deps] ComfyUI requirements (torch kept from the CUDA index)")
        run([py, "-m", "pip", "install", "-q", "-r", comfy / "requirements.txt"], ex)
        run([py, "-c", "import torch;assert torch.cuda.is_available(), 'CUDA torch missing';"
             "print('torch', torch.__version__, torch.cuda.get_device_name(0))"], ex)
    templates: dict[str, dict] = {}
    if "templates" in steps or "models" in steps:
        print("[templates] official Comfy-Org workflow templates (MIT)")
        for pack in packs:
            name = cat.PACKS[pack]["template"]
            url = cat.TEMPLATE_RAW.format(name=name)
            print(f"  GET {url}")
            if ex:
                with urllib.request.urlopen(url, timeout=60) as r:
                    raw = r.read()
                templates[name] = json.loads(raw.decode("utf-8-sig"))
                out = root / "workflows" / f"{name}.json"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(raw)
    if "models" in steps:
        print("[models]")
        planned = {(cat.MODELS[k][2], Path(cat.MODELS[k][1]).name): cat.model_url(k) for k in keys}
        for name, tpl in templates.items():
            for fname, directory, url in template_models(tpl):
                if (directory, fname) not in planned and precision == "int8":
                    print(f"  note: template {name} also needs {directory}/{fname}")
                    planned[(directory, fname)] = url
        for (directory, fname), url in planned.items():
            download(url, root / "data" / "models" / directory / fname, ex)
    if "launcher" in steps:
        print("[launcher]")
        write_launchers(root, free_port(), tier["launch_args"], ex)
    print("next: start ComfyUI with launch.ps1, open each template, File > Export (API) to "
          f"{root / 'workflows' / 'api'}, then use scripts/genai_comfy_run.py")


if __name__ == "__main__":
    main()
