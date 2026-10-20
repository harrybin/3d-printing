import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from printforge.cli import bootstrap, catalog_root, main, verify_catalog


class CatalogTests(unittest.TestCase):
    def make_catalog(self, root):
        (root / "models").mkdir()
        (root / "models" / "part.stl").write_bytes(b"unchanged mesh fixture")
        manifest = {
            "schema_version": 1,
            "models": [{"slug": "part", "outputs": ["models/part.stl"]}],
            "migration": {"sha256": {"models/part.stl": hashlib.sha256(
                b"unchanged mesh fixture").hexdigest()}},
        }
        (root / "catalog.json").write_text(json.dumps(manifest))
        return manifest

    def test_external_catalog_and_missing_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.make_catalog(root)
            with patch.dict(os.environ, {"CATALOG_ROOT": str(root)}):
                self.assertEqual(catalog_root(), root)
            with self.assertRaisesRegex(ValueError, "catalog.json missing"):
                catalog_root(root / "missing")

    def test_integrity_check_and_normal_catalog_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_catalog(root)
            self.assertEqual(verify_catalog(root, migration=True), 0)
            (root / "models" / "part.stl").write_bytes(b"new version")
            with contextlib.redirect_stderr(io.StringIO()) as error:
                self.assertEqual(verify_catalog(root, migration=True), 1)
            self.assertIn("Changed since migration", error.getvalue())
            self.assertEqual(verify_catalog(root), 0)

    def test_output_inventory_catches_unlisted_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_catalog(root)
            (root / "models" / "forgotten.3mf").write_bytes(b"fixture")
            with contextlib.redirect_stderr(io.StringIO()) as error:
                self.assertEqual(verify_catalog(root), 1)
            self.assertIn("forgotten.3mf", error.getvalue())

    def test_manifest_cannot_reference_outside_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.make_catalog(root)
            manifest["migration"]["sha256"] = {"../outside": "0" * 64}
            (root / "catalog.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "escapes catalog"):
                verify_catalog(root, migration=True)

    def test_generator_exit_code_and_catalog_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.make_catalog(root)
            (root / "scripts").mkdir()
            script = root / "scripts" / "probe.py"
            script.write_text("import os, pathlib, sys\n"
                              "assert pathlib.Path.cwd() == pathlib.Path(os.environ['CATALOG_ROOT'])\n"
                              "sys.exit(int(sys.argv[1]))\n")
            self.assertEqual(main(["run", "--catalog", str(root), "scripts/probe.py", "7"]), 7)
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                main(["run", "--catalog", str(root), "../outside.py"])

    def test_bootstrap_ignores_model_files_and_protects_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_catalog(root)
            bootstrap(root)
            self.assertTrue((root / ".github" / "skills" / "README.md").is_file())
            self.assertTrue((root / "scripts" / "mesh_tool.py").is_file())
            self.assertFalse((root / "scripts" / "ghouls_grip.py").exists())
            self.assertEqual((root / "models" / "part.stl").read_bytes(), b"unchanged mesh fixture")
            bootstrap(root)
            (root / "scripts" / "mesh_tool.py").write_text("user edit")
            with self.assertRaisesRegex(ValueError, "unmanaged/modified"):
                bootstrap(root)
