"""Shared catalog for the optional local 3D GenAI (image-to-mesh) toolchain.

Only permissively licensed, non-gated model files from the official Comfy-Org
Hugging Face repackages are listed here. Hunyuan3D is intentionally absent: its
Tencent community license excludes the EU, UK and South Korea.

Consumed by genai_hw_probe.py, genai_local_setup.py and the
local-3d-genai-meshgen skill. Keep the skill's tier table in sync.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

COMFYUI_REPO = "https://github.com/comfyanonymous/ComfyUI.git"
COMFYUI_TAG = "v0.42.1"
COMFYUI_DEFAULT_PORT = 8188
TEMPLATE_RAW = "https://raw.githubusercontent.com/Comfy-Org/workflow_templates/main/templates/{name}.json"
HF = "https://huggingface.co/{repo}/resolve/main/{path}"
ALLOWED_DOWNLOAD_PREFIXES = ("https://huggingface.co/Comfy-Org/",)

# file key -> (hf repo, path inside repo, ComfyUI models subfolder, size GB, license)
MODELS: dict[str, tuple[str, str, str, float, str]] = {
    "trellis2_int8": ("Comfy-Org/TRELLIS.2", "diffusion_models/trellis_2_int8_convrot.safetensors", "diffusion_models", 4.89, "MIT"),
    "trellis2_bf16": ("Comfy-Org/TRELLIS.2", "diffusion_models/trellis_2_bf16.safetensors", "diffusion_models", 9.63, "MIT"),
    "pixal3d_int8": ("Comfy-Org/Pixal3D", "diffusion_models/pixal3d_int8_convrot.safetensors", "diffusion_models", 5.20, "MIT"),
    "pixal3d_bf16": ("Comfy-Org/Pixal3D", "diffusion_models/pixal3d_bf16.safetensors", "diffusion_models", 10.24, "MIT"),
    "pixal3d_mv_int8": ("Comfy-Org/Pixal3D", "diffusion_models/pixal3d_multiview_int8_convrot.safetensors", "diffusion_models", 5.20, "MIT"),
    "pixal3d_mv_bf16": ("Comfy-Org/Pixal3D", "diffusion_models/pixal3d_multiview_bf16.safetensors", "diffusion_models", 10.24, "MIT"),
    "trellis2_shape_vae": ("Comfy-Org/Pixal3D", "vae/trellis_2_shape_vae_bf16.safetensors", "vae", 1.02, "MIT"),
    "trellis2_texture_vae": ("Comfy-Org/Pixal3D", "vae/trellis_2_texture_vae_bf16.safetensors", "vae", 0.88, "MIT"),
    "dino_v3_naf": ("Comfy-Org/Pixal3D", "clip_vision/dino_v3_L_naf_fp32.safetensors", "clip_vision", 1.13, "MIT"),
    "moge2": ("Comfy-Org/MoGe", "geometry_estimation/moge_2_vitl_normal_fp16.safetensors", "geometry_estimation", 0.62, "MIT"),
    "birefnet": ("Comfy-Org/BiRefNet", "background_removal/birefnet.safetensors", "background_removal", 0.41, "MIT"),
}

# pack -> official template name, model keys per precision
PACKS: dict[str, dict] = {
    "single-view": {
        "template": "3d_pixal3d_trellis2_image_to_model",
        "int8": ["pixal3d_int8", "trellis2_int8", "trellis2_shape_vae", "trellis2_texture_vae", "dino_v3_naf", "moge2", "birefnet"],
        "bf16": ["pixal3d_bf16", "trellis2_bf16", "trellis2_shape_vae", "trellis2_texture_vae", "dino_v3_naf", "moge2", "birefnet"],
    },
    "multi-view": {
        "template": "3d_pixal3d_multi_views",
        "int8": ["pixal3d_mv_int8", "trellis2_shape_vae", "trellis2_texture_vae", "dino_v3_naf", "birefnet"],
        "bf16": ["pixal3d_mv_bf16", "trellis2_shape_vae", "trellis2_texture_vae", "dino_v3_naf", "birefnet"],
    },
}

# Python env (torch + ComfyUI deps) and working headroom, GB
ENV_OVERHEAD_GB = 12.0
WORK_HEADROOM_GB = 10.0

# tier id -> recommendation; checked top-down by min VRAM (GB)
TIERS: list[dict] = [
    {"id": "nvidia-24gb", "min_vram": 22.0, "packs": ["single-view", "multi-view"], "precision": "bf16",
     "launch_args": [], "note": "Full-precision TRELLIS.2/Pixal3D; best detail."},
    {"id": "nvidia-12gb", "min_vram": 11.5, "packs": ["single-view", "multi-view"], "precision": "int8",
     "launch_args": [], "note": "int8_convrot weights (template defaults); good quality."},
    {"id": "nvidia-8gb", "min_vram": 7.5, "packs": ["single-view"], "precision": "int8",
     "launch_args": ["--disable-smart-memory", "--cache-none"],
     "note": "Experimental: int8 weights with aggressive offloading (dynamic VRAM), slow; single-view only, "
     "lower the shape resolution if it runs out of memory."},
]


def pack_models(packs: list[str], precision: str) -> list[str]:
    keys: list[str] = []
    for p in packs:
        for k in PACKS[p][precision]:
            if k not in keys:
                keys.append(k)
    return keys


def download_gb(keys: list[str]) -> float:
    return round(sum(MODELS[k][3] for k in keys), 2)


def model_url(key: str) -> str:
    repo, path, *_ = MODELS[key]
    return HF.format(repo=repo, path=path)


def default_home() -> Path:
    """User-local install root outside the git checkout (code, venv, models)."""
    env = os.environ.get("GENAI_HOME")
    if env:
        return Path(env)
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "3d-printing-genai"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "3d-printing-genai"


def torch_index_for_cuda(cuda: tuple[int, int] | None) -> str | None:
    """Pick the PyTorch wheel index the installed driver can run (driver CUDA >= wheel CUDA)."""
    if not cuda:
        return None
    if cuda >= (13, 0):
        return "cu130"
    if cuda >= (12, 8):
        return "cu128"
    if cuda >= (12, 6):
        return "cu126"
    return None
