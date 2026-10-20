"""Include agent/viewer resources in wheels without duplicating their sources."""

from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).parent
files = [
    path for directory in (".github/skills", ".github/extensions", ".vscode", "tools")
    for path in (root / directory).rglob("*") if path.is_file()
]
files += [root / "docs" / name for name in (
    "mcp-setup.md", "local-3d-genai-setup.md", "orcaslicer-mcp-recherche.md",
)]
files.append(root / "scripts" / "setup_orcaslicer_mcp.ps1")

class BuildPy(build_py):
    def run(self):
        super().run()
        # A single bundle avoids MAX_PATH failures in pip's Windows build tree.
        bundle = Path(self.build_lib) / "printforge" / "resources.zip"
        with ZipFile(bundle, "w", compression=ZIP_DEFLATED) as archive:
            for path in files:
                archive.write(path, path.relative_to(root).as_posix())


setup(cmdclass={"build_py": BuildPy})
