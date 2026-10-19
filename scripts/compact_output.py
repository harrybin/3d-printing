"""Keep full evidence on disk and return bounded, failure-aware tool summaries."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile


def summarize(text: str, limit: int = 12, tail: int = 8) -> dict:
    lines = text.splitlines()
    diagnostics = Counter(
        line.strip() for line in lines
        if re.search(r"\b(warn(?:ing)?|error|fatal|fail(?:ed|ure)?|traceback|exception)\b",
                     line, re.IGNORECASE)
    )
    results = [
        line.strip() for line in lines
        if re.search(r"^(?:Ran \d+ tests|OK$|FAILED|.*\b(?:passed|failed)\b|"
                     r".*(?:exit=|watertight|winding|degenerate|estimated printing time|"
                     r"filament used|total estimated time))", line, re.IGNORECASE)
    ]
    return {
        "lines": len(lines),
        "diagnosticOccurrences": sum(diagnostics.values()),
        "diagnostics": [{"text": line[:600], "count": count}
                        for line, count in diagnostics.most_common(limit)],
        "omittedDiagnosticKinds": max(0, len(diagnostics) - limit),
        "truncatedDiagnosticKinds": sum(len(line) > 600 for line in diagnostics),
        "results": [line[:600] for line in results[-limit:]],
        "tail": [line[:600] for line in lines[-tail:]] if tail else [],
        "notice": "Heuristic summary, not validation. Inspect full logs for unknown or omitted diagnostics.",
    }


def project_summary(path: Path) -> dict:
    with ZipFile(path) as archive:
        settings = json.loads(archive.read("Metadata/project_settings.config"))
        config = ET.fromstring(archive.read("Metadata/model_settings.config"))
        plates = []
        for plate in config.findall("plate"):
            metadata = {entry.get("key"): entry.get("value")
                        for entry in plate.findall("metadata")}
            plates.append({
                "id": metadata.get("plater_id"),
                "objects": len(plate.findall("model_instance")),
            })
        return {
            "path": str(path), "plates": plates,
            "objectCount": len(config.findall("object")),
            "settings": {key: settings.get(key) for key in (
                "filament_colour", "filament_settings_id", "printer_settings_id",
                "curr_bed_type", "layer_height", "seam_position",
                "ironing_type", "enable_support", "support_type",
                "support_top_z_distance", "support_bottom_z_distance")},
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    for name in ("log", "run"):
        command = commands.add_parser(name)
        command.add_argument("--limit", type=int, default=12)
        command.add_argument("--tail", type=int, default=8)
        if name == "log":
            command.add_argument("path", type=Path)
        else:
            command.add_argument("--log", type=Path, required=True)
            command.add_argument("command", nargs=argparse.REMAINDER)
    project = commands.add_parser("project")
    project.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    if args.action == "project":
        print(json.dumps(project_summary(args.path), ensure_ascii=True, indent=2))
        return 0
    if args.limit < 1 or args.tail < 0:
        parser.error("--limit must be positive and --tail nonnegative")
    exit_code = None
    if args.action == "run":
        command = args.command[1:] if args.command[:1] == ["--"] else args.command
        if not command:
            parser.error("run requires a command after --")
        args.log.parent.mkdir(parents=True, exist_ok=True)
        with args.log.open("wb") as output:
            # Stream to disk, not an unbounded in-memory capture.
            exit_code = subprocess.run(command, stdout=output,
                                       stderr=subprocess.STDOUT, check=False).returncode
        path = args.log
    else:
        path = args.path
    report = summarize(path.read_text(encoding="utf-8", errors="replace"),
                       args.limit, args.tail)
    report.update({"fullLog": str(path.resolve()), "exitCode": exit_code})
    print(json.dumps(report, ensure_ascii=True, indent=2))
    # A log-only summary cannot certify command success.
    return exit_code if exit_code is not None else 0


if __name__ == "__main__":
    sys.exit(main())
