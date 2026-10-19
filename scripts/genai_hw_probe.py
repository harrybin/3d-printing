"""Probe local hardware and recommend a local 3D GenAI tier or the Gemini route.

Stdlib only. Prints a human summary, or JSON with --json.

    .venv\\Scripts\\python.exe scripts\\genai_hw_probe.py
    .venv\\Scripts\\python.exe scripts\\genai_hw_probe.py --json
"""
from __future__ import annotations

import argparse
import ctypes
import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import genai_catalog as cat  # noqa: E402

MIN_RAM_GB = 16.0
REC_RAM_GB = 30.0  # "32 GB" machines report ~31.6 GB usable


def _run(cmd: list[str]) -> str | None:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def nvidia_gpus() -> tuple[list[dict], tuple[int, int] | None]:
    out = _run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"])
    gpus: list[dict] = []
    for line in (out or "").splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3 and parts[1].replace(".", "").isdigit():
            gpus.append({"vendor": "nvidia", "name": parts[0], "vram_gb": round(float(parts[1]) / 1024, 1),
                         "driver": parts[2]})
    cuda = None
    header = _run(["nvidia-smi"]) if gpus else None
    m = re.search(r"CUDA(?:\s+\w+)?\s+Version:\s*(\d+)\.(\d+)", header or "")
    if m:
        cuda = (int(m.group(1)), int(m.group(2)))
    return gpus, cuda


def other_gpus() -> list[dict]:
    found: list[dict] = []
    if shutil.which("rocm-smi"):
        found.append({"vendor": "amd", "name": "ROCm device", "vram_gb": None})
    if sys.platform == "darwin" and platform.machine() == "arm64":
        found.append({"vendor": "apple", "name": "Apple Silicon (MPS)", "vram_gb": None})
    if sys.platform == "win32" and not found:
        out = _run(["powershell", "-NoProfile", "-Command",
                    "(Get-CimInstance Win32_VideoController).Name"])
        for name in (out or "").splitlines():
            name = name.strip()
            if name and "nvidia" not in name.lower():
                vendor = "amd" if ("amd" in name.lower() or "radeon" in name.lower()) else \
                    "intel" if "intel" in name.lower() else "other"
                found.append({"vendor": vendor, "name": name, "vram_gb": None})
    return found


def ram_gb() -> float | None:
    if sys.platform == "win32":
        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        ms = MS()
        ms.dwLength = ctypes.sizeof(MS)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
            return round(ms.ullTotalPhys / 1024 ** 3, 1)
        return None
    try:
        text = Path("/proc/meminfo").read_text()
        kb = int(re.search(r"MemTotal:\s+(\d+)", text).group(1))
        return round(kb / 1024 ** 2, 1)
    except (OSError, AttributeError):
        out = _run(["sysctl", "-n", "hw.memsize"])
        return round(int(out) / 1024 ** 3, 1) if out and out.strip().isdigit() else None


def free_disk_gb(path: Path) -> float | None:
    p = path
    while not p.exists() and p.parent != p:
        p = p.parent
    try:
        return round(shutil.disk_usage(p).free / 1024 ** 3, 1)
    except OSError:
        return None


def recommend(gpus: list[dict], cuda: tuple[int, int] | None, ram: float | None, disk: float | None,
              others: list[dict] | None = None) -> dict:
    """Pure decision function (unit-tested)."""
    reasons: list[str] = []
    best = max(gpus, key=lambda g: g["vram_gb"], default=None)
    tier = None
    if best is None:
        vendors = sorted({g["vendor"] for g in (others or [])})
        reasons.append("no NVIDIA/CUDA GPU found" + (f" (found: {', '.join(vendors)})" if vendors else "")
                       + "; native TRELLIS.2/Pixal3D need CUDA")
    else:
        tier = next((t for t in cat.TIERS if best["vram_gb"] >= t["min_vram"]), None)
        if tier is None:
            reasons.append(f"{best['name']} has {best['vram_gb']} GB VRAM, below the 7.5 GB minimum")
    torch_index = cat.torch_index_for_cuda(cuda)
    if tier and torch_index is None:
        reasons.append(f"driver CUDA {cuda} is older than 12.6; update the NVIDIA driver first")
    if ram is not None and ram < MIN_RAM_GB:
        reasons.append(f"{ram} GB system RAM is below the {MIN_RAM_GB:.0f} GB minimum")
    keys = cat.pack_models(tier["packs"], tier["precision"]) if tier else []
    need = round(cat.download_gb(keys) + cat.ENV_OVERHEAD_GB + cat.WORK_HEADROOM_GB, 1) if tier else 0.0
    if tier and disk is not None and disk < need:
        reasons.append(f"only {disk} GB free disk, need about {need} GB")
    route = "local" if tier and not reasons else "gemini"
    warnings: list[str] = []
    if ram is not None and MIN_RAM_GB <= ram < REC_RAM_GB:
        warnings.append(f"{ram} GB RAM works but 32 GB is recommended for model offloading")
    if tier and tier["id"] == "nvidia-8gb":
        warnings.append(tier["note"])
    return {
        "route": route,
        "tier": tier["id"] if tier else None,
        "gpu": best,
        "cuda_driver": f"{cuda[0]}.{cuda[1]}" if cuda else None,
        "torch_index": torch_index,
        "packs": tier["packs"] if tier else [],
        "precision": tier["precision"] if tier else None,
        "launch_args": tier["launch_args"] if tier else [],
        "models": keys,
        "download_gb": cat.download_gb(keys),
        "disk_needed_gb": need,
        "reasons_against_local": reasons,
        "warnings": warnings,
    }


def probe() -> dict:
    gpus, cuda = nvidia_gpus()
    others = [] if gpus else other_gpus()
    home = cat.default_home()
    ram = ram_gb()
    disk = free_disk_gb(home)
    rec = recommend(gpus, cuda, ram, disk, others)
    return {"os": f"{platform.system()} {platform.release()} {platform.machine()}",
            "python": platform.python_version(), "ram_gb": ram, "install_root": str(home),
            "free_disk_gb": disk, "gpus": gpus + others, **rec}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    r = probe()
    if args.json:
        print(json.dumps(r, indent=2))
        return
    print(f"OS            {r['os']}   RAM {r['ram_gb']} GB")
    for g in r["gpus"]:
        print(f"GPU           {g['vendor']}: {g['name']}  VRAM {g.get('vram_gb')} GB")
    print(f"CUDA (driver) {r['cuda_driver']}   torch index {r['torch_index']}")
    print(f"install root  {r['install_root']}  (free {r['free_disk_gb']} GB)")
    print(f"ROUTE         {r['route'].upper()}   tier {r['tier']}")
    if r["tier"]:
        print(f"  packs {r['packs']}  precision {r['precision']}  launch {r['launch_args']}")
        print(f"  download {r['download_gb']} GB, disk needed ~{r['disk_needed_gb']} GB")
    for w in r["reasons_against_local"]:
        print(f"  against local: {w}")
    for w in r["warnings"]:
        print(f"  WARN {w}")


if __name__ == "__main__":
    main()
