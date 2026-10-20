"""Engine commands; model sources and generated assets stay in the catalog."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from . import __version__


TOOLS = (
    "compact_output", "fdm_joints", "genai_catalog", "genai_comfy_run",
    "genai_hw_probe", "genai_local_setup", "genai_mesh_postprocess",
    "make_contact_sheet", "mesh_kit", "mesh_tool", "render_3mf_previews",
    "render_gcode_preview", "sdf_blend", "sdf_bones",
)
ENGINE_DOCS = ("mcp-setup.md", "local-3d-genai-setup.md", "orcaslicer-mcp-recherche.md")


def catalog_root(value: str | Path | None = None) -> Path:
    root = Path(value or os.environ.get("CATALOG_ROOT") or Path.cwd()).resolve()
    if not (root / "catalog.json").is_file():
        raise ValueError(f"Not a model catalog (catalog.json missing): {root}")
    return root


def resource_files() -> dict[Path, bytes]:
    bundle = Path(__file__).with_name("resources.zip")
    if bundle.is_file():
        with ZipFile(bundle) as archive:
            return {Path(name): archive.read(name) for name in archive.namelist()}
    source = Path(__file__).resolve().parents[2]
    if (source / ".github" / "skills").is_dir():
        files = [
            path for directory in (".github/skills", ".github/extensions", ".vscode", "tools")
            for path in (source / directory).rglob("*") if path.is_file()
        ]
        files += [source / "docs" / name for name in ENGINE_DOCS]
        files.append(source / "scripts" / "setup_orcaslicer_mcp.ps1")
        return {path.relative_to(source): path.read_bytes() for path in files}
    raise FileNotFoundError("Engine resources missing; reinstall the engine wheel")


def bootstrap(root: Path) -> int:
    """Materialize ignored engine resources without overwriting catalog files."""
    root = root.resolve()
    sources = resource_files()
    for name in TOOLS:
        sources[Path("scripts") / f"{name}.py"] = Path(
            importlib.util.find_spec(name).origin).read_bytes()
    previous_path = root / ".engine-files.json"
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    # Check every target before writing anything; a tracked/user-edited file wins.
    for relative, content in sources.items():
        target = root / relative
        if target.exists() and target.read_bytes() != content:
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            if previous.get(relative.as_posix()) != digest:
                raise ValueError(f"Refusing to overwrite unmanaged/modified file: {target}")
    state = {}
    for relative, content in sources.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        state[relative.as_posix()] = hashlib.sha256(target.read_bytes()).hexdigest()
    previous_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"Engine {__version__}: materialized {len(state)} ignored resources in {root}")
    return 0


def verify_catalog(root: Path, migration: bool = False) -> int:
    root = root.resolve()
    manifest = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported catalog schema_version")
    errors = []
    for relative, digest in (manifest["migration"]["sha256"].items() if migration else []):
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"Path escapes catalog: {relative}")
        if not path.is_file():
            errors.append(f"Missing: {relative}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(f"Changed since migration: {relative}")
    slugs = set()
    outputs = set()
    for model in manifest["models"]:
        if model["slug"] in slugs:
            errors.append(f"Duplicate model: {model['slug']}")
        slugs.add(model["slug"])
        for relative in model["outputs"] + model.get("docs", []):
            path = (root / relative).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                errors.append(f"Invalid model path: {relative}")
        generator = model.get("generator")
        if generator and (not (root / generator).resolve().is_relative_to(root / "scripts")
                          or not (root / generator).is_file()):
            errors.append(f"Invalid generator: {generator}")
        for relative in model["outputs"]:
            if relative in outputs:
                errors.append(f"Duplicate output: {relative}")
            outputs.add(relative)
    actual_outputs = {
        path.relative_to(root).as_posix() for path in (root / "models").iterdir()
        if path.is_file() and path.suffix.lower() in {".stl", ".3mf"}
    }
    if actual_outputs != outputs:
        errors.append(f"Output inventory mismatch: {sorted(actual_outputs ^ outputs)}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Catalog OK: {len(manifest['models'])} models; {len(outputs)} outputs"
          + (f"; {len(manifest['migration']['sha256'])} unchanged migrated assets"
             if migration else ""))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("bootstrap", "verify-catalog"):
        command = commands.add_parser(name)
        command.add_argument("catalog", nargs="?")
        if name == "verify-catalog":
            command.add_argument("--migration", action="store_true",
                                 help="Also verify the immutable migration baseline")
    tool = commands.add_parser("tool", help="Run a reusable engine tool")
    tool.add_argument("name", choices=TOOLS)
    tool.add_argument("arguments", nargs=argparse.REMAINDER)
    run = commands.add_parser("run", help="Run a catalog-owned generator or audit")
    run.add_argument("--catalog", required=True)
    run.add_argument("script")
    run.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.command == "bootstrap":
            return bootstrap(catalog_root(args.catalog))
        if args.command == "verify-catalog":
            return verify_catalog(catalog_root(args.catalog), args.migration)
        if args.command == "tool":
            return subprocess.call([sys.executable, "-m", args.name, *args.arguments])
        root = catalog_root(args.catalog)
        script = (root / args.script).resolve()
        if not script.is_relative_to(root / "scripts") or not script.is_file():
            raise ValueError("Generator must be a file inside catalog/scripts")
        env = {**os.environ, "CATALOG_ROOT": str(root)}
        return subprocess.call([sys.executable, str(script), *args.arguments],
                               cwd=root, env=env)
    except (ValueError, FileNotFoundError) as error:
        parser.exit(2, f"error: {error}\n")
