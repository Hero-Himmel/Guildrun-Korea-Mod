from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOL_ROOT = Path(__file__).resolve().parents[1] / "tool"
sys.path.insert(0, str(TOOL_ROOT))

from game_layout import (  # noqa: E402
    DEFINITIONS,
    GameLayout,
    detect_game_layout,
    release_target,
)
from runtime_patcher import install, replace_from_payload, verify_source_files  # noqa: E402
from unity_patch import PatchCompatibilityError  # noqa: E402


class GameLayoutTests(unittest.TestCase):
    def test_detects_macos_from_install_root_or_app(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            install_root = Path(temporary) / "Guildrun Demo"
            executable = install_root / DEFINITIONS["macos"].executable
            executable.parent.mkdir(parents=True)
            executable.touch()

            from_root = detect_game_layout(install_root, "macos")
            from_app = detect_game_layout(install_root / "Guildrun.app", "macos")

            self.assertEqual(from_root, from_app)
            self.assertEqual(from_root.install_root, install_root.resolve())
            self.assertEqual(
                from_root.source_files["target"].parts[-2],
                "StandaloneOSX",
            )

    @mock.patch("game_layout.platform_module.machine", return_value="x86_64")
    def test_names_intel_macos_release_explicitly(self, _machine: mock.Mock) -> None:
        self.assertEqual(release_target("macos"), "macos-x64")


class TransactionTests(unittest.TestCase):
    def make_files(
        self, root: Path, layout: GameLayout, prefix: str
    ) -> dict[Path, bytes]:
        contents: dict[Path, bytes] = {}
        for role, relative in layout.source_files.items():
            data = f"{prefix}-{role}".encode()
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            contents[relative] = data
        return contents

    def test_accepts_changed_source_files_on_each_platform(self) -> None:
        for platform, definition in DEFINITIONS.items():
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as temporary:
                layout = GameLayout(Path(temporary), definition)
                self.make_files(layout.install_root, layout, "unregistered-hotfix")

                verify_source_files(layout)

    def test_rejects_missing_or_directory_inputs(self) -> None:
        for platform, definition in DEFINITIONS.items():
            for missing in definition.source_files().values():
                with (
                    self.subTest(platform=platform, missing=missing),
                    tempfile.TemporaryDirectory() as temporary,
                ):
                    layout = GameLayout(Path(temporary), definition)
                    self.make_files(layout.install_root, layout, "original")
                    path = layout.install_root / missing
                    path.unlink()
                    for directory in (False, True):
                        if directory:
                            path.mkdir()
                        with self.assertRaisesRegex(RuntimeError, "필수 게임 파일이 없습니다"):
                            verify_source_files(layout)

    def test_incompatible_structure_never_replaces_game_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            layout = GameLayout(Path(temporary), DEFINITIONS["macos"])
            originals = self.make_files(layout.install_root, layout, "hotfix")
            with (
                mock.patch(
                    "runtime_patcher.build_patch",
                    side_effect=PatchCompatibilityError("incompatible structure"),
                ),
                mock.patch("runtime_patcher.replace_from_payload") as replace,
                self.assertRaisesRegex(PatchCompatibilityError, "incompatible structure"),
            ):
                verify_source_files(layout)
                install(layout, mock.Mock())

            replace.assert_not_called()
            for relative, expected in originals.items():
                self.assertEqual((layout.install_root / relative).read_bytes(), expected)

    def test_success_leaves_no_persistent_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            layout = GameLayout(root / "game", DEFINITIONS["macos"])
            payload = root / "payload"
            self.make_files(layout.install_root, layout, "original")
            patched = self.make_files(payload, layout, "patched")

            replace_from_payload(layout, payload)

            for relative, expected in patched.items():
                self.assertEqual(
                    (layout.install_root / relative).read_bytes(), expected
                )
            self.assertFalse((layout.install_root / ".guildrun-ko-backups").exists())

    def test_failure_restores_every_replaced_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            layout = GameLayout(root / "game", DEFINITIONS["macos"])
            payload = root / "payload"
            originals = self.make_files(layout.install_root, layout, "original")
            self.make_files(payload, layout, "patched")
            real_replace = os.replace
            failed = False

            def fail_once(source: Path, destination: Path) -> None:
                nonlocal failed
                if not failed and Path(destination).name == "catalog.bin":
                    failed = True
                    raise OSError("injected replacement failure")
                real_replace(source, destination)

            with (
                mock.patch("runtime_patcher.os.replace", side_effect=fail_once),
                self.assertRaisesRegex(OSError, "injected replacement failure"),
            ):
                replace_from_payload(layout, payload)

            for relative, expected in originals.items():
                self.assertEqual(
                    (layout.install_root / relative).read_bytes(), expected
                )
            leftovers = list(layout.install_root.rglob("*.guildrun-ko-*.tmp"))
            self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
