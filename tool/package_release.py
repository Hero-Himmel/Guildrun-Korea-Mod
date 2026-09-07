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


TOOL_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TOOL_ROOT.parent
RESOURCE_ROOT = PROJECT_ROOT / "resource"
ICON_PATH = RESOURCE_ROOT / "icons" / "GuildrunKoreanPatcher.ico"
sys.path.insert(0, str(TOOL_ROOT))
from build_patch import RELEASE


def build_runtime_executable(build_root: Path) -> Path:
    if not ICON_PATH.is_file():
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
        "--icon",
        str(ICON_PATH),
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
    subprocess.run(command, check=True)
    executable = dist / "GuildrunKoreanPatcher.exe"
    if not executable.is_file():
        raise RuntimeError("PyInstaller did not create GuildrunKoreanPatcher.exe")
    return executable


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the GitHub Release runtime patcher ZIP.")
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT / "artifacts")
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    output_root = args.output_root.resolve()
    output = output_root / f"Guildrun-Korean-{RELEASE}"
    if output.exists():
        if not args.rebuild:
            raise RuntimeError(f"Release output already exists: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="guildrun-release-", dir=output_root) as temporary:
        executable = build_runtime_executable(Path(temporary))
        shutil.copy2(executable, output / executable.name)

    archive = output_root / f"{output.name}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        executable = output / "GuildrunKoreanPatcher.exe"
        zip_file.write(executable, executable.name)
    print(f"Release: {output}\nArchive: {archive}")


if __name__ == "__main__":
    main()
