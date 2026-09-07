"""Verify a source-only Guildrun Korean patch release directory and ZIP."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


TOOL_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TOOL_ROOT.parent
RESOURCE_ROOT = PROJECT_ROOT / "resource"
VERSION = json.loads((RESOURCE_ROOT / "version.json").read_text(encoding="utf-8"))
RELEASE = VERSION["release"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a source-only runtime patch release.")
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT / "artifacts")
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    release = output_root / f"Guildrun-Korean-{RELEASE}"
    executable = release / "GuildrunKoreanPatcher.exe"
    if not executable.is_file():
        raise RuntimeError("Release executable is missing")
    if [path for path in release.rglob("*") if path.is_file()] != [executable]:
        raise RuntimeError("Release directory must contain only GuildrunKoreanPatcher.exe")

    archive = output_root / f"{release.name}.zip"
    with zipfile.ZipFile(archive) as zip_file:
        if zip_file.testzip() is not None:
            raise RuntimeError("Release ZIP is corrupted")
        names = [item.filename for item in zip_file.infolist() if not item.is_dir()]
        if names != [executable.name] or hashlib.sha256(zip_file.read(executable.name)).digest() != hashlib.sha256(executable.read_bytes()).digest():
            raise RuntimeError("Release ZIP must contain only the runtime executable")
    print(json.dumps({"runtime_executable": True, "single_executable_release": True, "archive_verified": True}, indent=2))


if __name__ == "__main__":
    main()
