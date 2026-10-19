---
name: local-3d-genai-meshgen
description: Ask whether to use local image-to-3D models (TRELLIS.2/Pixal3D via ComfyUI) for organic seed meshes, probe hardware, install them on approval, run and post-process them into validated STL seeds; otherwise continue on the Gemini-assisted route.
---

# Local 3D GenAI mesh generation

Image-to-3D models can turn a reference photo into a rough organic mesh in
minutes. In this repo such a mesh is only a **seed** for organic or visual
regions (creatures, figurines, ornaments, sculpted shells). It is never the
source of fit-critical geometry and never a finished print.

Concepts adapted from the 3DGenStudio pipeline (Images -> Image edit -> Mesh
generation -> Mesh edit, with parent/child lineage, a managed ComfyUI with
separated code/model folders, pinned versions and post-install import checks).
No 3DGenStudio code or workflow files are copied; its license forbids
redistribution. The runnable workflows are the official MIT Comfy-Org templates.

## When this skill applies

Run the decision gate when **all** hold:

- `research-reusable-3d-assets` found no adequate license-compatible asset, or only a
  reference-only one (`asset_strategy = reference-only | rebuild`);
- the region is organic/visual (`modeling_route = blender | hybrid`);
- a usable reference image exists or can be produced.

Skip it for technical, dimensional or fit-critical parts; route those to Python.

## Decision gate (ask once per task, record `genai_route`)

1. Run the hardware probe and read the recommendation:

   ```powershell
   .\.venv\Scripts\python.exe scripts\genai_hw_probe.py
   ```

2. Ask the user exactly one question with `ask_user`, putting the probe's verdict
   first, for example:
   "Should I use local 3D generation models (TRELLIS.2/Pixal3D) for the organic seed mesh?"
   - `Yes, use local models (Recommended: <tier>, ~<download> GB download)` when the probe route is `local`
   - `No, continue with the Gemini route` (mark as recommended when the probe route is `gemini`)
3. Record `genai_route = local | gemini` and the probe tier in the interview outcome.
   Do not ask again in the same task unless the hardware or the user's answer changes.
   If the models are already installed (`<GENAI_HOME>\genai-install.json` exists),
   skip the install section.

## Hardware tiers (source of truth: `scripts/genai_catalog.py`)

| Tier | Typical hardware | Packs / precision | Launch args | Download |
| --- | --- | --- | --- | --- |
| `nvidia-24gb` | RTX 3090/4090/5090, >= 22 GB VRAM | single-view + multi-view, bf16 | - | ~35 GB |
| `nvidia-12gb` | RTX 3060 12 GB, 4070 Ti, 4080, 5070 Ti | single-view + multi-view, int8_convrot | - | ~19 GB |
| `nvidia-8gb` | RTX 3070/4060/4070 Laptop, 8 GB | single-view, int8_convrot (experimental) | `--disable-smart-memory --cache-none` | ~14 GB |
| none -> Gemini | < 7.5 GB VRAM, AMD, Intel, Apple Silicon, CPU-only | - | - | - |

Additional requirements: NVIDIA driver with CUDA >= 12.6 (torch wheels cu126,
cu128 or cu130 are chosen from the driver), >= 16 GB RAM (32 GB recommended),
and free disk for models plus ~12 GB Python environment and ~10 GB headroom.
AMD ROCm, Apple MPS and CPU are not offered: the native TRELLIS.2/Pixal3D nodes
are CUDA-targeted, and CPU generation is impractically slow. Suggest the Gemini
route there, or a cloud GPU only if the user asks.

## Models (all MIT, official Comfy-Org repackages)

| Model | Use | Folder |
| --- | --- | --- |
| TRELLIS.2 (Microsoft) | single-image -> 3D shape + texture | `diffusion_models` |
| Pixal3D (TencentARC) | pixel-aligned single- and multi-view -> 3D | `diffusion_models` |
| TRELLIS.2 shape/texture VAEs | decoding | `vae` |
| DINOv3-L NAF | image conditioning | `clip_vision` |
| MoGe-2 | geometry/FOV estimation for Pixal3D | `geometry_estimation` |
| BiRefNet | background removal before generation | `background_removal` |

Excluded: **Hunyuan3D 2.x** (the Tencent community license excludes the EU, UK
and South Korea; reference-only for this repo) and gated **RMBG-2.0** (use
BiRefNet). TripoSG (MIT) and Step1X-3D (Apache-2.0) are acceptable alternatives
only through an audited ComfyUI custom node; do not install unreviewed custom
nodes. Re-check model licenses on Hugging Face before adding anything to the
catalog.

## Install (route `local`, after explicit approval)

Installing downloads tens of GB and runs third-party code. The `ask_user` "Yes"
answer above is approval for this install plan; show the dry-run plan first.

```powershell
.\.venv\Scripts\python.exe scripts\genai_local_setup.py          # plan only
.\.venv\Scripts\python.exe scripts\genai_local_setup.py --yes    # execute
```

The script installs outside the git checkout (`%LOCALAPPDATA%\3d-printing-genai`
or `$GENAI_HOME`): pinned ComfyUI tag, isolated venv with CUDA torch from the
matching PyTorch index, ComfyUI requirements, a CUDA import check, resumable
size-checked model downloads from an allowlist of `huggingface.co/Comfy-Org/`
URLs, the official templates and `launch.ps1`/`launch.sh` bound to
`127.0.0.1` on the first free port from 8188. Models live in `data/` via
`--base-directory`, so reinstalling ComfyUI never re-downloads them.
ComfyUI-Manager is deliberately not installed because it can upgrade packages
and break the pinned environment. Overrides: `--packs`, `--precision`,
`--torch-index`, `--python`, `--only <steps>`, `--root`. Run the long install in
an async shell and report progress at phase boundaries.

If any step fails, report the exact failing command and log lines, then offer
the Gemini route instead of improvising unpinned installs.

## Generate

1. **Prepare the image.** Pick the clearest contact-sheet tile(s). Crop to the
   object, square it, light background. The templates remove the background with
   BiRefNet; check the mask preview. Prefer the multi-view pack when 2-4 consistent
   views (front/side/back) exist; single-view invents the hidden side.
2. **Start ComfyUI** with `<GENAI_HOME>\launch.ps1` (async/detached shell).
3. **Export API workflows once.** Open the template from `<GENAI_HOME>\workflows`,
   check that all models resolve, then use File > Export (API) into
   `<GENAI_HOME>\workflows\api\`. UI-format JSON cannot be queued.
4. **Run** with a fixed seed and record every override:

   ```powershell
   .\.venv\Scripts\python.exe scripts\genai_comfy_run.py --workflow <api.json> --image build\genai\ref.png --seed 42 --out build\genai\<name>-run1
   ```

   `--set NODE.INPUT=VALUE` changes resolution, steps or model file names
   (for example the bf16 weights). `COMFYUI_URL` overrides the server URL. The
   script writes `provenance.json` with hashes, seed, server version and outputs.
5. Generate 2-4 seeds or views and choose by render-compare against the reference
   (`stl-from-image-measurements`), not by the ComfyUI preview.

## Post-process into a print seed

```powershell
.\.venv\Scripts\python.exe scripts\genai_mesh_postprocess.py build\genai\<run>\<mesh>.glb build\genai\<name>-seed.stl --height <mm> --faces 200000 --report build\genai\<name>-seed.json
.\.venv\Scripts\python.exe scripts\mesh_tool.py validate build\genai\<name>-seed.stl
```

The script converts glTF Y-up to Z-up, removes floater shells, scales to the
measured/cited size, repairs or voxel-remeshes (with Taubin smoothing) to a
watertight solid, fuses shells with manifold3d, decimates while staying
watertight, places it on the bed and exports ASCII STL. Textures are dropped;
color regions come from separate bodies (`multimaterial-assembly-packaging`).
Raise `--resolution` for fine detail; use `--voxel` to force removal of internal
faces.

Then continue in `blender-assisted-modeling` (sculpt cleanup, retopology,
merging with frozen Python datums, color-body separation) and the normal
validation, packaging and OrcaSlicer gates. Generated detail must still meet
nozzle/layer limits and must not add supports versus a matched control.

## Provenance and lineage (mandatory)

Record in the model's `docs/` source/measurement note: route `local`, model and
precision, template, ComfyUI version, seed, input image (tile number),
`provenance.json` hash, post-process report and the chosen candidate. Treat the
seed like a licensed asset: MIT models impose no output restriction, but note the
model license. Keep large GLBs and runs under `build/` (ignored); commit only the
parametric/Blender source, the final STL/3MF and docs.

## Gemini route (`genai_route = gemini`)

Continue without local generators, using Gemini models for multimodal reasoning
via subagents (`task` with `model: "gemini-4-argon"` for detailed image analysis
and code generation, `gemini-3.8-flash` for quick tile triage):

- read contact-sheet tiles, extract landmarks, proportions, symmetry and the
  silhouette per view (`image-relief-vectorize`, `visual-hull-envelope-fit`);
- draft Blender Python or build123d code for the organic region from those
  landmarks, then run it locally and validate with repo tools;
- critique render-compare images against the reference and propose bounded,
  parameter-level corrections (`photo-anchor-candidate-fit`).

Only send the user's task images to the subagent. Gemini output is a proposal:
dimensions still come from measurements or cited specs, and every mesh is
produced by repo scripts or Blender and validated like any other.

## Completion checklist

- `genai_route` asked once and recorded with the probe tier.
- Install happened only after approval, outside git, with pinned versions.
- Only catalog (MIT) models used; no Hunyuan3D for EU users.
- Seed mesh scaled from measurements, post-processed, `mesh_tool.py validate` PASS.
- Fit-critical datums untouched by generated geometry.
- Provenance recorded in `docs/`.

## Sources

- 3DGenStudio (concept inspiration only, Community License, no code reused):
  https://github.com/visualbruno/3DGenStudio
- ComfyUI: https://github.com/comfyanonymous/ComfyUI
- Official workflow templates (MIT): https://github.com/Comfy-Org/workflow_templates
- Models: https://huggingface.co/Comfy-Org/TRELLIS.2,
  https://huggingface.co/Comfy-Org/Pixal3D, https://huggingface.co/Comfy-Org/MoGe,
  https://huggingface.co/Comfy-Org/BiRefNet, https://huggingface.co/microsoft/TRELLIS.2-4B
