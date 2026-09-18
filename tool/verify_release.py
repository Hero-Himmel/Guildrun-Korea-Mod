"""Verify a source-only Guildrun Korean patch release directory and ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from game_layout import (
    PLATFORM_MACOS,
    PLATFORM_WINDOWS,
    SUPPORTED_PLATFORMS,
    current_platform,
    release_target,
)

TOOL_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TOOL_ROOT.parent
RESOURCE_ROOT = PROJECT_ROOT / "resource"
VERSION = json.loads((RESOURCE_ROOT / "version.json").read_text(encoding="utf-8"))
RELEASE = VERSION["release"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify a source-only runtime patch release."
    )
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT / "artifacts")
    parser.add_argument(
        "--platform", choices=SUPPORTED_PLATFORMS, default=current_platform()
    )
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    target = release_target(args.platform)
    release = output_root / f"Guildrun-Korean-{RELEASE}-{target}"
    expected_names = (
        {"GuildrunKoreanPatcher.exe"}
        if args.platform == PLATFORM_WINDOWS
        else {"GuildrunKoreanPatcher", "GuildrunKoreanPatcher.command"}
    )
    files = sorted(path for path in release.rglob("*") if path.is_file())
    if {path.name for path in files} != expected_names or len(files) != len(
        expected_names
    ):
        raise RuntimeError(f"Release directory contents are invalid: {expected_names}")
    if args.platform == PLATFORM_MACOS:
        for path in files:
            if path.stat().st_mode & 0o111 == 0:
                raise RuntimeError(
                    f"macOS executable permission is missing: {path.name}"
                )

    archive = output_root / f"{release.name}.zip"
    with zipfile.ZipFile(archive) as zip_file:
        if zip_file.testzip() is not None:
            raise RuntimeError("Release ZIP is corrupted")
        names = [item.filename for item in zip_file.infolist() if not item.is_dir()]
        if set(names) != expected_names or len(names) != len(expected_names):
            raise RuntimeError("Release ZIP contents are invalid")
        for path in files:
            if args.platform == PLATFORM_MACOS:
                archived_mode = zip_file.getinfo(path.name).external_attr >> 16
                if archived_mode & 0o111 == 0:
                    raise RuntimeError(
                        f"macOS ZIP executable permission is missing: {path.name}"
                    )
            archived = hashlib.sha256(zip_file.read(path.name)).digest()
            local = hashlib.sha256(path.read_bytes()).digest()
            if archived != local:
                raise RuntimeError(f"Release ZIP hash mismatch: {path.name}")
    print(
        json.dumps(
            {
                "platform": args.platform,
                "target": target,
                "runtime_executable": True,
                "archive_verified": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
