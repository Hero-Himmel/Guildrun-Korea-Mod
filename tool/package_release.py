"""Build the source-only Guildrun Korean patch release ZIP."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from build_patch import RELEASE
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
ICON_PATH = RESOURCE_ROOT / "icons" / "GuildrunKoreanPatcher.ico"


def build_runtime_executable(build_root: Path, platform: str) -> Path:
    host_platform = current_platform()
    if platform != host_platform:
        raise RuntimeError(f"{platform} 릴리즈는 {platform} 환경에서 빌드해야 합니다")
    if platform == PLATFORM_WINDOWS and not ICON_PATH.is_file():
        raise RuntimeError(f"EXE icon is missing: {ICON_PATH}")
    dist = build_root / "dist"
    command = [
        sys.executable,
        "-B",
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--log-level",
        "WARN",
        "--onefile",
        "--console",
        "--name",
        "GuildrunKoreanPatcher",
    ]
    if platform == PLATFORM_WINDOWS:
        command.extend(["--icon", str(ICON_PATH)])
    command.extend(
        [
            "--add-data",
            f"{RESOURCE_ROOT}{os.pathsep}resource",
            "--paths",
            str(TOOL_ROOT),
            "--collect-all",
            "UnityPy",
            "--distpath",
            str(dist),
            "--workpath",
            str(build_root / "work"),
            "--specpath",
            str(build_root / "spec"),
            str(TOOL_ROOT / "runtime_patcher.py"),
        ]
    )
    subprocess.run(command, check=True)
    executable_name = (
        "GuildrunKoreanPatcher.exe"
        if platform == PLATFORM_WINDOWS
        else "GuildrunKoreanPatcher"
    )
    executable = dist / executable_name
    if not executable.is_file():
        raise RuntimeError(f"PyInstaller did not create {executable_name}")
    return executable


def create_macos_launcher(output: Path) -> Path:
    launcher = output / "GuildrunKoreanPatcher.command"
    launcher.write_text(
        '#!/bin/zsh\nexec "${0:A:h}/GuildrunKoreanPatcher" "$@"\n',
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    return launcher


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the GitHub Release runtime patcher ZIP."
    )
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT / "artifacts")
    parser.add_argument(
        "--platform", choices=SUPPORTED_PLATFORMS, default=current_platform()
    )
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    output_root = args.output_root.resolve()
    target = release_target(args.platform)
    output = output_root / f"Guildrun-Korean-{RELEASE}-{target}"
    if output.exists():
        if not args.rebuild:
            raise RuntimeError(f"Release output already exists: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(
        prefix="guildrun-release-", dir=output_root
    ) as temporary:
        executable = build_runtime_executable(Path(temporary), args.platform)
        shutil.copy2(executable, output / executable.name)
    if args.platform == PLATFORM_MACOS:
        create_macos_launcher(output)

    archive = output_root / f"{output.name}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for path in sorted(output.iterdir()):
            zip_file.write(path, path.name)
    print(f"Release: {output}\nArchive: {archive}")


if __name__ == "__main__":
    main()
