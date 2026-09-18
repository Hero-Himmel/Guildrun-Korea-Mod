"""Platform-specific Guildrun installation layout discovery."""

from __future__ import annotations

import platform as platform_module
import sys
from dataclasses import dataclass
from pathlib import Path

PLATFORM_WINDOWS = "windows"
PLATFORM_MACOS = "macos"
SUPPORTED_PLATFORMS = (PLATFORM_WINDOWS, PLATFORM_MACOS)


@dataclass(frozen=True)
class LayoutDefinition:
    platform: str
    executable: Path
    data_root: Path
    addressables_platform: str

    def source_files(self) -> dict[str, Path]:
        addressables = self.data_root / "StreamingAssets" / "aa"
        return {
            "resources": self.data_root / "resources.assets",
            "metadata": self.data_root
            / "il2cpp_data"
            / "Metadata"
            / "global-metadata.dat",
            "catalog": addressables / "catalog.bin",
            "target": addressables
            / self.addressables_platform
            / (
                "localization-string-tables-"
                "chinese(simplified)(zh-hans)_assets_all.bundle"
            ),
        }


DEFINITIONS = {
    PLATFORM_WINDOWS: LayoutDefinition(
        platform=PLATFORM_WINDOWS,
        executable=Path("Guildrun.exe"),
        data_root=Path("Guildrun_Data"),
        addressables_platform="StandaloneWindows64",
    ),
    PLATFORM_MACOS: LayoutDefinition(
        platform=PLATFORM_MACOS,
        executable=Path("Guildrun.app/Contents/MacOS/Guildrun"),
        data_root=Path("Guildrun.app/Contents/Resources/Data"),
        addressables_platform="StandaloneOSX",
    ),
}


@dataclass(frozen=True)
class GameLayout:
    install_root: Path
    definition: LayoutDefinition

    @property
    def platform(self) -> str:
        return self.definition.platform

    @property
    def executable(self) -> Path:
        return self.install_root / self.definition.executable

    @property
    def data_root(self) -> Path:
        return self.install_root / self.definition.data_root

    @property
    def source_files(self) -> dict[str, Path]:
        return self.definition.source_files()

    def path_for(self, role: str) -> Path:
        return self.install_root / self.source_files[role]


def current_platform() -> str:
    if sys.platform == "darwin":
        return PLATFORM_MACOS
    if sys.platform == "win32":
        return PLATFORM_WINDOWS
    raise RuntimeError(f"지원하지 않는 운영체제입니다: {sys.platform}")


def release_target(platform: str | None = None) -> str:
    platform = platform or current_platform()
    if platform == PLATFORM_WINDOWS:
        return PLATFORM_WINDOWS
    if platform != PLATFORM_MACOS:
        raise RuntimeError(f"지원하지 않는 플랫폼입니다: {platform}")
    architecture = platform_module.machine().lower()
    if architecture in {"arm64", "aarch64"}:
        return "macos-arm64"
    if architecture in {"x86_64", "amd64"}:
        return "macos-x64"
    raise RuntimeError(f"지원하지 않는 macOS 아키텍처입니다: {architecture}")


def default_game_roots(platform: str | None = None) -> tuple[Path, ...]:
    platform = platform or current_platform()
    if platform == PLATFORM_WINDOWS:
        return (Path(r"C:\Program Files (x86)\Steam\steamapps\common\Guildrun Demo"),)
    if platform == PLATFORM_MACOS:
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "Steam"
            / "steamapps"
            / "common"
            / "Guildrun Demo",
        )
    raise RuntimeError(f"지원하지 않는 플랫폼입니다: {platform}")


def normalize_install_root(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.name == "Guildrun.app" and resolved.is_dir():
        return resolved.parent
    return resolved


def detect_game_layout(path: Path, platform: str | None = None) -> GameLayout:
    install_root = normalize_install_root(path)
    candidates = (platform,) if platform is not None else SUPPORTED_PLATFORMS
    for candidate in candidates:
        definition = DEFINITIONS.get(candidate)
        if definition is None:
            raise RuntimeError(f"지원하지 않는 플랫폼입니다: {candidate}")
        layout = GameLayout(install_root=install_root, definition=definition)
        if layout.executable.is_file():
            return layout
    expected = ", ".join(str(DEFINITIONS[name].executable) for name in candidates)
    raise RuntimeError(f"게임 실행 파일을 찾지 못했습니다: {expected}")
