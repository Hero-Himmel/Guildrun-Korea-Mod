"""Build and install the Guildrun Korean patch from the user's local game files."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from build_patch import RELEASE, VERSION, build_patch
from game_layout import (
    GameLayout,
    current_platform,
    default_game_roots,
    detect_game_layout,
)


def configure_console() -> None:
    """Use UTF-8 directly from the EXE; no CMD launcher is required."""
    if os.name != "nt" or not sys.stdout.isatty():
        return
    try:
        import ctypes

        kernel32 = getattr(ctypes, "windll").kernel32
        kernel32.SetConsoleOutputCP(65001)
        if sys.stdin.isatty():
            kernel32.SetConsoleCP(65001)
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def safe_path(root: Path, relative: Path | str) -> Path:
    root = root.resolve()
    target = (root / relative).resolve()
    if target != root and root not in target.parents:
        raise RuntimeError(f"Unsafe path: {relative}")
    return target


def load_source_hashes(layout: GameLayout) -> dict[str, set[str]]:
    source_files = VERSION.get("source_files")
    configured = (
        source_files.get(layout.platform) if isinstance(source_files, dict) else None
    )
    expected_paths = {path.as_posix() for path in layout.source_files.values()}
    if not isinstance(configured, dict) or set(configured) != expected_paths:
        raise RuntimeError(
            f"version.json의 {layout.platform} source_files 구성이 잘못되었습니다"
        )
    result: dict[str, set[str]] = {}
    for relative, hashes in configured.items():
        if (
            not isinstance(hashes, list)
            or not hashes
            or not all(isinstance(value, str) for value in hashes)
        ):
            raise RuntimeError(f"version.json의 해시 목록이 잘못되었습니다: {relative}")
        result[relative] = set(hashes)
    return result


def verify_source_files(layout: GameLayout) -> dict[str, str]:
    allowed = load_source_hashes(layout)
    observed: dict[str, str] = {}
    for relative in layout.source_files.values():
        path = safe_path(layout.install_root, relative)
        if not path.is_file():
            raise RuntimeError(f"필수 게임 파일이 없습니다: {relative.as_posix()}")
        digest = sha256(path)
        observed[relative.as_posix()] = digest
        if digest not in allowed[relative.as_posix()]:
            raise RuntimeError(
                f"지원하지 않는 게임 파일입니다: {relative.as_posix()}. "
                "Steam 무결성 검사 후 다시 시도하세요"
            )
    return observed


def replace_from_payload(
    layout: GameLayout,
    payload_root: Path,
    before_replace: Callable[[], None] | None = None,
) -> None:
    """Replace all patch files, retaining originals only for the active transaction."""
    relative_files = tuple(layout.source_files.values())
    for relative in relative_files:
        if not safe_path(payload_root, relative).is_file():
            raise RuntimeError(f"생성된 패치 파일이 없습니다: {relative.as_posix()}")

    with tempfile.TemporaryDirectory(prefix="guildrun-korean-rollback-") as rollback:
        rollback_root = Path(rollback)
        for relative in relative_files:
            original = safe_path(layout.install_root, relative)
            saved = safe_path(rollback_root, relative)
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, saved)
        if before_replace is not None:
            before_replace()

        replaced: list[Path] = []
        pending: list[Path] = []
        try:
            for relative in relative_files:
                source = safe_path(payload_root, relative)
                destination = safe_path(layout.install_root, relative)
                temporary = destination.with_name(
                    destination.name + f".guildrun-ko-{uuid.uuid4().hex}.tmp"
                )
                pending.append(temporary)
                shutil.copy2(source, temporary)
                os.replace(temporary, destination)
                pending.remove(temporary)
                replaced.append(relative)
        except Exception as install_error:
            restore_errors: list[str] = []
            for relative in reversed(replaced):
                destination = safe_path(layout.install_root, relative)
                temporary = destination.with_name(
                    destination.name + f".guildrun-ko-restore-{uuid.uuid4().hex}.tmp"
                )
                try:
                    shutil.copy2(safe_path(rollback_root, relative), temporary)
                    os.replace(temporary, destination)
                except Exception as restore_error:
                    restore_errors.append(f"{relative.as_posix()}: {restore_error}")
                finally:
                    temporary.unlink(missing_ok=True)
            if restore_errors:
                details = "; ".join(restore_errors)
                raise RuntimeError(
                    f"설치 실패 후 자동 롤백도 완료하지 못했습니다: {details}. "
                    "Steam에서 게임 파일 무결성 검사를 실행하세요"
                ) from install_error
            raise
        finally:
            for temporary in pending:
                temporary.unlink(missing_ok=True)


def format_duration(seconds: int) -> str:
    hours, remaining = divmod(seconds, 3600)
    minutes, seconds = divmod(remaining, 60)
    return (
        f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        if hours
        else f"{minutes:02d}:{seconds:02d}"
    )


class ProgressTimer:
    """Keep a single elapsed-time line below the current patch stage."""

    def __init__(self) -> None:
        self.started_at = time.monotonic()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_second = -1

    def elapsed_seconds(self) -> int:
        return int(time.monotonic() - self.started_at)

    def _render(self) -> None:
        print(
            f"\r진행 시간: {format_duration(self.elapsed_seconds())}",
            end="",
            flush=True,
        )

    def _clear_line(self) -> None:
        print("\r" + " " * 32 + "\r", end="", flush=True)

    def _tick(self) -> None:
        while not self._stop_event.wait(0.1):
            with self._lock:
                elapsed = self.elapsed_seconds()
                if elapsed != self._last_second:
                    self._last_second = elapsed
                    self._render()

    def start(self) -> None:
        with self._lock:
            self._last_second = self.elapsed_seconds()
            self._render()
        if sys.stdout.isatty():
            self._thread = threading.Thread(
                target=self._tick, name="progress-timer", daemon=True
            )
            self._thread.start()

    def stage(self, message: str) -> None:
        with self._lock:
            self._clear_line()
            print(message)
            self._render()

    def stop(self) -> int:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1)
        with self._lock:
            elapsed = self.elapsed_seconds()
            self._clear_line()
            print(f"진행 시간: {format_duration(elapsed)}")
        return elapsed


def install(layout: GameLayout, progress: ProgressTimer) -> None:
    progress.stage("[2/4] 한글 문장과 폰트로 패치 파일을 생성하는 중... (약 1분 소요)")
    with tempfile.TemporaryDirectory(prefix="guildrun-korean-") as temporary_root:
        payload_root = Path(temporary_root) / "payload"
        build_patch(
            game_root=layout.install_root,
            output=payload_root,
            platform=layout.platform,
        )
        progress.stage("[3/4] 설치 중 자동 롤백용 원본을 임시 보관하는 중...")
        replace_from_payload(
            layout,
            payload_root,
            before_replace=lambda: progress.stage(
                "[4/4] 한글 패치 파일을 게임 폴더에 적용하는 중..."
            ),
        )


def choose_game_layout(given: str | None) -> GameLayout:
    platform = current_platform()
    if given:
        layout = detect_game_layout(Path(given), platform)
        print("게임 경로 확인 완료.")
        return layout
    for default_root in default_game_roots(platform):
        try:
            layout = detect_game_layout(default_root, platform)
        except RuntimeError:
            continue
        print("기본 게임 경로 확인 완료.")
        return layout
    print("기본 게임 경로를 찾지 못했습니다.")
    while True:
        answer = (
            input("Guildrun Demo 설치 폴더 또는 Guildrun.app 경로를 입력하세요: ")
            .strip()
            .strip('"')
        )
        if not answer:
            raise RuntimeError("게임 경로를 입력하지 않아 종료합니다")
        try:
            layout = detect_game_layout(Path(answer), platform)
        except RuntimeError:
            print("Guildrun 게임 실행 파일이 있는 올바른 경로를 입력하세요.")
        else:
            print("게임 경로 확인 완료.")
            return layout


def set_warning_color() -> tuple[Any, int] | None:
    """Set bright-green text in a Windows console and retain its original color."""
    if os.name != "nt":
        return None
    try:
        import ctypes

        class Coord(ctypes.Structure):
            _fields_ = [("x", ctypes.c_short), ("y", ctypes.c_short)]

        class SmallRect(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_short),
                ("top", ctypes.c_short),
                ("right", ctypes.c_short),
                ("bottom", ctypes.c_short),
            ]

        class ConsoleScreenBufferInfo(ctypes.Structure):
            _fields_ = [
                ("size", Coord),
                ("cursor_position", Coord),
                ("attributes", ctypes.c_ushort),
                ("window", SmallRect),
                ("maximum_window_size", Coord),
            ]

        kernel32 = getattr(ctypes, "windll").kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        info = ConsoleScreenBufferInfo()
        if handle in (0, -1) or not kernel32.GetConsoleScreenBufferInfo(
            handle, ctypes.byref(info)
        ):
            return None
        original = int(info.attributes)
        bright_green = (original & 0xFFF0) | 0x000A
        kernel32.SetConsoleTextAttribute(handle, bright_green)
        return kernel32, original
    except Exception:
        return None


def restore_console_color(state: tuple[Any, int] | None) -> None:
    if state is not None:
        kernel32, original = state
        kernel32.SetConsoleTextAttribute(kernel32.GetStdHandle(-11), original)


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def read_confirmation() -> str:
    if os.name == "nt" and sys.stdin.isatty():
        import msvcrt

        while True:
            print("계속하시겠습니까?  1. Yes  2. No : ", end="", flush=True)
            answer = getattr(msvcrt, "getwch")()
            if answer in {"1", "2"}:
                print(answer)
                return answer
            print("\n1 또는 2를 입력하세요.")
    while True:
        answer = input("계속하시겠습니까?  1. Yes  2. No : ").strip()
        if answer in {"1", "2"}:
            return answer
        print("1 또는 2를 입력하세요.")


def confirm_install() -> bool:
    color_state = set_warning_color()
    try:
        print(
            "\n[주의 사항]\n"
            "이 MOD는 비공식 한글 패치입니다. "
            "사용에 따른 책임은 사용자 본인에게 있습니다.\n"
            "설치 중에만 원본 파일을 임시 보관하며, 실패하면 자동으로 되돌립니다.\n"
            "패치 제거 또는 게임 업데이트 후 복구에는 Steam 무결성 검사를 사용하세요.\n"
            "번역은 AI를 활용했으며, 번역 데이터를 다른 MOD에 포함해 "
            "재배포하지 마세요.\n"
        )
        if read_confirmation() == "1":
            return True
        print("패치를 취소했습니다.")
        return False
    finally:
        restore_console_color(color_state)


def main() -> int:
    configure_console()
    parser = argparse.ArgumentParser(description="Guildrun Korean runtime patcher")
    parser.add_argument("--game-path")
    parser.add_argument("--action", choices=("install", "check"), default="install")
    parser.add_argument("--no-pause", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "install" and not confirm_install():
            return 0
        if args.action == "install":
            clear_screen()
        layout = choose_game_layout(args.game_path)
        print(f"Guildrun 한국어 패치 {RELEASE}")
        if args.action == "check":
            verify_source_files(layout)
            print("[1/1] 호환성 테스트 완료.")
        else:
            progress = ProgressTimer()
            progress.start()
            try:
                verify_source_files(layout)
                progress.stage("[1/4] 호환성 테스트 완료.")
                install(layout, progress)
            finally:
                elapsed = progress.stop()
            print(f"Done. 한글 패치 완료. (총 소요 시간: {format_duration(elapsed)})")
    except Exception as error:
        print(f"한글 패치 실패: {error}")
        return 1
    finally:
        if not args.no_pause and getattr(sys, "frozen", False):
            input("계속하려면 Enter를 누르세요 . . .")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
