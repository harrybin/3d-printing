# Local 3D GenAI setup and 3DGenStudio learnings

Optional toolchain for generating **organic seed meshes** from reference images.
The decision flow, install, generation and post-processing are defined in
[`.github/skills/local-3d-genai-meshgen/SKILL.md`](../.github/skills/local-3d-genai-meshgen/SKILL.md).

## Hardware tiers

Source of truth: [`scripts/genai_catalog.py`](../scripts/genai_catalog.py).
`scripts/genai_hw_probe.py` reads `nvidia-smi` (GPU, VRAM, driver CUDA), RAM and
free disk, and recommends a tier or the Gemini route.

| Tier | VRAM | Packs | Precision | Extra launch args | Model download |
| --- | --- | --- | --- | --- | --- |
| `nvidia-24gb` | >= 22 GB | single-view + multi-view | bf16 | - | ~35 GB |
| `nvidia-12gb` | >= 11.5 GB | single-view + multi-view | int8_convrot | - | ~19 GB |
| `nvidia-8gb` | >= 7.5 GB | single-view (experimental) | int8_convrot | `--disable-smart-memory --cache-none` | ~14 GB |
| Gemini route | less, or AMD / Intel / Apple / CPU | - | - | - | - |

Also required: NVIDIA driver with CUDA >= 12.6 (PyTorch index cu126/cu128/cu130 is
picked automatically), >= 16 GB RAM (32 GB recommended), and about 22 GB disk for
the Python environment and working headroom on top of the models.

Example verified on the development laptop (RTX 4070 Laptop 8 GB, driver CUDA
13.3, 32 GB RAM): tier `nvidia-8gb`, torch `cu130`, 14.15 GB model download.

## Install layout

Default root `%LOCALAPPDATA%\3d-printing-genai` (`$GENAI_HOME` overrides), never
inside the repository:

| Path | Content | Reinstall-safe |
| --- | --- | --- |
| `ComfyUI/` | ComfyUI at pinned tag `v0.42.1` | replaceable |
| `venv/` | isolated Python with CUDA torch | replaceable |
| `data/models/...` | model weights (`--base-directory data`) | kept |
| `workflows/` | official templates; `workflows/api/` API exports | kept |
| `launch.ps1`, `launch.sh`, `genai-install.json` | localhost launcher, install record | regenerated |

The server binds to `127.0.0.1` on the first free port from 8188.
`scripts/genai_comfy_run.py` uses `COMFYUI_URL` or that default.

## Model licenses

| Model | License | Status |
| --- | --- | --- |
| TRELLIS.2 (microsoft/TRELLIS.2-4B, Comfy-Org/TRELLIS.2) | MIT | catalog |
| Pixal3D (TencentARC/Pixal3D, Comfy-Org/Pixal3D) | MIT | catalog |
| MoGe-2 (Comfy-Org/MoGe) | MIT | catalog |
| BiRefNet (ZhengPeng7/BiRefNet, Comfy-Org/BiRefNet) | MIT | catalog |
| ComfyUI workflow templates (Comfy-Org/workflow_templates) | MIT | downloaded at install |
| TripoSG (VAST-AI) | MIT | allowed via audited custom node only |
| Step1X-3D (stepfun-ai) | Apache-2.0 | allowed via audited custom node only |
| Hunyuan3D 2.0 / 2.1 / 2mini (Tencent) | Tencent community license, excludes EU, UK, KR | excluded |
| RMBG-2.0 (briaai) | gated, non-commercial | excluded, use BiRefNet |

Licenses were read from the Hugging Face model metadata; re-check before adding
models to the catalog.

## What was adopted from 3DGenStudio

[3DGenStudio](https://github.com/visualbruno/3DGenStudio) orchestrates text/image
-> image edit -> mesh generation -> mesh edit -> texturing pipelines on ComfyUI.
Its Community License permits copying and modification but restricts selling the
software or derivatives, paid hosting/SaaS, and paid bundles. **No code or
workflow files were copied**; only the following concepts were adapted and
reimplemented:

| 3DGenStudio concept | Adopted here as |
| --- | --- |
| Opt-in managed ComfyUI, separate code and model directories (`--base-directory`) | `genai_local_setup.py` install layout |
| Pinned ComfyUI version, CUDA-matched torch installed first, no ComfyUI-Manager | pinned tag, torch index from driver CUDA, Manager excluded |
| Post-install import verification | CUDA torch check in the `deps` step |
| CUDA detection from `nvidia-smi` with CPU fallback | `genai_hw_probe.py` tiers with Gemini fallback instead of a CPU path |
| Model size variants (bf16 vs int8) chosen by VRAM | tier precision bf16 / int8_convrot |
| First free port from 8188 | launcher port selection |
| Background removal before TRELLIS.2 | BiRefNet in the templates; image-prep step in the skill |
| Single-view and multi-view mesh generation | `single-view` and `multi-view` packs |
| Workflow API manifests (node/input mapping) | `genai_comfy_run.py --set NODE.INPUT=VALUE`, API-format check |
| Asset lineage (parent/child versions) | `provenance.json` plus docs provenance requirement |
| Mesh edit: repair, retopology, optimize/LOD | `genai_mesh_postprocess.py` (repair, voxel remesh, decimate), then Blender |
| License acceptance before restricted downloads | MIT allowlist; Hunyuan3D excluded for EU |
| Game-ready budget check | existing print-ready gates (`validate-stl-mesh`, OrcaSlicer) |

Not adopted: texturing, rigging and animation (no FDM value), text-to-image
generation (reference photos come from the user), and the SAM part
segmentation (possible follow-up for color-body splits; colors are currently
separated as keyed bodies in Blender/Python).

## Direct3D-S2 research (Neural4D connection)

The supplied “AI Image to 3D Generator” title matches Neural4D's indexed image
generator page, although the `share.google` redirect itself could not be opened
to confirm the match. Neural4D is a hosted product; the public research project
associated with it is [Direct3D-S2](https://github.com/DreamTechAI/Direct3D-S2),
described in its [NeurIPS 2025 paper](https://arxiv.org/abs/2505.17412). The
paper lists researchers from Nanjing University, Fudan University, Oxford and
DreamTech.

Direct3D-S2 generates a mesh from an image using sparse 3D volumes and Spatial
Sparse Attention. Its code repository and linked
[Hugging Face model](https://huggingface.co/wushuang98/Direct3D-S2) declare MIT
licensing; any reused code must retain the copyright and license notice. The
upstream README reports about 10 GB VRAM for 512³ (lower quality) and 24 GB for
1024³, and tests an Ubuntu/CUDA 12.1/PyTorch 2.5.1 stack with TorchSparse,
FlashAttention and other dependencies. Its attention speedups are not a
measured end-to-end print workflow benchmark.

**Decision: do not add it to the supported ComfyUI packs or install path yet.**
It needs a separate runtime/model integration, while this engine already
supports opt-in image-to-mesh generation, hardware-aware selection, provenance,
and print-specific mesh validation. If evaluated later, keep it isolated from
the managed ComfyUI environment and treat its output only as an organic seed;
validate it through the existing post-processing, mesh, and slicer gates rather
than relying on upstream print-readiness claims. Upstream lists `pymeshfix`,
which must not be used on thin-walled or multi-chamber parts in this repository.

## Gemini route

When the user declines local models or the hardware is unsuitable, agents use
Gemini subagents (`gemini-4-argon` for detailed vision and code, `gemini-3.8-flash`
for quick triage) to read contact-sheet tiles, extract landmarks and
silhouettes, draft Blender/build123d code and critique render comparisons. All
geometry is still produced and validated locally.
