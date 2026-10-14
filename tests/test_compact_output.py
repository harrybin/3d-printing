import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compact_output import main, project_summary, summarize


class CompactOutputTests(unittest.TestCase):
    def test_deduplicates_and_reports_omitted_diagnostics(self):
        report = summarize("warning: A\nwarning: A\nerror: B\nerror: C\nOK", 1, 1)
        self.assertEqual(report["diagnosticOccurrences"], 4)
        self.assertEqual(report["diagnostics"][0]["count"], 2)
        self.assertEqual(report["omittedDiagnosticKinds"], 2)
        self.assertEqual(report["tail"], ["OK"])

    def test_keeps_full_failure_log_and_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.log"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["run", "--log", str(path), "--", sys.executable,
                             "-c", "print('error: intentional'); raise SystemExit(7)"])
            self.assertEqual(code, 7)
            self.assertIn("error: intentional", path.read_text())
            self.assertEqual(json.loads(output.getvalue())["exitCode"], 7)

    def test_marks_truncated_diagnostics(self):
        report = summarize("error: " + "x" * 1000)
        self.assertEqual(report["truncatedDiagnosticKinds"], 1)
        self.assertEqual(len(report["diagnostics"][0]["text"]), 600)

    def test_project_reports_plate_membership_and_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.3mf"
            with ZipFile(path, "w") as archive:
                archive.writestr("Metadata/project_settings.config",
                                 '{"filament_colour":["#202124"],"enable_support":"1"}')
                archive.writestr("Metadata/model_settings.config",
                                 '<config><object id="1"/><plate>'
                                 '<metadata key="plater_id" value="1"/>'
                                 '<model_instance/></plate></config>')
            report = project_summary(path)
            self.assertEqual(report["plates"], [{"id": "1", "objects": 1}])
            self.assertEqual(report["objectCount"], 1)
            self.assertEqual(report["settings"]["enable_support"], "1")


if __name__ == "__main__":
    unittest.main()
