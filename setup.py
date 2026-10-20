"""Include agent/viewer resources in wheels without duplicating their sources."""

from pathlib import Path
from setuptools import setup

root = Path(__file__).parent
files = [
    path for directory in (".github/skills", ".github/extensions", ".vscode", "tools")
    for path in (root / directory).rglob("*") if path.is_file()
]
files += [root / "docs" / name for name in (
    "mcp-setup.md", "local-3d-genai-setup.md", "orcaslicer-mcp-recherche.md",
)]
files.append(root / "scripts" / "setup_orcaslicer_mcp.ps1")
groups = {}
for path in files:
    relative = path.relative_to(root)
    destination = (Path("share/3d-printing") / relative.parent).as_posix()
    groups.setdefault(destination, []).append(relative.as_posix())
setup(data_files=list(groups.items()))
